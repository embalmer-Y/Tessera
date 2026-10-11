# SPDX-License-Identifier: Apache-2.0
"""sim↔real 语义对拍（NV-3，V0.1.0）。

形态现实：sim 侧判据 = L4 重放写序列（JSONL：ch/value_u/t_ms，M1 定稿
接口）；真机侧判据 = bench console 判据行（含读数）。逐字节 diff 不可行
（形态不对等），V1 口径 = **语义对拍**：同一场景下「各通道终态值」键值
集机械 diff（D9「合同 3 双证据」人工版的机械化——断链 fail-safe 落驱动
值 sim 写序列 vs 真机判据行读数）。

真机首基线随 NV-6 版本验收链产生（全流程本就要跑 sim→real）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimRealDiff:
    """对拍结果：逐通道 match/mismatch/missing。"""

    match: dict[str, Any] = field(default_factory=dict)
    mismatch: dict[str, Any] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)

    @property
    def pass_(self) -> bool:
        return not self.mismatch and not self.missing


def normalize_sim(writes: list[dict[str, Any]],
                  channels: list[str]) -> dict[str, Any]:
    """sim 写序列 → 各通道终态值（最后一次写）。"""
    out: dict[str, Any] = {}
    for w in writes:
        ch = str(w.get("ch", ""))
        if ch in channels:
            out[ch] = w.get("value_u")
    return {c: out[c] for c in channels if c in out}


def normalize_real(console_text: str,
                   patterns: dict[str, str]) -> dict[str, Any]:
    """真机 console → 各通道读数。

    :param patterns: {通道: 判据行正则}——每条须含一个捕获组（数值）；
        取**最后**一次命中（终态语义，与 sim 终态对齐）。
    """
    out: dict[str, Any] = {}
    lines = console_text.splitlines()
    for ch, pat in patterns.items():
        last: Any = None
        rx = re.compile(pat)
        for ln in lines:
            m = rx.search(ln)
            if m:
                raw = m.group(1)
                try:
                    last = int(raw)
                except ValueError:
                    try:
                        last = float(raw)
                    except ValueError:
                        last = raw
        if last is not None:
            out[ch] = last
    return out


def diff(sim_map: dict[str, Any], real_map: dict[str, Any],
         *, tolerance: int = 0) -> SimRealDiff:
    """键值集机械 diff（数值通道容差 = tolerance；非数值须相等）。"""
    res = SimRealDiff()
    for ch, sv in sim_map.items():
        if ch not in real_map:
            res.missing.append(ch)
            continue
        rv = real_map[ch]
        if isinstance(sv, (int, float)) and isinstance(rv, (int, float)):
            ok = abs(sv - rv) <= tolerance
        else:
            ok = sv == rv
        (res.match if ok else res.mismatch)[ch] = {"sim": sv, "real": rv}
    return res


# ---- V2-3 判据行级对拍（sim APP 装载面消费）----

_LOG_PREFIX_RE = re.compile(r"^\[[^\]]*\]\s*")


def normalize_verdict_line(line: str) -> str:
    """判据行归一化：去日志前缀（如 "[app1/l3] "）与时间戳尾缀。"""
    s = _LOG_PREFIX_RE.sub("", line.strip())
    return s.rstrip()


def extract_verdict_lines(console_text: str,
                          patterns: list[str]) -> list[str]:
    """按前缀/子串提取判据行（保持出现顺序，逐行归一化）。"""
    out: list[str] = []
    for ln in console_text.splitlines():
        n = normalize_verdict_line(ln)
        if any(p in n for p in patterns):
            out.append(n)
    return out


def diff_lines(sim_lines: list[str], real_lines: list[str],
               *, tail_align: bool = False) -> dict[str, Any]:
    """判据行序列机械 diff（V2-3 首基线消费）。

    :param tail_align: True = 尾部对齐（真机采集窗口首行截断的采集现实
        容忍——sim 为超集且尾部一致即过；False = 严格全等）。
    """
    sim_cmp, real_cmp = sim_lines, real_lines
    tail_aligned = False
    if tail_align and len(sim_lines) > len(real_lines):
        sim_cmp = sim_lines[-len(real_lines):]
        tail_aligned = True
    mismatch = [
        {"idx": i, "sim": s, "real": r}
        for i, (s, r) in enumerate(zip(sim_cmp, real_cmp, strict=False))
        if s != r
    ]
    ok = (not mismatch) and len(sim_cmp) == len(real_cmp)
    return {"pass": ok, "mismatch": mismatch[:8],
            "sim_len": len(sim_lines), "real_len": len(real_lines),
            "tail_aligned": tail_aligned}
