# SPDX-License-Identifier: Apache-2.0
"""硬件事实域（HW · LLD-A16 v0.3）测试：画像 [hardware] 装载矩阵 /
caps×画像机械门 / 能力缺口 / 选型预筛 / Zephyr 本地检索 / spec【目标硬件】
可选节 / 硬件写拒扫描 / post_deploy_check 判据降级。"""

from __future__ import annotations

from pathlib import Path

import pytest

from tessera_agent.domain import hardware as hw
from tessera_agent.domain.board_validation import (
    HardwarePin,
    HardwareSpec,
    ProfileError,
    load_profile,
)
from tessera_agent.tools_diag import classify as diag_cls
from tessera_agent.tools_diag import spec_gate

# ---- 画像 [hardware] 节（v1.1 加性）------------------------------------------

_ATK_PROFILE = Path(__file__).resolve().parents[1] / "boards" / "dnesp32s3b.toml"


def test_atk_profile_hardware_facts() -> None:
    """现役画像：LEDB=pwm:0 事实 + source 来源纪律（LED 缺陷实证入画像）。"""
    prof = load_profile(_ATK_PROFILE)
    assert prof.hardware is not None
    assert prof.hardware.zephyr_board == "dnesp32s3b_esp32s3"
    assert prof.hardware.pins[0].name == "LEDB"
    assert prof.hardware.pins[0].domain == "pwm"
    assert prof.hardware.bound("pwm", 0) is not None
    assert prof.hardware.bound("gpio", 0) is None  # gpio 域无板载绑定（实证）
    assert prof.hardware.pins[0].source  # 来源必填纪律


def test_hardware_missing_source_rejected(tmp_path: Path) -> None:
    toml = (
        '[board]\nid = "t"\n[serial]\nport = ""\n'
        '[flash]\nchip = "esp32s3"\nsize_kb = 8192\n'
        '[boot]\nready_patterns = ["CONNECTED"]\n[zenoh]\n'
        "[hardware]\n"
        "[[hardware.pin]]\nname = \"X\"\ndomain = \"gpio\"\ninstance = 0\n"
    )
    p = tmp_path / "t.toml"
    p.write_text(toml, encoding="utf-8")
    with pytest.raises(ProfileError, match="source"):
        load_profile(p)


def test_hardware_unknown_domain_rejected(tmp_path: Path) -> None:
    toml = (
        '[board]\nid = "t"\n[serial]\nport = ""\n'
        '[flash]\nchip = "esp32s3"\nsize_kb = 8192\n'
        '[boot]\nready_patterns = ["CONNECTED"]\n[zenoh]\n'
        "[hardware]\n"
        "[[hardware.pin]]\nname = \"X\"\ndomain = \"kv\"\ninstance = 0\n"
        'source = "s"\n'
    )
    p = tmp_path / "t.toml"
    p.write_text(toml, encoding="utf-8")
    with pytest.raises(ProfileError, match="物理域"):
        load_profile(p)


def test_hardware_absent_profile_backcompat(tmp_path: Path) -> None:
    """无 [hardware] 节 = hardware None（旧画像零重写兼容）。"""
    toml = (
        '[board]\nid = "t"\n[serial]\nport = ""\n'
        '[flash]\nchip = "esp32s3"\nsize_kb = 8192\n'
        '[boot]\nready_patterns = ["CONNECTED"]\n[zenoh]\n'
    )
    p = tmp_path / "t.toml"
    p.write_text(toml, encoding="utf-8")
    prof = load_profile(p)
    assert prof.hardware is None


# ---- caps×画像机械核对门（HW-4 ③）--------------------------------------------

def test_gate_rejects_unbound_channel_led_defect_signature() -> None:
    """LED 缺陷签名回归：gpio:write:0（缺陷 app 原始 caps）→ 拒。"""
    prof = load_profile(_ATK_PROFILE)
    assert hw.check_caps_against_profile(["gpio:write:0"], prof) == \
        ["gpio:write:0"]
    assert hw.check_caps_against_profile(["pwm:set:0"], prof) == []
    assert hw.check_caps_against_profile(["gpio:write:0-3"], prof) == \
        ["gpio:write:0-3"]
    assert hw.check_caps_against_profile(["gpio:write:0,2"], prof) == \
        ["gpio:write:0,2"]


def test_gate_logical_domains_exempt_and_no_hw_section_skip(tmp_path: Path) -> None:
    prof = load_profile(_ATK_PROFILE)
    assert hw.check_caps_against_profile(
        ["kv:write:0", "log:write:0", "fs:read:0", "power:set:0"], prof) == []
    bare = load_profile(_write_bare(tmp_path / "bare.toml"))
    assert hw.check_caps_against_profile(["gpio:write:0"], bare) == []


def _write_bare(p: Path) -> Path:
    p.write_text(
        '[board]\nid = "t"\n[serial]\nport = ""\n'
        '[flash]\nchip = "esp32s3"\nsize_kb = 8192\n'
        '[boot]\nready_patterns = ["CONNECTED"]\n[zenoh]\n', encoding="utf-8")
    return p


def test_capability_gaps() -> None:
    prof = load_profile(_ATK_PROFILE)
    gaps = hw.capability_gaps(["gpio:write:0", "pwm:set:0"], prof)
    assert len(gaps) == 1 and "gpio" in gaps[0]
    assert hw.capability_gaps(["pwm:set:0"], prof) == []
    assert hw.capability_gaps(["gpio:write:0"],
                              _hw_none_profile()) == []


