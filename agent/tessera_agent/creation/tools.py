# SPDX-License-Identifier: Apache-2.0
"""scoped 编辑动词（LLD-A08 §3）：LLM 创作面四件——ws_read/ws_write/ws_edit/ws_list。

语义要点：
- 先读后写（防盲写）：覆写/编辑要求目标自最近一次读后未变（mtime_ns+size 指纹）；
- 唯一锚定替换：old_string 必须全文唯一（replace_all 显式放开）——R7 §5 证据形态；
- 分页读（行号制，默认 400 行）——大文件不整灌上下文；
- roots/容量钳制见 workspace.py（本层只叠加编辑语义）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tessera_agent.common.errors import (
    TA_E_ANCHOR_AMBIGUOUS,
    TA_E_ANCHOR_NOT_FOUND,
    TA_E_ARGS,
    TA_E_NOT_CONFIGURED,
    TA_E_NOT_FOUND,
    TA_E_WORKSPACE_LIMIT,
    TA_E_WORKSPACE_PATH,
    TA_E_WORKSPACE_STALE,
    TaError,
)
from tessera_agent.creation.workspace import (
    DOMAIN,
    MAX_FILE_BYTES,
    Workspace,
)

DEFAULT_PAGE = 400


class WorkspaceTools:
    """绑定单工作区的编辑动词集（AG3 循环引擎将其包装为 PydanticAI 工具）。"""

    def __init__(self, ws: Workspace) -> None:
        self.ws = ws

    # ---- 内部 ------------------------------------------------------------

    def _fingerprint(self, path: Path) -> tuple[int, int]:
        st = path.stat()
        return (st.st_mtime_ns, st.st_size)

    def _mark_read(self, rel_key: str, path: Path) -> None:
        self.ws._read_marks[rel_key] = self._fingerprint(path)

    def _require_fresh_read(self, rel_key: str, path: Path) -> None:
        mark = self.ws._read_marks.get(rel_key)
        if mark is None or self._fingerprint(path) != mark:
            raise TaError(
                TA_E_WORKSPACE_STALE,
                "目标未读或读后已变（先 ws_read 再覆写/编辑）",
                domain=DOMAIN,
                detail={"path": rel_key},
            )

    @staticmethod
    def _rel_key(path: Path) -> str:
        return str(path)

    # ---- 动词 ------------------------------------------------------------

    def ws_read(self, path: str, offset: int = 0, limit: int = DEFAULT_PAGE) -> dict[str, Any]:
        """读文件（行号制分页）。读可达 = project/artifacts/仓库白名单。"""
        if offset < 0 or limit <= 0 or limit > 2000:
            raise TaError(
                TA_E_ARGS, "offset/limit 越界（0 ≤ offset，0 < limit ≤ 2000）",
                domain=DOMAIN, detail={"offset": offset, "limit": limit},
            )
        resolved = self.ws.resolve_read(path)
        if not resolved.is_file():
            raise TaError(
                TA_E_NOT_FOUND, f"文件不存在: {path}", domain=DOMAIN,
                detail={"path": path},
            )
        text = resolved.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        total = len(lines)
        window = lines[offset : offset + limit]
        self._mark_read(self._rel_key(resolved), resolved)
        return {
            "path": path,
            "offset": offset,
            "limit": limit,
            "total_lines": total,
            "has_more": offset + limit < total,
            "content": "\n".join(f"{i + 1}\t{line}" for i, line in enumerate(window, start=offset)),
        }

    def ws_write(self, path: str, content: str) -> dict[str, Any]:
        """新建/整文件覆写（仅 project/）。覆写要求先读（防盲写）。"""
        if "\x00" in content:
            raise TaError(TA_E_ARGS, "内容含 NUL", domain=DOMAIN)
        data = content.encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            raise TaError(
                TA_E_WORKSPACE_LIMIT,
                f"单文件超限（{len(data)} > {MAX_FILE_BYTES}B）",
                domain=DOMAIN,
                detail={"bytes": len(data)},
            )
        resolved = self.ws.resolve_write(path)
        rel = str(resolved.relative_to(self.ws.project_dir))
        exists = resolved.is_file()
        if exists:
            self._require_fresh_read(self._rel_key(resolved), resolved)
        self.ws._enforce_limits(rel, len(data))
        resolved.parent.mkdir(parents=True, exist_ok=True)
        tmp = resolved.with_name(resolved.name + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(resolved)  # 原子替换
        self.ws.register_file(rel)
        self._mark_read(self._rel_key(resolved), resolved)
        return {"path": rel, "bytes": len(data), "created": not exists}

    def ws_edit(
        self,
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> dict[str, Any]:
        """唯一锚定替换。失配/多义报错带行号；同要求先读。"""
        if not old_string:
            raise TaError(TA_E_ARGS, "old_string 不可为空", domain=DOMAIN)
        resolved = self.ws.resolve_read(path)
        if not resolved.is_relative_to(self.ws.project_dir):
            raise TaError(
                TA_E_WORKSPACE_PATH, "编辑仅限 project/ 内文件", domain=DOMAIN,
                detail={"path": path},
            )
        if not resolved.is_file():
            raise TaError(TA_E_NOT_FOUND, f"文件不存在: {path}", domain=DOMAIN)
        self._require_fresh_read(self._rel_key(resolved), resolved)
        text = resolved.read_text(encoding="utf-8", errors="replace")
        count = text.count(old_string)
        if count == 0:
            line = _nearest_line(text, old_string)
            raise TaError(
                TA_E_ANCHOR_NOT_FOUND,
                "锚点未找到（先 ws_read 核对原文）",
                domain=DOMAIN,
                detail={"path": path, "nearest_line": line},
            )
        if count > 1 and not replace_all:
            raise TaError(
                TA_E_ANCHOR_AMBIGUOUS,
                f"锚点非唯一（{count} 处）——扩大上下文或显式 replace_all",
                domain=DOMAIN,
                detail={"path": path, "occurrences": count},
            )
        new_text = text.replace(old_string, new_string)
        data = new_text.encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            raise TaError(
                TA_E_WORKSPACE_LIMIT,
                f"结果超单文件上限（{len(data)} > {MAX_FILE_BYTES}B）",
                domain=DOMAIN,
            )
        tmp = resolved.with_name(resolved.name + ".tmp")
        tmp.write_text(new_text, encoding="utf-8")
        tmp.replace(resolved)
        self._mark_read(self._rel_key(resolved), resolved)
        return {"path": path, "replaced": count if replace_all else 1}

    def ws_list(self, path: str = ".") -> dict[str, Any]:
        """工程树（文件+行数）。`@plan` = 计划项视图（AG3 循环引擎接线）。"""
        if path == "@plan":
            raise TaError(
                TA_E_NOT_CONFIGURED,
                "计划视图随 AG3 循环引擎提供",
                domain=DOMAIN,
            )
        base = self.ws.resolve_read(path)
        if not base.is_dir():
            raise TaError(TA_E_NOT_FOUND, f"目录不存在: {path}", domain=DOMAIN)
        entries = []
        for p in sorted(base.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(base)
            try:
                n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
            except OSError:
                n = 0
            entries.append({"file": str(rel), "lines": n})
        return {"base": path, "entries": entries, "count": len(entries)}


def _nearest_line(text: str, needle: str) -> int | None:
    """锚点失配时给最接近线索（首行共同前缀匹配）——降低模型盲试成本。"""
    key = needle.strip().splitlines()[0][:40] if needle.strip() else ""
    if not key:
        return None
    for i, line in enumerate(text.splitlines(), start=1):
        if key in line:
            return i
    return None
