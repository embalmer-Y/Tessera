# SPDX-License-Identifier: Apache-2.0
"""eval.report — AC-1 评分报告渲染（JSON + markdown 双形态，DEC-81）。"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from tessera_agent.eval.scorer import TaskScore

_ORDER = {"PASS": 0, "PARTIAL": 1, "FAIL": 2}


def suite_summary(scores: list[TaskScore]) -> dict[str, Any]:
    done = [s for s in scores if s.verdict != "FAIL"]
    passed = [s for s in scores if s.verdict == "PASS"]
    rounds = [s.rounds for s in done if s.rounds is not None]
    return {
        "tasks": len(scores),
        "pass": len(passed),
        "partial": len([s for s in scores if s.verdict == "PARTIAL"]),
        "fail": len([s for s in scores if s.verdict == "FAIL"]),
        "pass_rate": round(len(passed) / len(scores), 3) if scores else 0.0,
        "avg_rounds_done": round(sum(rounds) / len(rounds), 2) if rounds else None,
        "total_elapsed_s": round(sum(s.elapsed_s for s in scores), 1),
    }


def report_dict(scores: list[TaskScore], *, model: str,
                with_sim: bool) -> dict[str, Any]:
    return {
        "suite": "tessera-agent-eval/1 (AC-1, DEC-81)",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": model,
        "sim_section": "run" if with_sim else "skip（AC-3 判据闭环单元补全场景定义）",
        "summary": suite_summary(scores),
        "tasks": [s.to_dict() for s in scores],
    }


def render_markdown(rep: dict[str, Any]) -> str:
    lines = [
        "# Tessera Agent 能力评估报告（AC-1 基准）",
        "",
        f"- 套件：`{rep['suite']}`",
        f"- 生成：{rep['generated_at']}",
        f"- 模型：`{rep['model']}`",
        f"- sim 段：{rep['sim_section']}",
        "",
        "## 汇总",
        "",
        "| 指标 | 值 |",
        "|---|---|",
    ]
    s = rep["summary"]
    lines += [
        f"| 任务数 | {s['tasks']} |",
        f"| PASS | {s['pass']} |",
        f"| PARTIAL | {s['partial']} |",
        f"| FAIL | {s['fail']} |",
        f"| 通过率 | {s['pass_rate']} |",
        f"| 平均轮数（非 FAIL） | {s['avg_rounds_done']} |",
        f"| 总耗时 | {s['total_elapsed_s']}s |",
        "",
        "## 任务明细",
        "",
        "| 任务 | 判定 | 轮数 | 耗时s | 未过项 |",
        "|---|---|---|---|---|",
    ]
    for t in sorted(rep["tasks"], key=lambda x: _ORDER.get(x["verdict"], 9)):
        failed = [k for k, v in (t["checks"] or {}).items() if not v["ok"]]
        lines.append(
            f"| {t['id']} {t['title']} | {t['verdict']} | {t['rounds']} | "
            f"{t['elapsed_s']} | {', '.join(failed) or '—'}"
            + (f"（{t['error'][:60]}）" if t["error"] else "") + " |")
    lines += ["", "## 检查矩阵（✓/✗）", ""]
    all_keys: list[str] = []
    for t in rep["tasks"]:
        for k in (t["checks"] or {}):
            if k not in all_keys:
                all_keys.append(k)
    header = "| 任务 | " + " | ".join(all_keys) + " |"
    sep = "|---" * (len(all_keys) + 1) + "|"
    lines += [header, sep]
    for t in rep["tasks"]:
        cells = []
        for k in all_keys:
            v = (t["checks"] or {}).get(k)
            cells.append("—" if v is None else ("✓" if v["ok"] else "✗"))
        lines.append(f"| {t['id']} | " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def write_reports(rep: dict[str, Any], out_dir: str,
                  stem: str) -> tuple[str, str]:
    """落 JSON + markdown 双形态，返回两文件路径。"""
    from pathlib import Path

    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    jp = d / f"{stem}.json"
    mp = d / f"{stem}.md"
    jp.write_text(json.dumps(rep, ensure_ascii=False, indent=2),
                  encoding="utf-8")
    mp.write_text(render_markdown(rep), encoding="utf-8")
    return str(jp), str(mp)
