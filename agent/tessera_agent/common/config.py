# SPDX-License-Identifier: Apache-2.0
"""配置加载（LLD-A00 §4）。

密钥一律环境变量（gitignore 纪律），config.toml 只存非敏感配置；
加载优先级：内置默认值 < config.toml < 环境变量（TESSERA_AGENT_* 覆盖点）。
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_FILENAME = "config.toml"
ENV_CONFIG_PATH = "TESSERA_AGENT_CONFIG"
ENV_DEFAULT_MODEL = "TESSERA_AGENT_DEFAULT_MODEL"

# 默认路径与 WSL 目录规范一致（docs/dev-environment.md §1）
_DEFAULTS: dict[str, dict[str, Any]] = {
    "agent": {
        "workspace_repo": "~/project/tessera",
        "west_workspace": "~/project/zephyrproject",
        "west_venv_python": "~/project/zephyrproject/.venv/bin/python",
        "audit_dir": "~/project/tessera/agent/audit",
    },
    "providers": {
        # PydanticAI 模型串：openai:... / anthropic:... / ollama:...（LLD-A02 §2）
        "default_model": "",
        # 模型上下文窗口（DEC-38 #6：预算动态取此值；≥32k 为最低要求）。
        # 由部署方按所用模型声明；缺省按最低 32k 保守处理。
        "context_window": 32768,
    },
    "zenoh": {
        "router_locator": "tcp/127.0.0.1:7447",
    },
}


class ConfigError(Exception):
    """配置缺失必需字段或格式非法（启动期暴露，LLD-A00 §4）。"""


@dataclass(frozen=True)
class AgentConfig:
    """生效配置（展开后的路径与最终值）。"""

    workspace_repo: Path
    west_workspace: Path
    west_venv_python: Path
    audit_dir: Path
    default_model: str
    context_window: int
    router_locator: str


def _expand(value: str) -> Path:
    return Path(os.path.expanduser(value))


def _resolve_path() -> Path:
    env_path = os.environ.get(ENV_CONFIG_PATH)
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent.parent / DEFAULT_CONFIG_FILENAME


def load_config(path: str | Path | None = None) -> AgentConfig:
    """加载并校验配置；path 为空时按 env → agent/config.toml 顺序定位。"""
    cfg_path = Path(path) if path is not None else _resolve_path()
    merged: dict[str, dict[str, Any]] = {k: dict(v) for k, v in _DEFAULTS.items()}
    if cfg_path.exists():
        with cfg_path.open("rb") as fh:
            override = tomllib.load(fh)
        for section, values in override.items():
            if not isinstance(values, dict):
                msg = f"配置节 [{section}] 必须是表（键值对），当前为 {type(values).__name__}"
                raise ConfigError(msg)
            merged.setdefault(section, {}).update(values)

    env_model = os.environ.get(ENV_DEFAULT_MODEL)
    default_model = env_model or str(merged["providers"].get("default_model", ""))
    if not default_model:
        msg = f"providers.default_model 未配置（config.toml 或 ${ENV_DEFAULT_MODEL}）"
        raise ConfigError(msg)

    return AgentConfig(
        workspace_repo=_expand(str(merged["agent"]["workspace_repo"])),
        west_workspace=_expand(str(merged["agent"]["west_workspace"])),
        west_venv_python=_expand(str(merged["agent"]["west_venv_python"])),
        audit_dir=_expand(str(merged["agent"]["audit_dir"])),
        default_model=default_model,
        context_window=int(merged["providers"].get("context_window", 32768)),
        router_locator=str(merged["zenoh"]["router_locator"]),
    )
