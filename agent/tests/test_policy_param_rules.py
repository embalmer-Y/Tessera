# SPDX-License-Identifier: Apache-2.0
"""AG6 审批参数规则测试（Q-38⑤/LLD-A02 §3.1：求值序/AND 匹配/gated_tool 集成）。"""

from __future__ import annotations

import asyncio
import json

from tessera_agent.common.errors import TaError
from tessera_agent.core.session import (
    PolicyParamRules,
    PolicyTable,
    evaluate_param_rules,
    gated_tool,
)


def _policy() -> PolicyTable:
    return PolicyTable(
        entries={"deploy_push_app": "strict"},
        param_rules={
            "deploy_push_app": PolicyParamRules(
                allow={"cube": ["xiao-1"]},
                deny={"cube": ["prod-*"]},
            ),
        },
    )


def test_evaluation_order_deny_beats_allow():
    policy = _policy()
    # deny 命中（即便 allow 也匹配——按 LLD 求值序 deny 先）
    p = PolicyParamRules(allow={"cube": ["x"]}, deny={"cube": ["x"]})
    policy.param_rules["t"] = p
    assert evaluate_param_rules("t", {"cube": "x"}, policy) == "deny"


def test_evaluation_exact_and_semantics():
    policy = _policy()
    assert evaluate_param_rules(
        "deploy_push_app", {"cube": "xiao-1"}, policy) == "allow"
    assert evaluate_param_rules(
        "deploy_push_app", {"cube": "other"}, policy) is None  # 无命中 → 类别策略
    assert evaluate_param_rules(
        "deploy_push_app", {"cube": "prod-*"}, policy) == "deny"
    assert evaluate_param_rules("unknown_tool", {}, policy) is None
    # AND：多参数全匹配才 allow
    policy.param_rules["multi"] = PolicyParamRules(
        allow={"cube": ["c1"], "node": ["n1"]})
    assert evaluate_param_rules("multi", {"cube": "c1", "node": "n1"}, policy) == "allow"
    assert evaluate_param_rules("multi", {"cube": "c1", "node": "n2"}, policy) is None
    # str 归一：toml 数值 vs 工具 str 参数
    policy.param_rules["num"] = PolicyParamRules(allow={"timeout_s": [10]})
    assert evaluate_param_rules("num", {"timeout_s": "10"}, policy) == "allow"


class _RecordingBroker:
    """strict 桩：记录请求；wait 直接拒绝（测试 deny 路径）。"""

    def __init__(self):
        self.requests: list[str] = []

    def request(self, tool, preview, reason=""):
        self.requests.append(tool)
        return type("A", (), {"snapshot": lambda self: {}})()

    async def wait(self, approval, timeout_s=0):
        raise TaError(8, "审批拒绝/超时")


def _run(fn, **kw):
    return asyncio.run(fn(**kw))


async def _push_app(cube: str) -> str:
    return f"deployed:{cube}"


def test_gated_tool_allow_rule_bypasses_broker():
    broker = _RecordingBroker()
    wrapped = gated_tool("deploy_push_app", broker, category="strict",
                         policy=_policy())(_push_app)
    out = _run(wrapped, cube="xiao-1")
    assert out == "deployed:xiao-1"
    assert broker.requests == []  # allow 规则 = strict 自动放行（Q-38⑤ owner 语义）


def test_gated_tool_deny_rule_rejects():
    broker = _RecordingBroker()
    wrapped = gated_tool("deploy_push_app", broker, category="strict",
                         policy=_policy())(_push_app)
    out = _run(wrapped, cube="prod-*")
    assert "被拒绝" in out and "参数规则" in out
    payload = json.loads(out.split("：", 1)[1])
    assert payload["code"] == 8
    assert broker.requests == []


def test_gated_tool_no_rule_goes_to_broker():
    broker = _RecordingBroker()
    wrapped = gated_tool("deploy_push_app", broker, category="strict",
                         policy=_policy())(_push_app)
    out = _run(wrapped, cube="other-cube")
    assert "被拒绝" in out
    assert broker.requests == ["deploy_push_app"]  # 类别策略照常（无规则命中）


def test_compose_apply_param_rules():
    from tessera_agent.domain.firmware import FirmwareDomainPack
    from tessera_agent.gateway.compose import apply_param_rules

    pack = FirmwareDomainPack()
    n = apply_param_rules(pack, {
        "deploy_push_app": {"allow": {"cube": ["xiao-1"]}},
        "bad-entry": "not-a-dict",  # 坏条目跳过不静默生效
    })
    assert n == 1
    rules = pack.policy.param_rules["deploy_push_app"]
    assert rules.allow == {"cube": ["xiao-1"]}
    assert "bad-entry" not in pack.policy.param_rules


def test_config_loads_param_rules(tmp_path):
    from tessera_agent.common.config import load_config

    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        '[providers]\ndefault_model = "openai:test"\n\n'
        "[policy.param_rules.deploy_push_app]\n"
        '[policy.param_rules.deploy_push_app.allow]\ncube = ["xiao-1"]\n',
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    assert cfg.policy_param_rules["deploy_push_app"]["allow"]["cube"] == ["xiao-1"]
