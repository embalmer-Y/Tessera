#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""flash_prov.py — 生产 prov 直写工具（DEC-49③A：esptool 分区直写，制造期纪律）。

生成含**真实 pk0** 的 prov CBOR blob（node/cube/路由器/根公钥）并经
esptool 写入 ts-prov 分区（运行时只读面，合同 10）。

用法（制造期一次性，板在 esptool 模式）：
  python flash_prov.py --node n1 --cube c1 --router tcp/192.168.2.90:9955 \
      --pub0 root.pub --port /dev/ttyACM0 --offset 0x170000
  # standalone 设备 + 远程 estop 清除禁用（CG2/Q-42 schema v2）：
  python flash_prov.py ... --deploy-mode standalone --estop-remote-clear disabled

分区偏移须与板级 DT ts_prov_part 一致——**缺省 0x170000 = xiao 时代 bench 布局**；
ATK DNESP32-S3B（atkbench）实际 = **0x5f0000**（overlay ts_prov_part 实证）——
误烧落主固件槽尾部未用区（零功能损伤但 prov 不生效，2026-10-19 实测复盘）。
分区镜像 = u32 cbor_len（小端）| u16 crc16-ccitt（小端）| cbor[]——与
prov.c 装载器布局一致（CG2 修复：此前直写裸 CBOR，装载器必拒）。
键序 = prov.c 固定走查序（v,node_id,cube_id,routers,pk0,pk1,cred,pwr_ma,
estop[,deploy_mode,estop_remote_clear[,lconf[,tls_ca,tls_cert,tls_key]]]——
尾部追加纪律：v2 两键显式给值时追加；--lconf → 12 键（F3 · DEC-62①）；
--tls-ca/cert/key 三参同给 → 15 键（P1-2 · DEC-63③，EC P-256 DER）。
"""
from __future__ import annotations

import argparse
import struct
import subprocess
import sys


def _tstr(s: str) -> bytes:
    b = s.encode()
    if len(b) < 24:
        return bytes([0x60 | len(b)]) + b
    assert len(b) < 256
    return bytes([0x78, len(b)]) + b


def _bstr(b: bytes) -> bytes:
    n = len(b)
    if n < 24:
        return bytes([0x40 | n]) + b
    if n < 256:
        return bytes([0x58, n]) + b
    assert n < 65536
    return bytes([0x59, n >> 8, n & 0xFF]) + b


def crc16_ccitt(data: bytes) -> int:
    """与固件 ts_crc16 同型（poly 0x1021 / init 0xFFFF，store/internal.h）。"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
            crc &= 0xFFFF
    return crc


