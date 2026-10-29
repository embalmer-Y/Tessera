# SPDX-License-Identifier: Apache-2.0
"""test_patterns — AC-4 经验复用测试（DEC-83）。
索引器（双产物成功判定）/ 检索面（Jaccard + caps/imports 加权）/ 注入渲染
（防照抄明示 + 空库零注入）/ 创建循环接线（reference_block 进 plan 输入）。
"""
from __future__ import annotations

import json
from pathlib import Path

from tessera_agent.domain import patterns


def _make_sample(ws_dir: Path, app_id: str, summary: str,
                 caps: list[str] | None = None,
                 imports: tuple[str, ...] = ("ts_log_write",),
                 *, wasm_ok: bool = True) -> Path:
    (ws_dir / "project").mkdir(parents=True, exist_ok=True)
    (ws_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (ws_dir / "project.json").write_text(json.dumps({
        "schema": 1, "app_id": app_id,
        "manifest": {"app_id": app_id, "caps": caps or [], "threads": 1,
                     "tier": "small", "needs": None},
    }), encoding="utf-8")
    if wasm_ok:
        # 真最小 wasm 头（magic）+ import 名可读串（轻解析依赖）
        (ws_dir / "artifacts" / "app.wasm").write_bytes(
            b"\x00asm\x01\x00\x00\x00" + imports[0].encode())
        (ws_dir / "artifacts" / "x.tsap").write_bytes(b"pkg")
    (ws_dir / ".session").mkdir(exist_ok=True)
    (ws_dir / ".session" / "snapshot.json").write_text(json.dumps({
        "schema": 1, "state": "PACKAGED",
        "plan": [{"id": "s1", "desc": summary}],
    }), encoding="utf-8")
    return ws_dir


def test_index_requires_both_artifacts(tmp_path: Path):
    good = _make_sample(tmp_path / "t-good", "demo.a", "心跳计数日志输出")
    assert patterns.index_workspace(good) is not None
    # 缺 tsap = 未成功（快照 state 不可信——DEC-83①）
    bad = _make_sample(tmp_path / "t-bad", "demo.b", "x", wasm_ok=False)
    assert patterns.index_workspace(bad) is None
    # 缺 wasm = None
    (tmp_path / "t-nowasm" / "artifacts").mkdir(parents=True)
    assert patterns.index_workspace(tmp_path / "t-nowasm") is None


def test_search_ranks_by_relevance(tmp_path: Path):
    _make_sample(tmp_path / "t-hb", "demo.heartbeat",
                 "心跳计数 每 10 tick 日志输出 HB 行")
    _make_sample(tmp_path / "t-gpio", "demo.toggle",
                 "输出通道自检 翻转 gpio 电平 回读",
                 caps=["gpio:write:0-8"])
    _make_sample(tmp_path / "t-avg", "demo.avg8",
                 "滑动窗口平均滤波 每 40 输入日志输出 AVG")
    idx = patterns.build_index(tmp_path)
    assert len(idx) == 3
    hits = patterns.search(idx, "写一个滑动窗口平均滤波 APP，日志输出 AVG 行")
    assert hits and hits[0][0].app_id == "demo.avg8"
    # caps 加权：gpio 需求命中 gpio 样例
    hits2 = patterns.search(idx, "翻转 gpio 数字输出通道并回读电平")
    assert hits2[0][0].app_id == "demo.toggle"


def test_render_for_prompt_guardrails(tmp_path: Path):
    entry = patterns.index_workspace(
        _make_sample(tmp_path / "t-hb", "demo.heartbeat", "心跳计数"))
    block = patterns.render_for_prompt([(entry, 0.5)])
    assert "禁止照抄" in block and "参考样例结束" in block
    # 空命中 = 空串（零注入向后兼容）
    assert patterns.render_for_prompt([]) == ""
    assert patterns.retrieve(tmp_path / "nonexistent", "spec")[0] == ""


def test_loop_reference_block_reaches_plan_input():
    """接线：runner.reference_block 拼进 plan() 输入（捕获 _plan_agent 输入）。"""
    from tessera_agent.domain.app_chain import PydanticLoopRunner

    runner = PydanticLoopRunner.__new__(PydanticLoopRunner)
    runner.reference_block = "\n[参考样例（样例库检索命中……）]\n- x\n[参考样例结束]"

    captured: list[str] = []

    class FakeAgent:
        async def run(self, prompt: str):
            captured.append(prompt)

            class R:
                output = type("O", (), {
                    "requirements_summary": "r", "safety_notes": [],
                    "test_plan": [], "steps": ["s1"]})()
            return R()

    runner._plan_agent = FakeAgent()
    import asyncio
    items = asyncio.run(runner.plan("需求 spec", ["X DONE"]))
    assert len(items) == 1
    assert "参考样例" in captured[0]
    assert "需求 spec" in captured[0]
    assert "X DONE" in captured[0]
