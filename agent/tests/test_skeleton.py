# SPDX-License-Identifier: Apache-2.0
"""MA0 骨架测试：包结构 / 版本 / 配置加载 / CLI（不依赖网络与 LLM）。"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

from tessera_agent import __version__
from tessera_agent.common.config import AgentConfig, ConfigError, load_config

PKG_ROOT = Path(__file__).resolve().parent.parent
SUBPACKAGES = [
    "common",
    "gateway",
    "core",
    "tools_fw",
    "tools_sim",
    "tools_tsap",
    "tools_net",
    "skills",
]


def test_version() -> None:
    assert __version__ == "0.1.0"


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackages_importable(name: str) -> None:
    importlib.import_module(f"tessera_agent.{name}")


def test_config_from_example() -> None:
    cfg = load_config(PKG_ROOT / "config.example.toml")
    assert isinstance(cfg, AgentConfig)
    assert cfg.default_model
    assert cfg.router_locator.startswith("tcp/")
    assert cfg.workspace_repo.name == "tessera"


def test_config_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESSERA_AGENT_DEFAULT_MODEL", "ollama:test-model")
    cfg = load_config(PKG_ROOT / "config.example.toml")
    assert cfg.default_model == "ollama:test-model"


def test_config_missing_model_rejected() -> None:
    # 缺失 default_model 必须启动期报错（LLD-A00 §4：启动时校验）
    with pytest.raises(ConfigError):
        load_config(PKG_ROOT / "no-such-file.toml")


def test_cli_version() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tessera_agent", "--version"],
        capture_output=True,
        text=True,
        check=False,
        cwd=PKG_ROOT.parent,
    )
    assert proc.returncode == 0
    assert __version__ in proc.stdout
