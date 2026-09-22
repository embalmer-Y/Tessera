# SPDX-License-Identifier: Apache-2.0
"""上下文预算与输出限额（DEC-38 #6/#9：动态取模型窗口，最低要求值）。"""

from __future__ import annotations

from dataclasses import dataclass

from tessera_agent.common.errors import TA_E_ARGS, TaError

# 来源: DEC-38 #6——模型 context window 最低要求 32k（系统提示+skills+工具 schema+最小工作集约 20k）
MIN_CONTEXT_WINDOW_TOKENS = 32_000
# 来源: DEC-38 #6——压缩阈值（达窗口 70% 触发）
COMPRESS_THRESHOLD = 0.70
# 来源: DEC-38 #9——输出截断：单次 = 预算×5% 折算字节（≈4 字符/token），最低 16 KiB
OUTPUT_BUDGET_FRACTION = 0.05
MIN_SINGLE_RETURN_BYTES = 16 * 1024
# 来源: DEC-38 #9——单行 = max(2 KiB, 单次/16)
MIN_LINE_BYTES = 2 * 1024
LINE_DIVISOR = 16
# token 估算：≈4 字符/token（DEC-38 #9 折算口径）
CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class ContextBudget:
    """会话上下文预算（动态随模型配置；DEC-38 #6）。"""

    window_tokens: int

    def __post_init__(self) -> None:
        if self.window_tokens < MIN_CONTEXT_WINDOW_TOKENS:
            msg = (
                f"模型 context window {self.window_tokens} 低于最低要求 "
                f"{MIN_CONTEXT_WINDOW_TOKENS}（DEC-38 #6）"
            )
            raise TaError(TA_E_ARGS, msg, domain="core", detail={"min": MIN_CONTEXT_WINDOW_TOKENS})

    @property
    def compress_at_tokens(self) -> int:
        return int(self.window_tokens * COMPRESS_THRESHOLD)

    @property
    def single_return_bytes(self) -> int:
        est = int(self.window_tokens * OUTPUT_BUDGET_FRACTION * CHARS_PER_TOKEN)
        return max(MIN_SINGLE_RETURN_BYTES, est)

    @property
    def line_bytes(self) -> int:
        return max(MIN_LINE_BYTES, self.single_return_bytes // LINE_DIVISOR)

    def estimate_tokens(self, text: str) -> int:
        return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def truncate_line(line: str, budget: ContextBudget) -> str:
    """单行截断（超限打截断标记；TA_E_LOG_TRUNCATED 语义由调用方呈现）。"""
    limit = budget.line_bytes
    b = line.encode("utf-8")
    if len(b) <= limit:
        return line
    return b[: limit - 24].decode("utf-8", errors="ignore") + "…[truncated]"


def truncate_output(text: str, budget: ContextBudget) -> str:
    limit = budget.single_return_bytes
    b = text.encode("utf-8")
    if len(b) <= limit:
        return text
    return b[: limit - 32].decode("utf-8", errors="ignore") + "\n…[truncated]"
