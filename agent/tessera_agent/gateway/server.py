# SPDX-License-Identifier: Apache-2.0
"""MCP 网关门面（LLD-agent-mcp-gateway）——兼容层：实现已迁 platform/compose（skills-platform §3
平台/域拆分），本模块保留原导入路径（build_app/AppContext/run_server）。

错误呈现：TaError → ToolError(JSON payload)（isError + 结构化字段，LLD-agent-mcp-gateway §5）。
长任务纪律：耗时类工具立即返回句柄（DEC-36②），客户端经 task_* 轮询。
"""

from __future__ import annotations

from tessera_agent.common.config import AgentConfig
from tessera_agent.common.limits import ContextBudget
from tessera_agent.gateway.compose import build_app
from tessera_agent.platform import AppContext, assemble  # noqa: F401（再导出）

__all__ = ["AppContext", "assemble", "build_app", "run_server"]


def run_server(cfg: AgentConfig, *, transport: str = "stdio",
               host: str = "127.0.0.1", port: int = 9956) -> None:
    """服务入口。传输形态（V0.4.0 M12/A7，HLD §9 解锁）：
    - stdio（V1 唯一形态，DEC-38 #2——默认）
    - http（Streamable HTTP——远程/多客户端门面；FastMCP 原生，上限 2 并发
      〔HLD §9 既有约束〕；默认绑定 127.0.0.1——外网暴露 = owner 显式
      host 0.0.0.0 + 自担防火墙）。"""
    budget = ContextBudget(cfg.context_window)
    ctx = AppContext(cfg=cfg, budget=budget)  # 单实例——SSE 与 MCP 面共享注册表
    app = build_app(ctx)
    if transport == "http":
        # W1（LLD-agent-web-client）：web 渠道组装——/web 静态前端 + /events SSE 推送
        # （同源同端口；缺省 127.0.0.1——LLD-agent-mci-channels §2 安全约束）
        import uvicorn

        from tessera_agent.gateway.web import mount_web

        asgi = mount_web(app.http_app(path="/mcp"), ctx)
        uvicorn.run(asgi, host=host, port=port)
        return
    app.run()  # FastMCP 默认 stdio
