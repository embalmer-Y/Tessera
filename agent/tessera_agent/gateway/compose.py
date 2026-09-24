# SPDX-License-Identifier: Apache-2.0
"""组合根（LLD-A07 §3）：显式注册 DomainPack——平台与域在此汇合。

新增域 = 在此处追加注册（或经多域编排配置注入），平台/域代码零改动。
"""

from __future__ import annotations

from fastmcp import FastMCP

from tessera_agent.domain.firmware import FirmwareDomainPack
from tessera_agent.platform import AppContext, assemble


def build_app(ctx: AppContext) -> FastMCP:
    """装配完整 tessera-agent（V1 单域 = firmware）。"""
    return assemble(ctx, [FirmwareDomainPack()])
