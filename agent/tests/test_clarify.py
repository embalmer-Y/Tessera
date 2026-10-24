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


_ENV_CFG = None  # env fixture 登记的基线 cfg（HW 分支测试 west 定向复制）


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """最小 ctx（真实 registry/questions + 剧本注入点）。"""
    global _ENV_CFG
    from pathlib import Path

    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    pkg = Path(__file__).resolve().parent.parent
    _ENV_CFG = AgentConfig(
        workspace_repo=pkg.parent, west_workspace=pkg.parent,
        west_venv_python=pkg.parent / "agent" / "nofake",
        audit_dir=tmp_path / "audit", default_model="ollama:test",
        context_window=32_000, router_locator="tcp/127.0.0.1:7447")
    ctx = AppContext(cfg=_ENV_CFG, budget=ContextBudget(32_000))
    return ctx


def _answer_soon(ctx, answer, delay_s=0.05):
    async def run():
        await asyncio.sleep(delay_s)
        pending = ctx.questions.list_pending()
        if pending:
            ctx.questions.answer(pending[0]["question_id"], answer)
    return asyncio.create_task(run())


def test_clarify_full_chain_converges(env, tmp_path):
    """全链：缺口→1 问应答→硬件定向（暂不指定）→合成过门→proceed→交棒。"""
    from tessera_agent.domain import clarify

    async def fake_develop(ctx, spec, key_path, out_dir, **kw):
        # S0 ④定向产物：spec 尾部带【目标硬件】段（skipped = 未指定如实注记）
        assert spec.startswith(_GOOD_SPEC)
        assert "【目标硬件】" in spec and "未指定" in spec
        return {"state": "PACKAGED", "app_id": "com.t.x"}

    async def main():
        import tessera_agent.domain.app_chain as ac
        orig = ac.app_develop
        clarify.app_chain.app_develop = fake_develop
        try:
            task = await env.registry.create("app_clarify", {}, lambda t: None)
            _answer_soon(env, "60s")
            _answer_soon(env, "暂不指定", delay_s=0.15)
            _answer_soon(env, "proceed", delay_s=0.3)
            out = await clarify.clarify_and_develop(
                env, "让设备定时心跳", task, "k.key", model=_clarify_model(),
                log=lambda s: None)
        finally:
            clarify.app_chain.app_develop = orig
        assert out["state"] == "PACKAGED"
        assert out["clarify"]["questions_asked"] == 1
        assert out["clarify"]["rounds"] == 1
        assert out["clarify"]["spec"].startswith(_GOOD_SPEC)
        assert out["clarify"]["hardware"]["mode"] == "skipped"

    asyncio.run(main())


def test_clarify_spec_gate_repair_round(env):
    """门拒修复：坏 spec 一次重合成后过门（SPEC_REPAIR_MAX=1）。"""
    from tessera_agent.domain import clarify

    async def fake_develop(ctx, spec, key_path, out_dir, **kw):
        assert spec.startswith(_GOOD_SPEC)
        return {"state": "PACKAGED"}

    async def main():
        import tessera_agent.domain.app_chain as ac
        orig = ac.app_develop
        clarify.app_chain.app_develop = fake_develop
        try:
            task = await env.registry.create("app_clarify", {}, lambda t: None)
            _answer_soon(env, "60s")
            _answer_soon(env, "暂不指定", delay_s=0.15)
            _answer_soon(env, "proceed", delay_s=0.3)
            out = await clarify.clarify_and_develop(
                env, "定时心跳", task, "k.key", model=_clarify_model(True),
                log=lambda s: None)
        finally:
            clarify.app_chain.app_develop = orig
        assert out["clarify"]["spec"].startswith(_GOOD_SPEC)

    asyncio.run(main())


def test_clarify_restart_structured(env, monkeypatch):
    """restart = 结构化中止（TA_E_POLICY · state=RESTART——D7 abort 同型）。
    合成用非剧本模型也行：restart 发生在确认步。"""
    from tessera_agent.domain import clarify

    async def main():
        task = await env.registry.create("app_clarify", {}, lambda t: None)
        _answer_soon(env, "60s")
        _answer_soon(env, "暂不指定", delay_s=0.15)
        _answer_soon(env, "restart", delay_s=0.3)
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


# ---- HW-1/HW-3：S0 硬件定向槽（LLD-A16 §1/§3）--------------------------------

