# SPDX-License-Identifier: Apache-2.0
"""MA1 测试：任务注册表 / 限额与压缩 / 审批代理 / 网关（FastMCP 客户端实测）。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from tessera_agent.common.config import AgentConfig
from tessera_agent.common.errors import (
    TA_E_APPROVAL_DENIED,
    TA_E_TASK_NOT_FOUND,
    TA_E_TIMEOUT,
    TaError,
)
from tessera_agent.common.limits import (
    MIN_CONTEXT_WINDOW_TOKENS,
    ContextBudget,
    truncate_line,
)
from tessera_agent.common.tasks import TaskRegistry
from tessera_agent.core.session import maybe_compress
from tessera_agent.gateway.approvals import APPROVAL_TOKEN_ENV, ApprovalBroker

PKG_ROOT = Path(__file__).resolve().parent.parent


def run(coro):
    return asyncio.run(coro)


def unwrap(r) -> dict:
    """FastMCP CallToolResult → dict payload（工具统一返回裸 dict，LLD-A01 §5）。"""
    d = getattr(r, "data", r)
    if hasattr(d, "model_dump"):
        d = d.model_dump()
    assert isinstance(d, dict), f"unexpected tool result type: {type(d)}"
    return d


# ---- 任务注册表（LLD-A00 §2）-----------------------------------------------


def test_task_lifecycle_completed_and_failed():
    async def main():
        reg = TaskRegistry()

        async def ok_body(task):
            return {"value": 42}

        t1 = await reg.create("x", {}, ok_body)
        await t1._aio
        assert t1.state == "completed"
        assert t1.result == {"value": 42}

        async def bad_body(task):
            raise TaError(2, "参数错", domain="x")

        t2 = await reg.create("x", {}, bad_body)
        await t2._aio
        assert t2.state == "failed"
        assert t2.error["code"] == 2

    run(main())


def test_task_ttl_expiry():
    async def main():
        reg = TaskRegistry()

        async def slow(task):
            await asyncio.sleep(10)

        t = await reg.create("x", {}, slow)
        t.ttl_s = 0
        t.created_at -= 1
        got = reg.get(t.id)  # 触发 TTL 判定（DEC-38 #4：TTL 到期 → failed）
        assert got.state == "failed"
        assert got.error["code"] == TA_E_TIMEOUT

    run(main())


def test_task_not_found():
    reg = TaskRegistry()
    with pytest.raises(TaError) as ei:
        reg.get("t-nope")
    assert ei.value.code == TA_E_TASK_NOT_FOUND


def test_task_log_ring():
    reg = TaskRegistry()

    async def main():
        t = await reg.create("x", {}, lambda task: None)
        for i in range(1005):
            reg.append_log(t, f"line{i}")
        data = reg.log_slice(t, 990)
        assert data["total"] == 1000  # 环形 1000（DEC-38 #5）
        assert data["dropped"] == 5
        assert data["lines"][0] == "line995"

    run(main())


# ---- 限额与压缩（DEC-38 #6/#9）----------------------------------------------


def test_budget_min_window_rejected():
    with pytest.raises(TaError):
        ContextBudget(MIN_CONTEXT_WINDOW_TOKENS - 1)  # 32k 最低要求


def test_budget_math():
    b = ContextBudget(32_000)
    assert b.compress_at_tokens == 22_400  # 阈值 70%
    assert b.single_return_bytes == 16 * 1024  # 最低 16KiB 生效（3.2 万 token ×5%×4 < 16K）
    assert b.line_bytes == 2 * 1024  # max(2K, 16K/16)
    b2 = ContextBudget(200_000)
    assert b2.single_return_bytes == 40_000  # 200k×5%×4（动态，DEC-38 #9）
    assert b2.line_bytes == 2500


def test_truncate_line():
    b = ContextBudget(32_000)
    out = truncate_line("x" * 5000, b)
    assert len(out.encode()) <= b.line_bytes + 48
    assert out.endswith("…[truncated]")


def test_maybe_compress_triggers_and_keeps_tail():
    b = ContextBudget(32_000)

    async def summarize(text: str) -> str:
        return f"摘要({len(text)} 字符)"

    async def main():
        big = "y" * (b.compress_at_tokens + 100) * 4  # 确保超阈值
        turns = [big, "tail-1", "tail-2"]
        new, compressed = await maybe_compress(turns, b, summarize)
        assert compressed
        assert new[0].startswith("[summary]")
        assert new[-2:] == ["tail-1", "tail-2"]  # 保留近段（LLD-A02 §2）
        same, nc = await maybe_compress(["a", "b"], b, summarize)
        assert not nc and same == ["a", "b"]

    run(main())


# ---- 审批代理（LLD-A01 §4 / DEC-38 #7）--------------------------------------


def test_approval_deny_by_timeout():
    async def main():
        broker = ApprovalBroker()
        a = broker.request("deploy_push_app", {"k": "v"}, reason="strict")
        with pytest.raises(TaError) as ei:
            await broker.wait(a, timeout_s=0.05)  # 超时自动 deny
        assert ei.value.code == TA_E_APPROVAL_DENIED

    run(main())


def test_approval_decide_token_and_flow(monkeypatch):
    monkeypatch.setenv(APPROVAL_TOKEN_ENV, "tok-123")
    broker = ApprovalBroker()

    with pytest.raises(TaError):
        broker.decide("nope", "allow", "tok-123")  # 不存在的审批
    a = broker.request("t", {}, reason="r")
    with pytest.raises(TaError):
        broker.decide(a.id, "allow", "wrong-token")  # token 无效（防代批）

    async def main():
        waiter = asyncio.create_task(broker.wait(a))
        await asyncio.sleep(0.01)
        assert broker.list_pending()[0]["approval_id"] == a.id
        broker.decide(a.id, "allow", "tok-123")
        assert await waiter == "allow"

    run(main())


# ---- 网关（FastMCP 客户端 in-memory 实测，LLD-A01 §6）----------------------


def _build(tmp_path: Path):
    from tessera_agent.common.limits import ContextBudget as CB
    from tessera_agent.gateway.server import AppContext, build_app

    cfg = AgentConfig(
        workspace_repo=PKG_ROOT.parent,
        west_workspace=PKG_ROOT.parent,
        west_venv_python=Path(sys.executable),
        audit_dir=tmp_path / "audit",
        default_model="ollama:test",
        context_window=32_000,
        router_locator="tcp/127.0.0.1:7447",
    )
    ctx = AppContext(cfg=cfg, budget=CB(32_000))
    return ctx, build_app(ctx)


def test_gateway_sys_tools(tmp_path):
    async def main():
        ctx, app = _build(tmp_path)
        async with Client(app) as c:
            ping = unwrap(await c.call_tool("sys_ping", {}))
            assert ping["pong"] is True
            assert ping["version"]
            info = unwrap(await c.call_tool("sys_get_info", {}))
            assert info["context_window_tokens"] == 32_000
            assert info["workspace"]["repo_commit"]
            assert ctx.approvals.token_configured() is False

    run(main())


def test_gateway_task_flow_with_real_subprocess(tmp_path):
    """真实子进程句柄化冒烟：fw_pytest（仓库编码检查，秒级）→ task_status 轮询到终态。"""

    async def main():
        _, app = _build(tmp_path)
        async with Client(app) as c:
            r = unwrap(await c.call_tool("fw_pytest", {"scope": "firmware/tests/pytest"}))
            assert r["state"] == "working"  # 立即返回句柄（DEC-36②）
            task_id = r["task_id"]
            sd = None
            for _ in range(120):
                sd = unwrap(await c.call_tool("task_status", {"task_id": task_id}))
                if sd["state"] != "working":
                    break
                await asyncio.sleep(0.5)
            assert sd is not None and sd["state"] == "completed", sd
            assert "passed" in "\n".join(sd["result"]["tail"])
            log = unwrap(await c.call_tool("task_log", {"task_id": task_id, "limit": 5}))
            assert log["total"] >= 1
            with pytest.raises(ToolError):
                await c.call_tool("task_status", {"task_id": "t-nope"})  # isError 路径

    run(main())


def test_gateway_approval_flow_end_to_end(tmp_path, monkeypatch):
    """端到端审批：strict 工具挂起 → pending 呈现 → 错 token 拒 → 对 token 放行。"""
    monkeypatch.setenv(APPROVAL_TOKEN_ENV, "tok-abc")

    async def main():
        from tessera_agent.core.session import gated_tool

        ctx, app = _build(tmp_path)
        calls: list[str] = []

        @gated_tool("demo_strict", ctx.approvals, category="strict")
        async def demo_strict(x: int) -> str:
            calls.append(f"x={x}")
            return f"done {x}"

        async with Client(app) as c:
            runner = asyncio.create_task(demo_strict(x=7))
            pend = []
            for _ in range(100):
                pend = unwrap(await c.call_tool("sys_pending_approvals", {}))["pending"]
                if pend:
                    break
                await asyncio.sleep(0.02)
            assert pend, "审批请求应出现在 pending 列表"
            approval_id = pend[0]["approval_id"]
            with pytest.raises(ToolError):
                await c.call_tool(
                    "sys_approve",
                    {"approval_id": approval_id, "decision": "allow", "token": "wrong"},
                )
            ok = unwrap(
                await c.call_tool(
                    "sys_approve",
                    {"approval_id": approval_id, "decision": "allow", "token": "tok-abc"},
                )
            )
            assert ok["decision"] == "allow"
            assert await runner == "done 7"
            assert calls == ["x=7"]

    run(main())


def test_gateway_keygen_strict_gate(tmp_path, monkeypatch):
    """IR-14：MCP 面 strict 工具（tsap_keygen，HLD §5.1）必须过审批闸——
    句柄化 + input_required → sys_approve 放行 / 拒绝两路径；拒绝 = 无密钥产出。"""
    monkeypatch.setenv(APPROVAL_TOKEN_ENV, "tok-xyz")

    async def main():
        from tessera_agent.common.limits import ContextBudget as CB
        from tessera_agent.gateway.server import AppContext, build_app

        cfg = AgentConfig(
            workspace_repo=PKG_ROOT.parent,
            west_workspace=PKG_ROOT.parent,
            west_venv_python=Path(sys.executable),
            audit_dir=tmp_path / "audit",
            default_model="ollama:test",
            context_window=32_000,
            router_locator="tcp/127.0.0.1:7447",
        )
        ctx = AppContext(cfg=cfg, budget=CB(32_000), write_roots=[str(tmp_path)])
        app = build_app(ctx)
        keys_dir = tmp_path / "keys"

        async def wait_state(c, tid, want_terminal: bool):
            sd = {}
            for _ in range(300):
                sd = unwrap(await c.call_tool("task_status", {"task_id": tid}))
                done = sd["state"] not in ("working", "input_required")
                if done if want_terminal else sd["state"] == "input_required":
                    return sd
                await asyncio.sleep(0.02)
            return sd

        async with Client(app) as c:
            # 路径 1：allow → completed + 密钥产出
            r = unwrap(
                await c.call_tool("tsap_keygen", {"name": "dev1", "out_dir": str(keys_dir)})
            )
            assert r["state"] == "working"
            tid = r["task_id"]
            sd = await wait_state(c, tid, want_terminal=False)
            assert sd["state"] == "input_required", sd
            pend = unwrap(await c.call_tool("sys_pending_approvals", {}))["pending"]
            assert pend and pend[0]["tool"] == "tsap_keygen"
            ok = unwrap(
                await c.call_tool(
                    "sys_approve",
                    {"approval_id": pend[0]["approval_id"], "decision": "allow",
                     "token": "tok-xyz"},
                )
            )
            assert ok["decision"] == "allow"
            sd = await wait_state(c, tid, want_terminal=True)
            assert sd["state"] == "completed", sd
            assert Path(sd["result"]["pub_key_path"]).is_file()  # noqa: ASYNC240

            # 路径 2：deny → failed(TA_E_APPROVAL_DENIED) + 无密钥产出
            r2 = unwrap(
                await c.call_tool("tsap_keygen", {"name": "dev2", "out_dir": str(keys_dir)})
            )
            tid2 = r2["task_id"]
            sd2 = await wait_state(c, tid2, want_terminal=False)
            assert sd2["state"] == "input_required", sd2
            pend2 = unwrap(await c.call_tool("sys_pending_approvals", {}))["pending"]
            dn = unwrap(
                await c.call_tool(
                    "sys_approve",
                    {"approval_id": pend2[0]["approval_id"], "decision": "deny",
                     "token": "tok-xyz"},
                )
            )
            assert dn["decision"] == "deny"
            sd2 = await wait_state(c, tid2, want_terminal=True)
            assert sd2["state"] == "failed", sd2
            assert sd2["error"]["code"] == TA_E_APPROVAL_DENIED
            assert not (keys_dir / "dev2.key").exists()

    run(main())
