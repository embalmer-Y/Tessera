# SPDX-License-Identifier: Apache-2.0
"""AG4 终端门面测试（LLD-A09 §8——渲染纯函数 + 门面交互钩子，零 LLM/零网络）。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from tessera_agent.cli.facade import ABORTED, TerminalFrontend, TerminalOptions
from tessera_agent.cli.render import render_event, render_final, render_plan
from tessera_agent.creation.loop import PACKAGED, PlanItem, RoundOutcome
from tessera_agent.creation.workspace import Workspace
from tests.test_creation_loop import DummyVerifier, ScriptedRunner

# ---- 渲染纯函数 ------------------------------------------------------------


def test_render_plan_and_round():
    text = render_plan([
        {"id": "p1", "desc": "主逻辑", "status": "done"},
        {"id": "p2", "desc": "验证", "status": "in_progress"},
    ])
    assert "[x] p1: 主逻辑" in text and "[~] p2: 验证" in text
    line = render_event("round", {"round": 3, "budget": 12,
                                  "declared_done": True, "summary": "修好滞回"})
    assert "3/12" in line and "完成声明" in line


def test_render_final_report():
    class _Art:
        ok = True
        package_path = "/tmp/demo-1.0.0.tsap"

    class _R:
        state = PACKAGED
        rounds_used = 4
        failure_reason = ""
        evidence_log = []
        artifact = _Art()
        workspace = "/tmp/ws/t-1"
        plan = []

    text = render_final(_R())
    assert "PACKAGED" in text and "/tmp/demo-1.0.0.tsap" in text
    assert "工作区" in text


# ---- 门面 ------------------------------------------------------------------


@pytest.fixture()
def env(tmp_path: Path):
    ws = Workspace.create(tmp_path / "ws", "t-300")
    runner = ScriptedRunner([
        RoundOutcome(declared_done=True, summary="v1"),
    ])
    verifier = DummyVerifier()
    lines: list[str] = []
    return ws, runner, verifier, lines


def _run_facade(frontend, ws, runner, verifier, **kw):
    return asyncio.run(frontend.run(
        "写温控 APP", ws, verifier, runner,
        criteria=["TCTL DONE"], key_path="/tmp/k", **kw,
    ))


def test_facade_happy_path_renders_and_confirms(env):
    ws, runner, verifier, lines = env
    confirmed: list[list[PlanItem]] = []

    def on_plan(items: list[PlanItem]) -> bool:
        confirmed.append(items)
        return True

    fe = TerminalFrontend(plan_confirm_fn=on_plan, emit=lines.append)
    result = _run_facade(fe, ws, runner, verifier)
    assert result.state == PACKAGED
    assert len(confirmed) == 1 and confirmed[0][0].id == "p1"
    joined = "\n".join(lines)
    assert "PLANNING" in joined and "[ ] p1" in joined
    assert "终报" in joined and "TCTL" not in joined  # 判据在 prompt 不在渲染


def test_facade_plan_rejected_aborts(env):
    ws, runner, verifier, lines = env
    fe = TerminalFrontend(plan_confirm_fn=lambda items: False, emit=lines.append)
    result = _run_facade(fe, ws, runner, verifier)
    assert result.state == ABORTED
    assert "拒绝" in result.failure_reason
    assert verifier.calls == []  # 计划被拒 → 未进入实现/验证


def test_facade_yes_mode_skips_confirm_and_denies_approval(env):
    ws, runner, verifier, lines = env
    asked: list[tuple[str, list[str]]] = []
    fe = TerminalFrontend(
        plan_confirm_fn=lambda items: (_ for _ in ()).throw(AssertionError("不应被问")),
        question_fn=lambda q, opts: asked.append((q, opts)) or opts[0],
        approval_fn=lambda i, t, r: (_ for _ in ()).throw(AssertionError("不应被问")),
        emit=lines.append,
    )
    result = _run_facade(fe, ws, runner, verifier, options=TerminalOptions(yes=True))
    assert result.state == PACKAGED  # 循环本身无 strict 步——不受影响
    assert fe.ask_question("歧义?", ["A", "B"], yes=True) == "A"
    assert fe.resolve_approval("a-1", "deploy_push_app", "部署", yes=True) == ("deny", "")


def test_facade_json_mode_streams_events(env):
    ws, runner, verifier, lines = env
    fe = TerminalFrontend(emit=lines.append)
    result = _run_facade(
        fe, ws, runner, verifier, options=TerminalOptions(yes=True, json_mode=True),
    )
    assert result.state == PACKAGED
    events = [json.loads(line) for line in lines]
    kinds = [e["event"] for e in events]
    assert kinds[0] == "state" and "plan" in kinds and "final" in kinds
    plan_ev = next(e for e in events if e["event"] == "plan")
    assert plan_ev["items"][0]["id"] == "p1"


def test_facade_approval_injected_path(env):
    ws, runner, verifier, lines = env
    fe = TerminalFrontend(
        approval_fn=lambda i, t, r: ("allow", "tok-123"),
        emit=lines.append,
    )
    assert fe.resolve_approval("a-9", "tsap_keygen", "密钥生成", yes=False) == \
        ("allow", "tok-123")
