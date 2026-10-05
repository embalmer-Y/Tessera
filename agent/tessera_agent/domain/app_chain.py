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
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator
from pydantic_ai import Agent

from tessera_agent.common.errors import TA_E_ARGS, TA_E_TSAP, TaError
from tessera_agent.platform import AppContext
from tessera_agent.skills import loader as skill_loader
from tessera_agent.tools_net import deploy as net_deploy
from tessera_agent.tools_net.zenoh_service import ZenohService
from tessera_agent.tools_tsap import tools as tsap_tools
from tessera_agent.tools_tsap.manifest import TsapManifest
from tessera_agent.tools_tsap.wasm_build import compile_app_c


def _unwrap_item(v: object) -> object:
    """{"item": X} 传输伪影解包（见 DevelopOutcome 文档串）；其余原样。"""
    if isinstance(v, dict) and set(v) == {"item"}:
        inner = v["item"]
        return inner if isinstance(inner, list) else [inner]
    return v


TolerantStrList = Annotated[list[str], BeforeValidator(_unwrap_item)]

# 来源: DEC-38 #3——结构化输出重试预算 3
OUTPUT_RETRIES = 3
# 来源: MD1.1 实证（2026-10-04）——链外校验/编译反馈回路预算：manifest 多类
# 瑕疵 + 编译错误的叠加下 3 轮偶不够（MiniMax-M3 实测：数组伪影解包后仍需
# 2-3 轮修字段级错误）；预算独立于结构化重试，放宽到 4。
CHAIN_RETRIES = 4
# 来源: MD0-1 真实 LLM 冒烟（2026-10-02，MiniMax-M3）——思考型模型的推理段
# 会先耗尽 anthropic SDK 的 provider 缺省输出上限（UnexpectedModelBehavior
# "token limit exceeded before any response"），链路对真实端点开箱不可用。
# 16k = DevelopOutcome（manifest+计划）+ 思考段的实测裕量档。
OUTPUT_MAX_TOKENS = 16384
# 来源: DEC-45（Q-25 A，2026-10-04）——source_c 模式下源码进结构化产物，
# 输出预算上调（C 源 + manifest + 思考段；G1 spike 实测源码 ~1-2KB）。
OUTPUT_MAX_TOKENS_WITH_CODE = 32768


class DevelopOutcome(BaseModel):
    """app_develop 结构化产物（LLD-A02 §4 PlanDto 的 MA3 落地形态；
    DEC-45 扩展：source_c 可选——LLM 直接产 C 源，链内编译为 wasm）。

    列表字段经 _unwrap_item 容错（MD1.1 实证：MiniMax-M3 结构化输出的
    数组偶发被包成 {"item": X}——工具调用序列化层伪影；确定性解包，
    非掩盖：纯 {"item"} 包装才解，其余形态原样交校验）。"""

    dto_version: int = 1
    requirements_summary: str
    manifest: dict[str, Any]
    source_c: str | None = None
    safety_notes: TolerantStrList = []
    test_plan: TolerantStrList = []
    steps: TolerantStrList = []


def _develop_system_prompt() -> str:
    return "\n\n".join([
        "你是 Tessera 固件域 APP 开发者。依据需求产出 DevelopOutcome：",
        "manifest 必须满足 TsapManifest v1（app_id 反向域名小写串（仅 a-z0-9.，"
        "禁下划线）；app_ver/min_fw_ver semver；exports 必含 health_ping"
        "（可选 app_init/app_tick/app_evt）；stack_kb≤64）。",
        # MD0-1 实证：caps 文法必须内联——LLM 在仅口头引用 ts_perm_v1 时会自造
        # 格式（{'perm': 'pwm:0#set'}），manifest 硬校验 fail-closed 拦下但链路
        # 不可用；文法短小，直接入提示消除对 skill 阅读的依赖。
        "caps 是字符串数组，文法 ts_perm_v1：\"class:op:instances\"，"
        "class∈{gpio,pwm,adc,power,msg,sys}，op∈{read,write,set}，"
        "instances=实例号（0-3 或 0,2 或 0-3）——例如 [\"pwm:set:0\", \"gpio:write:0\"]。",
        # MD1.1 实证（MiniMax-M3）：结构化输出的数组字段偶发被包成
        # {"item": ...}（传输层 XML 伪影）——显式禁包装
        "caps 与 exports 必须是 JSON 数组字面量（如 [\"gpio:write:0\"]、"
        "[\"health_ping\",\"app_tick\"]）；严禁 {\"item\": ...} 之类的对象包装。",
        # DEC-45（G1）：source_c 主路径——整文件再生（aider 编辑格式分级结论：
        # 小文件域 whole 最可靠，避免部分编辑错位/elision）
        "source_c = 完整单文件 C 源（wasm32 自由固件，非 diff/片段）：",
        "① 导出约定：int app_init(int ctx) / int app_tick(void) / int app_evt(int v) / "
        "int health_ping(void)，全部用 __attribute__((export_name(\"名字\")))；"
        "manifest.exports 列出的必须全部导出。",
        "② 可导入宿主 natives（extern 声明，签名精确，禁其它任何导入）："
        "int ts_gpio_write(int ctx,int inst,int v)；int ts_gpio_read(int ctx,int inst)；"
        "int ts_pwm_set(int ctx,int inst,int hz,int permille)；"
        "int ts_adc_read(int ctx,int inst)；unsigned long long ts_time_ms(int ctx)；"
        "int ts_log_write(int ctx,int lvl,const char* msg,int len)。",
        "③ 约束：禁 WASI/stdio/全局构造/随机/墙钟；静态状态用 file-scope 变量；"
        "确定性（同输入序列同输出）。无源码需求时 source_c 置 null。",
        "安全合同内化：输出经保护层限幅、确定性（禁随机/墙钟分支）、越权拒绝留痕。",
        skill_loader.system_prompt_listing(),
        "先 read_skill 阅读相关 skill（tsap/safety 至少一次），再给出最终结构化产物。",
    ])


