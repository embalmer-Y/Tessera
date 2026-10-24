# SPDX-License-Identifier: Apache-2.0
"""硬件事实域（HW · LLD-agent-hardware-targeting v0.3——DEC-73 + HW-4 五面）。

确定性机械面（零 LLM）：画像目录装载 / caps×画像机械核对门（装前拒——
soft-pass/hard-invalid 缺口补位）/ 【目标硬件】段合成（创作链注入事实）/
Zephyr 收录本地检索 / 选型候选内存预筛 / spec 资源×画像能力缺口核对。

真相源纪律：画像 [hardware] 引脚级事实 = 物理绑定的唯一真相源；无画像 /
无 [hardware] 节 = 全部面按「画像无事实」跳过（旧画像零扰动，不静默改判）。
LLM 只做语义理解（S0 分支编排/候选生成），判定全部本模块机械完成。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tessera_agent.domain import board_validation as bv

# 常用装载面 re-export（clarify/firmware 经本模块统一入口）
from tessera_agent.domain.board_validation import (  # noqa: F401
    ProfileError,
    load_profile,
)

# 来源: LLD-agent-hardware-targeting §7.3——物理域 caps 解析（spec_gate._CAP_RE 同文法子集）
_CAP_SPLIT_RE = re.compile(
    r"^(gpio|pwm|adc|av):(read|write|set|list|delete):"
    r"([0-3])(?:-([0-3]))?(?:,([0-3](?:-[0-3])?))*$")

# 选型内存预筛口径（docs/memory-baseline.md v0.1 实测推导：最小 net 档在
# 512KB 级 SoC 上 heap 139K——低于 512KB 总内存跑不动 zenoh+TLS 数据面）
RESEARCH_MIN_TOTAL_RAM_KB = 512


# ---- 画像目录 ---------------------------------------------------------------

def boards_dir(cfg: Any) -> Path:
    return Path(cfg.workspace_repo) / "agent" / "boards"


def catalog_ids(cfg: Any) -> list[str]:
    return bv.list_profiles(boards_dir(cfg))


def load_bound_profile(cfg: Any) -> bv.BoardProfile | None:
    """按配置 board_profile 解析绑定画像；未配置/文件缺失 = None（跳过面）。"""
    pid = getattr(cfg, "board_profile", "")
    if not pid:
        return None
    p = boards_dir(cfg) / f"{pid}.toml"
    if not p.is_file():
        return None
    try:
        return bv.load_profile(p)
    except bv.ProfileError:
        return None


# ---- HW-4 ③ caps×画像机械核对门 ---------------------------------------------

def expand_cap_instances(cap: str) -> list[tuple[str, int]]:
    """物理域 cap 文法 → (domain, instance) 全列；非物理域/文法外 = 空列
    （门只核对物理域——power/fs/log/kv/msg/sys 豁免）。"""
    cap = cap.strip()
    m = re.match(r"^(\w+):(\w+):(.+)$", cap)
    if not m:
        return []
    domain, _op, inst = m.groups()
    if domain not in bv.HW_PHYSICAL_DOMAINS:
        return []
    out: list[tuple[str, int]] = []
    for part in inst.split(","):
        part = part.strip()
        if re.fullmatch(r"[0-3]-[0-3]", part):
            lo, hi = (int(x) for x in part.split("-"))
            out.extend((domain, i) for i in range(lo, hi + 1))
        elif re.fullmatch(r"[0-3]", part):
            out.append((domain, int(part)))
    return out


def check_caps_against_profile(caps: list[str],
                               profile: bv.BoardProfile) -> list[str]:
    """caps×画像机械核对（LLD-agent-hardware-targeting §7.3）：申请的物理通道实例在画像无物理
    绑定 → 违规串列表（空 = 过）。画像无 [hardware] = 跳过（[]，调用方
    以 hardware_facts_present 区分「过」与「未核对」）。"""
    hw = profile.hardware
    if hw is None:
        return []
    violations: list[str] = []
    for cap in caps:
        for domain, inst in expand_cap_instances(cap):
            if hw.bound(domain, inst) is None:
                violations.append(cap)
                break
    return violations


# ---- HW-4 ② 【目标硬件】段合成（创作链注入） ---------------------------------

def hardware_facts_brief(profile: bv.BoardProfile) -> str:
    """画像硬件事实 → LLM 可读摘要（注入 spec【目标硬件】段）。"""
    hw = profile.hardware
    lines = [f"board={profile.id}"]
    if hw is None:
        lines.append("facts=none（画像未含 [hardware] 事实节——通道物理绑定"
                     "未知，禁止假设任何通道对应板载外设）")
        return "；".join(lines)
    if hw.soc:
        lines.append(f"soc={hw.soc}")
    if hw.ram_kb or hw.psram_kb:
        lines.append(f"ram={hw.ram_kb}KB+psram={hw.psram_kb}KB")
    if hw.pins:
        pins = "；".join(
            f"{p.name}={p.domain}:{p.instance}（{p.desc}）" if p.desc
            else f"{p.name}={p.domain}:{p.instance}"
            for p in hw.pins)
        lines.append(f"板载硬件: {pins}")
        bound = {p.domain for p in hw.pins}
        lines.append("可用物理通道域: " + "/".join(sorted(bound))
                     + "——caps 只允许申请以上域中已列实例；未列出的通道"
                       "无物理绑定，申请即被部署门装前拒绝")
    else:
        lines.append("facts=pins-empty（[hardware] 节无 pin 条目——禁用一切"
                     "物理通道假设）")
    return "；".join(lines)


def target_hw_section(text: str) -> str:
    return f"【目标硬件】{text}"


def append_hw_section(spec: str, section_text: str) -> str:
    """spec 追加【目标硬件】段（幂等——已有段不重复追加）。"""
    if "【目标硬件】" in spec:
        return spec
    return spec.rstrip() + "\n" + target_hw_section(section_text) + "\n"


# ---- HW-1 分支 B：Zephyr 收录本地检索 ---------------------------------------

_BOARD_NAME_RE = re.compile(r"^\s*(?:-\s*)?name:\s*(\S+)", re.M)


def zephyr_local_index(west_workspace: Path) -> dict[str, str]:
    """本地 zephyr/boards/*/*/board.yml 板名索引（name → 相对路径）。
    检索失败/目录缺失 = 空 dict（联网核实为推定态）。"""
    root = Path(west_workspace) / "zephyr" / "boards"
    index: dict[str, str] = {}
    if not root.is_dir():
        return index
    for yml in root.glob("*/*/board.yml"):
        try:
            text = yml.read_text(encoding="utf-8")
        except OSError:
            continue
        for m in _BOARD_NAME_RE.finditer(text):
            index.setdefault(m.group(1), str(yml.relative_to(root)))
    return index


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def check_zephyr_inclusion(hint: str, west_workspace: Path) -> dict[str, Any]:
    """分支 B 收录检查·本地半（联网核实半在 clarify 编排——web 可选）。
    匹配 = 归一化（小写字母数字）双向子串（「XIAO ESP32-S3」↔
    「xiao_esp32s3」同族形态可中）。"""
    needle = _norm(hint)
    hits: dict[str, str] = {}
    if needle:
        for name, rel in zephyr_local_index(west_workspace).items():
            low = _norm(name)
            if needle in low or low in needle:
                hits[name] = rel
    return {"hint": hint, "included": bool(hits), "matches": hits,
            "source": "local-boards"}


# ---- HW-3 联网选型·机械预筛 ---------------------------------------------------

def prefilter_candidates(candidates: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, str]]]:
    """候选机械预筛（LLD-agent-hardware-targeting §3）：总内存（ram+psram）低于 net 档口径 →
    剔除并标注（LLM 候选只做语义理解，剔除判定机械）。返回 (保留, 剔除)。
    内存字段缺失 = 不剔除但标 presumed-unknown（推定态注记）。"""
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, str]] = []
    for c in candidates:
        ram = int(c.get("ram_kb") or 0)
        psram = int(c.get("psram_kb") or 0)
        total = ram + psram
        if 0 < total < RESEARCH_MIN_TOTAL_RAM_KB:
            dropped.append({
                "model": str(c.get("model", "?")),
                "reason": f"总内存 {total}KB 低于最小 net 档口径 "
                          f"{RESEARCH_MIN_TOTAL_RAM_KB}KB"
                          "（memory-baseline v0.1——zenoh+TLS 数据面跑不动）"})
            continue
        c = dict(c)
        c.setdefault("presumed", True)  # 推定态——采购+BV1 验证前不做能力承诺
        if total == 0:
            c["memory_unverified"] = True
        kept.append(c)
    return kept, dropped


# ---- HW-1 ③ 能力缺口核对（spec 资源 × 画像事实） -----------------------------

def capability_gaps(caps: list[str], profile: bv.BoardProfile) -> list[str]:
    """需求 caps × 画像物理绑定 → 缺口描述列表（外接/换板问询的判定源）。"""
    hw = profile.hardware
    if hw is None:
        return []
    gaps: list[str] = []
    for cap in caps:
        pairs = expand_cap_instances(cap)
        if not pairs:
            continue
        dom = pairs[0][0]
        if not hw.domain_pins(dom):
            gaps.append(f"{cap}——画像 {profile.id} 无 {dom} 域物理绑定")
    return gaps
