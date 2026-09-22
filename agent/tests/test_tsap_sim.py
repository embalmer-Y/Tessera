# SPDX-License-Identifier: Apache-2.0
"""MA2 测试：TSAP 打包签名（LLD-A05 §5）与场景校验（LLD-A04 §1）。

覆盖：keygen→package→verify 往返；双实现互验（pycose×DIY 四象限）；
篡改矩阵（坏签名/截断/坏 magic/坏版本/坏 manifest）；单键纪律；
密钥纪律（0600/越界拒绝/覆盖拒绝）；场景 schema 校验矩阵。
E2E 仿真（sim_run 真实 twister 双跑）= test_sim_e2e（env TESSERA_SIM_E2E=1 启用）。
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
from pydantic import ValidationError

from tessera_agent.common.errors import TA_E_ARGS, TA_E_POLICY, TA_E_TSAP, TaError
from tessera_agent.tools_sim.scenario import Scenario, scenario_validate
from tessera_agent.tools_tsap import cose
from tessera_agent.tools_tsap.manifest import TsapManifest
from tessera_agent.tools_tsap.tools import tsap_keygen, tsap_package, tsap_verify

KEYS = Path(__file__).resolve().parent.parent / "build" / "keys-test"
BUILD = Path(__file__).resolve().parent.parent / "build"

VALID_MANIFEST = {
    "app_id": "com.example.demo",
    "app_ver": "1.0.0",
    "min_fw_ver": "0.1.0",
    "caps": ["gpio:out:led1"],
    "stack_kb": 4,
    "heap_kb": 16,
    "exports": ["health_ping", "init", "tick"],
}


@pytest.fixture()
def keypair(tmp_path: Path) -> tuple[Path, Path]:
    d, x = cose.generate_keypair()
    priv = tmp_path / "k.key"
    pub = tmp_path / "k.pub"
    priv.write_bytes(d)
    pub.write_bytes(x)
    return priv, pub


@pytest.fixture()
def wasm_blob(tmp_path: Path) -> Path:
    w = tmp_path / "app.wasm"
    w.write_bytes(b"\x00asm" + bytes(range(64)))
    return w


def test_manifest_roundtrip_and_validation():
    m = TsapManifest(**VALID_MANIFEST)
    data = m.to_cbor()
    assert TsapManifest.from_cbor(data) == m
    # 确定性：两次编码逐字节一致（canonical）
    assert m.to_cbor() == data

    for bad in [
        {**VALID_MANIFEST, "app_ver": "1.0"},  # 非 semver
        {**VALID_MANIFEST, "app_id": "Bad Name"},
        {**VALID_MANIFEST, "exports": ["init"]},  # 缺 health_ping
        {**VALID_MANIFEST, "exports": ["health_ping", "bogus"]},
        {**VALID_MANIFEST, "stack_kb": 0},
    ]:
        with pytest.raises(ValidationError):
            TsapManifest(**bad)


def test_cose_cross_verification_four_quadrants(keypair: tuple[Path, Path]):
    priv, pub = keypair
    payload = b"manifest-bytes" + b"wasm-bytes"
    d = priv.read_bytes()
    x = pub.read_bytes()

    by_pycose = cose.sign_pycose(payload, d)
    by_diy = cose.sign_diy(payload, d)
    # 四象限互验（DR-21：双实现互验对冲 pycose 停更）
    assert cose.verify_pycose(by_pycose, x)
    assert cose.verify_diy(by_pycose, x)
    assert cose.verify_pycose(by_diy, x)
    assert cose.verify_diy(by_diy, x)
    # 错公钥必拒
    _, other_x = cose.generate_keypair()
    assert not cose.verify_diy(by_pycose, other_x)


def test_tsap_package_verify_roundtrip(tmp_path: Path, keypair: tuple[Path, Path], wasm_blob: Path):
    priv, pub = keypair
    out = tmp_path / "pkg"
    r = tsap_package(str(wasm_blob), VALID_MANIFEST, str(priv), str(out), [str(tmp_path)])
    assert r["signer_impl"] == "pycose"
    v = tsap_verify(r["package_path"], str(pub))
    assert v["valid"] is True
    assert v["manifest"]["app_id"] == "com.example.demo"
    assert v["wasm_len"] == 68
    assert set(v["checks"]) == {"header", "cose.pycose", "cose.diy", "manifest"}
    # 产物目录越界拒绝（IR-13）
    with pytest.raises(TaError) as eo:
        tsap_package(str(wasm_blob), VALID_MANIFEST, str(priv), "/tmp", [str(tmp_path)])
    assert eo.value.code == TA_E_POLICY


def test_tsap_tamper_matrix(tmp_path: Path, keypair: tuple[Path, Path], wasm_blob: Path):
    priv, pub = keypair
    out = tmp_path / "pkg"
    r = tsap_package(str(wasm_blob), VALID_MANIFEST, str(priv), str(out), [str(tmp_path)])
    pkg = bytearray(Path(r["package_path"]).read_bytes())

    def expect_reject(data: bytes, why: str):
        bad = tmp_path / f"bad-{why}.tsap"
        bad.write_bytes(data)
        with pytest.raises(TaError) as ei:
            tsap_verify(str(bad), str(pub))
        assert ei.value.code == TA_E_TSAP

    tampered = bytearray(pkg)
    tampered[-1] ^= 0xFF  # 坏签名（末字节翻转）
    expect_reject(bytes(tampered), "sig")
    expect_reject(bytes(pkg[:-4]), "truncated")
    bad_magic = bytearray(pkg)
    bad_magic[0] = ord("X")
    expect_reject(bytes(bad_magic), "magic")
    bad_ver = bytearray(pkg)
    bad_ver[5] = 9
    expect_reject(bytes(bad_ver), "ver")
    bad_len = bytearray(pkg)
    bad_len[9] = 0xFF  # manifest_len 越界
    expect_reject(bytes(bad_len), "len")


def test_tsap_no_signature_no_output(tmp_path: Path, wasm_blob: Path):
    with pytest.raises(TaError) as ei:
        tsap_package(
            str(wasm_blob), VALID_MANIFEST, str(tmp_path / "nope.key"), str(tmp_path),
            [str(tmp_path)],
        )
    assert ei.value.code == TA_E_TSAP  # 无签名不产出（硬点）


def test_keygen_discipline(tmp_path: Path):
    r = tsap_keygen("dev1", str(tmp_path), [str(tmp_path)])
    priv = Path(r["pub_key_path"]).with_suffix(".key")
    mode = stat.S_IMODE(priv.stat().st_mode)
    assert mode == 0o600  # 私钥 0600
    assert priv.read_bytes() != b"" and len(priv.read_bytes()) == 32
    with pytest.raises(TaError):
        tsap_keygen("dev1", str(tmp_path), [str(tmp_path)])  # 覆盖拒绝
    with pytest.raises(TaError) as ei:
        tsap_keygen("dev2", "/etc", [str(tmp_path)])  # 白名单越界
    assert ei.value.code == TA_E_POLICY
    with pytest.raises(TaError) as ei2:
        tsap_keygen("bad name!", str(tmp_path), [str(tmp_path)])
    assert ei2.value.code == TA_E_ARGS


def test_scenario_validation_matrix():
    good = {
        "inputs": [{"t_ms": 0, "ch": "di1", "value": 1}, {"t_ms": 100, "ch": "do1", "value": 0}],
        "expectations": [{"ch": "rep_a", "op": "eq", "value": 100}],
    }
    assert scenario_validate(good) == []
    assert Scenario(**good).inputs[0].t_ms == 0

    for bad, why in [
        (
            {**good, "inputs": [
                {"t_ms": 5, "ch": "a", "value": 1}, {"t_ms": 1, "ch": "a", "value": 0},
            ]},
            "乱序",
        ),
        ({**good, "expectations": [{"ch": "a", "op": "regex", "value": 1}]}, "非法 op"),
        ({**good, "inputs": []}, "空输入"),
    ]:
        assert scenario_validate(bad), why


def test_sim_e2e(tmp_path: Path):
    """E2E：sim_run 真实 twister 双跑（约 2×构建/运行，分钟级）。

    启用：环境变量 TESSERA_SIM_E2E=1（默认跳过——CI 常规 job 不跑分钟级仿真；
    MA2 退出验证时显式开启，结果留痕于交付报告）。
    """
    if os.environ.get("TESSERA_SIM_E2E") != "1":
        pytest.skip("E2E 仿真需 TESSERA_SIM_E2E=1（MA2 退出验证显式开启）")
    import asyncio

    from tessera_agent.common.config import AgentConfig
    from tessera_agent.tools_sim.runner import sim_run

    cfg = AgentConfig(
        workspace_repo=Path(__file__).resolve().parent.parent.parent,
        west_workspace=Path.home() / "project" / "zephyrproject",
        west_venv_python=Path.home() / "project/zephyrproject/.venv/bin/python",
        audit_dir=tmp_path / "audit",
        default_model="ollama:test",
        context_window=32768,
        router_locator="tcp/127.0.0.1:7447",
    )
    scenario = {
        "inputs": [
            {"t_ms": 200, "ch": "rep_a", "value": 100},
            {"t_ms": 210, "ch": "rep_a", "value": 300},
        ],
        # 固件内嵌场景的规格推导 golden（M1 replay：slew 5/ms → 100/155/100/7）
        "expectations": [
            {"ch": "rep_a", "op": "eq", "value": 7},
            {"ch": "rep_a", "op": "count", "value": 4},
        ],
    }
    report = asyncio.run(sim_run(cfg, scenario, task_id="e2e"))
    assert report["determinism"] is True
    assert report["evaluation"]["pass"] is True
    assert report["writes"] == 4  # stdout 仅输出 rep_a 通道（M1 接口：单通道 JSONL）
