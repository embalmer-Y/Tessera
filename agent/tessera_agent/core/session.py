# SPDX-License-Identifier: Apache-2.0
"""会话编排核心（LLD-A02，MA1 最小集）。

审批闸落点（MA1 形态）：**工具包装层**——所有注册给 PydanticAI Agent 的工具
（含自建编辑工具）经 `gated_tool` 装饰：strict 类先向 ApprovalBroker 请求并等待，
deny/超时返回结构化拒绝消息给模型（不抛裸异常）。等效 wrap_tool_execute 语义；
后续可替换为 PydanticAI 原生 Hooks（R5 §A3 事实已核验其存在）。
Frontend 抽象（ACP 预留缝，DEC-35）：McpFrontend = 任务日志行 + sys_pending_approvals
呈现（MA3 接 ACP 适配器时不改编排层）。
"""

from __future__ import annotations

import functools
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from tessera_agent.common.audit import args_preview
from tessera_agent.common.errors import TaError
from tessera_agent.common.limits import ContextBudget
from tessera_agent.gateway.approvals import ApprovalBroker

# 审批类别（HLD §5.1 / LLD-A01 §2 表）：auto 直行 / confirm 会话内直行（可经 config
# 收紧为挂起）/ strict 必须宿主批准。
CATEGORIES = ("auto", "confirm", "strict")


@dataclass
class PolicyTable:
    """工具名 → 类别；只可收紧不可放宽（收紧覆写经 config [policy]）。"""

    entries: dict[str, str] = field(default_factory=dict)

    def category_of(self, tool: str, declared: str = "auto") -> str:
        override = self.entries.get(tool)
        if override is None:
            return declared
        rank = {c: i for i, c in enumerate(CATEGORIES)}
        return override if rank[override] >= rank[declared] else declared


def gated_tool(
    name: str,
    broker: ApprovalBroker,
    category: str = "auto",
    policy: PolicyTable | None = None,
) -> Callable:
    """把异步函数包装为带审批闸的 agent 工具。"""

    def deco(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        cat = policy.category_of(name, category) if policy else category

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            if cat == "strict":
                approval = broker.request(name, args_preview(dict(kwargs)), reason="strict 工具")
                try:
                    await broker.wait(approval)
                except TaError as exc:
                    return f"工具 {name} 被拒绝：{json.dumps(exc.to_payload(), ensure_ascii=False)}"
            try:
                return await fn(*args, **kwargs)
            except TaError as exc:
                return f"工具 {name} 失败：{json.dumps(exc.to_payload(), ensure_ascii=False)}"

        return wrapper

    return deco


class PlanDto(BaseModel):
    """app_develop 的计划产物（LLD-A02 §4；结构化强制校验的 MA1 示例载体）。"""

    dto_version: int = 1
    requirements_summary: str
    steps: list[str]
    test_plan: list[str]


async def maybe_compress(
    turns: list[str],
    budget: ContextBudget,
    summarize: Callable[[str], Awaitable[str]],
) -> tuple[list[str], bool]:
    """上下文压缩（DEC-38 #6）：总 token 估算超窗口 70% → 远段摘要 + 保留近段。

    V1 语义：turns 为已渲染文本轮次（ModelMessage 级集成随 MA3 高层链接入）；
    返回 (新轮次列表, 是否压缩)。摘要轮带固定头，进入审计由调用方负责。
    """
    total = sum(budget.estimate_tokens(t) for t in turns)
    if total <= budget.compress_at_tokens:
        return turns, False
    keep_budget = int(budget.window_tokens * 0.35)  # 阈值内预算的后 50%（LLD-A02 §2）
    kept: list[str] = []
    kept_tokens = 0
    for turn in reversed(turns):
        t = budget.estimate_tokens(turn)
        if kept_tokens + t > keep_budget:
            break
        kept.append(turn)
        kept_tokens += t
    kept.reverse()
    head = "\n".join(t for t in turns[: len(turns) - len(kept)])
    summary = await summarize(head)
    return ["[summary] 早期会话压缩摘要：\n" + summary, *kept], True
