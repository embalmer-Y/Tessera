# SPDX-License-Identifier: Apache-2.0
"""固件域 DomainPack（LLD-A07 §3；DEC-33 多域预留的首个实现）。

域工具面：fw_*（A03）/ sim_*（A04）/ tsap_*（A05）/ deploy_*（A06）/
app_*（DEC-34 高层链）。组合根（gateway/compose.py）显式注册本包；
平台层（platform.py）不感知本模块。
"""

from __future__ import annotations

import asyncio
import secrets
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cbor2

from tessera_agent.common.errors import TA_E_ARGS, TA_E_TSAP, TaError
from tessera_agent.core.session import PolicyTable
from tessera_agent.domain import app_chain
from tessera_agent.domain import board_validation as bv
from tessera_agent.domain import memory_audit as ma
from tessera_agent.platform import AppContext, DomainPackBase, MountAPI
from tessera_agent.tools_diag import classify as diag_cls
from tessera_agent.tools_diag import simreal_diff as diag_sr
from tessera_agent.tools_diag import spec_gate as diag_spec_gate
from tessera_agent.tools_fw import tools as fw
from tessera_agent.tools_net import deploy as net_deploy
from tessera_agent.tools_net.zenoh_service import ZenohService
from tessera_agent.tools_sim import runner as sim_runner
from tessera_agent.tools_sim.scenario import scenario_validate
from tessera_agent.tools_tsap import tools as tsap_tools
from tessera_agent.tools_tsap.manifest import TsapManifest
from tessera_agent.tools_tsap.wasm_build import compile_app_c


@dataclass
class FirmwareDeployer:
    """域部署器（LLD-A07 §3 deployer；V1 = deploy.push_app 包装）。"""

    router_locator: str = "tcp/127.0.0.1:7447"

    def deploy(self, ctx: AppContext, node: str, cube: str, package_path: str,
               pub_key_path: str, log_fn=None) -> dict:
        with ZenohService(self.router_locator) as svc:
            return net_deploy.push_app(svc, node, cube, package_path, pub_key_path,
                                       log_fn=log_fn)


def install_permission_brief(package_path: str) -> str:
    """安装期权限呈报（V0.8.0 EC3 · Q-40③/DEC-60③——无头设备路）。

    strict 审批请求 reason 携带包声明权限面（manifest 摘要——工具内
    强制，不可跳过；坏包在审批前拦截）。有本地交互设备的本地确认路
    随设备形态批（LLD-A02 §3.2 注记——同型数据面）。"""
    s = tsap_tools.manifest_summary(package_path)
    caps = ",".join(s["caps"]) or "∅"
    fs = ";".join(s["fs_paths"] or []) or "∅"
    res = ";".join(s["needs"].get("resources", [])) or "∅"
    return (f"APP {s['app_id']} v{s['app_ver']} tier={s['tier']} "
            f"caps=[{caps}] fs_paths=[{fs}] needs.resources=[{res}] "
            f"threads={s['threads']} wasm={s['wasm_bytes']}B")


def validate_tsap_manifest(package_path: str) -> None:
    """产物校验器：TSAP 容器 manifest 段结构校验（TsapManifest v1）。"""
    p = Path(package_path)
    if not p.is_file():
        msg = f"产物不存在: {package_path}"
        raise TaError(TA_E_TSAP, msg, domain="validator")
    data = p.read_bytes()
    if len(data) < 16:
        msg = f"容器过短: {len(data)}B"
        raise TaError(TA_E_TSAP, msg, domain="validator")
    magic, ver, mlen, _wlen, _rsv = struct.unpack(">IHIIH", data[:16])
    if magic != tsap_tools.TSAP_MAGIC or ver != tsap_tools.TSAP_FMT_VER:
        msg = "容器头非法（magic/版本）"
        raise TaError(TA_E_TSAP, msg, domain="validator")
    try:
        m = cbor2.loads(data[16:16 + mlen])
        TsapManifest(**{k: v for k, v in m.items()})
    except Exception as exc:  # noqa: BLE001
        msg = f"manifest 校验失败: {exc}"
        raise TaError(TA_E_TSAP, msg, domain="validator") from exc


