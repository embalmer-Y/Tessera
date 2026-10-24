# SPDX-License-Identifier: Apache-2.0
"""CreationVerifier 域插件协议（LLD-agent-creation-workspace §4——循环引擎域无关的扩展点）。

固件域首实现 = domain/firmware_creation.py（FirmwareCreationVerifier）；
未来域（PCB/结构件）实现本协议即复用整个创作循环（DEC-33 结构原则）。
验证器为**同步**实现（子进程/文件操作）——循环引擎经 asyncio.to_thread 调度。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from tessera_agent.creation.workspace import Workspace


@dataclass
class VerifyOutcome:
    """统一验证结果：ok + 证据原文（detail 不截断不美化——R6 纪律）。"""

    ok: bool
    detail: str = ""
    facts: dict[str, Any] = field(default_factory=dict)

    def fail_summary(self) -> str:
        return self.detail if self.ok is False else ""


@dataclass
class PackageOutcome(VerifyOutcome):
    package_path: str = ""


@runtime_checkable
class CreationVerifier(Protocol):
    """域验证器：工作区 → 可部署物的唯一出口链（HLD-agent v0.2 §5.2）。"""

    def compile(self, ws: Workspace) -> VerifyOutcome:
        """聚合编译（工程清单 files/exports/threads 驱动）。"""

    def face_check(self, ws: Workspace) -> VerifyOutcome:
        """产物面检查：导入⊆白名单 / 导出齐 / 尺寸档门（对 artifacts 产物复检）。"""

    def simulate(self, ws: Workspace, scenario: dict[str, Any]) -> VerifyOutcome:
        """sim 重放（判据 diff）。场景语义域自定义。"""

    def package(self, ws: Workspace, key_path: str) -> PackageOutcome:
        """双编译一致 + 签名打包——工作区到可部署物唯一出口。"""


def workspace_roots(ws: Workspace) -> list[str]:
    """验证器 allowed_roots 便捷派生：工作区根（编译/打包落点钳制）。"""
    return [str(ws.root)]


def artifacts_wasm(ws: Workspace) -> Path:
    return ws.artifacts_dir / "app.wasm"
