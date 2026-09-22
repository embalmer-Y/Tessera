# SPDX-License-Identifier: Apache-2.0
"""错误模型（LLD-A00 §1）：TaError 结构化异常 + TA_E_* 错误码族。"""

from __future__ import annotations

from typing import Any

TA_E_INTERNAL = 1
TA_E_ARGS = 2
TA_E_TASK_NOT_FOUND = 3
TA_E_TASK_STATE = 4
TA_E_TIMEOUT = 5
TA_E_PROC_FAIL = 6
TA_E_LOG_TRUNCATED = 7
TA_E_APPROVAL_DENIED = 8
TA_E_APPROVAL_TIMEOUT = 9
TA_E_ZENOH = 10
TA_E_TSAP = 11
TA_E_SIM = 12
TA_E_POLICY = 13
TA_E_NOT_FOUND = 14
TA_E_NOT_CONFIGURED = 15


class TaError(Exception):
    """结构化错误：MCP 工具统一转结构化返回，不抛裸异常（LLD-A00 §1）。"""

    def __init__(
        self,
        code: int,
        message: str,
        *,
        domain: str = "common",
        retryable: bool = False,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.domain = domain
        self.retryable = retryable
        self.detail: dict[str, Any] = detail or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "detail": self.detail,
        }
