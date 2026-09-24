# SPDX-License-Identifier: Apache-2.0
"""接口缝预留（LLD-A07 §4/§5）：A2A PeerTransport 与 Frontend 抽象。

V1 仅协议定义 + 打桩可运行（编译级冒烟）；实现属未来 Q——
- PeerTransport（DEC-36④ A2A 预留，owner 要求显式登记）：启用条件 = 跨主体/
  长周期对等任务（Galatea 规模）；默认多域组合 = 上层编排 + 域 agent 各自 MCP 面。
- Frontend（DEC-35 ACP 预留）：V1 唯一实现 = MCP 门面；后补 ACP 适配模块
  （acp_frontend.py + 子进程入口）不改编排/域层。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PeerTransport(Protocol):
    """A2A 接入缝（旁挂 SessionOrchestrator，不侵入编排主链）。"""

    def serve_agent_card(self) -> dict[str, Any]:
        """生成 Agent Card（能力 = 本域工具面清单，DomainPack.tools）。"""
        ...  # pragma: no cover

    async def delegate_task(self, peer: str, payload: dict[str, Any]) -> dict[str, Any]:
        """对等任务委托（跨主体场景；V1 不实现）。"""
        ...  # pragma: no cover


@runtime_checkable
class Frontend(Protocol):
    """人机前端抽象（V1 实现 = MCP 门面；ACP 适配器后补）。"""

    def render_log(self, line: str) -> None:
        ...  # pragma: no cover

    def render_pending_approvals(self, pending: list[dict[str, Any]]) -> None:
        ...  # pragma: no cover


class McpFrontend:
    """V1 唯一 Frontend 实现：任务日志行 + 待审批呈现（LLD-A02 §1）。"""

    def __init__(self, log_fn=print) -> None:
        self._log = log_fn

    def render_log(self, line: str) -> None:
        self._log(line)

    def render_pending_approvals(self, pending: list[dict[str, Any]]) -> None:
        for p in pending:
            self._log(f"[approval] {p}")
