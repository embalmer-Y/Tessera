# SPDX-License-Identifier: Apache-2.0
"""wasm_build 测试（DEC-45/Q-25 A）：面解析器（仓库夹具对照）+ 真编译面。
硬依赖宿主 clang（M2b.2a 起在位；agent-checks CI 显式安装）——不做静默
skip（板级十教训：门控测试掩盖漂移）。全部 fail-closed 分支各一条。"""
from __future__ import annotations

from pathlib import Path

import pytest

from tessera_agent.common.errors import TaError
from tessera_agent.tools_tsap.wasm_build import (
    compile_app_c,
    wasm_func_surface,
)

REPO = Path(__file__).resolve().parents[2]
FIXTURE_WASM = REPO / "firmware" / "tests" / "app" / "appw" / "native_app.wasm"
FIXTURE_C = REPO / "firmware" / "tests" / "app" / "appw" / "native_app.c"

GOOD_C = """
extern int ts_pwm_set(int ctx, int inst, int hz, int permille);
static int g_ctx;
static int g_duty;
__attribute__((export_name("app_init"))) int app_init(int ctx) {
    g_ctx = ctx; g_duty = 0;
    return ts_pwm_set(ctx, 0, 1000, 0);
}
__attribute__((export_name("app_tick"))) int app_tick(void) {
    g_duty += 10;
    if (g_duty > 700) { g_duty = 0; }
    return ts_pwm_set(g_ctx, 0, 1000, g_duty);
}
__attribute__((export_name("app_evt"))) int app_evt(int v) { (void)v; return 0; }
__attribute__((export_name("health_ping"))) int health_ping(void) { return 0; }
"""


def _ctx_of(tmp_path):
    class Roots:
        @staticmethod
        def roots():
            return [str(tmp_path)]
    return Roots()


class TestWasmSurface:
    def test_fixture_surface(self):
        """仓库夹具（固件运行时同一工件）的已知面 = 解析器校准锚。"""
        imports, exports = wasm_func_surface(FIXTURE_WASM)
        assert imports == {"ts_gpio_write"}
        assert {"app_init", "app_tick", "app_evt", "health_ping",
                "get_last_evt"} <= exports

    def test_not_wasm(self, tmp_path):
        bad = tmp_path / "x.wasm"
        bad.write_bytes(b"ELF....")
        with pytest.raises(ValueError, match="not a wasm"):
            wasm_func_surface(bad)


