# SPDX-License-Identifier: Apache-2.0
"""高层链测试（DEC-34；LLD-agent-core §4 S2/S5）：app_develop（FunctionModel 剧本）/
app_deploy（FakeCube 全链）。不依赖 LLM 与网络。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from test_deploy import FakeCube, _make_pkg  # 复用语义桩与包构造

from tessera_agent.common.errors import TA_E_ARGS, TaError
from tessera_agent.domain import app_chain
from tessera_agent.platform import AppContext
from tessera_agent.tools_tsap import tools as tsap_tools


def asyncio_run(coro):
    return asyncio.run(coro)


def _ctx(tmp_path: Path) -> AppContext:
    class Cfg:
        audit_dir = tmp_path / "audit"
        workspace_repo = tmp_path
        default_model = "ollama:test"
        router_locator = "tcp://unused"

    from tessera_agent.common.limits import ContextBudget
    return AppContext(cfg=Cfg(), budget=ContextBudget(32_000),
                      write_roots=[str(tmp_path)])


_VALID_MANIFEST = {
    "app_id": "com.t.chain", "app_ver": "2.0.0", "min_fw_ver": "0.1.0",
    "caps": [], "stack_kb": 4, "heap_kb": 16,
    "exports": ["health_ping", "app_tick"],
}


def _model(manifest: dict, skill_probe: bool = True) -> FunctionModel:
    """剧本模型：可选 read_skill 探针 → 输出 DevelopOutcome JSON。"""
    state = {"probed": False}

    async def fn(messages, info) -> ModelResponse:
        if skill_probe and not state["probed"]:
            state["probed"] = True
            return ModelResponse(parts=[ToolCallPart("read_skill",
                                                     {"name": "tessera-safety"})])
        payload = {
            "requirements_summary": "demo spec",
            "manifest": manifest,
            "safety_notes": ["n1"],
            "test_plan": ["t1"],
            "steps": ["s1"],
        }
        return ModelResponse(parts=[TextPart(content=json.dumps(payload))])

    return FunctionModel(fn)


def _wasm(tmp_path: Path) -> Path:
    w = tmp_path / "a.wasm"
    w.write_bytes(b"\x00asm\x01\x00\x00\x00" + b"CHAIN" * 8)
    return w


@pytest.fixture()
def keys(tmp_path: Path):
    tsap_tools.tsap_keygen("k", str(tmp_path), [str(tmp_path)])
    return str(tmp_path / "k.key"), str(tmp_path / "k.pub")


def test_app_develop_full_chain(tmp_path, keys):
    key, _pub = keys
    logs: list[str] = []
    out = asyncio_run(app_chain.app_develop(
        _ctx(tmp_path), "做一个演示 APP", key,
        out_dir=str(tmp_path), wasm_path=str(_wasm(tmp_path)),
        model=_model(_VALID_MANIFEST), log_fn=logs.append,
    ))
    assert out["manifest"] == _VALID_MANIFEST
    assert Path(out["package_path"]).is_file() and out["package_size"] > 16
    assert out["skills_active"] == ["tessera-build", "tessera-safety",
                                    "tessera-tsap", "tessera-workflow"]
    assert any("read_skill" in ln or "skills active" in ln for ln in logs)
    tsap_tools.tsap_verify(out["package_path"], out["pub_key_path"])  # 产物可独立复验


_LOOP_MANIFEST = {
    "app_id": "com.t.loop", "app_ver": "1.0.0", "min_fw_ver": "0.1.0",
    "caps": [], "stack_kb": 4, "heap_kb": 16,
    "exports": ["health_ping", "app_tick"],
}

_GOOD_SRC = (
    "int health_ping(void) { return 0; }\n"
    "int app_tick(void) { return 1; }\n"
)
_BAD_SRC = "int health_ping(void) { return 0; }\n"  # 缺 app_tick → 面门拦


def _loop_model(bad_first: bool):
    """创作循环剧本：plan → implement r1（ws_write 源〔可先坏〕+ done+manifest）
    →（若坏源）r2 修好 → done。单 FunctionModel 状态机按调用序分派。"""
    from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart
    from pydantic_ai.models.function import FunctionModel

    calls = {"n": 0}

    async def fn(messages, info) -> ModelResponse:
        calls["n"] += 1
        n = calls["n"]
        if n == 1:  # plan
            payload = {"requirements_summary": "loop demo",
                       "safety_notes": ["n"], "test_plan": ["t"],
                       "steps": ["主逻辑", "验证"]}
            return ModelResponse(parts=[TextPart(content=json.dumps(payload))])
        if n == 2:  # implement r1：写源文件
            src = _BAD_SRC if bad_first else _GOOD_SRC
            return ModelResponse(parts=[ToolCallPart(
                "ws_write", {"path": "main.c", "content": src})])
        if n == 3:  # implement r1：声明完成 + manifest
            payload = {"declared_done": True, "summary": "v1",
                       "manifest": _LOOP_MANIFEST, "app_id": "com.t.loop"}
            return ModelResponse(parts=[TextPart(content=json.dumps(payload))])
        # n == 4/5（仅 bad_first）：r2 修好源并再声明
        if n == 4:
            return ModelResponse(parts=[ToolCallPart(
                "ws_write", {"path": "main.c", "content": _GOOD_SRC})])
        payload = {"declared_done": True, "summary": "v2",
                   "manifest": _LOOP_MANIFEST}
        return ModelResponse(parts=[TextPart(content=json.dumps(payload))])

    return FunctionModel(fn)


def test_app_develop_loop_converges(tmp_path, keys):
    """AG6 创作循环路径：plan → ws_write 多轮编辑 → 真编译/面检查 → 打包
    复验；返回键与单发流兼容 + 循环新键。"""
    key, _pub = keys
    logs: list[str] = []
    out = asyncio_run(app_chain.app_develop(
        _ctx(tmp_path), "呼吸灯", key,
        model=_loop_model(bad_first=False), log_fn=logs.append,
    ))
    assert out["state"] == "PACKAGED" and out["rounds"] == 1
    assert out["compiled"] is True
    assert out["manifest"] == _LOOP_MANIFEST
    assert out["task_id"].startswith("t-") and out["task_id"] in out["workspace"]
    assert Path(out["package_path"]).is_file()
    assert out["compile_facts"]["exports"] == ["app_tick", "health_ping"]
    tsap_tools.tsap_verify(out["package_path"], out["pub_key_path"])
    assert any(ln.startswith("loop:state") or "loop:" in ln for ln in logs)


def test_app_develop_loop_evidence_round_fixes(tmp_path, keys):
    """AG6 证据回喂：r1 坏源（缺导出）→ 面门证据 → r2 修复收敛。"""
    key, _pub = keys
    out = asyncio_run(app_chain.app_develop(
        _ctx(tmp_path), "呼吸灯", key,
        model=_loop_model(bad_first=True),
    ))
    assert out["state"] == "PACKAGED" and out["rounds"] == 2
    assert out["compile_facts"]["exports"] == ["app_tick", "health_ping"]


def test_app_develop_invalid_manifest_refused(tmp_path, keys):
    bad = dict(_VALID_MANIFEST, exports=["app_tick"])  # 缺 health_ping
    with pytest.raises(TaError):
        asyncio_run(app_chain.app_develop(
            _ctx(tmp_path), "spec", keys[0],
            out_dir=str(tmp_path), wasm_path=str(_wasm(tmp_path)),
            model=_model(bad, skill_probe=False),
        ))


class FakeService(FakeCube):
    """FakeCube + 上下文管理器形态（app_deploy 经 with 使用）。"""

    def __init__(self, *a, **kw) -> None:
        super().__init__(*a, **kw)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_app_deploy_full_chain_auto_target(tmp_path, keys, monkeypatch):
    pkg, pub, _raw = _make_pkg(tmp_path)
    fake = FakeService()
    monkeypatch.setattr(app_chain, "ZenohService",
                        lambda locator, **kw: fake)
    logs: list[str] = []
    out = asyncio_run(app_chain.app_deploy(
        _ctx(tmp_path), pkg, pub, log_fn=logs.append,
    ))
    assert out["node"] == "fn" and out["cube"] == "fc", "自动定位恰一在线 cube"
    assert out["deploy"]["confirmed"] is True
    assert fake.activate_calls == 1 and fake.lease_holder is None


def test_app_deploy_tampered_refused_before_push(tmp_path, keys, monkeypatch):
    pkg, pub, raw = _make_pkg(tmp_path)
    data = bytearray(raw)
    data[-1] ^= 0xFF
    Path(pkg).write_bytes(bytes(data))
    fake = FakeService()
    monkeypatch.setattr(app_chain, "ZenohService", lambda locator, **kw: fake)
    with pytest.raises(TaError):
        asyncio_run(app_chain.app_deploy(_ctx(tmp_path), pkg, pub))
    assert fake.chunks == {}, "复验拒绝必须发生在任何分块之前"


def test_app_deploy_node_cube_pairing(tmp_path, keys):
    pkg, pub, _ = _make_pkg(tmp_path)
    with pytest.raises(TaError) as ei:
        asyncio_run(app_chain.app_deploy(_ctx(tmp_path), pkg, pub, node="n1"))
    assert ei.value.code == TA_E_ARGS