def build_prov(node: str, cube: str, router: str, pk0: bytes,
               pk1: bytes = b"\x00" * 32, pwr_ma: int = 500,
               deploy_mode: int | None = None,
               estop_remote_clear: int | None = None,
               lconf: int | None = None,
               tls: tuple[bytes, bytes, bytes] | None = None) -> bytes:
    """构造 prov 分区镜像（头 + CBOR）。返回**整分区镜像**（非裸 CBOR）。

    schema 形态（键序 = prov.c 固定走查序，尾部追加纪律）：
      deploy_mode/estop_remote_clear 给值 → v2（11 键）；lconf → 12 键；
      tls = (ca_der, cert_der, key_der) 三元组同现 → 15 键（P1-2 · DEC-63③，
      EC P-256 DER）；None 维持既有缺省 → v1（9 键——旧固件兼容形状）。
    """
    assert len(pk0) == 32 and len(pk1) == 32
    v2 = (deploy_mode is not None or estop_remote_clear is not None
          or lconf is not None or tls is not None)
    pairs = 9
    if v2:
        pairs = 15 if tls is not None else (12 if lconf is not None else 11)
    out = bytearray()
    out += bytes([0xA0 | pairs])  # map(n) definite — 固定键序
    out += _tstr("v") + (b"\x02" if v2 else b"\x01")
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
    if v2:
        dm = deploy_mode if deploy_mode is not None else 0
        ec = estop_remote_clear if estop_remote_clear is not None else 1
        assert dm in (0, 1), "deploy_mode ∈ {0=orchestrated,1=standalone}"
        assert ec in (0, 1), "estop_remote_clear ∈ {0=disabled,1=enabled}"
        out += _tstr("deploy_mode") + bytes([dm])
        out += _tstr("estop_remote_clear") + bytes([ec])
    if pairs >= 12:
        lc = lconf if lconf is not None else 0
        assert lc in (0, 1), "lconf ∈ {0=off,1=on}"
        out += _tstr("lconf") + bytes([lc])
    if tls is not None:
        ca, cert, key = tls
        assert ca and cert and key, "TLS 三元组键在值空 = fail-closed（DEC-63③）"
        out += _tstr("tls_ca") + _bstr(ca)
        out += _tstr("tls_cert") + _bstr(cert)
        out += _tstr("tls_key") + _bstr(key)
    return struct.pack("<IH", len(out), crc16_ccitt(bytes(out))) + bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", required=True)
    ap.add_argument("--cube", required=True)
    ap.add_argument("--router", required=True)
    ap.add_argument("--pub0", required=True, help="生产根公钥（32B raw）")
    ap.add_argument("--pub1", default=None)
    ap.add_argument("--pwr-ma", type=int, default=500)
    ap.add_argument("--deploy-mode", choices=["orchestrated", "standalone"],
                    default=None, help="schema v2 部署模式（缺省 = v1 形状 = orchestrated）")
    ap.add_argument("--estop-remote-clear", choices=["enabled", "disabled"],
                    default=None, help="schema v2 远程 estop 清除通道（缺省 = v1 形状 = enabled）")
    ap.add_argument("--lconf", type=int, choices=[0, 1], default=None,
                    help="schema v2 12 键：安装闸本地确认（0=off/1=on；F3 · DEC-62①）")
    ap.add_argument("--tls-ca", default=None,
                    help="CA 证书 DER 文件（15 键三元组之一——P1-2 · DEC-63③，三参须同给）")
    ap.add_argument("--tls-cert", default=None,
                    help="设备客户端证书 DER 文件（三元组之一）")
    ap.add_argument("--tls-key", default=None,
                    help="设备私钥 DER 文件（EC SEC1；三元组之一）")
    ap.add_argument("--port", required=True)
    ap.add_argument("--offset", type=lambda x: int(x, 0), default=0x170000)
    a = ap.parse_args()

    pk0 = open(a.pub0, "rb").read()
    pk1 = open(a.pub1, "rb").read() if a.pub1 else b"\x00" * 32
    dm = None if a.deploy_mode is None else int(a.deploy_mode == "standalone")
    ec = None if a.estop_remote_clear is None else int(a.estop_remote_clear == "enabled")
    tls = None
    if any((a.tls_ca, a.tls_cert, a.tls_key)):
        assert all((a.tls_ca, a.tls_cert, a.tls_key)), "--tls-ca/cert/key 须同给（三键同现纪律）"
        tls = (open(a.tls_ca, "rb").read(), open(a.tls_cert, "rb").read(),
               open(a.tls_key, "rb").read())
        assert all(len(x) > 0 for x in tls), "TLS 三元组空文件 = fail-closed"
    blob = build_prov(a.node, a.cube, a.router, pk0, pk1, a.pwr_ma, dm, ec,
                      a.lconf, tls)
    tls_desc = "off"
    if tls is not None:
        tls_desc = f"on ca={len(tls[0])}B cert={len(tls[1])}B key={len(tls[2])}B"
    print(f"prov image: {len(blob)}B（头 6B + cbor {len(blob) - 6}B；"
          f"pk0={pk0.hex()[:16]}… deploy_mode={a.deploy_mode or 'v1-default'} "
          f"estop_remote_clear={a.estop_remote_clear or 'v1-default'} "
          f"lconf={a.lconf if a.lconf is not None else '缺省'} "
          f"tls={tls_desc}）")
    # esptool ≥5 不再接受 stdin "-"（write-flash 用法错）——落临时文件传路径
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tf:
        tf.write(blob)
        img = tf.name
    # esptool ≥5 二进制名无 .py 后缀（ARM 重建机 v5.4.0 实测）——which 解析
    import shutil

    esptool = shutil.which("esptool.py") or shutil.which("esptool")
    if esptool is None:
        print("esptool 不在 PATH（≥5 = `esptool`，旧版 = `esptool.py`）",
              file=sys.stderr)
        return 2
    # 写前擦除 prov 分区 4KB（教训 33：prov 换烧必擦——残留旧尾键被
    # len 前缀掩盖的风险面；分区尺寸 = 0x1000，bench 布局与生产同）
    subprocess.run(
        [esptool, "--port", a.port, "erase-region", hex(a.offset), "0x1000"],
        check=True)
    subprocess.run(
        [esptool, "--port", a.port, "write-flash", hex(a.offset), img],
        check=True)
    print("written（复位后 prov_load 直读——运行时只读面）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
