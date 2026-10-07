#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""flash_prov.py — 生产 prov 直写工具（DEC-49③A：esptool 分区直写，制造期纪律）。

生成含**真实 pk0** 的 prov CBOR blob（node/cube/路由器/根公钥）并经
esptool 写入 ts-prov 分区（运行时只读面，合同 10）。

用法（制造期一次性，板在 esptool 模式）：
  python flash_prov.py --node n1 --cube c1 --router tcp/192.168.2.90:9955 \
      --pub0 root.pub --port /dev/ttyACM0 --offset 0x170000

分区偏移须与板级 DT ts_prov_part 一致（bench 布局 = 0x170000/0x1000）。
键序 = prov.c 固定走查序（v,node_id,cube_id,routers,pk0,pk1,cred,pwr_ma,estop）。
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def _tstr(s: str) -> bytes:
    b = s.encode()
    if len(b) < 24:
        return bytes([0x60 | len(b)]) + b
    assert len(b) < 256
    return bytes([0x78, len(b)]) + b


def _bstr(b: bytes) -> bytes:
    assert len(b) < 256
    return (bytes([0x40 | len(b)]) if len(b) < 24 else bytes([0x58, len(b)])) + b


def build_prov(node: str, cube: str, router: str, pk0: bytes,
               pk1: bytes = b"\x00" * 32, pwr_ma: int = 500) -> bytes:
    assert len(pk0) == 32 and len(pk1) == 32
    out = bytearray()
    out += b"\xa9"  # map(9) — 固定键序
    out += _tstr("v") + b"\x01"
    out += _tstr("node_id") + _tstr(node)
    out += _tstr("cube_id") + _tstr(cube)
    out += _tstr("routers") + b"\x81" + _tstr(router)
    out += _tstr("pk0") + _bstr(pk0)
    out += _tstr("pk1") + _bstr(pk1)
    out += _tstr("cred") + _tstr("")
    out += _tstr("pwr_ma")
    assert pwr_ma < 65536
    out += bytes([0x19, pwr_ma >> 8, pwr_ma & 0xFF])
    out += _tstr("estop") + b"\x00"
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--cube", required=True)
    ap.add_argument("--router", required=True)
    ap.add_argument("--pub0", required=True, help="生产根公钥（32B raw）")
    ap.add_argument("--pub1", default=None)
    ap.add_argument("--pwr-ma", type=int, default=500)
    ap.add_argument("--port", required=True)
    ap.add_argument("--offset", type=lambda x: int(x, 0), default=0x170000)
    a = ap.parse_args()

    pk0 = open(a.pub0, "rb").read()
    pk1 = open(a.pub1, "rb").read() if a.pub1 else b"\x00" * 32
    blob = build_prov(a.node, a.cube, a.router, pk0, pk1, a.pwr_ma)
    print(f"prov blob: {len(blob)}B（走查键序；pk0={pk0.hex()[:16]}…）")
    subprocess.run(
        ["esptool.py", "--port", a.port, "write-flash", hex(a.offset), "-"],
        input=blob, check=True)
    print("written（复位后 prov_load 直读——运行时只读面）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
