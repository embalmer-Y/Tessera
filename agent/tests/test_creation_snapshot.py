# SPDX-License-Identifier: Apache-2.0
"""AG5 会话快照测试（LLD-agent-creation-workspace §6/§9：往返一致/STALE 检测/断点续跑/SIGINT）。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tessera_agent.cli.facade import INTERRUPTED, TerminalFrontend, TerminalOptions
from tessera_agent.common.errors import TA_E_ARGS, TA_E_SNAPSHOT_STALE, TaError
from tessera_agent.creation import snapshot
from tessera_agent.creation.loop import (
    IMPLEMENTING,
    PACKAGED,
    CreationLoop,
    PlanItem,
    RoundOutcome,
)
from tessera_agent.creation.workspace import Workspace
from tests.test_creation_loop import DummyVerifier, ScriptedRunner


@pytest.fixture()
def ws(tmp_path: Path) -> Workspace:
    ws = Workspace.create(tmp_path / "ws", "t-500")
    p = ws.project_dir / "main.c"
    p.write_text("int x;\n", encoding="utf-8")
    ws.register_file("main.c")
    return ws


def _loop(ws, runner, verifier=None, **kw) -> CreationLoop:
    return CreationLoop(ws, verifier or DummyVerifier(), runner, "spec-x", **kw)


def test_snapshot_roundtrip_and_file_table(ws):
    loop = _loop(ws, ScriptedRunner([]))
    loop.state = IMPLEMENTING
    loop.round = 3
    loop.plan = [PlanItem("p1", "主逻辑", "done"), PlanItem("p2", "验证")]
    loop.evidence_log.append({"round": 2, "step": "compile", "detail": "boom"})
    path = snapshot.take(loop)
    assert path.name == "snapshot.json"
    snap = snapshot.load(ws)
    assert snap["state"] == IMPLEMENTING and snap["round"] == 3
    assert snap["files"]["main.c"]["lines"] == 1
    assert snap["round_summaries"][0]["event"] == "compile"
    # 往返重建
    loop2 = _loop(ws, ScriptedRunner([]))
    snapshot.restore(loop2, snap)
    assert loop2.round == 3 and loop2.plan[0].status == "done"
    assert loop2.evidence_log[0]["step"] == "resumed"


def test_snapshot_stale_on_external_change(ws):
    loop = _loop(ws, ScriptedRunner([]))
    loop.state, loop.round = IMPLEMENTING, 1
    snapshot.take(loop)
    (ws.project_dir / "main.c").write_text("int y;\n", encoding="utf-8")
    with pytest.raises(TaError) as ei:
        snapshot.load(ws)
    assert ei.value.code == TA_E_SNAPSHOT_STALE
    # 缺文件同理
    (ws.project_dir / "main.c").write_text("int x;\n", encoding="utf-8")
    snapshot.load(ws)  # 恢复原内容 → 校验通过
    (ws.project_dir / "main.c").unlink()
    with pytest.raises(TaError) as ei:
        snapshot.load(ws)
    assert ei.value.code == TA_E_SNAPSHOT_STALE


def test_snapshot_missing_and_corrupt(tmp_path):
    ws = Workspace.create(tmp_path / "ws", "t-501")
    with pytest.raises(TaError) as ei:
        snapshot.load(ws)
    assert ei.value.code == TA_E_ARGS
    (ws.session_dir / "snapshot.json").write_text("{oops", encoding="utf-8")
    with pytest.raises(TaError) as ei:
        snapshot.load(ws)
    assert ei.value.code == TA_E_ARGS


def test_auto_snapshot_during_run_no_tmp_leftover(ws):
    runner = ScriptedRunner([
        RoundOutcome(declared_done=True),   # r1：compile 失败
        RoundOutcome(declared_done=True),   # r2：过 → 打包
    ])
    verifier = DummyVerifier({"compile": ["stderr: undefined X"]})
    result = asyncio.run(_loop(ws, runner, verifier, key_path="/tmp/k").run())
    assert result.state == PACKAGED
    snap = json.loads((ws.session_dir / "snapshot.json").read_text(encoding="utf-8"))
    assert snap["round"] == 2
    assert not list(ws.session_dir.glob("*.tmp"))


def test_interrupt_then_resume_end_to_end(tmp_path):
    ws = Workspace.create(tmp_path / "ws", "t-502")
    p = ws.project_dir / "main.c"
    p.write_text("int x;\n", encoding="utf-8")
    ws.register_file("main.c")

    class InterruptingRunner(ScriptedRunner):
        async def implement(self, prompt: str) -> RoundOutcome:
            if len(self.prompts) >= 1:
                raise KeyboardInterrupt
            return await super().implement(prompt)

    lines: list[str] = []
    fe = TerminalFrontend(
        plan_confirm_fn=lambda items: True, emit=lines.append,
    )
    result = asyncio.run(fe.run(
        "spec", ws, DummyVerifier(),
        InterruptingRunner([RoundOutcome(declared_done=False)]),
        key_path="/tmp/k", options=TerminalOptions(yes=True),
    ))
    assert result.state == INTERRUPTED
    assert "--resume t-502" in result.failure_reason
    snap = snapshot.load(ws)  # 中断路径快照有效
    assert snap["round"] == 1

    # 续跑：restore 后新 runner 完成收敛
    runner2 = ScriptedRunner([RoundOutcome(declared_done=True)])
    verifier = DummyVerifier()
    loop2 = CreationLoop(ws, verifier, runner2, "spec-x", key_path="/tmp/k")
    snapshot.restore(loop2, snap)
    assert loop2.round == 1
    result2 = asyncio.run(loop2.run())
    assert result2.state == PACKAGED and result2.rounds_used == 2
