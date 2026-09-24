# SPDX-License-Identifier: Apache-2.0
"""MCP 网关装配（LLD-A01）：FastMCP stdio 门面 + sys_*/task_*/fw_* 工具注册。

错误呈现：TaError → ToolError(JSON payload)（isError + 结构化字段，LLD-A01 §5）。
长任务纪律：耗时类工具立即返回句柄（DEC-36②），客户端经 task_* 轮询。
"""

from __future__ import annotations

import asyncio
import functools
import json
import secrets
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from tessera_agent import __version__
from tessera_agent.common.audit import ToolAudit
from tessera_agent.common.config import AgentConfig
from tessera_agent.common.errors import TA_E_POLICY, TaError
from tessera_agent.common.limits import ContextBudget
from tessera_agent.common.tasks import TaskRegistry
from tessera_agent.gateway.approvals import ApprovalBroker
from tessera_agent.tools_fw import tools as fw
from tessera_agent.tools_net import deploy as net_deploy
from tessera_agent.tools_net.zenoh_service import ZenohService
from tessera_agent.tools_sim import runner as sim_runner
from tessera_agent.tools_sim.scenario import scenario_validate
from tessera_agent.tools_tsap import tools as tsap_tools

# 来源: DEC-38 #10——限流 30 工具调用/min/客户端
RATE_LIMIT_PER_MIN = 30


@dataclass
class AppContext:
    cfg: AgentConfig
    budget: ContextBudget
    registry: TaskRegistry = field(default_factory=TaskRegistry)
    approvals: ApprovalBroker = field(default_factory=ApprovalBroker)
    audit: ToolAudit | None = None
    started_at: float = field(default_factory=time.time)
    # tsap_* 产物写白名单根（默认 workspace；测试注入 tmp 根）
    write_roots: list[str] | None = None

    def tool_audit(self) -> ToolAudit:
        return self.audit if self.audit is not None else ToolAudit(self.cfg.audit_dir)

    def roots(self) -> list[str]:
        return self.write_roots if self.write_roots else [str(self.cfg.workspace_repo)]


def _ta_payload(exc: TaError) -> str:
    return json.dumps({"ok": False, **exc.to_payload()}, ensure_ascii=False)




class RateLimiter:
    def __init__(self, limit: int = RATE_LIMIT_PER_MIN) -> None:
        self.limit = limit
        self._window_start = time.monotonic()
        self._count = 0

    def hit(self) -> None:
        now = time.monotonic()
        if now - self._window_start > 60:
            self._window_start = now
            self._count = 0
        self._count += 1
        if self._count > self.limit:
            msg = f"限流触发（{self.limit}/min，DEC-38 #10）"
            exc = TaError(TA_E_POLICY, msg, domain="gateway", retryable=True)
            raise ToolError(_ta_payload(exc)) from None


