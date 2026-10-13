# SPDX-License-Identifier: Apache-2.0
"""LN 编排器测试（V0.4.x M16，DEC-54①/Q-35 方案 A）。

双 FakeCube 拓扑：验证组注册/扇出部署/状态聚合/组恢复与非原子如实呈现。
"""
from __future__ import annotations

import pytest

from tessera_agent.common.errors import TA_E_ARGS, TaError
from tessera_agent.tools_net import lno
from tessera_agent.tools_net.deploy import CmdError
from test_deploy import FakeCube, _make_pkg
from pathlib import Path


class LnCube(FakeCube):
    """FakeCube + estop-clear 语义（M16 组恢复扇出对象）。"""

    def __init__(self, node: str, cube: str) -> None:
        super().__init__(node, cube)
        self.estop_clears = 0

    def _reply(self, key: str, payload: bytes) -> bytes:
        m = __import__("cbor2").loads(payload)
        if m["op"] == "estop-clear":
            if m.get("args", {}).get("confirm") != "estop":
                return self._enc(m["rid"], -1, {})
            self.estop_clears += 1
            return self._enc(m["rid"], 0, {"cleared": True})
        return super()._reply(key, payload)


class StubSvc:
    """按 (node, cube) 路由的双成员服务桩；offline 成员抛 TaError。"""

    def __init__(self, cubes: dict[tuple[str, str], LnCube],
                 offline: set[tuple[str, str]] = frozenset()) -> None:
        self.cubes = cubes
        self.offline = offline

    def _route(self, key: str):
        parts = key.split("/")
        node, cube = parts[1], parts[2]
        if (node, cube) in self.offline:
            msg = f"成员不可达: {node}/{cube}"
            raise TaError(11, msg, domain="zenoh", retryable=False)
        return self.cubes[(node, cube)]

    def query_one(self, key: str, payload: bytes, timeout_s: float = 10.0):
        return (key, self._route(key).query_one(key, payload)[1])

    def query(self, key: str, payload: bytes, timeout_s: float = 10.0):
        if "*" in key:  # 发现面（LN 不消费，桩保形）
            return []
        k, v = self.query_one(key, payload)
        return [(k, v)]


def _dual_topology():
    a = LnCube("ln1n", "ln1c")
    b = LnCube("ln2n", "ln2c")
    svc = StubSvc({("ln1n", "ln1c"): a, ("ln2n", "ln2c"): b})
    reg = lno.LnRegistry()
    reg.create("plant-a", [("ln1n", "ln1c"), ("ln2n", "ln2c")])
    return reg, svc, a, b


def test_ln_create_validation():
    reg = lno.LnRegistry()
    reg.create("ok-1", [("n1", "c1")])
    with pytest.raises(TaError):
        reg.create("bad id!", [("n", "c")])  # 非法字符
    with pytest.raises(TaError):
        reg.create("ok-1", [("n", "c")])  # 撞名
    with pytest.raises(TaError):
        reg.create("ok-2", [])  # 空成员
    with pytest.raises(TaError):
        reg.create("ok-3", [("n", "c"), ("n", "c")])  # 重复成员
    with pytest.raises(TaError):
        reg.create("ok-4", [("n", "c")], linkloss_policy="wat")
    assert len(reg.list()) == 1


def test_ln_deploy_dual_cube(tmp_path: Path):
    pkg, pub, raw = _make_pkg(tmp_path)
    reg, svc, a, b = _dual_topology()

    r = lno.ln_deploy(reg, svc, "plant-a", pkg, pub)
    assert r["ok"] is True and r["failed"] == 0
    # 双成员各自收齐全量包字节（顺序扇出双达）
    assert bytes(a.stage["buf"]) == raw
    assert bytes(b.stage["buf"]) == raw
    assert a.lease_holder is None and b.lease_holder is None  # 各自租约闭环
    assert a.activate_calls == 1 and b.activate_calls == 1


def test_ln_status_aggregation_and_degraded():
    reg, svc, a, b = _dual_topology()
    r = lno.ln_status(reg, svc, "plant-a")
    assert r["ok"] is True
    assert len(r["members"]) == 2
    assert r["degraded_members"] == []
    assert r["linkloss_policy"] == "continue"

    svc_off = StubSvc({("ln1n", "ln1c"): a, ("ln2n", "ln2c"): b},
                      offline={("ln2n", "ln2c")})
    r2 = lno.ln_status(reg, svc_off, "plant-a")
    assert r2["ok"] is False and r2["failed"] == 1
    assert "ln2n/ln2c" in r2["degraded_members"]
    assert "policy_hint" not in r2  # continue 策略无暂停提示

    reg.create("p2", [("ln1n", "ln1c"), ("ln2n", "ln2c")],
               linkloss_policy="pause")
    r3 = lno.ln_status(reg, svc_off, "p2")
    assert "policy_hint" in r3  # pause 策略提示


def test_ln_estop_clear_fanout():
    reg, svc, a, b = _dual_topology()
    r = lno.ln_estop_clear(reg, svc, "plant-a")
    assert r["ok"] is True
    assert a.estop_clears == 1 and b.estop_clears == 1  # 双成员 confirm 扇出


def test_ln_deploy_partial_failure_nonatomic(tmp_path: Path, monkeypatch):
    """非原子如实：成员 2 verify 失败不阻断成员 1（部署已落）——聚合标注。"""
    pkg, pub, raw = _make_pkg(tmp_path)
    reg, svc, a, b = _dual_topology()

    orig_verify = b._reply

    def broken_verify(key, payload):
        import cbor2
        m = cbor2.loads(payload)
        if m["op"] == "app-verify":
            raise CmdError("app-verify",
                           type("R", (), {"status": -4, "data": {}})())
        return orig_verify(key, payload)

    monkeypatch.setattr(b, "_reply", broken_verify)
    r = lno.ln_deploy(reg, svc, "plant-a", pkg, pub)
    assert r["ok"] is False and r["failed"] == 1
    flags = {e["cube"]: e["ok"] for e in r["members"]}
    assert flags == {"ln1c": True, "ln2c": False}
    assert bytes(a.stage["buf"]) == raw  # 成员 1 完整部署（不受 2 失败影响）
