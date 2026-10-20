# SPDX-License-Identifier: Apache-2.0
"""网关钩子链（D4 · DEC-67①③；D4b/A4 post 面）：MCP 工具调用前拦截 +
调用后观察——config 声明、首匹配生效（pre）/全匹配外发（post）。

- **pre 面**：deny = 结构化拒绝（TA_E_POLICY + rule_id 归因），observe =
  留观放行。服务端闸 = 管所有渠道（含未来外部 harness 客户端）的真边界
  （R11 §6.2——pi 缺省无逐调用审批，服务端闸更不可或缺）。
- **post 面（A4 · LLD-A15 §4）**：调用后结果摘要经钩子外发——observe-only
  （post deny 语义为空，规则解析期拒收）；摘要 = {tool, dur_ms, state,
  result_preview}，经事件总线 `hook.post` 事件外发（W2 SSE 消费）——诊断
  自动注入缝（v1 仅外发；消费侧闭环随诊断批）。

规则形态（config [hooks]，坏条目跳过不静默生效——compose 容错纪律）：
  [[hooks]]
  when = "pre" | "post"     # pre = 拦截；post = 观察（A4）
  match_tool = "app_deploy" # 精确名或 "prefix*" 形态前缀
  action = "deny" | "observe"   # pre 两可；post 仅 observe
  reason = "维护窗"
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

# 来源: A4——post 摘要 result_preview 截断（审计/事件面尺寸有界）
RESULT_PREVIEW_MAX = 400


@dataclass
class HookRule:
    rule_id: str
    when: str  # "pre" | "post"（A4）
    match_tool: str  # 精确工具名或 "prefix:*"
    action: str  # "deny" | "observe"（post 仅 observe）
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
        if when == "pre":
            if not match_tool or action not in ("deny", "observe"):
                continue
        elif when == "post":
            # post deny 语义为空（调用已发生）——解析期拒收不静默生效
            if not match_tool or action != "observe":
                continue
        else:
            continue
        out.append(HookRule(
            rule_id=f"h{i}",
            when=str(when),
            match_tool=str(match_tool),
            action=str(action),
            reason=str(spec.get("reason", "")),
        ))
    return out


def _match(rule_tool: str, tool: str) -> bool:
    if rule_tool.endswith("*"):
        return tool.startswith(rule_tool[:-1])
    return rule_tool == tool


class HookChain:
    def __init__(self, rules: list[HookRule] | None = None) -> None:
        self.rules = list(rules or [])

    def pre(self, tool: str) -> HookVerdict | None:
        """首匹配裁决；无匹配 = None（放行）。"""
        for r in self.rules:
            if r.when != "pre" or not _match(r.match_tool, tool):
                continue
            return HookVerdict(rule=r, action=r.action, reason=r.reason)
        return None

    def post(self, tool: str, summary: dict[str, Any]) -> list[HookVerdict]:
        """post 面全匹配（A4）：返回全部命中观察规则——调用方逐条外发。"""
        return [HookVerdict(rule=r, action=r.action, reason=r.reason)
                for r in self.rules
                if r.when == "post" and r.action == "observe"
                and _match(r.match_tool, tool)]

    @staticmethod
    def summarize(tool: str, dur_ms: int, state: str,
                  result: Any) -> dict[str, Any]:
        """结果摘要（尺寸有界——result_preview 截断；序列化失败容错）。"""
        try:
            preview = json.dumps(result, ensure_ascii=False, default=str)
        except Exception:  # noqa: BLE001
            preview = repr(result)
        return {"tool": tool, "dur_ms": dur_ms, "state": state,
                "result_preview": preview[:RESULT_PREVIEW_MAX]}


