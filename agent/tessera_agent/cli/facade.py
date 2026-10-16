# SPDX-License-Identifier: Apache-2.0
"""TerminalFrontend（LLD-A09 §2-§4——Frontend 第二实现，与 MCP 门面同根）。

交互钩子注入式：plan_confirm / question / approval 三回调默认走终端
（input/getpass），测试注入剧本——交互逻辑与渲染/IO 分离（测试面最大化）。
驱动对象 = CreationLoop（AG3）；PydanticAI runner 接线随 AG6。
"""

from __future__ import annotations

import getpass
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tessera_agent.cli.render import render_event, render_final
from tessera_agent.creation.loop import CreationLoop, LoopResult, PlanItem
from tessera_agent.creation.verifier import CreationVerifier
from tessera_agent.creation.workspace import Workspace

PlanConfirmFn = Callable[[list[PlanItem]], bool]
QuestionFn = Callable[[str, list[str]], str]
ApprovalFn = Callable[[str, str, str], tuple[str, str]]  # (id, tool, reason) → (decision, token)
EmitFn = Callable[[str], None]


@dataclass
class TerminalOptions:
    yes: bool = False
    json_mode: bool = False
    plan_confirm: bool = True


ABORTED = "ABORTED"  # 门面级终态：owner 在计划确认处拒绝（LLD-A09 §4）
INTERRUPTED = "INTERRUPTED"  # 门面级终态：SIGINT 优雅退出（快照续跑——LLD-A09 §4）


class _Aborted(Exception):
    """计划确认被拒——按 LLD-A09 语义终止会话（不产出）。"""


