# SPDX-License-Identifier: Apache-2.0
"""domain/criteria — 判据窗引擎（AC-3 · DEC-82）。

判据窗方法学（ds41 双板部署实证——一六一⑥）升格为 Agent 侧机械面：
**CONNECTED 切段**（CH343 开埠复位脉动会混入上一实例残留行——判据窗必须
以段标记行切段取末段）+ 两类机械规则（present 存在性 / monotonic 单调性）。

纯函数引擎：输入 = 文本行列表 + 规则集；输出 = 结构化报告。三个消费面：
① MCP `app_criteria_run`（真机串口窗）；② `domain/wasm_sim.py`（创作 wasm
PC 侧执行器的判据行核验）；③ eval --with-sim。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# 规则 v1（DEC-82④）：present（行存在 ≥ min_count）/ monotonic（模式提取
# 整数组严格递增——样本 ≥2 才可判单调，否则证据不足判失败）。
RULE_TYPES = ("present", "monotonic")


@dataclass
class CriteriaReport:
    segment_lines: int = 0
    segments_seen: int = 0
    rules: list[dict[str, Any]] = field(default_factory=list)

    @property
    def overall_ok(self) -> bool:
        return bool(self.rules) and all(r["ok"] for r in self.rules)

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_lines": self.segment_lines,
            "segments_seen": self.segments_seen,
            "overall_ok": self.overall_ok,
            "rules": self.rules,
        }

    def render_evidence(self, title: str = "判据窗核验") -> str:
        """修复链可直喂文本（S8 repair / deploy 诊断通道组合面——DEC-82⑤）。"""
        lines = [f"【{title}】overall={'PASS' if self.overall_ok else 'FAIL'}",
                 f"切段标记命中 {self.segments_seen} 次；窗内行 {self.segment_lines}"]
        for r in self.rules:
            head = f"- [{r['type']}] {r['pattern']}: {'PASS' if r['ok'] else 'FAIL'}"
            body = f"（samples={r.get('samples', r.get('count', 0))}）"
            if not r["ok"] and r.get("detail"):
                body += f" {r['detail']}"
            lines.append(head + body)
        return "\n".join(lines)


def _segment(lines: list[str], marker: str | None) -> tuple[list[str], int]:
    """切段：取**最后一个** marker 之后的行（无 marker = 全文单段）。"""
    if not marker:
        return list(lines), 0
    idx = -1
    hits = 0
    for i, ln in enumerate(lines):
        if marker in ln:
            idx = i
            hits += 1
    if idx < 0:
        return list(lines), 0  # 无标记命中 = 全文（调用方规则可判 present 失败）
    return lines[idx + 1:], hits


def _extract_ints(pattern: str, group: int, lines: list[str]) -> list[int]:
    rx = re.compile(pattern)
    out: list[int] = []
    for ln in lines:
        m = rx.search(ln)
        if m:
            try:
                out.append(int(m.group(group)))
            except (IndexError, ValueError):
                continue
    return out


def judge_lines(lines: list[str], rules: list[dict[str, Any]],
                segment_marker: str | None = None) -> CriteriaReport:
    """机械判定。rules 元素：{"type": "present"|"monotonic", "pattern": str,
    可选 "min_count"(present 缺省 1) / "group"(monotonic 缺省 1——正则捕获组)}。
    非法规则类型 = ValueError（fail-closed）。"""
    window, hits = _segment(lines, segment_marker)
    rep = CriteriaReport(segment_lines=len(window), segments_seen=hits)
    for rule in rules:
        rtype = rule.get("type")
        pattern = rule.get("pattern")
        if rtype not in RULE_TYPES or not pattern:
            raise ValueError(f"判据规则非法: {rule!r}（type ∈ {RULE_TYPES}）")
        entry: dict[str, Any] = {"type": rtype, "pattern": pattern}
        matched = [ln for ln in window if re.search(pattern, ln)]
        if rtype == "present":
            min_count = int(rule.get("min_count", 1))
            entry["count"] = len(matched)
            entry["ok"] = len(matched) >= min_count
            if not entry["ok"]:
                entry["detail"] = f"命中 {len(matched)} < 要求 {min_count}"
        else:  # monotonic
            group = int(rule.get("group", 1))
            nums = _extract_ints(pattern, group, window)
            entry["samples"] = nums[:32]
            mono = all(b > a for a, b in zip(nums, nums[1:], strict=False))
            entry["ok"] = mono and len(nums) >= 2
            if not entry["ok"]:
                entry["detail"] = (
                    f"样本 {len(nums)}（需 ≥2）"
                    + ("" if len(nums) >= 2 and not mono else "；非严格单调")
                    if len(nums) >= 2 and not mono else f"样本 {len(nums)}（需 ≥2）")
        rep.rules.append(entry)
    return rep
