# SPDX-License-Identifier: Apache-2.0
"""deploy_* 实现（LLD-A06 §3）：发现 / 状态 / TSAP 包分块推送。

push_app 纪律（全部硬点，工具内强制）：
  ① tsap_verify 复验不可跳过（链外直调同样强制）；
  ② 租约闭环（DEC-41）：acquire → 周期续期 → 结束 release（失败也 release）；
  ③ 分块 2KB 默认（上限 4KB，NeuroLink 实证档位）+ 每块 idem（重试安全，DEC-40）；
  ④ 分步对齐固件安装链：upload → verify（容器事实对拍）→ activate → get-app
     确认（版本回读一致才置 confirmed）。
同步实现（zenoh 会话经 ZenohService 工作线程）；网关侧 asyncio 用 to_thread 包装。
"""

from __future__ import annotations

import secrets
import struct
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tessera_agent.common.errors import TA_E_ARGS, TA_E_POLICY, TA_E_TSAP, TaError
from tessera_agent.tools_net import keys
from tessera_agent.tools_net.zenoh_service import ZenohService
from tessera_agent.tools_tsap import tools as tsap_tools

# 来源: LLD-A06 §3（2KB 默认 / 4KB 上限）
CHUNK_DEFAULT = 2048
CHUNK_MAX = 4096
# 来源: DEC-41（TTL 10s）——续期间隔 = TTL/3
LEASE_TTL_S = 10.0
RENEW_AFTER_S = LEASE_TTL_S / 3.0
# 单块重试（超时/无回执可重试；idem 保证重发安全）
CHUNK_RETRY_MAX = 3

# TSAP v1 头（M2a 定稿，大端）：magic u32 | fmt u16 | manifest u32 | wasm u32 | rsv u16
_TSAP_HDR = struct.Struct(">IHIIH")


class CmdError(TaError):
    """固件命令回执 status != 0（携带原始 status/data）。"""

    def __init__(self, op: str, reply: keys.Reply) -> None:
        self.status = reply.status
        self.reply_data = reply.data
        msg = f"固件命令 {op} 拒绝: status={reply.status} data={reply.data}"
        super().__init__(TA_E_POLICY, msg, domain="deploy",
                         detail={"op": op, "status": reply.status, "data": reply.data})


def _cmd(svc: ZenohService, node: str, cube: str, op: str, rid: str,
         **env: Any) -> keys.Reply:
    _, payload = svc.query_one(keys.key_sys(node, cube, op),
                               keys.envelope(op, rid, **env))
    return keys.parse_reply(payload)


def _cmd_ok(svc: ZenohService, node: str, cube: str, op: str, rid: str,
            **env: Any) -> dict[str, Any]:
    r = _cmd(svc, node, cube, op, rid, **env)
    if r.status != 0:
        raise CmdError(op, r)
    return r.data


def _retry(fn: Callable[[], Any], *, retries: int, log) -> Any:
    last: TaError | None = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except TaError as exc:
            last = exc
            if not getattr(exc, "retryable", False) or attempt == retries:
                raise
            log(f"retry {attempt}/{retries}: {exc.message}")
    raise last  # pragma: no cover（循环必经 raise/return）


def discover(svc: ZenohService, *, timeout_s: float = 10.0) -> list[dict[str, Any]]:
    """router 侧在线 cube 发现：通配 query get-info。

    身份以回执**载荷**为准（固件 get-info 自报 node/cube——通配查询的回执
    key 为查询通配形态，不作身份源）；未知形态载荷透传跳过（DEC-42 §0）。
    """
    replies = svc.query("tessera/*/*/sys/get-info",
                        keys.envelope("get-info", f"disc-{secrets.token_hex(3)}"),
                        timeout_s)
    cubes: dict[tuple[str, str], dict[str, Any]] = {}
    for _, payload in replies:
        r = keys.parse_reply(payload)
        node = r.data.get("node")
        cube = r.data.get("cube")
        if not isinstance(node, str) or not isinstance(cube, str) or not node or not cube:
            continue
        cubes.setdefault((node, cube), {
            "node_id": node,
            "cube_id": cube,
            "fw": r.data.get("fw"),
            "board": r.data.get("board"),
            "status": r.status,
        })
    return sorted(cubes.values(), key=lambda c: (c["node_id"], c["cube_id"]))


def status(svc: ZenohService, node: str, cube: str) -> dict[str, Any]:
    """组合 get-info + get-link + get-safety + get-app 快照（部署前核验依据）。"""
    d = secrets.token_hex(3)
    out: dict[str, Any] = {"node_id": node, "cube_id": cube}
    for op in ("get-info", "get-link", "get-safety", "get-app"):
        out[op] = _cmd_ok(svc, node, cube, op, f"{d}-{op}"[:keys.RID_MAX])
    return out


