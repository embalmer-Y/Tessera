# SPDX-License-Identifier: Apache-2.0
"""问询代理（D7 · DEC-67①：问询/审批为 MCP 一等实体——opencode permission/form
同型，LLD-agent-mcp-gateway §4 审批族的姊妹面）。

问询面 = 便利交互面：sys_answer 无 token（多渠道应答为设计意图），审计归因；
**安全边界 = strict 审批 token（DEC-38 #7 不变）**。答案枚举域内 fail-closed；
超时取 default（无 default = 超时异常——确定缺省纪律，DEC-38 #4 同型）。"""

from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from tessera_agent.common.errors import TA_E_ARGS, TA_E_TIMEOUT, TaError

# 来源: DEC-38 #4 同型——问询等待超时 10 min
QUESTION_WAIT_S = 600


@dataclass
class Question:
    id: str
    question: str
    options: list[str]
    default: str | None
    context: str | None
    created_at: float = field(default_factory=time.monotonic)
    event: asyncio.Event = field(default_factory=asyncio.Event)
    answer: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "question_id": self.id,
            "question": self.question,
            "options": list(self.options),
            "default": self.default,
            "context": self.context,
            "created_at": self.created_at,
            "expires_in_s": max(0, QUESTION_WAIT_S - (time.monotonic() - self.created_at)),
        }


class QuestionBroker:
    def __init__(self, bus: Any | None = None) -> None:
        self._pending: dict[str, Question] = {}
        # W2（LLD-agent-web-reshape §3.2）：可选事件总线——question.opened/closed 事件
        self._bus = bus

    def attach_bus(self, bus: Any) -> None:
        self._bus = bus

    def _publish(self, kind: str, q: Question, **extra: Any) -> None:
        if self._bus is None:
            return
        try:
            self._bus.publish(kind, {"question_id": q.id, **extra})
        except Exception:  # noqa: BLE001
            pass

    def ask(self, question: str, options: list[str], *,
            default: str | None = None, context: str | None = None) -> Question:
        if not options:
            raise TaError(TA_E_ARGS, "options 不能为空", domain="questions")
        if default is not None and default not in options:
            raise TaError(TA_E_ARGS, f"default 不在 options 域内: {default}",
                          domain="questions")
        q = Question(
            id=f"q-{secrets.token_hex(6)}",
            question=question,
            options=list(options),
            default=default,
            context=context,
        )
        self._pending[q.id] = q
        self._publish("question.opened", q, question=q.question,
                      options=list(options), default=default, context=context)
        return q

    async def wait(self, q: Question, timeout_s: int = QUESTION_WAIT_S) -> str:
        """等待应答；超时取 default（无 default = 超时异常，域 questions）。"""
        try:
            await asyncio.wait_for(q.event.wait(), timeout=timeout_s)
        except TimeoutError:
            self._pending.pop(q.id, None)
            self._publish("question.closed", q, answer=None, expired=True)
            if q.default is None:
                raise TaError(
                    TA_E_TIMEOUT,
                    f"问询超时且无缺省: {q.question[:60]}",
                    domain="questions",
                    detail={"question_id": q.id},
                ) from None
            return q.default
        self._pending.pop(q.id, None)
        assert q.answer is not None
        return q.answer

    def list_pending(self) -> list[dict[str, Any]]:
        return [q.snapshot() for q in self._pending.values()]

    def answer(self, question_id: str, answer: str) -> dict[str, Any]:
        q = self._pending.get(question_id)
        if q is None:
            raise TaError(
                TA_E_ARGS,
                f"问询不存在或已答: {question_id}",
                domain="questions",
                detail={"question_id": question_id},
            )
        if q.answer is not None:
            raise TaError(
                TA_E_ARGS,
                f"问询已应答（单次应答契约）: {question_id}",
                domain="questions",
                detail={"question_id": question_id, "answer": q.answer},
            )
        if answer not in q.options:
            raise TaError(
                TA_E_ARGS,
                f"answer 不在 options 域内: {answer}",
                domain="questions",
                detail={"question_id": question_id, "options": q.options},
            )
        q.answer = answer
        q.event.set()
        self._publish("question.closed", q, answer=answer, expired=False)
        return {"question_id": question_id, "answer": answer}
