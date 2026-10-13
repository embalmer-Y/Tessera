# SPDX-License-Identifier: Apache-2.0
"""会话快照（LLD-A08 §6——Q-38④）：任务级断点续跑。

纪律：文件内容本体在 project/（快照只存哈希表——单一事实源不双写）；
原子写（tmp+os.replace）；resume 哈希校验失败 = TA_E_SNAPSHOT_STALE 如实报。
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tessera_agent.common.errors import (
    TA_E_ARGS,
    TA_E_SNAPSHOT_STALE,
    TaError,
)
from tessera_agent.creation.loop import PlanItem

if TYPE_CHECKING:
    from tessera_agent.creation.loop import CreationLoop

DOMAIN = "creation"
SNAPSHOT_SCHEMA = 1
SNAPSHOT_NAME = "snapshot.json"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_table(ws) -> dict[str, dict[str, Any]]:
    table: dict[str, dict[str, Any]] = {}
    for name in ws.load_project().get("files", []):
        p = ws.project_dir / name
        if p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace")
            table[name] = {"sha256": _digest(content), "lines": len(content.splitlines())}
    return table


def take(loop: CreationLoop) -> Path:
    """从循环状态落快照（状态迁移/轮末调用）。"""
    summaries = [
        {
            "r": ev.get("round", 0),
            "event": ev.get("step", "round"),
            "digest": _digest(ev.get("detail", ""))[:12],
        }
        for ev in loop.evidence_log
    ]
    snap = {
        "schema": SNAPSHOT_SCHEMA,
        "task_id": loop.ws.root.name,
        "state": loop.state,
        "round": loop.round,
        "budget": loop.budget,
        "plan": [
            {"id": p.id, "desc": p.desc, "status": p.status} for p in loop.plan
        ],
        "spec_digest": _digest(loop.spec),
        "criteria": list(loop.criteria),
        "files": _file_table(loop.ws),
        "round_summaries": summaries,
        "created_at": _now(),
    }
    path = loop.ws.session_dir / SNAPSHOT_NAME
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(snap, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)
    return path


def load(ws) -> dict[str, Any]:
    """装载并校验快照（schema/哈希——不一致 = STALE 如实报）。"""
    path = ws.session_dir / SNAPSHOT_NAME
    if not path.is_file():
        raise TaError(
            TA_E_ARGS, f"快照不存在: {path}", domain=DOMAIN, detail={"path": str(path)},
        )
    try:
        snap = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TaError(
            TA_E_ARGS, f"快照损坏: {exc}", domain=DOMAIN,
        ) from exc
    if snap.get("schema") != SNAPSHOT_SCHEMA:
        raise TaError(
            TA_E_ARGS, f"快照 schema 不支持: {snap.get('schema')!r}", domain=DOMAIN,
        )
    verify_files(ws, snap)
    return snap


def verify_files(ws, snap: dict[str, Any]) -> None:
    """工程文件与快照哈希逐项比对——外部改动即 STALE（续跑前必检）。"""
    recorded: dict[str, dict[str, Any]] = snap.get("files", {})
    for name, meta in recorded.items():
        p = ws.project_dir / name
        if not p.is_file():
            raise TaError(
                TA_E_SNAPSHOT_STALE,
                f"快照后文件缺失: {name}",
                domain=DOMAIN, detail={"file": name},
            )
        content = p.read_text(encoding="utf-8", errors="replace")
        if _digest(content) != meta.get("sha256"):
            raise TaError(
                TA_E_SNAPSHOT_STALE,
                f"快照后文件已变（先核再续）: {name}",
                domain=DOMAIN, detail={"file": name},
            )


def restore(loop: CreationLoop, snap: dict[str, Any]) -> None:
    """把快照状态重建进循环（round/plan/evidence 上下文由 summaries 重组）。"""
    loop.state = snap.get("state", "IMPLEMENTING")
    loop.round = int(snap.get("round", 0))
    loop.plan = [
        PlanItem(i["id"], i["desc"], i.get("status", "pending"))
        for i in snap.get("plan", [])
    ]
    # 证据本体不回灌（体积）；summaries 作为首轮证据提示注入
    digests = snap.get("round_summaries", [])
    if digests:
        loop.evidence_log.append({
            "round": -1,  # resume 标记（历史证据摘要）
            "step": "resumed",
            "detail": "续跑：历史证据摘要 "
            + "; ".join(f"r{d.get('r')}:{d.get('event')}" for d in digests[-5:]),
        })
