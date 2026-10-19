# SPDX-License-Identifier: Apache-2.0
"""板卡验证域测试（BV1-I · LLD-A12 §7——FakeTransport 全检查矩阵 sim 级）。

覆盖：画像 fail-closed 装载 / 检查项三态（PASS/FAIL/SKIP）× 派生 SKIP 链
× stop_on_fail / overall 三态判定 / progress 序列 / 报告双形态 / LiveTransport
无硬件分支。
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tessera_agent.domain import board_validation as bv
from tessera_agent.domain.firmware import FirmwareDomainPack

GOOD_TOML = """\
[board]
id = "fake-board"
description = "测试画像"

[serial]
port = "/dev/fake/tty0"
baud = 115200

[flash]
chip = "esp32s3"
size_kb = 16384

[boot]
ready_patterns = ["CONNECTED loc="]
timeout_s = 30.0

[zenoh]
expect_discover = true
cube = ""

[caps]
tiers = ["small"]
min_slot_pool_kb = 128

[smoke]
package_path = "demos/x.tsap"
pub_path = "demos/x.pub"
criteria = ["PROBE DONE"]
window_s = 20.0
"""


class FakeTransport:
    """全好板缺省行为；按参数覆盖即注入失败场景（LLD-A12 §7）。"""

    def __init__(self, **kw: object) -> None:
        self.port_ready_ret = kw.get("port_ready_ret", (True, "port open ok"))
        self.flash_ret = kw.get("flash_ret", (
            True, {"chip": "ESP32-S3", "size_kb": 16384},
            ["Chip is ESP32-S3", "Detected flash size: 16MB"]))
        self.boot_ret = kw.get("boot_ret", (
            True, ["boot ok", "CONNECTED loc=tcp/1.2.3.4:7447"]))
        self.discover_ret = kw.get("discover_ret", (
            True, [{"node_id": "n1", "cube_id": "cube1", "fw": "1.0"}]))
        self.snapshot_ret = kw.get("snapshot_ret", (
            True, {"get-info": {"caps": {"tiers": ["small", "large"],
                                         "slot_pool_kb": 512}},
                   "get-app": {"state": 3}}))
        self.deploy_ret = kw.get("deploy_ret", (
            True, {"deploy": {"app_id": "demo.x"},
                   "post": {"criteria_pass": True}}))
        self.calls: list[tuple] = []

    def port_ready(self, port: str):
        self.calls.append(("port_ready", port))
        return self.port_ready_ret

    def flash_identity(self, port: str, chip: str):
        self.calls.append(("flash", port, chip))
        return self.flash_ret

    def boot_capture(self, port: str, baud: int, seconds: float,
                     reset: bool):
        self.calls.append(("boot", seconds, reset))
        return self.boot_ret

    def discover(self, timeout_s: float):
        self.calls.append(("discover", timeout_s))
        return self.discover_ret

    def node_snapshot(self, node: str, cube: str):
        self.calls.append(("snap", node, cube))
        return self.snapshot_ret

    def deploy_smoke(self, node: str, cube: str, package_path: str,
                     pub_path: str, criteria: list[str], serial_port: str,
                     window_s: float):
        self.calls.append(("deploy", node, cube, tuple(criteria)))
        return self.deploy_ret


def _write_profile(tmp_path: Path, text: str = GOOD_TOML) -> bv.BoardProfile:
    p = tmp_path / "fake-board.toml"
    p.write_text(text, encoding="utf-8")
    return bv.load_profile(p)


@pytest.fixture
def profile(tmp_path: Path) -> bv.BoardProfile:
    return _write_profile(tmp_path)


# ---- 画像装载（fail-closed）--------------------------------------------------

def test_profile_load_fields(profile: bv.BoardProfile) -> None:
    assert profile.id == "fake-board"
    assert profile.serial.port == "/dev/fake/tty0"
    assert profile.flash.size_kb == 16384
    assert profile.boot.ready_patterns == ("CONNECTED loc=",)
    assert profile.caps is not None and profile.caps.min_slot_pool_kb == 128
    assert profile.smoke is not None and profile.smoke.criteria == ("PROBE DONE",)
    assert profile.build.enabled is False


@pytest.mark.parametrize("text,fragment", [
    (GOOD_TOML + "\n[mystery]\nx = 1\n", "未知画像节"),
    (GOOD_TOML.replace("baud = 115200", "baud = 115200\nboggan = 1"), "未知键"),
    (GOOD_TOML.replace('ready_patterns = ["CONNECTED loc="]\n', ""),
     "ready_patterns"),
    (GOOD_TOML.replace("size_kb = 16384", "size_kb = 0"), "非空期望值"),
    (GOOD_TOML.replace(
        "[smoke]",
        '[build]\nenabled = true\napp_target = "x"\n\n[smoke]'), "未接入"),
])
def test_profile_fail_closed(tmp_path: Path, text: str,
                             fragment: str) -> None:
    p = tmp_path / "bad.toml"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(bv.ProfileError, match=fragment):
        bv.load_profile(p)


def test_profile_missing_section(tmp_path: Path) -> None:
    p = tmp_path / "bad.toml"
    p.write_text(GOOD_TOML.replace('[zenoh]\nexpect_discover = true\ncube = ""\n', ""),
                 encoding="utf-8")
    with pytest.raises(bv.ProfileError, match="缺必需节"):
        bv.load_profile(p)


def test_list_profiles(tmp_path: Path) -> None:
    _write_profile(tmp_path)
    (tmp_path / "b.toml").write_text(GOOD_TOML, encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("x", encoding="utf-8")
    assert bv.list_profiles(tmp_path) == ["b", "fake-board"]
    assert bv.list_profiles(tmp_path / "nope") == []


# ---- 流水线：全 PASS / 派生 SKIP 链 / overall 三态 -----------------------------

def test_happy_path_all_pass(profile: bv.BoardProfile) -> None:
    tr = FakeTransport()
    seen: list[dict] = []
    report = bv.validate(profile, tr, progress_cb=seen.append)
    assert report.overall == "PASS"
    assert [c.verdict for c in report.checks] == ["PASS"] * 6
    assert [c.check for c in report.checks] == list(bv.CHECK_ORDER)
    # C6 消费 C4 的 node/cube
    assert ("deploy", "n1", "cube1", ("PROBE DONE",)) in tr.calls
    # progress 序列：逐检查回调且终态 done == total
    assert [p["done"] for p in seen] == [1, 2, 3, 4, 5, 6]
    assert seen[-1]["total"] == 6 and seen[-1]["verdicts"]["C6"] == "PASS"
    assert seen[0]["stage"] == "board_validate"


def test_c1_fail_terminates(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(port_ready_ret=(False, "串口不存在"))
    report = bv.validate(profile, tr)
    assert report.checks[0].verdict == "FAIL"
    assert all(c.verdict == "SKIP" and c.derived_skip
               for c in report.checks[1:])
    assert report.overall == "FAIL"
    assert len(tr.calls) == 1  # C1 终止后零后续真实调用（物理域 fail-fast）


def test_c2_mismatch_continues(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(flash_ret=(True, {"chip": "ESP32-C6", "size_kb": 4096},
                                  ["Chip is ESP32-C6"]))
    report = bv.validate(profile, tr)
    c2 = report.checks[1]
    assert c2.verdict == "FAIL" and "ESP32-C6" in c2.detail
    assert report.checks[2].verdict == "PASS"  # 身份错不阻断 boot 检查
    assert report.overall == "FAIL"


def test_c2_tool_fail(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(flash_ret=(False, {}, ["esptool 未找到"]))
    report = bv.validate(profile, tr, checks=["C2"])
    assert report.checks[0].verdict == "FAIL"


def test_c3_miss_derives_c4_c5_c6(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(boot_ret=(True, ["boot ok", "WDT reset"]))
    report = bv.validate(profile, tr)
    assert report.checks[2].verdict == "FAIL"
    assert "CONNECTED" in report.checks[2].detail
    for c in report.checks[3:]:
        assert c.verdict == "SKIP" and c.derived_skip
    assert report.overall == "FAIL"


def test_c3_capture_fail(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(boot_ret=(False, ["OSError: boom"]))
    report = bv.validate(profile, tr, checks=["C3"])
    assert report.checks[0].verdict == "FAIL"
    assert report.checks[0].evidence == ["OSError: boom"]


def test_c4_discover_fail(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(discover_ret=(False, [{"error": "timeout"}]))
    report = bv.validate(profile, tr)
    c4, c5, c6 = report.checks[3], report.checks[4], report.checks[5]
    assert c4.verdict == "FAIL"
    assert c5.verdict == "SKIP" and c5.derived_skip
    assert c6.verdict == "SKIP" and c6.derived_skip
    assert report.overall == "FAIL"


def test_c4_ambiguous_without_named_cube(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(discover_ret=(True, [
        {"node_id": "n1", "cube_id": "cube1"},
        {"node_id": "n2", "cube_id": "cube2"}]))
    report = bv.validate(profile, tr, checks=["C4"])
    assert report.checks[0].verdict == "FAIL"
    assert "恰一" in report.checks[0].detail


def test_c4_named_cube_match(tmp_path: Path) -> None:
    profile = _write_profile(tmp_path, GOOD_TOML.replace(
        'cube = ""', 'cube = "cube2"'))
    tr = FakeTransport(discover_ret=(True, [
        {"node_id": "n1", "cube_id": "cube1"},
        {"node_id": "n2", "cube_id": "cube2"}]))
    report = bv.validate(profile, tr, checks=["C4"])
    assert report.checks[0].verdict == "PASS"
    assert report.checks[0].facts["cube"] == "cube2"


def test_c5_caps_mismatch(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(snapshot_ret=(True, {"get-info": {
        "caps": {"tiers": ["large"], "slot_pool_kb": 64}}}))
    report = bv.validate(profile, tr, checks=["C4", "C5"])
    assert report.checks[1].verdict == "FAIL"
    assert "tiers" in report.checks[1].detail


def test_c5_caps_block_absent(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(snapshot_ret=(True, {"get-info": {"fw": "1.0"}}))
    report = bv.validate(profile, tr, checks=["C4", "C5"])
    assert report.checks[1].verdict == "FAIL"
    assert "未自报 caps" in report.checks[1].detail


def test_c5_declared_skip_degrades(tmp_path: Path) -> None:
    profile = _write_profile(
        tmp_path,
        GOOD_TOML.replace("[caps]\ntiers = [\"small\"]\nmin_slot_pool_kb = 128\n\n", ""))
    report = bv.validate(profile, FakeTransport())
    c5 = report.checks[4]
    assert c5.verdict == "SKIP" and not c5.derived_skip
    assert report.overall == "DEGRADED"  # 零 FAIL 有 SKIP


def test_c6_criteria_miss(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(deploy_ret=(True, {
        "deploy": {"app_id": "demo.x"},
        "post": {"criteria_pass": False,
                 "diag": {"category": "app_no_verdict",
                          "summary": "无判据行", "repair_hint": "查串口"}}}))
    report = bv.validate(profile, tr, checks=["C4", "C6"])
    c6 = report.checks[1]
    assert c6.verdict == "FAIL"
    assert c6.facts["diag"]["category"] == "app_no_verdict"


def test_c6_unverified_is_derived_skip(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(deploy_ret=(True, {
        "deploy": {"app_id": "demo.x"},
        "post": {"criteria_pass": None, "diag_error": "抓取失败"}}))
    report = bv.validate(profile, tr)
    c6 = report.checks[5]
    assert c6.verdict == "SKIP" and c6.derived_skip
    assert "未验证" in c6.detail
    assert report.overall == "DEGRADED"


def test_c6_deploy_fail(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(deploy_ret=(False, {"deploy_error": "TA_E_VERIFY"}))
    report = bv.validate(profile, tr, checks=["C4", "C6"])
    assert report.checks[1].verdict == "FAIL"
    assert "TA_E_VERIFY" in report.checks[1].detail


def test_c6_declared_skip_no_smoke(tmp_path: Path) -> None:
    profile = _write_profile(
        tmp_path,
        GOOD_TOML.replace('[smoke]\npackage_path = "demos/x.tsap"\n'
                          'pub_path = "demos/x.pub"\n'
                          'criteria = ["PROBE DONE"]\nwindow_s = 20.0\n', ""))
    report = bv.validate(profile, FakeTransport())
    c6 = report.checks[5]
    assert c6.verdict == "SKIP" and not c6.derived_skip
    assert "零板态扰动" in c6.detail


# ---- 流水线控制：stop_on_fail / 子集 / 参数校验 --------------------------------

def test_stop_on_fail(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(flash_ret=(True, {"chip": "ESP32-C6", "size_kb": 1}, []))
    report = bv.validate(profile, tr, stop_on_fail=True)
    assert report.checks[1].verdict == "FAIL"
    for c in report.checks[2:]:
        assert c.verdict == "SKIP" and "stop_on_fail" in c.detail


def test_checks_subset(profile: bv.BoardProfile) -> None:
    report = bv.validate(profile, FakeTransport(), checks=["C1", "C4"])
    assert [c.check for c in report.checks] == ["C1", "C4"]
    assert report.overall == "PASS"


def test_unknown_check_raises(profile: bv.BoardProfile) -> None:
    with pytest.raises(bv.ProfileError, match="未知检查项"):
        bv.validate(profile, FakeTransport(), checks=["C9"])


# ---- 报告双形态 ----------------------------------------------------------------

def test_report_json_and_render(profile: bv.BoardProfile) -> None:
    report = bv.validate(profile, FakeTransport())
    data = report.to_json()
    for key in ("board_id", "overall", "dur_s", "checks"):
        assert key in data
    assert data["overall"] == "PASS" and len(data["checks"]) == 6
    text = report.render()
    assert "Board fake-board" in text and ": PASS" in text
    assert "[C1] PASS 串口在场" in text


def test_render_shows_fail_evidence(profile: bv.BoardProfile) -> None:
    tr = FakeTransport(boot_ret=(True, [f"line{i}" for i in range(20)]))
    report = bv.validate(profile, tr)
    text = report.render()
    assert "[C3] FAIL" in text
    assert "| line0" in text
    assert "全量见 JSON" in text  # 超过 10 行时收敛提示


# ---- LiveTransport（无硬件分支）与 MCP 面登记 -----------------------------------

def test_live_transport_port_missing() -> None:
    cfg = SimpleNamespace(west_venv_python="/no/venv/python",
                          router_locator="tcp/127.0.0.1:7447")
    tr = bv.LiveTransport(cfg)
    ok, why = tr.port_ready("/nonexistent/port0")
    assert ok is False and "串口不存在" in why
    ok2, why2 = tr.port_ready("")
    assert ok2 is False and "未配置" in why2


def test_live_transport_deploy_requires_ctx() -> None:
    cfg = SimpleNamespace(west_venv_python="/no/venv/python",
                          router_locator="tcp/127.0.0.1:7447")
    tr = bv.LiveTransport(cfg)
    ok, out = tr.deploy_smoke("n", "c", "p", "k", ["x"], "/dev/null", 1.0)
    assert ok is False and "ctx 未注入" in out["deploy_error"]


def test_repo_path_resolution() -> None:
    cfg = SimpleNamespace(workspace_repo="/repo")
    assert bv._resolve_repo_path(cfg, "agent/demos/x.tsap") \
        == Path("/repo/agent/demos/x.tsap")
    assert bv._resolve_repo_path(cfg, "/abs/x.tsap") == Path("/abs/x.tsap")


def test_mcp_face_registration() -> None:
    pack = FirmwareDomainPack()
    assert "board_validate" in pack.tools
    assert pack.policy.entries.get("board_validate") == "strict"
