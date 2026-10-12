# SPDX-License-Identifier: Apache-2.0
"""MCP 网关门面（LLD-A01）——兼容层：实现迁移至 platform/compose（LLD-A07 §3
平台/域拆分），本模块保留原导入路径（build_app/AppContext/run_server）。

错误呈现：TaError → ToolError(JSON payload)（isError + 结构化字段，LLD-A01 §5）。
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
    app = build_app(AppContext(cfg=cfg, budget=budget))
    if transport == "http":
        app.run(transport="http", host=host, port=port)
        return
    app.run()  # FastMCP 默认 stdio
