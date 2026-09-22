# SPDX-License-Identifier: Apache-2.0
"""子进程纪律（LLD-A00 §5 / DR-23）：禁 shell、超时必填、进程组杀、流式日志。"""

from __future__ import annotations

import asyncio
import os
import signal
from collections.abc import Sequence

from tessera_agent.common.errors import TA_E_POLICY, TA_E_PROC_FAIL, TA_E_TIMEOUT, TaError
from tessera_agent.common.limits import ContextBudget, truncate_line

# 来源: DEC-38 #4——子进程默认超时 120s（fw_build/fw_twister 类由调用方给 30min）
PROC_DEFAULT_TIMEOUT_S = 120


def check_path_allowed(path: str, roots: Sequence[str]) -> None:
    """路径白名单：可读写路径必须位于 workspace 根内（越界 = TA_E_POLICY）。"""
    resolved = os.path.realpath(os.path.expanduser(path))
    for root in roots:
        r = os.path.realpath(os.path.expanduser(root))
        if resolved == r or resolved.startswith(r + os.sep):
            return
    msg = f"路径越界（白名单外）: {path}"
    raise TaError(TA_E_POLICY, msg, domain="proc", detail={"path": path})


async def run_proc(
    cmd: Sequence[str],
    *,
    cwd: str,
    timeout_s: int = PROC_DEFAULT_TIMEOUT_S,
    log_fn=None,
    budget: ContextBudget | None = None,
    env: dict[str, str] | None = None,
) -> dict:
    """执行子进程：立即返回流式日志入 log_fn；返回 {exit_code, last_lines}。

    纪律：create_subprocess_exec（禁 shell=True）；start_new_session=True 使超时可杀
    整个进程组；每行经单行截断（DEC-38 #9）。
    """
    log_lines: list[str] = []

    def emit(line: str) -> None:
        if budget is not None:
            line = truncate_line(line, budget)
        log_lines.append(line)
        if log_fn is not None:
            log_fn(line)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=os.path.expanduser(cwd),  # noqa: ASYNC240
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )

    async def pump() -> None:
        assert proc.stdout is not None
        while True:
            raw = await proc.stdout.readline()
            if not raw:
                break
            emit(raw.decode("utf-8", errors="replace").rstrip("\n"))

    assert proc is not None
    try:
        pump_task = asyncio.create_task(pump())
        await asyncio.wait_for(proc.wait(), timeout=timeout_s)
    except TimeoutError:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        await proc.wait()
        pump_task.cancel()
        msg = f"子进程超时（{timeout_s}s）: {' '.join(cmd[:3])}…"
        raise TaError(TA_E_TIMEOUT, msg, domain="proc", retryable=True) from None

    await pump_task
    tail = log_lines[-40:]
    if proc.returncode != 0:
        msg = f"子进程非零退出 rc={proc.returncode}: {' '.join(cmd[:3])}…"
        raise TaError(
            TA_E_PROC_FAIL,
            msg,
            domain="proc",
            detail={"returncode": proc.returncode, "tail": tail},
        )
    return {"exit_code": proc.returncode, "tail": tail}