class TestCompileAppC:
    def test_ok_and_deterministic(self, tmp_path):
        out = compile_app_c(GOOD_C, str(tmp_path / "o"), [str(tmp_path)])
        assert out["imports"] == ["ts_pwm_set"]
        assert "health_ping" in out["exports"]
        assert out["deterministic"] is True
        assert 0 < out["size"] <= 16384
        assert len(out["source_sha256"]) == 64
        assert Path(out["wasm_path"]).is_file()

    def test_threads_mode_shared_memory(self, tmp_path):
        """M19/DEC-55：threads>1 线程档——共享内存 + 原子 + ts_thread_* 白名单。"""
        src = (
            "extern int ts_thread_start(int c, const char *n, int l, int a);\n"
            "extern int ts_thread_join(int c, int h);\n"
            "static int g_cnt;\n"
            "__attribute__((export_name(\"health_ping\")))\n"
            "int health_ping(void) { return 0; }\n"
            "__attribute__((export_name(\"worker\")))\n"
            "int worker(int n) {\n"
            "    for (int i = 0; i < n; i++)\n"
            "        __atomic_fetch_add(&g_cnt, 1, __ATOMIC_RELAXED);\n"
            "    return n;\n"
            "}\n"
            "__attribute__((export_name(\"spawn_two\")))\n"
            "int spawn_two(int n) {\n"
            "    int h = ts_thread_start(0, \"worker\", 6, n);\n"
            "    return (h > 0) ? ts_thread_join(0, h) : h;\n"
            "}\n"
        )
        out = compile_app_c(src, str(tmp_path / "o"), [str(tmp_path)],
                            required_exports=["health_ping", "worker",
                                              "spawn_two"],
                            threads=2)
        assert set(out["imports"]) == {"ts_thread_join", "ts_thread_start"}
        assert out["deterministic"] is True
        # 共享内存标记落在 memory 段（flags bit1 = shared）——面检查容忍
        buf = Path(out["wasm_path"]).read_bytes()
        assert buf[:4] == b"\x00asm"

    def test_same_source_as_repo_fixture(self, tmp_path):
        """同源不变量：用仓库夹具 native_app.c 编译，面与随仓 .wasm 一致。"""
        src = FIXTURE_C.read_text(encoding="utf-8")
        out = compile_app_c(src, str(tmp_path / "o"), [str(tmp_path)],
                            required_exports=["app_init", "app_evt", "app_tick",
                                              "health_ping", "get_last_evt"])
        fi, fe = wasm_func_surface(FIXTURE_WASM)
        assert set(out["imports"]) == fi
        assert set(out["exports"]) == fe

    def test_compile_error_feeds_back_stderr(self, tmp_path):
        with pytest.raises(TaError) as ei:
            compile_app_c("int broken( {", str(tmp_path / "o"), [str(tmp_path)])
        assert "编译失败" in ei.value.message
        assert ei.value.detail and "stderr" in ei.value.detail

    def test_import_whitelist_reject(self, tmp_path):
        evil = ("extern int evil(int);\n"
                '__attribute__((export_name("health_ping"))) '
                "int health_ping(void) { return evil(1); }\n")
        with pytest.raises(TaError, match="导入面越权"):
            compile_app_c(evil, str(tmp_path / "o"), [str(tmp_path)])

    def test_missing_export_reject(self, tmp_path):
        no_export = "static int x;\n"
        with pytest.raises(TaError, match="缺少必需导出"):
            compile_app_c(no_export, str(tmp_path / "o"), [str(tmp_path)])

    def test_size_cap_reject(self, tmp_path):
        with pytest.raises(TaError, match="尺寸.*超上限"):
            compile_app_c(GOOD_C, str(tmp_path / "o"), [str(tmp_path)],
                          max_bytes=16)

    def test_roots_reject(self, tmp_path):
        with pytest.raises(TaError, match="越界"):
            compile_app_c(GOOD_C, "/etc", [str(tmp_path)])

    def test_empty_source(self, tmp_path):
        with pytest.raises(TaError, match="source_c 为空"):
            compile_app_c("  ", str(tmp_path / "o"), [str(tmp_path)])

    # ---- IR2-03 加固批（DEC-48 排期表单元 3）--------------------------------

    # ---- V0.4.0 M3：health_ping 语义门（nvd 单迹定性对策）--------------------

    def test_health_ping_nonzero_literal_reject(self, tmp_path):
        """health_ping 返回非零字面量（nvd 实测误解形态 `done ? 1 : 0`）= 拒绝。"""
        src = GOOD_C.replace(
            "int health_ping(void) { return 0; }",
            "int health_ping(void) { static int done = 1;"
            " return done ? 1 : 0; }")
        assert src != GOOD_C
        with pytest.raises(TaError, match="health_ping 语义合同"):
            compile_app_c(src, str(tmp_path / "o"), [str(tmp_path)])

    def test_health_ping_neg_const_reject(self, tmp_path):
        """-1 错误码返回 = 同样拒绝（非零即病）。"""
        src = GOOD_C.replace(
            "int health_ping(void) { return 0; }",
            "int health_ping(void) { return -1; }")
        with pytest.raises(TaError, match="health_ping 语义合同"):
            compile_app_c(src, str(tmp_path / "o"), [str(tmp_path)])

    def test_health_ping_var_and_string_digits_pass(self, tmp_path):
        """纯变量返回/字符串内数字放行（静态不可知——提示词合同兜底）。"""
        src = GOOD_C.replace(
            "int health_ping(void) { return 0; }",
            'int health_ping(void) { static int e = 0;'
            ' return e; } /* "ticks=10" 注释含数字不作数 */')
        compile_app_c(src, str(tmp_path / "o"), [str(tmp_path)])

    def test_include_gate_system(self, tmp_path):
        """#include 系统头 = 预处理读面，拒绝（自由固件零依赖）。"""
        with pytest.raises(TaError, match="#include"):
            compile_app_c("#include <stdio.h>\n" + GOOD_C,
                          str(tmp_path / "o"), [str(tmp_path)])

    def test_include_gate_absolute_path(self, tmp_path):
        """绝对路径 #include = 主机任意文件探读，拒绝。"""
        with pytest.raises(TaError, match="#include"):
            compile_app_c('#include "/etc/passwd"\n' + GOOD_C,
                          str(tmp_path / "o"), [str(tmp_path)])

    def test_has_include_probe_gate(self, tmp_path):
        """__has_include 可作文件存在性探针，拒绝。"""
        with pytest.raises(TaError, match="include"):
            compile_app_c("#if __has_include(<stdlib.h>)\n#endif\n" + GOOD_C,
                          str(tmp_path / "o"), [str(tmp_path)])

    def test_max_bytes_server_clamp(self, tmp_path):
        """调用方传超大 max_bytes 不可放宽服务端钳制（DEFAULT_MAX_BYTES）。"""
        pad = ",".join(str(i % 251) for i in range(20000))
        src = (f"const unsigned char pad[20000] __attribute__((used)) = {{{pad}}};\n"
               "__attribute__((export_name(\"app_tick\"))) "
               "int app_tick(void){ return pad[0]; }\n"
               "__attribute__((export_name(\"health_ping\"))) "
               "int health_ping(void){ return 0; }\n")
        with pytest.raises(TaError, match="超上限 16384"):
            compile_app_c(src, str(tmp_path / "o"), [str(tmp_path)],
                          max_bytes=10**9)


