# SPDX-License-Identifier: Apache-2.0
"""deploy_* 实现（LLD-agent-deploy-net §3）：发现 / 状态 / TSAP 包分块推送。

push_app 纪律（全部硬点，工具内强制）：
  ① tsap_verify 复验不可跳过（链外直调同样强制）；
  ② 租约闭环（DEC-41）：acquire → 周期续期 → 结束 release（失败也 release）；
  ③ 分块 2KB 默认（上限 4KB，NeuroLink 实证档位）+ 每块 idem（重试安全，DEC-40）；
  ④ 分步对齐固件安装链：upload → verify（容器事实对拍）→ activate → get-app
     确认（版本回读一致才置 confirmed）。
同步实现（zenoh 会话经 ZenohService 工作线程）；网关侧 asyncio 用 to_thread 包装。
"""

from __future__ import annotations

import hashlib
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

# 来源: LLD-agent-deploy-net §3（2KB 默认 / 4KB 上限）
CHUNK_DEFAULT = 2048
CHUNK_MAX = 4096
TS_E_PENDING = -13  # 固件 err.h（F3 · DEC-62①）：安装闸结构化中间态
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
    # 偶发空回执重试（K3 真机实证：同进程内 status 通/trust-get 空的组合
    # 竞态、隔离复测同 query 恒 44B 正常回执——PC 侧会话竞态域，重试即过；
    # 仅空载荷重试 3 次，间隔 0.5s）。
    #
    # 超时跨自愈窗重试 ×2（R5-V · DEC-65；R2 族）：部署突发可触发板侧 TCP
    # 单向僵（上游 Zephyr 原生 TCP 乱序域），板侧自愈 = **glue session_poll
    # 重连**（pico AUTO_RECONNECT=0 仓钉版——F7 破案；is_up 三判据判死
    # 〔LLD-ts-net v0.4.7〕→ 租期判死 10s + 退避 + 重握手，真机 ≤~26s，
    # 证据 r5v_zombie_heal_console.txt）——单次 10s 查询恰落在自愈窗内
    # 超时 = 部署误败。Timeout 类回执间隔 8s 重试 2 次（verify 幂等安全；
    # activate 重试落 E_BUSY 可见不腐蚀）。其余语义不变。
    payload = b""
    timeout_retries = 2
    for _ in range(5):
        try:
            _, payload = svc.query_one(keys.key_sys(node, cube, op),
                                       keys.envelope(op, rid, **env))
        except TaError as e:
            if timeout_retries > 0 and (e.retryable or "Timeout" in str(e)):
                timeout_retries -= 1
                time.sleep(8.0)
                continue
            raise
        if payload:
            break
        time.sleep(0.5)
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
    app: int = 1,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """TSAP 包分块推送 + 分步安装（严格类语义由网关审批层承载）。

    app = 目标实例 app_id（1..N，Q-32⑤/V0.4.0 M7b）——多 APP 板部署位选择；
    缺省 1 = 单实例语义（旧调用方零改动）。"""
    log = log_fn or (lambda s: None)
    if not 1 <= app <= 4:
        msg = f"app 越界 [1,4]: {app}"
        raise TaError(TA_E_ARGS, msg, domain="deploy")
    if not (1 <= chunk_size <= CHUNK_MAX):
        msg = f"chunk_size 越界 [1,{CHUNK_MAX}]: {chunk_size}"
        raise TaError(TA_E_ARGS, msg, domain="deploy")

    # ① tsap_verify 强制复验（不可跳过——工具内实现，链外直调同样强制）
    verify = tsap_tools.tsap_verify(package_path, pub_key_path)
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
        # TSAP v2 布局（DEC-49②）：头 16 + 摘要 32 → 内容区 = 48（D8 真机
        # 对拍拦下的存量缺陷——本行原为 v1 布局 16+ml+wl，网络链自板级十
        # 后未跑、单元 D v2 迁移漏改此面）。
        "cose_off": tsap_tools.TSAP_CONTENT_OFF + mlen + wlen,
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
        # ①b 设备能力预检（CG5-A · Q-39④：caps 消费——装前匹配前置到
        # 部署会话，免整包上传后才被安装期矩阵拒；caps 缺失 = 旧固件 →
        # 跳过（新固件安装期矩阵仍兜底）。get-info 只读豁免租约。
        info = _cmd_ok(svc, node, cube, "get-info", rid("cap"))
        caps = info.get("caps") or {}
        tiers = caps.get("tiers") or []
        manifest = verify.get("manifest") or {}
        tier = str(manifest.get("tier") or "small")
        if tiers and tier not in tiers:
            msg = f"设备档位不支持 tier={tier}（caps.tiers={tiers}）"
            raise TaError(TA_E_POLICY, msg, domain="deploy",
                          detail={"tier": tier, "caps": caps})
        lin = (manifest.get("needs") or {}).get("linear_memory_kb")
        cap_lin = caps.get("max_linear_memory_kb")
        if lin is not None and cap_lin is not None and int(lin) > int(cap_lin):
            msg = f"线性内存申报 {lin}KB 超设备帽 {cap_lin}KB"
            raise TaError(TA_E_POLICY, msg, domain="deploy",
                          detail={"linear_memory_kb": lin,
                                  "max_linear_memory_kb": cap_lin})
        result["device_caps"] = caps or "legacy-fw"

        # ② 租约闭环：acquire（续期幂等——同 holder re-acquire）
        renew(force=True)
        lease_acquired = True
        log(f"lease acquired: id={result['lease_id']} holder={holder}")

        # ③ upload：begin → 分块（每块 idem + 超时重试；重发安全）
        data = _cmd_ok(svc, node, cube, "app-begin", rid("begin"),
                       total=len(pkg), idem=idem("begin"), app=app)
        result["slot"] = data.get("slot")
        log(f"upload → slot {result['slot']}（total={len(pkg)}B）")
        sent = 0
        for off in range(0, len(pkg), chunk_size):
            piece = pkg[off:off + chunk_size]

            def send(o: int = off, p: bytes = piece) -> dict:
                try:
                    return _cmd_ok(svc, node, cube, "app-chunk", rid(f"c{o}"),
                                   offset=o, data=p, idem=idem(f"c{o}"))
                except CmdError as exc:
                    # 租约瞬断自愈（BV1 板级专项 2026-10-19）：板侧执行器
                    # 高压停顿（wifi TX 拥塞窗）> 租约 TTL 时懒过期拒绝
                    # chunk——force renew 后同 idem 重发（幂等安全）。非租约
                    # 类拒绝原样上抛。
                    if "lease required" in str(exc.reply_data):
                        log("lease 瞬断（板侧高压停顿懒过期）——force renew "
                            "后同 idem 重发")
                        renew(force=True)
                        return _cmd_ok(svc, node, cube, "app-chunk",
                                       rid(f"c{o}"), offset=o, data=p,
                                       idem=idem(f"c{o}"))
                    raise

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

        # ⑤ activate → get-app 确认（版本回读一致才置 confirmed）。
        # F3 · DEC-62① 安装闸：prov lconf=1 的板 activate 返回 -13 结构化
        # 中间态 {pending, slot}——部署按「待板上本地确认」收尾（确认仅
        # 固件本地路：短按 BOOT=确认/长按≥2s=拒绝；60s fail-closed 超时
        # 撤销后可重推）。EC3 双路同数据面：本侧呈报 = install_permission_brief。
        act_raw = _cmd(svc, node, cube, "app-activate", rid("activate"),
                       idem=idem("activate"), app=app)
        if act_raw.status == TS_E_PENDING:
            pend = act_raw.data or {}
            result["pending_local_confirm"] = True
            result["pending_slot"] = int(pend.get("slot", -1))
            result["app_id_target"] = app
            log(f"activate PENDING slot={result['pending_slot']}: "
                "待板上本地确认（短按=确认/长按≥2s=拒绝，60s fail-closed）")
            return result
        if act_raw.status != 0:
            raise CmdError("app-activate", act_raw)
        act = act_raw.data
        result["active_slot"] = act.get("active_slot")
        result["app_id_target"] = app
        app_view = _cmd_ok(svc, node, cube, "get-app", rid("getapp"), app=app)
        result["app"] = app_view
        result["confirmed"] = (
            int(app_view.get("active_slot", -1)) == int(result["active_slot"]))
        if not result["confirmed"]:
            msg = (f"确认回读不一致: activate slot={result['active_slot']} "
                   f"get-app={app_view}")
            raise TaError(TA_E_TSAP, msg, domain="deploy",
                          detail={"get_app": app_view})
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


