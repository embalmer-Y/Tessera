# SPDX-License-Identifier: Apache-2.0
"""Web 渠道服务面（W1 · LLD-A11 / A10 §2）：静态前端同源挂载 + SSE 推送。

- `/web` = StaticFiles（agent/web/，单页 ES modules 零构建——Q-48② 案 A）
- `/events` = SSE 推送（v1 轮询差分策略——A10 §2 诚实注记：0.5s 差分源 =
  task_log 尾随 + questions/approvals pending + task state/progress；语义
  完备零重构，内核事件总线直推随 A10 修订评估）
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
TICK_S = 0.5


def build_frame(ctx: Any, cursor: dict[str, Any], task_id: str | None) -> list[dict[str, Any]]:
    """差分帧：日志新行（游标推进）+ 状态帧（签名变化才发）。"""
    tasks = ctx.registry.list_tasks()
    task = None
    if task_id:
        task = next((t for t in tasks if t.id == task_id), None)
    elif tasks:
        task = tasks[-1]
    out: list[dict[str, Any]] = []
    if task is None:
        sig = "empty"
        if cursor["sig"] != sig:
            cursor["sig"] = sig
            out.append({"kind": "state", "task_id": None, "state": None,
                        "progress": {}, "questions": [], "approvals": []})
        return out
    sl = ctx.registry.log_slice(task, cursor["log_idx"], 200)
    lines = sl.get("lines", [])
    cursor["log_idx"] += len(lines)
    if lines:
        out.append({"kind": "task_log", "task_id": task.id, "lines": lines})
    questions = ctx.questions.list_pending()
    approvals = ctx.approvals.list_pending()
    sig = json.dumps([task.id, task.state, sorted(json.dumps(q, sort_keys=True)
                                                  for q in questions),
                      sorted(json.dumps(a, sort_keys=True)
                             for a in approvals),
                      json.dumps(task.progress, sort_keys=True, default=str)],
                     sort_keys=True)
    if sig != cursor["sig"]:
        cursor["sig"] = sig
        out.append({"kind": "state", "task_id": task.id, "state": task.state,
                    "progress": task.progress, "questions": questions,
                    "approvals": approvals})
    return out


async def event_stream(ctx: Any, task_id: str | None,
                       stop_after: int | None = None) -> AsyncIterator[bytes]:
    """SSE 字节流（stop_after = 测试注入的帧数上限；生产 None = 常驻）。"""
    cursor: dict[str, Any] = {"log_idx": 0, "sig": ""}
    sent = 0
    # 首帧（连接确认 + 当前快照——前端清空日志区，游标从连接起算）
    for frame in build_frame(ctx, cursor, task_id):
        yield f"data: {json.dumps(frame, ensure_ascii=False)}\n\n"
        sent += 1
    while stop_after is None or sent < stop_after:
        await asyncio.sleep(TICK_S)
        for frame in build_frame(ctx, cursor, task_id):
            yield f"data: {json.dumps(frame, ensure_ascii=False)}\n\n"
            sent += 1


def mount_web(asgi: Any, ctx: Any) -> Any:
    """向 FastMCP http_app 组装 web 渠道（/web 静态 + /events 推送）。"""
    asgi.mount("/web", StaticFiles(directory=str(WEB_DIR), html=True),
               name="web")

    async def events(request: Request) -> StreamingResponse:
        task_id = request.query_params.get("task_id") or None
        gen = event_stream(ctx, task_id)
        return StreamingResponse(gen, media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache",
                                          "X-Accel-Buffering": "no"})

    asgi.router.routes.append(_route("/events", events))
    return asgi


def _route(path: str, endpoint: Any) -> Any:
    from starlette.routing import Route

    return Route(path, endpoint, methods=["GET"])
