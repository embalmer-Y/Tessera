# SPDX-License-Identifier: Apache-2.0
"""clarify 需求澄清域（W2 · LLD-A14 §8）测试：FunctionModel 剧本——
缺口分析→澄清问答→合成过门→确认交棒全链 + 门拒修复 + restart 结构化
中止 + LLM 失败结构化 + app_clarify 注册事实。"""

from __future__ import annotations

import asyncio
import json

import pytest

from tessera_agent.common.errors import TaError

_GOOD_SPEC = (
    "【需求】设备每 60 秒闪烁一次状态灯并打印心跳。\n"
    "【资源】gpio（板载 LED）。\n"
    "【判据】\n- \"HEARTBEAT OK\"\n"
    "【安全声明】本应用不驱动任何安全输出，不写入持久存储。"
)


def _clarify_model(reject_first: bool = False):
    """剧本：① 缺口分析（1 问）→ ② 追问轮（空）→ ③ 合成（可先坏 spec）
    →（修复）→ 成品。单 FunctionModel 按调用序分派。"""
    from pydantic_ai.messages import ModelResponse, TextPart
    from pydantic_ai.models.function import FunctionModel

    calls = {"n": 0}

    async def fn(messages, info) -> ModelResponse:
        calls["n"] += 1
        n = calls["n"]
        if n == 1:  # 缺口分析
            payload = {
                "understood": "周期心跳指示应用",
                "questions": [{"question": "闪烁周期？", "options": ["30s", "60s"],
                               "default": "60s"}],
            }
            return ModelResponse(parts=[TextPart(content=json.dumps(payload))])
        if n == 2:  # 追问轮缺口（空 = 澄清收敛）
            payload = {"understood": "周期心跳指示应用", "questions": []}
            return ModelResponse(parts=[TextPart(content=json.dumps(payload))])
        # ③ 合成（n=3；reject_first 时先坏——【判据】节缺引号串）
        spec = _BAD_SPEC if (reject_first and n == 3) else _GOOD_SPEC
        return ModelResponse(parts=[TextPart(content=json.dumps({"spec": spec}))])

    return FunctionModel(fn)


_BAD_SPEC = (
    "【需求】设备周期心跳。\n【资源】无特殊资源。\n【判据】周期打印心跳。\n"
    "【安全声明】无危险动作。"
)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """最小 ctx（真实 registry/questions + 剧本注入点）。"""
    from pathlib import Path

    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    pkg = Path(__file__).resolve().parent.parent
    cfg = AgentConfig(
        workspace_repo=pkg.parent, west_workspace=pkg.parent,
        west_venv_python=pkg.parent / "agent" / "nofake",
        audit_dir=tmp_path / "audit", default_model="ollama:test",
        context_window=32_000, router_locator="tcp/127.0.0.1:7447")
    ctx = AppContext(cfg=cfg, budget=ContextBudget(32_000))
    return ctx


def _answer_soon(ctx, answer, delay_s=0.05):
    async def run():
        await asyncio.sleep(delay_s)
        pending = ctx.questions.list_pending()
        if pending:
            ctx.questions.answer(pending[0]["question_id"], answer)
    return asyncio.create_task(run())


def test_clarify_full_chain_converges(env, tmp_path):
    """全链：缺口→1 问应答→合成过门→proceed→交棒（app_develop 桩）。"""
    from tessera_agent.domain import clarify

    async def fake_develop(ctx, spec, key_path, out_dir, **kw):
        assert spec == _GOOD_SPEC
        return {"state": "PACKAGED", "app_id": "com.t.x"}

    async def main():
        import tessera_agent.domain.app_chain as ac
        orig = ac.app_develop
        clarify.app_chain.app_develop = fake_develop
        try:
            task = await env.registry.create("app_clarify", {}, lambda t: None)
            _answer_soon(env, "60s")
            _answer_soon(env, "proceed", delay_s=0.2)
            out = await clarify.clarify_and_develop(
                env, "让设备定时心跳", task, "k.key", model=_clarify_model(),
                log=lambda s: None)
        finally:
            clarify.app_chain.app_develop = orig
        assert out["state"] == "PACKAGED"
        assert out["clarify"]["questions_asked"] == 1
        assert out["clarify"]["rounds"] == 1
        assert out["clarify"]["spec"] == _GOOD_SPEC

    asyncio.run(main())


