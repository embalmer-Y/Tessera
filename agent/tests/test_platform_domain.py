# SPDX-License-Identifier: Apache-2.0
"""平台/域拆分测试（LLD-A07 §3/§7）：导入图 / DomainPack 装配 / 策略只收紧 /
接口缝（A2A/ACP）打桩。"""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

from fastmcp import Client

from tessera_agent.core.peer import Frontend, McpFrontend, PeerTransport
from tessera_agent.core.session import PolicyTable
from tessera_agent.domain.firmware import FirmwareDomainPack
from tessera_agent.gateway.compose import build_app

PKG = Path(__file__).resolve().parent.parent / "tessera_agent"


def test_platform_imports_no_domain_modules():
    """架构硬约束（LLD-A07 §3）：平台层不 import 任何域模块。"""
    tree = ast.parse((PKG / "platform.py").read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    banned = ("tessera_agent.tools_", "tessera_agent.domain", "tessera_agent.gateway.compose")
    bad = [m for m in imported if m.startswith(banned)]
    assert not bad, f"平台层不得导入域模块: {bad}"


def test_firmware_pack_declaration_surface():
    pack = FirmwareDomainPack()
    assert pack.name == "firmware"
    for tool in ("app_develop", "app_deploy", "deploy_push_app", "tsap_package"):
        assert tool in pack.tools
    assert sorted(pack.skills) == ["tessera-build", "tessera-safety",
                                   "tessera-tsap", "tessera-workflow"]
    assert pack.policy.entries["app_deploy"] == "strict"
    assert callable(pack.validators[0])
    # 校验器冒烟：合法包路径由 test_app_chain 覆盖；此处验拒绝路径
    import pytest

    from tessera_agent.common.errors import TaError
    with pytest.raises(TaError):
        pack.validators[0]("/nonexistent/pkg.tsap")


def test_policy_table_only_tightens():
    pol = PolicyTable(entries={"fw_build": "strict", "tsap_keygen": "auto"})
    assert pol.category_of("fw_build", "confirm") == "strict", "收紧生效"
    assert pol.category_of("tsap_keygen", "strict") == "strict", "不得放宽"
    assert pol.category_of("unknown", "auto") == "auto"


def test_peer_and_frontend_stubs():
    class FakePeer:
        def serve_agent_card(self) -> dict:
            return {"tools": ["x"]}

        async def delegate_task(self, peer: str, payload: dict) -> dict:
            return {"peer": peer}

    assert isinstance(FakePeer(), PeerTransport)
    fe = McpFrontend(log_fn=lambda s: None)
    assert isinstance(fe, Frontend)
    fe.render_log("line")
    fe.render_pending_approvals([{"id": "a"}])


def test_compose_app_exposes_platform_and_domain_tools(tmp_path):
    """组合根装配：平台工具（skill_read/sys_*）+ 域工具（app_*）同面可用。"""

    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    cfg_dir = tmp_path / "audit"
    ctx = AppContext(
        cfg=type("C", (), {  # 最小 cfg 桩（skill_read 不触网络/工作区）
            "audit_dir": cfg_dir, "workspace_repo": tmp_path,
        })(),
        budget=ContextBudget(32_000),
    )
    app = build_app(ctx)

    async def main() -> None:
        async with Client(app) as c:
            r = await c.call_tool("skill_read", {"name": "tessera-tsap"})
            body = getattr(r, "data", r)
            if hasattr(body, "model_dump"):
                body = body.model_dump()
            assert "TSAP" in str(body)

    asyncio.run(main())
