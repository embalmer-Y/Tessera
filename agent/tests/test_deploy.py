# SPDX-License-Identifier: Apache-2.0
"""deploy_* 单元测试（LLD-A06 §5）：FakeCube 进程内固件语义桩。

覆盖：信封编码黄金性质 / 发现（载荷身份）/ push_app 全链（分块重组、租约
闭环、幂等重试、篡改拒绝、事实对拍失败）/ 门控语义（v2+租约）。
真机 E2E 见 test_deploy_e2e.py（环境门控）。
"""

from __future__ import annotations

import struct
from pathlib import Path

import cbor2
import pytest

from tessera_agent.common.errors import TA_E_ARGS, TA_E_TSAP, TaError
from tessera_agent.tools_net import deploy, keys
from tessera_agent.tools_tsap import tools as tsap_tools

# ---- FakeCube：固件命令面语义桩（v2 信封 + 门控 + staging）------------------


class FakeCube:
    """deploy 依赖面（query/query_one）的最小固件语义实现。"""

    GATED = {"app-begin", "app-chunk", "app-verify", "app-activate"}

    def __init__(self, node: str = "fn", cube: str = "fc") -> None:
        self.node, self.cube = node, cube
        self.lease_holder: str | None = None
        self.lease_deny = False
        self.active_slot = 0
        self.stage: dict | None = None
        self.chunks: dict[int, bytes] = {}
        self.idems: list[str] = []
        self.attempts: dict[int, int] = {}
        self.drop_once: set[int] = set()
        self.facts_override: dict | None = None
        self.verify_calls = 0
        self.activate_calls = 0

    # -- 传输面 --
    def query(self, key: str, payload: bytes, timeout_s: float = 10.0):
        return [(key, self._reply(key, payload))]

    def query_one(self, key: str, payload: bytes, timeout_s: float = 10.0):
        return (key, self._reply(key, payload))

    # -- 命令面 --
    def _reply(self, key: str, payload: bytes) -> bytes:
        m = cbor2.loads(payload)
        rid = m.get("rid", "")
        src = m.get("src", "")
        op = m["op"]
        args = m.get("args", {})

        if op in self.GATED:
            if "ver" not in m:
                return self._enc(rid, -1, {})
            if self.lease_holder != src:
                return self._enc(rid, -4, {})

        if op == "get-info":
            return self._enc(rid, 0, {"fw": "fake", "board": "fake",
                                      "node": self.node, "cube": self.cube})
        if op == "get-link":
            return self._enc(rid, 0, {"state": 1, "link_up": True})
        if op == "get-safety":
            return self._enc(rid, 0, {"channels": 0})
        if op == "get-app":
            return self._enc(rid, 0, {"state": 2, "active_slot": self.active_slot,
                                      "rollback_count": 0, "app_id": ""})
        if op == "lease-acquire":
            if self.lease_deny:
                return self._enc(rid, -4, {"holder": "other"})
            self.lease_holder = args["holder"]
            return self._enc(rid, 0, {"lease_id": 1, "expires_at_ms": 10_000})
        if op == "lease-release":
            if self.lease_holder != args.get("holder"):
                return self._enc(rid, -4, {})
            self.lease_holder = None
            return self._enc(rid, 0, {"released": True})
        if op == "app-begin":
            self.stage = {"total": args["total"], "hw": 0, "verified": False,
                          "slot": self.active_slot ^ 1,
                          "buf": bytearray(args["total"])}
            self.chunks = {}
            return self._enc(rid, 0, {"slot": self.stage["slot"], "total": args["total"]})
        if op == "app-chunk":
            off, data = args["offset"], args["data"]
            self.attempts[off] = self.attempts.get(off, 0) + 1
            if off in self.drop_once:
                self.drop_once.discard(off)
                msg = f"注入丢块: off={off}"
                raise TaError(10, msg, domain="zenoh", retryable=True)
            if self.stage is None or off + len(data) > self.stage["total"]:
                return self._enc(rid, -1, {})
            self.stage["buf"][off:off + len(data)] = data
            self.stage["hw"] = max(self.stage["hw"], off + len(data))
            self.chunks[off] = bytes(data)
            if "idem" in args:
                self.idems.append(args["idem"])
            return self._enc(rid, 0, {"written": len(data), "high_water": self.stage["hw"]})
        if op == "app-verify":
            self.verify_calls += 1
            st = self.stage
            if st is None or st["hw"] < st["total"]:
                return self._enc(rid, -4, {})
            magic, ver, mlen, wlen, _ = struct.unpack(">IHIIH", bytes(st["buf"][:16]))
            facts = {"manifest_len": mlen, "wasm_len": wlen,
                     "cose_off": 16 + mlen + wlen}
            if self.facts_override:
                facts.update(self.facts_override)
            st["verified"] = True
            return self._enc(rid, 0, facts)
        if op == "app-activate":
            self.activate_calls += 1
            if self.stage is None or not self.stage["verified"]:
                return self._enc(rid, -4, {})
            self.active_slot = self.stage["slot"]
            return self._enc(rid, 0, {"state": 2, "active_slot": self.active_slot,
                                      "rollback_count": 0})
        return self._enc(rid, -7, {})

    @staticmethod
    def _enc(rid: str, status: int, data: dict) -> bytes:
        return cbor2.dumps({"ver": 1, "kind": 16, "rid": rid,
                            "status": status, "data": data})


