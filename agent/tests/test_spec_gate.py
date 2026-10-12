# SPDX-License-Identifier: Apache-2.0
"""NV-2 spec 质量门测试：四节模板解析 / 判据派生 / 文法提示 / 兼容语义 +
repair_loop 的 spec 派生联动 + app_develop 入口阻塞路径。"""
from __future__ import annotations

import asyncio

from tessera_agent.common.errors import TaError
from tessera_agent.tools_diag import repair as rp
from tessera_agent.tools_diag import spec_gate as sg

GOOD_TEMPLATED = """\
【需求】确定性计数与日志输出演示：tick 计数 0..5，补零两位输出。
【资源】caps=["gpio:read:0"]（声明不使用）；无 fs_paths。
【判据】输出行 "NV2 DONE ticks=05"（精确补零形态）即达成；心跳稳态。
【安全声明】输出经保护层限幅；确定性输出；无越权访问。
"""

LEGACY = "自由文本 spec：app tick 计数，log 'nv2 done' 后停。caps=[\"gpio:read:0\"]。"


def test_templated_good():
    r = sg.check_spec(GOOD_TEMPLATED)
    assert r.ok and r.templated
    assert r.pass_patterns == ["NV2 DONE ticks=05"]
    assert r.primary_pattern == "NV2 DONE ticks=05"
    assert not r.errors and not r.warnings


def test_primary_pattern_is_first_quoted():
    """多判据串：primary = 第一个（主判据书写约定）。"""
    spec = ("【需求】x\n【资源】无\n"
            "【判据】输出行 \"A DONE 07\" 即达成；附属前缀 \"tick n=\"。\n"
            "【安全声明】限幅\n")
    r = sg.check_spec(spec)
    assert r.primary_pattern == "A DONE 07"
    assert r.pass_patterns == ["A DONE 07", "tick n="]


def test_legacy_free_text_compatible():
    """旧式自由文本：warning 不阻塞，不派生 patterns。"""
    r = sg.check_spec(LEGACY)
    assert r.ok and not r.templated
    assert r.pass_patterns == []
    assert any("四节模板" in w for w in r.warnings)


def test_missing_sections_are_errors():
    r = sg.check_spec("【需求】x\n【判据】输出行 \"A DONE 01\"\n")
    assert not r.ok
    assert any("【资源】" in e for e in r.errors)
    assert any("【安全声明】" in e for e in r.errors)


def test_verdict_without_quoted_string_is_error():
    r = sg.check_spec(
        "【需求】x\n【资源】无\n【判据】完成后输出成功标记行\n【安全声明】确定性\n")
    assert not r.ok
    assert any("引号" in e for e in r.errors)


def test_empty_verdict_section_is_error():
    r = sg.check_spec(
        "【需求】x\n【资源】无\n【判据】\n【安全声明】确定性\n")
    assert not r.ok


def test_caps_and_fs_paths_hard_errors():
    """V0.4.0 M4（IR-17）：caps/fs_paths 硬校验——确定性 spec 期拦截。"""
    spec = ("【需求】x\n【资源】caps=[\"gpio:read:9\"]；"
            "fs_paths=[\"SD:/data\"]\n"
            "【判据】\"Z DONE 02\"\n【安全声明】限幅\n")
    r = sg.check_spec(spec)
    assert not r.ok  # 硬校验阻塞
    assert any("caps 文法非法" in e for e in r.errors)
    assert any("绝对路径" in e for e in r.errors)
    # 合法形态（含 log 类）放行
    ok_spec = ("【需求】x\n【资源】caps=[\"gpio:read:0-3\",\"log:write:0\"]\n"
               "【判据】\"Z DONE 02\"\n【安全声明】限幅\n")
    r2 = sg.check_spec(ok_spec)
    assert r2.ok
    assert not any("caps" in e for e in r2.errors)



def test_safety_keywords_absent_warns():
    spec = ("【需求】x\n【资源】无\n【判据】\"Q DONE 03\"\n"
            "【安全声明】本 APP 无特殊说明\n")
    r = sg.check_spec(spec)
    assert r.ok
    assert any("安全关键词" in w for w in r.warnings)


def test_empty_spec_is_error():
    r = sg.check_spec("  \n")
    assert not r.ok and r.errors


# ---- repair_loop 联动（pass_patterns=None 派生）----

class _H:
    def __init__(self, monkeypatch, texts):
        self.texts = list(texts)
        self.calls = 0

        async def fake_develop(ctx, spec, key_path, out_dir="agent/build", *,
                                wasm_path=None, repair_feedback="", model=None,
                                log_fn=None):
            self.calls += 1
            return {"package_path": f"/p/{self.calls}.tsap"}

        monkeypatch.setattr("tessera_agent.domain.app_chain.app_develop",
                            fake_develop)

        async def deploy(pkg):
            return {"confirmed": True}

        self.deploy_fn = deploy
        self.capture_fn = lambda: (self.texts.pop(0) if self.texts else "")


PASS_TEXT = 'TS3 APP ACTIVE app=d\nNV2 DONE ticks=05\nDB alive t=1'


def test_repair_loop_derives_patterns_from_spec(monkeypatch):
    """pass_patterns=None → 从【判据】节派生（spec 单一事实源）。"""
    h = _H(monkeypatch, [PASS_TEXT])
    out = asyncio.run(rp.repair_loop(
        None, spec=GOOD_TEMPLATED, key_path="k", out_dir="o",
        pass_patterns=None, deploy_fn=h.deploy_fn, capture_fn=h.capture_fn))
    assert out["status"] == rp.STATUS_PASS


def test_repair_loop_evidence_report(monkeypatch):
    """V2-4：pass 轮附带 evidence_hits/缺失报告（附属行缺 = 如实非阻塞）。"""
    spec = ("【需求】x\n【资源】无\n"
            "【判据】输出行 \"A DONE 07\" 即达成；附属前缀 \"tick n=\"。\n"
            "【安全声明】限幅\n")
    text = "TS3 APP ACTIVE\nA DONE 07\nDB alive"   # 附属 tick 行缺失
    h = _H(monkeypatch, [text])
    out = asyncio.run(rp.repair_loop(
        None, spec=spec, key_path="k", out_dir="o",
        pass_patterns=None, deploy_fn=h.deploy_fn, capture_fn=h.capture_fn))
    assert out["status"] == rp.STATUS_PASS
    assert out["evidence_missing"] == ["tick n="]
    hits = out["history"][0]["evidence_hits"]
    assert hits == {"A DONE 07": True, "tick n=": False}


def test_repair_loop_no_derivable_patterns_fails_fast(monkeypatch):
    """无可机读判据且未显式给 → 硬错（不烧任何 LLM 轮）。"""
    h = _H(monkeypatch, [PASS_TEXT])
    try:
        asyncio.run(rp.repair_loop(
            None, spec=LEGACY, key_path="k", out_dir="o",
            pass_patterns=None, deploy_fn=h.deploy_fn, capture_fn=h.capture_fn))
        raise AssertionError("应抛 TaError")
    except TaError as exc:
        assert "机读判据" in str(exc)
    assert h.calls == 0


def test_app_develop_blocks_on_gate_errors():
    """app_develop 入口：gate errors 阻塞（不构造 Agent / 不烧 LLM）。"""
    from tessera_agent.domain import app_chain

    try:
        asyncio.run(app_chain.app_develop(
            None, "【需求】x\n【判据】无引号串\n【安全声明】y\n【资源】z\n",
            "k", log_fn=lambda s: None))
        raise AssertionError("应抛 TaError")
    except TaError as exc:
        assert "spec 质量门" in str(exc)
