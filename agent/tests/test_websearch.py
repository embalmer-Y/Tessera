# SPDX-License-Identifier: Apache-2.0
"""web_search 工具面（HW-2 · LLD-agent-hardware-targeting §2）测试：凭据打码 / 工厂缺省与未知值
raise / keyless 头形状 / key 升级与 401 回退 / 结果解析 / MCP 注册事实。"""

from __future__ import annotations

import httpx
import pytest

from tessera_agent.common.config import AgentConfig, ConfigError
from tessera_agent.gateway.websearch import (
    TavilyProvider,
    get_search_provider,
    scrub_query,
)


def _cfg(provider: str = "tavily") -> AgentConfig:
    return AgentConfig(
        workspace_repo=__import__("pathlib").Path("."),
        west_workspace=__import__("pathlib").Path("."),
        west_venv_python=__import__("pathlib").Path("."),
        audit_dir=__import__("pathlib").Path("."),
        default_model="ollama:test", context_window=32_000,
        router_locator="tcp/127.0.0.1:7447", web_search_provider=provider)


def test_scrub_query_redacts_credentials() -> None:
    q = "connect sk-abcdef1234567890 with password=hunter2 and token: aabb" \
        "ccdd00112233445566778899aabbcc"
    out = scrub_query(q)
    assert "sk-abcdef" not in out
    assert "hunter2" not in out
    assert "aabbccdd0011" not in out
    assert out.count("[REDACTED]") == 3


def test_factory_default_tavily_and_unknown_raises() -> None:
    assert get_search_provider(_cfg()).name == "tavily"
    with pytest.raises(ConfigError):
        get_search_provider(_cfg("ddg"))


class _FakeResp:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=None, response=None)


class _FakeClient:
    """记录请求形状（头/载荷）并按脚本回状态码。"""

    def __init__(self, script: list[_FakeResp]) -> None:
        self.script = list(script)
        self.calls: list[dict] = []

    async def post(self, url, json=None, headers=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.script.pop(0)

    async def aclose(self) -> None:
        return None


def test_keyless_header_shape_and_parsing() -> None:
    client = _FakeClient([_FakeResp(200, {"results": [
        {"title": "T", "url": "https://x", "content": "s", "raw_content": "r"}]})])
    prov = TavilyProvider(None, client=client)

    import asyncio

    out = asyncio.run(prov.search("zephyr board support", 3))
    call = client.calls[0]
    assert call["url"].endswith("/search")
    assert call["headers"]["X-Tavily-Access-Mode"] == "keyless"
    assert "Authorization" not in call["headers"]
    assert call["json"]["max_results"] == 3
    assert out[0]["title"] == "T" and out[0]["content"] == "r"


def test_key_upgrade_bearer_and_401_fallback_keyless() -> None:
    # key 在位：首呼 Bearer；401 → 摘掉 Authorization 回退 keyless 重试
    client = _FakeClient([
        _FakeResp(401), _FakeResp(200, {"results": []})])
    prov = TavilyProvider("tk-123", client=client)

    import asyncio

    out = asyncio.run(prov.search("q", 5))
    assert len(client.calls) == 2
    assert client.calls[0]["headers"]["Authorization"] == "Bearer tk-123"
    assert "Authorization" not in client.calls[1]["headers"]
    assert out == []


def test_http_error_propagates_structured() -> None:
    client = _FakeClient([_FakeResp(500)])
    prov = TavilyProvider(None, client=client)

    import asyncio

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(prov.search("q", 5))


def test_web_search_mcp_registered() -> None:
    """域注册事实：tools 面含 web_search，policy = confirm（出站联网）。"""
    from tessera_agent.domain.firmware import FirmwareDomainPack

    pack = FirmwareDomainPack()
    assert "web_search" in pack.tools
    assert pack.policy.entries.get("web_search") == "confirm"
