# SPDX-License-Identifier: Apache-2.0
"""高层任务链（DEC-34 高层层；HLD-agent §2.1 S2/S5）。

- app_develop：spec →（PydanticAI 编排：skills 渐进披露 + 结构化产物校验）
  → manifest 校验 → tsap_package 签名 → tsap_verify 复验 → 交付包路径。
  **V1 边界**：wasm 产物由调用方提供（wasm 工具链 = M2b.2）——本链负责
  计划/manifest/打包/复验的确定性与"无签名不产出"硬点。
- app_deploy：tsap_verify 复验 → discover 定位（未指名时须恰一在线）→
  push_app 分块分步部署 → status 确认回读（S5）。
测试注：模型经 model 参数注入（FunctionModel 剧本），生产 = cfg.default_model。
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent

from tessera_agent.common.errors import TA_E_ARGS, TA_E_TSAP, TaError
from tessera_agent.platform import AppContext
from tessera_agent.skills import loader as skill_loader
from tessera_agent.tools_net import deploy as net_deploy
from tessera_agent.tools_net.zenoh_service import ZenohService
from tessera_agent.tools_tsap import tools as tsap_tools
from tessera_agent.tools_tsap.manifest import TsapManifest

# 来源: DEC-38 #3——结构化输出重试预算 3
OUTPUT_RETRIES = 3


class DevelopOutcome(BaseModel):
    """app_develop 结构化产物（LLD-A02 §4 PlanDto 的 MA3 落地形态）。"""

    dto_version: int = 1
    requirements_summary: str
    manifest: dict[str, Any]
    safety_notes: list[str] = []
    test_plan: list[str] = []
    steps: list[str] = []


def _develop_system_prompt() -> str:
    return "\n\n".join([
        "你是 Tessera 固件域 APP 开发编排器。依据需求产出 DevelopOutcome：",
        "manifest 必须满足 TsapManifest v1（app_id 反向域名式；app_ver/min_fw_ver semver；",
        "exports 必含 health_ping；stack_kb≤64；caps 遵循 ts_perm_v1 最小权限）。",
        "安全合同内化：输出经保护层限幅、确定性（禁随机/墙钟分支）、越权拒绝留痕。",
        skill_loader.system_prompt_listing(),
        "先 read_skill 阅读相关 skill（tsap/safety 至少一次），再给出最终结构化产物。",
    ])


async def app_develop(
    ctx: AppContext,
    spec: str,
    wasm_path: str,
    key_path: str,
    out_dir: str = "agent/build",
    *,
    model: Any = None,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    log = log_fn or (lambda s: None)
    skills = skill_loader.load_skills()
    active = [s.name for s in skills]
    log(f"skills active: {active}")

    async def read_skill(name: str) -> str:
        """读取 skill 全文（渐进披露二级内容）。"""
        return skill_loader.read_skill(name)

    agent = Agent(
        model or ctx.cfg.default_model,
        output_type=DevelopOutcome,
        retries=OUTPUT_RETRIES,
        system_prompt=_develop_system_prompt(),
    )
    agent.tool_plain(read_skill)
    result = await agent.run(spec)
    outcome: DevelopOutcome = result.output
    log(f"plan: {outcome.requirements_summary[:80]}")

    # manifest 硬校验（打包前；失败 = 结构化错误，不降级）
    try:
        TsapManifest(**outcome.manifest)
    except Exception as exc:  # noqa: BLE001
        msg = f"产物 manifest 非法: {exc}"
        raise TaError(TA_E_TSAP, msg, domain="app_develop",
                      detail={"manifest": outcome.manifest}) from exc

    # 打包 + 复验（阻塞文件/ed25519 操作 → 线程；"无签名不产出"硬点在工具内）
    def _package_and_verify() -> tuple[dict, str]:
        pkg = tsap_tools.tsap_package(wasm_path, outcome.manifest, key_path, out_dir,
                                      ctx.roots())
        pub = str(Path(key_path).expanduser().with_suffix(".pub"))
        tsap_tools.tsap_verify(pkg["package_path"], pub)
        return pkg, pub

    pkg, pub = await asyncio.to_thread(_package_and_verify)
    log(f"package + verify PASS: {pkg['package_path']}")
    return {
        "requirements_summary": outcome.requirements_summary,
        "safety_notes": outcome.safety_notes,
        "test_plan": outcome.test_plan,
        "steps": outcome.steps,
        "manifest": outcome.manifest,
        "package_path": pkg["package_path"],
        "package_size": pkg["size"],
        "pub_key_path": pub,
        "skills_active": active,
        "model": str(model or ctx.cfg.default_model),
    }


async def app_deploy(
    ctx: AppContext,
    package_path: str,
    pub_key_path: str,
    node: str | None = None,
    cube: str | None = None,
    *,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    log = log_fn or (lambda s: None)
    if bool(node) != bool(cube):
        msg = "node 与 cube 须成对提供（或都不提供=自动发现恰一在线 cube）"
        raise TaError(TA_E_ARGS, msg, domain="app_deploy")

    # S5：复验 → 定位 → 推送 → 确认
    tsap_tools.tsap_verify(package_path, pub_key_path)
    log("tsap_verify PASS")

    def work() -> dict[str, Any]:
        with ZenohService(ctx.cfg.router_locator) as svc:
            n, c = node, cube
            if not n:
                cubes = net_deploy.discover(svc)
                if len(cubes) != 1:
                    msg = f"须指定 node/cube 或恰好一个在线 cube（当前 {len(cubes)} 个）"
                    raise TaError(TA_E_ARGS, msg, domain="app_deploy",
                                  detail={"cubes": cubes})
                n, c = cubes[0]["node_id"], cubes[0]["cube_id"]
                log(f"auto-target: {n}/{c}")
            deployed = net_deploy.push_app(svc, n, c, package_path, pub_key_path,
                                           log_fn=log)
            status_after = net_deploy.status(svc, n, c)
            return {"node": n, "cube": c, "deploy": deployed,
                    "status_after": status_after}

    out = await asyncio.to_thread(work)
    if not out["deploy"].get("confirmed"):
        msg = "部署未确认（activate/get-app 回读不一致）"
        raise TaError(TA_E_TSAP, msg, domain="app_deploy", detail=out["deploy"])
    log(f"deployed + confirmed: {out['node']}/{out['cube']}")
    return out
