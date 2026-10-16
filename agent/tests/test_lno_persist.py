# SPDX-License-Identifier: Apache-2.0
"""G 批 D1：LN 注册表持久化——落盘/恢复/降级/环境重定向。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tessera_agent.tools_net.lno import LnRegistry


def test_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "lno.json"
    r = LnRegistry(p)
    r.create("ln-a", [("dbn", "dbc"), ("akn", "akc")])
    r.create("ln-b", [("n1", "c1")], linkloss_policy="pause")
    # 恢复：新实例从盘装载
    r2 = LnRegistry(p)
    ids = [n["ln_id"] for n in r2.list()]
    assert ids == ["ln-a", "ln-b"]
    ln = r2.get("ln-a")
    assert [(m.node, m.cube) for m in ln.members] == [("dbn", "dbc"), ("akn", "akc")]
    assert r2.get("ln-b").linkloss_policy == "pause"


def test_remove_persists(tmp_path: Path) -> None:
    p = tmp_path / "lno.json"
    r = LnRegistry(p)
    r.create("ln-x", [("n", "c")])
    r.remove("ln-x")
    r2 = LnRegistry(p)
    assert r2.list() == []


def test_corrupt_degrades_to_empty(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    p = tmp_path / "lno.json"
    p.write_text("{not json", encoding="utf-8")
    r = LnRegistry(p)
    assert r.list() == []
    assert "恢复失败" in capsys.readouterr().err


def test_entry_corruption_skipped(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    p = tmp_path / "lno.json"
    p.write_text(json.dumps({"nodes": [
        {"ln_id": "good", "members": [{"node": "n", "cube": "c"}]},
        {"ln_id": "bad", "members": "not-a-list"},
    ]}), encoding="utf-8")
    r = LnRegistry(p)
    assert [n["ln_id"] for n in r.list()] == ["good"]
    assert "损坏跳过" in capsys.readouterr().err


def test_memory_mode_no_persist(tmp_path: Path) -> None:
    r = LnRegistry(None)
    r.create("ln-m", [("n", "c")])
    assert r.list()[0]["ln_id"] == "ln-m"


def test_persist_io_failure_warns_not_raises(tmp_path: Path,
                                             capsys: pytest.CaptureFixture) -> None:
    # 目录占位为不可写目标：persist 路径指向一个目录下的同名目录
    (tmp_path / "blocked.json").mkdir()
    r = LnRegistry(tmp_path / "blocked.json")
    r.create("ln-io", [("n", "c")])  # 落盘失败 → 告警不抛
    assert "落盘失败" in capsys.readouterr().err
    assert [n["ln_id"] for n in r.list()] == ["ln-io"]
