# SPDX-License-Identifier: Apache-2.0
"""zenoh key 约定与命令信封镜像（LLD-A06 §2；固件侧权威 = LLD-ts-net §3/§4.4）。

镜像纪律：key 构造与 kind 注册表**不自行发明**——固件侧定义变更时本文件同步
（与 l3_client.py 同源对拍，Q-19 #13 skill/镜像同步检查项的部署面部分）。
请求编码 = 固件 cbor_min 确定性子集（definite map/tstr/uint/bstr，定键序）；
回执解析用 cbor2 全解码（host 侧只读，容错未知 kind 透传不解析——DEC-42 §0）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cbor2

# ---- kind 注册表（唯一权威 = LLD-ts-net §4.4；Agent 侧镜像）----------------
KIND_SYS_REQUEST = 1    # 请求区间 1-15：1 = sys 命令（op 分流）
KIND_CMD_REPLY = 16     # 回执区间 16-31：16 = 命令回执
KIND_EVT_BASE = 32      # 事件区间 32-95：32 + TS_EVT_ID
KIND_TELEMETRY = 96     # 遥测区间 96-127：96 = 输出实例快照

# 信封身份缺省（审计归因 src，DEC-40）
DEFAULT_SRC = "tessera-agent"

# 固件侧长度上限（LLD-ts-net §4.2；镜像——越界即拒绝）
RID_MAX = 16
IDEM_MAX = 16
HOLDER_MAX = 24
TO_MAX_MS = 5000


def key_prefix(node: str, cube: str) -> str:
    return f"tessera/{node}/{cube}"


def key_sys(node: str, cube: str, cmd: str) -> str:
    return f"tessera/{node}/{cube}/sys/{cmd}"


def key_cmd(node: str, cube: str, uid: str) -> str:
    return f"tessera/{node}/{cube}/{uid}/cmd"


def key_tel(node: str, cube: str, uid: str) -> str:
    return f"tessera/{node}/{cube}/{uid}/telemetry"


def key_evt(node: str, cube: str, uid: str) -> str:
    return f"tessera/{node}/{cube}/{uid}/event"


def key_hb(node: str, cube: str, *, host_dir: bool = False) -> str:
    suffix = "hb-host" if host_dir else "hb"  # DR-12
    return f"tessera/{node}/{cube}/sys/{suffix}"


# ---- cbor_min 确定性子集编码（请求构造；与固件编码器同标）------------------

def _tstr(s: str) -> bytes:
    b = s.encode()
    if len(b) < 24:
        return bytes([0x60 | len(b)]) + b
    if len(b) < 256:
        return bytes([0x78]) + bytes([len(b)]) + b
    msg = f"tstr 超 cbor_min 即时长度域: {len(b)}B"
    raise ValueError(msg)


def _uint(v: int) -> bytes:
    if v < 0:
        msg = f"负值非 uint: {v}"
        raise ValueError(msg)
    if v < 24:
        return bytes([v])
    for n, ai in ((1, 24), (2, 25), (4, 26), (8, 27)):
        if v < (1 << (8 * n)):
            return bytes([ai]) + v.to_bytes(n, "big")
    msg = f"uint 溢出: {v}"
    raise ValueError(msg)


def _bstr(d: bytes) -> bytes:
    n = len(d)
    if n < 24:
        return bytes([0x40 | n]) + d
    if n < 256:
        return bytes([0x58]) + bytes([n]) + d
    if n < 65536:
        return bytes([0x59]) + n.to_bytes(2, "big") + d
    msg = f"bstr 超 cbor_min 长度域: {n}B"
    raise ValueError(msg)


def envelope(
    op: str,
    rid: str,
    src: str = DEFAULT_SRC,
    *,
    total: int | None = None,
    offset: int | None = None,
    data: bytes | None = None,
    holder: str | None = None,
    time_ms: int | None = None,
    confirm: str | None = None,
    idem: str | None = None,
    to: int | None = None,
) -> bytes:
    """命令信封 v2 请求（DEC-40）：map{ver,kind,rid,src,op,args?}。

    args 定序：total → offset → data → holder → time_ms → confirm → idem → to
    （固件解码键序无关，编码侧定序保确定性——合同 9）。
    """
    if len(rid) > RID_MAX:
        msg = f"rid 超上限 {RID_MAX}: {rid!r}"
        raise ValueError(msg)
    if src and len(src) > HOLDER_MAX:
        msg = f"src 超上限 {HOLDER_MAX}: {src!r}"
        raise ValueError(msg)
    if idem is not None and len(idem) > IDEM_MAX:
        msg = f"idem 超上限 {IDEM_MAX}: {idem!r}"
        raise ValueError(msg)
    items: list[tuple[bytes, bytes]] = []
    if total is not None:
        items.append((_tstr("total"), _uint(total)))
    if offset is not None:
        items.append((_tstr("offset"), _uint(offset)))
    if data is not None:
        items.append((_tstr("data"), _bstr(data)))
    if holder is not None:
        items.append((_tstr("holder"), _tstr(holder)))
    if time_ms is not None:
        items.append((_tstr("time_ms"), _uint(time_ms)))
    if confirm is not None:
        items.append((_tstr("confirm"), _tstr(confirm)))
    if idem is not None:
        items.append((_tstr("idem"), _tstr(idem)))
    if to is not None:
        items.append((_tstr("to"), _uint(to)))
    out = bytes([0xA5 if not items else 0xA6]) \
        + _tstr("ver") + _uint(1) \
        + _tstr("kind") + _uint(KIND_SYS_REQUEST) \
        + _tstr("rid") + _tstr(rid) \
        + _tstr("src") + _tstr(src) \
        + _tstr("op") + _tstr(op)
    if items:
        out += _tstr("args") + bytes([0xA0 | len(items)])
        for k, v in items:
            out += k + v
    return out


# ---- 回执解析（v1/v2 兼容；未知键透传保留于 data）---------------------------

@dataclass
class Reply:
    status: int
    data: dict[str, Any] = field(default_factory=dict)
    ver: int | None = None
    kind: int | None = None
    rid: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def v2(self) -> bool:
        return self.ver is not None


def parse_reply(payload: bytes) -> Reply:
    """回执 map 解析：v1 {status,data} / v2 {ver,kind,rid,status,data}（键集判别）。"""
    m = cbor2.loads(payload)
    if not isinstance(m, dict) or "status" not in m:
        msg = f"回执非法（无 status）: {sorted(m) if isinstance(m, dict) else type(m)}"
        raise ValueError(msg)
    data = m.get("data")
    return Reply(
        status=int(m["status"]),
        data=data if isinstance(data, dict) else {},
        ver=m.get("ver"),
        kind=m.get("kind"),
        rid=m.get("rid"),
        raw=m,
    )
