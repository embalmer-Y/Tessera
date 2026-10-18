# SPDX-License-Identifier: Apache-2.0
"""D2 计划/进度 MCP 外显（DEC-65⑤）：

- note_loop_progress 纯映射矩阵（循环事件 → 进度键，形状稳定）
- Task.snapshot 携带 progress（task_status 同源面）
- task_progress MCP 工具（working 态实时读 + 未知句柄 isError）"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tessera_agent.common.tasks import Task
from tessera_agent.domain.app_chain import note_loop_progress

PKG_ROOT = Path(__file__).resolve().parent.parent


def test_note_loop_progress_full_sequence():
    """事件序列映射：plan→round→evidence→state(repair)→final 全键落位。"""
    progress: dict = {}
    note_loop_progress(progress, "state", {"state": "PLANNING"})
    note_loop_progress(progress, "plan", {"items": [
        {"id": "p1", "desc": "骨架", "status": "pending"},
        {"id": "p2", "desc": "判据", "status": "pending"},
    ]})
    note_loop_progress(progress, "round", {"round": 1, "budget": 12,
                                           "declared_done": False,
                                           "summary": "s"})
    note_loop_progress(progress, "evidence", {"step": "compile", "round": 1})
    note_loop_progress(progress, "evidence", {"step": "face", "round": 1})
    note_loop_progress(progress, "state", {"state": "VERIFYING", "repair": 1,
                                           "repairs": 1})
    note_loop_progress(progress, "final", {"state": "PACKAGED", "rounds": 2})

    assert progress["plan"] == [
        {"id": "p1", "desc": "骨架", "status": "pending"},
        {"id": "p2", "desc": "判据", "status": "pending"},
    ]
    assert progress["round"] == 1
    assert progress["round_budget"] == 12
    assert progress["last_declared_done"] is False
    assert progress["evidence_count"] == 2
    assert progress["last_evidence"] == {"step": "face", "round": 1}
    assert progress["repairing"] is True
    assert progress["loop_state"] == "PACKAGED"
    assert progress["rounds_used"] == 2


def test_note_loop_progress_unknown_kind_and_empty():
    """未知事件静默忽略；空计划照常覆盖（消费面不炸）。"""
    progress: dict = {"round": 3}
    note_loop_progress(progress, "mystery", {"x": 1})
    assert progress == {"round": 3}
    note_loop_progress(progress, "plan", {})
    assert progress["plan"] == []


def test_task_snapshot_carries_progress():
    """snapshot 同源携带（task_status 消费面 additive）。"""
    task = Task(id="t-x", tool="app_develop", args_digest="d")
    task.progress["loop_state"] = "IMPLEMENTING"
    snap = task.snapshot()
    assert snap["progress"] == {"loop_state": "IMPLEMENTING"}
    # 快照为浅拷贝——外部改动不穿透注册表
    snap["progress"]["loop_state"] = "MUTATED"
    assert task.progress["loop_state"] == "IMPLEMENTING"


def test_task_progress_tool_via_mcp(tmp_path):
    """MCP 面：registry 直注任务 → task_progress 读回 working 态进度；
    未知句柄 = isError（TaError 结构化）。"""
    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.gateway.compose import build_app
    from tessera_agent.platform import AppContext

    def unwrap(res):
        data = res.data if hasattr(res, "data") else res
        if isinstance(data, dict) and data.get("isError"):
            raise ToolError(str(data))
        return data

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
        task = Task(id="t-d2", tool="app_develop", args_digest="d")
        task.progress["plan"] = [{"id": "p1", "desc": "x", "status": "done"}]
        task.progress["round"] = 2
        ctx.registry._tasks[task.id] = task
        app = build_app(ctx)
        async with Client(app) as c:
            r = unwrap(await c.call_tool("task_progress",
                                         {"task_id": "t-d2"}))
            assert r["state"] == "working"
            assert r["progress"]["round"] == 2
            assert r["progress"]["plan"][0]["status"] == "done"
            with pytest.raises(ToolError):
                await c.call_tool("task_progress", {"task_id": "t-nope"})

    asyncio.run(main())
