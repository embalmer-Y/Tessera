# SPDX-License-Identifier: Apache-2.0
"""W1 web 渠道（LLD-A11 §5 测试口径）：

- /web 静态挂载（index/app.js 可达 + Content-Type + ES import 路径全存在）
- /events 路由注册 + SSE 帧语义（build_frame 差分：日志新行/状态签名变化）
- MCP 面不受组装影响（build_app 照常挂 sys_ping）"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

from tessera_agent.gateway.web import WEB_DIR, build_frame, event_stream, mount_web

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


def test_build_frame_diff_semantics(tmp_path):
    """差分帧：无任务 = 单空态帧；日志新行/进度变化/问询出现 各自发帧；
    签名不变不重复发。"""
    async def main():
        ctx, _ = _ctx(tmp_path)
        cursor = {"log_idx": 0, "sig": ""}
        # 无任务：首帧空态，此后静默
        assert build_frame(ctx, cursor, None)[0]["kind"] == "state"
        assert build_frame(ctx, cursor, None) == []

        task = await ctx.registry.create("app_develop", {}, lambda t: {"ok": True})
        task.log.append("AK0 start")
        task.log.append("[tsi] info rc=0")
        task.progress["loop_state"] = "PLANNING"
        frames = build_frame(ctx, cursor, task.id)
        kinds = [f["kind"] for f in frames]
        assert "task_log" in kinds and "state" in kinds
        log_frame = next(f for f in frames if f["kind"] == "task_log")
        assert log_frame["lines"] == ["AK0 start", "[tsi] info rc=0"]
        # 无变化 = 静默
        assert build_frame(ctx, cursor, task.id) == []
        # 进度变化 → 状态帧
        task.progress["loop_state"] = "IMPLEMENTING"
        frames2 = build_frame(ctx, cursor, task.id)
        assert [f["kind"] for f in frames2] == ["state"]
        assert frames2[0]["progress"]["loop_state"] == "IMPLEMENTING"
        # 问询出现 → 状态帧（pending 快照入帧）
        ctx.questions.ask("继续？", ["proceed", "abort"], default="abort")
        frames3 = build_frame(ctx, cursor, task.id)
        st = next(f for f in frames3 if f["kind"] == "state")
        assert st["questions"][0]["question_id"].startswith("q-")
        # 审批出现 → 状态帧
        ctx.approvals.request("app_deploy", {}, reason="strict")
        frames4 = build_frame(ctx, cursor, task.id)
        st4 = next(f for f in frames4 if f["kind"] == "state")
        assert st4["approvals"][0]["tool"] == "app_deploy"

    asyncio.run(main())


def test_event_stream_yields_frames(tmp_path):
    """SSE 字节流：帧 = data: JSON 形态；stop_after 注入收口（测试面）。"""
    async def main():
        ctx, _ = _ctx(tmp_path)
        await ctx.registry.create("app_develop", {}, lambda t: {"ok": True})
        out = []
        async for chunk in event_stream(ctx, None, stop_after=1):
            out.append(chunk)
        assert out and out[0].startswith("data: ")
        frame = json.loads(out[0][6:].strip())
        assert frame["kind"] in ("state", "task_log")

    asyncio.run(main())


def test_mcp_surface_unaffected(tmp_path):
    """组装不破坏 MCP 面：sys_ping 经 build_app 照常应答（FastMCP Client 直连）。"""
    from fastmcp import Client

    async def main():
        ctx, app = _ctx(tmp_path)
        async with Client(app) as c:
            r = await c.call_tool("sys_ping", {})
            data = r.data if hasattr(r, "data") else r
            assert data["pong"] is True
            # 钩子链缺省空 = 行为不变（D4 缺省链已在 ctx）
            assert list(ctx.hooks.rules) == []

    asyncio.run(main())
