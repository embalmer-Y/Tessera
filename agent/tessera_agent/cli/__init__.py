# SPDX-License-Identifier: Apache-2.0
"""终端门面（LLD-A09 · AG4）：TerminalFrontend = Frontend 第二实现。

AG4 = 渲染纯函数层 + 门面（交互钩子注入式——测试面最大化）；
`tessera-agent run` 子命令接线随 AG6（PydanticAI runner 就绪后）。
"""

from tessera_agent.cli.facade import TerminalFrontend, TerminalOptions

__all__ = ["TerminalFrontend", "TerminalOptions"]
