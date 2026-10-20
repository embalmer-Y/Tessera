# SPDX-License-Identifier: Apache-2.0
"""A5 外部 MCP server 桥接（LLD-A15）测试：内存 server 全链（list/call/
strict 审批 deny+allow）+ 名字净化 + config 解析 + 组合根注册事实。"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

PKG_ROOT = Path(__file__).resolve().parent.parent


async def _tool_names(app):
    from fastmcp import Client

    async with Client(app) as c:
        return await c.list_tools()


def _demo_server():
    from fastmcp import FastMCP

    srv = FastMCP("demo-ext")

    @srv.tool
    def greet(who: str) -> str:
        """问候。"""
        return f"hello {who}"

    return srv


def _env(tmp_path, monkeypatch, token: str | None = None):
    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    if token:
        monkeypatch.setenv("TESSERA_AGENT_APPROVAL_TOKEN", token)
    cfg = AgentConfig(
        workspace_repo=PKG_ROOT.parent, west_workspace=PKG_ROOT.parent,
        west_venv_python=PKG_ROOT.parent / "agent" / "nofake",
        audit_dir=tmp_path / "audit", default_model="ollama:test",
        context_window=32_000, router_locator="tcp/127.0.0.1:7447",
        mcp_clients={"demo": {"_inline": _demo_server()}},
    )
    return AppContext(cfg=cfg, budget=ContextBudget(32_000))


def test_sanitize_server_name():
    from tessera_agent.gateway.mcp_clients import sanitize_server

    assert sanitize_server("my-srv.1") == "my_srv_1"
    with pytest.raises(Exception, match="名字非法"):
        sanitize_server("///")


def test_config_parse_mcp_clients(tmp_path):
    """config [mcp_clients] 解析：表项进 AgentConfig，非表项跳过。"""
    from tessera_agent.common.config import load_config

    p = tmp_path / "config.toml"
    p.write_text(
        "[providers]\ndefault_model = \"ollama:test\"\n"
        "[agent]\nworkspace_repo = \".\"\nwest_workspace = \".\"\n"
        "west_venv_python = \".\"\naudit_dir = \".\"\n"
        "[zenoh]\nrouter_locator = \"tcp/127.0.0.1:7447\"\n"
        "[mcp_clients.demo]\nurl = \"http://127.0.0.1:9\"\n"
        "[mcp_clients.demo.env]\nKEY = \"v\"\n",
        encoding="utf-8")
    cfg = load_config(p)
    assert cfg.mcp_clients["demo"]["url"] == "http://127.0.0.1:9"
    assert cfg.mcp_clients["demo"]["env"] == {"KEY": "v"}


def test_bridged_list_and_call_full_chain(tmp_path, monkeypatch):
    """全链：x_demo_list 清单透传；x_demo_call strict 挂起 → 审批放行 →
    结果回传（长任务句柄收口）。"""
    from fastmcp import Client

    from tessera_agent.gateway.compose import build_app

    ctx = _env(tmp_path, monkeypatch, token="tok")
    app = build_app(ctx)

    async def main():
        async with Client(app) as c:
            r = await c.call_tool("x_demo_list", {})
            d = r.data if hasattr(r, "data") else r
            assert d["server"] == "demo"
            assert any(t["name"] == "greet" for t in d["tools"])
            # call → strict 挂起 → 句柄
            r2 = await c.call_tool("x_demo_call",
                                   {"tool": "greet", "args": {"who": "tessera"}})
            d2 = r2.data if hasattr(r2, "data") else r2
            assert d2["task_id"] and d2["state"] == "working"
            # 审批放行 → 任务完成
            pending = ctx.approvals.list_pending()
            assert pending and pending[0]["tool"] == "x_demo_greet"
            ctx.approvals.decide(pending[0]["approval_id"], "allow", "tok")
            for _ in range(50):
                snap = ctx.registry.get(d2["task_id"])
                if snap.state == "completed":
                    break
                await asyncio.sleep(0.05)
            assert snap.state == "completed"
            out = snap.result["result"]
            assert "hello tessera" in str(out)

    asyncio.run(main())


def test_bridged_call_deny(tmp_path, monkeypatch):
    """审批拒绝 → 任务 failed（TA_E_APPROVAL_DENIED——不信任面默认挡）。"""
    from fastmcp import Client

    from tessera_agent.gateway.compose import build_app

    ctx = _env(tmp_path, monkeypatch, token="tok")
    app = build_app(ctx)

    async def main():
        async with Client(app) as c:
            r = await c.call_tool("x_demo_call",
                                  {"tool": "greet", "args": {"who": "x"}})
            d = r.data if hasattr(r, "data") else r
            pending = ctx.approvals.list_pending()
            ctx.approvals.decide(pending[0]["approval_id"], "deny", "tok")
            for _ in range(50):
                snap = ctx.registry.get(d["task_id"])
                if snap.state == "failed":
                    break
                await asyncio.sleep(0.05)
            assert snap.state == "failed"
            assert snap.error["code"] == 8  # TA_E_APPROVAL_DENIED

    asyncio.run(main())


def test_compose_registration_facts(tmp_path, monkeypatch):
    """组合根：mcp_clients 非空 → 桥接包注册（tools 面可见）；空 → 不注册。"""
    from tessera_agent.gateway.compose import build_app
    from tessera_agent.gateway.mcp_clients import MCPClientDomainPack

    ctx = _env(tmp_path, monkeypatch)
    app = build_app(ctx)
    registered = {t.name for t in asyncio.run(_tool_names(app))}
    assert "x_demo_list" in registered and "x_demo_call" in registered
    # 空配置 → 无桥接面
    ctx2 = _env(tmp_path, monkeypatch)
    ctx2.cfg.mcp_clients.clear()
    app2 = build_app(ctx2)
    registered2 = {t.name for t in asyncio.run(_tool_names(app2))}
    assert not any(n.startswith("x_") for n in registered2)
    # 包构造面直接核
    pack = MCPClientDomainPack({"a-b": {"url": "http://x"}})
    assert pack.tools == ["x_a_b_list", "x_a_b_call"]


def test_inline_absent_from_config_loader(tmp_path):
    """_inline 键仅测试面——config 加载器不会产生（透传 dict 原样，注入
    通道文档化）。"""
    from tessera_agent.common.config import load_config

    p = tmp_path / "config.toml"
    p.write_text(
        "[providers]\ndefault_model = \"ollama:test\"\n"
        "[agent]\nworkspace_repo = \".\"\nwest_workspace = \".\"\n"
        "west_venv_python = \".\"\naudit_dir = \".\"\n"
        "[zenoh]\nrouter_locator = \"tcp/127.0.0.1:7447\"\n"
        "[mcp_clients.d]\nurl = \"http://127.0.0.1:9\"\n",
        encoding="utf-8")
    cfg = load_config(p)
    assert "_inline" not in cfg.mcp_clients["d"]
