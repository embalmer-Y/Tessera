# SPDX-License-Identifier: Apache-2.0
"""Web 渠道服务面（W2 · LLD-A14 §3.3）：静态前端同源挂载 + SSE 直推。

- `/web` = StaticFiles（agent/web/，单页 ES modules 零构建——Q-48② 案 A）
- `/events` = SSE v2：EventBus 直推（W1 的 0.5s 轮询差分删除；保留
  10s 慢速对账 tick 作遗漏防御）+ 首帧全量快照 + `Last-Event-ID` 续传
  （环形缓冲重放）+ 15s `: ping` 保活 + 慢消费者 `resync`（客户端收到
  即全量重对齐——LLD-A14 §3.1）。
- 消费面 = 手写 mcp.js（浏览器原生 fetch/EventSource，零 Node——LLD-A11 §1）
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.staticfiles import StaticFiles

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
PING_S = 15.0
RECONCILE_S = 10.0
PHASES = (
    "idle", "planning", "implementing", "verifying", "repairing",
    "awaiting_confirm", "awaiting_approval", "packaging", "deploying",
    "done", "failed",
)


def derive_phase(state: str | None, progress: dict[str, Any],
                 questions: list, approvals: list) -> str:
    """状态灯单源派生（LLD-A14 §4.2——server 侧一张映射表，前端零推导）。

    优先级：等待人 > 终态 > 部署 > 循环阶段。"""
    if questions:
        return "awaiting_confirm"
    if approvals:
        return "awaiting_approval"
    if state in ("completed", "cancelled"):
        return "done"
    if state == "failed":
        return "failed"
    loop = (progress or {}).get("loop_state")
    if loop == "implementing" and (progress or {}).get("repairing"):
        return "repairing"
    if loop in ("planning", "implementing", "verifying", "packaging"):
        return loop
    if loop is not None and state == "working":
        return "implementing"
    return "idle" if state is None else "deploying"


def build_tasks_frame(ctx: Any) -> dict[str, Any]:
    """任务列表帧（多任务视图——LLD-A14 §4.6；轻量快照）。"""
    tasks = [
        {"task_id": t.id, "tool": t.tool, "state": t.state,
         "created_at": t.created_at,
         "phase": derive_phase(t.state, t.progress, [], [])}
        for t in ctx.registry.list_tasks()
    ]
    return {"kind": "tasks", "tasks": tasks}


def build_snapshot(ctx: Any, task_id: str | None) -> dict[str, Any]:
    """首帧全量快照（W1 语义保留：附着任务的状态/进度/问答/审批）。"""
    tasks = ctx.registry.list_tasks()
    task = None
    if task_id:
        task = next((t for t in tasks if t.id == task_id), None)
    elif tasks:
        task = tasks[-1]
    questions = ctx.questions.list_pending()
    approvals = ctx.approvals.list_pending()
    snap = {
        "kind": "state",
        "task_id": task.id if task else None,
        "state": task.state if task else None,
        "progress": dict(task.progress) if task else {},
        "phase": derive_phase(task.state if task else None,
                              task.progress if task else {},
                              questions, approvals),
        "questions": questions,
        "approvals": approvals,
    }
    if task is not None:
        # W2 验收修复③：连接/切换任务 = 历史日志回放（进程内环形缓冲，
        # ≤1000 行——刷新/切任务不丢会话；跨进程持久化 = v2 登记不实现）
        sl = ctx.registry.log_slice(task, 0, 1000)
        snap["log"] = sl["lines"]
    return snap


async def event_stream(ctx: Any, task_id: str | None,
                       stop_after: int | None = None,
                       last_event_id: int | None = None) -> AsyncIterator[bytes]:
    """SSE v2 字节流（stop_after = 测试注入的帧数上限；生产 None = 常驻）。"""
    bus = getattr(ctx, "events", None)
    sub = None
    if bus is not None:
        try:
            sub = await bus.subscribe(after_seq=last_event_id or 0)
        except RuntimeError:  # pragma: no cover——非循环上下文（测试直调）
            sub = None

    async def sse(ev_seq: int | None, frame: dict[str, Any]) -> bytes:
        head = f"id: {ev_seq}\n" if ev_seq is not None else ""
        return (head
                + f"data: {json.dumps(frame, ensure_ascii=False)}\n\n").encode()

    sent = 0
    # ① 首帧快照（连接确认；重连时 Last-Event-ID 走 ② 重放补差）
    if last_event_id:
        for ev in (bus.replay(last_event_id) if bus else []):
            frame = _event_frame(ctx, task_id, ev)
            if frame is not None:
                yield await sse(ev.seq, frame)
                sent += 1
    yield await sse(None, build_snapshot(ctx, task_id))
    yield await sse(None, build_tasks_frame(ctx))
    sent += 2
    if sub is None:
        # 无总线（直测/降级）——退化为 W1 形态的慢速对账循环
        cursor: dict[str, Any] = {"sig": ""}
        while stop_after is None or sent < stop_after:
            await asyncio.sleep(RECONCILE_S)
            snap = build_snapshot(ctx, task_id)
            sig = json.dumps(snap, sort_keys=True, default=str)
            if sig != cursor["sig"]:
                cursor["sig"] = sig
                yield await sse(None, snap)
                sent += 1
        return

    # ② 总线直推 + 心跳 + 慢速对账（遗漏防御）
    async def heartbeat() -> AsyncIterator[bytes]:
        while True:
            await asyncio.sleep(PING_S)
            yield b": ping\n\n"

    async def reconcile() -> AsyncIterator[tuple[int, dict[str, Any]]]:
        prev = json.dumps(build_snapshot(ctx, task_id), sort_keys=True,
                          default=str)  # 首拍防重发（首帧快照已发）
        while True:
            await asyncio.sleep(RECONCILE_S)
            snap = build_snapshot(ctx, task_id)
            sig = json.dumps(snap, sort_keys=True, default=str)
            if sig != prev:
                prev = sig
                yield (0, snap)

    hb = heartbeat()
    rc = reconcile()

    async def pump() -> AsyncIterator[tuple[int | None, Any]]:
        """总线事件 / 心跳 / 对账三路竞速。"""
        ev_task = asyncio.create_task(_anext(sub))
        hb_task = asyncio.create_task(hb.__anext__())
        rc_task = asyncio.create_task(rc.__anext__())
        try:
            while stop_after is None or sent < stop_after:
                done, _ = await asyncio.wait(
                    {ev_task, hb_task, rc_task},
                    return_when=asyncio.FIRST_COMPLETED)
                if ev_task in done:
                    ev = ev_task.result()
                    frame = _event_frame(ctx, task_id, ev)
                    if frame is not None:
                        yield ev.seq, frame
                    ev_task = asyncio.create_task(_anext(sub))
                if hb_task in done:
                    yield None, hb_task.result()
                    hb_task = asyncio.create_task(hb.__anext__())
                if rc_task in done:
                    yield 0, rc_task.result()
                    rc_task = asyncio.create_task(rc.__anext__())
        finally:
            for t in (ev_task, hb_task, rc_task):
                t.cancel()
            sub.close()

    async for seq, frame in pump():
        if isinstance(frame, bytes):  # 心跳注释行
            yield frame
        else:
            yield await sse(seq or None, frame)
        sent += 1


async def _anext(sub: Any) -> Any:
    return await sub.__anext__()


def _event_frame(ctx: Any, task_id: str | None, ev: Any) -> dict[str, Any] | None:
    """总线事件 → SSE 帧；task_id 附着过滤 + resync → 快照。"""
    if ev.kind == "resync":
        return build_snapshot(ctx, task_id)
    if task_id and ev.kind.startswith("task.") \
            and ev.data.get("task_id") != task_id:
        return None
    if ev.kind == "task.state":
        questions = ctx.questions.list_pending()
        approvals = ctx.approvals.list_pending()
        return {"kind": "state", "task_id": ev.data.get("task_id"),
                "state": ev.data.get("state"),
                "progress": ev.data.get("progress", {}),
                "phase": derive_phase(ev.data.get("state"),
                                      ev.data.get("progress", {}),
                                      questions, approvals)}
    if ev.kind == "task.log":
        return {"kind": "task_log", "task_id": ev.data.get("task_id"),
                "lines": ev.data.get("lines", [])}
    if ev.kind == "question.opened":
        return {"kind": "questions", "opened": True, **ev.data}
    if ev.kind == "question.closed":
        return {"kind": "questions", "opened": False, **ev.data}
    if ev.kind == "approval.requested":
        return {"kind": "approvals", "opened": True, **ev.data}
    if ev.kind == "approval.decided":
        return {"kind": "approvals", "opened": False, **ev.data}
    if ev.kind == "task.created":
        return build_tasks_frame(ctx)  # 任务列存根刷新（多任务视图）
    if ev.kind == "tasks":
        return build_tasks_frame(ctx)
    return None  # 未知事件型——前端未知即忽略（前向兼容）


def mount_web(asgi: Any, ctx: Any) -> Any:
    """向 FastMCP http_app 组装 web 渠道（/web 静态 + /events 推送）。"""
    asgi.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True),
               name="web")

    async def events(request: Request) -> StreamingResponse:
        task_id = request.query_params.get("task_id") or None
        last_id = request.headers.get("last-event-id")
        last_event_id = int(last_id) if last_id and last_id.isdigit() else None
        gen = event_stream(ctx, task_id, last_event_id=last_event_id)
        return StreamingResponse(gen, media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache",
                                          "X-Accel-Buffering": "no"})

    asgi.router.routes.append(_route("/events", events))
    return asgi


def _route(path: str, endpoint: Any) -> Any:
    from starlette.routing import Route

    return Route(path, endpoint, methods=["GET"])
