# SPDX-License-Identifier: Apache-2.0
"""审计双流（LLD-A00 §3）：工具流（本模块）+ 会话流（core/session 侧）。

纪律：参数只存摘要（sha256 + 截断预览）；永不记录密钥/令牌；写入失败 = 调用失败。
V1 全量落盘不滚动（DEC-38 #8）。
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

_SENSITIVE_HINTS = ("token", "secret", "password", "api_key", "private")


def args_digest(args: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()


def args_preview(args: dict[str, Any], limit: int = 120) -> dict[str, Any]:
    """脱敏预览：敏感键只留 <redacted>，值截断。"""
    out: dict[str, Any] = {}
    for key, value in args.items():
        if any(h in key.lower() for h in _SENSITIVE_HINTS):
            out[key] = "<redacted>"
            continue
        text = repr(value)
        out[key] = text if len(text) <= limit else text[: limit - 3] + "..."
    return out


class ToolAudit:
    """工具流 JSONL 追加写入（每次工具调用一行）。"""

    def __init__(self, audit_dir: Path) -> None:
        self._dir = audit_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        tool: str,
        args: dict[str, Any],
        state: str,
        dur_ms: int,
        task_id: str | None = None,
        session_id: str | None = None,
        approval: str | None = None,
    ) -> None:
        record = {
            "ts": time.time(),
            "tool": tool,
            "args_digest": args_digest(args),
            "args_preview": args_preview(args),
            "state": state,
            "dur_ms": dur_ms,
            "task_id": task_id,
            "session_id": session_id,
            "approval": approval,
        }
        day = time.strftime("%Y%m%d")
        path = self._dir / "tools" / f"{day}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
