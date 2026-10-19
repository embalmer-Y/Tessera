# SPDX-License-Identifier: Apache-2.0
"""D5 决策链回放（DEC-67①）：load_timeline 过滤/排序/截尾 + render 形态 +
CLI replay 子命令 + sys_timeline MCP 工具（W1 时间线同源）。"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from fastmcp.exceptions import ToolError

from tessera_agent.audit_replay import load_timeline, render_timeline

PKG_ROOT = Path(__file__).resolve().parent.parent
NOW = time.time()
DAY = time.strftime("%Y%m%d", time.localtime(NOW))


def _write_audit(tmp_path: Path, rows: list[dict]) -> Path:
    d = tmp_path / "audit" / "tools"
    d.mkdir(parents=True)
    (d / f"{DAY}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8")
    return tmp_path / "audit"


def _rows() -> list[dict]:
    return [
        {"ts": NOW - 30, "tool": "sys_ping", "state": "ok", "dur_ms": 3,
         "args_preview": {}, "task_id": "t-a"},
        {"ts": NOW - 20, "tool": "app_deploy", "state": "hook_denied",
         "dur_ms": 1, "args_preview": {}, "task_id": "t-a"},
        {"ts": NOW - 10, "tool": "sys_approve", "state": "ok", "dur_ms": 2,
         "args_preview": {"decision": "allow-session", "approval_id": "a-1"},
         "task_id": "t-a"},
        {"ts": NOW - 5, "tool": "sys_answer", "state": "ok", "dur_ms": 1,
         "args_preview": {"question_id": "q-1", "answer": "proceed"},
         "task_id": "t-b"},
        {"ts": NOW - 1, "tool": "app_compile", "state": "failed", "dur_ms": 900,
         "args_preview": {}, "task_id": "t-b"},
        {"ts": NOW + 5, "tool": "sys_ping", "state": "ok", "dur_ms": 2,
         "args_preview": {}, "task_id": "t-b"},
    ]


def test_load_timeline_filter_and_order(tmp_path):
    audit = _write_audit(tmp_path, _rows())
    tl = load_timeline(audit)
    assert tl["total"] == 6 and not tl["truncated"]
    assert tl["entries"][0]["tool"] == "sys_ping"  # ts 升序
    assert tl["span"] == [tl["entries"][0]["time"], tl["entries"][-1]["time"]]
    # kind 语义派生
    kinds = {(e["tool"], e["kind"]) for e in tl["entries"]}
    assert ("sys_approve", "审批") in kinds and ("sys_answer", "问询") in kinds
    # 过滤：task / tool / limit 截尾
    assert all(e["task_id"] == "t-a"
               for e in load_timeline(audit, task_id="t-a")["entries"])
    assert all(e["tool"] == "sys_ping"
               for e in load_timeline(audit, tool="sys_ping")["entries"])
    tl3 = load_timeline(audit, limit=2)
    assert tl3["truncated"] and len(tl3["entries"]) == 2  # 尾部 2 条
    # 缺日 = 空
    assert load_timeline(audit, day="19990101")["entries"] == []


def test_render_timeline_shape(tmp_path):
    audit = _write_audit(tmp_path, _rows())
    text = render_timeline(load_timeline(audit))
    assert "决策链时间线" in text and "✓" in text and "✗" in text
    assert "⛔" in text and "hook_denied" in text
    assert "allow-session" in text and "proceed" in text  # 关键决策入行


def test_cli_replay_json(tmp_path, monkeypatch, capsys):
    """CLI 子命令端到端：配置经 env 注入；--json 结构化输出。"""
    audit = _write_audit(tmp_path, _rows())
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f"[agent]\n"
        f'workspace_repo = "{PKG_ROOT.parent}"\n'
        f'west_workspace = "{PKG_ROOT.parent}"\n'
        f'west_venv_python = "{PKG_ROOT.parent}/agent/nofake"\n'
        f'audit_dir = "{audit}"\n'
        "[providers]\n"
        'default_model = "ollama:test"\n'
        "context_window = 32000\n"
        "[zenoh]\n"
        'router_locator = "tcp/127.0.0.1:7447"\n',
        encoding="utf-8")
    monkeypatch.setenv("TESSERA_AGENT_CONFIG", str(cfg))
    from tessera_agent.__main__ import main

    rc = main(["replay", "--json", "--task-id", "t-b"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["total"] == 3
    assert {e["tool"] for e in out["entries"]} == {"sys_answer",
                                                   "app_compile", "sys_ping"}


def test_sys_timeline_tool(tmp_path):
    """sys_timeline MCP 工具（W1 时间线 tab 同源数据）。"""
    from fastmcp import Client

    audit = _write_audit(tmp_path, _rows())

    def unwrap(res):
        data = res.data if hasattr(res, "data") else res
        if isinstance(data, dict) and data.get("isError"):
            raise ToolError(str(data))
        return data

    async def main():
        from tessera_agent.common.config import AgentConfig
        from tessera_agent.common.limits import ContextBudget
        from tessera_agent.gateway.compose import build_app
        from tessera_agent.platform import AppContext

        cfg = AgentConfig(
            workspace_repo=PKG_ROOT.parent,
            west_workspace=PKG_ROOT.parent,
            west_venv_python=PKG_ROOT.parent / "agent" / "nofake",
            audit_dir=audit,
            default_model="ollama:test",
            context_window=32_000,
            router_locator="tcp/127.0.0.1:7447",
        )
        app = build_app(AppContext(cfg=cfg, budget=ContextBudget(32_000)))
        async with Client(app) as c:
            tl = unwrap(await c.call_tool("sys_timeline",
                                          {"task_id": "t-a", "limit": 10}))
            assert tl["total"] == 3
            assert tl["entries"][-1]["kind"] in ("审批", "命令")

    asyncio.run(main())

