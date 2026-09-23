# SPDX-License-Identifier: Apache-2.0
"""L3 端到端联调客户端（LLD-ts-net §8-L3；M3a.2 记录）。

前置：
  1. zenohd 运行：~/project/tools/zenohd --listen tcp/0.0.0.0:7447
  2. 固件运行：build-l3/zephyr/zephyr.exe --tap=zeth（TAP host 侧 192.0.2.2）
用法：agent-venv python firmware/l3app/l3_client.py
退出码 0 = 全部 L3 验证点通过；输出 JSON 结论。

验证点（LLD §8）：
  ① 发现：cube→host 心跳（sys/hb）与遥测（l3led/telemetry）到达
  ② 命令-回执：sys/get-info / get-link / get-safety query-reply（status=0）
     estop-clear 错误令牌 = status=TS_E_PARAM(-1)（确认令牌硬点）
  ③ 心跳保持与断链判定：持续 hb-host → link_up=true（通道恢复 ACTIVE 可写）；
     停发 >6 周期（10s）→ link_up=false 且通道进 SAFE_LINKLOSS（get-safety 计数）
"""
from __future__ import annotations

import json
import sys
import time

import cbor2
import zenoh

Z = "tessera/l3n/l3c"
TS_E_PARAM = -1


def tstr(s: str) -> bytes:
    b = s.encode()
    assert len(b) < 24
    return bytes([0x60 | len(b)]) + b


def req(op: str) -> bytes:
    """定体请求 map{"op": op}（固件 cbor_min 确定性子集）。"""
    return bytes([0xA1]) + tstr("op") + tstr(op)


def query(s, cmd: str, payload: bytes | None = None) -> tuple[int, dict]:
    """sys 命令 query → (status, data)。回执 = map{"status", "data"}。"""
    replies = s.get(f"{Z}/sys/{cmd}", payload=payload if payload else req(cmd))
    for r in replies:
        if r.ok is None:
            raise RuntimeError(f"query {cmd} replied ERR: {r.err_payload}")
        m = cbor2.loads(bytes(r.ok.payload))
        return int(m["status"]), (m.get("data") if isinstance(m.get("data"), dict) else {})
    raise RuntimeError(f"query {cmd}: no reply")


def main() -> int:
    conf = zenoh.Config()
    conf.insert_json5("connect", json.dumps({"endpoints": ["tcp/127.0.0.1:7447"]}))
    s = zenoh.open(conf)

    seen: dict[str, int] = {}

    def on_sample(sample) -> None:
        k = str(sample.key_expr)
        seen[k] = seen.get(k, 0) + 1

    sub = s.declare_subscriber("tessera/**", handler=on_sample)

    out: dict[str, object] = {}

    # ① 发现：等心跳与遥测到达（固件连接 + 200ms 快照 + 1s 心跳）
    deadline = time.time() + 15
    while time.time() < deadline and not (
        seen.get(f"{Z}/sys/hb") and seen.get(f"{Z}/l3led/telemetry")
    ):
        time.sleep(0.2)
    out["hb_arrived"] = seen.get(f"{Z}/sys/hb", 0)
    out["telem_arrived"] = seen.get(f"{Z}/l3led/telemetry", 0)
    if not out["hb_arrived"] or not out["telem_arrived"]:
        print(json.dumps({"FAIL": "discovery", **out}, ensure_ascii=False, default=str))
        return 1

    # ② 命令-回执
    st_info, d_info = query(s, "get-info")
    st_link, d_link = query(s, "get-link")
    st_safety, _ = query(s, "get-safety")
    # estop-clear 错误令牌（op 带 args.confirm="stop" → 固件拒 TS_E_PARAM）
    bad = bytes([0xA2]) + tstr("op") + tstr("estop-clear") + tstr("args") + \
        bytes([0xA1]) + tstr("confirm") + tstr("stop")
    st_estop, _ = query(s, "estop-clear", payload=bad)
    out.update(
        get_info_status=st_info, fw=d_info.get("fw"), board=d_info.get("board"),
        get_link_status=st_link, session_state=d_link.get("state"),
        get_safety_status=st_safety, estop_clear_wrong_token=st_estop,
    )
    if st_info != 0 or st_link != 0 or st_safety != 0 or st_estop != TS_E_PARAM:
        print(json.dumps({"FAIL": "commands", **out}, ensure_ascii=False, default=str))
        return 1

    # ③ 心跳保持 → link_up（滞回 2 次即恢复）
    for _ in range(8):  # 8 × 0.4s ≈ 3.2s
        s.put(f"{Z}/sys/hb-host", b"hb")
        time.sleep(0.4)
    time.sleep(0.5)
    _, d2 = query(s, "get-link")
    out["link_up_after_hb"] = d2.get("link_up")
    _, ds2 = query(s, "get-safety")
    out["active_after_hb"] = ds2.get("active")

    # 断链：停发 10s（> 6 周期 × 1s）→ link_up=false + 通道 LINKLOSS
    time.sleep(10)
    _, d3 = query(s, "get-link")
    _, ds3 = query(s, "get-safety")
    out["link_up_after_starve"] = d3.get("link_up")
    out["linkloss_after_starve"] = ds3.get("linkloss")
    # bool 经 CBOR 解码可能为 True/CBORSimpleValue——统一归一后比较
    def as_bool(v: object) -> bool:
        if isinstance(v, bool):
            return v
        return getattr(v, "value", None) == 1 or str(v) in ("1", "True", "true")

    ok = (
        as_bool(out["link_up_after_hb"])
        and out["active_after_hb"] == 1
        and not as_bool(out["link_up_after_starve"])
        and out["linkloss_after_starve"] == 1
    )
    out["result"] = "PASS" if ok else "FAIL"
    print(json.dumps(out, ensure_ascii=False, default=str))
    sub.undeclare()
    s.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
