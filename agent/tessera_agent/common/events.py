# SPDX-License-Identifier: Apache-2.0
"""进程内事件总线（W2 · LLD-agent-web-reshape §3.1——SSE 轮询差分 → 直推）。

发布模型：sync `publish`（工作线程安全——TaskRegistry.append_log 在
worker 线程）→ 每订阅者独立 asyncio.Queue 扇出；慢消费者策略 = 丢最旧
+ `resync` 事件（客户端收到即全量快照重对齐——观测渠道宁可重对齐不可
假死）。环形缓冲（512 条单调 seq）支持 Last-Event-ID 重放。

零订阅者 = 纯环形缓冲记录（发布开销 = 一次 append + 一次扇出调度）；
未接线总线（bus=None）的组件行为逐字节等价——LLD-agent-web-reshape §3.2 对照组纪律。
"""
from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

# 来源: LLD-agent-web-reshape §3.1——订阅者队列上限 / 重放缓冲上限
EVENT_QUEUE_MAX = 512
EVENT_REPLAY_MAX = 512


@dataclass(frozen=True)
class Event:
    seq: int
    kind: str
    data: dict[str, Any]
    ts: float


class EventBus:
    """扇出总线：publish（任意线程）→ subscribe（事件循环内）异步迭代。"""

    def __init__(self, *, queue_max: int = EVENT_QUEUE_MAX,
                 replay_max: int = EVENT_REPLAY_MAX) -> None:
        self._lock = threading.Lock()
        self._ring: deque[Event] = deque(maxlen=replay_max)
        self._seq = 0
        self._queue_max = queue_max
        self._queues: list[asyncio.Queue[Event]] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    # ---- 发布（任意线程安全） ------------------------------------------

    def publish(self, kind: str, data: dict[str, Any]) -> Event:
        with self._lock:
            self._seq += 1
            ev = Event(seq=self._seq, kind=kind, data=dict(data),
                       ts=time.time())
            self._ring.append(ev)
        loop = self._loop
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return ev  # 尚无事件循环（CLI/装配早期）——仅入环缓冲
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is loop:
            self._fanout(ev)
        else:
            # 工作线程发布 → 投递回总线所属循环（subscribe 期锁定）
            loop.call_soon_threadsafe(self._fanout, ev)
        return ev

    def _fanout(self, ev: Event) -> None:
        for q in list(self._queues):
            if q.full():
                try:
                    q.get_nowait()  # 丢最旧
                except asyncio.QueueEmpty:  # pragma: no cover——full 保证非空
                    pass
                self._offer(q, Event(seq=ev.seq, kind="resync", data={}, ts=ev.ts))
            self._offer(q, ev)

    @staticmethod
    def _offer(q: asyncio.Queue[Event], ev: Event) -> None:
        try:
            q.put_nowait(ev)
        except asyncio.QueueFull:  # pragma: no cover——丢旧后必有空位
            pass

    # ---- 订阅 / 重放（事件循环内） --------------------------------------

    async def subscribe(self, *, after_seq: int = 0) -> _Subscription:
        """注册订阅者队列；返回订阅句柄——replay() 先取重放批，随后
        async 迭代事实流（seq 单调，按序消费即可）。"""
        self._loop = asyncio.get_running_loop()
        q: asyncio.Queue[Event] = asyncio.Queue(maxsize=self._queue_max)
        self._queues.append(q)
        return _Subscription(self, q, after_seq)

    def replay(self, after_seq: int, limit: int = EVENT_REPLAY_MAX) -> list[Event]:
        with self._lock:
            return [ev for ev in self._ring if ev.seq > after_seq][-limit:]

    def unsubscribe(self, sub: _Subscription) -> None:
        try:
            self._queues.remove(sub.queue)
        except ValueError:  # pragma: no cover——重复退订幂等
            pass


class _Subscription:
    """订阅句柄：replay() 批 + async 迭代事实流；close() 退订。"""

    def __init__(self, bus: EventBus, queue: asyncio.Queue[Event],
                 after_seq: int) -> None:
        self.bus = bus
        self.queue = queue
        self._after = after_seq

    def replay(self) -> list[Event]:
        return self.bus.replay(self._after)

    def __aiter__(self) -> _Subscription:
        return self

    async def __anext__(self) -> Event:
        ev = await self.queue.get()
        self._after = ev.seq
        return ev

    def close(self) -> None:
        self.bus.unsubscribe(self)
