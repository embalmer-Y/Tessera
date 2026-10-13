# SPDX-License-Identifier: Apache-2.0
"""APP C 源 → wasm32 自由固件编译 + 面检查（DEC-45 / Q-25 方案 A；G1）。

可靠性工程（调研 Claude Code / Codex CLI / aider 的实践映射，见
docs/agent-codegen-reliability-01.md）：
- **验证阶梯的确定性门**（R1/R5）：编译（clang 固定 flags）→ 导入/导出
  面检查（白名单 fail-closed）→ 尺寸上限 → **双编译字节一致**（同源两次
  编译产物逐字节相等——确定性自证，合同 9 精神延伸到工具链；不一致 =
  环境泄漏，拒绝）。
- **错误如实反馈**（R2/R6）：编译器 stderr 完整进错误 detail（调用方可
  喂回 LLM 有界重试）；不截断不美化。
- **沙箱纪律**（R4）：子进程零网络诉求（clang 编译不触网）、固定参数、
  时限 kill（timeout_s）、**产物不执行**（wasm 只产不跑）。
- **整文件再生**（R3）：本链的产物形态 = 完整单文件 C 源（aider 编辑格式
  分级结论：小文件域 whole-file 可靠性最优，避免部分编辑错位/elision）。
"""
from __future__ import annotations

import hashlib
import os
import re
import signal
import subprocess
import threading
from pathlib import Path
from typing import Any

from tessera_agent.common.errors import TA_E_ARGS, TA_E_TSAP, TaError
from tessera_agent.tools_tsap.tools import _resolve_within

# natives 白名单 = 固件 runtime 注册面（natives.c native_symbols[]）；
# 沙箱边界：白名单外导入 = 一票拒绝 fail-closed
NATIVE_WHITELIST = frozenset({
    "ts_gpio_write", "ts_gpio_read", "ts_pwm_set", "ts_adc_read",
    "ts_time_ms", "ts_log_write",
    "ts_fs_read", "ts_fs_write", "ts_fs_list", "ts_fs_delete",  # DEC-47④（MD1.2e）
    "ts_av_capture", "ts_net_publish",  # DEC-47③⑥（MD1.2g）
    "ts_kv_save", "ts_kv_load",  # V0.4.0 M9（DR-15）：业务状态持久化
    # V2 纵深 M19（DEC-55/Q-37 A）：宿主侧线程编排——固件 TS_APP_THREADS
    # 门控注册（默认构建不存在 = 装载期未解析导入即拒，fail-closed 仍闭环）
    "ts_thread_start", "ts_thread_join",
})

# 框架回调（runtime lookup：health_ping 必有；app_init/app_tick/app_evt
# 可选——required_exports 未给时的下限）
MIN_EXPORTS = frozenset({"health_ping"})

# 编译 flags = firmware/tests/app/appw/build.sh 同款（M2b.2a 定稿自由固件
# 惯例；禁 WASI/stdio、无入口、未定义符号延后链接期）
CLANG_FLAGS = [
    "--target=wasm32", "-O2", "-nostdlib", "-ffreestanding", "-fno-builtin",
    "-Wl,--no-entry", "-Wl,--allow-undefined", "-Wl,--strip-all",
]

# 线程档追加 flags（M19/DEC-55）= firmware/tests/threads/thrdw/build.sh
# 同款（WAMR samples/spawn-thread 官方配方）：-pthread（原子内建）+
# 共享内存 + aux stack（-z stack-size）+ max-memory 上界。
CLANG_FLAGS_THREADS = [
    "-pthread", "-z", "stack-size=32768",
    "-Wl,--shared-memory", "-Wl,--max-memory=131072",
]

# 尺寸上限默认 = CONFIG_TS_APP_LOAD_MAX 默认 16384（固件装载缓冲结构性
# 上限；板级裁剪按板声明——工具按调用方参数收紧）
DEFAULT_MAX_BYTES = 16384
# 编译时限（秒）：R4 沙箱纪律——所有子进程有时限，超时杀进程如实报错
DEFAULT_TIMEOUT_S = 60.0
CLANG = "clang"


