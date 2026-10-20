# SPDX-License-Identifier: Apache-2.0
"""审批代理（LLD-A01 §4 / LLD-A02 §3）：strict 类工具挂起 → sys_pending_approvals
呈现 → sys_approve（token 校验，防其他 MCP 客户端代批，DEC-38 #7）→ 放行/拒绝。"""

from __future__ import annotations

import asyncio
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from tessera_agent.common.errors import TA_E_APPROVAL_DENIED, TA_E_ARGS, TaError

# 来源: DEC-38 #4——审批等待超时 10 min（超时自动 deny）
APPROVAL_WAIT_S = 600
APPROVAL_TOKEN_ENV = "TESSERA_AGENT_APPROVAL_TOKEN"


@dataclass
class Approval:
    id: str
    tool: str
    args_preview: dict[str, Any]
    reason: str
    created_at: float = field(default_factory=time.monotonic)
    event: asyncio.Event = field(default_factory=asyncio.Event)
    decision: str | None = None  # allow / deny

    def snapshot(self) -> dict[str, Any]:
        return {
            "approval_id": self.id,
            "tool": self.tool,
            "args_preview": self.args_preview,
            "reason": self.reason,
            "created_at": self.created_at,
            "expires_in_s": max(0, APPROVAL_WAIT_S - (time.monotonic() - self.created_at)),
        }


class ApprovalBroker:
    def __init__(self, bus: Any | None = None) -> None:
        self._pending: dict[str, Approval] = {}
        # D4（DEC-67③）：allow-session 会话域记住集（进程生命周期、不落盘
        # ——codex ReviewDecision::ApprovedForSession 同型；审批疲劳缓释）
        self._session_allowed: set[str] = set()
        # W2（LLD-A14 §3.2）：可选事件总线——approval.requested/decided 事件
        self._bus = bus

    def attach_bus(self, bus: Any) -> None:
        self._bus = bus

    def _publish(self, kind: str, a: Approval, **extra: Any) -> None:
        if self._bus is None:
            return
        try:
            self._bus.publish(kind, {"approval_id": a.id, "tool": a.tool, **extra})
        except Exception:  # noqa: BLE001
            pass

    @staticmethod
    def token_configured() -> bool:
        return bool(os.environ.get(APPROVAL_TOKEN_ENV))

    def request(self, tool: str, args_preview: dict[str, Any], reason: str) -> Approval:
        approval = Approval(
            id=f"a-{secrets.token_hex(6)}",
            tool=tool,
            args_preview=args_preview,
            reason=reason,
        )
        if tool in self._session_allowed:
            approval.decision = "allow"  # 会话域已记住——自动放行（零挂起）
            approval.event.set()
        self._pending[approval.id] = approval
        if approval.decision != "allow":
            self._publish("approval.requested", approval,
                          reason=approval.reason,
                          args_preview=args_preview,
                          expires_in_s=max(0, APPROVAL_WAIT_S
                                           - (time.monotonic()
                                              - approval.created_at)))
        return approval

    async def wait(self, approval: Approval, timeout_s: int = APPROVAL_WAIT_S) -> str:
        """等待决定；超时自动 deny（LLD-A01 §4）。"""
        try:
            await asyncio.wait_for(approval.event.wait(), timeout=timeout_s)
        except TimeoutError:
            approval.decision = "deny"
            self._publish("approval.decided", approval, decision="deny",
                          expired=True)
        self._pending.pop(approval.id, None)
        if approval.decision != "allow":
            msg = f"审批拒绝/超时: {approval.tool}（{approval.reason}）"
            raise TaError(
                TA_E_APPROVAL_DENIED,
                msg,
                domain="approvals",
                detail={"approval_id": approval.id, "decision": approval.decision},
            )
        return "allow"

    def list_pending(self) -> list[dict[str, Any]]:
        return [a.snapshot() for a in self._pending.values()]

    def decide(self, approval_id: str, decision: str, token: str) -> dict[str, Any]:
        expected = os.environ.get(APPROVAL_TOKEN_ENV, "")
        if not expected or not secrets.compare_digest(token, expected):
            msg = "审批 token 无效或未配置（宿主环境变量 TESSERA_AGENT_APPROVAL_TOKEN）"
            raise TaError(TA_E_ARGS, msg, domain="approvals")
        approval = self._pending.get(approval_id)
        if approval is None:
            msg = f"审批请求不存在或已决: {approval_id}"
            raise TaError(TA_E_ARGS, msg, domain="approvals", detail={"approval_id": approval_id})
        if decision not in ("allow", "deny", "allow-session"):
            msg = "decision 必须为 allow/allow-session/deny: " + str(decision)
            raise TaError(TA_E_ARGS, msg, domain="approvals")
        approval.decision = "allow" if decision == "allow-session" else decision
        if decision == "allow-session":
            self._session_allowed.add(approval.tool)
        approval.event.set()
        self._publish("approval.decided", approval, decision=decision,
                      expired=False)
        return {"approval_id": approval_id, "decision": decision}
