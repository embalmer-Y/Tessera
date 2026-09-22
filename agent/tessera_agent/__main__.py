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
    sub.add_parser("serve", help="启动 MCP stdio 网关（V1 唯一形态）")
    args = parser.parse_args(argv)

    if args.command == "serve":
        from tessera_agent.common.config import load_config
        from tessera_agent.gateway.server import run_server

        run_server(load_config())
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