def post_deploy_check(
    svc: ZenohService,
    node: str,
    cube: str,
    *,
    serial_port: str | None = None,
    window_s: float = 8.0,
    app_id_expect: str | None = None,
    pass_patterns: list[str] | None = None,
    reset_before_capture: bool = False,
) -> dict[str, Any]:
    """部署后健康检查 + 失败自动诊断（G 批 D3 · CLI 调研批候选③；
    P1-5 S8 增判据面）。

    健康判定 = get-app state==ACTIVE（可选 app_id 精确比对）。健康 →
    {healthy: true, get-app:…}；非健康 → 若给出 serial_port 则被动窗口
    抓取（capture_window——不复位；开埠脉动仅失败路径可接受）+
    classify_run 自动分类，回执携带 category/repair_hint/evidence——
    调用方（MCP 部署面/创作循环）直接回喂 LLM，免人工逐工具诊断。
    无串口配置 → 仅结构化不健康快照（分类留调用方）。

    P1-5（HLD-agent §4 S8）：给出 pass_patterns 时**判据面升级**——
    即使 get-app 健康也抓窗对拍判据行（bench 契约：判据行出现即达成）；
    回执增 {criteria_pass, pass_patterns}；判据 miss = criteria_pass
    False + diag（S8 修复轮回喂证据）。抓取失败 = criteria_pass None
    （不掩蔽主判定——如实区分「未验证」与「未命中」）。

    FIX-2 增 reset_before_capture（BV1 C6 暖复位语义专用）：True =
    复用 reset_and_capture（单端口会话内 RTS 复位 + 抓取）——C6 原
    「_serial_reset 关口 → capture_window 再开」两段式在 CH343 快速
    关/开竞态下窗口零字节（no_verdict 假 FAIL，真机实测复现）。缺省
    False = 既有调用方（S8 修复轮/CLI 部署后判据）行为逐字节不变。
    """
    g = _cmd_ok(svc, node, cube, "get-app", f"pc-{cube}")
    healthy = int(g.get("state", -1)) == 3 and (
        app_id_expect is None or g.get("app_id", "") == app_id_expect)
    out: dict[str, Any] = {"healthy": healthy, "get-app": g}
    need_capture = serial_port is not None and (
        not healthy or (pass_patterns is not None and len(pass_patterns) > 0))
    if not need_capture:
        if pass_patterns is not None:
            out["criteria_pass"] = None  # 无串口/无判据窗 = 未验证（≠ 未命中）
            out["pass_patterns"] = pass_patterns
        return out
    from tessera_agent.tools_diag import capture as diag_capture
    from tessera_agent.tools_diag import classify as diag_cls

    try:
        if reset_before_capture:
            text = diag_capture.reset_and_capture(serial_port, window_s)
        else:
            text = diag_capture.capture_window(serial_port, window_s)
    except Exception as exc:  # noqa: BLE001 —— 抓取失败不掩蔽主判定
        out["diag_error"] = f"{type(exc).__name__}: {exc}"
        if pass_patterns is not None:
            out["criteria_pass"] = None  # 未验证（≠ 未命中）
            out["pass_patterns"] = pass_patterns
        return out
    r = diag_cls.classify_run(text,
                              pass_patterns=pass_patterns or [])
    out["diag"] = {"category": r.category, "summary": r.summary,
                   "repair_hint": r.repair_hint, "evidence": r.evidence}
    # HW-4 ④⑤（LLD-agent-hardware-targeting §7.4/§7.5）：硬件写拒扫描 + 判据硬件感知——判据行
    # 命中但窗内存在 `<TOKEN> WRITE REJECTED` = soft-pass/hard-invalid，
    # criteria_pass 降级 False（物理动作未发生，日志行是假象）；扫描结果
    # 随回执进修复轮证据链（S8 criteria_pass=False → repair 零改动消费）。
    from tessera_agent.tools_diag.classify import scan_hardware_rejections
    rejections = scan_hardware_rejections(text)
    out["hardware"] = {"rejections": rejections}
    if pass_patterns is not None:
        matched = r.category == "pass"
        if matched and rejections:
            toks = ", ".join(f"{x['token']}×{x['count']}"
                             for x in rejections)
            out["diag"]["repair_hint"] = (
                "硬件写被拒（" + toks + "）——判据行为日志假象，物理动作"
                "未发生；请核对申请通道与目标板卡物理绑定（画像 [hardware]"
                " 事实节），改用有绑定的通道或修订 caps 后重新生成")
            out["diag"]["evidence"] = list(out["diag"]["evidence"]) + [
                x["first_line"] for x in rejections[:5]]
            out["criteria_pass"] = False
        else:
            out["criteria_pass"] = matched
        out["pass_patterns"] = pass_patterns
    return out


