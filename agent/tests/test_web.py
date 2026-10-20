# SPDX-License-Identifier: Apache-2.0
"""W2 web 渠道（LLD-A14 §8 测试口径；W1 静态/路由/URL 纪律沿用）：

- /web 静态挂载（index/app.js 可达 + Content-Type + ES import 路径全存在）
- /events v2：EventBus 直推（快照首帧/task.created 任务帧/Last-Event-ID 续传）
- phase 派发表（11 态单源）
- MCP 面不受组装影响（build_app 照常挂 sys_ping）"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

from tessera_agent.common.events import EventBus
from tessera_agent.gateway.web import (
    WEB_DIR,
    _event_frame,
    build_snapshot,
    derive_phase,
    event_stream,
    mount_web,
)

PKG_ROOT = Path(__file__).resolve().parent.parent


def _ctx(tmp_path):
    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    cfg = AgentConfig(
        workspace_repo=PKG_ROOT.parent,
        west_workspace=PKG_ROOT.parent,
        west_venv_python=PKG_ROOT.parent / "agent" / "nofake",
        audit_dir=tmp_path / "audit",
        default_model="ollama:test",
        context_window=32_000,
        router_locator="tcp/127.0.0.1:7447",
    )
    from tessera_agent.gateway.compose import build_app

    ctx = AppContext(cfg=cfg, budget=ContextBudget(32_000))
    return ctx, build_app(ctx)


def test_web_static_mount(tmp_path):
    """/web 单页与 ES modules 可达；index 引用的资源与 import 路径全存在。"""
    async def main():
        ctx, mcp = _ctx(tmp_path)
        asgi = mount_web(mcp.http_app(path="/mcp"), ctx)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=asgi), base_url="http://t"
        ) as c:
            r = await c.get("/web/")
            assert r.status_code == 200
            assert "text/html" in r.headers["content-type"]
            js = await c.get("/web/app.js")
            assert js.status_code == 200
            assert "javascript" in js.headers["content-type"]
            css = await c.get("/web/tokens.css")
            assert css.status_code == 200
            # index 引用的静态资源存在性
            for ref in re.findall(r'(?:src|href)="([^"]+)"', r.text):
                assert (WEB_DIR / ref).exists(), ref
            # ES import 路径解析（相对，无第三方——零供应链面）
            for mod in re.findall(r'from\s+"(\./[^"]+)"', js.text):
                assert (WEB_DIR / mod[2:]).exists(), mod

    asyncio.run(main())


def test_events_route_registered(tmp_path):
    """/events 路由在组装后注册（SSE 推送面）。"""
    ctx, mcp = _ctx(tmp_path)
    asgi = mount_web(mcp.http_app(path="/mcp"), ctx)
    paths = {getattr(r, "path", None) for r in asgi.router.routes}
    assert "/events" in paths
    assert "/mcp" in paths


def test_web_urls_are_root_absolute(tmp_path):
    """前端 new URL 首参必须根绝对（"/..."）——/web/ 挂载下相对解析 =
    /web/mcp（StaticFiles 405）与 /web/events（404），W1 人工验收实抓。"""
    for name in ("app.js", "mcp.js"):
        src = (WEB_DIR / name).read_text(encoding="utf-8")
        for target in re.findall(r'new URL\(\s*"([^"]+)"', src):
            assert target.startswith("/"), f"{name}: new URL(\"{target}\") 非根绝对"


# ---- phase 派发表（11 态单源——LLD-A14 §4.2） ------------------------------

def test_derive_phase_priority():
    assert derive_phase(None, {}, [], []) == "idle"
    # 等待人最高优先
    assert derive_phase("working", {}, [{}], []) == "awaiting_confirm"
    assert derive_phase("working", {}, [], [{}]) == "awaiting_approval"
    # 终态
    assert derive_phase("completed", {}, [], []) == "done"
    assert derive_phase("failed", {}, [], []) == "failed"
    # 循环阶段（repairing 优先于 implementing）
    assert derive_phase("working", {"loop_state": "implementing",
                                    "repairing": True}, [], []) == "repairing"
    assert derive_phase("working", {"loop_state": "PLANNING"}, [], []) \
        in ("planning", "implementing")
    # working 无循环信息 = 部署/执行域
    assert derive_phase("working", {}, [], []) == "deploying"


# ---- /events v2：直推 + 快照 + 续传 -----------------------------------------

def _frames(chunk: bytes) -> list[dict]:
    """SSE chunk → JSON 帧列表（id: 前缀行跳过）。"""
    out = []
    for line in chunk.decode("utf-8").splitlines():
        if line.startswith("data: "):
            out.append(json.loads(line[6:]))
    return out


def test_event_stream_snapshot_first(tmp_path):
    """SSE v2 首两帧 = 快照 + 任务列表（data: JSON 形态）。"""
    async def main():
        ctx, _ = _ctx(tmp_path)
        await ctx.registry.create("app_develop", {}, lambda t: {"ok": True})
        out = []
        async for chunk in event_stream(ctx, None, stop_after=2):
            out.append(chunk)
        assert len(out) == 2
        snap = _frames(out[0])[0]
        assert snap["kind"] == "state" and "phase" in snap
        tasks = _frames(out[1])[0]
        assert tasks["kind"] == "tasks" and tasks["tasks"][0]["tool"] == "app_develop"

    asyncio.run(main())


def test_event_stream_pushes_bus_events(tmp_path):
    """总线事件直推：日志行经 task.log 事件成帧（v1 轮询差分删除）。"""
    async def main():
        ctx, _ = _ctx(tmp_path)
        task = await ctx.registry.create("app_develop", {},
                                         lambda t: {"ok": True})
        out = []

        async def consume():
            async for chunk in event_stream(ctx, task.id, stop_after=4):
                out.append(chunk)

        consumer = asyncio.create_task(consume())
        await asyncio.sleep(0.2)          # 快照/任务帧先落
        ctx.registry.append_log(task, "[tsi] info rc=0")
        ctx.registry.note_progress(task, {"loop_state": "IMPLEMENTING"})
        await asyncio.wait_for(consumer, timeout=5)
        frames = [f for c in out for f in _frames(c)]
        kinds = [f["kind"] for f in frames]
        assert "task_log" in kinds and "state" in kinds
        log_frame = next(f for f in frames if f["kind"] == "task_log")
        assert log_frame["lines"] == ["[tsi] info rc=0"]
        st = next(f for f in frames if f["kind"] == "state"
                  and f.get("progress", {}).get("loop_state") == "IMPLEMENTING")
        assert st["progress"]["loop_state"] == "IMPLEMENTING"

    asyncio.run(main())


def test_event_frame_question_approval_mapping(tmp_path):
    """/events 事件映射：问答/审批开关事件成帧；resync → 快照。"""
    async def main():
        ctx, _ = _ctx(tmp_path)
        bus = ctx.events
        q = ctx.questions.ask("继续？", ["proceed", "abort"], default="abort")
        evs = bus.replay(0)
        frames = [_event_frame(ctx, None, e) for e in evs]
        opened = next(f for f in frames if f and f["kind"] == "questions"
                      and f.get("opened"))
        assert opened["question_id"] == q.id
        ctx.questions.answer(q.id, "proceed")
        evs = bus.replay(evs[-1].seq)
        closed = next(f for f in [_event_frame(ctx, None, e) for e in evs]
                      if f and f["kind"] == "questions" and not f.get("opened"))
        assert closed["answer"] == "proceed"
        # resync → 快照
        snap = _event_frame(ctx, None, EventBus().publish("resync", {}))
        assert snap["kind"] == "state"

    asyncio.run(main())


def test_registry_question_approval_bus_zero_change_without_bus(
        tmp_path, monkeypatch):
    """对照组（LLD-A14 §3.2 纪律）：bus=None 缺省构造 = 行为逐字节等价
    （问答/审批/日志全功能可用，仅无事件）。"""

    from tessera_agent.common.tasks import TaskRegistry
    from tessera_agent.gateway.approvals import APPROVAL_TOKEN_ENV, ApprovalBroker
    from tessera_agent.gateway.questions import QuestionBroker

    monkeypatch.setenv(APPROVAL_TOKEN_ENV, "tok")
    reg = TaskRegistry()       # bus 缺省 None
    qb = QuestionBroker()
    ab = ApprovalBroker()
    assert reg._bus is None and qb._bus is None and ab._bus is None
    q = qb.ask("Q?", ["a", "b"], default="a")
    assert qb.answer(q.id, "a")["answer"] == "a"
    a = ab.request("t", {}, reason="r")
    ab.decide(a.id, "deny", token="tok")
    assert a.decision == "deny"
    task = asyncio.run(reg.create("x", {}, lambda t: 1))
    reg.append_log(task, "line")
    reg.note_progress(task, {"k": 1})
    assert task.progress["k"] == 1 and "last_activity_ts" in task.progress


def test_mcp_surface_unaffected(tmp_path):
    """组装不破坏 MCP 面：sys_ping/sys_tasks 经 build_app 照常应答。"""
    from fastmcp import Client

    async def main():
        ctx, app = _ctx(tmp_path)
        async with Client(app) as c:
            r = await c.call_tool("sys_ping", {})
            data = r.data if hasattr(r, "data") else r
            assert data["pong"] is True
            r2 = await c.call_tool("sys_tasks", {})
            d2 = r2.data if hasattr(r2, "data") else r2
            assert d2["total"] == 0
            assert list(ctx.hooks.rules) == []

    asyncio.run(main())


def test_snapshot_carries_log_replay(tmp_path):
    """W2 验收修复③：快照帧携带历史日志（刷新/切任务不丢会话）。"""
    async def main():
        ctx, _ = _ctx(tmp_path)
        task = await ctx.registry.create("app_develop", {}, lambda t: {"ok": True})
        ctx.registry.append_log(task, "line-one")
        ctx.registry.append_log(task, "line-two")
        snap = build_snapshot(ctx, task.id)
        assert snap["log"] == ["line-one", "line-two"]
        # 无任务态（独立 ctx，无回退对象）无 log 键
        ctx2, _ = _ctx(tmp_path / "c2")
        assert "log" not in build_snapshot(ctx2, None)

    asyncio.run(main())
