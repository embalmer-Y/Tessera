# SPDX-License-Identifier: Apache-2.0
"""tsap_* 工具实现（LLD-A05 §3）。

无签名不产出（合同"Agent 无豁免"硬点）：key 缺失/校验失败 → TA_E_TSAP，
**不降级出未签名包**。容器 = TSAP v1（16B 头/大端，M2a 定稿，include/ts/tsap.h）。
"""

from __future__ import annotations

import hashlib
import os
import re
import struct
from pathlib import Path

from tessera_agent.common.errors import TA_E_ARGS, TA_E_POLICY, TA_E_TSAP, TaError
from tessera_agent.tools_tsap import cose
from tessera_agent.tools_tsap.manifest import TsapManifest

TSAP_MAGIC = 0x54534150  # "TSAP"（大端，M2a 定稿）
TSAP_FMT_VER = 1
TSAP_HEADER = struct.Struct(">IHIIH")  # magic|fmt_ver|manifest_len|wasm_len|rsv


def tsap_keygen(name: str, out_dir: str, allowed_roots: list[str]) -> dict:
    """Ed25519 开发密钥对生成（strict 类）。私钥仅写文件 0600，不进返回/日志。 """
    if not re.fullmatch(r"[a-zA-Z0-9._-]{1,48}", name):
        msg = f"非法密钥名: {name!r}"
        raise TaError(TA_E_ARGS, msg, domain="tsap")
    base = Path(os.path.expanduser(out_dir))
    real = base.resolve()
    for root in allowed_roots:
        r = Path(os.path.expanduser(root)).resolve()
        if real == r or str(real).startswith(str(r) + os.sep):
            break
    else:
        msg = f"密钥目录越界（白名单外）: {out_dir}"
        raise TaError(TA_E_POLICY, msg, domain="tsap")
    real.mkdir(parents=True, exist_ok=True)
    priv_path = real / f"{name}.key"
    pub_path = real / f"{name}.pub"
    if priv_path.exists() or pub_path.exists():
        msg = f"密钥已存在（拒绝覆盖）: {name}"
        raise TaError(TA_E_ARGS, msg, domain="tsap")
    d, x = cose.generate_keypair()
    priv_path.write_bytes(d)
    os.chmod(priv_path, 0o600)
    pub_path.write_bytes(x)
    fingerprint = hashlib.sha256(x).hexdigest()[:16]
    return {"pub_key_path": str(pub_path), "pub_key_fingerprint": fingerprint}


def tsap_package(wasm_path: str, manifest: dict, key_path: str, out_dir: str) -> dict:
    """打包签名（confirm 类，句柄化）。返回 {package_path, manifest_digest, signer_impl…}。"""
    wasm = Path(os.path.expanduser(wasm_path))
    if not wasm.is_file():
        msg = f"wasm 不存在: {wasm_path}"
        raise TaError(TA_E_ARGS, msg, domain="tsap")
    try:
        m = TsapManifest(**manifest)
    except Exception as exc:  # noqa: BLE001
        raise TaError(TA_E_ARGS, f"manifest 非法: {exc}", domain="tsap") from exc

    key_file = Path(os.path.expanduser(key_path))
    if not key_file.is_file():
        msg = f"签名私钥不存在: {key_path}（无签名不产出——硬点）"
        raise TaError(TA_E_TSAP, msg, domain="tsap")
    d = key_file.read_bytes()
    if len(d) != 32:
        msg = "私钥格式非法（须 ed25519 raw 32B）"
        raise TaError(TA_E_TSAP, msg, domain="tsap")

    manifest_cbor = m.to_cbor()
    wasm_bytes = wasm.read_bytes()
    payload = manifest_cbor + wasm_bytes
    cose_bytes, signer = cose.sign_cross_verified(payload, d)

    header = TSAP_HEADER.pack(TSAP_MAGIC, TSAP_FMT_VER, len(manifest_cbor), len(wasm_bytes), 0)
    package = header + payload + cose_bytes

    out = Path(os.path.expanduser(out_dir))
    out.mkdir(parents=True, exist_ok=True)
    pkg_path = out / f"{m.app_id}-{m.app_ver}.tsap"
    pkg_path.write_bytes(package)
    return {
        "package_path": str(pkg_path),
        "size": len(package),
        "manifest_digest": hashlib.sha256(manifest_cbor).hexdigest()[:16],
        "signature_fingerprint": hashlib.sha256(cose_bytes).hexdigest()[:16],
        "signer_impl": signer,
    }


def tsap_verify(package_path: str, pub_key_path: str) -> dict:
    """全量反向验证（auto 类）：容器 → COSE 双实现验签 → manifest 解码。"""
    pkg = Path(os.path.expanduser(package_path))
    if not pkg.is_file():
        msg = f"包不存在: {package_path}"
        raise TaError(TA_E_ARGS, msg, domain="tsap")
    data = pkg.read_bytes()
    if len(data) < TSAP_HEADER.size:
        msg = "包长度不足（头 16B）"
        raise TaError(TA_E_TSAP, msg, domain="tsap")
    magic, ver, mlen, wlen, _rsv = TSAP_HEADER.unpack_from(data, 0)
    checks: list[str] = []
    if magic != TSAP_MAGIC:
        checks.append("magic")
    if ver != TSAP_FMT_VER:
        checks.append("fmt_ver")
    cose_off = TSAP_HEADER.size + mlen + wlen
    if cose_off >= len(data):
        checks.append("lengths")
    if checks:
        msg = f"容器头校验失败: {checks}"
        raise TaError(TA_E_TSAP, msg, domain="tsap", detail={"checks": checks})

    manifest_cbor = data[TSAP_HEADER.size : TSAP_HEADER.size + mlen]
    cose_bytes = data[cose_off:]
    pub = Path(os.path.expanduser(pub_key_path)).read_bytes()
    ok, impls = cose.verify_both(cose_bytes, pub)
    if not ok:
        msg = "COSE 验签失败"
        raise TaError(TA_E_TSAP, msg, domain="tsap", detail={"impls": impls})
    try:
        m = TsapManifest.from_cbor(manifest_cbor)
    except Exception as exc:  # noqa: BLE001
        raise TaError(TA_E_TSAP, f"manifest 解码失败: {exc}", domain="tsap") from exc
    return {
        "valid": True,
        "manifest": m.model_dump(),
        "checks": ["header", "cose.pycose", "cose.diy", "manifest"],
        "wasm_len": wlen,
    }
