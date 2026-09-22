# SPDX-License-Identifier: Apache-2.0
"""CLI 入口（MA0 骨架自检；MCP stdio 服务随 MA1 接入，LLD-A01 §1）。"""

from __future__ import annotations

import argparse
import sys

from tessera_agent import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tessera-agent", description="Tessera AI Agent (MCP server)"
    )
    parser.add_argument("--version", action="version", version=f"tessera-agent {__version__}")
    parser.parse_args(argv)
    print("tessera-agent: MCP 网关尚未接入（MA1 交付，LLD-A01）；当前入口仅作骨架自检。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