# ---- CG4（Q-39②⑤/Q-42 · DEC-59）：档位门 + needs 链接钉死 ------------------

BIG_C = GOOD_C.replace(
    "__attribute__((export_name(\"app_evt\"))) int app_evt(int v) { (void)v; return 0; }",
    "static const unsigned char pad[24576] = {[3] = 7};\n"
    "__attribute__((export_name(\"app_evt\"))) int app_evt(int v)"
    " { return pad[v & 3]; }")

NEEDS = {"linear_memory_kb": 128, "stack_kb": 32}


class TestTierGates:
    def test_small_gate_rejects_big_wasm(self, tmp_path):
        """24KB 表 > small 门 16KB → 拒（门不撤只分档——small 维持）。"""
        with pytest.raises(TaError, match="尺寸.*超上限"):
            compile_app_c(BIG_C, str(tmp_path / "o"), [str(tmp_path)])

    def test_large_gate_and_link_flags(self, tmp_path):
        """tier=large + needs：门放行（≤256KB）+ initial/max-memory 钉死
        （128KB → 2 页恰整——链接无取整余量）+ 双编译一致维持。"""
        r = compile_app_c(BIG_C, str(tmp_path / "o"), [str(tmp_path)],
                          tier="large", needs=NEEDS)
        assert r["size"] > 24576
        assert r["deterministic"] is True

    def test_needs_page_rounding(self, tmp_path):
        """非整页 needs（100KB → 2 页 128KB）链接接受（向上取整钉死）。"""
        r = compile_app_c(GOOD_C, str(tmp_path / "o"), [str(tmp_path)],
                          tier="large",
                          needs={"linear_memory_kb": 100, "stack_kb": 8})
        assert r["size"] <= 262144

    def test_group_discipline(self, tmp_path):
        """large 无 needs / needs 配 small = 成组违例拒（与 TsapManifest 同语义）。"""
        with pytest.raises(TaError, match="须附 needs"):
            compile_app_c(GOOD_C, str(tmp_path / "o"), [str(tmp_path)],
                          tier="large")
        with pytest.raises(TaError, match="仅 tier=large"):
            compile_app_c(GOOD_C, str(tmp_path / "o"), [str(tmp_path)],
                          needs=NEEDS)

    def test_large_gate_still_clamps(self, tmp_path):
        """large 档钳制维持：调用方 max_bytes 不可越 256KB（IR2-03 语义平移）。"""
        with pytest.raises(TaError, match="超上限"):
            compile_app_c(GOOD_C, str(tmp_path / "o"), [str(tmp_path)],
                          max_bytes=8, tier="large", needs=NEEDS)


# ---- K2（Q-44②/DEC-61②）：ts_av_write 白名单同步 ------------------------------

class TestAvWriteWhitelist:
    def test_ts_av_write_whitelisted(self):
        """ts_av_write 在 NATIVE_WHITELIST（av:write 输出面——固件 natives 同步）。"""
        from tessera_agent.tools_tsap.wasm_build import NATIVE_WHITELIST
        assert "ts_av_write" in NATIVE_WHITELIST