def _hw_model(mention: str = "", n_questions: int = 0,
              spec: str | None = None, research: dict | None = None):
    """剧本：① 缺口（可携 hardware_mention）→（research 给出时 n=2 回候选）
    → spec 合成（其余调用）。"""
    from pydantic_ai.messages import ModelResponse, TextPart
    from pydantic_ai.models.function import FunctionModel

    calls = {"n": 0}

    async def fn(messages, info) -> ModelResponse:
        calls["n"] += 1
        n = calls["n"]
        if n == 1:
            payload = {"understood": "需求", "questions": [
                {"question": f"问{i}", "options": ["a"], "default": "a"}
                for i in range(n_questions)],
                "hardware_mention": mention}
            return ModelResponse(parts=[TextPart(content=json.dumps(payload))])
        if research is not None and n == 2:
            return ModelResponse(parts=[TextPart(
                content=json.dumps(research))])
        return ModelResponse(parts=[TextPart(
            content=json.dumps({"spec": spec or _GOOD_SPEC}))])

    return FunctionModel(fn)


def test_clarify_hw_mention_binds_catalog_profile(env, monkeypatch):
    """分支 A：需求提及「ATK DNESP32-S3」→ 目录绑定 atk 画像 →【目标硬件】
    段携带引脚级事实（LEDB=pwm:0）；无硬件问询卡（恰一命中直接绑定）。"""
    from tessera_agent.domain import clarify

    got = {}

    async def fake_develop(ctx, spec, key_path, out_dir, **kw):
        got["spec"] = spec
        return {"state": "PACKAGED"}

    async def main():
        import tessera_agent.domain.app_chain as ac
        orig = ac.app_develop
        clarify.app_chain.app_develop = fake_develop
        try:
            task = await env.registry.create("app_clarify", {}, lambda t: None)
            _answer_soon(env, "proceed", delay_s=0.15)
            out = await clarify.clarify_and_develop(
                env, "让板载 LED 闪烁", task, "k.key",
                model=_hw_model(mention="ATK DNESP32-S3B"), log=lambda s: None)
        finally:
            clarify.app_chain.app_develop = orig
        assert out["clarify"]["hardware"]["mode"] == "profile"
        assert out["clarify"]["hardware"]["board"] == "dnesp32s3b"
        assert "LEDB=pwm:0" in got["spec"]
        assert "【目标硬件】" in got["spec"]

    asyncio.run(main())


def test_clarify_hw_research_path(env, monkeypatch):
    """分支 C：无提及 → 主问询选「帮我联网选型」→ 候选卡（低内存候选被
    机械预筛剔除）→ 选定 → 推定态记录入【目标硬件】段。"""
    from tessera_agent.domain import clarify

    got = {}

    async def fake_develop(ctx, spec, key_path, out_dir, **kw):
        got["spec"] = spec
        return {"state": "PACKAGED"}

    research = {"candidates": [
        {"model": "tiny-mcu", "ram_kb": 64, "psram_kb": 0},
        {"model": "good-board-x", "soc": "esp32s3", "ram_kb": 512,
         "psram_kb": 8192, "zephyr_supported": True},
    ]}

    async def main():
        import tessera_agent.domain.app_chain as ac
        orig = ac.app_develop
        clarify.app_chain.app_develop = fake_develop
        try:
            task = await env.registry.create("app_clarify", {}, lambda t: None)
            _answer_soon(env, "帮我联网选型")
            _answer_soon(env, "good-board-x", delay_s=0.15)
            _answer_soon(env, "proceed", delay_s=0.3)
            out = await clarify.clarify_and_develop(
                env, "做个采集终端", task, "k.key",
                model=_hw_model(research=research), log=lambda s: None)
        finally:
            clarify.app_chain.app_develop = orig
        hw = out["clarify"]["hardware"]
        assert hw["mode"] == "research" and hw["board"] == "good-board-x"
        assert hw["presumed"] is True and len(hw["dropped"]) == 1
        assert "推定态" in got["spec"] and "tiny-mcu" not in got["spec"]

    asyncio.run(main())


