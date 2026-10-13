# SPDX-License-Identifier: Apache-2.0
"""渲染层（LLD-A09 §5）：事件 → 字符串的纯函数（无 IO——单测直接断言）。

行式渲染（非全屏 TUI）：无 curses 依赖、输出可重定向、--json 同源。
"""

from __future__ import annotations

from typing import Any

_PLAN_MARK = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}


def render_plan(items: list[dict[str, Any]]) -> str:
    lines = [f"{_PLAN_MARK.get(it.get('status'), '[?]')} {it.get('id')}: {it.get('desc')}"
             for it in items]
    return "\n".join(lines) or "（空计划）"


def render_state(ev: dict[str, Any]) -> str:
    state = ev.get("state", "")
    extra = ev.get("package") or ""
    return f"== {state} == {extra}".rstrip()


def render_round(ev: dict[str, Any]) -> str:
    done = "完成声明" if ev.get("declared_done") else "编辑中"
    summary = ev.get("summary") or ""
    line = f"· 第 {ev.get('round')}/{ev.get('budget')} 轮 {done}"
    if summary:
        line += f" — {summary[:120]}"
    return line


def render_evidence(ev: dict[str, Any]) -> str:
    return f"! 验证不通过：{ev.get('step')}（第 {ev.get('round')} 轮）——证据已回喂"


def render_final(result: Any) -> str:
    """终报（LLD-A09 §4）：状态/判据/产物/工作区/预算。"""
    lines = [
        "―――― 终报 ――――",
        f"状态：{result.state}",
        f"轮次：{result.rounds_used}",
    ]
    if result.failure_reason:
        lines.append(f"未收敛：{result.failure_reason}")
    if result.evidence_log:
        lines.append(f"证据条数：{len(result.evidence_log)}（工作区留档）")
    if result.artifact is not None and result.artifact.ok:
        lines.append(f"产物：{result.artifact.package_path}")
    lines.append(f"工作区：{result.workspace}")
    return "\n".join(lines)


RENDERERS = {
    "plan": lambda ev: render_plan(ev.get("items", [])),
    "state": render_state,
    "round": render_round,
    "evidence": render_evidence,
    "final": lambda ev: f"终态：{ev.get('state')}（{ev.get('rounds')} 轮）",
}


def render_event(kind: str, data: dict[str, Any]) -> str | None:
    fn = RENDERERS.get(kind)
    if fn is None:
        return None
    return fn(data)