class TerminalFrontend:
    """终端门面：事件渲染（行式/--json）+ 三交互点 + 终报。"""

    def __init__(
        self,
        *,
        plan_confirm_fn: PlanConfirmFn | None = None,
        question_fn: QuestionFn | None = None,
        approval_fn: ApprovalFn | None = None,
        emit: EmitFn = print,
    ) -> None:
        self._plan_confirm_fn = plan_confirm_fn
        self._question_fn = question_fn
        self._approval_fn = approval_fn
        self._emit = emit

    # ---- 内部 ------------------------------------------------------------

    def _out(self, kind: str, data: dict[str, Any]) -> None:
        if self._json_line(kind, data):
            return
        text = render_event(kind, data)
        if text is not None:
            self._emit(text)

    def _json_line(self, kind: str, data: dict[str, Any]) -> bool:
        if not getattr(self, "_json_mode", False):
            return False
        self._emit(json.dumps({"event": kind, **data}, ensure_ascii=False))
        return True

    def _default_plan_confirm(self, items: list[PlanItem]) -> bool:
        from tessera_agent.cli.render import render_plan

        self._emit("【计划确认】")
        self._emit(render_plan([
            {"id": i.id, "desc": i.desc, "status": i.status} for i in items
        ]))
        ans = input("确认执行此计划？[Y/n] ").strip().lower()
        return ans in ("", "y", "yes")

    def _default_question(self, question: str, options: list[str]) -> str:
        self._emit(f"【问询】{question}")
        for i, opt in enumerate(options, start=1):
            self._emit(f"  {i}. {opt}")
        raw = input(f"选择 [1-{len(options)}]（默认 1）: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        return options[0]

    def _default_approval(self, approval_id: str, tool: str, reason: str) -> tuple[str, str]:
        self._emit(f"【审批请求】{tool}（{reason}）[{approval_id}]")
        decision = input("允许？[y/N] ").strip().lower()
        if decision not in ("y", "yes"):
            return ("deny", "")
        token = getpass.getpass("审批 token: ")
        return ("allow", token)

    # ---- 对外（AG6 接线问询/审批时复用；AG4 起计划确认已生效） ----------

    def ask_question(self, question: str, options: list[str], *, yes: bool) -> str:
        if yes:
            return options[0]
        fn = self._question_fn or self._default_question
        return fn(question, options)

    def resolve_approval(
        self, approval_id: str, tool: str, reason: str, *, yes: bool
    ) -> tuple[str, str]:
        if yes:
            return ("deny", "")  # --yes 不豁免 strict（安全默认——LLD-A09 §3）
        fn = self._approval_fn or self._default_approval
        return fn(approval_id, tool, reason)

    # ---- 主驱动 ------------------------------------------------------------

    async def resume(
        self,
        spec: str,
        ws: Workspace,
        verifier: CreationVerifier,
        runner: Any,
        snap: dict[str, Any],
        *,
        options: TerminalOptions | None = None,
        budget: int = 12,
        key_path: str | None = None,
    ) -> LoopResult:
        """断点续跑（AG6 · LLD-A09 §3 --resume）：快照重建后同 run() 驱动。"""
        from tessera_agent.creation.loop import CreationLoop
        from tessera_agent.creation.snapshot import restore

        opts = options or TerminalOptions()
        self._json_mode = opts.json_mode
        loop = CreationLoop(
            ws, verifier, runner, spec,
            criteria=list(snap.get("criteria", [])), budget=budget,
            key_path=key_path, on_event=self._on_event(opts),
        )
        restore(loop, snap)
        return await self._drive(loop)

    async def _drive(self, loop: CreationLoop) -> LoopResult:
        self._loop = loop  # S8（P1-5）：修复轮再入（deploy 判据 miss 回注）
        try:
            result = await loop.run()
        except _Aborted as exc:
            result = LoopResult(
                state=ABORTED, rounds_used=loop.round, plan=loop.plan,
                workspace=str(loop.ws.root), failure_reason=str(exc),
            )
        except KeyboardInterrupt:
            # SIGINT：快照已随轮末落盘（loop._snapshot）；此处优雅汇报续跑路径
            from tessera_agent.creation import snapshot as _snap

            try:
                _snap.take(loop)
            except Exception:  # noqa: BLE001——中断路径的快照失败不掩盖主信号
                pass
            result = LoopResult(
                state=INTERRUPTED, rounds_used=loop.round, plan=loop.plan,
                workspace=str(loop.ws.root),
                failure_reason=f"中断（--resume {loop.ws.root.name} 续跑）",
            )
        self._report(result)
        return result

    async def run(
        self,
        spec: str,
        ws: Workspace,
        verifier: CreationVerifier,
        runner: Any,
        *,
        options: TerminalOptions | None = None,
        criteria: list[str] | None = None,
        scenario: dict[str, Any] | None = None,
        budget: int = 12,
        key_path: str | None = None,
    ) -> LoopResult:
        opts = options or TerminalOptions()
        self._json_mode = opts.json_mode
        loop = CreationLoop(
            ws, verifier, runner, spec,
            criteria=criteria, scenario=scenario, budget=budget,
            key_path=key_path,
            on_event=self._on_event(opts),
        )
        return await self._drive(loop)

    async def repair(self, evidence: str, *, reason: str = "deploy") -> LoopResult:
        """S8（P1-5 · HLD-agent §4）：部署判据 miss → 诊断证据回注修复轮
        （loop.repair 驱动 + 终报；CLI --deploy 闭环消费）。"""
        loop = getattr(self, "_loop", None)
        if loop is None:
            raise RuntimeError("无活动创作循环（先 run）")
        result = await loop.repair(evidence, reason=reason)
        self._report(result)
        return result

    def _report(self, result: LoopResult) -> None:
        """终报（LLD-A09 §4）：--json = 结构化行；文本 = render_final。"""
        if getattr(self, "_json_mode", False):
            self._emit(json.dumps({
                "event": "report",
                "state": result.state,
                "rounds": result.rounds_used,
                "package": result.artifact.package_path
                if result.artifact is not None and result.artifact.ok else None,
                "workspace": result.workspace,
                "failure_reason": result.failure_reason,
            }, ensure_ascii=False))
            return
        self._emit(render_final(result))

    def _on_event(self, opts: TerminalOptions) -> Callable[[str, dict[str, Any]], None]:
        confirmed = {"plan": False}

        def handler(kind: str, data: dict[str, Any]) -> None:
            self._out(kind, data)
            if kind == "plan" and opts.plan_confirm and not confirmed["plan"]:
                confirmed["plan"] = True
                items = [PlanItem(i["id"], i["desc"], i["status"])
                         for i in data.get("items", [])]
                fn = self._plan_confirm_fn or self._default_plan_confirm
                if not opts.yes and not fn(items):
                    raise _Aborted("计划被拒绝")

        return handler

    def aborted(self, result_note: str) -> str:
        return f"会话终止：{result_note}（工作区保留，快照续跑随 AG5）"
