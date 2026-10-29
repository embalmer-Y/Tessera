# SPDX-License-Identifier: Apache-2.0
"""test_criteria_sim — AC-3 判据自评价闭环测试（DEC-82）。
判据窗引擎（纯函数）/ 创作 wasm 执行器（现场 clang 编译最小件——无
wasm 工具链环境 skip）/ sim 桥 / MCP app_criteria_run 面。
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from tessera_agent.common.errors import TA_E_SIM, TaError
from tessera_agent.domain import wasm_sim
from tessera_agent.domain.criteria import judge_lines

FIX = Path(__file__).parent / "fixtures"


# ---- 判据窗引擎 ----------------------------------------------------------


def test_segment_takes_last_marker_window():
    lines = [
        "HB n=990",  # 上一实例残留（开埠复位脉动前）
        "CONNECTED loc=tcp/1.2.3.4:9957",
        "HB n=10", "HB n=20", "HB n=30",
    ]
    rep = judge_lines(
        lines, [{"type": "monotonic", "pattern": r"HB n=(\d+)"}], "CONNECTED")
    assert rep.segments_seen == 1
    assert rep.segment_lines == 3
    assert rep.rules[0]["ok"] and rep.rules[0]["samples"] == [10, 20, 30]


def test_present_and_missing():
    lines = ["CONNECTED x", "HB n=10", "HB n=20"]
    rep = judge_lines(lines, [
        {"type": "present", "pattern": "HB n="},
        {"type": "present", "pattern": "TOGGLE", "min_count": 3},
    ], "CONNECTED")
    assert rep.rules[0]["ok"] and rep.rules[0]["count"] == 2
    assert not rep.rules[1]["ok"]
    assert not rep.overall_ok
    ev = rep.render_evidence()
    assert "FAIL" in ev and "TOGGLE" in ev


def test_invalid_rule_fail_closed():
    with pytest.raises(ValueError):
        judge_lines([], [{"type": "threshold", "pattern": "x"}])


# ---- 创作 wasm 执行器（现场编译；无 wasm 工具链 skip）--------------------

SIM_C = r'''
__attribute__((import_module("env"), import_name("ts_log_write")))
int ts_log_write(int ctx, int lvl, const char *msg, int len);
__attribute__((import_module("env"), import_name("ts_time_ms")))
unsigned long long ts_time_ms(void);
static int s_count;

__attribute__((export_name("app_init"))) int app_init(int ctx) {
    (void)ctx; s_count = 0; return 0;
}
__attribute__((export_name("app_tick"))) int app_tick(int ctx) {
    (void)ctx;
    s_count += 1;
    if (s_count % 10 == 0) {
        char buf[32];
        int n = 0;
        unsigned v = (unsigned)s_count;
        do { buf[n++] = (char)('0' + v % 10); v /= 10; } while (v);
        char out[40]; int o = 0;
        const char *pfx = "SIM HB n=";
        for (int i = 0; pfx[i]; i++) out[o++] = pfx[i];
        while (n > 0) out[o++] = buf[--n];
        ts_log_write(0, 3, out, o);
    }
    return 0;
}
__attribute__((export_name("app_evt"))) int app_evt(int ctx, int type) {
    (void)ctx; (void)type; return 0;
}
__attribute__((export_name("health_ping"))) int health_ping(int ctx) {
    (void)ctx; return 42;
}
'''


def _clang_wasm(tmp_path: Path) -> Path | None:
    clang = shutil.which("clang")
    if not clang:
        return None
    src = tmp_path / "sim_app.c"
    src.write_text(SIM_C, encoding="utf-8")
    out = tmp_path / "app.wasm"
    r = subprocess.run(
        [clang, "--target=wasm32", "-O1", "-nostdlib", "-ffreestanding",
         "-fno-builtin", "-Wl,--no-entry", "-Wl,--allow-undefined",
         "-o", str(out), str(src)],
        capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    return out


@pytest.fixture(scope="module")
def sim_wasm(tmp_path_factory) -> Path:
    tmp = tmp_path_factory.mktemp("simapp")
    out = _clang_wasm(tmp)
    if out is None:
        pytest.skip("wasm 工具链（clang→wasm32）不可用")
    return out


def test_wasm_sim_run_and_criteria(sim_wasm: Path):
    sim = wasm_sim.WasmSim(sim_wasm)
    sim.run(ticks=100)
    assert len(sim.log_lines) == 10  # 每 10 tick 一行
    assert sim.log_lines[0] == "SIM HB n=10"
    rep = judge_lines(sim.log_lines, [
        {"type": "present", "pattern": "SIM HB n="},
        {"type": "monotonic", "pattern": r"HB n=(\d+)"},
    ])
    assert rep.overall_ok


def test_run_sim_criteria_pass_and_fail(sim_wasm: Path):
    facts = wasm_sim.run_sim_criteria(
        sim_wasm, {"ticks": 100, "verdict_patterns": ["SIM HB n="],
                   "monotonic": r"HB n=(\d+)"})
    assert facts["writes_n"] == 0 and facts["ticks"] == 100
    with pytest.raises(TaError) as ei:
        wasm_sim.run_sim_criteria(
            sim_wasm, {"ticks": 100,
                       "verdict_patterns": ["NEVER APPEARS"]})
    assert ei.value.code == TA_E_SIM
    # 无判据 = 拒绝假通过
    with pytest.raises(TaError):
        wasm_sim.run_sim_criteria(sim_wasm, {"ticks": 10})


def test_applicability_gate():
    with pytest.raises(wasm_sim.SimSkip):
        wasm_sim.check_applicable(
            {"manifest": {"threads": 2}})
    with pytest.raises(wasm_sim.SimSkip):
        wasm_sim.check_applicable(
            {"manifest": {"needs": {"resources": ["/config/"]}}})
    wasm_sim.check_applicable({"manifest": {"threads": 1, "needs": None}})


def test_creation_sim_runner_skip_note(tmp_path: Path, monkeypatch):
    """skip = ok + facts.sim_skipped 注记（不跑假 sim——DEC-82① 诚实面）。"""
    from tessera_agent.creation.workspace import Workspace
    from tessera_agent.domain.firmware_creation import creation_sim_runner

    ws = Workspace.create(tmp_path, "t-simtest")
    ws.save_project({"schema": 1, "manifest": {"threads": 2, "needs": None}})
    out = creation_sim_runner(ws, {"verdict_patterns": ["X"]})
    assert out.ok and out.facts.get("sim_skipped")


# ---- MCP 面 ---------------------------------------------------------------


def test_mcp_criteria_run_registered():
    from tessera_agent.domain.firmware import FirmwareDomainPack

    pack = FirmwareDomainPack()
    assert "app_criteria_run" in pack.tools
    assert pack.policy.entries.get("app_criteria_run") == "confirm"


def test_scorer_sim_section_true_machine_domain(tmp_path: Path):
    """sim=None 任务（T4/T5）= 真机域注记，不降判定（DEC-82④）。"""
    from tessera_agent.eval import scorer as eval_scorer
    from tessera_agent.eval import suite as eval_suite

    task = eval_suite.select(["T4"])[0]
    chk = eval_scorer._score_sim(task, {"workspace": ""})
    assert chk["ok"] and "真机域" in chk["detail"]
