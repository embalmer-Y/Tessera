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
import hashlib
import json
import secrets
import time
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator
from pydantic_ai import Agent

from tessera_agent.common.errors import TA_E_ARGS, TA_E_POLICY, TA_E_TSAP, TaError
from tessera_agent.creation.loop import (
    DEFAULT_BUDGET as LOOP_BUDGET,
)
from tessera_agent.creation.loop import (
    CreationLoop,
    PlanItem,
    RoundOutcome,
)
from tessera_agent.creation.tools import WorkspaceTools
from tessera_agent.creation.workspace import Workspace
from tessera_agent.domain.firmware_creation import FirmwareCreationVerifier
from tessera_agent.platform import AppContext
from tessera_agent.skills import loader as skill_loader
from tessera_agent.tools_diag import spec_gate
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
# 来源: NV-1 真机实证（2026-10-11）——activate 后板自动暖复位（断链重连
# 实测 ~10-15s），立即 status 核验撞复位窗口 Timeout 误报部署失败；
# REBOOT_WAIT_S = 轮询上限 30s（实测 2 倍裕量），REBOOT_RETRY_S = 间隔。
REBOOT_WAIT_S = 30.0
REBOOT_RETRY_S = 2.0


class DevelopOutcome(BaseModel):
    """app_develop 结构化产物（LLD-agent-core §4 PlanDto 的 MA3 落地形态；
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


# 工程约定块（单发流与创作循环共用——改一处两流同步）
_CONVENTIONS = [
    # MD0-1 实证：caps 文法必须内联——LLM 在仅口头引用 ts_perm_v1 时会自造
    # 格式（{'perm': 'pwm:0#set'}），manifest 硬校验 fail-closed 拦下但链路
    # 不可用；文法短小，直接入提示消除对 skill 阅读的依赖。
    "caps 是字符串数组，文法 ts_perm_v1：\"class:op:instances\"，"
    "class∈{gpio,pwm,adc,power,fs,av,msg,sys}，op∈{read,write,set,list,delete,send}，"
    "instances=实例号（0-3 或 0,2 或 0-3）——例如 [\"pwm:set:0\", "
    "\"gpio:write:0\", \"fs:read:0\"]。"
    "msg 类例外（APP 间消息）：实例段 = 目标 APP 串身份——"
    "\"msg:send:<目标app_id>\"（如 [\"msg:send:tessera.demo.other\"]；"
    "最多 4 个目标，未声明目标的发送运行时拒绝）。"
    "fs 类的路径授权用 manifest 可选字段 fs_paths（绝对路径前缀白名单数组，"
    "如 [\"/SD:/apps-data\"]——未列前缀的路径运行时拒绝）。"
    "av 类（采集/流发布，MD1.2g）必须在 manifest 声明 av_fmt（\"jpeg\"|"
    "\"rgb565\"）+ av_w + av_h（三者与 caps 含 \"av:read:0\" 互为充要）。",
    # MD1.1 实证（MiniMax-M3）：结构化输出的数组字段偶发被包成
    # {"item": ...}（传输层 XML 伪影）——显式禁包装
    "caps 与 exports 必须是 JSON 数组字面量（如 [\"gpio:write:0\"]、"
    "[\"health_ping\",\"app_tick\"]）；严禁 {\"item\": ...} 之类的对象包装。",
    "② 可导入宿主 natives（extern 声明，签名精确，禁其它任何导入）："
    "int ts_gpio_write(int ctx,int inst,int v)；int ts_gpio_read(int ctx,int inst)；"
    "int ts_pwm_set(int ctx,int inst,int hz,int permille)；"
    "int ts_adc_read(int ctx,int inst)；unsigned long long ts_time_ms(int ctx)；"
    "int ts_log_write(int ctx,int lvl,const char* msg,int len)；"
    "int ts_fs_read(int ctx,const char* path,int path_len,int off,char* buf,int cap)；"
    "int ts_fs_write(int ctx,const char* path,int path_len,int off,const char* data,int len)；"
    "int ts_fs_list(int ctx,const char* dir,int dir_len,char* out,int cap)；"
    "int ts_fs_delete(int ctx,const char* path,int path_len)；"
    "int ts_av_capture(int ctx,char* buf,int cap)；"
    "int ts_net_publish(int ctx,int frame_id,int chunk_id,"
    "int n_chunks,const char* buf,int len)；"
    "int ts_kv_save(int ctx,const char* buf,int len)；"
    "int ts_kv_load(int ctx,char* buf,int cap)；"
    "int ts_msg_send(int ctx,const char* target,int target_len,const char* data,int len)；"
    "int ts_msg_recv(int ctx,char* from,int from_cap,char* buf,int cap)；"
    "int ts_power_set(int ctx,int slot,int on,int ma)；"
    "int ts_power_get(int ctx,int slot,int* ma)。",
    "（fs natives 仅当 manifest caps 含对应 fs:op 且 fs_paths 覆盖路径时可用；"
    "返回 >=0 为字节数、<0 为错误码；路径缓冲在 wasm 线性内存内。）"
    "（ts_kv_save/ts_kv_load = 本 APP 业务状态持久化（V0.4.0 M9，DR-15）："
    "一份 ≤250B 不透明 blob，跨升级/回滚自动保留（按 app_id 归属，无需键名）；"
    "save 全量覆盖、load 返回最新长度（≥0）或错误码（<0；-6 = 未存过）；"
    "仅当 caps 含 kv:write:0 / kv:read:0 时可用——静态状态优先存全局变量，"
    "仅**跨重启/升级需要保留**的才用 kv。）"
    "（ts_msg_send/ts_msg_recv = APP 间消息（P1-1）：向运行中的目标 APP 串身份发送 "
    "≤96B 载荷（授权 = caps 的 msg:send 名单；目标未运行 = -7；对方消息槽满 = -5）；"
        "接收方在 app_evt 收到负载 0x4D53475A 时调 ts_msg_recv 取件（from = 发送方身份；"
        "返回 ≥0 为长度，0 = 空。）"
    "（资源档位 CG4：manifest 可选字段 tier=\"small\"（缺省，wasm ≤16KB）/"
    "\"large\"（≤256KB，须附 needs={linear_memory_kb, stack_kb, resources[]}——"
    "线性内存/栈在编译期钉死；resources = 需要的 fs 路径前缀清单）。"
    "大型资源表（字体/位图等 >16KB）用 tier=large 声明，"
    "常规 APP 一律缺省 small 不携带该字段。）"
    "（ts_av_capture 阻塞取一帧到 buf，返回帧长；仅当 caps 含 av:read:0 且 "
    "manifest 声明 av_fmt/av_w（图像另需 av_h；pcm16 音频 = av_w 恒 16、"
    "无 av_h，帧 640B 定长）时可用。ts_net_publish 发布一分片：把帧"
    "按 ≤1024 字节切块、frame_id 每帧自增、chunk_id/n_chunks 标注分片序；"
    "宿主负责打拍与重试——连续调用无需自行等待；返回 <0 且为 -5（BUSY）时"
    "稍后重发同一分片即可。）",
    "③ 约束：禁 WASI/stdio/全局构造/随机/墙钟；静态状态用 file-scope 变量；"
    "确定性（同输入序列同输出）。"
    "安全合同内化：输出经保护层限幅、确定性（禁随机/墙钟分支）、越权拒绝留痕。",
]

_EXPORT_CONVENTION = (
    "① 导出约定：int app_init(int ctx) / int app_tick(void) / int app_evt(int v) / "
    "int health_ping(void)。manifest.exports 列出的必须全部导出。"
    "**health_ping 语义合同：恒返回 0**"
    "（0=健康；非零=健康失败，连续 3 次触发自动回滚——业务完成态/终态一律经"
    " ts_log 行表达，绝不用 health_ping 返回值表达；编译门对非零返回字面量直接拒绝）。"
)


def _develop_system_prompt() -> str:
    """单发流（wasm_path 旧路径）系统提示——内容与 AG6 前版本一致。"""
    return "\n\n".join([
        "你是 Tessera 固件域 APP 开发者。依据需求产出 DevelopOutcome：",
        "manifest 必须满足 TsapManifest v1（app_id 反向域名小写串（仅 a-z0-9.，"
        "禁下划线）；app_ver/min_fw_ver semver；exports 必含 health_ping"
        "（可选 app_init/app_tick/app_evt）；stack_kb≤64）。",
        *(_CONVENTIONS[:2]),
        # DEC-45（G1）：source_c 主路径——整文件再生（aider 编辑格式分级结论：
        # 小文件域 whole 最可靠，避免部分编辑错位/elision）
        "source_c = 完整单文件 C 源（wasm32 自由固件，非 diff/片段）：",
        _EXPORT_CONVENTION + "全部用 __attribute__((export_name(\"名字\")))；",
        *_CONVENTIONS[2:],
        "无源码需求时 source_c 置 null。",
        skill_loader.system_prompt_listing(),
        "先 read_skill 阅读相关 skill（tsap/safety 至少一次），再给出最终结构化产物。",
    ])


def _plan_system_prompt() -> str:
    return "\n\n".join([
        "你是 Tessera APP 工程负责人。把需求分解为实现步骤（3-8 步，每步一句"
        "话、可验证判定），并给出安全性注记与测试计划。",
        "requirements_summary 一句话概括需求。",
    ])


def _implement_system_prompt() -> str:
    """创作循环 implement 轮系统提示（AG6 · LLD-agent-creation-workspace §5.4）。"""
    return "\n\n".join([
        "你是 Tessera 固件域 APP 开发者，在创作工作区中多轮迭代实现工程。",
        "manifest 必须满足 TsapManifest v1（app_id 反向域名小写串（仅 a-z0-9.，"
        "禁下划线）；app_ver/min_fw_ver semver；exports 必含 health_ping；"
        "stack_kb≤64）。",
        *(_CONVENTIONS[:2]),
        _EXPORT_CONVENTION,
        "工程形态：用 ws_write/ws_edit 编写多文件工程（main.c/thermo.c/"
        "include/*.h）——**ws_* 路径以工程根为基准（直接写 main.c、"
        "include/util.h，不带 project/ 前缀）**，"
        "工程内头文件用引号包含（#include \"include/util.h\"——仅限工程文件表内，"
        "系统 #include<> 禁止）；小文件（≤200 行）整文件再生，大文件用唯一锚点替换。",
        "manifest 就绪时随 ImplementOutcome 的 manifest 字段给出（app_id/threads "
        "同轮给出；exports 会同步工程清单用于链接导出）。",
        "全部实现完成且 manifest 就绪才 declared_done=true；验证证据不通过时"
        "按证据最小修复，不要重写无关文件。",
        *_CONVENTIONS[2:],
        skill_loader.system_prompt_listing(),
        "可用 ws_read/ws_list 查看工程与仓库白名单（框架头文件/skills/文档）。",
    ])


class PlanOutcome(BaseModel):
    """创作循环 plan 阶段产物（AG6 · LLD-agent-core §5a）。"""

    dto_version: int = 1
    requirements_summary: str
    safety_notes: TolerantStrList = []
    test_plan: TolerantStrList = []
    steps: TolerantStrList = []


class ImplementOutcome(BaseModel):
    """创作循环 implement 轮产物：manifest 就绪时随轮给出（工程清单由
    runner 落盘），全部完成才 declared_done。"""

    declared_done: bool
    summary: str = ""
    manifest: dict[str, Any] | None = None
    app_id: str | None = None
    threads: int | None = None


class PydanticLoopRunner:
    """LoopRunner 的 PydanticAI 实现（AG6 接线；HLD-agent v0.2 §2.2）。

    plan/implement 双 Agent；implement 工具面 = ws_* 四动词 + read_skill
    （渐进披露维持）；manifest 随轮校验（TsapManifest 硬校验不过 →
    declared_done=False 带错误小结回喂下轮，不抛崩循环）。
    """

    def __init__(
        self,
        ctx: AppContext,
        ws: Workspace,
        *,
        model: Any = None,
        log_fn: Callable[[str], None] | None = None,
    ) -> None:
        self._log = log_fn or (lambda s: None)
        self._ws = ws
        m = model or ctx.cfg.default_model
        tools = WorkspaceTools(ws)

        async def read_skill(name: str) -> str:
            return skill_loader.read_skill(name)

        def _safe(fn):
            """TaError → 结构化字符串返回（LLM 反馈回喂——与 gated_tool 同语义，
            AG7 实证：路径错之类模型侧失误不该炸穿循环）。"""
            import functools

            @functools.wraps(fn)
            async def wrapper(*args, **kwargs):
                try:
                    result = fn(*args, **kwargs)
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                except TaError as exc:
                    return (f"工具 {fn.__name__} 失败："
                            f"{json.dumps(exc.to_payload(), ensure_ascii=False)}")
            return wrapper

        self._plan_agent = Agent(
            m, output_type=PlanOutcome, retries=OUTPUT_RETRIES,
            system_prompt=_plan_system_prompt(),
            model_settings={"max_tokens": OUTPUT_MAX_TOKENS},
        )
        impl = Agent(
            m, output_type=ImplementOutcome, retries=OUTPUT_RETRIES,
            system_prompt=_implement_system_prompt(),
            model_settings={"max_tokens": OUTPUT_MAX_TOKENS_WITH_CODE},
        )
        impl.tool_plain(_safe(tools.ws_read))
        impl.tool_plain(_safe(tools.ws_write))
        impl.tool_plain(_safe(tools.ws_edit))
        impl.tool_plain(_safe(tools.ws_list))
        impl.tool_plain(_safe(read_skill))
        self._impl_agent = impl
        self.requirements_summary = ""
        self.safety_notes: list[str] = []
        self.test_plan: list[str] = []
        self.steps: list[str] = []

    async def plan(self, spec: str, criteria: list[str]) -> list[PlanItem]:
        clause = ""
        if criteria:
            lines = "\n".join(f'  - "{c}"' for c in criteria)
            clause = ("\n\n[判据/附属证据行约束——实现必须让这些行逐字出现：\n"
                      f"{lines}\n]")
        result = await self._plan_agent.run(spec + clause)
        out = result.output
        self.requirements_summary = out.requirements_summary
        self.safety_notes = list(out.safety_notes)
        self.test_plan = list(out.test_plan)
        self.steps = list(out.steps)
        return [PlanItem(f"s{i}", s) for i, s in enumerate(out.steps, start=1)]

    async def implement(self, prompt: str) -> RoundOutcome:
        result = await self._impl_agent.run(prompt)
        out = result.output
        if out.manifest is not None:
            return self._persist_or_feedback(out)
        return RoundOutcome(declared_done=out.declared_done, summary=out.summary)

    def _persist_or_feedback(self, out: ImplementOutcome) -> RoundOutcome:
        """manifest 归一化 + 硬校验 + 工程清单落盘；校验不过转下轮反馈。"""
        try:
            manifest = _normalize_manifest(dict(out.manifest), self._log)
            TsapManifest(**manifest)
        except Exception as exc:  # noqa: BLE001 - 反馈回喂（R6：原文不美化）
            return RoundOutcome(
                declared_done=False,
                summary=f"manifest 校验未过：{exc}",
            )
        project = self._ws.load_project()
        if out.app_id:
            project["app_id"] = out.app_id
        if out.threads:
            project["threads"] = int(out.threads)
        project["manifest"] = manifest
        project["exports"] = list(manifest.get("exports", ["health_ping"]))
        # CG4（Q-39②）：档位三方一致——manifest tier/needs 同步工程清单
        #（compile 消费 project.json 同名字段；manifest 与编译门不允许漂移）
        if "tier" in manifest:
            project["tier"] = manifest["tier"]
        if manifest.get("needs") is not None:
            project["needs"] = manifest["needs"]
        self._ws.save_project(project)
        self._log(f"manifest 落盘：app_id={manifest.get('app_id')} "
                  f"exports={project['exports']}")
        return RoundOutcome(
            declared_done=out.declared_done, summary=out.summary,
            manifest=manifest, app_id=out.app_id, threads=out.threads,
        )


def _normalize_manifest(m: dict[str, Any], log: Callable[[str], None]) -> dict[str, Any]:
    """传输伪影归一化（MD1.1 实证，MiniMax-M3）：结构化输出的数组字段
    偶发被包成 {"item": X} 或整段序列化为 JSON 字符串，且可叠加（NV-1
    实测第三形态：{"item": "[\\\"health_ping\\",…]"} 双层）——级联确定性
    解包（上限 3 层）+ 留痕；其余畸形留给反馈回路（R6：不掩盖根因）。"""
    out = dict(m)
    for f in ("caps", "exports", "fs_paths"):  # fs_paths（MD1.2f 实证同伪影）
        v = out.get(f)
        changed = False
        for _ in range(3):  # 实测叠加 ≤2 层；3 = 防御上限
            if isinstance(v, dict) and set(v) == {"item"}:
                inner = v["item"]
                v = inner if isinstance(inner, list) else [inner]
                changed = True
            elif isinstance(v, str) and v.lstrip().startswith("["):
                try:
                    parsed = json.loads(v)
                except ValueError:
                    break  # 非法 JSON 交校验器如实报错
                if not isinstance(parsed, list):
                    break
                v = parsed
                changed = True
            else:
                break
        if changed:
            out[f] = v
            log(f"传输伪影已解包：{f}（级联，留痕）")
    return out


async def app_develop(
    ctx: AppContext,
    spec: str,
    key_path: str,
    out_dir: str = "agent/build",
    *,
    wasm_path: str | None = None,
    repair_feedback: str = "",
    model: Any = None,
    log_fn: Callable[[str], None] | None = None,
    task: Any = None,
    plan_confirm: bool = False,
) -> dict[str, Any]:
    """spec → APP 开发包（双路径，AG6 · DEC-56/57）：

    - **创作循环路径**（wasm_path=None，主路径）：spec_check 门 → 工作区
      创作循环（计划→ws_* 多文件编辑→编译/sim 证据回喂→收敛）→ 签名打包
      → 复验（HLD-agent v0.2 S2'）。
    - **单发路径**（wasm_path 给出，旧契约维持）：单轮结构化产物 +
      校验/编译反馈回路（AG6 前行为，供自带产物/既有剧本）。

    :param repair_feedback: 部署后诊断反馈（NV-1）——循环路径注入首轮证据；
        单发路径追加首轮提示（既有语义）。
    """
    log = log_fn or (lambda s: None)
    gate = spec_gate.check_spec(spec)
    for w in gate.warnings:
        log(f"spec-gate: {w}")
    if gate.errors:
        msg = f"spec 质量门未过：{'；'.join(gate.errors)}"
        raise TaError(TA_E_ARGS, msg, domain="app_develop",
                      detail={"errors": gate.errors})
    # HW-4 ②（LLD-agent-hardware-targeting §7.2）：直填 spec 无【目标硬件】段且配置绑定画像 →
    # 自动追加硬件事实段（可用通道/实例/禁假设纪律注入创作链——LLM 不再
    # 凭空假设「gpio 0 = 板载 LED」）；未配置/无事实 = 原样（不静默改判）。
    from tessera_agent.domain import hardware as hwdom
    profile = hwdom.load_bound_profile(ctx.cfg)
    if profile is not None and "【目标硬件】" not in spec:
        brief = hwdom.hardware_facts_brief(profile)
        spec = hwdom.append_hw_section(spec, brief)
        log(f"hardware facts 注入: {brief[:160]}")
    skills = skill_loader.load_skills()
    active = [s.name for s in skills]
    log(f"skills active: {active}")

    if wasm_path is None:
        return await _app_develop_loop(ctx, spec, key_path, gate, active,
                                       model=model, log=log,
                                       repair_feedback=repair_feedback,
                                       task=task,
                                       plan_confirm=plan_confirm)
    return await _app_develop_single_shot(ctx, spec, key_path, out_dir, wasm_path,
                                          gate, active, model=model, log=log,
                                          repair_feedback=repair_feedback)


def note_loop_progress(progress: dict[str, Any], kind: str,
                       data: dict[str, Any]) -> None:
    """创作循环事件 → 任务结构化进度（D2 · DEC-65⑤：计划/进度 MCP 外显）。

    只增改已知键（计划覆盖/轮次覆盖/状态覆盖/证据计数累加），不新增顶层
    形状——task_progress 消费面稳定；非循环事件静默忽略。"""
    if kind == "state":
        progress["loop_state"] = data.get("state")
        if "repair" in data:
            progress["repairing"] = bool(data.get("repair"))
    elif kind == "plan":
        progress["plan"] = list(data.get("items", []))
    elif kind == "round":
        progress["round"] = data.get("round")
        progress["round_budget"] = data.get("budget")
        progress["last_declared_done"] = bool(data.get("declared_done"))
    elif kind == "evidence":
        progress["evidence_count"] = int(progress.get("evidence_count", 0)) + 1
        progress["last_evidence"] = {"step": data.get("step"),
                                     "round": data.get("round")}
    elif kind == "final":
        progress["loop_state"] = data.get("state")
        progress["rounds_used"] = data.get("rounds")


async def _app_develop_loop(
    ctx: AppContext,
    spec: str,
    key_path: str,
    gate: Any,
    active: list[str],
    *,
    model: Any = None,
    log: Callable[[str], None],
    repair_feedback: str = "",
    task: Any = None,
    plan_confirm: bool = False,
) -> dict[str, Any]:
    """创作循环后端（HLD-agent v0.2 §2.2；LLD-agent-creation-workspace 全链）。"""
    repo = Path(ctx.cfg.workspace_repo)
    base = repo / "agent" / "workspace"
    task_id = f"t-{secrets.token_hex(4)}"
    ro_roots = [
        p for p in (
            repo / "firmware" / "module" / "tessera" / "include",
            repo / "agent" / "skills",
            repo / "docs",
        ) if p.is_dir()
    ]
    ws = Workspace.create(base, task_id, ro_roots=ro_roots)
    log(f"workspace: {ws.root}")

    runner = PydanticLoopRunner(ctx, ws, model=model, log_fn=log)
    verifier = FirmwareCreationVerifier()

    async def _on_event(kind: str, data: dict[str, Any]) -> None:
        log(f"loop:{kind} {json.dumps(data, ensure_ascii=False)[:200]}")
        if task is not None:
            note_loop_progress(task.progress, kind, data)
            # W2（LLD-agent-web-reshape §4.2）：活动触碰 + 总线发布（registry 单一入口）
            ctx.registry.note_progress(task)
        # D7（DEC-67①）：计划确认经问询实体透传（MCP 客户端应答；超时取
        # default/无 default 异常）。CLI 路径不走此桥（门面终端确认不变）。
        if kind == "plan" and plan_confirm:
            q = ctx.questions.ask(
                "计划确认：是否按该计划开始实施？",
                ["proceed", "abort"],
                default="abort",
                context="app_develop.plan_confirm",
            )
            ans = await ctx.questions.wait(q)
            log(f"plan_confirm: {ans}")
            if ans != "proceed":
                raise TaError(
                    TA_E_POLICY,
                    "计划被拒绝（plan_confirm=abort）",
                    domain="app_develop",
                    detail={"state": "ABORTED", "question_id": q.id},
                )

    loop = CreationLoop(
        ws, verifier, runner, spec,
        criteria=list(gate.pass_patterns), budget=LOOP_BUDGET,
        key_path=key_path, on_event=_on_event,
    )
    if repair_feedback:
        loop.evidence_log.append(
            {"round": 0, "step": "deploy_diag", "detail": repair_feedback})

    result = await loop.run()
    if result.state != "PACKAGED":
        msg = (f"创作循环未收敛（{result.state}，{result.rounds_used} 轮）："
               f"{result.failure_reason}")
        raise TaError(TA_E_TSAP, msg, domain="app_develop",
                      detail={"state": result.state,
                              "rounds": result.rounds_used,
                              "workspace": result.workspace,
                              "evidence_tail": result.evidence_log[-3:]})
    assert result.artifact is not None
    compile_facts = dict(result.facts.get("compile", {}))
    pkg_facts = result.artifact.facts

    def _verify_packaged() -> str:
        pub = str(Path(key_path).expanduser().with_suffix(".pub"))
        tsap_tools.tsap_verify(result.artifact.package_path, pub, ctx.roots())
        return pub

    pub = await asyncio.to_thread(_verify_packaged)  # 阻塞文件操作 → 线程
    files_sha = compile_facts.get("files_sha256") or {}
    source_sha256 = (
        hashlib.sha256(json.dumps(files_sha, sort_keys=True).encode()).hexdigest()
        if files_sha else None
    )
    log(f"loop PACKAGED: {result.artifact.package_path}（{result.rounds_used} 轮）")
    return {
        "requirements_summary": runner.requirements_summary,
        "safety_notes": runner.safety_notes,
        "test_plan": runner.test_plan,
        "steps": runner.steps,
        "manifest": ws.load_project().get("manifest", {}),
        "source_sha256": source_sha256,
        "compiled": True,
        "compile_facts": compile_facts,
        "package_path": result.artifact.package_path,
        "package_size": pkg_facts.get("size"),
        "pub_key_path": pub,
        "skills_active": active,
        "model": str(model or ctx.cfg.default_model),
        # 循环新键（additive——旧调用方不受影响）
        "task_id": task_id,
        "workspace": result.workspace,
        "state": result.state,
        "rounds": result.rounds_used,
    }


async def _app_develop_single_shot(
    ctx: AppContext,
    spec: str,
    key_path: str,
    out_dir: str,
    wasm_path: str,
    gate: Any,
    active: list[str],
    *,
    model: Any = None,
    log: Callable[[str], None],
    repair_feedback: str = "",
) -> dict[str, Any]:
    """单发流（wasm_path 旧契约——AG6 前行为原样维持）。"""
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

    # V2-4 附属证据约束：spec_gate 派生的全部判据/附属串注入首轮提示——
    # NV-6 实证 LLM 会简化附属证据行（周期/告警行未实现，仅主判据达成）；
    # 显式列全部必须输出的行，把「spec 判据节全部引号串 = 实现面」写死。
    evidence_clause = ''
    if len(gate.pass_patterns) > 1:
        lines = "\n".join(f'  - "{p}"' for p in gate.pass_patterns)
        evidence_clause = (
            "\n\n[判据/附属证据行约束——以下每一行都必须在 APP 运行中按"
            f"精确格式逐字输出（含前缀与格式细节，缺一即实现不完整）：\n{lines}\n]"
        )

    # 硬校验反馈回路（MD0-1 实证 + DEC-45 扩展编译级）
    history: list[Any] | None = None
    feedback = ''
    compiled: dict[str, Any] | None = None
    outcome: DevelopOutcome | None = None

    for attempt in range(1, CHAIN_RETRIES + 1):
        if history is None:
            user_prompt = spec + evidence_clause
            if repair_feedback:
                user_prompt += (
                    "\n\n[部署后诊断反馈——上一版部署到真机运行失败，"
                    f"请在本版修复：\n{repair_feedback}\n]"
                )
        else:
            user_prompt = f'产物校验失败，请修正后重新给出完整产物：\n{feedback}'
        result = await agent.run(user_prompt, message_history=history)
        outcome = result.output
        outcome.manifest = _normalize_manifest(outcome.manifest, log)
        history = result.all_messages()
        try:
            TsapManifest(**outcome.manifest)
            if outcome.source_c is not None:
                need = list(outcome.manifest.get("exports", ["health_ping"]))
                compiled = compile_app_c(
                    outcome.source_c, out_dir, ctx.roots(),
                    required_exports=need,
                    threads=int(outcome.manifest.get("threads") or 1),
                    tier=str(outcome.manifest.get("tier") or "small"),
                    needs=outcome.manifest.get("needs"))
            break
        except Exception as exc:  # noqa: BLE001
            feedback = str(exc)
            compiled = None
            log(f'产物校验失败（尝试 {attempt}/{OUTPUT_RETRIES}）：{feedback[:120]}')
    else:
        msg = f"产物非法（{CHAIN_RETRIES} 次反馈后仍未通过）: {feedback}"
        raise TaError(TA_E_TSAP, msg, domain="app_develop",
                      detail={"manifest": outcome.manifest if outcome else None})
    assert outcome is not None
    log(f'plan（第 {attempt} 轮通过）: {outcome.requirements_summary[:80]}')

    wasm = compiled["wasm_path"] if compiled else wasm_path
    if compiled:
        log(f"链内编译 PASS: size={compiled['size']}B "
            f"imports={compiled['imports']} exports={compiled['exports']}")

    # 打包 + 复验（阻塞文件/ed25519 操作 → 线程；"无签名不产出"硬点在工具内）
    def _package_and_verify() -> tuple[dict, str]:
        pkg = tsap_tools.tsap_package(wasm, outcome.manifest, key_path, out_dir,
                                      ctx.roots())
        pub = str(Path(key_path).expanduser().with_suffix(".pub"))
        tsap_tools.tsap_verify(pkg["package_path"], pub, ctx.roots())  # IR2-03
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
    tsap_tools.tsap_verify(package_path, pub_key_path, ctx.roots())  # IR2-03
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
            # activate 后板自动暖复位装载（DR-14）——立即 status 会撞复位
            # 窗口（板断链 ~10s 重连；d8_client 同型 boot-wait 时序）。先试
            # 后等轮询至板回来（NV-1 真机实证竞态：立即核验 Timeout 误报
            # 部署失败而部署实际已确认——DB PASS + APP 运行单迹）。
            status_after = None
            deadline = time.monotonic() + REBOOT_WAIT_S
            while time.monotonic() < deadline:
                try:
                    status_after = net_deploy.status(svc, n, c)
                    break
                except Exception:  # noqa: BLE001 —— 板复位中，2s 后重试
                    time.sleep(REBOOT_RETRY_S)
            if status_after is None:
                msg = f"部署已确认但板 {REBOOT_WAIT_S:.0f}s 内未回来（status 核验超时）"
                raise TaError(TA_E_TSAP, msg, domain="app_deploy",
                              detail={"deploy": deployed})
            return {"node": n, "cube": c, "deploy": deployed,
                    "status_after": status_after}

    out = await asyncio.to_thread(work)
    if not out["deploy"].get("confirmed"):
        msg = "部署未确认（activate/get-app 回读不一致）"
        raise TaError(TA_E_TSAP, msg, domain="app_deploy", detail=out["deploy"])
    log(f"deployed + confirmed: {out['node']}/{out['cube']}")
    return out
