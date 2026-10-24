# SPDX-License-Identifier: Apache-2.0
"""BV2 新板卡适配域测试（V0.15.0 · LLD-agent-board-adaptation · DEC-74）。

矩阵：定位命中/未命中 → 布局模板族（P4 playbook 真锚）→ 接入件五件套 →
C0 预检（防篡改）→ 工单闭环（owner 闸）→ 未收录清单待确认态。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tessera_agent.domain import board_adapt as ba


@pytest.fixture()
def ws(tmp_path: Path) -> Path:
    """假 west 工作区：两块收录板（一块 4096 档、一块多 qualifier）。"""
    zboards = tmp_path / "zephyr" / "boards"
    d1 = zboards / "acme" / "super4096"
    d1.mkdir(parents=True)
    (d1 / "board.yml").write_text(
        "board:\n  name: super4096\n  full_name: ACME Super 4096\n"
        "  vendors:\n    - acme\n  socs:\n    - name: supcore\n",
        encoding="utf-8")
    d2 = zboards / "beta" / "dualcore"
    d2.mkdir(parents=True)
    (d2 / "board.yml").write_text(
        "board:\n  name: dualcore\n  socs:\n    - name: b1\n",
        encoding="utf-8")
    return tmp_path


# ---- 接入件一：定位 -----------------------------------------------------------

def test_locate_hit(ws: Path) -> None:
    loc = ba.locate_board("Super 4096", ws)  # 归一化子串命中
    assert loc.name == "super4096"
    assert loc.rel_path == "acme/super4096/board.yml"


def test_locate_miss_transfers_to_schematic(ws: Path) -> None:
    with pytest.raises(ba.AdaptError) as ei:
        ba.locate_board("不存在的板", ws)
    assert ei.value.stage == "locate"


# ---- 接入件二：布局模板族（P4 playbook 真锚）----------------------------------

def test_plan_partitions_p4_anchors() -> None:
    """16MB 档 = P4 playbook 原样（firmware/tests/p4bench/boards overlay）。"""
    plan = ba.plan_partitions(16384)
    assert plan.carve_base == 0x7E0000
    assert plan.prov_off == 0x7E0000
    assert plan.meta_off == 0x7E1000
    assert plan.slot_a_off == 0x7E3000
    assert plan.slot_b_off == 0x7EB000
    assert plan.noinit_off == 0x7F3000
    assert plan.slot_size == 32768


def test_plan_partitions_in_tree_overlay_match() -> None:
    """生成器 vs 在树 P4 overlay 逐偏移对拍（BV2 收录板路首应用真锚）。"""
    overlay = (Path(__file__).resolve().parents[2]
               / "firmware" / "tests" / "p4bench" / "boards"
               / "esp32p4_wifi6_dev_kit_esp32p4_hpcore.overlay")
    if not overlay.is_file():  # 仓外检出守卫
        pytest.skip("in-tree p4bench overlay 不在位")
    text = overlay.read_text(encoding="utf-8")
    plan = ba.plan_partitions(16384)
    for label, off in plan.offsets_dict().items():
        tag = label.replace("_", "-")
        m = re.search(rf"ts-{tag}.*?reg = <(0x[0-9a-f]+) ", text, re.S)
        assert m, f"在树 overlay 缺 ts-{tag}"
        assert int(m.group(1), 16) == off, f"ts-{tag} 偏移失配"


def test_plan_partitions_unknown_flash_failclosed() -> None:
    with pytest.raises(ba.AdaptError) as ei:
        ba.plan_partitions(65536)
    assert ei.value.stage == "plan"


# ---- 接入件五件套 + C0 预检 ---------------------------------------------------

def test_adapt_included_board_artifacts(ws: Path, tmp_path: Path) -> None:
    adapt_root = tmp_path / "adapt"
    rep = ba.adapt_included_board("super4096", 4096, ws, adapt_root,
                                  arch="riscv")
    d = adapt_root / "super4096"
    assert (d / "board.overlay").is_file()
    assert (d / "board.conf").is_file()
    assert (d / "prov.json").is_file()
    assert (d / "workorder.json").is_file()
    assert rep["c0_preflight"]["ok"] is True
    assert rep["owner_review"] == "pending"
    conf = (d / "board.conf").read_text(encoding="utf-8")
    assert "CONFIG_TS_STORE_SLOT_SIZE=16384" in conf  # 4MB 档 slot 减半
    assert "CONFIG_MAIN_STACK_SIZE=8192" in conf  # riscv 深帧口径
    prov = json.loads((d / "prov.json").read_text(encoding="utf-8"))
    assert prov["prov_offset"] == "0x3f0000"
    assert "offset 陷阱" in prov["note"]  # 教训 39 注记随行


def test_c0_preflight_detects_conf_tamper(ws: Path, tmp_path: Path) -> None:
    adapt_root = tmp_path / "adapt"
    rep = ba.adapt_included_board("super4096", 4096, ws, adapt_root)
    d = Path(rep["artifacts_dir"])
    conf = d / "board.conf"
    conf.write_text(conf.read_text(encoding="utf-8").replace(
        "CONFIG_TS_STORE_SLOT_SIZE=16384", "CONFIG_TS_STORE_SLOT_SIZE=32768"),
        encoding="utf-8")
    pre = ba.c0_preflight(d, ba.plan_partitions(4096))
    assert pre["ok"] is False
    assert any("耦合失配" in f for f in pre["findings"])


# ---- 工单闭环：画像入目录 owner 闸（DEC-74①）---------------------------------

def test_install_profile_owner_gate(ws: Path, tmp_path: Path) -> None:
    adapt_root = tmp_path / "adapt"
    ba.adapt_included_board("super4096", 4096, ws, adapt_root)
    boards_dir = tmp_path / "boards"
    with pytest.raises(ba.AdaptError):
        ba.install_profile(adapt_root, "super4096", boards_dir,
                           owner_approved=False)
    assert not boards_dir.exists()  # 未批准零落盘
    dst = ba.install_profile(adapt_root, "super4096", boards_dir,
                             owner_approved=True)
    text = dst.read_text(encoding="utf-8")
    assert 'id = "super4096"' in text
    assert "size_kb = 4096" in text
    assert "推定态" in text  # 接线前推定态如实标注
    assert 'port = ""' in text  # 实测值待 bring-up 回填


# ---- 未收录板路：移植清单待确认态（人工确认闸如实登记）------------------------

def test_migration_checklist_pending_state() -> None:
    cl = ba.migration_checklist("魔改板 X", {"外设树盘点": "1×I2C + 1×SPI"})
    assert cl["path"] == "schematic-collab"
    assert len(cl["items"]) == 5
    assert all(i["status"] == "pending-confirm" and not i["confirmed"]
               for i in cl["items"])
    assert cl["go_build"] is False  # 未确认条目不进构建
    assert "无机械判据" in cl["note"]
    facted = cl["items"][0]
    assert facted["fact"] == "1×I2C + 1×SPI"  # 提供的事实随条目携带


# ---- MCP 面注册（strict 类——DEC-74 写 adapt 工作区）--------------------------


def test_mcp_tool_registered() -> None:
    from tessera_agent.domain import firmware

    pack = firmware.FirmwareDomainPack()
    assert "board_adapt" in pack.tools
    assert pack.policy.entries.get("board_adapt") == "strict"


def test_workorder_chain_profile_loadable(ws: Path, tmp_path: Path) -> None:
    """工单闭环末端：BV2 生成草稿 → owner 批准入目录 → BV1 loader 可装载
    （clarify 分支 A mention 绑定同源消费——LLD-agent-board-adaptation §1 工单两端）。"""
    from tessera_agent.domain import board_validation as bv

    adapt_root = tmp_path / "adapt"
    ba.adapt_included_board("super4096", 4096, ws, adapt_root)
    dst = ba.install_profile(adapt_root, "super4096", tmp_path / "boards",
                             owner_approved=True)
    p = bv.load_profile(dst)
    assert p.id == "super4096"
    assert p.flash.size_kb == 4096
