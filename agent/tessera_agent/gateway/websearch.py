# SPDX-License-Identifier: Apache-2.0
"""web_search 工具面（HW-2 · LLD-A16 §2——DEC-73 裁决① QwenPaw 同款模式）。

SearchProvider ABC + TavilyProvider（**keyless 匿名缺省**——`POST
api.tavily.com/search` 带 `X-Tavily-Access-Mode: keyless` 头免 key 直调；
配置 TAVILY_API_KEY 时 Bearer 优先，HTTP 401/429/432 自动回退 keyless）+
工厂按 config `[web_search] provider` 选择（缺省 tavily；未知值 raise 不
静默路由——QwenPaw 同款）。弃 ddgs 抓取提案（裁决①）。

凭据过滤（LLD-A16 §2）：查询词进入 provider/审计前过 scrub_query——
常见密钥形态（sk- 前缀/Bearer 串/password= 赋值/长 hex 串）打码，防用户
需求文本携带的凭据外泄到第三方搜索服务。
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod

import httpx

from tessera_agent.common.config import AgentConfig, ConfigError

TAVILY_BASE_URL = "https://api.tavily.com"
#: 401/429/432 = key 无效/配额尽/匿名态限流——自动回退 keyless（LLD-A16 §2）
_KEYLESS_FALLBACK_STATUS = {401, 429, 432}
SEARCH_TIMEOUT_S = 30.0

_REDACTED = "[REDACTED]"
_SCRUB_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"), _REDACTED),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._-]{8,}\b", re.IGNORECASE), _REDACTED),
    (re.compile(r"(?i)\b(api[_-]?key|password|passwd|token|secret)\s*[=:]\s*\S+"),
     _REDACTED),
    (re.compile(r"\b[0-9a-fA-F]{32,}\b"), _REDACTED),  # 长 hex（密钥/摘要形态）
)


def scrub_query(query: str) -> str:
    """查询词凭据打码（进入 provider 与审计日志前调用——LLD-A16 §2）。"""
    out = query
    for pattern, repl in _SCRUB_RULES:
        out = pattern.sub(repl, out)
    return out


class SearchProvider(ABC):
    """搜索 provider 契约（QwenPaw agents/tools/websearch 同型）。"""

    name: str = ""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        """返回 [{title, url, snippet, content}]；失败如实抛（调用方结构化）。"""


class TavilyProvider(SearchProvider):
    """Tavily REST——keyless 匿名缺省 + env key 升级 + 三态回退。"""

    name = "tavily"

    def __init__(self, api_key: str | None = None, *,
                 base_url: str = TAVILY_BASE_URL,
                 client: httpx.AsyncClient | None = None) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client  # 测试注入面；None = 惰性自建

    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        q = scrub_query(query)
        payload = {"query": q, "max_results": max(1, int(max_results)),
                   "search_depth": "basic"}
        client = self._client or httpx.AsyncClient(timeout=SEARCH_TIMEOUT_S)
        try:
            headers = {"X-Tavily-Access-Mode": "keyless",
                       "Content-Type": "application/json"}
            if self._api_key:
                headers["Authorization"] = f"Bearer {self._api_key}"
            resp = await client.post(f"{self._base_url}/search",
                                     json=payload, headers=dict(headers))
            if resp.status_code in _KEYLESS_FALLBACK_STATUS and self._api_key:
                # key 升级态被拒（无效/配额尽/限流）——回退 keyless 匿名重试
                headers.pop("Authorization", None)
                resp = await client.post(f"{self._base_url}/search",
                                         json=payload, headers=dict(headers))
            resp.raise_for_status()
            data = resp.json()
        finally:
            if self._client is None:
                await client.aclose()
        return [
            {"title": str(r.get("title", "")),
             "url": str(r.get("url", "")),
             "snippet": str(r.get("content", ""))[:400],
             "content": str(r.get("raw_content", "") or r.get("content", ""))}
            for r in data.get("results", [])
        ]


def get_search_provider(cfg: AgentConfig | None = None,
                        api_key: str | None = None,
                        client: httpx.AsyncClient | None = None) -> SearchProvider:
    """工厂：config `[web_search] provider`（缺省 tavily）；未知值 raise
    （不静默路由——QwenPaw 同款）。key 缺省读 TAVILY_API_KEY env。"""
    import os

    provider = "tavily"
    if cfg is not None:
        provider = str(getattr(cfg, "web_search_provider", "tavily") or "tavily")
    if provider == "tavily":
        key = api_key if api_key is not None else os.environ.get("TAVILY_API_KEY")
        return TavilyProvider(key or None, client=client)
    raise ConfigError(f"未知 web_search provider: {provider!r}（合法 = tavily）")
