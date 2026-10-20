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

from pydantic import BaseModel
from pydantic_ai import Agent

from tessera_agent.common.errors import TA_E_POLICY, TaError
from tessera_agent.domain import app_chain
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
    "questions 返回空列表。全部用中文。"
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


class ClarifyQuestion(BaseModel):
    question: str
    options: list[str]
    default: str | None = None


class GapAnalysis(BaseModel):
    understood: str
    questions: list[ClarifyQuestion]


class SpecDraft(BaseModel):
    spec: str



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

        # ③ spec 合成 + ④ 门（一次修复重合成）
        spec_agent = Agent(m, output_type=SpecDraft, retries=OUTPUT_RETRIES,
                           system_prompt=_SPEC_SYSTEM)
        synth_prompt = (f"原始需求：{requirement}\n澄清问答：\n"
                        + "\n".join(f"问：{a}\n答：{b}" for a, b in qa))
        spec = (await spec_agent.run(synth_prompt)).output.spec
        gate = spec_gate.check_spec(spec)
        repairs = 0
        while not gate.ok and repairs < SPEC_REPAIR_MAX:
            repairs += 1
            log(f"[clarify] spec 门未过（{'; '.join(gate.errors)}）——修复重合成")
            spec = (await spec_agent.run(
                synth_prompt + "\n上一版需求单未过检查，错误："
                + "; ".join(gate.errors)
                + "\n请修正后重新输出完整需求单。")).output.spec
            gate = spec_gate.check_spec(spec)
        if not gate.ok:
            raise TaError(
                TA_E_POLICY,
                "澄清产物未过需求单检查：" + "; ".join(gate.errors),
                domain="clarify",
                detail={"errors": gate.errors, "state": "SPEC_REJECTED"})
        log(f"[clarify] 需求单过门（判据 {len(gate.pass_patterns)} 条）")
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
                         "spec": spec, "understood": understood}
    return result
