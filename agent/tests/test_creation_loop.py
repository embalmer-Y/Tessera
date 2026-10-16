# SPDX-License-Identifier: Apache-2.0
"""AG3 循环引擎 + 域验证器测试（LLD-A08 §9——零 LLM/零网络；真 clang 编译链）。

两层：① DummyVerifier + 剧本 Runner 的状态机全矩阵（域无关引擎）；
② FirmwareCreationVerifier 真链（多文件聚合编译/面检查/真签名打包）。
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tessera_agent.common.errors import TA_E_ARGS, TA_E_NOT_CONFIGURED, TaError
from tessera_agent.creation.loop import (
    CONVERGED,
    DRAFT,
    FAILED,
    PACKAGED,
    PLANNING,
    VERIFYING,
    CreationLoop,
    PlanItem,
    RoundOutcome,
)
from tessera_agent.creation.verifier import PackageOutcome, VerifyOutcome
from tessera_agent.creation.workspace import Workspace
from tessera_agent.domain.firmware_creation import FirmwareCreationVerifier
from tessera_agent.tools_tsap.wasm_build import compile_project_c

# ---- 剧本桩（域无关引擎面） ------------------------------------------------


class ScriptedRunner:
    """plan → 固定计划；implement → 按剧本出队；记录每轮 prompt。"""

    def __init__(self, outcomes: list[RoundOutcome]):
        self._outcomes = list(outcomes)
        self.prompts: list[str] = []

    async def plan(self, spec, criteria):
        return [PlanItem("p1", "主逻辑"), PlanItem("p2", "验证")]

    async def implement(self, prompt: str) -> RoundOutcome:
        self.prompts.append(prompt)
        return self._outcomes.pop(0)


class DummyVerifier:
    """按 step 脚本出结果；记录调用序。"""

    def __init__(self, script: dict[str, list[VerifyOutcome]] | None = None):
        self.script = {k: list(v) for k, v in (script or {}).items()}
        self.calls: list[str] = []

    def _next(self, step: str) -> VerifyOutcome:
        self.calls.append(step)
        seq = self.script.get(step)
        if not seq:
            return VerifyOutcome(ok=True, detail=f"{step} ok")
        out = seq.pop(0)
        if isinstance(out, str):
            return VerifyOutcome(ok=False, detail=out)
        return out

    def compile(self, ws):
        return self._next("compile")

    def face_check(self, ws):
        return self._next("face_check")

    def simulate(self, ws, scenario):
        return self._next("simulate")

    def package(self, ws, key_path):
        r = self._next("package")
        return PackageOutcome(ok=r.ok, detail=r.detail,
                              package_path="/tmp/x.tsap" if r.ok else "")


@pytest.fixture()
def ws(tmp_path: Path) -> Workspace:
    return Workspace.create(tmp_path / "ws", "t-100")


def _events(loop_events: list) -> dict[str, list]:
    kinds: dict[str, list] = {}
    for kind, data in loop_events:
        kinds.setdefault(kind, []).append(data)
    return kinds


def test_converge_after_compile_failure_with_evidence_feed(ws):
    events: list = []
    runner = ScriptedRunner([
        RoundOutcome(declared_done=True, summary="v1"),
        RoundOutcome(declared_done=True, summary="v2"),
    ])
    verifier = DummyVerifier({"compile": ["clang 编译失败（exit 1）\nstderr: undefined symbol"]})
    loop = CreationLoop(
        ws, verifier, runner, "写温控 APP", criteria=["TCTL DONE t=100"],
        key_path="/tmp/k", on_event=lambda k, d: events.append((k, d)),
    )
    result = pytest.run_loop = _run(loop)
    assert result.state == PACKAGED
    assert result.rounds_used == 2
    # 证据自动回喂：第 2 轮 prompt 含第 1 轮编译失败原文与判据
    assert "undefined symbol" in runner.prompts[1]
    assert "clang 编译失败" in runner.prompts[1]
    assert 'TCTL DONE t=100' in runner.prompts[1]
    assert "上轮验证证据" in runner.prompts[1]
    assert len(result.evidence_log) == 1
    kinds = _events(events)
    assert kinds["state"][0] == {"state": PLANNING}
    states = [s["state"] for s in kinds["state"]]
    assert VERIFYING in states and states[-1] == "PACKAGED"


def test_budget_exhaustion_failed_with_workspace_kept(ws):
    runner = ScriptedRunner([
        RoundOutcome(declared_done=False) for _ in range(12)
    ])
    verifier = DummyVerifier()
    loop = CreationLoop(ws, verifier, runner, "spec", budget=12)
    result = _run(loop)
    assert result.state == FAILED
    assert result.rounds_used == 12
    assert "预算耗尽" in result.failure_reason
    assert Path(result.workspace).is_dir()  # 工作区保留（证据归档）
    assert verifier.calls == []  # 从未声明 done → 验证未触发


def test_face_fail_loops_back_then_converges(ws):
    runner = ScriptedRunner([
        RoundOutcome(declared_done=True),
        RoundOutcome(declared_done=True),
        RoundOutcome(declared_done=True),
    ])
    verifier = DummyVerifier({"face_check": ["导入面越权: [system]"]})
    loop = CreationLoop(ws, verifier, runner, "spec", key_path="/tmp/k")
    result = _run(loop)
    assert result.state == PACKAGED
    assert len(result.evidence_log) == 1
    assert result.evidence_log[0]["step"] == "face_check"
    assert "导入面越权" in runner.prompts[1]


def test_package_failure_fails_with_evidence(ws):
    runner = ScriptedRunner([RoundOutcome(declared_done=True)])
    verifier = DummyVerifier({"package": ["私钥不存在"]})
    loop = CreationLoop(ws, verifier, runner, "spec", key_path="/bad")
    result = _run(loop)
    assert result.state == FAILED
    assert result.evidence_log[-1]["step"] == "package"


def test_sim_skipped_without_scenario_and_honest_without_runner(ws):
    runner = ScriptedRunner([RoundOutcome(declared_done=True)])
    verifier = DummyVerifier()
    loop = CreationLoop(ws, verifier, runner, "spec", key_path="/tmp/k")
    result = _run(loop)
    assert result.state == PACKAGED
    assert "simulate" not in verifier.calls
    # 场景给了但 sim_runner 未注入 → 诚实拒绝（不假日通过）
    fw = FirmwareCreationVerifier(sim_runner=None)
    with pytest.raises(TaError) as ei:
        fw.simulate(ws, {"inputs": []})
    assert ei.value.code == TA_E_NOT_CONFIGURED


def test_converged_without_keypath(ws):
    runner = ScriptedRunner([RoundOutcome(declared_done=True)])
    verifier = DummyVerifier()
    loop = CreationLoop(ws, verifier, runner, "spec")
    result = _run(loop)
    assert result.state == CONVERGED  # 打包由外层显式触发（AG6 接线面）
    assert result.artifact is None


def _run(coro_or_loop):
    import asyncio

    if hasattr(coro_or_loop, "run"):
        return asyncio.run(coro_or_loop.run())
    return asyncio.run(coro_or_loop)  # 既有协程（S8 repair 等）


# ---- FirmwareCreationVerifier 真链（真 clang） ------------------------------

_MULTI_FILES = {
    "include/util.h": "int util_half(int v);\n",
    "main.c": (
        '#include "include/util.h"\n'
        "extern int ts_log_write(int ctx, int lvl, const char* msg, int len);\n"
        "int health_ping(void) { return 0; }\n"
        "int app_init(int ctx) { return 0; }\n"
        "int app_tick(void) { ts_log_write(0, 1, \"tick\", 4); return util_half(84); }\n"
        "int app_evt(int v) { return 0; }\n"
    ),
    "util.c": '#include "include/util.h"\nint util_half(int v) { return v / 2; }\n',
}
_EXPORTS = ["health_ping", "app_init", "app_tick", "app_evt"]


def _project_ws(tmp_path: Path) -> Workspace:
    ws = Workspace.create(tmp_path / "ws", "t-200", app_id="demo.multi")
    project = ws.load_project()
    project["files"] = sorted(_MULTI_FILES)
    project["exports"] = list(_EXPORTS)
    project["manifest"] = {
        "app_id": "demo.multi", "app_ver": "1.0.0", "min_fw_ver": "0.1.0",
        "caps": [], "stack_kb": 4, "heap_kb": 16, "exports": list(_EXPORTS),
    }
    ws.save_project(project)
    for name, content in _MULTI_FILES.items():
        p = ws.project_dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return ws


def test_compile_project_c_multi_file_with_internal_header(tmp_path):
    out = compile_project_c(
        _MULTI_FILES, str(tmp_path / "out"), [str(tmp_path)],
        exports=_EXPORTS,
    )
    assert out["exports"] == sorted(_EXPORTS)
    assert out["imports"] == ["ts_log_write"]
    assert out["deterministic"] is True


def test_compile_project_c_gates(tmp_path):
    roots = [str(tmp_path)]
    # 系统 include 拒
    with pytest.raises(TaError) as ei:
        compile_project_c(
            {"a.c": "#include <stdio.h>\nint health_ping(void){return 0;}\n"},
            str(tmp_path / "o1"), roots)
    assert ei.value.code == TA_E_ARGS
    # 引号包含越出文件表拒
    with pytest.raises(TaError) as ei:
        compile_project_c(
            {"a.c": '#include "../../etc/passwd"\nint health_ping(void){return 0;}\n'},
            str(tmp_path / "o2"), roots)
    assert ei.value.code == TA_E_ARGS
    # 缺导出符号 = 面检查一票拒（--allow-undefined 为 natives 未定义所必需，
    # 链接期不可区分——fail-closed 由面门承载，与单文件链同型）
    with pytest.raises(TaError) as ei:
        compile_project_c(
            {"a.c": "int health_ping(void){return 0;}\n"},
            str(tmp_path / "o3"), roots, exports=["app_init"])
    assert ei.value.code == 11  # TA_E_TSAP
    assert "缺少必需导出" in ei.value.message
    assert "app_init" in str(ei.value.detail)


def test_firmware_verifier_full_chain(tmp_path):
    ws = _project_ws(tmp_path)
    verifier = FirmwareCreationVerifier()
    c = verifier.compile(ws)
    assert c.ok, c.detail
    f = verifier.face_check(ws)
    assert f.ok, f.detail
    # 真签名打包（32B raw 密钥）
    key = tmp_path / "k.key"
    key.write_bytes(os.urandom(32))
    pkg = verifier.package(ws, str(key))
    assert pkg.ok, pkg.detail
    assert pkg.package_path.endswith(".tsap")
    # 面检查对未编译工作区拒绝
    ws2 = Workspace.create(tmp_path / "ws2", "t-201")
    assert verifier.face_check(ws2).ok is False
    assert verifier.compile(ws2).ok is False  # 空工程（无 .c）


def test_firmware_verifier_compile_evidence_carries_stderr(tmp_path):
    ws = _project_ws(tmp_path)
    # 注入坏源（缺分号）→ compile 返回 ok=False 且 detail 含 clang stderr 原文
    (ws.project_dir / "util.c").write_text(
        '#include "include/util.h"\nint util_half(int v) { return v / 2 }\n',
        encoding="utf-8",
    )
    verifier = FirmwareCreationVerifier()
    outcome = verifier.compile(ws)
    assert outcome.ok is False
    assert "expected" in outcome.detail  # clang 诊断原文回喂


# ---- S8（P1-5 · HLD-agent §4）：部署判据 miss → 修复轮自动回注 --------------


def test_s8_repair_round_reconverges_and_repacks(ws):
    """PACKAGED → repair(真机证据) → 修复轮（证据经上轮小结回喂）→ 再收敛
    再打包（S8_REPAIR_MAX 内）。"""
    events: list = []
    runner = ScriptedRunner([
        RoundOutcome(declared_done=True, summary="v1"),  # 首收敛
        RoundOutcome(declared_done=True, summary="fix-1"),  # 修复轮
    ])
    verifier = DummyVerifier()
    loop = CreationLoop(ws, verifier, runner, "spec",
                        criteria=["APP DONE"], key_path="/tmp/k",
                        on_event=lambda k, d: events.append((k, d)))
    assert _run(loop).state == PACKAGED

    r2 = _run(loop.repair("category=criteria-miss evidence=['AK FAIL install r=-9']"))

    assert r2.state == PACKAGED
    assert len(runner.prompts) == 2, "修复轮实际执行（prompt 链推进）"
    assert "criteria-miss" in runner.prompts[1], "真机诊断证据经上轮小结回喂"
    assert "AK FAIL install r=-9" in runner.prompts[1]
    assert r2.artifact is not None and r2.artifact.ok
    kinds = _events(events)
    assert any(d.get("repair") == 1 for d in kinds["state"]), "修复轮事件可观测"


def test_s8_repair_budget_exhausts_to_failed(ws):
    """修复窗超限（S8_REPAIR_MAX=2）= FAILED（证据归档语义）。"""
    runner = ScriptedRunner([
        RoundOutcome(declared_done=True, summary="v1"),
        RoundOutcome(declared_done=True, summary="fix-1"),
        RoundOutcome(declared_done=True, summary="fix-2"),
    ])
    loop = CreationLoop(ws, DummyVerifier(), runner, "spec",
                        key_path="/tmp/k")
    assert _run(loop).state == PACKAGED
    assert _run(loop.repair("miss-1")).state == PACKAGED
    assert _run(loop.repair("miss-2")).state == PACKAGED, "第 2 窗仍可修"
    r3 = _run(loop.repair("miss-3"))
    assert r3.state == FAILED, "第 3 次修复请求 = 窗耗尽（S8_REPAIR_MAX=2）"


def test_s8_repair_rejects_non_packaged(ws):
    """非 PACKAGED 态 repair = 拒（状态机保形——DRAFT 不可修复轮）。"""
    runner = ScriptedRunner([])
    loop = CreationLoop(ws, DummyVerifier(), runner, "spec")
    r = _run(loop.repair("early"))
    assert r.state == DRAFT, "DRAFT 原态保持"