# ---- wasm 二进制面解析（零依赖；llvm-objdump-18 解析不了 strip 后 wasm——
# G1 spike 实证，已用仓库夹具对照校准）----------------------------------------

def _leb(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(buf):
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, pos
        shift += 7
        if shift > 35:
            raise ValueError("leb128 溢出")
    raise ValueError("leb128 截断")


def _name(buf: bytes, pos: int) -> tuple[bytes, int]:
    n, pos = _leb(buf, pos)
    if pos + n > len(buf):
        raise ValueError("name 截断")
    return buf[pos:pos + n], pos + n


def wasm_func_surface(path: str | Path) -> tuple[set[str], set[str]]:
    """提取 wasm 二进制的函数导入/导出名集合（自由固件子集：仅函数面）。"""
    buf = Path(path).read_bytes()
    if len(buf) < 8 or buf[:4] != b"\x00asm":
        raise ValueError("not a wasm binary")
    pos = 8
    imports: set[str] = set()
    exports: set[str] = set()
    while pos < len(buf):
        sec_id = buf[pos]
        pos += 1
        size, pos = _leb(buf, pos)
        end = pos + size
        if end > len(buf):
            raise ValueError("section 越界")
        if sec_id == 2:  # import
            count, p = _leb(buf, pos)
            for _ in range(count):
                _mod, p = _name(buf, p)
                nm, p = _name(buf, p)
                kind = buf[p] if p < len(buf) else -1
                p += 1
                if kind == 0x00:  # func
                    _, p = _leb(buf, p)
                    imports.add(nm.decode("utf-8", "replace"))
                elif kind == 0x02:  # memory
                    raise ValueError("imported memory（WASI/非自由固件）")
                else:
                    p += 1  # table/global/tag：V1 natives 不含，粗跳过
        elif sec_id == 7:  # export
            count, p = _leb(buf, pos)
            for _ in range(count):
                nm, p = _name(buf, p)
                kind = buf[p] if p < len(buf) else -1
                _, p = _leb(buf, p + 1)
                if kind == 0x00:
                    exports.add(nm.decode("utf-8", "replace"))
        pos = end
    return imports, exports


# ---- 编译 + 面检查 ------------------------------------------------------------

# IR2-03（impl-review-02）预处理读面封死：自由固件零 include（natives 经
# extern 声明）；#include 与 __has_include 可探读/回显主机任意文件（clang
# 诊断含被包含源文本 → stderr 回喂 LLM），一律拒绝。放宽须走门 ③。
_INCLUDE_RE = re.compile(r"^\s*#\s*include\b", re.MULTILINE)

# 同 out_dir 串行化（IR2-10）：固定文件名 app.c/app.wasm 在并发编译下会
# 交叉污染双编译一致性检查——按真实路径互斥。
_DIR_LOCKS: dict[str, threading.Lock] = {}
_DIR_LOCKS_GUARD = threading.Lock()


def _dir_lock(real: Path) -> threading.Lock:
    with _DIR_LOCKS_GUARD:
        return _DIR_LOCKS.setdefault(str(real), threading.Lock())


def _gate_source(source_c: str) -> None:
    if _INCLUDE_RE.search(source_c) or "__has_include" in source_c:
        raise TaError(
            TA_E_ARGS,
            "source_c 含 #include/__has_include（自由固件零依赖：natives 经 "
            "extern 声明；禁预处理读面）",
            domain="app_compile",
        )
    _gate_health_ping(source_c)


# 多文件工程包含门（AG3 · LLD-A08 §2.2）：引号包含仅限工程内相对头
_INCLUDE_ANGLE_RE = re.compile(r"^\s*#\s*include\s*<", re.M)
_INCLUDE_QUOTED_RE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.M)


