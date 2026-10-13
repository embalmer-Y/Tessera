# SPDX-License-Identifier: Apache-2.0
"""创作循环引擎（LLD-A08 §5——域无关状态机/预算/计划/证据自动回喂）。

引擎不含任何固件语义：LLM 交互经 LoopRunner 协议注入（生产 = PydanticAI
适配器〔AG6〕；测试 = 剧本桩）；验证经 CreationVerifier 协议注入。
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from tessera_agent.creation.verifier import (
    CreationVerifier,
    PackageOutcome,
    VerifyOutcome,
)
from tessera_agent.creation.workspace import Workspace

# 状态机（LLD-A08 §5.1）
DRAFT = "DRAFT"
PLANNING = "PLANNING"
IMPLEMENTING = "IMPLEMENTING"
VERIFYING = "VERIFYING"
CONVERGED = "CONVERGED"
PACKAGED = "PACKAGED"
FAILED = "FAILED"

DEFAULT_BUDGET = 12  # LLD-A08 §5.1（轮次预算；config 化随 AG6）

EventFn = Callable[[str, dict[str, Any]], None]


@dataclass
class PlanItem:
    id: str
    desc: str
    status: str = "pending"  # pending | in_progress | done


@dataclass
class RoundOutcome:
    """implement 轮的结构化产物（runner 返回）。"""

    declared_done: bool
    summary: str = ""


class LoopRunner(Protocol):
    """LLM 适配协议：plan = 工程分解；implement = 一轮编辑（工具面由适配器闭包注入）。"""

    async def plan(self, spec: str, criteria: list[str]) -> list[PlanItem]: ...

    async def implement(self, prompt: str) -> RoundOutcome: ...


@dataclass
class LoopResult:
    state: str
    rounds_used: int
    plan: list[PlanItem]
    evidence_log: list[dict[str, Any]] = field(default_factory=list)
    artifact: PackageOutcome | None = None
    workspace: str = ""
    failure_reason: str = ""


class CreationLoop:
    """单任务创作循环。事件流：on_event(kind, data)——AG4 终端渲染/AG6 task_log 同源。"""

    def __init__(
        self,
        ws: Workspace,
        verifier: CreationVerifier,
        runner: LoopRunner,
        spec: str,
        *,
        criteria: list[str] | None = None,
        scenario: dict[str, Any] | None = None,
        budget: int = DEFAULT_BUDGET,
        key_path: str | None = None,
        on_event: EventFn | None = None,
    ) -> None:
        self.ws = ws
        self.verifier = verifier
        self.runner = runner
        self.spec = spec
        self.criteria = criteria or []
        self.scenario = scenario
        self.budget = max(1, int(budget))
        self.key_path = key_path
        self.on_event = on_event
        self.state = DRAFT
        self.round = 0
        self.plan: list[PlanItem] = []
        self.evidence_log: list[dict[str, Any]] = []

    # ---- 内部 ------------------------------------------------------------

    def _emit(self, kind: str, data: dict[str, Any]) -> None:
        if self.on_event is not None:
            self.on_event(kind, data)

    def _pending_plan_lines(self) -> list[str]:
        return [f"- [{it.status}] {it.id}: {it.desc}" for it in self.plan]

    def _assemble_prompt(self) -> str:
        """每轮用户侧消息 = spec 摘要 + 计划状态 + 上轮证据块（自动回喂核心）。"""
        parts = [
            f"【需求】{self.spec[:2000]}",
            f"【当前状态】{self.state}（第 {self.round + 1}/{self.budget} 轮）",
            "【计划】" + ("\n".join(self._pending_plan_lines()) or "（空）"),
        ]
        if self.criteria:
            parts.append("【判据】\n" + "\n".join(f'- "{c}"' for c in self.criteria))
        if self.evidence_log:
            blocks = []
            for ev in self.evidence_log[-3:]:  # 近 3 条证据（上下文预算）
                blocks.append(f"[{ev['step']}] 不通过：\n{ev['detail']}")
            parts.append("【上轮验证证据——必须修复】\n" + "\n\n".join(blocks))
        else:
            parts.append("【验证证据】尚无——完成实现后声明 done 触发验证")
        parts.append(
            "【循环纪律】用 ws_* 工具编辑工程；全部完成后才声明 declared_done；"
            "证据不通过时优先最小修复。"
        )
        return "\n\n".join(parts)

    async def _verify(self) -> list[dict[str, Any]]:
        """三步验证；返回失败证据列表（空 = 全绿）。"""
        fails: list[dict[str, Any]] = []
        for step, fn, args in (
            ("compile", self.verifier.compile, (self.ws,)),
            ("face_check", self.verifier.face_check, (self.ws,)),
        ):
            outcome: VerifyOutcome = await asyncio.to_thread(fn, *args)
            if not outcome.ok:
                fails.append({"step": step, "detail": outcome.detail,
                              "facts": outcome.facts})
        if self.scenario is not None:
            sim: VerifyOutcome = await asyncio.to_thread(
                self.verifier.simulate, self.ws, self.scenario)
            if not sim.ok:
                fails.append({"step": "simulate", "detail": sim.detail,
                              "facts": sim.facts})
        return fails

    # ---- 主流程 ----------------------------------------------------------

    def _snapshot(self) -> None:
        """状态迁移/轮末快照（AG5 · LLD-A08 §6.2——原子写；失败如实抛）。"""
        from tessera_agent.creation import snapshot

        snapshot.take(self)

    async def run(self) -> LoopResult:
        self.state = PLANNING
        self._emit("state", {"state": self.state})
        self.plan = await self.runner.plan(self.spec, self.criteria)
        self._emit("plan", {"items": [
            {"id": p.id, "desc": p.desc, "status": p.status} for p in self.plan
        ]})

        self.state = IMPLEMENTING
        self._emit("state", {"state": self.state})
        self._snapshot()
        failure_reason = ""
        while self.round < self.budget:
            prompt = self._assemble_prompt()
            outcome = await self.runner.implement(prompt)
            self.round += 1
            self._emit("round", {
                "round": self.round, "budget": self.budget,
                "declared_done": outcome.declared_done,
                "summary": outcome.summary,
            })
            self._snapshot()
            if not outcome.declared_done:
                continue
            self.state = VERIFYING
            self._emit("state", {"state": self.state})
            fails = await self._verify()
            if fails:
                self.evidence_log.extend(
                    {"round": self.round, **f} for f in fails
                )
                for f in fails:
                    self._emit("evidence", {"step": f["step"],
                                            "round": self.round})
                self.state = IMPLEMENTING
                self._emit("state", {"state": self.state})
                self._snapshot()
                continue
            self.state = CONVERGED
            self._emit("state", {"state": self.state})
            break
        else:
            failure_reason = f"轮次预算耗尽（{self.budget}）——证据归档，工作区保留"

        artifact: PackageOutcome | None = None
        if self.state == CONVERGED:
            if self.key_path:
                artifact = await asyncio.to_thread(
                    self.verifier.package, self.ws, self.key_path)
                if artifact.ok:
                    self.state = PACKAGED
                    self._emit("state", {"state": self.state,
                                         "package": artifact.package_path})
                else:
                    self.state = FAILED
                    failure_reason = f"打包失败：{artifact.detail}"
                    self.evidence_log.append(
                        {"round": self.round, "step": "package",
                         "detail": artifact.detail})
            # 无 key_path：CONVERGED 即终态（打包由外层显式触发——AG6 接线面）
        elif self.state != CONVERGED:
            self.state = FAILED
        self._emit("final", {"state": self.state, "rounds": self.round})
        return LoopResult(
            state=self.state,
            rounds_used=self.round,
            plan=self.plan,
            evidence_log=self.evidence_log,
            artifact=artifact,
            workspace=str(self.ws.root),
            failure_reason=failure_reason,
        )

    # ---- 快照面（AG5 消费；AG3 预留一致性检查） --------------------------

    def budget_exceeded(self) -> bool:
        return self.round >= self.budget
