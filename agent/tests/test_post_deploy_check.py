# SPDX-License-Identifier: Apache-2.0
"""G 批 D3：部署后诊断自动回喂——健康/不健康/抓取失败三态。"""
from __future__ import annotations

from pathlib import Path

from tessera_agent.tools_net.deploy import post_deploy_check


def _reply(app_id: bytes, state: bytes) -> bytes:
    import cbor2

    return cbor2.dumps({"status": 0,
                         "data": {"app_id": app_id, "state": state}})


class FakeSvcOK:
    def query_one(self, key, payload, timeout_s=10.0):
        return ("k", _reply(b"abc", 3))


class FakeSvcDead:
    def query_one(self, key, payload, timeout_s=10.0):
        return ("k", _reply(b"", 2))


def test_healthy_short_circuits(monkeypatch, tmp_path: Path) -> None:
    called = {"cap": 0}

    def fake_capture(port, seconds, *, baud=115200):
        called["cap"] += 1
        return ""

    import tessera_agent.tools_diag.capture as cap

    monkeypatch.setattr(cap, "capture_window", fake_capture)
    out = post_deploy_check(FakeSvcOK(), "n", "c", serial_port="/dev/x")
    assert out["healthy"] is True
    assert called["cap"] == 0  # 健康不触发抓取
    assert out["get-app"]["state"] == 3


def test_unhealthy_diagnoses(monkeypatch, tmp_path: Path) -> None:
    import tessera_agent.tools_diag.capture as cap

    monkeypatch.setattr(
        cap, "capture_window",
        lambda port, seconds, *, baud=115200:
            "AK alive t=100\n[wdt] 上次异常复位留痕 reason=0x00020000\n")
    out = post_deploy_check(FakeSvcDead(), "n", "c", serial_port="/dev/x")
    assert out["healthy"] is False
    assert "diag" in out
    assert out["diag"]["category"]  # 分类非空
    assert out["diag"]["evidence"]


def test_unhealthy_no_port_structured_only() -> None:
    out = post_deploy_check(FakeSvcDead(), "n", "c")
    assert out["healthy"] is False
    assert "diag" not in out


def test_capture_failure_not_masking(monkeypatch) -> None:
    import tessera_agent.tools_diag.capture as cap

    def boom(port, seconds, *, baud=115200):
        raise OSError("port busy")

    monkeypatch.setattr(cap, "capture_window", boom)
    out = post_deploy_check(FakeSvcDead(), "n", "c", serial_port="/dev/x")
    assert out["healthy"] is False
    assert "diag_error" in out and "port busy" in out["diag_error"]


def test_app_id_expect_mismatch_unhealthy() -> None:
    out = post_deploy_check(FakeSvcOK(), "n", "c", app_id_expect="other")
    assert out["healthy"] is False


# ---- P1-5（S8）：判据面——pass_patterns 升级健康判定 --------------------------


def test_criteria_hit_upgrades_verdict(monkeypatch) -> None:
    """健康 + 判据行命中 = criteria_pass True（S8 终止条件）。"""
    import tessera_agent.tools_diag.capture as cap

    monkeypatch.setattr(cap, "capture_window",
                        lambda p, s, *, baud=115200: "AK alive t=1\nAPP DONE n=5\n")
    out = post_deploy_check(FakeSvcOK(), "n", "c", serial_port="/dev/x",
                            pass_patterns=["APP DONE"])
    assert out["healthy"] is True
    assert out["criteria_pass"] is True
    assert out["diag"]["category"] == "pass"


def test_criteria_miss_feeds_s8(monkeypatch) -> None:
    """健康但判据行未现 = criteria_pass False + diag（S8 修复轮回喂证据）。"""
    import tessera_agent.tools_diag.capture as cap

    monkeypatch.setattr(cap, "capture_window",
                        lambda p, s, *, baud=115200: "AK alive t=1 net=1\n")
    out = post_deploy_check(FakeSvcOK(), "n", "c", serial_port="/dev/x",
                            pass_patterns=["APP DONE"])
    assert out["healthy"] is True
    assert out["criteria_pass"] is False
    assert out["diag"]["category"] != "pass"


def test_criteria_without_serial_unverified() -> None:
    """无串口 + 判据 = criteria_pass None（未验证 ≠ 未命中——如实区分）。"""
    out = post_deploy_check(FakeSvcOK(), "n", "c", pass_patterns=["APP DONE"])
    assert out["healthy"] is True
    assert out["criteria_pass"] is None


# ---- FIX-2：reset_before_capture——单端口会话复位+抓取（BV1 C6 专用）----------


def test_reset_flag_routes_to_reset_and_capture(monkeypatch) -> None:
    """True = reset_and_capture 单会话；False = capture_window（原路径不扰）。"""
    import tessera_agent.tools_diag.capture as cap

    calls: dict[str, int] = {"reset": 0, "window": 0}

    monkeypatch.setattr(cap, "reset_and_capture",
                        lambda p, s, *, baud=115200:
                        calls.__setitem__("reset", calls["reset"] + 1)
                        or "P4W2 PROBE INIT\n")
    monkeypatch.setattr(cap, "capture_window",
                        lambda p, s, *, baud=115200:
                        calls.__setitem__("window", calls["window"] + 1)
                        or "P4W2 PROBE INIT\n")
    out = post_deploy_check(FakeSvcOK(), "n", "c", serial_port="/dev/x",
                            pass_patterns=["PROBE INIT"],
                            reset_before_capture=True)
    assert out["criteria_pass"] is True
    assert calls == {"reset": 1, "window": 0}

    out2 = post_deploy_check(FakeSvcOK(), "n", "c", serial_port="/dev/x",
                             pass_patterns=["PROBE INIT"])
    assert out2["criteria_pass"] is True
    assert calls == {"reset": 1, "window": 1}  # 缺省路径零变化
