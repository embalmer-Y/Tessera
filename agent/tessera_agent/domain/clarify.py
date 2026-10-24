# SPDX-License-Identifier: Apache-2.0
"""需求澄清域（W2 · LLD-A14 §5.1——DEC-69⑥ 双模式之普通模式）。

创作循环的**前置阶段**：LLM 驱动但产物过确定性门（NV-2 spec_check）——
与 CreationLoop 同族定性（LLM 提议澄清轮与问询选项；门与判据派生零
改动，如实注记）。五步：① 缺口分析 → ② 澄清轮（QuestionBroker 问询
卡，轮 ≤3/问 ≤8——防循环）→ ③ spec 合成 → ④ spec_check 门（不过 =
一次修复重合成）→ ⑤ 确认（proceed → 交棒 app_develop 同任务句柄 /
restart → 结构化中止——D7 plan_confirm abort 同型）。

失败语义（LLD-A14 §5.1）：LLM 不可用 → 结构化错误（提示切换开发者
模式直填 spec）；门硬伤修复后仍不过 → 如实返回 errors 不静默降级。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from tessera_agent.common.errors import TA_E_POLICY, TaError
from tessera_agent.domain import app_chain
from tessera_agent.domain import hardware as hwdom
from tessera_agent.domain.app_chain import OUTPUT_RETRIES

# 来源: LLD-A14 §5.1——澄清防循环闸
CLARIFY_ROUNDS_MAX = 3
CLARIFY_QUESTIONS_MAX = 8
SPEC_REPAIR_MAX = 1

_FOUR_SECTIONS = "【需求】【资源】【判据】【安全声明】"

_GAP_SYSTEM = (
    "你是嵌入式设备应用的需求澄清助手。用户会给出一段粗糙的需求描述，"
    "你要：① 用一句话复述你的理解（understood）；② 列出为形成正式需求单"
    "（四节模板：" + _FOUR_SECTIONS + "）仍需澄清的问题——每题给 2-4 个候选"
    "选项与缺省项，让用户点选即可回答。只问真正影响实现与验收的问题"
    "（尤其【判据】节：设备上要观察到什么可验证的行为）；需求已清晰则"
    "questions 返回空列表。③ hardware_mention = 用户在需求文本中**明确提到**"
    "的目标板卡/硬件型号（如「ATK DNESP32-S3」「XIAO ESP32-S3」）；"
    "未提到就留空字符串——严禁猜测或编造型号。全部用中文。"
)

_SPEC_SYSTEM = (
    "你是 Tessera 平台的需求单撰写助手。依据用户原始需求与澄清问答，"
    "写出一份正式四节需求单（" + _FOUR_SECTIONS + "）：\n"
    "【需求】一段话说明应用做什么；\n"
    "【资源】用到的设备能力（gpio/adc/pwm/i2s/kv/log 等，没有则写「无特殊资源」）；\n"
    "【判据】验收检查——一行一条引号串（设备运行日志中将逐字出现的行，"
    "例如 \"HEALTH OK 60s\"），至少一条，必须是设备运行时可观察的确定性行；\n"
    "【安全声明】说明该应用不做什么危险动作（不动安全输出/不写持久存储等）。\n"
    "只输出需求单全文，不要额外解释。全部用中文。"
)

# HW-3（LLD-A16 §3）：联网选型调研 agent——候选 ≤5 结构化，检索走 search_web
# 工具（Tavily keyless）；内存/Zephyr 收录判定由机械预筛完成（LLM 只做语义）。
_RESEARCH_SYSTEM = (
    "你是嵌入式板卡选型调研助手。依据需求要点（必要时用 search_web 工具检索"
    "「板卡型号 + Zephyr support + 外设规格」），给出最多 5 个候选板卡。"
    "每个候选字段：model（精确型号串）、soc、ram_kb、psram_kb（KB 数值，"
    "未知填 0）、peripherals、price_band、zephyr_supported（true/false/null）、"
    "source_urls、notes。候选须可采购的量产板卡，禁止自造型号。全部用中文。"
)


class ClarifyQuestion(BaseModel):
    question: str
    options: list[str]
    default: str | None = None


class GapAnalysis(BaseModel):
    understood: str
    questions: list[ClarifyQuestion]
    # HW-1（LLD-A16 §1①）：需求文本中明确提到的目标板卡型号（未提 = 空）
    hardware_mention: str = ""


class SpecDraft(BaseModel):
    spec: str


class BoardCandidate(BaseModel):
    model: str
    soc: str = ""
    ram_kb: int = 0
    psram_kb: int = 0
    peripherals: str = ""
    price_band: str = ""
    zephyr_supported: bool | None = None
    source_urls: list[str] = Field(default_factory=list)
    notes: str = ""


class ResearchOut(BaseModel):
    candidates: list[BoardCandidate] = Field(default_factory=list)



def resolve_key_path(ctx: Any, key_path: str | None) -> str:
    """私钥缺省发现（普通模式不应要求用户懂私钥——DEC-69⑥；CLI 同款
    规则：缺省查 <workspace>/agent/keys/*.key 首个；找不到 = 结构化错）。"""
    if key_path:
        return key_path
    from pathlib import Path

    keys_dir = Path(ctx.cfg.workspace_repo) / "agent" / "keys"
    cands = sorted(keys_dir.glob("*.key")) if keys_dir.is_dir() else []
    if cands:
        return str(cands[0])
    raise TaError(
        TA_E_POLICY,
        "未找到签名私钥（设置抽屉「签名私钥路径」或 agent/keys/*.key）",
        domain="clarify", detail={"state": "KEY_NOT_FOUND"})


# ---- HW-1/HW-3：S0 硬件定向槽（LLD-A16 §1——问询驱动，无静默假设）-----------

_HW_ASK_OTHER = "其他板卡"
_HW_ASK_RESEARCH = "帮我联网选型"
_HW_ASK_SKIP = "暂不指定"


def _match_catalog(hint: str, ids: list[str]) -> str | None:
    """需求提及型号 ↔ 画像目录匹配（归一化双向子串——「ATK DNESP32-S3B」
    ↔「dnesp32s3b」同族形态可中）；恰一命中才绑定，多命中/零命中
    = None（零命中走分支 B 收录检查）。"""
    hits = [i for i in ids
            if hwdom._norm(i) in hwdom._norm(hint)
            or hwdom._norm(hint) in hwdom._norm(i)]
    return hits[0] if len(hits) == 1 else None


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


async def _ask(ctx: Any, task: Any, question: str, options: list[str],
               default: str | None, context: str, log: Any) -> str:
    """问询卡同步等待（D7 面）；问答行入日志（历史回放重建消费同格式）。"""
    q = ctx.questions.ask(question, options, default=default, context=context)
    task.state = "input_required"
    try:
        ans = await ctx.questions.wait(q)
    finally:
        task.state = "working"
    log(f"[clarify] 问答：{question.splitlines()[0]} → {ans}")
    return ans


async def _web_verify_note_async(ctx: Any, hint: str) -> str:
    """分支 B 联网核实（异步原语；失败 = 空注记——本地结论仍成立）。"""
    try:
        from tessera_agent.gateway.websearch import get_search_provider
        prov = get_search_provider(ctx.cfg)
        results = await prov.search(f"Zephyr RTOS {hint} board support",
                                    max_results=3)
        return "\n".join(f"- {r['title']}: {r['snippet'][:120]}"
                         for r in results)
    except Exception:  # noqa: BLE001
        return ""


async def _research_boards(ctx: Any, requirement: str, task: Any, *,
                           model: Any, log: Any) -> dict:
    """HW-3 联网选型调研（LLD-A16 §3）：结构化候选 ≤5 → 机械预筛（内存
    口径）→ 候选问询卡 → 用户选定（推定态记录）。"""
    from tessera_agent.domain import hardware as hwdom

    agent = Agent(model, output_type=ResearchOut, retries=OUTPUT_RETRIES,
                  system_prompt=_RESEARCH_SYSTEM)

    @agent.tool_plain
    async def search_web(query: str) -> str:
        """联网搜索板卡资料（Tavily keyless；查询词凭据打码后发出）。"""
        from tessera_agent.gateway.websearch import get_search_provider, scrub_query
        try:
            prov = get_search_provider(ctx.cfg)
            results = await prov.search(query, max_results=5)
        except Exception as exc:  # noqa: BLE001 —— 搜索不可用如实回传
            return f"（搜索不可用：{type(exc).__name__}: {exc}）"
        lines = [f"- {r['title']}: {r['snippet'][:200]}（{r['url']}）"
                 for r in results]
        scrubbed = scrub_query(query)
        return "\n".join(lines) if lines else f"（无结果：{scrubbed}）"

    log("[clarify] 联网选型调研…")
    out = (await agent.run(
        f"需求要点：{requirement}\n请给出候选板卡（≤5，宁缺毋滥）。")).output
    cands = [c.model_dump() for c in out.candidates[:5]]
    kept, dropped = hwdom.prefilter_candidates(cands)
    for d in dropped:
        log(f"[clarify] 候选剔除（内存预筛）：{d['model']}——{d['reason']}")
    if not kept:
        raise TaError(
            TA_E_POLICY,
            "联网选型候选全部被机械预筛剔除（内存口径）——请补充需求要点"
            "或更换候选来源",
            domain="clarify", detail={"state": "NO_CANDIDATE",
                                      "dropped": dropped})
    rows = "\n".join(
        f"{i+1}. {c['model']}（{c.get('soc') or '?'}；ram={c.get('ram_kb', 0)}"
        f"KB+psram={c.get('psram_kb', 0)}KB；zephyr="
        + ("是" if c.get("zephyr_supported") else
           "否" if c.get("zephyr_supported") is False else "未知") + "）"
        for i, c in enumerate(kept))
    options = [str(c["model"]) for c in kept] + ["都不合适（中止）"]
    ans = await _ask(
        ctx, task,
        f"联网选型候选（推定态——采购与板卡验证前不做能力承诺）：\n{rows}\n"
        "请选择目标板卡：", options, default=options[0],
        context="app_clarify 联网选型", log=log)
    if ans.startswith("都不合适"):
        raise TaError(TA_E_POLICY, "用户否决全部选型候选",
                      domain="clarify", detail={"state": "RESEARCH_REJECTED"})
    sel = next(c for c in kept if str(c["model"]) == ans)
    return {"mode": "research", "board": ans, "candidate": sel,
            "presumed": True, "dropped": dropped}


async def _hw_section_text(rec: dict, profile: Any) -> str:
    """定向记录 → spec【目标硬件】段文本（HW-4 §7.2 注入面）。"""
    from tessera_agent.domain import hardware as hwdom

    if rec["mode"] == "profile" and profile is not None:
        return hwdom.hardware_facts_brief(profile)
    if rec["mode"] == "research":
        c = rec.get("candidate") or {}
        z = c.get("zephyr_supported")
        return ("联网选型（推定态——采购与板卡验证前不做能力承诺）："
                f"model={rec['board']}"
                + (f"；soc={c['soc']}" if c.get("soc") else "")
                + f"；ram={c.get('ram_kb', 0)}KB+psram={c.get('psram_kb', 0)}KB"
                + ("；zephyr 收录=" + ("是" if z else
                                      "否" if z is False else "未知"))
                + "；未采购未验证——禁止假设任何通道与板载外设的对应关系")
    return ("用户暂未指定目标硬件——部署前需指定；禁止假设任何通道与板载"
            "外设的对应关系（无事实支撑的 caps 申请会被部署门装前拒绝或"
            "运行期写拒）")


async def _hardware_targeting(ctx: Any, requirement: str, gap: GapAnalysis,
                              task: Any, *, model: Any, log: Any,
                              ask_main: bool = True) -> tuple[dict, Any]:
    """S0 槽（LLD-A16 §1①②）：返回（定向记录, 绑定画像|None）。
    mention→目录内绑定（A）/ 其他板卡→Zephyr 收录检查（B：收录=BV2 工单 /
    未收录=原理图协作）/ 未提及→主问询（A/B/C/暂不指定）。"""
    from tessera_agent.domain import hardware as hwdom

    cat = hwdom.catalog_ids(ctx.cfg)
    hint = (gap.hardware_mention or "").strip()

    if hint:
        bound = _match_catalog(hint, cat)
        if bound is not None:
            log(f"[clarify] 硬件定向：需求提及 {hint} → 目录绑定 {bound}")
            return ({"mode": "profile", "board": bound, "via": "mention"},
                    hwdom.load_profile(
                        hwdom.boards_dir(ctx.cfg) / f"{bound}.toml"))
        z = hwdom.check_zephyr_inclusion(hint, ctx.cfg.west_workspace)
        web = await _web_verify_note_async(ctx, hint)
        if web:
            log(f"[clarify] Zephyr 收录联网核实：\n{web[:300]}")
        if z["included"]:
            ans = await _ask(
                ctx, task,
                f"「{hint}」为 Zephyr 收录板（本地命中："
                f"{', '.join(z['matches'])}），但不在本机画像目录——需 BV2 "
                "新板适配（移植接入件 + bring-up 验证）后方可部署。如何继续？",
                ["入 BV2 适配队列（生成本次工单后中止）", "改选目录内板卡",
                 _HW_ASK_RESEARCH],
                default="改选目录内板卡" if cat else
                "入 BV2 适配队列（生成本次工单后中止）",
                context="app_clarify 硬件定向（Zephyr 收录板）", log=log)
            if ans.startswith("入 BV2"):
                raise TaError(
                    TA_E_POLICY,
                    f"已入 BV2 新板适配队列（board={hint}）——适配完成后"
                    "画像入目录即可直接使用",
                    domain="clarify",
                    detail={"state": "BV2_QUEUED", "board": hint,
                            "zephyr_matches": z["matches"]})
        else:
            ans = await _ask(
                ctx, task,
                f"「{hint}」未在 Zephyr 收录中命中——自定义板移植需要您提供"
                "原理图/引脚表（人机协作：Agent 出移植清单与风险点，您供图"
                "定案）。如何继续？",
                ["我提供原理图（中止并记录协作清单）", "改选目录内板卡",
                 _HW_ASK_RESEARCH],
                default="改选目录内板卡" if cat else
                "我提供原理图（中止并记录协作清单）",
                context="app_clarify 硬件定向（未收录板）", log=log)
            if ans.startswith("我提供原理图"):
                raise TaError(
                    TA_E_POLICY,
                    "自定义板移植待原理图——请提供原理图/引脚表后重新发起"
                    "（协作清单见任务日志）",
                    domain="clarify",
                    detail={"state": "SCHEMATIC_REQUIRED", "board": hint,
                            "checklist": ["原理图/PDF 或引脚表",
                                          "供电与调试口",
                                          "外设清单（屏幕/音频/传感器）"]})
        if ans.startswith("改选"):
            pass  # 落到主问询
        elif ans == _HW_ASK_RESEARCH:
            rec = await _research_boards(ctx, requirement, task, model=model,
                                         log=log)
            return rec, None
        else:  # pragma: no cover —— 选项集闭合
            raise TaError(TA_E_POLICY, "硬件定向选项异常",
                          domain="clarify", detail={"answer": ans})

    if not ask_main:
        return {"mode": "skipped", "board": "", "via": "default"}, None
    options = list(cat) + [_HW_ASK_OTHER, _HW_ASK_RESEARCH, _HW_ASK_SKIP]
    log("[clarify] 硬件定向：需求未指明目标硬件——提醒用户指定")
    ans = await _ask(
        ctx, task,
        "需求未指明目标硬件——您是否有现成的目标板卡？（目录内可直接绑定；"
        "其他板卡将检查 Zephyr 收录；也可以由我联网选型）",
        options, default=_HW_ASK_SKIP,
        context="app_clarify 硬件定向", log=log)
    if ans in (_HW_ASK_OTHER, _HW_ASK_RESEARCH):
        if ans == _HW_ASK_RESEARCH:
            rec = await _research_boards(ctx, requirement, task, model=model,
                                         log=log)
            return rec, None
        # 其他板卡但需求未提型号——枚举域内给出诚实路径
        ans2 = await _ask(
            ctx, task,
            "请提供板卡型号（当前问询卡不支持自由文本——可在需求文本中写明"
            "型号后重新发起，或走以下路径）：",
            ["改为联网选型", "暂不指定"],
            default="暂不指定", context="app_clarify 硬件定向（其他板卡）",
            log=log)
        if ans2 == "改为联网选型":
            rec = await _research_boards(ctx, requirement, task, model=model,
                                         log=log)
            return rec, None
        return {"mode": "skipped", "board": "", "via": "other"}, None
    if ans in cat:
        return ({"mode": "profile", "board": ans, "via": "ask"},
                hwdom.load_profile(hwdom.boards_dir(ctx.cfg) / f"{ans}.toml"))
    return {"mode": "skipped", "board": "", "via": "answer"}, None


async def clarify_and_develop(
    ctx: Any,
    requirement: str,
    task: Any,
    key_path: str,
    out_dir: str = "agent/build",
    *,
    model: Any = None,
    log: Any = None,
) -> dict[str, Any]:
    """普通模式入口：澄清五步 → 过门确认 → 交棒 app_develop（同任务句柄
    ——进度/日志/任务栏全程连续）。返回键 = app_develop 结果 +
    additive clarify 块（rounds/questions_asked/spec）。"""
    from tessera_agent.tools_diag import spec_gate

    log = log or (lambda s: None)
    m = model or ctx.cfg.default_model
    rounds = 0
    asked = 0
    qa: list[tuple[str, str]] = []
    understood = ""

    def note_progress(patch: dict[str, Any]) -> None:
        ctx.registry.note_progress(task, patch)

    try:
        note_progress({"loop_state": "clarify"})
        # W2 验收修复⑤：需求原文入日志（历史回放重建气泡的数据源）
        log(f"[clarify] 需求：{requirement}")
        # ① 缺口分析
        gap_agent = Agent(m, output_type=GapAnalysis, retries=OUTPUT_RETRIES,
                          system_prompt=_GAP_SYSTEM)
        log("[clarify] 缺口分析…")
        gap = (await gap_agent.run(requirement)).output
        understood = gap.understood
        log(f"[clarify] 理解：{understood}")

        # ② 澄清轮（问询卡——D7 面；restart 语义见 ⑤）
        for _ in range(CLARIFY_ROUNDS_MAX):
            batch = gap.questions[: CLARIFY_QUESTIONS_MAX - asked]
            if not batch:
                break
            for cq in batch:
                options = list(dict.fromkeys(
                    ([cq.default] if cq.default else []) + list(cq.options)))
                q = ctx.questions.ask(cq.question, options,
                                      default=cq.default,
                                      context="app_clarify 需求澄清")
                task.state = "input_required"
                try:
                    ans = await ctx.questions.wait(q)
                finally:
                    task.state = "working"
                asked += 1
                qa.append((cq.question, ans))
                log(f"[clarify] 问答：{cq.question} → {ans}")
            # 追问轮：依已答更新缺口
            follow_prompt = (f"原始需求：{requirement}\n已澄清问答：\n"
                             + "\n".join(f"问：{a}\n答：{b}" for a, b in qa)
                             + "\n仍需澄清的问题（无则空列表）：")
            gap = (await gap_agent.run(follow_prompt)).output
            rounds += 1

        # ②b S0 硬件定向槽（HW-1 · LLD-A16 §1——问询驱动，无静默假设）：
        # 需求分析先行（①与本硬件无关），此处才问板卡。
        hw_rec, hw_profile = await _hardware_targeting(
            ctx, requirement, gap, task, model=m, log=log)
        hw_section = await _hw_section_text(hw_rec, hw_profile)
        note_progress({"loop_state": "hw_targeted",
                       "hw_mode": hw_rec["mode"],
                       "hw_board": hw_rec.get("board", "")})

        # ③ spec 合成 + ④ 门（一次修复重合成）；【目标硬件】段 = S0 定向
        # 产物（HW-4 §7.2——合成体不携带，由本侧拼接，能力核对可整体重排）
        spec_agent = Agent(m, output_type=SpecDraft, retries=OUTPUT_RETRIES,
                           system_prompt=_SPEC_SYSTEM)
        synth_prompt = (f"原始需求：{requirement}\n澄清问答：\n"
                        + "\n".join(f"问：{a}\n答：{b}" for a, b in qa))
        spec_body = (await spec_agent.run(synth_prompt)).output.spec
        spec = spec_body.rstrip() + "\n" + hwdom.target_hw_section(hw_section) + "\n"
        gate = spec_gate.check_spec(spec)
        repairs = 0
        while not gate.ok and repairs < SPEC_REPAIR_MAX:
            repairs += 1
            log(f"[clarify] spec 门未过（{'; '.join(gate.errors)}）——修复重合成")
            spec_body = (await spec_agent.run(
                synth_prompt + "\n上一版需求单未过检查，错误："
                + "; ".join(gate.errors)
                + "\n请修正后重新输出完整需求单。")).output.spec
            spec = (spec_body.rstrip() + "\n"
                    + hwdom.target_hw_section(hw_section) + "\n")
            gate = spec_gate.check_spec(spec)
        if not gate.ok:
            raise TaError(
                TA_E_POLICY,
                "澄清产物未过需求单检查：" + "; ".join(gate.errors),
                domain="clarify",
                detail={"errors": gate.errors, "state": "SPEC_REJECTED"})
        log(f"[clarify] 需求单过门（判据 {len(gate.pass_patterns)} 条）")

        # ③b 能力核对（HW-1 · LLD-A16 §1③）：需求 caps × 画像物理绑定 →
        # 缺口问询（外接硬件/更换板卡/如实标注继续）——换板重走定向一次。
        for _ in range(2):
            if hw_rec["mode"] != "profile" or hw_profile is None:
                break
            gaps = hwdom.capability_gaps(
                spec_gate.extract_caps(spec_body), hw_profile)
            if not gaps:
                break
            ans = await _ask(
                ctx, task,
                "目标板卡能力缺口核对：\n- " + "\n- ".join(gaps)
                + "\n如何处理？",
                ["外接硬件（扩展模块）", "更换板卡",
                 "仍按此板继续（缺口如实标注）"],
                default="仍按此板继续（缺口如实标注）",
                context="app_clarify 能力核对", log=log)
            if ans.startswith("更换板卡"):
                hw_rec, hw_profile = await _hardware_targeting(
                    ctx, requirement, gap, task, model=m, log=log)
                hw_section = await _hw_section_text(hw_rec, hw_profile)
                spec = (spec_body.rstrip() + "\n"
                        + hwdom.target_hw_section(hw_section) + "\n")
                continue
            if ans.startswith("外接硬件"):
                hw_section += "；需外接硬件：" + "；".join(gaps)
            else:
                hw_section += "；能力缺口（如实标注）：" + "；".join(gaps)
            spec = (spec_body.rstrip() + "\n"
                    + hwdom.target_hw_section(hw_section) + "\n")
            break
        note_progress({"loop_state": "clarified", "clarify_rounds": rounds,
                       "clarify_asked": asked})

        # ⑤ 确认（proceed → 交棒；restart → 结构化中止）
        confirm = ctx.questions.ask(
            "需求单已生成，是否按此开始生成应用？\n" + spec,
            ["proceed", "restart"], default="proceed",
            context="app_clarify 需求单确认")
        task.state = "input_required"
        try:
            ans = await ctx.questions.wait(confirm)
        finally:
            task.state = "working"
        log(f"[clarify] 确认：{ans}")
        if ans != "proceed":
            raise TaError(
                TA_E_POLICY, "用户要求重新澄清（restart）",
                domain="clarify", detail={"state": "RESTART"})
    except TaError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise TaError(
            TA_E_POLICY,
            f"需求澄清失败（{type(exc).__name__}: {exc}）——"
            "可切换开发者模式直填四节需求单后重试",
            domain="clarify", detail={"state": "CLARIFY_FAILED"}) from exc

    # ⑥ 交棒 app_develop（同任务句柄——进度/日志连续；计划确认缺省关）
    result = await app_chain.app_develop(
        ctx, spec, key_path, out_dir, log_fn=log, task=task,
        plan_confirm=False)
    result["clarify"] = {"rounds": rounds, "questions_asked": asked,
                         "spec": spec, "understood": understood,
                         "hardware": hw_rec}
    return result
