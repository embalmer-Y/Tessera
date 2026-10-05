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