def build_app(ctx: AppContext) -> FastMCP:
    mcp = FastMCP("tessera-agent")
    limiter = RateLimiter()

    def audited(tool_name: str) -> Callable:
        """审计（工具流）+ TaError → ToolError(JSON)（LLD-A01 §5）。"""

        def deco(fn: Callable) -> Callable:
            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                t0 = time.monotonic()
                limiter.hit()
                state = "ok"
                try:
                    return await fn(*args, **kwargs)
                except TaError as exc:
                    state = "failed"
                    raise ToolError(_ta_payload(exc)) from exc
                finally:
                    ctx.tool_audit().append(
                        tool=tool_name,
                        args=kwargs,
                        state=state,
                        dur_ms=int((time.monotonic() - t0) * 1000),
                    )

            return wrapper

        return deco

    async def spawn(tool: str, args: dict[str, Any], body: Callable[[], Awaitable[Any]]) -> dict:
        task = await ctx.registry.create(tool, args, body)
        return {"task_id": task.id, "state": "working"}

    # ---- sys_* ------------------------------------------------------------
    @mcp.tool
    @audited("sys_ping")
    async def sys_ping() -> dict:
        """健康探测：返回 pong 与版本。"""
        return ({"pong": True, "version": __version__})

    @mcp.tool
    @audited("sys_get_info")
    async def sys_get_info() -> dict:
        """网关与配置概要：版本/模型与上下文窗口/工作区状态/审批 token 是否配置。"""
        ws = await fw.fw_workspace_status(ctx.cfg, ctx.budget)
        return (
            {
                "version": __version__,
                "model": ctx.cfg.default_model,
                "context_window_tokens": ctx.budget.window_tokens,
                "approval_token_configured": ctx.approvals.token_configured(),
                "uptime_s": int(time.time() - ctx.started_at),
                "workspace": ws,
            }
        )

    @mcp.tool
    @audited("sys_pending_approvals")
    async def sys_pending_approvals() -> dict:
        """列出等待宿主审批的 strict 类工具请求。"""
        return ({"pending": ctx.approvals.list_pending()})

    @mcp.tool
    @audited("sys_approve")
    async def sys_approve(approval_id: str, decision: str, token: str) -> dict:
        """审批决定（allow/deny）；token = 宿主环境变量 TESSERA_AGENT_APPROVAL_TOKEN。"""
        return (ctx.approvals.decide(approval_id, decision, token))

    # ---- task_* -----------------------------------------------------------
    @mcp.tool
    @audited("task_status")
    async def task_status(task_id: str) -> dict:
        """查询长任务状态（终态含 result/error）。"""
        return (ctx.registry.get(task_id).snapshot())

    @mcp.tool
    @audited("task_log")
    async def task_log(task_id: str, offset: int = 0, limit: int = 200) -> dict:
        """分页读取任务日志。"""
        task = ctx.registry.get(task_id)
        data = ctx.registry.log_slice(task, offset, limit)
        data["task_id"] = task_id
        return (data)

    @mcp.tool
    @audited("task_cancel")
    async def task_cancel(task_id: str) -> dict:
        """取消长任务（协作式：终止子进程组）。"""
        task = await ctx.registry.cancel(task_id)
        return (task.snapshot())

    # ---- fw_*（confirm 类，V1 会话内直行——策略经 config 收紧，DEC-38 #7）----
    @mcp.tool
    @audited("fw_workspace_status")
    async def fw_workspace_status() -> dict:
        """固件工作区状态：分支/提交/dirty/测试清单。"""
        return (await fw.fw_workspace_status(ctx.cfg, ctx.budget))

    @mcp.tool
    @audited("fw_build")
    async def fw_build(board: str, extra_args: list[str] | None = None) -> dict:
        """构建固件（west build；长任务，立即返回句柄，经 task_status 轮询）。"""
        args = {"board": board, "extra_args": extra_args or []}
        task_id = f"fwbuild-{secrets.token_hex(4)}"

        async def body(task) -> dict:
            log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
            return await fw.fw_build(
                ctx.cfg, ctx.budget, board=board, extra_args=extra_args,
                task_id=task_id, log_fn=log,
            )

        return await spawn("fw_build", args, body)

    @mcp.tool
    @audited("fw_twister")
    async def fw_twister(platform: str, extra_args: list[str] | None = None) -> dict:
        """运行 twister 测试（长任务，返回句柄）。"""
        args = {"platform": platform, "extra_args": extra_args or []}
        task_id = f"fwtw-{secrets.token_hex(4)}"

        async def body(task) -> dict:
            log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
            return await fw.fw_twister(
                ctx.cfg, ctx.budget, platform=platform, extra_args=extra_args,
                task_id=task_id, log_fn=log,
            )

        return await spawn("fw_twister", args, body)

    @mcp.tool
    @audited("fw_pytest")
    async def fw_pytest(scope: str = "firmware/tests/pytest") -> dict:
        """运行仓库 pytest（长任务，返回句柄）。"""
        args = {"scope": scope}

        async def body(task) -> dict:
            log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
            return await fw.fw_pytest(ctx.cfg, ctx.budget, scope=scope, log_fn=log)

        return await spawn("fw_pytest", args, body)

    # ---- sim_*（MA2，LLD-A04）----------------------------------------------
    @mcp.tool
    @audited("sim_validate_scenario")
    async def sim_validate_scenario(scenario: dict) -> dict:
        """校验仿真场景 schema v1（inputs 升序/op 合法等）；返回错误清单（空=合法）。"""
        return {"errors": scenario_validate(scenario)}

    @mcp.tool
    @audited("sim_run")
    async def sim_run(scenario: dict) -> dict:
        """运行确定性重放仿真（framework.replay 双跑比对 + 期望评估；长任务句柄）。"""
        args = {"scenario": scenario}
        task_id = f"simrun-{secrets.token_hex(4)}"

        async def body(task) -> dict:
            log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
            return await sim_runner.sim_run(ctx.cfg, scenario, task_id=task_id, log_fn=log)

        return await spawn("sim_run", args, body)

    # ---- tsap_*（MA2，LLD-A05；无签名不产出——硬点）--------------------------
    @mcp.tool
    @audited("tsap_keygen")
    async def tsap_keygen(name: str, out_dir: str = "agent/keys") -> dict:
        """生成 ed25519 开发密钥对（strict 类：挂起宿主审批，超时自动拒绝；
        长任务句柄——轮询 task_status 至 input_required，经 sys_pending_approvals/
        sys_approve 决；私钥 0600 落盘，不回显/不入审计）。"""
        args = {"name": name, "out_dir": out_dir}

        async def body(task) -> dict:
            approval = ctx.approvals.request(
                "tsap_keygen",
                {"name": name, "out_dir": out_dir},
                reason="strict 类：生成签名密钥材料（HLD §5.1）",
            )
            task.state = "input_required"
            try:
                await ctx.approvals.wait(approval)
            finally:
                task.state = "working"
            return tsap_tools.tsap_keygen(name, out_dir, ctx.roots())

        return await spawn("tsap_keygen", args, body)

    @mcp.tool
    @audited("tsap_package")
    async def tsap_package(
        wasm_path: str, manifest: dict, key_path: str, out_dir: str = "agent/build"
    ) -> dict:
        """TSAP 打包签名（canonical CBOR + COSE_Sign1 双实现互验；长任务句柄）。"""
        args = {"wasm_path": wasm_path, "manifest": manifest, "key_path": key_path}

        async def body(task) -> dict:
            return tsap_tools.tsap_package(wasm_path, manifest, key_path, out_dir, ctx.roots())

        return await spawn("tsap_package", args, body)

    @mcp.tool
    @audited("tsap_verify")
    async def tsap_verify(package_path: str, pub_key_path: str) -> dict:
        """TSAP 包全量反向验证（容器头 + COSE 双实现 + manifest 解码）。"""
        return tsap_tools.tsap_verify(package_path, pub_key_path)

    # ---- deploy_*（MA3.1，LLD-A06；同步 zenoh 面经 to_thread 桥接）---------
    @mcp.tool
    @audited("deploy_discover")
    async def deploy_discover(timeout_s: float = 10.0) -> dict:
        """发现 router 侧在线 cube（通配 query get-info；超时默认 10s，DEC-38 #4）。"""
        def work() -> dict:
            with ZenohService(ctx.cfg.router_locator, query_timeout_s=timeout_s) as svc:
                return {"cubes": net_deploy.discover(svc, timeout_s=timeout_s)}

        return await asyncio.to_thread(work)

    @mcp.tool
    @audited("deploy_status")
    async def deploy_status(node: str, cube: str) -> dict:
        """组合快照：get-info/get-link/get-safety/get-app（部署前核验依据）。"""
        def work() -> dict:
            with ZenohService(ctx.cfg.router_locator) as svc:
                return net_deploy.status(svc, node, cube)

        return await asyncio.to_thread(work)

    @mcp.tool
    @audited("deploy_push_app")
    async def deploy_push_app(
        node: str,
        cube: str,
        package_path: str,
        pub_key_path: str,
        holder: str = "tessera-agent",
        chunk_size: int = net_deploy.CHUNK_DEFAULT,
    ) -> dict:
        """TSAP 包分块部署到 cube（strict：挂起宿主审批；长任务句柄）。

        硬点（工具内强制，不可跳过）：tsap_verify 复验 → 租约闭环（acquire/
        续期/release）→ 2KB 分块（idem 重试安全）→ upload/verify/activate 分步
        → get-app 确认回读。失败留于当前步（重试从断点续传）。"""
        args = {
            "node": node, "cube": cube, "package_path": package_path,
            "pub_key_path": pub_key_path, "holder": holder, "chunk_size": chunk_size,
        }

        async def body(task) -> dict:
            log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
            approval = ctx.approvals.request(
                "deploy_push_app",
                args,
                reason="strict 类：远程安装 APP（写 inactive slot + meta 切换）",
            )
            task.state = "input_required"
            try:
                await ctx.approvals.wait(approval)
            finally:
                task.state = "working"

            def work() -> dict:
                with ZenohService(ctx.cfg.router_locator) as svc:
                    return net_deploy.push_app(
                        svc, node, cube, package_path, pub_key_path,
                        holder=holder, chunk_size=chunk_size, log_fn=log,
                    )

            return await asyncio.to_thread(work)

        return await spawn("deploy_push_app", args, body)

    return mcp


def run_server(cfg: AgentConfig) -> None:
    """stdio 服务入口（V1 唯一传输，DEC-38 #2）。"""
    budget = ContextBudget(cfg.context_window)
    app = build_app(AppContext(cfg=cfg, budget=budget))
    app.run()  # FastMCP 默认 stdio
