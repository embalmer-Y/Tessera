# SPDX-License-Identifier: Apache-2.0
"""test_eval_bench — AC-1 评估基准测试（DEC-81）。全 Mock 零网络：
任务谱契约 / 评分器机械判定（PASS-PARTIAL-FAIL 三态）/ 报告渲染 / CLI 契约。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tessera_agent.eval import report as eval_report
from tessera_agent.eval import scorer as eval_scorer
from tessera_agent.eval import suite as eval_suite
from tessera_agent.tools_tsap.wasm_build import NATIVE_WHITELIST


def _outcome(package_path: str = "", **over) -> dict:
    """合规 outcome 工厂（T1 形态）。package_path 传真实文件路径以便
    package_on_disk 检查。"""
    base = {
        "state": "PACKAGED", "rounds": 2,
        "workspace": "", "package_path": package_path,
        "compile_facts": {
            "imports": ["ts_log_write", "ts_time_ms"],
            "exports": ["health_ping", "app_init", "app_tick", "app_evt"],
            "deterministic": True, "size": 1200, "files_sha256": {"main.c": "x"},
        },
        "manifest": {"caps": [], "threads": 1, "tier": "small", "needs": None},
    }
    base.update(over)
    return base


def test_suite_contract():
    ids = [t.id for t in eval_suite.SUITE]
    assert ids == ["T1", "T2", "T3", "T4", "T5"]
    for t in eval_suite.SUITE:
        assert t.spec.strip() and t.title.strip()
        assert set(t.expect) <= set(eval_suite._EXPECT_KEYS)
        # 导入允许族 ⊆ 固件白名单（fail-closed 边界不因任务谱失守）
        assert set(t.expect["imports_allowed"]) <= NATIVE_WHITELIST
    # T5 = large 档 + 资源 needs；T4 = threads 档
    t5 = eval_suite.select(["T5"])[0]
    assert t5.expect["tier"] == "large" and t5.expect["needs_expected"]
    t4 = eval_suite.select(["T4"])[0]
    assert t4.expect["threads"] == 2
    # 未知 id fail-closed
    with pytest.raises(ValueError):
        eval_suite.select(["T9"])


def test_score_pass(tmp_path):
    pkg = tmp_path / "a.tsap"
    pkg.write_bytes(b"p")
    task = eval_suite.select(["T1"])[0]
    sc = eval_scorer.score_outcome(task, _outcome(package_path=str(pkg)))
    assert sc.verdict == "PASS"
    assert all(v["ok"] for v in sc.checks.values())


def test_score_partial_caps_missing():
    task = eval_suite.select(["T3"])[0]
    oc = _outcome(compile_facts={
        "imports": ["ts_gpio_write", "ts_log_write"],
        "exports": ["health_ping", "app_init", "app_tick"],
        "deterministic": True, "size": 1500, "files_sha256": {"a.c": "x"},
    }, manifest={"caps": [], "threads": 1, "tier": "small", "needs": None})
    sc = eval_scorer.score_outcome(task, oc)
    assert sc.verdict == "PARTIAL"
    assert not sc.checks["caps"]["ok"]
    assert sc.checks["converged"]["ok"]


def test_score_fail_unconverged():
    task = eval_suite.select(["T1"])[0]
    sc = eval_scorer.score_outcome(task, None, err="创作循环未收敛")
    assert sc.verdict == "FAIL"
    assert not sc.checks["converged"]["ok"]


def test_score_needs_resources_expected():
    task = eval_suite.select(["T5"])[0]
    ok_manifest = {"caps": ["fs:read:0"], "threads": 1, "tier": "large",
                   "needs": {"linear_memory_kb": 256, "stack_kb": 16,
                             "resources": ["/config/"]}}
    sc = eval_scorer.score_outcome(
        task, _outcome(manifest=ok_manifest,
                       compile_facts={"imports": ["ts_fs_read"],
                                      "exports": ["health_ping"],
                                      "deterministic": True, "size": 30000,
                                      "files_sha256": {"m.c": "x"}}))
    assert sc.checks["needs"]["ok"]
    assert sc.checks["tier"]["ok"]
    # 缺 needs = PARTIAL
    bad = dict(ok_manifest, needs=None)
    sc2 = eval_scorer.score_outcome(task, _outcome(manifest=bad))
    assert not sc2.checks["needs"]["ok"]


def test_run_task_injected_fake(tmp_path: Path):
    task = eval_suite.select(["T1"])[0]
    calls: list[str] = []

    async def fake_develop(cfg, spec, key_path, log_fn=None):
        calls.append(spec[:10])
        if log_fn:
            log_fn("fake round")
        return _outcome(package_path=str(tmp_path / "x.tsap"))

    (tmp_path / "x.tsap").write_bytes(b"pkg")
    import asyncio
    from types import SimpleNamespace

    fake_cfg = SimpleNamespace(context_window=40000, default_model="fake")
    sc = asyncio.run(eval_scorer.run_task(
        fake_cfg, task, str(tmp_path / "k.key"), develop_fn=fake_develop))
    assert sc.verdict == "PASS"
    assert calls == [task.spec[:10]]
    assert sc.checks["package_on_disk"]["ok"]


def test_report_render_and_write(tmp_path: Path):
    pkg = tmp_path / "b.tsap"
    pkg.write_bytes(b"p")
    task = eval_suite.select(["T1"])[0]
    scores = [
        eval_scorer.score_outcome(task, _outcome(package_path=str(pkg))),
        eval_scorer.score_outcome(task, None, err="超时"),
    ]
    rep = eval_report.report_dict(scores, model="fake-model", with_sim=False)
    assert rep["summary"]["pass"] == 1
    assert rep["summary"]["fail"] == 1
    assert "skip" in rep["sim_section"]
    md = eval_report.render_markdown(rep)
    assert "T1" in md and "FAIL" in md and "检查矩阵" in md
    jp, mp = eval_report.write_reports(rep, str(tmp_path), "eval-test")
    assert Path(jp).is_file() and Path(mp).is_file()
    assert json.loads(Path(jp).read_text(encoding="utf-8"))["model"] == "fake-model"


def test_cli_contract(capsys):
    """CLI 契约：agent-eval 子命令可达且 fail-closed（未知 id 不触网即退）。"""
    from tessera_agent.__main__ import main

    with pytest.raises(SystemExit):
        main(["agent-eval", "--help"])
    out = capsys.readouterr().out
    assert "agent-eval" in out and "T1-T5" in out
    # 未知任务 id = 退出码 2（选择层 fail-closed，先于任何 LLM 调用）
    assert main(["agent-eval", "--tasks", "T9"]) == 2
    # 缺签名私钥 = 退出码 2
    assert main(["agent-eval", "--key", "/nonexistent/k.key",
                 "--config", "/nonexistent/config.toml"]) == 2
