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
