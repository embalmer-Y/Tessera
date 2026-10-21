# SPDX-License-Identifier: Apache-2.0
"""部署后诊断分类器（NV-1，V0.1.0 编程链路完整性批）。

输入 = 一次真机运行的串口全文（复位后窗口抓取），输出 = 失败类别 +
修复提示 + 证据行。类别链全部来自项目真机历史失败形态（每类注释标注
出处），供修复闭环（repair.py）把类别翻译成 app_develop 的反馈上下文。

纯文本函数，无 I/O——CI 可全量测试（tests/test_diag.py 的向量即历史
单迹摘录）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ---- 类别（判据链按优先级从高到低；同文本多类命中时取链首）----

#: 判据行达成（bench 语义 = PASS 行出现即达成；后续复位循环不改判）
DIAG_PASS = "pass"
#: 环境/介质层失败（挂载/写卡/网络）——与 APP 无关，重生成不救济
DIAG_ENV_BOOT = "env_boot_fail"
#: 安装链失败（begin/chunk/verify/install 任一步错误码）
DIAG_INSTALL_FAIL = "install_fail"
#: 安装完成但 APP 未 ACTIVE（装载拒收 / boot 早期夭折）
DIAG_NOT_ACTIVE = "not_active"
#: 看门狗/系统失败复位循环（含 APP 卡死弃管升级路径，IR2-06）
DIAG_WDT_RESET = "wdt_reset"
#: ACTIVE 后无任何后续输出（健康链终止/配额超限/栈溢出——「静默死」，
#: 板级 BB1 原型形态）
DIAG_APP_SILENT = "app_silent"
#: ACTIVE 且存活心跳在跑但判据行未出现（APP 活着，逻辑未达成）
DIAG_APP_NO_VERDICT = "app_no_verdict"
#: 窗口内无任何有效信号
DIAG_NO_VERDICT = "no_verdict"

#: 类别优先级链（先匹配先得；pass 恒最高）
_PRIORITY = [
    DIAG_PASS, DIAG_ENV_BOOT, DIAG_INSTALL_FAIL, DIAG_NOT_ACTIVE,
    DIAG_WDT_RESET, DIAG_APP_SILENT, DIAG_APP_NO_VERDICT, DIAG_NO_VERDICT,
]

#: 证据行筛选关键词（保留含任一关键词的行，其余丢弃降噪）
_EVIDENCE_KEYS = (
    "PASS", "FAIL", "fail", "error", "Error", "ACTIVE", "active",
    "install", "verify", "chunk", "begin", "mount", "sd:", "fs:",
    "wdt", "WDT", "system_fail", "rst:", "health", "perm",
)

# 每类修复提示（进 app_develop 反馈上下文的修复方向；与类别一一对应）
_REPAIR_HINTS = {
    DIAG_PASS: "判据达成，无需修复。",
    DIAG_ENV_BOOT: (
        "环境/介质层失败（存储挂载或写卡、网络）——与 APP 无关，"
        "重生成 APP 不救济；请检查板卡介质与网络环境后重跑。"
    ),
    DIAG_INSTALL_FAIL: (
        "包安装链失败——检查 manifest 语法（caps ts_perm_v1 文法/exports "
        "必含 health_ping/fs_paths 绝对路径）与包完整性；若错误码出自 "
        "verify 步（负码）则优先排查签名与摘要。"
    ),
    DIAG_NOT_ACTIVE: (
        "安装完成但 APP 未进入 ACTIVE——典型原因：manifest caps 组合被"
        "装载走查拒收（越权类组合 fail-closed）、exports 缺 health_ping、"
        "或 boot 链早期失败。请对照串口 boot 步骤行核对 manifest，"
        "并确认 caps 只声明 spec 真正需要的最小面。"
    ),
    DIAG_WDT_RESET: (
        "看门狗复位循环——APP 存在长阻塞路径（单次 app_tick/app_init "
        "计算或忙等超过喂狗周期，或 health_ping 被重活拖住）。修复：把"
        "长计算拆成多次 app_tick 分片推进；health_ping 保持轻量立即返回；"
        "禁止任何忙等循环。"
    ),
    DIAG_APP_SILENT: (
        "APP 进入 ACTIVE 后无任何后续输出（静默死）——典型原因：单次 "
        "tick 指令量超配额被健康链终止（boardbench BB1 原型：大循环被"
        "终止）、栈溢出、或 init 内死循环。修复：大幅削减单次 tick 的"
        "计算量（循环上限收敛）、避免深递归与大局部数组、确保 app_init "
        "快速返回。"
    ),
    DIAG_APP_NO_VERDICT: (
        "APP 存活但判据行始终未出现——检查：判据输出调用是否走 "
        "ts_log_write 且格式与判据模式精确一致（含前缀与完整单行）；"
        "触发条件是否可达（阈值/输入假设在真机上是否成立）；状态机"
        "是否卡在等待分支。"
    ),
    DIAG_NO_VERDICT: (
        "窗口内无任何有效信号——建议延长抓取窗口或复位后重抓；若复现"
        "仍空，检查串口连接与波特率。"
    ),
}


@dataclass
class DiagResult:
    """分类结果：类别 + 修复提示 + 证据行 + 单行结论。"""

    category: str
    repair_hint: str
    evidence: list[str] = field(default_factory=list)
    summary: str = ""


def _match_pass(lines: list[str], pass_patterns: list[str]) -> bool:
    return any(p and p in ln for ln in lines for p in pass_patterns)


# HW-4 ④⑤（LLD-A16 §7.4/§7.5）：硬件写拒回执扫描——固件 fail-safe 回执的
# app 侧正典形态（ts_gpio_write 等被拒 → app 打 `<TOKEN> WRITE REJECTED`，
# W2 验收 LED 缺陷 168 对实证）。判据行命中而写拒存在 = soft-pass/hard-invalid。
_HW_REJECT_RE = re.compile(r"(\S+)\s+WRITE\s+REJECTED", re.IGNORECASE)


def scan_hardware_rejections(text: str) -> list[dict[str, Any]]:
    """窗口文本硬件写拒聚类：[{token, count, first_line}]（无 = 空列）。"""
    counts: dict[str, int] = {}
    first: dict[str, str] = {}
    for ln in text.splitlines():
        m = _HW_REJECT_RE.search(ln)
        if m:
            token = m.group(1)
            counts[token] = counts.get(token, 0) + 1
            first.setdefault(token, ln.strip())
    return [{"token": t, "count": n, "first_line": first[t]}
            for t, n in sorted(counts.items(), key=lambda kv: -kv[1])]


def _first_match(lines: list[str], keys: tuple[str, ...]) -> str | None:
    for ln in lines:
        if any(k in ln for k in keys):
            return ln
    return None


def classify_run(
    text: str,
    *,
    pass_patterns: list[str],
    alive_patterns: tuple[str, ...] = ("alive",),
    active_keys: tuple[str, ...] = ("ACTIVE", "app active", "app running"),
) -> DiagResult:
    """对一次运行的串口全文做失败分类。

    :param text: 复位后窗口抓取的串口全文
    :param pass_patterns: 判据子串列表（如 ["DS PASS", "DS5 "]）——任一
        子串命中任一行即 pass（bench 契约：判据行出现即达成）
    :param alive_patterns: 存活心跳行关键词（默认 "alive"；bench 惯例）
    :param active_keys: APP 激活行关键词（默认覆盖 "APP ACTIVE" 与
        deploybench 的 "app running" 形态）
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    evidence = [ln.strip() for ln in lines if any(k in ln for k in _EVIDENCE_KEYS)]

    if _match_pass(lines, pass_patterns):
        cat = DIAG_PASS
    elif _first_match(lines, ("mount error", "mount r=-", "fs mount",
                              "Write failed", "DHCP timeout")):
        # 历史原型：dsdbench 坏卡（fs mount -5 + sd: Write failed）；
        # mount/写卡/DHCP 均为介质或网络层，APP 无责
        cat = DIAG_ENV_BOOT
    elif _first_match(lines, ("install r=-", "begin r=-", "chunk r=-",
                              "verify r=-", "FAIL install")):
        # 历史原型：persistbench 安装链分步报码（MD 批：begin/chunk/
        # verify 各步负码）；v2 验签拒收也走 verify 负码
        cat = DIAG_INSTALL_FAIL
    elif not _first_match(lines, active_keys):
        # 无 ACTIVE 行且无安装负码：有意义的 boot 输出（>3 行）= 装载拒收
        # 或早期夭折（not_active）；近乎空窗（≤3 行）= 抓取窗口/连接问题
        # （no_verdict——延长窗口重抓，不误导为装载失败）
        cat = DIAG_NOT_ACTIVE if len(lines) > 3 else DIAG_NO_VERDICT
    elif _first_match(lines, ("task wdt", "WDT-WARN", "system_fail",
                              "wdt reset")):
        # 历史原型：wdtbench 复位循环 / inputdemo 停喂升级链（IR2-06
        # 处置后的预期形态）
        cat = DIAG_WDT_RESET
    elif not _first_match(lines, alive_patterns):
        # 有 ACTIVE 无 alive：静默死（boardbench BB1 原型——健康链终止
        # 后既无判据也无心跳）
        cat = DIAG_APP_SILENT
    else:
        # 有 ACTIVE 有 alive 无判据：逻辑未达成
        cat = DIAG_APP_NO_VERDICT

    hint = _REPAIR_HINTS[cat]
    summary = f"{cat}: {hint.split('；')[0].split('。')[0]}"
    return DiagResult(category=cat, repair_hint=hint, evidence=evidence[:40],
                      summary=summary)