def _hw_none_profile() -> object:
    from tessera_agent.domain.board_validation import (
        BoardProfile,
        BootSpec,
        FlashSpec,
        SerialSpec,
        ZenohSpec,
    )
    return BoardProfile(
        id="x", description="", serial=SerialSpec(port=""),
        flash=FlashSpec(chip="c", size_kb=1), boot=BootSpec(ready_patterns=("x",)),
        zenoh=ZenohSpec(), hardware=None)


# ---- 【目标硬件】段 + spec 门兼容（HW-4 ②）------------------------------------

_GATED_SPEC = (
    "【需求】LED 闪烁。\n【资源】caps = [\"gpio:write:0\"]。\n"
    "【判据】\n- \"LED BLINK ON\"\n"
    "【安全声明】不动安全输出。"
)


def test_target_hw_section_optional_in_gate() -> None:
    """【目标硬件】= 可选节：缺省不阻塞；携带时四节判定不受扰。"""
    r = spec_gate.check_spec(_GATED_SPEC)
    assert r.ok
    from tessera_agent.domain import hardware as hw2
    extended = hw2.append_hw_section(_GATED_SPEC, "board=x；facts=none")
    assert "【目标硬件】" in extended
    r2 = spec_gate.check_spec(extended)
    assert r2.ok and r2.primary_pattern == "LED BLINK ON"
    # 幂等：已带段不重复追加
    assert hw2.append_hw_section(extended, "y") == extended
    assert spec_gate.extract_caps(_GATED_SPEC) == ["gpio:write:0"]


# ---- 选型机械预筛（HW-3）------------------------------------------------------

def test_prefilter_candidates_memory_floor() -> None:
    kept, dropped = hw.prefilter_candidates([
        {"model": "small-mcu", "ram_kb": 128, "psram_kb": 0},
        {"model": "ok-board", "ram_kb": 512, "psram_kb": 8192},
        {"model": "unknown-mem", "ram_kb": 0, "psram_kb": 0},
    ])
    assert [c["model"] for c in kept] == ["ok-board", "unknown-mem"]
    assert all(c["presumed"] for c in kept)
    assert kept[1]["memory_unverified"] is True
    assert dropped[0]["model"] == "small-mcu"
    assert "512" in dropped[0]["reason"]


# ---- Zephyr 本地收录检索（HW-1 分支 B）----------------------------------------

def test_zephyr_local_index_hits(tmp_path: Path) -> None:
    bdir = tmp_path / "zephyr" / "boards" / "seeed" / "xiao"
    bdir.mkdir(parents=True)
    (bdir / "board.yml").write_text(
        "board:\n  name: xiao_esp32s3\n  full_name: XIAO ESP32-S3\n",
        encoding="utf-8")
    r = hw.check_zephyr_inclusion("XIAO ESP32-S3", tmp_path)
    assert r["included"] and "xiao_esp32s3" in r["matches"]
    r2 = hw.check_zephyr_inclusion("esp32c6dev", tmp_path)
    assert not r2["included"]


# ---- 硬件写拒扫描 + 判据降级（HW-4 ④⑤）----------------------------------------

def test_scan_hardware_rejections_clusters() -> None:
    text = ("LED BLINK ON 100MS\nLED WRITE REJECTED\n"
            "LED BLINK ON 100MS\nLED WRITE REJECTED\n"
            "FAN WRITE REJECTED\nother log\n")
    out = diag_cls.scan_hardware_rejections(text)
    assert out[0]["token"] == "LED" and out[0]["count"] == 2
    assert out[1]["token"] == "FAN"
    assert diag_cls.scan_hardware_rejections("clean log") == []


def test_post_deploy_criteria_downgrade_on_hw_rejection(monkeypatch) -> None:
    """判据行命中但硬件写拒在窗 → criteria_pass False + 修复提示带事实。"""
    from tessera_agent.tools_net.deploy import post_deploy_check

    class FakeSvcOK:
        def query_one(self, key, payload, timeout_s=10.0):
            import cbor2
            return ("k", cbor2.dumps({"status": 0, "data": {
                "app_id": b"abc", "state": 3}}))

    import tessera_agent.tools_diag.capture as cap
    monkeypatch.setattr(
        cap, "capture_window",
        lambda port, seconds, *, baud=115200:
            "LED BLINK ON 100MS\nLED WRITE REJECTED\n")
    out = post_deploy_check(FakeSvcOK(), "n", "c", serial_port="/dev/x",
                            pass_patterns=["LED BLINK ON"])
    assert out["criteria_pass"] is False
    assert out["hardware"]["rejections"][0]["token"] == "LED"
    assert "硬件写被拒" in out["diag"]["repair_hint"]


def test_post_deploy_criteria_pass_without_rejections(monkeypatch) -> None:
    from tessera_agent.tools_net.deploy import post_deploy_check

    class FakeSvcOK:
        def query_one(self, key, payload, timeout_s=10.0):
            import cbor2
            return ("k", cbor2.dumps({"status": 0, "data": {
                "app_id": b"abc", "state": 3}}))

    import tessera_agent.tools_diag.capture as cap
    monkeypatch.setattr(
        cap, "capture_window",
        lambda port, seconds, *, baud=115200: "LED BLINK ON 100MS\n")
    out = post_deploy_check(FakeSvcOK(), "n", "c", serial_port="/dev/x",
                            pass_patterns=["LED BLINK ON"])
    assert out["criteria_pass"] is True
    assert out["hardware"]["rejections"] == []


def test_hardware_spec_bound_helper() -> None:
    hs = HardwareSpec(pins=(HardwarePin(
        name="L", domain="gpio", instance=2, source="s"),))
    assert hs.bound("gpio", 2) is not None
    assert hs.bound("gpio", 0) is None
    assert hs.domain_pins("gpio") == hs.pins
