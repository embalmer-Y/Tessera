# SPDX-License-Identifier: Apache-2.0
"""BV2 新板卡适配域（V0.15.0 · LLD-A17 v0.1 · DEC-74 门③三裁决落地）。

DEC-33 原则面：确定性流水线为骨、LLM 只在语义理解处。本模块 = 收录板路
的**机械变换**主体（板定义定位 → 接入件五件套生成 → C0 预检 → 工单闭环）
与未收录板路的**移植清单骨架**（逐项待确认态，人工确认闸如实登记）。

DEC-74 三裁决：
1. 接入件产出 = ``agent/adapt/<board>/`` 工作区（适配件是产物不是源码；
   owner review 后人工并入 firmware/tests/——不直写固件树）；
2. C0 解锁 = 流水线内临时面（本模块只做预检 + 命令产出；真实构建随
   会话执行，不全局化 build.enabled）；
3. v1 = 收录板路全链 + 未收录板路移植清单生成（协作 DTS 确认面随 W2 后批）。

P4 适配 playbook（firmware/tests/p4bench/boards/*——P4-W0/W2 会话沉淀）=
模板族的事实来源；分区布局 = 「ts 五分区 carve 自 4.5 默认布局尾部、8MB
保守兼容」（DEC-23/一四三 纪律）。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tessera_agent.domain import hardware


class AdaptError(Exception):
    """BV2 流水线结构化错误（stage 标注来源段）。"""

    def __init__(self, msg: str, *, stage: str, detail: dict | None = None):
        super().__init__(msg)
        self.stage = stage
        self.detail = detail or {}


# ---- 接入件一：板定义定位（机械——board.yml 索引）----------------------------


@dataclass(frozen=True)
class BoardLocation:
    """Zephyr 收录板定位结果（board.yml 命中）。"""

    name: str  # board.yml 的 name（如 xiao_esp32s3）
    rel_path: str  # 相对 zephyr/boards/ 的 yml 路径（<vendor>/<board>/board.yml）
    qualifiers: list[str] = field(default_factory=list)  # board.yml qualifiers


def _parse_board_yml(text: str) -> dict[str, Any]:
    """board.yml 最小字段走查（name/boards/qualifiers——非全量 YAML，
    只取适配所需键；无 PyYAML 依赖）。"""
    out: dict[str, Any] = {"name": None, "qualifiers": []}
    m = re.search(r"^\s*name:\s*(\S+)", text, re.M)
    if m:
        out["name"] = m.group(1)
    # v4.5 多核形态：boards: <qualifier>: <soc 系>（如 hpcore: esp32p4）
    for qm in re.finditer(r"^\s{4}(\w[\w-]*):\s*$", text, re.M):
        out["qualifiers"].append(qm.group(1))
    return out


def locate_board(hint: str, west_workspace: Path) -> BoardLocation:
    """接入件一：Zephyr 收录板定位（hardware.check_zephyr_inclusion 同源
    匹配——归一化双向子串）。未命中 = AdaptError（调用方转未收录路）。"""
    res = hardware.check_zephyr_inclusion(hint, Path(west_workspace))
    hits: dict[str, str] = res["matches"]
    if not hits:
        raise AdaptError(
            f"Zephyr 收录索引未命中「{hint}」——转未收录板路（原理图协作）",
            stage="locate",
            detail={"hint": hint})
    # 恰一命中取一；多命中取归一化全等者，否则首项（候选面随报告披露）
    names = sorted(hits)
    needle = hardware._norm(hint)
    exact = [n for n in names if hardware._norm(n) == needle]
    name = (exact or names)[0]
    rel = hits[name]
    yml = (Path(west_workspace) / "zephyr" / "boards" / rel)
    info = _parse_board_yml(yml.read_text(encoding="utf-8"))
    return BoardLocation(name=name, rel_path=rel,
                         qualifiers=info.get("qualifiers", []))


# ---- 接入件二：五分区布局（模板族——8MB 保守兼容纪律）------------------------


@dataclass(frozen=True)
class PartitionPlan:
    """ts 五分区布局（P4 playbook 同构：prov/meta/slot_a/slot_b/noinit +
    fw-b 预留）。offset = 绝对 flash 地址；size 单位字节。"""

    flash_kb: int
    carve_base: int  # ts 区基址（min(flash,8MB) 尾部——8MB 保守兼容）
    prov_off: int
    meta_off: int
    slot_a_off: int
    slot_b_off: int
    noinit_off: int
    slot_size: int  # 字节（= CONFIG_TS_STORE_SLOT_SIZE 耦合）
    erase_block: int = 0x1000  # 4KB（esp 系擦除块；对齐校验用）

    def offsets_dict(self) -> dict[str, int]:
        return {"prov": self.prov_off, "meta": self.meta_off,
                "slot_a": self.slot_a_off, "slot_b": self.slot_b_off,
                "noinit": self.noinit_off}


# 布局模板族（实测口径锚定——16MB = P4 playbook 原样；8MB = atk 纪律同构）。
# 键 = flash_kb；其余尺寸 fail-closed（不发明——质量优先条款）。
_LAYOUTS: dict[int, dict[str, int]] = {
    16384: {  # P4（Waveshare ESP32-P4-WIFI6-DEV-KIT，GD 16MB——P4-W0/W2 实测）
        "carve_base": 0x7E0000, "prov": 0x1000, "meta": 0x2000,
        "slot": 0x8000, "noinit": 0x1000, "slot_size": 32768,
    },
    8192: {  # 8MB 保守兼容（atk xiao_esp32s3 纪律——ts 区置于 8MB 尾）
        "carve_base": 0x7E0000, "prov": 0x1000, "meta": 0x2000,
        "slot": 0x8000, "noinit": 0x1000, "slot_size": 32768,
    },
    4096: {  # 4MB 最小档（slot 减半——large 档不可用，如实注记）
        "carve_base": 0x3F0000, "prov": 0x1000, "meta": 0x2000,
        "slot": 0x4000, "noinit": 0x1000, "slot_size": 16384,
    },
}


def plan_partitions(flash_kb: int) -> PartitionPlan:
    """接入件二：五分区布局（模板族查表——未知尺寸 fail-closed）。"""
    tpl = _LAYOUTS.get(int(flash_kb))
    if tpl is None:
        raise AdaptError(
            f"flash {flash_kb}KB 无布局模板（支持 4096/8192/16384——其余尺寸"
            "须人工出图后补表，不发明）", stage="plan",
            detail={"flash_kb": flash_kb})
    base = tpl["carve_base"]
    slot = tpl["slot"]
    return PartitionPlan(
        flash_kb=int(flash_kb), carve_base=base,
        prov_off=base, meta_off=base + tpl["prov"],
        slot_a_off=base + tpl["prov"] + tpl["meta"],
        slot_b_off=base + tpl["prov"] + tpl["meta"] + slot,
        noinit_off=base + tpl["prov"] + tpl["meta"] + 2 * slot,
        slot_size=tpl["slot_size"])


# ---- 接入件三/四/五：overlay + 板级 conf + prov 口径（模板渲染）--------------


_WAMR_ARCH_NOTES = {
    # R3 /64 教训：按目标处理器映射 invoke thunk——板级仅注记，构建面由
    # 模块 Kconfig/工具链自动分派；MAIN_STACK = RV32 深调用帧实测口径。
    "riscv": ("riscv（RV32）", 8192,
              "RV32 调用帧深（P4 实测：4096 main 栈安装链溢出）→ 8192"),
    "xtensa": ("xtensa", 4096, "Xtensa 缺省 4096（persistbench 同口径）"),
    "arm": ("arm/arm64", 4096, "ARM 缺省 4096；AARCH64 WAMR thunk 按 R3 映射"),
    "x86": ("x86", 4096, "x86 缺省 4096（native_sim 口径）"),
}


def render_overlay(loc: BoardLocation, plan: PartitionPlan,
                   target: str) -> str:
    """接入件：五分区 overlay（P4 playbook 同构模板）。target = 板目标
    全名（v4.5 斜杠限定，如 esp32p4_wifi6_dev_kit/esp32p4/hpcore）。"""
    assert plan.carve_base % plan.erase_block == 0, "carve 基址须对齐擦除块"
    fw_b_size = plan.flash_kb * 1024 - (plan.noinit_off + plan.erase_block
                                        - plan.carve_base) - plan.carve_base
    lines = [
        "/*",
        " * BV2 适配接入件（LLD-A17 · DEC-74——agent/adapt 产物，review 后入树）。",
        f" * 板：{loc.name}（zephyr/boards/{loc.rel_path}）；目标 = {target}",
        f" * flash = {plan.flash_kb}KB；ts 五分区 carve 自 0x{plan.carve_base:x}"
        "（8MB 保守兼容纪律，DEC-23）。",
        " * 尺寸耦合：slot = CONFIG_TS_STORE_SLOT_SIZE（本板 conf = "
        f"{plan.slot_size}；part.c BUILD_ASSERT 把关）。",
        " */",
        "/delete-node/ &slot1_partition;",
        "",
        "&flash0 {",
        "\tpartitions {",
        f"\t\tts_prov_part: partition@{plan.prov_off:x} {{",
        "\t\t\tcompatible = \"zephyr,mapped-partition\";",
        "\t\t\tlabel = \"ts-prov\";",
        f"\t\t\treg = <0x{plan.prov_off:x} 0x1000>;",
        "\t\t};",
        f"\t\tts_meta_part: partition@{plan.meta_off:x} {{",
        "\t\t\tcompatible = \"zephyr,mapped-partition\";",
        "\t\t\tlabel = \"ts-meta\";",
        f"\t\t\treg = <0x{plan.meta_off:x} 0x2000>;",
        "\t\t};",
    ]
    for tag, off in (("a", plan.slot_a_off), ("b", plan.slot_b_off)):
        lines += [
            f"\t\tts_slot_{tag}_part: partition@{off:x} {{",
            "\t\t\tcompatible = \"zephyr,mapped-partition\";",
            f"\t\t\tlabel = \"ts-slot-{tag}\";",
            f"\t\t\treg = <0x{off:x} 0x{plan.slot_size:x}>;",
            "\t\t};",
        ]
    lines += [
        f"\t\tts_noinit_part: partition@{plan.noinit_off:x} {{",
        "\t\t\tcompatible = \"zephyr,mapped-partition\";",
        "\t\t\tlabel = \"ts-noinit\";",
        f"\t\t\treg = <0x{plan.noinit_off:x} 0x1000>;",
        "\t\t};",
        "\t\t/* fw-b：未来 MCUmgr 固件第二 slot 预留（DEC-23；V1 未接线） */",
        f"\t\tfw_b_part: partition@{plan.noinit_off + plan.erase_block:x} {{",
        "\t\t\tlabel = \"fw-b\";",
        f"\t\t\treg = <0x{plan.noinit_off + plan.erase_block:x} "
        f"0x{fw_b_size:x}>;",
        "\t\t};",
        "\t};",
        "};",
        "",
    ]
    return "\n".join(lines)


def render_board_conf(plan: PartitionPlan, arch: str) -> str:
    """接入件：板级 conf（内存初值家族 + 架构注记——R1/R2/R3 4096 族由
    bench prj.conf 承载，板级片段只定 slot/线程栈/main 栈）。"""
    arch_name, main_stack, note = _WAMR_ARCH_NOTES.get(
        arch, (arch, 4096, "未收录架构——缺省 4096，待实测校准（如实注记）"))
    return "\n".join([
        "# SPDX-License-Identifier: Apache-2.0",
        f"# BV2 适配接入件：{arch_name} 板级片段（LLD-A17 · DEC-74 产物）。",
        f"# 架构注记：{note}。",
        f"CONFIG_TS_STORE_SLOT_SIZE={plan.slot_size}",
        "CONFIG_TS_APP_THREAD_STACK=16384",
        f"CONFIG_MAIN_STACK_SIZE={main_stack}",
        "",
    ])


def prov_notes(plan: PartitionPlan) -> dict[str, Any]:
    """接入件五：prov/TS_TEST 通道口径（教训 39 offset 陷阱注记随行）。"""
    return {
        "prov_offset": f"0x{plan.prov_off:x}",
        "prov_size": "0x1000",
        "note": "flash_prov --offset 须与本表一致（教训 39：offset 陷阱——"
                "缺省值≠本板布局，误烧落主固件槽尾部）",
        "test_channel": "TS_TEST 构建 prov 注入通道（合同 10）随 bench prj.conf",
    }


# ---- C0 预检（流水线内临时面——DEC-74②：只预检+出命令，不全局解锁）----------


def c0_preflight(artifacts_dir: Path, plan: PartitionPlan) -> dict[str, Any]:
    """C0 构建级预检（机械）：接入件齐备性 + 分区对齐/越界 + slot 尺寸耦合
    + 内存初值家族（R1/R2/R3 4096 族与生成值对拍）。真实板级构建 = 会话内
    执行产出的 west 命令（不在本函数内跑——spawn 面职责）。"""
    findings: list[str] = []
    files = sorted(p.name for p in artifacts_dir.iterdir() if p.is_file())
    if not any("overlay" in f for f in files):
        findings.append("overlay 缺失")
    if not any("board.conf" in f for f in files):
        findings.append("board.conf 缺失")
    for name, off in (("prov", plan.prov_off), ("meta", plan.meta_off),
                      ("slot_a", plan.slot_a_off), ("slot_b", plan.slot_b_off),
                      ("noinit", plan.noinit_off)):
        if off % plan.erase_block:
            findings.append(f"{name} 偏移未对齐擦除块（0x{off:x}）")
    end = plan.noinit_off + plan.erase_block
    if end > plan.flash_kb * 1024:
        findings.append("ts 区越出 flash 尾")
    conf = next((artifacts_dir / f for f in files
                 if f.endswith("board.conf")), None)
    if conf is not None:
        text = conf.read_text(encoding="utf-8")
        if f"CONFIG_TS_STORE_SLOT_SIZE={plan.slot_size}" not in text:
            findings.append("board.conf slot 尺寸与布局模板耦合失配")
    return {"ok": not findings, "findings": findings,
            "files": files,
            "c0_note": "真实构建 = west build -b <target>（流水线会话内执行；"
                       "C0 全局化随 v4.5.0 平移批评估——DEC-74②）"}


# ---- 未收录板路：移植清单骨架（逐项待确认态——人工确认闸）--------------------


_CHECKLIST_ITEMS = (
    "外设树盘点", "引脚冲突检测", "驱动缺口风险", "供电与调试口",
    "flash-RAM 画像草案",
)


def migration_checklist(hint: str,
                        schematic: dict[str, Any] | None = None) -> dict:
    """未收录板路：原理图协作移植清单（LLD-A17 §3）。v1 = 结构骨架 +
    待确认态强制：所有条目 status='pending-confirm'，confirmed=False；
    **未确认条目不进构建**（go_build 恒 False——唯一人工环节如实登记，
    原理图正确性无机械判据）。schematic = 调用方（LLM/人）提供的原理图
    事实（来源标注强制缺省待确认）。"""
    items = []
    for name in _CHECKLIST_ITEMS:
        fact = (schematic or {}).get(name)
        items.append({
            "item": name,
            "status": "pending-confirm",
            "fact": fact,
            "source": (schematic or {}).get(f"{name}.source"),
            "confirmed": False,  # 人工确认闸——owner 逐项点头后转 True
        })
    return {
        "hint": hint,
        "path": "schematic-collab",
        "items": items,
        "go_build": False,
        "note": "原理图正确性无机械判据（DEC-33 唯一人工环节如实登记）；"
                "BV1 C2 flash 身份 = 接线后首个机械事实锚点",
    }


# ---- 收录板路编排：接入件五件套 → agent/adapt/<board>/ 工作区 ---------------


def adapt_included_board(
    hint: str,
    flash_kb: int,
    west_workspace: Path,
    adapt_root: Path,
    *,
    arch: str | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    """收录板路全链（LLD-A17 §2）：定位 → 布局 → 五件套生成 → C0 预检。
    产物 = agent/adapt/<board>/（DEC-74①：产物非源码——不入 agent/boards/
    目录；画像入目录须 owner review 后显式 install_profile）。
    arch 缺省 = board.yml 无法机械得出时由调用方提供（HW 域语义理解处）；
    未提供 = 'unknown' 如实标注。"""
    loc = locate_board(hint, west_workspace)
    plan = plan_partitions(flash_kb)
    board_dir_name = hardware._norm(loc.name)
    out_dir = Path(adapt_root) / board_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)

    arch_key = (arch or "unknown").lower()
    (out_dir / "board.overlay").write_text(
        render_overlay(loc, plan, target or loc.name), encoding="utf-8")
    (out_dir / "board.conf").write_text(
        render_board_conf(plan, arch_key), encoding="utf-8")
    (out_dir / "prov.json").write_text(
        json.dumps(prov_notes(plan), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    pre = c0_preflight(out_dir, plan)
    report = {
        "board": loc.name,
        "rel_path": loc.rel_path,
        "qualifiers": list(loc.qualifiers),
        "arch": arch_key,
        "flash_kb": plan.flash_kb,
        "partitions": plan.offsets_dict(),
        "slot_size": plan.slot_size,
        "artifacts_dir": str(out_dir),
        "c0_preflight": pre,
        "owner_review": "pending",
    }
    (out_dir / "workorder.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    return report


def install_profile(adapt_root: Path, board_id: str, boards_dir: Path,
                    *, owner_approved: bool) -> Path:
    """画像入目录（工单闭环末端——DEC-74① 人工 review 闸：owner_approved
    = False 恒拒）。draft 画像 = agent/boards/<id>.toml 的 v1 骨架
    （serial/flash 实测值接线后由 BV1 bring-up 回填——推定态如实）。"""
    if not owner_approved:
        raise AdaptError("画像入目录须 owner review 批准（DEC-74①——"
                         "适配件是产物，review 后才入目录）", stage="install")
    src = Path(adapt_root) / hardware._norm(board_id) / "workorder.json"
    if not src.is_file():
        raise AdaptError(f"工单不存在：{src}", stage="install")
    wo = json.loads(src.read_text(encoding="utf-8"))
    dst = Path(boards_dir) / f"{board_id}.toml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join([
        "# SPDX-License-Identifier: Apache-2.0",
        "# BV2 适配画像草稿（LLD-A17——owner review 后入目录；接线前为推定态）",
        f"# 工单：agent/adapt/{hardware._norm(board_id)}/workorder.json",
        "[board]",
        f'id = "{board_id}"',
        f'description = "BV2 适配（Zephyr 收录板 {wo["board"]}；'
        f'{wo["flash_kb"]}KB）——接线后 BV1 bring-up 实测回填"',
        "",
        "[serial]",
        'port = "" # 待接线实测（by-id 纪律）',
        "baud = 115200",
        "",
        "[flash]",
        'adapter = "esptool"',
        f'chip = "{wo["board"]}"',
        f"size_kb = {wo['flash_kb']}",
        "",
        "[boot]",
        "reset = true",
        'ready_patterns = ["CONNECTED loc="]',
        "timeout_s = 90.0",
        "",
        "[zenoh]",
        "expect_discover = true",
        'cube = ""',
        "",
        "[caps]",
        'tiers = ["small"]',
        f"min_slot_pool_kb = {wo['slot_size'] // 1024}",
        "",
        "[smoke]",
        'package_path = "" # 待 bring-up 后指定探针包',
        'pub_path = ""',
        'criteria = []',
        "window_s = 90.0",
        "",
    ]) + "\n", encoding="utf-8")
    return dst