async def app_develop(
    ctx: AppContext,
    spec: str,
    key_path: str,
    out_dir: str = "agent/build",
    *,
    wasm_path: str | None = None,
    model: Any = None,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """spec →（LLM：计划/manifest + 可选 source_c）→ manifest 硬校验 + 链内
    编译（DEC-45）→ TSAP 打包签名 → 复验。wasm_path 与 source_c 至少其一：
    LLM 产源码时链内编译（导入白名单/导出面/尺寸/双编译一致性全检查）；
    仅给 wasm_path = 旧路径（调用方自带产物）不衰减。"""
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
        model_settings={'max_tokens': OUTPUT_MAX_TOKENS_WITH_CODE},
    )
    agent.tool_plain(read_skill)

    # 硬校验反馈回路（MD0-1 实证 + DEC-45 扩展编译级）：manifest 校验与
    # 编译/面检查都发生在 LLM 运行之后，pydantic 的结构化重试管不到——
    # 回路 = 校验/编译错误文本 + 消息历史续跑，预算同 OUTPUT_RETRIES（3）；
    # 文法/导出约定内联系统提示降低首错率，本回路兜底。
    history: list[Any] | None = None
    feedback = ''
    compiled: dict[str, Any] | None = None

    def _normalize_manifest(m: dict[str, Any]) -> dict[str, Any]:
        """传输伪影归一化（MD1.1 实证，MiniMax-M3）：结构化输出的数组字段
        偶发被包成 {"item": X}（工具调用序列化层伪影，非模型逻辑错误）——
        确定性解包 + 留痕；其余畸形留给反馈回路（R6：不掩盖根因）。"""
        out = dict(m)
        for f in ("caps", "exports"):
            v = out.get(f)
            if isinstance(v, dict) and set(v) == {"item"}:
                out[f] = v["item"] if isinstance(v["item"], list) else [v["item"]]
                log(f'传输伪影已解包：{f} 的 item 包装（留痕）')
        return out

    for attempt in range(1, CHAIN_RETRIES + 1):
        result = await agent.run(spec if history is None else
                                 f'产物校验失败，请修正后重新给出完整产物：\n{feedback}',
                                 message_history=history)
        outcome: DevelopOutcome = result.output
        outcome.manifest = _normalize_manifest(outcome.manifest)
        history = result.all_messages()
        try:
            TsapManifest(**outcome.manifest)
            if outcome.source_c is not None:
                need = list(outcome.manifest.get("exports", ["health_ping"]))
                compiled = compile_app_c(
                    outcome.source_c, out_dir, ctx.roots(),
                    required_exports=need)
            break
        except Exception as exc:  # noqa: BLE001
            feedback = str(exc)
            compiled = None
            log(f'产物校验失败（尝试 {attempt}/{OUTPUT_RETRIES}）：{feedback[:120]}')
    else:
        msg = f"产物非法（{CHAIN_RETRIES} 次反馈后仍未通过）: {feedback}"
        raise TaError(TA_E_TSAP, msg, domain="app_develop",
                      detail={"manifest": outcome.manifest})
    log(f'plan（第 {attempt} 轮通过）: {outcome.requirements_summary[:80]}')

    wasm = compiled["wasm_path"] if compiled else wasm_path
    if not wasm:
        msg = "wasm_path 与 source_c 至少其一（LLM 未产源码且未提供 wasm）"
        raise TaError(TA_E_ARGS, msg, domain="app_develop")
    if compiled:
        log(f"链内编译 PASS: size={compiled['size']}B "
            f"imports={compiled['imports']} exports={compiled['exports']}")

    # 打包 + 复验（阻塞文件/ed25519 操作 → 线程；"无签名不产出"硬点在工具内）
    def _package_and_verify() -> tuple[dict, str]:
        pkg = tsap_tools.tsap_package(wasm, outcome.manifest, key_path, out_dir,
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
        "source_sha256": compiled["source_sha256"] if compiled else None,
        "compiled": compiled is not None,
        "compile_facts": compiled,
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