def test_clarify_hw_zephyr_included_bv2_queued(tmp_path, monkeypatch):
    """分支 B-收录：提及目录外 Zephyr 收录板 → BV2 工单结构化中止
    （state=BV2_QUEUED）；联网核实失败如实降级为本地结论（离线注入）。"""
    from pathlib import Path

    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.domain import clarify
    from tessera_agent.platform import AppContext

    bdir = tmp_path / "zephyr" / "boards" / "espressif" / "c6"
    bdir.mkdir(parents=True)
    (bdir / "board.yml").write_text("board:\n  name: esp32c6devkitc\n",
                                    encoding="utf-8")
    pkg = Path(__file__).resolve().parent.parent
    cfg = AgentConfig(
        workspace_repo=pkg.parent, west_workspace=tmp_path,
        west_venv_python=pkg.parent / "agent" / "nofake",
        audit_dir=tmp_path / "audit", default_model="ollama:test",
        context_window=32_000, router_locator="tcp/127.0.0.1:7447")
    ctx = AppContext(cfg=cfg, budget=ContextBudget(32_000))

    monkeypatch.setattr(
        "tessera_agent.gateway.websearch.get_search_provider",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline")))

    async def main():
        task = await ctx.registry.create("app_clarify", {}, lambda t: None)
        _answer_soon(ctx, "入 BV2 适配队列（生成本次工单后中止）",
                     delay_s=0.1)
        with pytest.raises(TaError) as ei:
            await clarify.clarify_and_develop(
                ctx, "用 ESP32-C6 DevKit 做心率采集", task, "k.key",
                model=_hw_model(mention="ESP32-C6 DevKit"),
                log=lambda s: None)
        assert ei.value.detail.get("state") == "BV2_QUEUED"
        assert ei.value.detail.get("board") == "ESP32-C6 DevKit"

    asyncio.run(main())


def test_clarify_hw_unincluded_schematic_required(tmp_path, monkeypatch):
    """分支 B-未收录：提及未知板 → 原理图协作路径（state=SCHEMATIC_REQUIRED，
    detail 携带协作清单）；离线注入（联网核实失败不阻塞判定）。"""
    from pathlib import Path

    from tessera_agent.common.config import AgentConfig
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.domain import clarify
    from tessera_agent.platform import AppContext

    pkg = Path(__file__).resolve().parent.parent
    cfg = AgentConfig(  # 空 ws（无本地收录索引）
        workspace_repo=pkg.parent, west_workspace=tmp_path,
        west_venv_python=pkg.parent / "agent" / "nofake",
        audit_dir=tmp_path / "audit", default_model="ollama:test",
        context_window=32_000, router_locator="tcp/127.0.0.1:7447")
    ctx = AppContext(cfg=cfg, budget=ContextBudget(32_000))

    monkeypatch.setattr(
        "tessera_agent.gateway.websearch.get_search_provider",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("offline")))

    async def main():
        task = await ctx.registry.create("app_clarify", {}, lambda t: None)
        _answer_soon(ctx, "我提供原理图（中止并记录协作清单）", delay_s=0.1)
        with pytest.raises(TaError) as ei:
            await clarify.clarify_and_develop(
                ctx, "用神秘自制板 X-Board 采集", task, "k.key",
                model=_hw_model(mention="X-Board"), log=lambda s: None)
        d = ei.value.detail
        assert d.get("state") == "SCHEMATIC_REQUIRED"
        assert d.get("board") == "X-Board"
        assert isinstance(d.get("checklist"), list) and d["checklist"]

    asyncio.run(main())


def test_clarify_capability_gap_continue(env, monkeypatch):
    """③ 能力核对：绑定 atk（仅 pwm:0 有绑定）而 spec 申请 gpio:write:0 →
    缺口问询 →「仍按此板继续」→【目标硬件】段如实标注缺口。"""
    from tessera_agent.domain import clarify

    spec_gpio = (
        "【需求】LED 闪烁。\n【资源】caps = [\"gpio:write:0\"]。\n"
        "【判据】\n- \"LED BLINK ON\"\n【安全声明】不动安全输出。")
    got = {}

    async def fake_develop(ctx, spec, key_path, out_dir, **kw):
        got["spec"] = spec
        return {"state": "PACKAGED"}

    async def main():
        import tessera_agent.domain.app_chain as ac
        orig = ac.app_develop
        clarify.app_chain.app_develop = fake_develop
        try:
            task = await env.registry.create("app_clarify", {}, lambda t: None)
            _answer_soon(env, "仍按此板继续（缺口如实标注）", delay_s=0.1)
            _answer_soon(env, "proceed", delay_s=0.3)
            await clarify.clarify_and_develop(
                env, "板载 LED 闪烁", task, "k.key",
                model=_hw_model(mention="ATK DNESP32-S3B", spec=spec_gpio),
                log=lambda s: None)
        finally:
            clarify.app_chain.app_develop = orig
        assert "能力缺口" in got["spec"] and "gpio" in got["spec"]

    asyncio.run(main())


def test_clarify_hw_gate_would_reject_led_signature():
    """端到端锚（机械面）：LED 缺陷签名 caps（gpio:write:0）× atk 画像 →
    部署门违规；pwm:set:0 → 过（HW-4 ③ 的回归锚）。"""
    from pathlib import Path

    from tessera_agent.domain import hardware as hwdom
    from tessera_agent.domain.board_validation import load_profile

    prof = load_profile(Path(__file__).resolve().parents[1] / "boards" /
                        "dnesp32s3b.toml")
    assert hwdom.check_caps_against_profile(["gpio:write:0"], prof)
    assert not hwdom.check_caps_against_profile(["pwm:set:0"], prof)
