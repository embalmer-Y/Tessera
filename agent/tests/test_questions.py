# SPDX-License-Identifier: Apache-2.0
"""D7 问询双向化（DEC-67①）：

- QuestionBroker 单元（实体/枚举域 fail-closed/超时缺省语义/已答不可再答）
- MCP 面（sys_pending_questions / sys_answer——isError 路径）
- loop 异步回调（async on_event 被 await——plan_confirm 桥的前提）
- plan_confirm 桥（loop plan 事件 → 问询实体 → abort = 结构化终止）"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tessera_agent.common.errors import TA_E_ARGS, TA_E_POLICY, TA_E_TIMEOUT, TaError
from tessera_agent.creation.loop import CONVERGED, CreationLoop, RoundOutcome
from tessera_agent.creation.workspace import Workspace
from tessera_agent.gateway.questions import QuestionBroker

PKG_ROOT = Path(__file__).resolve().parent.parent


def _unwrap(res):
    data = res.data if hasattr(res, "data") else res
    if isinstance(data, dict) and data.get("isError"):
        raise ToolError(str(data))
    return data


# ---- Broker 单元 -----------------------------------------------------------

def test_broker_ask_answer_happy_path():
    b = QuestionBroker()
    q = b.ask("计划确认？", ["proceed", "abort"], default="abort",
              context="app_develop")
    assert b.list_pending()[0]["question_id"] == q.id
    assert b.list_pending()[0]["default"] == "abort"
    assert b.answer(q.id, "proceed") == {"question_id": q.id,
                                         "answer": "proceed"}
    # pending 移除时机 = wait 消费（ApprovalBroker 同型——应答对列举面
    # 保持可见至取用，避免 UI 竞态）
    assert asyncio.run(b.wait(q)) == "proceed"
    assert b.list_pending() == []


def test_broker_answer_enum_failclosed():
    b = QuestionBroker()
    q = b.ask("选一个", ["a", "b"])
    with pytest.raises(TaError) as ei:
        b.answer(q.id, "c")
    assert ei.value.code == TA_E_ARGS
    with pytest.raises(TaError):
        b.answer("q-nope", "a")  # 不存在
    b.answer(q.id, "a")
    with pytest.raises(TaError):
        b.answer(q.id, "b")  # 已答不可再答（同一实体单次应答）


def test_broker_ask_domain_validation():
    b = QuestionBroker()
    with pytest.raises(TaError):
        b.ask("空选项", [])
    with pytest.raises(TaError):
        b.ask("缺省越域", ["a", "b"], default="c")


def test_broker_wait_timeout_semantics():
    b = QuestionBroker()
    q_default = b.ask("有缺省", ["yes", "no"], default="no")
    assert asyncio.run(b.wait(q_default, timeout_s=1)) == "no"
    q_nod = b.ask("无缺省", ["yes", "no"])
    with pytest.raises(TaError) as ei:
        asyncio.run(b.wait(q_nod, timeout_s=1))
    assert ei.value.code == TA_E_TIMEOUT


# ---- MCP 面 ----------------------------------------------------------------

def test_question_tools_via_mcp(tmp_path):
    """sys_pending_questions 列举 + sys_answer 应答 + isError 路径。"""
    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.gateway.compose import build_app
    from tessera_agent.platform import AppContext

    async def main():
        cfg = AgentConfig(
            workspace_repo=PKG_ROOT.parent,
            west_workspace=PKG_ROOT.parent,
            west_venv_python=PKG_ROOT.parent / "agent" / "nofake",
            audit_dir=tmp_path / "audit",
            default_model="ollama:test",
            context_window=32_000,
            router_locator="tcp/127.0.0.1:7447",
        )
        ctx = AppContext(cfg=cfg, budget=ContextBudget(32_000))
        q = ctx.questions.ask("继续吗？", ["proceed", "abort"],
                              default="abort", context="test")
        app = build_app(ctx)
        async with Client(app) as c:
            lst = _unwrap(await c.call_tool("sys_pending_questions", {}))
            assert lst["pending"][0]["question_id"] == q.id
            r = _unwrap(await c.call_tool(
                "sys_answer", {"question_id": q.id, "answer": "proceed"}))
            assert r["answer"] == "proceed"
            assert q.id in [p["question_id"] for p in _unwrap(
                await c.call_tool("sys_pending_questions", {}))["pending"]]
            with pytest.raises(ToolError):
                await c.call_tool("sys_answer",
                                  {"question_id": "q-nope", "answer": "a"})
            q2 = ctx.questions.ask("再来", ["x", "y"])
            with pytest.raises(ToolError):
                await c.call_tool("sys_answer",
                                  {"question_id": q2.id, "answer": "z"})

    asyncio.run(main())


# ---- loop 异步回调 + plan_confirm 桥 ---------------------------------------

class _ScriptedRunner:
    """plan → 固定计划；implement → 单轮收敛。"""

    def __init__(self):
        self.prompts: list[str] = []

    async def plan(self, spec, criteria):
        from tessera_agent.creation.loop import PlanItem
        return [PlanItem("p1", "主逻辑")]

    async def implement(self, prompt: str) -> RoundOutcome:
        self.prompts.append(prompt)
        return RoundOutcome(declared_done=True, summary="v1")


class _OkVerifier:
    """CreationVerifier 协议签名（verifier.py §36）：compile/face_check(ws)、
    simulate(ws, scenario)、package(ws, key_path)。"""

    def compile(self, ws):
        from tessera_agent.creation.verifier import VerifyOutcome
        return VerifyOutcome(ok=True, detail="ok")

    def face_check(self, ws):
        from tessera_agent.creation.verifier import VerifyOutcome
        return VerifyOutcome(ok=True, detail="ok")

    def simulate(self, ws, scenario):
        from tessera_agent.creation.verifier import VerifyOutcome
        return VerifyOutcome(ok=True, detail="ok")

    def package(self, ws, key_path):
        from tessera_agent.creation.verifier import PackageOutcome
        return PackageOutcome(ok=True, detail="ok", artifact_path=None,
                              facts={})


def test_loop_awaits_async_on_event(tmp_path):
    """async on_event 被循环 await（D7 桥接前提）；完成序在事件后。"""
    events: list[str] = []

    async def cb(kind: str, data: dict) -> None:
        await asyncio.sleep(0.01)
        events.append(f"done:{kind}")

    loop = CreationLoop(Workspace.create(tmp_path / "ws", "t-d7"),
                        _OkVerifier(), _ScriptedRunner(), "spec", on_event=cb)
    result = asyncio.run(loop.run())
    # 无 key_path = CONVERGED 即终态（AG3：打包外层显式触发）
    assert result.state == CONVERGED
    assert events and all(e.startswith("done:") for e in events)


def test_plan_confirm_bridge_abort_and_proceed(tmp_path):
    """plan_confirm 桥（与 _app_develop_loop._on_event 同构的最小验证）：
    abort = 结构化终止（state=ABORTED）；proceed = 收敛照常。"""

    # abort 路径：应答 abort → 结构化终止（超时缺省语义由 broker 单测覆盖）
    b2 = QuestionBroker()
    events2: list[str] = []

    def on_event2(kind: str, data: dict):
        async def inner():
            events2.append(kind)
            if kind == "plan":
                q = b2.ask("计划确认？", ["proceed", "abort"], default="abort")
                b2.answer(q.id, "abort")
                ans = await b2.wait(q)
                assert ans == "abort"
                raise TaError(TA_E_POLICY, "计划被拒绝", domain="app_develop",
                              detail={"state": "ABORTED"})
        return inner()

    loop2 = CreationLoop(Workspace.create(tmp_path / "ws2", "t-d7b"),
                         _OkVerifier(), _ScriptedRunner(), "spec",
                         on_event=on_event2, budget=3)
    # 回调异常从 run() 直接传播（MCP 路径 = 任务结构化失败，detail 携带
    # state=ABORTED——app_chain 侧 TaError 语义）
    with pytest.raises(TaError) as ei:
        asyncio.run(loop2.run())
    assert ei.value.code == TA_E_POLICY
    assert ei.value.detail.get("state") == "ABORTED"
    assert "计划被拒绝" in str(ei.value)

    # proceed 路径：应答 proceed → 收敛照常
    b3 = QuestionBroker()

    def on_event3(kind: str, data: dict):
        async def inner():
            if kind == "plan":
                q = b3.ask("计划确认？", ["proceed", "abort"])
                b3.answer(q.id, "proceed")
                await b3.wait(q)
        return inner()

    loop3 = CreationLoop(Workspace.create(tmp_path / "ws3", "t-d7c"),
                         _OkVerifier(), _ScriptedRunner(), "spec",
                         on_event=on_event3)
    result3 = asyncio.run(loop3.run())
    assert result3.state == CONVERGED
