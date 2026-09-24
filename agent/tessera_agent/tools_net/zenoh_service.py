# SPDX-License-Identifier: Apache-2.0
"""ZenohService：专属线程 zenoh 会话桥（LLD-A06 §1；Q-19 #1 手搭队列，不引 janus）。

eclipse-zenoh 1.10.1 同步 API（asyncio 已被上游移除）——会话驻留单一工作线程，
跨线程调用经队列 + 结果盒封送（部署/查询为请求-响应型，无订阅回调需求时
零回调穿线）。DR-22：三方同 minor（zenohd / eclipse-zenoh / zenoh-pico）。
"""

from __future__ import annotations

import json
import queue
import threading
from collections.abc import Callable
from typing import Any

import zenoh

from tessera_agent.common.errors import TA_E_ZENOH, TaError

# 来源: DEC-38 #4（deploy_discover 10s；单条 query 同档）
QUERY_TIMEOUT_S = 10.0


class ZenohService:
    """单会话单线程桥；上下文管理器形态（open→work→close）。"""

    def __init__(self, locator: str, *, query_timeout_s: float = QUERY_TIMEOUT_S) -> None:
        self._locator = locator
        self._timeout_s = query_timeout_s
        self._reqs: queue.SimpleQueue[
            tuple[Callable[[zenoh.Session], Any] | None, threading.Event, dict]
        ] = queue.SimpleQueue()
        self._thread: threading.Thread | None = None
        self._open_error: BaseException | None = None

    # ---- 生命周期 ----------------------------------------------------------

    def _run(self) -> None:
        try:
            conf = zenoh.Config()
            conf.insert_json5(
                "connect", json.dumps({"endpoints": [self._locator]})
            )
            session = zenoh.open(conf)
        except BaseException as exc:  # noqa: BLE001
            # 启动失败须可达调用方
            self._open_error = exc
            return
        while True:
            fn, done, box = self._reqs.get()
            if fn is None:
                break
            try:
                box["result"] = fn(session)
            except BaseException as exc:  # noqa: BLE001
                box["error"] = exc
            finally:
                done.set()
        session.close()

    def __enter__(self) -> ZenohService:
        self._thread = threading.Thread(
            target=self._run, name="tessera-zenoh", daemon=True
        )
        self._thread.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        if self._thread is not None:
            self._reqs.put((None, threading.Event(), {}))
            self._thread.join(timeout=5.0)
            self._thread = None

    # ---- 调用封送 ----------------------------------------------------------

    def _call(self, fn: Callable[[zenoh.Session], Any],
              timeout_s: float | None = None) -> Any:
        if self._thread is None:
            msg = "ZenohService 未启动（须以 with 语句使用）"
            raise TaError(TA_E_ZENOH, msg, domain="zenoh")
        if self._open_error is not None:
            msg = f"zenoh 会话建立失败: {self._open_error}"
            raise TaError(TA_E_ZENOH, msg, domain="zenoh") from self._open_error
        done = threading.Event()
        box: dict[str, Any] = {}
        self._reqs.put((fn, done, box))
        if not done.wait(timeout=timeout_s or self._timeout_s + 5.0):
            msg = f"zenoh 调用超时（worker 未响应 {timeout_s or self._timeout_s + 5.0}s）"
            raise TaError(TA_E_ZENOH, msg, domain="zenoh", retryable=True)
        if "error" in box:
            exc = box["error"]
            if isinstance(exc, TaError):
                raise exc
            msg = f"zenoh 调用失败: {exc}"
            raise TaError(TA_E_ZENOH, msg, domain="zenoh") from exc
        return box.get("result")

    # ---- 数据面 ------------------------------------------------------------

    def query(self, key: str, payload: bytes,
              timeout_s: float = QUERY_TIMEOUT_S) -> list[tuple[str, bytes]]:
        """query → [(回执 key, 回执 payload)]；ERR 回执 = TaError（不留静默）。"""

        def do(s: zenoh.Session) -> list[tuple[str, bytes]]:
            out: list[tuple[str, bytes]] = []
            for r in s.get(key, payload=payload, timeout=timeout_s):
                if r.ok is None:
                    msg = f"query {key} 收到 ERR 回执: {bytes(r.err_payload)!r}"
                    raise TaError(TA_E_ZENOH, msg, domain="zenoh")
                out.append((str(r.ok.key_expr), bytes(r.ok.payload)))
            return out

        return self._call(do, timeout_s=timeout_s + 5.0)

    def query_one(self, key: str, payload: bytes,
                  timeout_s: float = QUERY_TIMEOUT_S) -> tuple[str, bytes]:
        """单目标 query（sys 命令面）：无回执 = 超时 TaError（可重试）。"""
        replies = self.query(key, payload, timeout_s)
        if not replies:
            msg = f"query 无回执（超时 {timeout_s}s）: {key}"
            raise TaError(TA_E_ZENOH, msg, domain="zenoh", retryable=True)
        return replies[0]

    def put(self, key: str, payload: bytes) -> None:
        def do(s: zenoh.Session) -> None:
            s.put(key, payload)

        self._call(do)