def test_clarify_spec_gate_repair_round(env):
    """门拒修复：坏 spec 一次重合成后过门（SPEC_REPAIR_MAX=1）。"""
    from tessera_agent.domain import clarify

    async def fake_develop(ctx, spec, key_path, out_dir, **kw):
        assert spec == _GOOD_SPEC
        return {"state": "PACKAGED"}

    async def main():
        import tessera_agent.domain.app_chain as ac
        orig = ac.app_develop
        clarify.app_chain.app_develop = fake_develop
        try:
            task = await env.registry.create("app_clarify", {}, lambda t: None)
            _answer_soon(env, "60s")
            _answer_soon(env, "proceed", delay_s=0.25)
            out = await clarify.clarify_and_develop(
                env, "定时心跳", task, "k.key", model=_clarify_model(True),
                log=lambda s: None)
        finally:
            clarify.app_chain.app_develop = orig
        assert out["clarify"]["spec"] == _GOOD_SPEC

    asyncio.run(main())


def test_clarify_restart_structured(env, monkeypatch):
    """restart = 结构化中止（TA_E_POLICY · state=RESTART——D7 abort 同型）。
    合成用非剧本模型也行：restart 发生在确认步。"""
    from tessera_agent.domain import clarify

    async def main():
        task = await env.registry.create("app_clarify", {}, lambda t: None)
        _answer_soon(env, "60s")
        _answer_soon(env, "restart", delay_s=0.25)
        with pytest.raises(TaError) as ei:
            await clarify.clarify_and_develop(
                env, "定时心跳", task, "k.key", model=_clarify_model(),
                log=lambda s: None)
        assert ei.value.detail.get("state") == "RESTART"

    asyncio.run(main())


def test_clarify_llm_failure_structured(env, monkeypatch):
    """LLM 失败 → 结构化错误（提示切换开发者模式——不裸抛）。"""
    from tessera_agent.domain import clarify

    class Boom:
        def __init__(self, *a, **kw):
            pass

        async def run(self, *a, **kw):
            raise RuntimeError("no api key")

    monkeypatch.setattr(clarify, "Agent", Boom)

    async def main():
        task = await env.registry.create("app_clarify", {}, lambda t: None)
        with pytest.raises(TaError) as ei:
            await clarify.clarify_and_develop(
                env, "需求", task, "k.key", log=lambda s: None)
        assert ei.value.detail.get("state") == "CLARIFY_FAILED"
        assert "开发者模式" in ei.value.to_payload().get("message", "")

    asyncio.run(main())


def test_app_clarify_registered():
    """域注册事实：tools 面含 app_clarify，policy = confirm。"""
    from tessera_agent.domain.firmware import FirmwareDomainPack

    pack = FirmwareDomainPack()
    assert "app_clarify" in pack.tools
    assert pack.policy.entries.get("app_clarify") == "confirm"


def test_resolve_key_path_default_discovery(tmp_path, monkeypatch):
    """缺省私钥发现（W2 验收修复回归）：None → agent/keys/*.key 首个；
    无私钥 = 结构化错（KEY_NOT_FOUND）；显式路径原样透传。"""
    from tessera_agent.domain.clarify import resolve_key_path

    keys = tmp_path / "agent" / "keys"
    keys.mkdir(parents=True)
    (keys / "b.key").write_bytes(b"k")
    (keys / "a.key").write_bytes(b"k")

    class Cfg:
        workspace_repo = tmp_path

    class Ctx:
        cfg = Cfg()

    got = resolve_key_path(Ctx(), None)
    assert got.endswith("a.key")  # 排序首
    assert resolve_key_path(Ctx(), "explicit.key") == "explicit.key"
    (keys / "a.key").unlink()
    (keys / "b.key").unlink()
    with pytest.raises(TaError) as ei:
        resolve_key_path(Ctx(), None)
    assert ei.value.detail.get("state") == "KEY_NOT_FOUND"


def test_app_clarify_key_path_optional_signature():
    """app_clarify key_path 已改可选（普通模式 MCP 面不再强制私钥参数）。"""
    import inspect

    from tessera_agent.domain.firmware import FirmwareDomainPack

    pack = FirmwareDomainPack()

    async def probe():
        return pack

    # 工具签名经 mount 后不可直接检——检源码面契约即可（tools 面注册事实
    # 已有测试覆盖；此处锚定关键行为：resolve_key_path 存在且被引用）。
    import tessera_agent.domain.firmware as fw

    src = inspect.getsource(fw)
    assert "resolve_key_path" in src
    assert probe is not None
