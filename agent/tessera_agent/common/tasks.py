# SPDX-License-Identifier: Apache-2.0
"""长任务句柄注册表（LLD-A00 §2，DEC-36②/DEC-38 #4/#5）。

状态机对齐 MCP Tasks V2 语义：working → completed|failed|cancelled；
working 可进 input_required（审批等待）后回 working。
V1 为进程内注册表（单进程 stdio 形态；持久化留多进程阶段）。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from tessera_agent.common.errors import (
    TA_E_INTERNAL,
    TA_E_TASK_NOT_FOUND,
    TA_E_TASK_STATE,
    TA_E_TIMEOUT,
    TaError,
)

# 来源: DEC-38 #4——长任务 TTL 30 min
TASK_TTL_S = 1800
# 来源: DEC-38 #5——任务日志环形缓冲 1000 行/任务
TASK_LOG_RING = 1000

TaskCallback = Callable[["Task"], Awaitable[Any]]


def _digest(args: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()[:16]


@dataclass
class Task:
    id: str
    tool: str
    args_digest: str
    state: str = "working"
    created_at: float = field(default_factory=time.monotonic)
    ttl_s: int = TASK_TTL_S
    log: deque[str] = field(default_factory=lambda: deque(maxlen=TASK_LOG_RING))
    result: Any = None
    error: dict[str, Any] | None = None
    log_dropped: int = 0
    _aio: asyncio.Task[None] | None = None

    def expired(self) -> bool:
        return self.state in ("working", "input_required") and (
            time.monotonic() - self.created_at > self.ttl_s
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "task_id": self.id,
            "tool": self.tool,
            "state": self.state,
            "created_at": self.created_at,
            "ttl_s": self.ttl_s,
            "result": self.result,
            "error": self.error,
        }


class TaskRegistry:
    """进程内任务注册表；create() 立即返回句柄（句柄化纪律，DEC-36②）。"""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def create(self, tool: str, args: dict[str, Any], body: TaskCallback) -> Task:
        task = Task(id=f"t-{secrets.token_hex(8)}", tool=tool, args_digest=_digest(args))
        async with self._lock:
            self._tasks[task.id] = task

        async def runner() -> None:
            try:
                task.result = await body(task)
                task.state = "completed"
            except TaError as exc:
                task.error = exc.to_payload()
                task.state = "failed"
            except Exception as exc:  # noqa: BLE001
                # 兜底转结构化（TA_E_INTERNAL）
                task.error = TaError(
                    TA_E_INTERNAL, f"{type(exc).__name__}: {exc}", domain=tool
                ).to_payload()
                task.state = "failed"

        task._aio = asyncio.create_task(runner())
        return task

    def get(self, task_id: str) -> Task:
        task = self._tasks.get(task_id)
        if task is None:
            msg = f"任务句柄不存在或已过期: {task_id}"
            raise TaError(TA_E_TASK_NOT_FOUND, msg, domain="tasks", detail={"task_id": task_id})
        if task.expired():
            task.state = "failed"
            task.error = TaError(
                TA_E_TIMEOUT, f"TTL {task.ttl_s}s 到期", domain="tasks"
            ).to_payload()
            if task._aio is not None and not task._aio.done():
                task._aio.cancel()
        return task

    async def cancel(self, task_id: str) -> Task:
        task = self.get(task_id)
        if task.state not in ("working", "input_required"):
            msg = f"任务已终态，无法取消: {task_id}（{task.state}）"
            raise TaError(
                TA_E_TASK_STATE, msg, domain="tasks", detail={"state": task.state}
            )
        if task._aio is not None:
            task._aio.cancel()
        task.state = "cancelled"
        return task

    def append_log(self, task: Task, line: str) -> None:
        if len(task.log) == task.log.maxlen:
            task.log_dropped += 1
        task.log.append(line)

    def log_slice(self, task: Task, offset: int = 0, limit: int = 200) -> dict[str, Any]:
        lines = list(task.log)
        return {
            "lines": lines[offset : offset + limit],
            "total": len(lines),
            "dropped": task.log_dropped,
            "truncated": len(lines) > offset + limit,
        }
