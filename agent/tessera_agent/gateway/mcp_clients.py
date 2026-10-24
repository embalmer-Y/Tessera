# SPDX-License-Identifier: Apache-2.0
"""外部 MCP server 桥接（A5 · D6 客户端——DEC-12 v1.1 双角色消费侧，
九十六候选⑦；LLD-agent-mcp-clients-and-post-hooks §2/§3）。

Agent 作为 MCP **client** 接入外部 server，工具桥接进本 Agent 面：

- **前缀命名空间防撞**（双向）：桥接面 = `x_<server>_list`（工具清单）与
  `x_<server>_call`（点名调用）——server 名取自 config 键（`[A-Za-z0-9_]`
  净化），永不与本域工具/彼此相撞；外部工具的原始名仅作为 call 参数。
- **外部工具默认 strict 类（不信任面原则）**：每次 call 先挂起宿主审批
  （args 预览入 reason）——审批 token 闸、D4 hooks 拦截、审计同源全部
  照常作用于桥接面（渠道=客户端，安全在服务端）。
- **长任务句柄**：call 走 spawn（外部 server 延迟不可控——句柄化纪律
  DEC-36②；进度/日志/任务栏一致性）。
- 传输形态（LLD-agent-mcp-clients-and-post-hooks §2.1）：`url`（HTTP） / `command`（stdio 子进程） /
  `_inline`（测试注入的内存 FastMCP——仅测试面，config 加载器不产生）。

会话形态 v1 = 每调用连接（connect→call→close——外部 server 数量少、
调用频率低，握手开销可接受；常驻连接池 = v2 登记不实现）。
"""
from __future__ import annotations

import asyncio
import re
from typing import Any

from fastmcp import Client

from tessera_agent.common.errors import TA_E_ARGS, TA_E_TIMEOUT, TaError
from tessera_agent.platform import AppContext, DomainPackBase, MountAPI

# 来源: LLD-agent-mcp-clients-and-post-hooks §3——外部调用超时（外部 server 无 SLA，兜底防悬挂）
MCP_CALL_TIMEOUT_S = 60.0
_SERVER_NAME_RE = re.compile(r"[^A-Za-z0-9_]")


def sanitize_server(name: str) -> str:
    """server 名净化（config 键 → 命名空间段；非法字符折 `_`）。"""
    cleaned = _SERVER_NAME_RE.sub("_", name).strip("_")
    if not cleaned:
        raise TaError(TA_E_ARGS, f"mcp_clients 名字非法: {name!r}",
                      domain="mcp_clients")
    return cleaned


def _client_for(entry: dict[str, Any]) -> Client:
    """传输形态解析（url / command / _inline——LLD-agent-mcp-clients-and-post-hooks §2.1）。"""
    if "_inline" in entry:  # 测试注入面（config 加载器不产生此键）
        return Client(entry["_inline"])
    if "url" in entry:
        return Client(str(entry["url"]))
    if "command" in entry:
        cmd = [str(c) for c in entry["command"]]
        env = {str(k): str(v) for k, v in
               (entry.get("env") or {}).items()} or None
        from fastmcp.client.transports import StdioTransport

        return Client(StdioTransport(cmd[0], cmd[1:], env=env))
    raise TaError(TA_E_ARGS,
                  "mcp_clients 条目须含 url 或 command：" + str(sorted(entry)),
                  domain="mcp_clients")