def push_resources(
    svc: ZenohService,
    node: str,
    cube: str,
    files: dict[str, bytes],
    *,
    app: int = 1,
    holder: str = keys.DEFAULT_SRC,
    chunk_size: int = CHUNK_DEFAULT,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """部署会话资源推送（CG5-B · Q-39③ 方案 A——HLD-contract-v2 §6）。

    授权 = 目标 entry 激活包 needs.resources 前缀白名单（固件 activate/boot
    绑定）+ 租约（gated）；完整性 = 每文件 sha256 随 fs-begin 携带、固件
    全量读回校验（verified 回执）——失配固件侧自删（fail-closed）。
    files = {设备绝对路径: 内容字节}；推送序按路径排序（确定性）。
    app = 目标实例（与 push_app 部署位一致）。"""
    log = log_fn or (lambda m: None)
    if not files:
        raise TaError(TA_E_ARGS, "files 为空", domain="deploy")
    if not 1 <= app <= 4:
        raise TaError(TA_E_ARGS, f"app 越界 [1,4]: {app}", domain="deploy")
    for p in files:
        if not p.startswith("/") or ".." in p:
            msg = f"资源路径非法（须绝对路径禁 ..）: {p!r}"
            raise TaError(TA_E_ARGS, msg, domain="deploy")

    d = secrets.token_hex(3)

    def rid(tag: str) -> str:
        return f"{d}-fs{tag}"[: keys.RID_MAX]

    result: dict[str, Any] = {"app": app, "files": []}
    lease_acquired = False
    try:
        # 租约先行（fs-begin 门控；跨多文件会话持续续期）
        _cmd_ok(svc, node, cube, "lease-acquire", rid("la"), holder=holder)
        lease_acquired = True
        log(f"lease acquired: holder={holder}")

        for path, data in sorted(files.items()):
            sha = hashlib.sha256(data).digest()
            r = _cmd_ok(svc, node, cube, "fs-begin", rid("b"), app=app,
                        path=path, total=len(data), sha256=sha, holder=holder)
            log(f"fs-begin: {path} ({len(data)}B staged={r.get('staged')})")
            for off in range(0, len(data), chunk_size):
                _retry(
                    lambda o=off, d=data: _cmd_ok(  # 默认参绑定循环变量（B023）
                        svc, node, cube, "fs-chunk", rid("c"), app=app,
                        offset=o, data=d[o:o + chunk_size], holder=holder),
                    retries=CHUNK_RETRY_MAX, log=log)
            _cmd_ok(svc, node, cube, "lease-acquire", rid("lr"), holder=holder)
            c = _cmd_ok(svc, node, cube, "fs-commit", rid("m"), app=app,
                        holder=holder)
            if c.get("verified") is not True:
                msg = f"资源完整性校验未过: {path}（回执 {c}）"
                raise TaError(TA_E_TSAP, msg, domain="deploy",
                              detail={"path": path, "reply": c})
            result["files"].append({"path": path, "bytes": len(data)})
            log(f"fs-commit verified: {path}")
        return result
    finally:
        if lease_acquired:
            try:
                _cmd_ok(svc, node, cube, "lease-release", rid("lx"),
                        holder=holder)
            except TaError as exc:
                log(f"WARN lease release 失败（TTL 兜底失权）: {exc.message}")


def trust_get(svc: ZenohService, node: str, cube: str) -> dict[str, Any]:
    """信任根表读取（V0.8.0 EC2 · Q-43⑤/DEC-60④；LLD-agent-deploy-net §3）。

    返回 {ver, keys: [bytes×n]}（公钥 = 公开材料——未门控命令）。
    旧固件/未使能 TS_STORE_TRUST 设备 = op 未知拒 → CmdError 如实上抛
    （调用方可据此判定设备信任表能力）。"""
    r = _cmd_ok(svc, node, cube, "trust-get", "trust-get")
    ver = r.get("ver")
    ks = r.get("keys")
    if not isinstance(ver, int) or not isinstance(ks, list):
        msg = f"trust-get 回执形态非法: {r}"
        raise TaError(TA_E_POLICY, msg, domain="deploy", detail={"reply": r})
    return {"ver": ver, "keys": [bytes(k) for k in ks]}


def _trust_table_cbor(ver: int, dev_keys: list[bytes]) -> bytes:
    """表 CBOR（固件定稿键序 map{"ver":uint,"keys":[bstr(32)]}——与
    ts_trust.c trust_walk 字节级同构；手工构造非 canonical 排序）。"""
    if not 1 <= ver <= 23 or len(dev_keys) > 8:
        msg = f"信任表参数越界（ver∈[1,23]，键≤8）: ver={ver} n={len(dev_keys)}"
        raise TaError(TA_E_ARGS, msg, domain="deploy")
    seen: set[bytes] = set()
    for k in dev_keys:
        if not isinstance(k, (bytes, bytearray)) or len(k) != 32:
            msg = f"开发者公钥须 raw 32B: {type(k).__name__}/{len(k)}"
            raise TaError(TA_E_ARGS, msg, domain="deploy")
        if bytes(k) in seen:
            msg = "开发者键重复（全量替换语义下生成侧错误）"
            raise TaError(TA_E_ARGS, msg, domain="deploy")
        seen.add(bytes(k))
    out = bytes([0xA2]) + b"\x63ver" + bytes([ver]) + b"\x64keys"
    out += bytes([0x80 | len(dev_keys)])
    for k in dev_keys:
        out += b"\x58\x20" + bytes(k)
    return out


def trust_update(
    svc: ZenohService,
    node: str,
    cube: str,
    dev_keys: list[bytes],
    signer_key_path: str,
    *,
    holder: str = keys.DEFAULT_SRC,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """信任根表更新（V0.8.0 EC2；TUF root 同型全量替换——撤销 = 次版剔除）。

    dev_keys = 更新后的**完整**开发者公钥集（≤8；空表合法 = 全撤回工厂根
    单源）。signer_key_path = **现有效集内任一私钥**（首次注册 = 工厂根
    pk0 对应方；互荐 = 既有开发者键）。流程：trust-get 读现表 → 组次版
    （ver+1）→ COSE_Sign1 签名（cose.sign_diy——与 TSAP 同构）→ 租约 +
    sys/trust-update 单发（表 ≤270B + COSE ≈350B < 单块上限——免分块）。
    失败如实上抛：TS_E_RANGE（ver 非当前+1——并发更新，重读重试）、
    TS_E_INVALID_SIG（签名键不在有效集）。私钥仓外纪律（DR-22 同源）。"""
    log = log_fn or (lambda m: None)
    sk = Path(signer_key_path).expanduser().read_bytes()
    if len(sk) != 32:
        msg = f"签名私钥格式非法（须 ed25519 raw 32B）: {signer_key_path}"
        raise TaError(TA_E_ARGS, msg, domain="deploy")

    cur = trust_get(svc, node, cube)
    payload = _trust_table_cbor(cur["ver"] + 1, dev_keys)

    from tessera_agent.tools_tsap.cose import sign_diy

    blob = sign_diy(payload, sk)
    log(f"trust table v{cur['ver']}→{cur['ver'] + 1} keys={len(dev_keys)} "
        f"blob={len(blob)}B")

    d = secrets.token_hex(3)
    lease_acquired = False
    try:
        _cmd_ok(svc, node, cube, "lease-acquire", f"{d}-ta"[:keys.RID_MAX],
                holder=holder)
        lease_acquired = True
        r = _cmd_ok(svc, node, cube, "trust-update", f"{d}-tu"[:keys.RID_MAX],
                    data=blob, holder=holder)
        if r.get("ver") != cur["ver"] + 1:
            msg = f"trust-update 回执版本异常: {r}"
            raise TaError(TA_E_TSAP, msg, domain="deploy", detail={"reply": r})
        result = {"ver": r["ver"], "keys": len(dev_keys),
                  "prev_ver": cur["ver"]}
        log(f"trust table updated: v{result['ver']} keys={len(dev_keys)}")
        return result
    finally:
        if lease_acquired:
            try:
                _cmd_ok(svc, node, cube, "lease-release",
                        f"{d}-tx"[:keys.RID_MAX], holder=holder)
            except TaError as exc:
                log(f"WARN lease release 失败（TTL 兜底失权）: {exc.message}")


def push_prov(
    svc: ZenohService,
    node: str,
    cube: str,
    cbor: bytes,
    *,
    holder: str = keys.DEFAULT_SRC,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """远程 prov 维护通道（V0.4.0 M10，Q-34/DEC-53；LLD-agent-deploy-net §6 例外收口）。

    lease 门控 + confirm="prov" 硬令牌 + 固件侧写前全量 schema 校验 +
    per-boot 一次性窗（再写须复位循环）。生效 = 下次复位（返回 applies
    ="next-reboot"——调用方按需复位板）。cbor = prov CBOR v1/v2 schema 字节
    （gen 脚本/迁移工具产出；本函数不构造内容——CG2 起固件双形态收）。"""
    log = log_fn or (lambda s: None)
    if not cbor:
        msg = "prov cbor 为空"
        raise TaError(TA_E_ARGS, msg, domain="deploy")
    if len(cbor) > 3800:
        msg = f"prov cbor 超上限 3800: {len(cbor)}"
        raise TaError(TA_E_ARGS, msg, domain="deploy")

    lease_acquired = False
    result: dict[str, Any] = {}
    n = [0]

    def rid(tag: str) -> str:
        n[0] += 1
        return f"prov-{tag}-{n[0]:03d}"

    try:
        acq = _cmd_ok(svc, node, cube, "lease-acquire", rid("pacq"),
                      holder=holder)
        lease_acquired = True
        result["lease_id"] = acq.get("lease_id")
        log(f"lease acquired: id={acq.get('lease_id')} holder={holder}")

        r = _cmd_ok(svc, node, cube, "prov-write", rid("pw"),
                    confirm="prov", data=cbor, holder=holder)
        result["written"] = r.get("written")
        result["applies"] = r.get("applies", "next-reboot")
        log(f"prov written={result['written']}（生效 = 下次复位）")
        return result
    finally:
        if lease_acquired:
            try:
                _cmd_ok(svc, node, cube, "lease-release", rid("prel"),
                        holder=holder)
                result["released"] = True
                log("lease released")
            except TaError as exc:
                result["released"] = False
                result["release_error"] = exc.to_payload()
                log(f"WARN lease release 失败（TTL 兜底失权）: {exc.message}")
