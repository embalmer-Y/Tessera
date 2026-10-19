# SPDX-License-Identifier: Apache-2.0
"""通用内存规划程序（LLD-A13 · DEC-70；V0.13.0 MP）。

构建期确定性内存审计：输入一次真实构建的产物（GNU ld linker map +
Kconfig .config），输出三层内存账本（region / 具名对象 / config 意图）
+ 规则目录判定报告。跨芯片通用性锚定两个芯片无关接口——GNU ld map
格式（xtensa/aarch64/riscv/x86_64 同构实测）与 Kconfig 生效值；芯片
知识只存在于规则目录（每条挂教训/证据出处，版本化随教训增长）。

定性继承 BV1（LLD-A12 §1）：非 LLM 创作任务，LLM 不在关键路径。
声明≠生效（R0）：.config 是唯一生效值事实源——atkbench prj.conf 声明
堆 196608 被板级 conf 覆盖为 58368（2026-10-19 设计批首日实录）。

规则目录 v1（RULES_VERSION=1，出处见 LLD-A13 §4）：R1 rx 栈下限
（FIX-1 崩机案）/ R2 sysworkq 栈（SENTINEL 案）/ R3 shell 栈
（EXCCAUSE 0 案）/ R4 wifi TX 堆压（ENOMEM 噪声案）/ R5 TLS 堆下限
（P1-2 -80 案）/ R6 区域余量 / R7 STATIC TX 观察（教训 41）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

RULES_VERSION = 1
OVERALL_PASS, OVERALL_WARN, OVERALL_FAIL = "PASS", "WARN", "FAIL"
# wifi 帧缓冲经验尺寸（R4——802.11 MPDU ~1.6KB；经验常数非精确定义，LLD §4）
WIFI_FRAME_EST_BYTES = 1600


class AuditError(Exception):
    """审计输入不可用（文件缺失/解析失败——fail-closed）。"""


@dataclass
class Region:
    name: str
    origin: int
    length: int
    attrs: str = ""
    used: int = 0          # output section 字节和
    reserved: int = 0      # 保留窗（IRAM 镜像类——无实输入的填充 output 节，不可用）

    @property
    def slack(self) -> int:
        return self.length - self.used - self.reserved


@dataclass
class MemObject:
    region: str
    section: str
    addr: int
    size: int
    objfile: str
    kind: str = "static"   # stack / heap / slab / pool / static
    name: str = ""         # 符号归并名（空 = 未归并——归并率如实报告）


@dataclass
class Finding:
    rule_id: str
    severity: str          # fail / warn / info
    message: str
    evidence: str = ""


@dataclass
class MemoryReport:
    map_path: str
    config_path: str
    pre_build: bool
    regions: list[Region] = field(default_factory=list)
    objects: list[MemObject] = field(default_factory=list)
    fills: int = 0
    config: dict[str, str] = field(default_factory=dict)
    config_diffs: list[dict[str, str]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    attributed: int = 0    # 具名归并对象字节
    unattributed: int = 0  # 未具名静态字节

    @property
    def overall(self) -> str:
        sev = {f.severity for f in self.findings}
        if "fail" in sev:
            return OVERALL_FAIL
        if "warn" in sev:
            return OVERALL_WARN
        return OVERALL_PASS

    def _intent_ledger(self) -> list[tuple[str, int]]:
        """config 内存意图账——全量扫描 *STACK_SIZE/*HEAP*/*POOL* 整型键
        （零硬编码；配置声明了什么，一目了然）。"""
        out: list[tuple[str, int]] = []
        for key, val in sorted(self.config.items()):
            if not (key.endswith("STACK_SIZE") or "HEAP" in key
                    or "POOL" in key):
                continue
            try:
                num = int(val, 0)
            except ValueError:
                continue
            if num > 0:
                out.append((key, num))
        return out

    def to_json(self) -> dict:
        return {
            "rules_version": RULES_VERSION,
            "map": self.map_path,
            "config": self.config_path,
            "pre_build": self.pre_build,
            "overall": self.overall,
            "regions": [
                {"name": r.name, "origin": hex(r.origin), "length": r.length,
                 "used": r.used, "reserved": r.reserved, "slack": r.slack,
                 "attrs": r.attrs}
                for r in self.regions],
            "objects": [
                {"region": o.region, "kind": o.kind, "name": o.name,
                 "size": o.size, "section": o.section, "objfile": o.objfile}
                for o in self.objects],
            "fills": self.fills,
            "attributed": self.attributed,
            "unattributed": self.unattributed,
            "config_diffs": self.config_diffs,
            "intent": dict(self._intent_ledger()),
            "findings": [
                {"rule": f.rule_id, "severity": f.severity,
                 "message": f.message, "evidence": f.evidence}
                for f in self.findings],
        }

    def render(self) -> str:
        lines = [f"memory audit · {self.map_path}"
                 f"{'（pre-build 图）' if self.pre_build else ''}",
                 f"overall: {self.overall}  (rules v{RULES_VERSION})"]
        origins: dict[int, list[str]] = {}
        for r in self.regions:
            origins.setdefault(r.origin, []).append(r.name)
        lines.append("-- regions --")
        for r in self.regions:
            alias = (f"（别名窗：{'/'.join(origins[r.origin])}）"
                     if len(origins[r.origin]) > 1 else "")
            lines.append(
                f"  {r.name:16s} {r.length:>9}B used {r.used:>9}"
                f" reserved {r.reserved:>7} slack {r.slack:>8}"
                f" ({r.slack / 1024:6.1f}K){alias}")
        lines.append("-- named objects (top) --")
        named = sorted((o for o in self.objects if o.kind != "static"
                        or o.name), key=lambda o: -o.size)
        for o in named[:16]:
            lines.append(
                f"  [{o.region[:7]:7s}][{o.kind:5s}] {o.size:>8}B"
                f" {o.name or o.section[-36:]:40s} {o.objfile[-32:]}")
        lines.append(
            f"  归并率: 具名 {self.attributed}B / 未具名 {self.unattributed}B")
        lines.append("-- config 内存意图账 --")
        for key, num in self._intent_ledger():
            lines.append(f"  {key:44s} {num:>9}B ({num / 1024:6.1f}K)")
        if self.config_diffs:
            lines.append("-- config 声明≠生效 (R0) --")
            for d in self.config_diffs:
                lines.append(f"  {d['key']}: 声明 {d['declared']}"
                             f" → 生效 {d['effective']}")
        lines.append("-- findings --")
        if not self.findings:
            lines.append("  （无）")
        for f in self.findings:
            lines.append(f"  [{f.severity:4s}] {f.rule_id}: {f.message}")
        return "\n".join(lines)


# ---- 解析器（GNU ld map；三行式 input 条目 + 符号归并——LLD-A13 §3.2）----

_RE_REGION = re.compile(
    r"^([A-Za-z][\w.]*)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+([a-z-]+)?\s*$",
    re.M)
_RE_OUT = re.compile(
    r"^(\.[\w./\-]+)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)"
    r"(?:\s+load address\s+(0x[0-9a-fA-F]+))?", re.M)
_RE_IN_INLINE = re.compile(
    r"^\s+(\.[\w./\-]+|COMMON)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)"
    r"(?:\s+(\S.*))?$")
_RE_FILL = re.compile(r"^\s+\*fill\*\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)")
_RE_NAME_ONLY = re.compile(r"^\s+(\.[\w./\-]+)\s*$")
_RE_CONT = re.compile(r"^\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(\S.*)$")
_RE_SYMBOL = re.compile(r"^\s+(0x[0-9a-fA-F]+)\s+([A-Za-z_][\w.$]*)\s*$")
_RE_WILDCARD = re.compile(r"^\s*\*?\(")
# 链接器元数据节（地址 0、不入内存——debug/xtensa 属性表等；排除防 FLASH
# 账污染——atk 真图 .debug_* 14MB 实录）
_RE_META_OUT = re.compile(
    r"^\.(?:debug|comment|stab|line|note|pdr|mdebug|xt\.|xtensa|gnu\.version"
    r"|ident|group|gcc Exist)")
_RE_DUMMY_OUT = re.compile(r"dummy", re.I)


def _parse_regions(txt: str) -> list[Region]:
    regions = []
    for m in _RE_REGION.finditer(txt):
        if m.group(1) == "Name":  # 表头行（Name Origin Length Attributes）
            continue
        regions.append(Region(name=m.group(1), origin=int(m.group(2), 16),
                              length=int(m.group(3), 16), attrs=m.group(4)))
    return regions


def _region_of(regions: list[Region], addr: int) -> Region | None:
    for r in regions:
        if r.origin <= addr < r.origin + r.length:
            return r
    return None


def _classify(section: str, addr: int, symmap: dict[int, list[str]]) -> tuple[str, str]:
    """符号/形态归并——返回 (kind, name)。归并失败 = ("static", "")。"""
    for sym in symmap.get(addr, []):
        if sym.startswith("_k_thread_stack_"):
            return "stack", sym.removeprefix("_k_thread_stack_")
        if sym.endswith("_stack") or sym == "z_interrupt_stacks":
            return "stack", sym
        if "stack_area" in sym:  # zenoh-pico pthread 栈池（system.c）
            return "stack", sym
        if sym.startswith("kheap_") or "_heap" in sym:
            return "heap", sym
        if sym.startswith("_k_mem_slab_buf_"):
            return "slab", sym.removeprefix("_k_mem_slab_buf_")
    if re.search(r"pool|mempool|_buf|ring|cache", section, re.I):
        return "pool", ""
    return "static", ""


def _parse_map(txt: str) -> tuple[list[Region], list[MemObject], int, dict]:
    """返回 (regions, objects, fills, per_region_fills)。

    output section 占用与保留窗：output 节 span 内的实输入字节和为 0
    （仅 fill/表达式）→ 保留（IRAM 镜像窗类——不冒充可用余量）。
    """
    regions = _parse_regions(txt)
    raw: list[tuple[str, int, int, str]] = []
    fills: list[tuple[int, int]] = []
    symmap: dict[int, list[str]] = {}
    pending: str | None = None

    # 解析主体 = 「Linker script and memory map」段；其后的「Discarded
    # input sections」（--gc-sections 丢弃清单，地址全 0）截断——防丢弃
    # 对象冒充实账（atk 2MB video pool 实录；部分 ld 版本该段在前部）
    start = txt.find("Linker script and memory map")
    body = txt[start:] if start >= 0 else txt
    cut = body.find("Discarded input sections")
    if cut >= 0:
        body = body[:cut]

    for line in body.splitlines():
        m = _RE_IN_INLINE.match(line)
        if m:
            raw.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16),
                        (m.group(4) or "").strip()))
            pending = None
            continue
        m = _RE_FILL.match(line)
        if m:
            fills.append((int(m.group(1), 16), int(m.group(2), 16)))
            continue
        m = _RE_NAME_ONLY.match(line)
        if m:
            pending = m.group(1)
            continue
        m = _RE_CONT.match(line)
        if m and pending:
            raw.append((pending, int(m.group(1), 16), int(m.group(2), 16),
                        m.group(3).strip()))
            pending = None
            continue
        m = _RE_SYMBOL.match(line)
        if m:
            symmap.setdefault(int(m.group(1), 16), []).append(m.group(2))
            continue
        if _RE_OUT.match(line) or _RE_WILDCARD.match(line):
            pending = None  # output 节头/通配行 = 上下文重置

    objects: list[MemObject] = []
    for sec, addr, size, src in raw:
        if size <= 0 or _RE_META_OUT.match(sec):
            continue
        reg = _region_of(regions, addr)
        if reg is None:
            continue
        kind, name = _classify(sec, addr, symmap)
        objects.append(MemObject(region=reg.name, section=sec, addr=addr,
                                 size=size, objfile=src, kind=kind, name=name))

    # output 节占用 + 保留窗判定（span 内实输入字节 = 0 → reserved；节 size
    # 已含内部 fill——不再重复加）。元数据节（debug/属性表，地址 0）不入账；
    # dummy 标记节（IRAM 镜像窗/ROM 别名）→ 保留。
    for m in _RE_OUT.finditer(body):
        if _RE_META_OUT.match(m.group(1)):
            continue
        addr, size = int(m.group(2), 16), int(m.group(3), 16)
        reg = _region_of(regions, addr)
        if reg is None:
            continue
        real = sum(o.size for o in objects
                   if addr <= o.addr < addr + size)
        if real == 0 or _RE_DUMMY_OUT.search(m.group(1)):
            reg.reserved += size
        else:
            reg.used += size
    total_fills = sum(f for _, f in fills)
    return regions, objects, total_fills, symmap


def parse_map_file(path: str | Path) -> tuple[list[Region], list[MemObject], int]:
    txt = Path(path).read_text(encoding="utf-8", errors="replace")
    regions, objects, fills, _ = _parse_map(txt)
    if not regions:
        raise AuditError(f"map 未解析出 Memory Configuration 表: {path}")
    return regions, objects, fills


def parse_config(text: str) -> dict[str, str]:
    """Kconfig 行 → 字典；`# CONFIG_X is not set` 记为 n。"""
    cfg: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^# CONFIG_([A-Z0-9_]+) is not set$", line)
        if m:
            cfg[m.group(1)] = "n"
            continue
        m = re.match(r"^(?:CONFIG_)?([A-Z0-9_]+)=(.*)$", line)
        if m and not line.startswith("#"):
            cfg[m.group(1)] = m.group(2).strip().strip('"')
    return cfg


def audit(map_path: str | Path, config_path: str | Path,
          prj_conf: str | Path | None = None) -> MemoryReport:
    mp, cp = Path(map_path), Path(config_path)
    if not mp.is_file():
        raise AuditError(f"map 不存在: {mp}")
    if not cp.is_file():
        raise AuditError(f"config 不存在: {cp}")

    regions, objects, fills = parse_map_file(mp)
    cfg = parse_config(cp.read_text(encoding="utf-8", errors="replace"))
    if not cfg:
        raise AuditError(f"config 未解析出任何键: {cp}")

    diffs: list[dict[str, str]] = []
    if prj_conf is not None:
        pcp = Path(prj_conf)
        if not pcp.is_file():
            raise AuditError(f"prj-conf 不存在: {pcp}")
        declared = parse_config(pcp.read_text(encoding="utf-8",
                                              errors="replace"))
        for key, val in declared.items():
            eff = cfg.get(key)
            if eff is None:
                diffs.append({"key": key, "declared": val, "effective": "<未生效>"})
            elif eff != val:
                diffs.append({"key": key, "declared": val, "effective": eff})

    report = MemoryReport(
        map_path=str(mp), config_path=str(cp),
        pre_build="pre" in mp.stem, regions=regions, objects=objects,
        fills=fills, config=cfg, config_diffs=diffs)
    for o in objects:
        if o.kind == "static" and not o.name:
            report.unattributed += o.size
        else:
            report.attributed += o.size

    report.findings = run_rules(cfg, report, diffs)
    return report


def _cfg_int(cfg: dict[str, str], key: str) -> int | None:
    val = cfg.get(key)
    if val is None:
        return None
    try:
        return int(val, 0)
    except ValueError:
        return None


def run_rules(cfg: dict[str, str], report: MemoryReport,
              diffs: list[dict[str, str]]) -> list[Finding]:
    """规则目录 v1（LLD-A13 §4——每条挂教训出处；目录版本化）。"""
    out: list[Finding] = []

    def num(key: str) -> int | None:
        return _cfg_int(cfg, key)

    def flag(key: str) -> bool:
        return cfg.get(key) == "y"

    # R0 声明≠生效（atkbench 堆 196608→58368 实录——设计批首日）
    for d in diffs:
        out.append(Finding(
            "R0", "warn",
            f"config 声明≠生效: {d['key']} 声明 {d['declared']}"
            f" → 生效 {d['effective']}（板级 conf/cmake 覆盖链——"
            "以 .config 为准）",
            "LLD-A13 §4 R0；2026-10-19 MP 设计批首日实录"))

    heap = num("HEAP_MEM_POOL_SIZE") or 0
    # R1 rx 栈下限（FIX-1：缺省 1500 被部署突发压穿 FATAL）
    if flag("WIFI"):
        rx = num("NET_RX_STACK_SIZE") or 0
        if rx < 4096:
            out.append(Finding(
                "R1", "fail",
                f"NET_RX_STACK_SIZE={rx} < 4096（WiFi 使能——部署突发压穿"
                " rx_q 栈 FATAL 风险）",
                "FIX-1 · bv1_c6_crash_console.txt · LLD-A13 §4 R1"))
    # R2 sysworkq 栈（SENTINEL 案：WiFi/DHCP 事件建链窗溢出）
    if flag("TS_NET_ZENOH"):
        sw = num("SYSTEM_WORKQUEUE_STACK_SIZE") or 0
        if sw < 4096:
            out.append(Finding(
                "R2", "fail",
                f"SYSTEM_WORKQUEUE_STACK_SIZE={sw} < 4096（zenoh 建链窗"
                " WiFi/DHCP 事件溢出风险）",
                "R5-V③ STACK_SENTINEL 案 · LLD-A13 §4 R2"))
    # R3 shell 栈（confirm 链 2048 装不下——EXCCAUSE 0 野跳）
    if flag("SHELL"):
        sh = num("SHELL_STACK_SIZE") or 0
        if sh < 4096:
            out.append(Finding(
                "R3", "fail",
                f"SHELL_STACK_SIZE={sh} < 4096（confirm 链 stage_commit"
                " meta flash 写 + shell_print 深栈风险）",
                "R5-V③ EXCCAUSE 0 案 · LLD-A13 §4 R3"))
    # R4 wifi TX 堆压（TX 突发 ENOMEM——atk 残余噪声）
    if flag("WIFI") and not flag("ESP32_WIFI_STATIC_TX_BUFFER"):
        txn = num("ESP32_WIFI_DYNAMIC_TX_BUFFER_NUM") or 0
        if heap and txn * WIFI_FRAME_EST_BYTES > heap // 2:
            out.append(Finding(
                "R4", "warn",
                f"wifi 动态 TX 池峰值 {txn}×{WIFI_FRAME_EST_BYTES}B"
                f" > 系统堆 {heap}B 的 50%（TX 突发 ENOMEM 风险——"
                "降 TX 上限或增堆）",
                "R5-I/FIX-1 残余 ENOMEM 噪声 · LLD-A13 §4 R4"))
    # R5 TLS 建链堆下限（P1-2：50-56K 档 -80 循环实证）
    if flag("TS_NET_TLS") and 0 < heap < 65536:
        out.append(Finding(
            "R5", "warn",
            f"TS_NET_TLS=y 且系统堆 {heap}B < 65536（TLS 建链期"
            " z_malloc -80 量级风险）",
            "P1-2 双重内存耗尽案 · LLD-A13 §4 R5"))
    # R6 区域余量（链接器擦边不可部署）
    for r in report.regions:
        if r.used and r.slack >= 0 and r.slack < 2048:
            out.append(Finding(
                "R6", "warn",
                f"region {r.name} 余量 {r.slack}B < 2048B（对齐/填充漂移"
                "无缓冲——不可部署擦边态）",
                "LLD-A13 §4 R6"))
    # R7 STATIC TX 观察态（教训 41：两轮实测均劣化——上游映射待核实）
    if flag("ESP32_WIFI_STATIC_TX_BUFFER"):
        out.append(Finding(
            "R7", "warn",
            "ESP32_WIFI_STATIC_TX_BUFFER=y（本机两轮实测均劣化："
            "+SPIRAM heap=数据面死 / 单用=关联失败 rc=-134；4.5-rc1"
            " 双层 TX buffer Kconfig 映射存疑）",
            "教训 41 · dev-env v2.30 · LLD-A13 §4 R7"))
    return out
