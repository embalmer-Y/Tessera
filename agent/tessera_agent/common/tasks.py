# SPDX-License-Identifier: Apache-2.0
"""长任务句柄注册表（LLD-agent-common §2，DEC-36②/DEC-38 #4/#5）。

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
    # D2（DEC-65⑤）：结构化进度面（运行体经 note_progress 更新——app_develop
    # 创作循环事件实时映射；只增改已知键，消费面 = task_progress 工具）。
    progress: dict[str, Any] = field(default_factory=dict)
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
            "progress": dict(self.progress),
        }


class TaskRegistry:
    """进程内任务注册表；create() 立即返回句柄（句柄化纪律，DEC-36②）。

    W2（LLD-agent-web-reshape §3.2）：可选事件总线——接线后发布 task.created/state/log
    事件；bus=None（缺省）行为逐字节等价（对照组纪律）。"""

    def __init__(self, bus: Any | None = None) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self._bus = bus

    def attach_bus(self, bus: Any) -> None:
        """装配期接线（AppContext.__post_init__ 单一调用点）。"""
        self._bus = bus

    def _publish(self, kind: str, task: Task, **extra: Any) -> None:
        if self._bus is None:
            return
        try:
            self._bus.publish(kind, {"task_id": task.id, "tool": task.tool,
                                     "state": task.state, **extra})
        except Exception:  # noqa: BLE001
            pass

    async def create(self, tool: str, args: dict[str, Any], body: TaskCallback) -> Task:
        task = Task(id=f"t-{secrets.token_hex(8)}", tool=tool, args_digest=_digest(args))
        async with self._lock:
            self._tasks[task.id] = task
        self._publish("task.created", task)
        self._touch(task)

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
            self._publish("task.state", task, progress=dict(task.progress))

        task._aio = asyncio.create_task(runner())
        return task

    def list_tasks(self) -> list[Task]:
        """按创建序列出全部任务（W1 web 推送面消费——缺省附着一个最新）。
        进程内注册表（V1 单进程形态——A00 §2）；过期任务照常列出
        （snapshot 已带终态语义）。"""
        return sorted(self._tasks.values(), key=lambda t: t.created_at)

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
        self._touch(task)
        self._publish("task.log", task, lines=[line])

    def note_progress(self, task: Task, patch: dict[str, Any] | None = None) -> None:
        """进度变更 + 活动触碰 + 总线发布（W2 · LLD-agent-web-reshape §4.2——调用方
        经此单一入口更新 progress；patch = None 表示仅触碰/发布）。"""
        if patch:
            task.progress.update(patch)
        self._touch(task)
        self._publish("task.state", task, progress=dict(task.progress))

    def _touch(self, task: Task) -> None:
        task.progress["last_activity_ts"] = time.time()

    def log_slice(self, task: Task, offset: int = 0, limit: int = 200) -> dict[str, Any]:
        lines = list(task.log)
        return {
            "lines": lines[offset : offset + limit],
            "total": len(lines),
            "dropped": task.log_dropped,
            "truncated": len(lines) > offset + limit,
        }
