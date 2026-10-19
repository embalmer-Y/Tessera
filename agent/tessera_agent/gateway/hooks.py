# SPDX-License-Identifier: Apache-2.0
"""网关钩子链（D4 · DEC-67①③）：MCP 工具调用**前**拦截面——config 声明、
首匹配生效；deny = 结构化拒绝（TA_E_POLICY + rule_id 归因），observe = 留观
放行。服务端闸 = 管所有渠道（含未来外部 harness 客户端）的真边界（R11 §6.2
——pi 缺省无逐调用审批，服务端闸更不可或缺）。

v1 范围 = pre 面；post 面（调用后观察）随 A10 审计扩展批（余项登记）。
规则形态（config [hooks]，坏条目跳过不静默生效——compose 容错纪律）：
  [[hooks]]
  when = "pre"          # v1 仅 pre
  match_tool = "app_deploy"   # 精确名或 "prefix*" 形态前缀
  action = "deny" | "observe"
  reason = "维护窗"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HookRule:
    rule_id: str
    when: str  # "pre"（v1 仅此）
    match_tool: str  # 精确工具名或 "prefix:*"
    action: str  # "deny" | "observe"
    reason: str = ""


@dataclass
class HookVerdict:
    rule: HookRule
    action: str
    reason: str


def parse_rules(raw: list[dict[str, Any]] | None) -> list[HookRule]:
    """config 规则 → HookRule（坏条目跳过；rule_id = 序号派生）。"""
    out: list[HookRule] = []
    for i, spec in enumerate(raw or []):
        if not isinstance(spec, dict):
            continue
        when = spec.get("when", "pre")
        match_tool = spec.get("match_tool")
        action = spec.get("action")
        if when != "pre" or not match_tool or action not in ("deny", "observe"):
            continue  # v1 仅 pre；形态非法跳过
        out.append(HookRule(
            rule_id=f"h{i}",
            when="pre",
            match_tool=str(match_tool),
            action=str(action),
            reason=str(spec.get("reason", "")),
        ))
    return out


class HookChain:
    def __init__(self, rules: list[HookRule] | None = None) -> None:
        self.rules = list(rules or [])

    def pre(self, tool: str) -> HookVerdict | None:
        """首匹配裁决；无匹配 = None（放行）。"""
        for r in self.rules:
            if r.match_tool.endswith("*"):
                if not tool.startswith(r.match_tool[:-1]):
                    continue
            elif tool != r.match_tool:
                continue
            return HookVerdict(rule=r, action=r.action, reason=r.reason)
        return None
