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

# natives 白名单 = 固件 runtime 注册面（natives.c native_symbols[]，板级十
# 对齐后六函数；沙箱边界：白名单外导入 = 一票拒绝 fail-closed）
NATIVE_WHITELIST = frozenset({
    "ts_gpio_write", "ts_gpio_read", "ts_pwm_set", "ts_adc_read",
    "ts_time_ms", "ts_log_write",
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


def _run_clang(c_path: Path, wasm_path: Path, timeout_s: float) -> None:
    """clang 编译；失败/超时 → TaError（stderr 完整保留，供 LLM 反馈回路）。

    IR2-09：start_new_session + 超时杀整进程组（clang 派生孙进程不遗留；
    proc.py 同纪律）。"""
    proc = subprocess.Popen(
        [CLANG, *CLANG_FLAGS, "-o", str(wasm_path), str(c_path)],
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


def compile_app_c(
    source_c: str,
    out_dir: str,
    allowed_roots: list[str],
    *,
    required_exports: list[str] | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> dict[str, Any]:
    """C 源 → wasm 自由固件 + 面检查（DEC-45；全部 fail-closed）。

    返回 {wasm_path, size, imports, exports, source_sha256, deterministic}。
    拒绝条件（任一）：编译失败/超时；导入非白名单符号；缺必需导出；
    尺寸超限；双编译字节不一致。
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
    with _dir_lock(real):  # IR2-10：同 out_dir 串行（防交叉污染）
        c_path.write_text(source_c, encoding="utf-8")
        _run_clang(c_path, wasm_path, timeout_s)
        # 确定性自证：同源重编译逐字节比对（R5；不一致 = 环境泄漏）
        _run_clang(c_path, wasm2_path, timeout_s)
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
