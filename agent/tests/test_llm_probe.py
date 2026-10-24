# SPDX-License-Identifier: Apache-2.0
"""llm_probe · LLM 端点探针测试（DEC-80——URL 校验/协议检测/鉴权面判定/冒烟/异常分类）。

全部经 httpx.MockTransport 注入——零真实网络；密钥红线断言贯穿（报告不含 key）。
"""
from __future__ import annotations

import json

import httpx
import pytest

from tessera_agent.domain import llm_probe
from tessera_agent.domain.firmware import FirmwareDomainPack

KEY = "sk-test-key-should-never-leak-0123456789abcdef"


def _transport(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _ok_json(status: int, payload: dict) -> httpx.Response:
    return httpx.Response(status, json=payload)


# ---------- URL 静态校验 ----------
def test_validate_url_rejects_bad_forms():
    assert llm_probe.validate_url("") == ["URL 为空"]
    assert any("协议" in i for i in llm_probe.validate_url("ftp://h/x"))
    assert any("空白" in i for i in llm_probe.validate_url("https://h/ a\r\nx"))
    assert any("主机名" in i for i in llm_probe.validate_url("https:///path"))
    assert any(".." in i for i in llm_probe.validate_url("https://h/../etc"))


def test_validate_url_accepts_and_hints_version_segment():
    issues = llm_probe.validate_url("https://router.example.com/api/v1")
    assert issues == [] or all(i.startswith("提示") for i in issues)
    assert any("版本段" in i for i in llm_probe.validate_url("https://router.example.com"))


# ---------- 双协议检测 + 模型表三形态 ----------
def _dual_router_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/models"):
        if "x-api-key" in request.headers:   # anthropic 形态
            return _ok_json(200, {"data": [{"id": "bigmodel/glm-5.3-flash"},
                                           {"id": "openai/gpt-6-astra"}]})
        return _ok_json(200, {"data": [{"api_name": "bigmodel/glm-5.3-flash",
                                        "company": "OpenAI"}]})   # 路由扩展形态
    if request.url.path.endswith("/messages"):
        assert request.headers["x-api-key"] == KEY
        return _ok_json(200, {"model": "bigmodel/glm-5.3-flash",
                              "content": [{"type": "thinking", "thinking": "..."},
                                          {"type": "text", "text": "通"}],
                              "usage": {"input_tokens": 3, "output_tokens": 16}})
    return _ok_json(404, {"error": {"message": "no route"}})


def test_probe_dual_protocol_full_pass():
    rep = llm_probe.probe("https://router.example.com/api/v1", KEY,
                          transport=_transport(_dual_router_handler))
    assert rep.url_valid and rep.overall_ok
    assert rep.protocols == {"openai": True, "anthropic": True}
    assert rep.models["count"] == 2          # api_name 与 id 归一去重
    assert "bigmodel/glm-5.3-flash" in rep.models["sample"]
    assert rep.key_valid["ok"] is True
    mc = rep.model_check
    assert mc["ok"] and mc["model"] == "bigmodel/glm-5.3-flash"   # flash 自动优选
    assert mc["text"] == "通"                                     # thinking 块被滤除
    assert mc["usage"]["output_tokens"] == 16
    sug = rep.suggestion
    assert sug["provider_prefix"] == "anthropic"
    assert sug["model_string"] == "anthropic:bigmodel/glm-5.3-flash"
    assert sug["env"] == {"base": "ANTHROPIC_BASE_URL", "key": "ANTHROPIC_API_KEY"}
    # 凭据红线：报告 JSON 全文不含 key
    assert KEY not in json.dumps(rep.to_dict(), ensure_ascii=False)


def test_probe_openai_only_falls_back():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models") and "x-api-key" not in request.headers:
            return _ok_json(200, {"data": [{"id": "qwen3-max"}]})
        if request.url.path.endswith("/chat/completions"):
            return _ok_json(200, {"model": "qwen3-max",
                                  "choices": [{"message": {"content": "ok"}}],
                                  "usage": {"prompt_tokens": 1, "completion_tokens": 5}})
        return _ok_json(404, {"error": {}})
    rep = llm_probe.probe("https://oa.example.com/v1", KEY,
                          transport=_transport(handler))
    assert rep.protocols == {"openai": True, "anthropic": False}
    assert rep.suggestion["provider_prefix"] == "openai"
    assert rep.suggestion["model_string"] == "openai:qwen3-max"
    assert rep.overall_ok


# ---------- /models 不鉴权 + 鉴权面 401（实测路由行为） ----------
def test_models_unauthenticated_key_judged_by_auth_surface():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return _ok_json(200, {"data": [{"id": "m1"}]})   # 不校验头——坏 key 也 200
        return _ok_json(401, {"error": {"code": "invalid_api_key",
                                        "message": "invalid token"}})
    rep = llm_probe.probe("https://x.example.com/v1", "sk-wrong",
                          transport=_transport(handler))
    assert rep.reachability["ok"] and rep.models["count"] == 1
    assert rep.key_valid["ok"] is False and "401" in rep.key_valid["detail"]
    assert rep.model_check["detail"] == "未测——key 无效"
    assert not rep.overall_ok


# ---------- 状态分类 ----------
def test_status_classification_429_and_404_model():
    def make(status_models, status_chat, body_chat):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/models"):
                return _ok_json(status_models, {"data": [{"id": "m1"}]})
            return _ok_json(status_chat, body_chat)
        return handler

    rep = llm_probe.probe("https://a.example.com/v1", KEY, transport=_transport(
        make(200, 429, {"error": {"message": "rate limited"}})))
    assert rep.key_valid["ok"] is True            # 429 ≠ key 无效
    assert rep.model_check["ok"] is None          # 可用性无法判定（◐）

    rep = llm_probe.probe("https://b.example.com/v1", KEY, transport=_transport(
        make(200, 404, {"error": {"message": "model not found"}})))
    assert rep.key_valid["ok"] is True
    assert rep.model_check["ok"] is False and "模型不存在" in rep.model_check["detail"]


# ---------- 网络异常分类 ----------
def test_network_exception_classification():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("dns failure")
    rep = llm_probe.probe("https://down.example.com/v1", KEY,
                          transport=_transport(handler))
    assert rep.reachability["ok"] is False
    assert "DNS" in rep.reachability["error_class"]
    assert "代理" in rep.reachability["hint"]

    def handler2(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out")
    rep2 = llm_probe.probe("https://slow.example.com/v1", KEY,
                           transport=_transport(handler2))
    assert rep2.reachability["error_class"] == "超时"


# ---------- 非法 URL 短路（零网络） ----------
def test_invalid_url_short_circuits_without_network():
    rep = llm_probe.probe("ftp://bad host", KEY,
                          transport=_transport(lambda r: pytest.fail("不应发请求")))
    assert not rep.url_valid and not rep.overall_ok


# ---------- 人读渲染 ----------
def test_render_report_shape():
    rep = llm_probe.probe("https://router.example.com/api/v1", KEY,
                          transport=_transport(_dual_router_handler))
    text = llm_probe.render_report(rep)
    for kw in ("URL 合法性", "连通性", "协议", "模型列表", "KEY 有效性",
               "模型可用性", "配置建议", "总判定"):
        assert kw in text
    assert KEY not in text


# ---------- MCP 注册面 ----------
def test_llm_check_registered_confirm_class():
    pack = FirmwareDomainPack()
    assert "llm_check" in pack.tools
    assert pack.policy.entries["llm_check"] == "confirm"
