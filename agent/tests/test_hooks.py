# SPDX-License-Identifier: Apache-2.0
"""D4 hooks 拦截面（DEC-67①③）：

- allow-session 审批语义（会话域记住、零挂起、不落盘、deny 不污染）
- HookChain 单元（精确/前缀/首匹配/坏条目跳过）
- 网关集成（deny = isError + rule_id 归因 + 审计 hook_denied；observe = 放行
  + 审计 _hook 留观标）"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tessera_agent.common.errors import TA_E_ARGS, TaError
from tessera_agent.gateway.approvals import ApprovalBroker
from tessera_agent.gateway.hooks import HookChain, parse_rules

PKG_ROOT = Path(__file__).resolve().parent.parent


def _unwrap(res):
    data = res.data if hasattr(res, "data") else res
    if isinstance(data, dict) and data.get("isError"):
        raise ToolError(str(data))
    return data


# ---- allow-session ---------------------------------------------------------

def test_allow_session_decision_semantics(monkeypatch):
    monkeypatch.setenv("TESSERA_AGENT_APPROVAL_TOKEN", "tok")
    async def main():
        b = ApprovalBroker()
        a = b.request("app_deploy", {}, reason="strict")
        with pytest.raises(TaError) as ei:
            b.decide(a.id, "allow-session", token="bad")
        assert ei.value.code == TA_E_ARGS  # token 校验先行
        d = b.decide(a.id, "allow-session", token="tok")
        assert d["decision"] == "allow-session"
        assert await b.wait(a) == "allow"  # 本次放行
        # 同工具后续调用 = 零挂起自动放行
        a2 = b.request("app_deploy", {}, reason="strict")
        assert await b.wait(a2) == "allow"
        # 其他工具不受影响
        a3 = b.request("app_compile", {}, reason="strict")
        assert not a3.event.is_set()
        # deny 不污染会话集
        a4 = b.request("app_deploy", {}, reason="strict")
        b.decide(a4.id, "deny", token="tok")
        with pytest.raises(TaError):
            await b.wait(a4)
        a5 = b.request("app_deploy", {}, reason="strict")
        assert await b.wait(a5) == "allow"  # deny 不入会话集

    asyncio.run(main())


def test_decision_domain_failclosed():
    async def main():
        b = ApprovalBroker()
        a = b.request("t", {}, reason="r")
        with pytest.raises(TaError):
            b.decide(a.id, "forever", token="tok")
        # 决策域外 → 审批仍待决（不被污染）
        assert a.decision is None

    asyncio.run(main())


# ---- HookChain 单元 --------------------------------------------------------

def test_hook_chain_matching():
    rules = parse_rules([
        {"when": "pre", "match_tool": "app_deploy", "action": "deny",
         "reason": "维护窗"},
        {"when": "pre", "match_tool": "tsap_*", "action": "observe",
         "reason": "留观"},
        {"when": "post", "match_tool": "x", "action": "deny"},  # v1 非 pre → 跳过
        {"when": "pre", "match_tool": "", "action": "deny"},  # 坏条目跳过
        {"when": "pre", "match_tool": "y", "action": "nuke"},  # 动作域外跳过
    ])
    chain = HookChain(rules)
    v = chain.pre("app_deploy")
    assert v is not None and v.action == "deny" and v.rule.rule_id == "h0"
    assert v.reason == "维护窗"
    v2 = chain.pre("tsap_package")  # 前缀形态
    assert v2 is not None and v2.action == "observe"
    assert chain.pre("sys_ping") is None  # 无匹配 = 放行
    assert len(chain.rules) == 2  # 坏条目跳过


# ---- 网关集成 --------------------------------------------------------------

def _build(tmp_path, hooks: list[dict]):
    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.gateway.compose import build_app
    from tessera_agent.platform import AppContext

    cfg = AgentConfig(
        workspace_repo=PKG_ROOT.parent,
        west_workspace=PKG_ROOT.parent,
        west_venv_python=PKG_ROOT.parent / "agent" / "nofake",
        audit_dir=tmp_path / "audit",
        default_model="ollama:test",
        context_window=32_000,
        router_locator="tcp/127.0.0.1:7447",
        hooks=hooks,
    )
    ctx = AppContext(cfg=cfg, budget=ContextBudget(32_000))
    return ctx, build_app(ctx)


def test_gateway_deny_hook(tmp_path):
    """deny 钩子：sys_ping 调用 = isError + rule_id 归因 + 审计 hook_denied。"""
    async def main():
        _, app = _build(tmp_path, [
            {"when": "pre", "match_tool": "sys_ping", "action": "deny",
             "reason": "维护窗"},
        ])
        async with Client(app) as c:
            with pytest.raises(ToolError) as ei:
                await c.call_tool("sys_ping", {})
            payload = json.loads(str(ei.value))
            assert payload["code"] == 13  # TA_E_POLICY
            assert payload["detail"]["rule_id"] == "h0"
            assert payload["detail"]["reason"] == "维护窗"
        day = time.strftime("%Y%m%d")
        audit_file = tmp_path / "audit" / "tools" / f"{day}.jsonl"
        rows = [json.loads(ln) for ln in audit_file.read_text().splitlines()]
        ping = [r for r in rows if r["tool"] == "sys_ping"]
        assert ping and ping[-1]["state"] == "hook_denied"

    asyncio.run(main())


def test_gateway_observe_hook(tmp_path):
    """observe 钩子：调用照常成功，审计 args 带 _hook 留观标。"""
    async def main():
        _, app = _build(tmp_path, [
            {"when": "pre", "match_tool": "sys_*", "action": "observe",
             "reason": "巡检"},
        ])
        async with Client(app) as c:
            r = _unwrap(await c.call_tool("sys_ping", {}))
            assert r["pong"] is True
        day = time.strftime("%Y%m%d")
        audit_file = tmp_path / "audit" / "tools" / f"{day}.jsonl"
        rows = [json.loads(ln) for ln in audit_file.read_text().splitlines()]
        ping = [r for r in rows if r["tool"] == "sys_ping"]
        hook_mark = ping[-1]["args_preview"].get("_hook", "")
        assert "巡检" in hook_mark  # args_preview 值 = repr 截断（留观标入审计）

    asyncio.run(main())


# ---- A4 · D4b post 观察面（LLD-agent-mcp-clients-and-post-hooks §4）------------------------------

def test_post_rule_parsing():
    """post 仅 observe（deny 解析期拒收）；pre 语义不变。"""
    rules = parse_rules([
        {"when": "post", "match_tool": "app_deploy", "action": "observe",
         "reason": "部署观察"},
        {"when": "post", "match_tool": "x", "action": "deny"},   # 拒收
        {"when": "pre", "match_tool": "y", "action": "deny"},    # pre 不变
    ])
    assert [(r.when, r.action) for r in rules] == [("post", "observe"),
                                                   ("pre", "deny")]


def test_post_matching_and_summary():
    chain = HookChain(parse_rules([
        {"when": "post", "match_tool": "deploy_*", "action": "observe"},
    ]))
    hits = chain.post("deploy_push_app", {"tool": "deploy_push_app"})
    assert len(hits) == 1 and hits[0].rule.rule_id == "h0"
    assert chain.post("sys_ping", {}) == []
    s = HookChain.summarize("t", 12, "ok", {"big": "x" * 1000})
    assert s["dur_ms"] == 12 and len(s["result_preview"]) == 400


def test_gateway_post_hook_publishes_event(tmp_path):
    """网关集成：post 规则命中 → 工具调用后 hook.post 事件入总线。"""
    async def main():
        from tessera_agent.common.config import AgentConfig
        from tessera_agent.common.limits import ContextBudget
        from tessera_agent.gateway.compose import build_app
        from tessera_agent.platform import AppContext

        cfg = AgentConfig(
            workspace_repo=PKG_ROOT.parent, west_workspace=PKG_ROOT.parent,
            west_venv_python=PKG_ROOT.parent / "agent" / "nofake",
            audit_dir=tmp_path / "audit", default_model="ollama:test",
            context_window=32_000, router_locator="tcp/127.0.0.1:7447",
            hooks=[{"when": "post", "match_tool": "sys_ping",
                    "action": "observe", "reason": "ping 观察"}])
        ctx = AppContext(cfg=cfg, budget=ContextBudget(32_000))
        app = build_app(ctx)
        sub = await ctx.events.subscribe()
        from fastmcp import Client

        async with Client(app) as c:
            r = await c.call_tool("sys_ping", {})
            assert (r.data if hasattr(r, "data") else r)["pong"] is True
        ev = await asyncio.wait_for(sub.__anext__(), timeout=3)
        assert ev.kind == "hook.post"
        assert ev.data["tool"] == "sys_ping"
        assert ev.data["rule_id"] == "h0"
        assert ev.data["state"] == "ok" and "pong" in ev.data["result_preview"]
        sub.close()

    asyncio.run(main())
