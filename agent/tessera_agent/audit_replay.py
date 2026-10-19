# SPDX-License-Identifier: Apache-2.0
"""决策链回放（D5 · DEC-67①）：持久审计流（ToolAudit JSONL）→ 统一时间线。

数据源 = 审计 JSONL（tools/{YYYYMMDD}.jsonl——进程重启后仍可回放的 durable
面；TaskRegistry 日志为内存态不属回放域）。条目语义派生：
  sys_approve = 审批决定（D4 allow-session 三维）
  sys_answer  = 问询应答（D7）
  其余        = 工具命令（state: ok/failed/hook_denied——D4 拦截留痕）
pi 会话树（R11 §6.1）取线性子集；HTML 导出随 W1 时间线面评估（余项）。
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

STATE_GLYPH = {"ok": "✓", "failed": "✗", "hook_denied": "⛔"}
SEMANTIC_TOOLS = {"sys_approve": "审批", "sys_answer": "问询"}


def _day_files(audit_dir: Path, day: str | None) -> list[Path]:
    tools_dir = audit_dir / "tools"
    if not tools_dir.is_dir():
        return []
    if day and day != "all":
        p = tools_dir / f"{day}.jsonl"
        return [p] if p.is_file() else []
    return sorted(tools_dir.glob("*.jsonl"))


def load_timeline(audit_dir: Path, *, day: str | None = None,
                  task_id: str | None = None, tool: str | None = None,
                  limit: int = 500) -> dict[str, Any]:
    """审计 JSONL → 时间线条目（ts 升序；过滤条件 AND；尾部 limit 截取）。"""
    rows: list[dict[str, Any]] = []
    files = _day_files(audit_dir, day)
    for p in files:
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue  # 坏行跳过（回放面不因脏数据崩）
    if task_id:
        rows = [r for r in rows if r.get("task_id") == task_id]
    if tool:
        rows = [r for r in rows if r.get("tool") == tool]
    rows.sort(key=lambda r: r.get("ts", 0.0))
    total = len(rows)
    rows = rows[-limit:]
    entries = []
    for r in rows:
        ts = r.get("ts", 0.0)
        state = r.get("state", "ok")
        kind = SEMANTIC_TOOLS.get(r.get("tool", ""), "命令")
        entries.append({
            "ts": ts,
            "time": time.strftime("%H:%M:%S", time.localtime(ts)),
            "day": time.strftime("%Y-%m-%d", time.localtime(ts)),
            "tool": r.get("tool", ""),
            "kind": kind,
            "state": state,
            "dur_ms": r.get("dur_ms", 0),
            "args_preview": r.get("args_preview", {}),
            "task_id": r.get("task_id"),
        })
    counts: dict[str, int] = {}
    for e in entries:
        key = f"{e['tool']}:{e['state']}"
        counts[key] = counts.get(key, 0) + 1
    return {
        "entries": entries,
        "total": total,
        "truncated": total > len(entries),
        "days": [p.stem for p in files],
        "counts": counts,
        "span": [entries[0]["time"], entries[-1]["time"]] if entries else [],
    }


def render_timeline(tl: dict[str, Any]) -> str:
    """时间线文本渲染（CLI replay 缺省形态——线性 + 状态符 + 汇总头）。"""
    out: list[str] = []
    days = "/".join(tl.get("days", []) or ["—"])
    span = " → ".join(tl.get("span", []) or ["—"])
    out.append(f"决策链时间线（{days} · {span} · {tl['total']} 条"
               + ("，已截尾" if tl.get("truncated") else "") + "）")
    for key, n in sorted(tl.get("counts", {}).items()):
        out.append(f"  {key}: {n}")
    out.append("")
    for e in tl.get("entries", []):
        glyph = STATE_GLYPH.get(e["state"], "·")
        line = f"[{e['time']}] {glyph} {e['tool']} ({e['kind']}, {e['dur_ms']}ms)"
        if e.get("task_id"):
            line += f" task={e['task_id']}"
        args = e.get("args_preview") or {}
        interesting = {k: v for k, v in args.items()
                       if k in ("decision", "answer", "approval_id",
                                "question_id", "spec", "package_path")}
        if interesting:
            line += f" {json.dumps(interesting, ensure_ascii=False)}"
        out.append(line)
    return "\n".join(out)
