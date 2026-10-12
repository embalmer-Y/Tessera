# SPDX-License-Identifier: Apache-2.0
"""CLI 入口（MA1：`tessera-agent serve` = MCP stdio 网关，LLD-A01 §1）。"""

from __future__ import annotations

import argparse
import sys

from tessera_agent import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tessera-agent", description="Tessera AI Agent (MCP server)"
    )
    parser.add_argument("--version", action="version", version=f"tessera-agent {__version__}")
    sub = parser.add_subparsers(dest="command")
    serve = sub.add_parser("serve", help="启动 MCP 网关（默认 stdio）")
    serve.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                       help="V0.4.0 M12/A7：http = Streamable HTTP 远程门面")
    serve.add_argument("--host", default="127.0.0.1",
                       help="http 传输绑定地址（外网暴露自担）")
    serve.add_argument("--port", type=int, default=9956, help="http 传输端口")
    args = parser.parse_args(argv)

    if args.command == "serve":
        from tessera_agent.common.config import load_config
        from tessera_agent.gateway.server import run_server

        run_server(load_config(), transport=args.transport,
                   host=args.host, port=args.port)
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