def _gate_project_sources(files: dict[str, str]) -> None:
    """多文件工程源门：系统包含与 __has_include 全拒（IR2-03 读面纪律维持）；
    引号包含 = 仅限工程文件表内相对头（规范化后不得越出文件表——防探读工程外）。"""
    import posixpath

    names = set(files)
    for name, src in files.items():
        if "__has_include" in src or _INCLUDE_ANGLE_RE.search(src):
            raise TaError(
                TA_E_ARGS,
                f"{name}: 含 #include<>/__has_include（自由固件零依赖：natives 经 extern 声明）",
                domain="app_compile",
            )
        for m in _INCLUDE_QUOTED_RE.finditer(src):
            inc = m.group(1)
            norm = posixpath.normpath(posixpath.join(posixpath.dirname(name), inc))
            if (posixpath.isabs(norm) or ".." in norm.split("/")
                    or norm not in names):
                raise TaError(
                    TA_E_ARGS,
                    f"{name}: 引号包含越界（仅限工程文件表内头文件）: {inc}",
                    domain="app_compile",
                    detail={"file": name, "include": inc},
                )
        _gate_health_ping(src)


def _gate_health_ping(source_c: str) -> None:
    """health_ping 返回值语义门（V0.4.0 M3，nvd 单迹定性对策）。

    框架合同：health_ping 返回 0 = 健康；非零 = 健康失败（连续 3 次 →
    自动回滚）。LLM 实测误解：把「业务完成态」当非零返回值表达（nvd APP
    `return g_done ? 1 : 0` → DONE 后死亡回滚）。启发式拦截：函数体内任一
    return 表达式含**非零整型字面量** → 拒绝（剥字符串/字符/注释后扫描；
    纯变量返回放行——静态不可知，提示词合同兜底）。"""
    m = re.search(r"health_ping\s*\([^)]*\)\s*\{", source_c)
    if m is None:
        return  # 缺导出由 exports 面门拦截（此处不重复）
    depth = 1
    pos = m.end()
    while pos < len(source_c) and depth > 0:
        ch = source_c[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        pos += 1
    body = source_c[m.end():pos - 1]
    # 剥字符串/字符字面量与注释（其中数字不作数）
    stripped = re.sub(r'"(?:\\.|[^"\\])*"', '""', body)
    stripped = re.sub(r"'(?:\\.|[^'\\])*'", "''", stripped)
    stripped = re.sub(r"/\*.*?\*/", " ", stripped, flags=re.S)
    stripped = re.sub(r"//[^\n]*", " ", stripped)
    for ret in re.finditer(r"return\s+([^;]*);", stripped):
        expr = ret.group(1)
        # 含函数调用的返回值静态不可知（如 return evil(1) 的实参字面量
        # 不属返回值语义）——跳过，提示词合同兜底
        if re.search(r"[A-Za-z_][A-Za-z0-9_]*\s*\(", expr):
            continue
        if re.search(r"(?<![0-9A-Za-z_])[1-9][0-9]*(?![0-9A-Za-z_])", expr):
            raise TaError(
                TA_E_ARGS,
                "health_ping 语义合同违反：return 表达式含非零字面量"
                f"（`return {ret.group(1).strip()};`）。合同：health_ping 恒返回 0"
                "（0=健康；非零=健康失败，连续 3 次将触发自动回滚）。"
                "业务完成态一律经 ts_log 行表达，绝不用 health_ping 返回值表达。",
                domain="app_compile",
            )


def _run_clang_files(
    c_paths: list[Path],
    wasm_path: Path,
    timeout_s: float,
    extra_flags: list[str] | None = None,
    exports: list[str] | None = None,
) -> None:
    """clang 聚合编译（单/多文件同一实现）；失败/超时 → TaError（stderr 完整保留）。

    IR2-09：start_new_session + 超时杀整进程组。exports：逐符号
    `-Wl,--export=`——符号缺失即链接错（工程清单 fail-closed，Q-39①）。"""
    cmd = [
        CLANG, *CLANG_FLAGS, *(extra_flags or []),
        *[f"-Wl,--export={e}" for e in (exports or [])],
        "-o", str(wasm_path), *[str(p) for p in c_paths],
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True,
    )
    try:
        _out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            proc.kill()
        proc.communicate()
        msg = f"clang 编译超时（>{timeout_s}s，进程组已终止）"
        raise TaError(TA_E_TSAP, msg, domain="app_compile") from None
    if proc.returncode != 0:
        msg = f"clang 编译失败（exit {proc.returncode}）"
        raise TaError(TA_E_TSAP, msg, domain="app_compile",
                      detail={"stderr": (err or "")[-4000:], "stdout": ""})


def _run_clang(c_path: Path, wasm_path: Path, timeout_s: float,
               extra_flags: list[str] | None = None) -> None:
    """单文件兼容包装（既有调用面不变）。"""
    _run_clang_files([c_path], wasm_path, timeout_s, extra_flags)


def compile_app_c(
    source_c: str,
    out_dir: str,
    allowed_roots: list[str],
    *,
    required_exports: list[str] | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    threads: int = 1,
) -> dict[str, Any]:
    """C 源 → wasm 自由固件 + 面检查（DEC-45；全部 fail-closed）。

    返回 {wasm_path, size, imports, exports, source_sha256, deterministic}。
    拒绝条件（任一）：编译失败/超时；导入非白名单符号；缺必需导出；
    尺寸超限；双编译字节不一致。
    threads>1（M19/DEC-55）：线程档——共享内存 + 原子 + aux stack flags
    （CLANG_FLAGS_THREADS）。
    """
    if not source_c or not source_c.strip():
        raise TaError(TA_E_ARGS, "source_c 为空", domain="app_compile")
    _gate_source(source_c)
    # IR2-03 服务端钳制：调用方（含 LLM）传大值不可放宽固件装载上限
    max_bytes = min(int(max_bytes), DEFAULT_MAX_BYTES)
    real = _resolve_within(out_dir, allowed_roots)
    real.mkdir(parents=True, exist_ok=True)
    c_path = real / "app.c"
    wasm_path = real / "app.wasm"
    wasm2_path = real / "app.wasm.check"
    thr_flags = CLANG_FLAGS_THREADS if int(threads) > 1 else []
    with _dir_lock(real):  # IR2-10：同 out_dir 串行（防交叉污染）
        c_path.write_text(source_c, encoding="utf-8")
        _run_clang(c_path, wasm_path, timeout_s, thr_flags)
        # 确定性自证：同源重编译逐字节比对（R5；不一致 = 环境泄漏）
        _run_clang(c_path, wasm2_path, timeout_s, thr_flags)
        deterministic = wasm_path.read_bytes() == wasm2_path.read_bytes()
        wasm2_path.unlink()
    if not deterministic:
        msg = "双编译产物字节不一致（编译环境非确定性——拒绝）"
        raise TaError(TA_E_TSAP, msg, domain="app_compile")

    size = wasm_path.stat().st_size
    if size > max_bytes:
        msg = f"wasm 尺寸 {size}B 超上限 {max_bytes}B（TS_APP_LOAD_MAX 域）"
        raise TaError(TA_E_TSAP, msg, domain="app_compile",
                      detail={"size": size, "max_bytes": max_bytes})

    imports, exports = wasm_func_surface(wasm_path)
    bad = sorted(imports - NATIVE_WHITELIST)
    if bad:
        msg = f"导入面越权（natives 白名单外）: {bad}"
        raise TaError(TA_E_TSAP, msg, domain="app_compile",
                      detail={"imports": sorted(imports), "whitelist": sorted(NATIVE_WHITELIST)})
    need = set(required_exports) if required_exports else set(MIN_EXPORTS)
    missing = sorted(need - exports)
    if missing:
        msg = f"缺少必需导出: {missing}"
        raise TaError(TA_E_TSAP, msg, domain="app_compile",
                      detail={"exports": sorted(exports), "required": sorted(need)})

    return {
        "wasm_path": str(wasm_path),
        "size": size,
        "imports": sorted(imports),
        "exports": sorted(exports),
        "source_sha256": hashlib.sha256(source_c.encode()).hexdigest(),
        "deterministic": True,
    }


def compile_project_c(
    files: dict[str, str],
    out_dir: str,
    allowed_roots: list[str],
    *,
    exports: list[str] | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    threads: int = 1,
) -> dict[str, Any]:
    """多文件工程 → 单 wasm（AG3 · LLD-A08 §2.2/§4——工程清单驱动，Q-39①）。

    files = {相对路径: 源文本}（.c 入编译命令；.h 落盘供引号包含解析）；
    exports = 工程清单导出表 → 逐符号 `-Wl,--export=`（缺符号 = 链接错，
    fail-closed）。门与单文件链一致：工程包含门（_gate_project_sources）、
    双编译字节一致、尺寸、导入白名单、必需导出。
    返回 {wasm_path, size, imports, exports, files_sha256, deterministic}。
    """
    if not files or not any(n.endswith(".c") for n in files):
        raise TaError(TA_E_ARGS, "工程须含至少一个 .c 文件", domain="app_compile")
    _gate_project_sources(files)
    max_bytes = min(int(max_bytes), DEFAULT_MAX_BYTES)
    real = _resolve_within(out_dir, allowed_roots)
    src_dir = real / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    c_paths: list[Path] = []
    for name, content in sorted(files.items()):
        p = src_dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        if name.endswith(".c"):
            c_paths.append(p)
    need = list(exports) if exports else sorted(MIN_EXPORTS)
    wasm_path = real / "app.wasm"
    wasm2_path = real / "app.wasm.check"
    thr_flags = CLANG_FLAGS_THREADS if int(threads) > 1 else []
    with _dir_lock(real):  # IR2-10：同 out_dir 串行
        _run_clang_files(c_paths, wasm_path, timeout_s, thr_flags, need)
        _run_clang_files(c_paths, wasm2_path, timeout_s, thr_flags, need)
        deterministic = wasm_path.read_bytes() == wasm2_path.read_bytes()
        wasm2_path.unlink()
    if not deterministic:
        raise TaError(
            TA_E_TSAP, "双编译产物字节不一致（编译环境非确定性——拒绝）",
            domain="app_compile",
        )
    size = wasm_path.stat().st_size
    if size > max_bytes:
        raise TaError(
            TA_E_TSAP,
            f"wasm 尺寸 {size}B 超上限 {max_bytes}B（档位门——Q-39⑤ 分档双门）",
            domain="app_compile",
            detail={"size": size, "max_bytes": max_bytes},
        )
    imports, got_exports = wasm_func_surface(wasm_path)
    bad = sorted(imports - NATIVE_WHITELIST)
    if bad:
        raise TaError(
            TA_E_TSAP, f"导入面越权（natives 白名单外）: {bad}",
            domain="app_compile",
            detail={"imports": sorted(imports), "whitelist": sorted(NATIVE_WHITELIST)},
        )
    missing = sorted(set(need) - got_exports)
    if missing:
        raise TaError(
            TA_E_TSAP, f"缺少必需导出: {missing}",
            domain="app_compile",
            detail={"exports": sorted(got_exports), "required": sorted(set(need))},
        )
    return {
        "wasm_path": str(wasm_path),
        "size": size,
        "imports": sorted(imports),
        "exports": sorted(got_exports),
        "files_sha256": {
            n: hashlib.sha256(c.encode()).hexdigest() for n, c in sorted(files.items())
        },
        "deterministic": True,
    }