@dataclass
class FirmwareDomainPack(DomainPackBase):
    name: str = "firmware"
    tools: list[str] = field(default_factory=lambda: [
        "fw_workspace_status", "fw_build", "fw_twister", "fw_pytest",
        "sim_validate_scenario", "sim_run",
        "tsap_keygen", "tsap_package", "tsap_verify",
        "deploy_discover", "deploy_status", "deploy_push_app", "deploy_push_prov",
        "ln_create", "ln_list", "ln_remove", "ln_status", "ln_deploy",
        "ln_estop_clear",
        "app_develop", "app_deploy", "app_compile",
        "board_validate", "memory_audit",
        "diag_classify", "spec_check", "simreal_diff",
    ])
    skills: list[str] = field(default_factory=lambda: [
        "tessera-workflow", "tessera-build", "tessera-tsap", "tessera-safety",
    ])
    policy: PolicyTable = field(default_factory=lambda: PolicyTable(entries={
        # 审批类别声明（只可收紧；HLD §5.1）
        "tsap_keygen": "strict",
        "deploy_push_app": "strict",
        "deploy_push_prov": "strict",
        "ln_deploy": "strict",  # DEC-54①：组部署 = N 成员写操作

        "app_develop": "confirm",
        "app_deploy": "strict",
        "board_validate": "strict",  # V0.13.0 BV1：复位+部署冒烟=板态写入
        "memory_audit": "confirm",   # V0.13.0 MP：本地只读分析（LLD-A13）
        "diag_classify": "confirm",
        "spec_check": "confirm",
        "simreal_diff": "confirm",
    }))
    validators: list = field(default_factory=lambda: [validate_tsap_manifest])
    deployer: Any = field(default_factory=lambda: None)  # 组合根注入 router 配置

    async def info_extras(self, ctx: AppContext) -> dict[str, Any]:
        boards_dir = Path(ctx.cfg.workspace_repo) / "agent" / "boards"
        return {"workspace": await fw.fw_workspace_status(ctx.cfg, ctx.budget),
                "tools": self.tools,
                "board_validation": {"profiles": bv.list_profiles(boards_dir),
                                     "checks": list(bv.CHECK_ORDER)}}

    def mount(self, api: MountAPI) -> None:
        ctx, audited, spawn = api.ctx, api.audited, api.spawn
        mcp = api.mcp

        # ---- fw_*（confirm 类，V1 会话内直行——策略经 config 收紧，DEC-38 #7）
        @mcp.tool
        @audited("fw_workspace_status")
        async def fw_workspace_status() -> dict:
            """固件工作区状态：分支/提交/dirty/测试清单。"""
            return (await fw.fw_workspace_status(ctx.cfg, ctx.budget))

        @mcp.tool
        @audited("fw_build")
        async def fw_build(board: str, extra_args: list[str] | None = None) -> dict:
            """构建固件（west build；长任务，立即返回句柄，经 task_status 轮询）。"""
            args = {"board": board, "extra_args": extra_args or []}
            task_id = f"fwbuild-{secrets.token_hex(4)}"

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                return await fw.fw_build(
                    ctx.cfg, ctx.budget, board=board, extra_args=extra_args,
                    task_id=task_id, log_fn=log,
                )

            return await spawn("fw_build", args, body)

        @mcp.tool
        @audited("fw_twister")
        async def fw_twister(platform: str, extra_args: list[str] | None = None) -> dict:
            """运行 twister 测试（长任务，返回句柄）。"""
            args = {"platform": platform, "extra_args": extra_args or []}
            task_id = f"fwtw-{secrets.token_hex(4)}"

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                return await fw.fw_twister(
                    ctx.cfg, ctx.budget, platform=platform, extra_args=extra_args,
                    task_id=task_id, log_fn=log,
                )

            return await spawn("fw_twister", args, body)

        @mcp.tool
        @audited("fw_pytest")
        async def fw_pytest(scope: str = "firmware/tests/pytest") -> dict:
            """运行仓库 pytest（长任务，返回句柄）。"""
            args = {"scope": scope}

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                return await fw.fw_pytest(ctx.cfg, ctx.budget, scope=scope, log_fn=log)

            return await spawn("fw_pytest", args, body)

        # ---- sim_*（MA2，LLD-A04；G5/单元 H 输入文件实装）--------------------
        @mcp.tool
        @audited("sim_validate_scenario")
        async def sim_validate_scenario(scenario: dict) -> dict:
            """校验仿真场景 schema v1（inputs 升序/op 合法等）；返回错误清单（空=合法）。

            inputs.ch 命名空间："link"(值 0|1) / "estop"(值忽略) /
            "in:0"|"in:1"(ADC 注入 mv；首拍建基线无回显) / "rep_c"|"rep_d"(输出
            通道直驱，slew 5/ms 限幅 0..1000)。expectations.ch 同域（输入回显
            = "in:N" 通道）。"""
            return {"errors": scenario_validate(scenario)}

        @mcp.tool
        @audited("sim_run")
        async def sim_run(scenario: dict,
                          verdict_patterns: list[str] | None = None) -> dict:
            """运行确定性重放仿真（inputs 落 replay_script.tsv 驱动固件脚本会话；
            双跑比对 + 期望评估；长任务句柄）。期望值按规格推导（slew/限幅数学），
            禁"跑一遍拿输出当基准"；ch 命名空间见 sim_validate_scenario。
            verdict_patterns（V2-3 可选）= 判据行子串——命中行按序归一化
            提取进 report.verdict_lines（sim APP 装载面的判据行，供
            simreal_diff 首基线对拍消费）。"""
            args = {"scenario": scenario,
                    "verdict_patterns": verdict_patterns}
            task_id = f"simrun-{secrets.token_hex(4)}"

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                return await sim_runner.sim_run(
                    ctx.cfg, scenario, task_id=task_id,
                    verdict_patterns=verdict_patterns, log_fn=log)

            return await spawn("sim_run", args, body)

        # ---- tsap_*（MA2，LLD-A05；无签名不产出——硬点）----------------------
        @mcp.tool
        @audited("tsap_keygen")
        async def tsap_keygen(name: str, out_dir: str = "agent/keys") -> dict:
            """生成 ed25519 开发密钥对（strict 类：挂起宿主审批，超时自动拒绝；
            长任务句柄——轮询 task_status 至 input_required，经 sys_pending_approvals/
            sys_approve 决；私钥 0600 落盘，不回显/不入审计）。"""
            args = {"name": name, "out_dir": out_dir}

            async def body(task) -> dict:
                approval = ctx.approvals.request(
                    "tsap_keygen",
                    {"name": name, "out_dir": out_dir},
                    reason="strict 类：生成签名密钥材料（HLD §5.1）",
                )
                task.state = "input_required"
                try:
                    await ctx.approvals.wait(approval)
                finally:
                    task.state = "working"
                return tsap_tools.tsap_keygen(name, out_dir, ctx.roots())

            return await spawn("tsap_keygen", args, body)

        @mcp.tool
        @audited("tsap_package")
        async def tsap_package(wasm_path: str, manifest: dict, key_path: str,
                               out_dir: str = "agent/build") -> dict:
            """TSAP 打包签名（canonical CBOR + COSE_Sign1 双实现互验；长任务句柄）。"""
            args = {"wasm_path": wasm_path, "manifest": manifest, "key_path": key_path}

            async def body(task) -> dict:
                return tsap_tools.tsap_package(wasm_path, manifest, key_path, out_dir,
                                               ctx.roots())

            return await spawn("tsap_package", args, body)

        @mcp.tool
        @audited("tsap_verify")
        async def tsap_verify(package_path: str, pub_key_path: str) -> dict:
            """TSAP 包全量反向验证（容器头 + COSE 双实现 + manifest 解码）。"""
            # IR2-03：包路径读面白名单（ctx.roots）
            return tsap_tools.tsap_verify(package_path, pub_key_path, ctx.roots())

        # ---- deploy_*（MA3.1，LLD-A06；同步 zenoh 面经 to_thread 桥接）------
        @mcp.tool
        @audited("deploy_discover")
        async def deploy_discover(timeout_s: float = 10.0) -> dict:
            """发现 router 侧在线 cube（通配 query get-info；超时默认 10s，DEC-38 #4）。"""
            def work() -> dict:
                with ZenohService(ctx.cfg.router_locator, query_timeout_s=timeout_s) as svc:
                    return {"cubes": net_deploy.discover(svc, timeout_s=timeout_s)}

            return await asyncio.to_thread(work)

        @mcp.tool
        @audited("deploy_status")
        async def deploy_status(node: str, cube: str) -> dict:
            """组合快照：get-info/get-link/get-safety/get-app（部署前核验依据）。"""
            def work() -> dict:
                with ZenohService(ctx.cfg.router_locator) as svc:
                    return net_deploy.status(svc, node, cube)

            return await asyncio.to_thread(work)

        @mcp.tool
        @audited("ln_create")
        async def ln_create(ln_id: str, members: list[dict],
                            linkloss_policy: str = "continue") -> dict:
            """创建逻辑节点（V0.4.x M16/DEC-54① 方案 A——Agent 侧编排）。

            members = [{"node": ..., "cube": ...}, ...]（≥1）；linkloss_policy
            ∈ continue|pause（降级策略语义提示）。注册表 = server 生存期内存态。"""
            def work() -> dict:
                from tessera_agent.tools_net.lno import REGISTRY
                ln = REGISTRY.create(
                    ln_id, [(m["node"], m["cube"]) for m in members],
                    linkloss_policy=linkloss_policy)
                return {"ln_id": ln.ln_id, "members": len(ln.members),
                        "linkloss_policy": ln.linkloss_policy}

            return await asyncio.to_thread(work)

        @mcp.tool
        @audited("ln_list")
        async def ln_list() -> dict:
            """列出全部逻辑节点（成员拓扑 + 策略）。"""
            def work() -> dict:
                from tessera_agent.tools_net.lno import REGISTRY
                return {"nodes": REGISTRY.list()}

            return await asyncio.to_thread(work)

        @mcp.tool
        @audited("ln_remove")
        async def ln_remove(ln_id: str) -> dict:
            """移除逻辑节点注册（不动成员 cube 状态）。"""
            def work() -> dict:
                from tessera_agent.tools_net.lno import REGISTRY
                REGISTRY.remove(ln_id)
                return {"removed": ln_id}

            return await asyncio.to_thread(work)

        @mcp.tool
        @audited("ln_status")
        async def ln_status(ln_id: str) -> dict:
            """组状态聚合：逐成员四合一快照 + linkloss 降级视图。"""
            def work() -> dict:
                from tessera_agent.tools_net import lno
                with ZenohService(ctx.cfg.router_locator) as svc:
                    return lno.ln_status(lno.REGISTRY, svc, ln_id)

            return await asyncio.to_thread(work)

        @mcp.tool
        @audited("ln_deploy")
        async def ln_deploy(ln_id: str, package_path: str, pub_key_path: str,
                            app: int = 1) -> dict:
            """组部署（strict：挂起宿主审批）：顺序扇出至全部成员。

            **非原子**（DEC-54① 如实）：失败成员不阻断后续；聚合视图逐成员
            标注 deployed/failed。app = 实例位（多 APP 板，缺省 1）。"""
            args = {"ln_id": ln_id, "package_path": package_path,
                    "pub_key_path": pub_key_path, "app": app}

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                # EC3（Q-40③）：审批请求携带包权限面（坏包审批前拦截）
                brief = install_permission_brief(package_path)
                log(f"install permissions: {brief}")
                approval = ctx.approvals.request(
                    "ln_deploy", args,
                    reason=f"strict 类：组部署（N 成员远程安装 APP）｜{brief}",
                )
                task.state = "input_required"
                try:
                    await ctx.approvals.wait(approval)
                finally:
                    task.state = "working"

                def work() -> dict:
                    from tessera_agent.tools_net import lno
                    with ZenohService(ctx.cfg.router_locator) as svc:
                        return lno.ln_deploy(lno.REGISTRY, svc, ln_id,
                                             package_path, pub_key_path,
                                             app=app, log_fn=log)

                return await asyncio.to_thread(work)

            return await ctx.registry.start(
                "ln_deploy", args, body, budget=ctx.budget)

        @mcp.tool
        @audited("ln_estop_clear")
        async def ln_estop_clear(ln_id: str) -> dict:
            """组恢复：扇出 sys/estop-clear（confirm 硬令牌；幂等安全）。"""
            def work() -> dict:
                from tessera_agent.tools_net import lno
                with ZenohService(ctx.cfg.router_locator) as svc:
                    return lno.ln_estop_clear(lno.REGISTRY, svc, ln_id)

            return await asyncio.to_thread(work)

        @mcp.tool
        @audited("deploy_push_prov")
        async def deploy_push_prov(node: str, cube: str, prov_path: str,
                                   holder: str = "tessera-agent") -> dict:
            """远程 prov 维护通道（V0.4.0 M10/Q-34；strict：挂起宿主审批）。

            硬点：lease 门控 + confirm 令牌 + 固件写前全量 schema 校验 +
            per-boot 一次性窗（再写须复位循环）；生效 = 下次复位（applies=
            next-reboot）。prov_path = prov CBOR v1/v2 schema 文件（不构造
            内容；v2 = CG2 部署模式/estop 远程清除字段，旧固件只收 v1）。
            高危操作（换身份/根钥）——生产部署前安全评审（Q-34 B 升级项）。"""
            args = {"node": node, "cube": cube, "prov_path": prov_path,
                    "holder": holder}

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                approval = ctx.approvals.request(
                    "deploy_push_prov", args,
                    reason="strict 类：远程 prov 维护写入（换身份/根钥——高危）",
                )
                task.state = "input_required"
                try:
                    await ctx.approvals.wait(approval)
                finally:
                    task.state = "working"

                def work() -> dict:
                    cbor = Path(prov_path).read_bytes()
                    with ZenohService(ctx.cfg.router_locator) as svc:
                        return net_deploy.push_prov(
                            svc, node, cube, cbor, holder=holder, log_fn=log,
                        )

                return await asyncio.to_thread(work)

            return await ctx.registry.start(
                "deploy_push_prov", args, body, budget=ctx.budget)

        @mcp.tool
        @audited("deploy_push_app")
        async def deploy_push_app(node: str, cube: str, package_path: str,
                                  pub_key_path: str, holder: str = "tessera-agent",
                                  chunk_size: int = net_deploy.CHUNK_DEFAULT,
                                  post_check_s: float = 0.0,
                                  serial_port: str | None = None) -> dict:
            """TSAP 包分块部署到 cube（strict：挂起宿主审批；长任务句柄）。

            硬点（工具内强制，不可跳过）：tsap_verify 复验 → 租约闭环（acquire/
            续期/release）→ 2KB 分块（idem 重试安全）→ upload/verify/activate 分步
            → get-app 确认回读。失败留于当前步（重试从断点续传）。

            G 批 D3（诊断自动回喂）：post_check_s > 0 时部署后延时健康检查
            （get-app ACTIVE）——不健康且给出 serial_port 则自动抓取+分类，
            结果入 post_check 键（category/repair_hint/evidence）直接回喂。"""
            args = {
                "node": node, "cube": cube, "package_path": package_path,
                "pub_key_path": pub_key_path, "holder": holder, "chunk_size": chunk_size,
            }

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                # EC3（Q-40③）：审批请求携带包权限面（坏包审批前拦截）
                brief = install_permission_brief(package_path)
                log(f"install permissions: {brief}")
                approval = ctx.approvals.request(
                    "deploy_push_app", args,
                    reason=f"strict 类：远程安装 APP（写 inactive slot + meta 切换）"
                           f"｜{brief}",
                )
                task.state = "input_required"
                try:
                    await ctx.approvals.wait(approval)
                finally:
                    task.state = "working"

                def work() -> dict:
                    with ZenohService(ctx.cfg.router_locator) as svc:
                        out = net_deploy.push_app(
                            svc, node, cube, package_path, pub_key_path,
                            holder=holder, chunk_size=chunk_size, log_fn=log,
                        )
                        if post_check_s > 0:
                            import time as _t

                            _t.sleep(post_check_s)
                            out["post_check"] = net_deploy.post_deploy_check(
                                svc, node, cube,
                                serial_port=serial_port)
                        return out

                return await asyncio.to_thread(work)

            return await spawn("deploy_push_app", args, body)

        # ---- app_*（MA3.2 高层链，DEC-34；消费上述原子工具的实现）----------
        @mcp.tool
        @audited("app_compile")
        async def app_compile(source_c: str, out_dir: str = "agent/build",
                              required_exports: list[str] | None = None,
                              max_bytes: int = 16384) -> dict:
            """C 源 → wasm32 自由固件 + 面检查（DEC-45/Q-25 A；auto 类——本地
            确定性构建，无网络无部署）。检查链全部 fail-closed：clang 固定
            flags 编译（stderr 如实回传供 LLM 反馈回路）→ 导入面 ⊆ natives
            白名单 → 必需导出齐 → 尺寸上限 → 双编译字节一致（确定性自证）。
            产物不执行。"""
            def work() -> dict:
                return compile_app_c(source_c, out_dir, ctx.roots(),
                                     required_exports=required_exports,
                                     max_bytes=max_bytes)
            return await asyncio.to_thread(work)

        @mcp.tool
        @audited("app_develop")
        async def app_develop(spec: str, key_path: str,
                              out_dir: str = "agent/build",
                              wasm_path: str | None = None,
                              plan_confirm: bool = False) -> dict:
            """高层链：需求 spec →（LLM：计划/manifest + source_c C 源）→
            manifest 硬校验 + 链内编译（导入白名单/导出面/尺寸/确定性，
            DEC-45）→ TSAP 打包签名 → 复验（confirm 类；长任务句柄）。
            skills 渐进披露注入编排会话；校验/编译错误反馈回路（预算 3）。
            wasm_path 可选 = 调用方自带产物路径（source_c 缺省时必需）。
            plan_confirm（D7 · DEC-67①）= 计划经问询实体确认（MCP 客户端
            经 sys_answer 应答 proceed/abort；超时缺省 abort）。"""
            args = {"spec": spec, "key_path": key_path, "out_dir": out_dir,
                    "wasm_path": wasm_path, "plan_confirm": plan_confirm}

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                return await app_chain.app_develop(
                    ctx, spec, key_path, out_dir, wasm_path=wasm_path, log_fn=log,
                    task=task,  # D2：循环事件 → task.progress（task_progress 面）
                    plan_confirm=plan_confirm,  # D7：计划确认经问询实体
                )

            return await spawn("app_develop", args, body)

        @mcp.tool
        @audited("app_deploy")
        async def app_deploy(package_path: str, pub_key_path: str,
                             node: str | None = None, cube: str | None = None) -> dict:
            """高层链：包 → 复验 → 发现定位（未指名须恰一在线）→ 分块分步部署 →
            状态确认（strict：挂起宿主审批；长任务句柄）。"""
            args = {"package_path": package_path, "pub_key_path": pub_key_path,
                    "node": node, "cube": cube}

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                # EC3（Q-40③）：审批请求携带包权限面（坏包审批前拦截）
                brief = install_permission_brief(package_path)
                log(f"install permissions: {brief}")
                approval = ctx.approvals.request(
                    "app_deploy", args,
                    reason=f"strict 类：部署 APP 到设备（远程写 slot + meta 切换）"
                           f"｜{brief}",
                )
                task.state = "input_required"
                try:
                    await ctx.approvals.wait(approval)
                finally:
                    task.state = "working"
                return await app_chain.app_deploy(
                    ctx, package_path, pub_key_path, node, cube, log_fn=log,
                )

            return await spawn("app_deploy", args, body)

        # ---- board_validate（V0.13.0 BV1 · LLD-A12；strict 类）
        @mcp.tool
        @audited("board_validate")
        async def board_validate(profile_id: str,
                                 checks: list[str] | None = None,
                                 stop_on_fail: bool = False) -> dict:
            """板卡验证域：画像驱动的确定性检查流水线（串口在场/flash 身份/
            boot 判据/zenoh 连通/caps 消费/部署 E2E 冒烟 → 结构化报告）。
            strict：复位 + 部署冒烟探针 = 板态写入（探针包驻留，不自动还原）；
            spawn 长任务句柄；进度经 task_progress（D2 面）实时外显。"""
            args = {"profile_id": profile_id, "checks": checks,
                    "stop_on_fail": stop_on_fail}
            boards_dir = Path(ctx.cfg.workspace_repo) / "agent" / "boards"

            async def body(task) -> dict:
                approval = ctx.approvals.request(
                    "board_validate", args,
                    reason="strict 类：板卡验证（复位 + 部署冒烟探针——"
                           "板态写入，探针包驻留）",
                )
                task.state = "input_required"
                try:
                    await ctx.approvals.wait(approval)
                finally:
                    task.state = "working"
                profile = bv.load_profile(boards_dir / f"{profile_id}.toml")

                def progress_cb(p: dict) -> None:
                    task.progress.update(p)
                    ctx.registry.append_log(
                        task, f"[bv] {p['check']} {p.get('verdict', '…')}"
                              f" ({p['done']}/{p['total']})")

                transport = bv.LiveTransport(
                    ctx.cfg, ctx=ctx,
                    log_fn=lambda s: ctx.registry.append_log(task, s))
                report = await asyncio.to_thread(
                    bv.validate, profile, transport, checks=checks,
                    stop_on_fail=stop_on_fail, progress_cb=progress_cb)
                task.progress.update({"overall": report.overall,
                                      "checks_done": len(report.checks)})
                out = report.to_json()
                out["report_text"] = report.render()
                return out

            return await spawn("board_validate", args, body)

        # ---- memory_audit（V0.13.0 MP · LLD-A13；confirm 类——本地只读）
        @mcp.tool
        @audited("memory_audit")
        async def memory_audit(map_path: str, config_path: str,
                               prj_conf: str | None = None) -> dict:
            """构建期内存审计（LLD-A13 · DEC-70）：GNU ld map + Kconfig
            .config → 三层内存账本（region 占用/保留/余量 + 具名对象 +
            config 内存意图账）+ 规则目录判定（R0 声明≠生效 / R1-R3 栈
            下限 / R4-R5 堆压 / R6 区域余量 / R7 STATIC TX 观察）。
            overall = PASS/WARN/FAIL；prj_conf 可选作 R0 覆盖对照。"""
            try:
                report = await asyncio.to_thread(
                    ma.audit, map_path, config_path, prj_conf)
            except ma.AuditError as exc:
                raise TaError(TA_E_ARGS, str(exc),
                              domain="memory_audit") from exc
            out = report.to_json()
            out["report_text"] = report.render()
            return out

        # ---- diag_*（NV-1 部署后诊断；confirm 类)
        @mcp.tool
        @audited("diag_classify")
        async def diag_classify(serial_text: str,
                                pass_patterns: list[str],
                                alive_patterns: list[str] | None = None) -> dict:
            """部署后诊断（纯文本分类，无 I/O）：对一次真机运行的串口全文
            做失败分类——类别（pass/env_boot_fail/install_fail/not_active/
            wdt_reset/app_silent/app_no_verdict/no_verdict）+ 修复方向 +
            证据行。类别链源自项目真机历史失败形态；修复闭环编排
            （部署→抓取→分类→反馈重生成→重部署）见 tools_diag/repair.py
            （Python API，编排逻辑随 MCP 会话组装）。"""
            result = diag_cls.classify_run(
                serial_text, pass_patterns=pass_patterns,
                alive_patterns=tuple(alive_patterns or ("alive",)))
            return {"category": result.category, "summary": result.summary,
                    "repair_hint": result.repair_hint,
                    "evidence": result.evidence}

        @mcp.tool
        @audited("spec_check")
        async def spec_check(spec: str) -> dict:
            """spec 质量门（NV-2，纯文本检查）：四节模板（【需求】【资源】
            【判据】【安全声明】）完备性 + 判据引号串机读派生（repair_loop
            的 pass_patterns 单一事实源）+ caps/fs_paths 文法提示。errors
            级硬伤会在 app_develop 入口阻塞（不值得烧 LLM 轮次）。"""
            r = diag_spec_gate.check_spec(spec)
            return {"ok": r.ok, "templated": r.templated,
                    "errors": r.errors, "warnings": r.warnings,
                    "pass_patterns": r.pass_patterns}

        @mcp.tool
        @audited("simreal_diff")
        async def simreal_diff(sim_writes: list[dict],
                               real_console: str,
                               channel_patterns: dict[str, str],
                               tolerance: int = 0) -> dict:
            """sim↔real 语义对拍（NV-3）：sim 重放写序列（sim_run 的
            writes，L4 JSONL）各通道终态 vs 真机 console 判据行读数
            （channel_patterns = {通道: 含一个捕获组的正则}，取最后一次
            命中）——键值集机械 diff（数值容差 tolerance）。"""
            chans = list(channel_patterns)
            sim_map = diag_sr.normalize_sim(sim_writes, chans)
            real_map = diag_sr.normalize_real(real_console, channel_patterns)
            res = diag_sr.diff(sim_map, real_map, tolerance=tolerance)
            return {"pass": res.pass_, "match": res.match,
                    "mismatch": res.mismatch, "missing": res.missing,
                    "sim_map": sim_map, "real_map": real_map}