async def list_external_tools(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """外部工具清单（name/description/schema——原样透传）。"""
    async with _client_for(entry) as c:
        tools = await asyncio.wait_for(c.list_tools(), timeout=MCP_CALL_TIMEOUT_S)
    return [{"name": t.name, "description": t.description or "",
             "schema": t.inputSchema} for t in tools]


async def call_external_tool(entry: dict[str, Any], tool: str,
                             args: dict[str, Any]) -> Any:
    """点名调用（每调用连接——v1 会话形态）。"""
    async with _client_for(entry) as c:
        res = await asyncio.wait_for(c.call_tool(tool, args or {}),
                                     timeout=MCP_CALL_TIMEOUT_S)
    if getattr(res, "is_error", False):
        msg = str(res.content[0].text if res.content else "外部工具报错")
        raise TaError(TA_E_ARGS, f"外部工具 {tool} 报错：{msg}",
                      domain="mcp_clients")
    data = getattr(res, "data", None)
    if data is not None:
        return data
    return [block.text for block in res.content] if res.content else None


class MCPClientDomainPack(DomainPackBase):
    """外部 MCP server 桥接包（A5）：每 server 两个桥接工具，组合根注册。

    tools 面在构造期依 config 展开（sys 面可见性）；strict 审批在工具体
    内强制（外部工具默认 strict——不信任面原则，PolicyTable 之外的第二
    道闸，双保险）。"""

    def __init__(self, clients: dict[str, dict[str, Any]]) -> None:
        self._clients = {
            sanitize_server(name): dict(entry)
            for name, entry in (clients or {}).items()
        }
        self.name = "mcp_clients"
        flat = [f"x_{s}_list" for s in self._clients]
        flat += [f"x_{s}_call" for s in self._clients]
        self.tools = flat
        self.skills = []

    def info_extras(self, ctx: AppContext) -> dict[str, Any]:
        return {"mcp_clients": {
            s: {"transport": ("inline" if "_inline" in e
                              else "http" if "url" in e else "stdio")}
            for s, e in self._clients.items()
        }}

    def mount(self, api: MountAPI) -> None:
        ctx, mcp, audited, spawn = api.ctx, api.mcp, api.audited, api.spawn

        for server, entry in self._clients.items():
            @mcp.tool(name=f"x_{server}_list")
            @audited(f"x_{server}_list")
            async def x_list(server: str = server) -> dict:
                """外部 MCP server 工具清单（A5 桥接面——只读，无审批）。"""
                try:
                    tools = await list_external_tools(self._clients[server])
                except TaError:
                    raise
                except Exception as exc:  # noqa: BLE001——外部域故障结构化
                    raise TaError(
                        TA_E_ARGS,
                        f"外部 server {server} 不可达：{type(exc).__name__}: {exc}",
                        domain="mcp_clients") from exc
                return {"server": server, "tools": tools}

            @mcp.tool(name=f"x_{server}_call")
            @audited(f"x_{server}_call")
            async def x_call(server: str = server, tool: str = "",
                             args: dict[str, Any] | None = None) -> dict:
                """外部工具点名调用（A5 桥接面——**默认 strict**：每次
                调用挂起宿主审批，args 预览入 reason；长任务句柄）。"""
                if not tool:
                    raise TaError(TA_E_ARGS, "tool 不能为空",
                                  domain="mcp_clients")
                call_args = {"server": server, "tool": tool, "args": args or {}}
                entry = self._clients[server]

                async def body(task) -> dict:
                    approval = ctx.approvals.request(
                        f"x_{server}_{tool}", call_args,
                        reason=f"strict 类：外部 MCP 工具 {server}/{tool}"
                               f"（不信任面——默认审批不豁免）")
                    task.state = "input_required"
                    try:
                        await ctx.approvals.wait(approval)
                    finally:
                        task.state = "working"
                    log = lambda ln: ctx.registry.append_log(task, ln)  # noqa: E731
                    log(f"[x] {server}/{tool} 调用中…")
                    try:
                        out = await call_external_tool(entry, tool, args or {})
                    except TaError:
                        raise
                    except TimeoutError as exc:
                        raise TaError(
                            TA_E_TIMEOUT,
                            f"外部工具 {server}/{tool} 超时"
                            f"（>{MCP_CALL_TIMEOUT_S:.0f}s）",
                            domain="mcp_clients") from exc
                    except Exception as exc:  # noqa: BLE001——外部域故障结构化
                        raise TaError(
                            TA_E_ARGS,
                            f"外部工具 {server}/{tool} 失败："
                            f"{type(exc).__name__}: {exc}",
                            domain="mcp_clients") from exc
                    return {"server": server, "tool": tool, "result": out}

                return await spawn(f"x_{server}_call", call_args, body)
