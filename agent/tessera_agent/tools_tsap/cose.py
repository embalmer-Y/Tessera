# SPDX-License-Identifier: Apache-2.0
"""COSE_Sign1(ed25519) 双实现（LLD-A05 §1 / DR-21 / R5 §4）。

- 主路径 = pycose；DIY = cryptography ed25519 + cbor2 手构 RFC 9052 Sig_structure。
- **双实现互验**：任一产物必须能被另一实现验签（pycose 验 DIY 产物 / 反之）——
  对冲 pycose 停更风险（R5：2023-12 后无 release）。
- **单键纪律（DR-21）**：protected header 只放 {1: -8}(alg=EdDSA)，KID 入
  unprotected——规避 pycose 内部非 canonical map 序的字节复现隐患。
"""

from __future__ import annotations

import cbor2
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from pycose.keys import OKPKey
from pycose.messages import Sign1Message

ALG_EDDSA = -8


def generate_keypair() -> tuple[bytes, bytes]:
    """返回 (private_raw32, public_raw32)。"""
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    d = priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    x = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return d, x


def _phdr() -> dict:
    return {1: ALG_EDDSA}  # 单键纪律（DR-21）


def _pycose_key(d: bytes | None, x: bytes | None) -> OKPKey:
    # pycose OKP 要求 x 必在（私钥也需公钥分量）；且其 from_dict 对 -3(d) 有
    # 归零怪癖（实测 1.1.0）——故直接构造 OKPKey
    if d is not None and x is None:
        x = _pub_of(d)
    if d is not None:
        return OKPKey(crv=6, x=x, d=d)
    return OKPKey(crv=6, x=x)  # d=None 会触发其 setter 报错（实测 1.1.0）


def sign_pycose(payload: bytes, private_raw: bytes) -> bytes:
    msg = Sign1Message(phdr=_phdr(), payload=payload)
    msg.key = _pycose_key(private_raw, None)
    return msg.encode()


def verify_pycose(cose_sign1: bytes, public_raw: bytes) -> bool:
    try:
        # cbor2 6.x 将数组解码为 tuple，而 pycose 1.1.0 的 decode 只认 list
        #（停更兼容缺口，R5 风险实证）——手工剥 tag 转 list 后走 from_cose_obj
        obj = cbor2.loads(cose_sign1)
        if not isinstance(obj, cbor2.CBORTag) or obj.tag != 18:
            return False
        fields = list(obj.value)
        fields[1] = dict(fields[1])  # cbor2 6.x 空 map -> frozendict（非 dict 子类）
        msg = Sign1Message.from_cose_obj(fields, True)
    except Exception:  # noqa: BLE001
        return False
    msg.key = _pycose_key(None, public_raw)
    return bool(msg.verify_signature())  # pycose 1.1.0 方法名（无 verify）




def sign_diy(payload: bytes, private_raw: bytes) -> bytes:
    priv = Ed25519PrivateKey.from_private_bytes(private_raw)
    phdr_bstr = cbor2.dumps(_phdr(), canonical=True)
    sig_structure = ["Signature1", phdr_bstr, b"", payload]
    to_be_signed = cbor2.dumps(sig_structure, canonical=True)
    sig = priv.sign(to_be_signed)
    # wire 层 uhdr = 真实空 map（cbor2 编码为 0xa0）；Sig_structure 第三段 =
    # external_aad(b"")——两者不同（RFC 9052 §4.2）
    return cbor2.dumps(cbor2.CBORTag(18, [phdr_bstr, {}, payload, sig]), canonical=True)


def verify_diy(cose_sign1: bytes, public_raw: bytes) -> bool:
    try:
        tag = cbor2.loads(cose_sign1)
        if not isinstance(tag, cbor2.CBORTag) or tag.tag != 18:
            return False
        phdr_bstr, uhdr, payload, sig = tag.value
        uhdr_ok = hasattr(uhdr, "keys") and len(uhdr) == 0  # dict 或 frozendict 空 map
        if not uhdr_ok or not isinstance(phdr_bstr, bytes) or not isinstance(sig, bytes):
            return False
        phdr = cbor2.loads(phdr_bstr)
        if phdr != _phdr():
            return False
        to_be_signed = cbor2.dumps(["Signature1", phdr_bstr, b"", payload], canonical=True)
        pub = Ed25519PublicKey.from_public_bytes(public_raw)
        pub.verify(sig, to_be_signed)
        return True
    except Exception:  # noqa: BLE001
        return False


def sign_cross_verified(payload: bytes, private_raw: bytes) -> tuple[bytes, str]:
    """签名并强制双实现互验；返回 (cose_sign1, signer_impl)。"""
    cose = sign_pycose(payload, private_raw)
    if not verify_diy(cose, _pub_of(private_raw)):
        msg = "双实现互验失败（pycose 签名/DIY 验签）"
        raise RuntimeError(msg)
    return cose, "pycose"


def _pub_of(private_raw: bytes) -> bytes:
    priv = Ed25519PrivateKey.from_private_bytes(private_raw)
    return priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


def verify_both(cose_sign1: bytes, public_raw: bytes) -> tuple[bool, dict]:
    """双实现验签（install 链复验用）；返回 (ok, 详情)。"""
    p = verify_pycose(cose_sign1, public_raw)
    d = verify_diy(cose_sign1, public_raw)
    return p and d, {"pycose": p, "diy": d}
