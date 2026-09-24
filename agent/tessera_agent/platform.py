# SPDX-License-Identifier: Apache-2.0
"""平台层（LLD-A07 §3）：sys_*/task_*/skill_read 工具 + DomainPack 注册表装配。

纪律：**本模块不 import 任何域模块**（tools_fw/tools_sim/tools_tsap/tools_net/
domain/*）——域工具经 DomainPack.mount 装配（组合根 = gateway/compose.py，
显式注册 FirmwareDomainPack）。新增域 = 新包 + 组合根注册，平台零改动。
"""

from __future__ import annotations

import asyncio
import functools
import json
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from tessera_agent import __version__
from tessera_agent.common.audit import ToolAudit
from tessera_agent.common.config import AgentConfig
from tessera_agent.common.errors import TA_E_POLICY, TaError
from tessera_agent.common.limits import ContextBudget
from tessera_agent.common.tasks import TaskRegistry
from tessera_agent.core.session import PolicyTable
from tessera_agent.gateway.approvals import ApprovalBroker
from tessera_agent.skills import loader as skill_loader

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


# ---- DomainPack 协议（多域预留核心，DEC-33；固件域 = 首个实现）----------------

ArtifactValidator = Callable[[str], None]  # 产物路径 → 校验失败抛 TaError


@dataclass
class Deployer(Protocol):
    """域部署器（固件域 V1 = deploy.push_app 包装）。"""

    def deploy(self, ctx: AppContext, node: str, cube: str, package_path: str,
               pub_key_path: str, log_fn: Callable[[str], None] | None = None) -> dict:
        ...  # pragma: no cover——协议声明


@dataclass
class DomainPackBase:
    """DomainPack 基座：声明面 + 默认实现（子类覆写 mount/info_extras）。"""

    name: str = "unnamed"
    tools: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)          # SkillRef name 集
    policy: PolicyTable = field(default_factory=PolicyTable)  # 只可收紧（core.session）
    validators: list[ArtifactValidator] = field(default_factory=list)
    deployer: Deployer | None = None

    def mount(self, api: MountAPI) -> None:  # pragma: no cover——子类实现
        raise NotImplementedError

    def info_extras(self, ctx: AppContext) -> dict[str, Any]:
        return {}


@dataclass
class MountAPI:
    """平台递给域包的装配面（审计/限流/句柄化与上下文）。"""

    mcp: FastMCP
    ctx: AppContext
    audited: Callable[[str], Callable]
    spawn: Callable[[str, dict[str, Any], Callable[[], Awaitable[Any]]], Awaitable[dict]]


@runtime_checkable
class DomainPack(Protocol):
    name: str
    tools: list[str]

    def mount(self, api: MountAPI) -> None: ...


# ---- 装配 ------------------------------------------------------------------

def assemble(ctx: AppContext, packs: Sequence[DomainPack]) -> FastMCP:
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

    async def spawn(tool: str, args: dict[str, Any],
                    body: Callable[[], Awaitable[Any]]) -> dict:
        task = await ctx.registry.create(tool, args, body)
        return {"task_id": task.id, "state": "working"}

    api = MountAPI(mcp=mcp, ctx=ctx, audited=audited, spawn=spawn)

    # ---- 平台工具：sys_* / task_* / skill_read ----------------------------
    @mcp.tool
    @audited("sys_ping")
    async def sys_ping() -> dict:
        """健康探测：返回 pong 与版本。"""
        return ({"pong": True, "version": __version__})

    @mcp.tool
    @audited("sys_get_info")
    async def sys_get_info() -> dict:
        """网关与配置概要：版本/模型与上下文窗口/各域 extras/审批 token 配置。"""
        info = {
            "version": __version__,
            "model": ctx.cfg.default_model,
            "context_window_tokens": ctx.budget.window_tokens,
            "approval_token_configured": ctx.approvals.token_configured(),
            "uptime_s": int(time.time() - ctx.started_at),
            "skills": [s.listing() for s in skill_loader.load_skills()],
            "domains": [],
        }
        for pack in packs:
            pack_name = getattr(pack, "name", type(pack).__name__)
            extras = pack.info_extras(ctx) if hasattr(pack, "info_extras") else {}
            if asyncio.iscoroutine(extras):
                extras = await extras
            info["domains"].append({"domain": pack_name, **extras})
            if "workspace" in extras and "workspace" not in info:
                info["workspace"] = extras["workspace"]  # 兼容键（单域提升）
        return info

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

    @mcp.tool
    @audited("skill_read")
    async def skill_read(name: str) -> dict:
        """读取 skill 全文（渐进披露二级内容，auto 类；一览见 sys_get_info.skills）。"""
        try:
            return {"name": name, "body": skill_loader.read_skill(name)}
        except ValueError as exc:
            raise ToolError(_ta_payload(TaError(
                TA_E_POLICY, str(exc), domain="skills",
                detail={"known": [s.name for s in skill_loader.load_skills()]},
            ))) from exc

    # ---- 域装配（组合根传入；平台不感知具体域）----------------------------
    for pack in packs:
        pack.mount(api)
    return mcp
