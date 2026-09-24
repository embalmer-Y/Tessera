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

from tessera_agent.common.errors import TA_E_TSAP, TaError
from tessera_agent.core.session import PolicyTable
from tessera_agent.domain import app_chain
from tessera_agent.platform import AppContext, DomainPackBase, MountAPI
from tessera_agent.tools_fw import tools as fw
from tessera_agent.tools_net import deploy as net_deploy
from tessera_agent.tools_net.zenoh_service import ZenohService
from tessera_agent.tools_sim import runner as sim_runner
from tessera_agent.tools_sim.scenario import scenario_validate
from tessera_agent.tools_tsap import tools as tsap_tools
from tessera_agent.tools_tsap.manifest import TsapManifest


@dataclass
class FirmwareDeployer:
    """域部署器（LLD-A07 §3 deployer；V1 = deploy.push_app 包装）。"""

    router_locator: str = "tcp/127.0.0.1:7447"

    def deploy(self, ctx: AppContext, node: str, cube: str, package_path: str,
               pub_key_path: str, log_fn=None) -> dict:
        with ZenohService(self.router_locator) as svc:
            return net_deploy.push_app(svc, node, cube, package_path, pub_key_path,
                                       log_fn=log_fn)


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
        "deploy_discover", "deploy_status", "deploy_push_app",
        "app_develop", "app_deploy",
    ])
    skills: list[str] = field(default_factory=lambda: [
        "tessera-workflow", "tessera-build", "tessera-tsap", "tessera-safety",
    ])
    policy: PolicyTable = field(default_factory=lambda: PolicyTable(entries={
        # 审批类别声明（只可收紧；HLD §5.1）
        "tsap_keygen": "strict",
        "deploy_push_app": "strict",
        "app_develop": "confirm",
        "app_deploy": "strict",
    }))
    validators: list = field(default_factory=lambda: [validate_tsap_manifest])
    deployer: Any = field(default_factory=lambda: None)  # 组合根注入 router 配置

    async def info_extras(self, ctx: AppContext) -> dict[str, Any]:
        return {"workspace": await fw.fw_workspace_status(ctx.cfg, ctx.budget),
                "tools": self.tools}

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

        # ---- sim_*（MA2，LLD-A04）------------------------------------------
        @mcp.tool
        @audited("sim_validate_scenario")
        async def sim_validate_scenario(scenario: dict) -> dict:
            """校验仿真场景 schema v1（inputs 升序/op 合法等）；返回错误清单（空=合法）。"""
            return {"errors": scenario_validate(scenario)}

        @mcp.tool
        @audited("sim_run")
        async def sim_run(scenario: dict) -> dict:
            """运行确定性重放仿真（framework.replay 双跑比对 + 期望评估；长任务句柄）。"""
            args = {"scenario": scenario}
            task_id = f"simrun-{secrets.token_hex(4)}"

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                return await sim_runner.sim_run(ctx.cfg, scenario, task_id=task_id,
                                                log_fn=log)

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
            return tsap_tools.tsap_verify(package_path, pub_key_path)

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
        @audited("deploy_push_app")
        async def deploy_push_app(node: str, cube: str, package_path: str,
                                  pub_key_path: str, holder: str = "tessera-agent",
                                  chunk_size: int = net_deploy.CHUNK_DEFAULT) -> dict:
            """TSAP 包分块部署到 cube（strict：挂起宿主审批；长任务句柄）。

            硬点（工具内强制，不可跳过）：tsap_verify 复验 → 租约闭环（acquire/
            续期/release）→ 2KB 分块（idem 重试安全）→ upload/verify/activate 分步
            → get-app 确认回读。失败留于当前步（重试从断点续传）。"""
            args = {
                "node": node, "cube": cube, "package_path": package_path,
                "pub_key_path": pub_key_path, "holder": holder, "chunk_size": chunk_size,
            }

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                approval = ctx.approvals.request(
                    "deploy_push_app", args,
                    reason="strict 类：远程安装 APP（写 inactive slot + meta 切换）",
                )
                task.state = "input_required"
                try:
                    await ctx.approvals.wait(approval)
                finally:
                    task.state = "working"

                def work() -> dict:
                    with ZenohService(ctx.cfg.router_locator) as svc:
                        return net_deploy.push_app(
                            svc, node, cube, package_path, pub_key_path,
                            holder=holder, chunk_size=chunk_size, log_fn=log,
                        )

                return await asyncio.to_thread(work)

            return await spawn("deploy_push_app", args, body)

        # ---- app_*（MA3.2 高层链，DEC-34；消费上述原子工具的实现）----------
        @mcp.tool
        @audited("app_develop")
        async def app_develop(spec: str, wasm_path: str, key_path: str,
                              out_dir: str = "agent/build") -> dict:
            """高层链：需求 spec → 计划/manifest（结构化校验）→ TSAP 打包签名 →
            复验（confirm 类；长任务句柄）。skills 渐进披露注入编排会话；
            V1 边界：wasm 产物由调用方提供（wasm 工具链 = M2b.2）。"""
            args = {"spec": spec, "wasm_path": wasm_path, "key_path": key_path,
                    "out_dir": out_dir}

            async def body(task) -> dict:
                log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                return await app_chain.app_develop(
                    ctx, spec, wasm_path, key_path, out_dir, log_fn=log,
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
                approval = ctx.approvals.request(
                    "app_deploy", args,
                    reason="strict 类：部署 APP 到设备（远程写 slot + meta 切换）",
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
