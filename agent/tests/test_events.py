# SPDX-License-Identifier: Apache-2.0
"""EventBus（W2 · LLD-A14 §3.1）单测：扇出/重放/慢消费者 resync/
线程发布/退订。"""

from __future__ import annotations

import asyncio
import threading

from tessera_agent.common.events import EVENT_QUEUE_MAX, EventBus


def test_publish_replay_seq_monotonic():
    bus = EventBus()
    e1 = bus.publish("a", {"x": 1})
    e2 = bus.publish("b", {"x": 2})
    assert e2.seq == e1.seq + 1
    assert [ev.kind for ev in bus.replay(0)] == ["a", "b"]
    assert [ev.kind for ev in bus.replay(e1.seq)] == ["b"]
    assert bus.replay(e2.seq) == []


def test_subscribe_receives_fact_and_replay():
    async def main():
        bus = EventBus()
        bus.publish("old", {})  # 订阅前事实 → 重放批
        sub = await bus.subscribe()
        replayed = sub.replay()
        assert [e.kind for e in replayed] == ["old"]
        bus.publish("new", {"k": 1})
        ev = await asyncio.wait_for(sub.__anext__(), timeout=2)
        assert ev.kind == "new"
        sub.close()

    asyncio.run(main())


def test_last_event_id_resume_excludes_seen():
    async def main():
        bus = EventBus()
        bus.publish("e1", {})
        bus.publish("e2", {})
        sub = await bus.subscribe(after_seq=1)  # Last-Event-ID=1 → 只补 e2
        assert [e.kind for e in sub.replay()] == ["e2"]
        sub.close()

    asyncio.run(main())


def test_slow_consumer_gets_resync():
    async def main():
        bus = EventBus(queue_max=4)
        sub = await bus.subscribe()
        for i in range(EVENT_QUEUE_MAX + 8):  # 不消费 → 溢出丢旧 + resync
            bus.publish("flood", {"i": i})
        kinds = []
        while len(kinds) < 4:
            ev = await asyncio.wait_for(sub.__anext__(), timeout=2)
            kinds.append(ev.kind)
        assert "resync" in kinds  # 溢出标记到达（宁可重对齐不可假死）
        sub.close()

    asyncio.run(main())


def test_publish_from_worker_thread_reaches_subscriber():
    async def main():
        bus = EventBus()
        sub = await bus.subscribe()
        def worker():
            bus.publish("from_thread", {"ok": True})
        t = threading.Thread(target=worker)
        t.start()
        ev = await asyncio.wait_for(sub.__anext__(), timeout=2)
        t.join()
        assert ev.kind == "from_thread" and ev.data["ok"] is True
        sub.close()

    asyncio.run(main())


def test_publish_before_loop_only_rings():
    bus = EventBus()  # 无 subscribe → 无 loop 捕获
    ev = bus.publish("cold", {})  # CLI/装配早期——仅入环缓冲，不抛
    assert ev.kind == "cold" and bus.replay(0)[0].kind == "cold"
