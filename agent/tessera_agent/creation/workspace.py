# SPDX-License-Identifier: Apache-2.0
"""工作区模型（LLD-agent-creation-workspace §2）：布局 / roots 钳制 / project.json 工程清单。

纪律（HLD-agent v0.2 §5.2）：
- 工作区永不入仓（.gitignore 常设 agent/workspace/）；
- artifacts/ 对编辑面只读（交付产物不可手改）；.session/ 对编辑面不可见（防快照自篡改）；
- 一切编辑路径经符号链接解析后必须落在许可 roots 内（IR-13 `_resolve_within` 纪律平移）。

本模块 = 管理面（循环引擎/门面调用，受信代码）；LLM 编辑面 = tools.py 的四动词
（在本模块钳制之上叠加先读后写/唯一锚定语义）。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from tessera_agent.common.errors import (
    TA_E_ARGS,
    TA_E_WORKSPACE_LIMIT,
    TA_E_WORKSPACE_PATH,
    TaError,
)

DOMAIN = "creation"

# 容量上限（LLD-agent-creation-workspace §2.3；防资源耗尽——超限 TA_E_WORKSPACE_LIMIT）
MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024
MAX_FILE_COUNT = 64

PROJECT_JSON = "project.json"


def _empty_project(app_id: str = "", app_ver: str = "1.0.0") -> dict[str, Any]:
    """project.json v1 初始骨架（LLD-agent-creation-workspace §2.2；files/exports 为唯一来源）。"""
    return {
        "schema": 1,
        "app_id": app_id,
        "app_ver": app_ver,
        "tier": "small",
        "files": [],
        "exports": ["app_init", "app_tick", "app_evt", "health_ping"],
        "compile_flags_extra": [],
        "threads": 1,
        "manifest": {},
        "resources": [],
        "needs": None,
    }


class Workspace:
    """单任务工作区。生命周期：create() 建立 → tools/verifier 使用 → 快照/保留策略（AG5）。"""

    def __init__(self, root: Path, ro_roots: list[Path] | None = None) -> None:
        self.root = Path(root).resolve()
        self.project_dir = self.root / "project"
        self.artifacts_dir = self.root / "artifacts"
        self.session_dir = self.root / ".session"
        self.ro_roots = [Path(p).resolve() for p in (ro_roots or [])]
        self._read_marks: dict[str, tuple[int, int]] = {}  # 相对路径 → (mtime_ns, size)

    # ---- 建立与装载 ----------------------------------------------------

    @classmethod
    def create(
        cls,
        base: Path,
        task_id: str,
        ro_roots: list[Path] | None = None,
        app_id: str = "",
    ) -> Workspace:
        root = Path(base) / task_id
        if root.exists():
            raise TaError(
                TA_E_WORKSPACE_PATH,
                f"工作区已存在: {root}",
                domain=DOMAIN,
                detail={"root": str(root)},
            )
        (root / "project").mkdir(parents=True)
        (root / "artifacts").mkdir()
        (root / ".session").mkdir()
        ws = cls(root, ro_roots)
        ws.save_project(_empty_project(app_id))
        return ws

    @classmethod
    def open(cls, base: Path, task_id: str, ro_roots: list[Path] | None = None) -> Workspace:
        """resume/续用装载（AG5 快照路径亦经此）。"""
        ws = cls(Path(base) / task_id, ro_roots)
        if not ws.root.is_dir() or not (ws.root / PROJECT_JSON).is_file():
            raise TaError(
                TA_E_WORKSPACE_PATH,
                f"工作区不存在或不完整: {ws.root}",
                domain=DOMAIN,
                detail={"root": str(ws.root)},
            )
        return ws

    # ---- 工程清单（单一事实源） ----------------------------------------

    def load_project(self) -> dict[str, Any]:
        path = self.root / PROJECT_JSON
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise TaError(
                TA_E_WORKSPACE_PATH,
                f"project.json 解析失败: {exc}",
                domain=DOMAIN,
            ) from exc
        if data.get("schema") != 1:
            raise TaError(
                TA_E_ARGS,
                f"project.json schema 不支持: {data.get('schema')!r}",
                domain=DOMAIN,
            )
        return data

    def save_project(self, data: dict[str, Any]) -> None:
        path = self.root / PROJECT_JSON
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)  # 原子写（LLD-agent-creation-workspace §6.2 纪律平移）

    # ---- 路径钳制（符号链接防御核心） ----------------------------------

    def _inside(self, resolved: Path, base: Path) -> bool:
        try:
            resolved.relative_to(base)
            return True
        except ValueError:
            return False

    @staticmethod
    def _strip_project_alias(path: str) -> str:
        """AG7 实证别名规整：LLM 自然写 project/xxx 前缀——确定性剥除
        （提示词已声明工程根基准；本层兜底，路径语义不变）。"""
        if path == "project":
            return "."
        if path.startswith("project/"):
            return path[len("project/"):]
        return path

    def resolve_read(self, path: str) -> Path:
        """读可达面：工程根相对路径 + artifacts/**（前缀显式，只读）+ ro_roots（绝对路径）。

        .session/ 永不可达（防快照自篡改）。
        """
        path = self._strip_project_alias(path)
        candidate = Path(path)
        if not candidate.is_absolute():
            if path.startswith(("artifacts/", ".session/")):
                candidate = self.root / candidate
            else:
                candidate = self.project_dir / candidate
        resolved = candidate.resolve(strict=False)
        if self._inside(resolved, self.session_dir):
            raise TaError(
                TA_E_WORKSPACE_PATH, "会话目录对编辑面不可见", domain=DOMAIN,
                detail={"path": path},
            )
        ok = (
            self._inside(resolved, self.project_dir)
            or self._inside(resolved, self.artifacts_dir)
            or any(self._inside(resolved, ro) for ro in self.ro_roots)
        )
        if not ok:
            raise TaError(
                TA_E_WORKSPACE_PATH,
                "路径越界（读面 = 工程/产物/仓库白名单）",
                domain=DOMAIN,
                detail={"path": path},
            )
        return resolved

    def resolve_write(self, path: str) -> Path:
        """写可达面 = project/**（工程根相对——作者视角的根）。保留前缀与仓库只读面全拒。"""
        path = self._strip_project_alias(path)
        candidate = Path(path)
        if not candidate.is_absolute():
            if path.startswith(("artifacts/", ".session/")):
                raise TaError(
                    TA_E_WORKSPACE_PATH,
                    "保留目录不可写（artifacts 只读 / 会话目录不可见）",
                    domain=DOMAIN,
                    detail={"path": path},
                )
            candidate = self.project_dir / candidate
        resolved = candidate.resolve(strict=False)
        if not self._inside(resolved, self.project_dir):
            raise TaError(
                TA_E_WORKSPACE_PATH,
                "写面仅限工程目录（artifacts 只读 / 仓库白名单只读 / 会话目录不可见）",
                domain=DOMAIN,
                detail={"path": path},
            )
        return resolved

    # ---- 容量与账目 ------------------------------------------------------

    def _enforce_limits(self, rel: str, new_bytes: int) -> None:
        project = self.load_project()
        files: list[str] = list(project.get("files", []))
        if rel not in files and len(files) + 1 > MAX_FILE_COUNT:
            raise TaError(
                TA_E_WORKSPACE_LIMIT,
                f"文件数超限（>{MAX_FILE_COUNT}）",
                domain=DOMAIN,
                detail={"count": len(files)},
            )
        total = 0
        for name in files:
            if name == rel:
                continue
            p = self.project_dir / name
            if p.is_file():
                total += p.stat().st_size
        if total + new_bytes > MAX_TOTAL_BYTES:
            raise TaError(
                TA_E_WORKSPACE_LIMIT,
                f"工程总量超限（>{MAX_TOTAL_BYTES}B）",
                domain=DOMAIN,
                detail={"total": total + new_bytes},
            )

    def register_file(self, rel: str) -> None:
        """写后把文件登记进 project.json files 表（单一事实源维护）。"""
        project = self.load_project()
        files: list[str] = list(project.get("files", []))
        if rel not in files:
            files.append(rel)
            files.sort()
            project["files"] = files
            self.save_project(project)

    def total_bytes(self) -> int:
        return sum(
            p.stat().st_size
            for p in self.project_dir.rglob("*")
            if p.is_file()
        )