def push_app(
    svc: ZenohService,
    node: str,
    cube: str,
    package_path: str,
    pub_key_path: str,
    *,
    holder: str = keys.DEFAULT_SRC,
    chunk_size: int = CHUNK_DEFAULT,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """TSAP 包分块推送 + 分步安装（严格类语义由网关审批层承载）。"""
    log = log_fn or (lambda s: None)
    if not (1 <= chunk_size <= CHUNK_MAX):
        msg = f"chunk_size 越界 [1,{CHUNK_MAX}]: {chunk_size}"
        raise TaError(TA_E_ARGS, msg, domain="deploy")

    # ① tsap_verify 强制复验（不可跳过——工具内实现，链外直调同样强制）
    tsap_tools.tsap_verify(package_path, pub_key_path)
    pkg = Path(package_path).expanduser().read_bytes()
    if len(pkg) < _TSAP_HDR.size:
        msg = f"包长度不足（头 16B）: {len(pkg)}"
        raise TaError(TA_E_TSAP, msg, domain="deploy")
    magic, ver, mlen, wlen, _rsv = _TSAP_HDR.unpack_from(pkg, 0)
    if magic != tsap_tools.TSAP_MAGIC or ver != tsap_tools.TSAP_FMT_VER:
        msg = "本地容器头非法（复验已过，此处为双保险）"
        raise TaError(TA_E_TSAP, msg, domain="deploy")
    local_facts = {
        "manifest_len": mlen,
        "wasm_len": wlen,
        "cose_off": _TSAP_HDR.size + mlen + wlen,
    }
    log(f"tsap_verify PASS: {package_path}（{len(pkg)}B，分块 {chunk_size}B）")

    d = secrets.token_hex(3)  # 6 字符部署批次前缀（rid/idem 空间见 keys 上限）

    def rid(tag: str) -> str:
        return f"{d}-{tag}"[: keys.RID_MAX]

    def idem(tag: str) -> str:
        return f"{d}:{tag}"[: keys.IDEM_MAX]

    result: dict[str, Any] = {
        "package": str(package_path), "size": len(pkg),
        "chunks": (len(pkg) + chunk_size - 1) // chunk_size,
        "holder": holder,
    }
    lease_acquired = False
    renew_n = 0
    last_renew = 0.0

    def renew(force: bool = False) -> None:
        nonlocal renew_n, last_renew
        if not force and (time.monotonic() - last_renew) < RENEW_AFTER_S:
            return
        data = _cmd_ok(svc, node, cube, "lease-acquire", rid(f"la{renew_n}"),
                       holder=holder, idem=idem(f"la{renew_n}"))
        result["lease_id"] = data.get("lease_id")
        renew_n += 1
        last_renew = time.monotonic()

    try:
        # ② 租约闭环：acquire（续期幂等——同 holder re-acquire）
        renew(force=True)
        lease_acquired = True
        log(f"lease acquired: id={result['lease_id']} holder={holder}")

        # ③ upload：begin → 分块（每块 idem + 超时重试；重发安全）
        data = _cmd_ok(svc, node, cube, "app-begin", rid("begin"),
                       total=len(pkg), idem=idem("begin"))
        result["slot"] = data.get("slot")
        log(f"upload → slot {result['slot']}（total={len(pkg)}B）")
        sent = 0
        for off in range(0, len(pkg), chunk_size):
            piece = pkg[off:off + chunk_size]

            def send(o: int = off, p: bytes = piece) -> dict:
                return _cmd_ok(svc, node, cube, "app-chunk", rid(f"c{o}"),
                               offset=o, data=p, idem=idem(f"c{o}"))

            r = _retry(send, retries=CHUNK_RETRY_MAX, log=log)
            got_hw = int(r.get("high_water", 0))
            if got_hw < off + len(piece):
                msg = f"块回执进度回退: off={off} high_water={got_hw}"
                raise TaError(TA_E_TSAP, msg, domain="deploy",
                              detail={"offset": off, "high_water": got_hw})
            sent += len(piece)
            renew()
        result["uploaded"] = sent
        log(f"upload complete: {sent}/{len(pkg)}B")

        # ④ verify：固件容器事实与本地对拍（「版本回读一致」确认语义的前半）
        fw_facts = _cmd_ok(svc, node, cube, "app-verify", rid("verify"),
                           idem=idem("verify"))
        result["verify"] = fw_facts
        if {k: int(fw_facts[k]) for k in local_facts if k in fw_facts} != local_facts:
            msg = f"容器事实对拍失败: 固件={fw_facts} 本地={local_facts}"
            raise TaError(TA_E_TSAP, msg, domain="deploy",
                          detail={"firmware": fw_facts, "local": local_facts})
        log(f"verify PASS: facts={fw_facts}")

        # ⑤ activate → get-app 确认（版本回读一致才置 confirmed）
        act = _cmd_ok(svc, node, cube, "app-activate", rid("activate"),
                      idem=idem("activate"))
        result["active_slot"] = act.get("active_slot")
        app = _cmd_ok(svc, node, cube, "get-app", rid("getapp"))
        result["app"] = app
        result["confirmed"] = int(app.get("active_slot", -1)) == int(result["active_slot"])
        if not result["confirmed"]:
            msg = f"确认回读不一致: activate slot={result['active_slot']} get-app={app}"
            raise TaError(TA_E_TSAP, msg, domain="deploy", detail={"get_app": app})
        log(f"activate confirmed: slot={result['active_slot']}")
        return result
    finally:
        if lease_acquired:
            try:
                _cmd_ok(svc, node, cube, "lease-release", rid(f"lr{renew_n}"),
                        holder=holder, idem=idem(f"lr{renew_n}"))
                result["released"] = True
                log("lease released")
            except TaError as exc:
                result["released"] = False
                result["release_error"] = exc.to_payload()
                log(f"WARN lease release 失败（TTL 兜底失权）: {exc.message}")