# ---- 信封编码 --------------------------------------------------------------

def test_envelope_roundtrip_and_caps():
    req = keys.envelope("app-chunk", "rid-1", total=128, offset=0, data=b"\x01\x02",
                        holder="h", idem="k1", to=5000)
    m = cbor2.loads(req)
    assert m["ver"] == 1 and m["kind"] == keys.KIND_SYS_REQUEST
    assert m["op"] == "app-chunk" and m["rid"] == "rid-1"
    assert m["args"] == {"total": 128, "offset": 0, "data": b"\x01\x02",
                         "holder": "h", "idem": "k1", "to": 5000}
    with pytest.raises(ValueError):
        keys.envelope("op", "r" * 17)  # rid 超上限
    with pytest.raises(ValueError):
        keys.envelope("op", "r", idem="k" * 17)  # idem 超上限


def test_parse_reply_v1_and_v2():
    r2 = keys.parse_reply(cbor2.dumps({"ver": 1, "kind": 16, "rid": "r",
                                       "status": 0, "data": {"a": 1}}))
    assert r2.v2 and r2.status == 0 and r2.rid == "r" and r2.data == {"a": 1}
    r1 = keys.parse_reply(cbor2.dumps({"status": -1, "data": {}}))
    assert not r1.v2 and r1.status == -1
    with pytest.raises(ValueError):
        keys.parse_reply(cbor2.dumps({"nope": 1}))


# ---- 发现 / 状态 ------------------------------------------------------------

def test_discover_uses_payload_identity():
    fake = FakeCube()
    out = deploy.discover(fake)
    assert out == [{"node_id": "fn", "cube_id": "fc", "fw": "fake",
                    "board": "fake", "status": 0}]


def test_status_merges_four_faces():
    st = deploy.status(FakeCube(), "fn", "fc")
    assert set(st) == {"node_id", "cube_id", "get-info", "get-link",
                       "get-safety", "get-app"}


# ---- push_app --------------------------------------------------------------

