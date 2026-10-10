# SPDX-License-Identifier: Apache-2.0
"""spec 质量门（NV-2，V0.1.0 编程链路完整性批）。

spec 是编程链路的单一事实源——但自由文本 spec 的判据是隐式的（修复闭环
NV-1 的 pass_patterns 与 spec 两处手写已现不一致风险）。本门做两件事：
① 推广四节模板（【需求】【资源】【判据】【安全声明】）；
② 机器解析【判据】节引号串 → pass_patterns（spec 即判据单一事实源），
   供 repair_loop / sim↔real 对拍（NV-3）机械消费。

分级：errors（硬伤，app_develop 入口阻塞）/ warnings（提示，log 留痕）。
旧式自由文本 spec 兼容：无节标记 → warning 不阻塞，不派生 patterns。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

#: 四节模板标记（行首；容全角空格）
SECTIONS = ("需求", "资源", "判据", "安全声明")
_SEC_RE = re.compile(r"^【(需求|资源|判据|安全声明)】\s*")

#: 【判据】节引号串提取（ASCII 双引号 + 中文引号；串内禁换行）
_QUOTED_RE = re.compile(r'["“]([^"”\n]{3,120})["”]')

#: ts_perm_v1 文法（对齐 app_chain 提示词内联文法；实例段 0-3 集合形态）
_CAP_RE = re.compile(
    r"^(gpio|pwm|adc|power|fs|av|msg|sys):"
    r"(read|write|set|list|delete):"
    r"([0-3](-[0-3])?(,[0-3](-[0-3])?)*)$"
)
_CAPS_LIST_RE = re.compile(r"caps\s*=\s*\[([^\]]*)\]")
_FS_PATHS_LIST_RE = re.compile(r"fs_paths\s*=\s*\[([^\]]*)\]")

_SAFETY_KEYS = ("限幅", "安全", "确定性", "越权", "保护层")

#: 判据串最短长度（太短 = 噪声误提，如单个 OK/0）
_MIN_PATTERN_LEN = 3


@dataclass
class SpecGateResult:
    """质量门结果：错误（阻塞级）/ 警告（提示级）/ 机器判据派生。"""

    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    pass_patterns: list[str] = field(default_factory=list)
    templated: bool = False


def _split_sections(spec: str) -> dict[str, str]:
    """按节标记切分；无标记返回空 dict（旧式自由文本）。"""
    out: dict[str, str] = {}
    cur: str | None = None
    buf: list[str] = []
    for ln in spec.splitlines():
        m = _SEC_RE.match(ln.strip())
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur = m.group(1)
            buf = [ln.strip()[m.end():]]
        elif cur is not None:
            buf.append(ln)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def check_spec(spec: str) -> SpecGateResult:
    """对 spec 做质量门检查（纯文本函数，CI 可全量测试）。"""
    res = SpecGateResult(ok=True)
    if not spec or not spec.strip():
        res.errors.append("spec 为空")
        res.ok = False
        return res

    sections = _split_sections(spec)
    if not sections:
        res.warnings.append(
            "spec 未用四节模板（【需求】【资源】【判据】【安全声明】）——"
            "判据不可机读，修复闭环须显式传 pass_patterns"
        )
        return res
    res.templated = True

    for name in SECTIONS:
        if name not in sections:
            res.errors.append(f"缺【{name}】节")

    # 判据节：引号串 ≥1 条（机器可判据 = 闭环/对拍的消费面）
    verdict = sections.get("判据", "")
    patterns = [p for p in _QUOTED_RE.findall(verdict)
                if len(p) >= _MIN_PATTERN_LEN]
    if verdict.strip() and not patterns:
        res.errors.append("【判据】节无引号包裹的精确判据串（≥3 字符）")
    elif not verdict.strip() and "判据" in sections:
        res.errors.append("【判据】节为空")
    res.pass_patterns = patterns

    # 资源节：caps 文法 + fs_paths 绝对路径（提示级——与固件走查的差异
    # 交 manifest 硬校验兜底，这里只做早期提示）
    resrc = sections.get("资源", "")
    m = _CAPS_LIST_RE.search(resrc)
    if m:
        for cap in re.findall(r'"([^"]+)"', m.group(1)):
            if not _CAP_RE.match(cap):
                res.warnings.append(f"caps 文法可疑: {cap!r}（ts_perm_v1: "
                                    "class:op:instances）")
    m = _FS_PATHS_LIST_RE.search(resrc)
    if m:
        for p in re.findall(r'"([^"]+)"', m.group(1)):
            if not p.startswith("/") or ".." in p:
                res.warnings.append(f"fs_paths 条目须绝对路径且禁 ..: {p!r}")

    # 安全声明节：存在 + 关键词命中（弱启发式，提示级）
    safety = sections.get("安全声明", "")
    if safety.strip() and not any(k in safety for k in _SAFETY_KEYS):
        res.warnings.append("【安全声明】节未提及任何安全关键词"
                            f"（{'/'.join(_SAFETY_KEYS)}）")

    res.ok = not res.errors
    return res
