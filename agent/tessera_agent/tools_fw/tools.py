# SPDX-License-Identifier: Apache-2.0
"""fw_* 固件域工具集（LLD-A03；MA1 最小集）。

子进程纪律（A00 §5）：west/pytest 经 venv 解释器调用；build/输出目录在 agent/build/
（任务级隔离，任务结束保留）；extra_args 白名单前缀校验（防任意注入）。
"""

from __future__ import annotations

import os
import re
from typing import Any

from tessera_agent.common.config import AgentConfig
from tessera_agent.common.errors import TA_E_ARGS, TA_E_POLICY, TaError
from tessera_agent.common.proc import run_proc

# 来源: DEC-38 #4——fw_build/fw_twister 超时 30 min
FW_BUILD_TIMEOUT_S = 1800
_EXTRA_ARG_ALLOWED_PREFIXES = ("-D", "-DCONFIG_", "-DEXTRA_", "--")
_FORBIDDEN_ARG_RE = re.compile(r"[;&|`$<>\n]")


def _west_bin(cfg: AgentConfig) -> str:
    return os.path.join(os.path.dirname(str(cfg.west_venv_python)), "west")


def _validate_extra_args(extra_args: list[str] | None) -> list[str]:
    if not extra_args:
        return []
    for arg in extra_args:
        if _FORBIDDEN_ARG_RE.search(arg) or not arg.startswith(_EXTRA_ARG_ALLOWED_PREFIXES):
            msg = f"extra_args 含非法项（白名单: -D*/--*，禁 shell 元字符）: {arg!r}"
            raise TaError(TA_E_POLICY, msg, domain="fw")
    return list(extra_args)


async def fw_workspace_status(cfg: AgentConfig, budget) -> dict[str, Any]:
    repo = str(cfg.workspace_repo)
    out = await run_proc(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, timeout_s=15, budget=budget
    )
    branch = out["tail"][-1].strip() if out["tail"] else "?"
    out = await run_proc(["git", "rev-parse", "HEAD"], cwd=repo, timeout_s=15, budget=budget)
    commit = out["tail"][-1].strip() if out["tail"] else "?"
    out = await run_proc(["git", "status", "--porcelain"], cwd=repo, timeout_s=15, budget=budget)
    dirty = len(out["tail"])
    return {
        "repo_branch": branch,
        "repo_commit": commit[:12],
        "repo_dirty_files": dirty,
        "west_workspace": str(cfg.west_workspace),
        "test_suites": sorted(
            p.name for p in (cfg.workspace_repo / "firmware" / "tests").iterdir() if p.is_dir()
        ),
    }


async def fw_build(
    cfg: AgentConfig,
    budget,
    *,
    board: str,
    target: str = "app",
    extra_args: list[str] | None = None,
    task_id: str = "adhoc",
    log_fn=None,
) -> dict[str, Any]:
    if not re.fullmatch(r"[a-zA-Z0-9_/-]+", board):
        msg = f"非法板名: {board!r}"
        raise TaError(TA_E_ARGS, msg, domain="fw")
    if target not in ("app",):
        msg = f"未知 target: {target}（V1=app；测试走 fw_twister/fw_pytest）"
        raise TaError(TA_E_ARGS, msg, domain="fw")
    src = str(cfg.workspace_repo / "firmware" / target)
    build_dir = str(cfg.workspace_repo / "agent" / "build" / task_id)
    os.makedirs(build_dir, exist_ok=True)
    cmd = [
        _west_bin(cfg), "build", "-b", board, src, "-d", build_dir,
        "--", f"-DZEPHYR_EXTRA_MODULES={cfg.workspace_repo / 'firmware' / 'module' / 'tessera'}",
        *_validate_extra_args(extra_args),
    ]
    out = await run_proc(
        cmd, cwd=str(cfg.west_workspace), timeout_s=FW_BUILD_TIMEOUT_S, budget=budget, log_fn=log_fn
    )
    return {"build_dir": build_dir, "tail": out["tail"][-20:]}


async def fw_twister(
    cfg: AgentConfig,
    budget,
    *,
    platform: str,
    extra_args: list[str] | None = None,
    task_id: str = "adhoc",
    log_fn=None,
) -> dict[str, Any]:
    if not re.fullmatch(r"[a-zA-Z0-9_/-]+", platform):
        msg = f"非法平台名: {platform!r}"
        raise TaError(TA_E_ARGS, msg, domain="fw")
    out_dir = str(cfg.workspace_repo / "agent" / "build" / task_id)
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        _west_bin(cfg), "twister", "-p", platform,
        "-T", str(cfg.workspace_repo / "firmware" / "tests"),
        "-o", out_dir,
        f"--extra-args=ZEPHYR_EXTRA_MODULES={cfg.workspace_repo / 'firmware' / 'module' / 'tessera'}",  # noqa: E501
        *_validate_extra_args(extra_args),
    ]
    out = await run_proc(
        cmd, cwd=str(cfg.west_workspace), timeout_s=FW_BUILD_TIMEOUT_S, budget=budget, log_fn=log_fn
    )
    summary = next(
        (ln for ln in reversed(out["tail"]) if "executed test configurations" in ln), None
    )
    return {"out_dir": out_dir, "summary": summary, "tail": out["tail"][-20:]}


async def fw_pytest(
    cfg: AgentConfig, budget, *, scope: str = "firmware/tests/pytest", log_fn=None
) -> dict[str, Any]:
    if not re.fullmatch(r"[a-zA-Z0-9_/.-]+", scope) or ".." in scope:
        msg = f"非法 scope: {scope!r}"
        raise TaError(TA_E_ARGS, msg, domain="fw")
    cmd = [str(cfg.west_venv_python), "-m", "pytest", scope, "-q", "--tb=short"]
    out = await run_proc(
        cmd, cwd=str(cfg.workspace_repo), timeout_s=600, budget=budget, log_fn=log_fn
    )
    return {"tail": out["tail"][-15:]}