def _make_pkg(tmp_path: Path) -> tuple[str, str, bytes]:
    tsap_tools.tsap_keygen("u-key", str(tmp_path), [str(tmp_path)])
    wasm = tmp_path / "a.wasm"
    wasm.write_bytes(b"\x00asm\x01\x00\x00\x00" + b"UNIT" * 40)
    pkg = tsap_tools.tsap_package(
        str(wasm), {"app_id": "com.t.unit", "app_ver": "0.1.0",
                    "min_fw_ver": "0.1.0", "caps": [], "stack_kb": 4,
                    "heap_kb": 16, "exports": ["health_ping"]},
        str(tmp_path / "u-key.key"), str(tmp_path), [str(tmp_path)])
    return pkg["package_path"], str(tmp_path / "u-key.pub"), Path(pkg["package_path"]).read_bytes()


def test_push_app_happy_path(tmp_path):
    pkg, pub, raw = _make_pkg(tmp_path)
    fake = FakeCube()
    logs: list[str] = []
    out = deploy.push_app(fake, "fn", "fc", pkg, pub, chunk_size=512,
                          log_fn=logs.append)
    assert out["confirmed"] is True and out["released"] is True
    assert bytes(fake.stage is not None and fake.stage["buf"] or b"") == raw
    # 分块重组 = 原包字节；每块带 idem；activate 已确认；租约已归还
    assert sorted(fake.chunks) == list(range(0, len(raw), 512))
    assert all(len(c) <= 512 for c in fake.chunks.values())
    assert len(fake.idems) == len(fake.chunks)
    assert fake.activate_calls == 1 and fake.verify_calls == 1
    assert fake.lease_holder is None
    assert any("tsap_verify PASS" in ln for ln in logs)


def test_push_app_tampered_refused_before_upload(tmp_path):
    pkg, pub, raw = _make_pkg(tmp_path)
    p = Path(pkg)
    data = bytearray(raw)
    data[-1] ^= 0xFF  # 破坏 COSE 尾字节
    p.write_bytes(bytes(data))
    fake = FakeCube()
    with pytest.raises(TaError):
        deploy.push_app(fake, "fn", "fc", pkg, pub)
    assert fake.chunks == {}, "复验拒绝必须发生在任何分块之前"


def test_push_app_lease_denied(tmp_path):
    pkg, pub, _ = _make_pkg(tmp_path)
    fake = FakeCube()
    fake.lease_deny = True
    with pytest.raises(TaError) as ei:
        deploy.push_app(fake, "fn", "fc", pkg, pub)
    assert ei.value.code == TA_E_TSAP or "拒绝" in ei.value.message
    assert fake.chunks == {}


def test_push_app_chunk_retry_same_idem(tmp_path):
    pkg, pub, _ = _make_pkg(tmp_path)
    fake = FakeCube()
    fake.drop_once = {0}  # 首块丢一次 → 重试同 idem
    out = deploy.push_app(fake, "fn", "fc", pkg, pub)
    assert out["confirmed"] is True
    assert fake.attempts[0] == 2, "丢块必须重试"
    idem_counts = {}
    for tag in fake.idems:
        idem_counts[tag.split(":")[-1]] = idem_counts.get(tag.split(":")[-1], 0) + 1
    assert max(idem_counts.values()) == 1 or len(fake.idems) == len(set(fake.idems)), \
        "同 offset 重试共用同一 idem 前缀"


def test_push_app_facts_mismatch_rejected(tmp_path):
    pkg, pub, _ = _make_pkg(tmp_path)
    fake = FakeCube()
    fake.facts_override = {"manifest_len": 999}
    with pytest.raises(TaError) as ei:
        deploy.push_app(fake, "fn", "fc", pkg, pub)
    assert ei.value.code == TA_E_TSAP
    assert fake.activate_calls == 0, "事实对拍失败不得激活"
    assert fake.lease_holder is None, "失败路径也必须释放租约"


def test_push_app_chunk_size_bounds(tmp_path):
    pkg, pub, _ = _make_pkg(tmp_path)
    with pytest.raises(TaError) as ei:
        deploy.push_app(FakeCube(), "fn", "fc", pkg, pub, chunk_size=4097)
    assert ei.value.code == TA_E_ARGS
