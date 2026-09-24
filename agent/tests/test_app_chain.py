# SPDX-License-Identifier: Apache-2.0
"""高层链测试（DEC-34；LLD-A02 §4 S2/S5）：app_develop（FunctionModel 剧本）/
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
    "exports": ["health_ping", "tick"],
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
        _ctx(tmp_path), "做一个演示 APP", str(_wasm(tmp_path)), key,
        out_dir=str(tmp_path), model=_model(_VALID_MANIFEST), log_fn=logs.append,
    ))
    assert out["manifest"] == _VALID_MANIFEST
    assert Path(out["package_path"]).is_file() and out["package_size"] > 16
    assert out["skills_active"] == ["tessera-build", "tessera-safety",
                                    "tessera-tsap", "tessera-workflow"]
    assert any("read_skill" in ln or "skills active" in ln for ln in logs)
    tsap_tools.tsap_verify(out["package_path"], out["pub_key_path"])  # 产物可独立复验


def test_app_develop_invalid_manifest_refused(tmp_path, keys):
    bad = dict(_VALID_MANIFEST, exports=["tick"])  # 缺 health_ping
    with pytest.raises(TaError):
        asyncio_run(app_chain.app_develop(
            _ctx(tmp_path), "spec", str(_wasm(tmp_path)), keys[0],
            out_dir=str(tmp_path), model=_model(bad, skill_probe=False),
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
