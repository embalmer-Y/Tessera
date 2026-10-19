# SPDX-License-Identifier: Apache-2.0
"""组合根（LLD-A07 §3）：显式注册 DomainPack——平台与域在此汇合。

新增域 = 在此处追加注册（或经多域编排配置注入），平台/域代码零改动。
"""

from __future__ import annotations

from fastmcp import FastMCP

from tessera_agent.core.session import PolicyParamRules
from tessera_agent.domain.firmware import FirmwareDomainPack
from tessera_agent.gateway.hooks import HookChain, parse_rules
from tessera_agent.platform import AppContext, assemble


def apply_param_rules(pack: FirmwareDomainPack, rules: dict) -> int:
    """config [policy.param_rules] 并入 DomainPack 策略表（Q-38⑤）。

    返回并入条数；deny/allow 形态非法的条目跳过（启动期容错——config 为
    人工维护面，坏条目不静默生效）。"""
    n = 0
    for tool, spec in (rules or {}).items():
        if not isinstance(spec, dict):
            continue
        try:
            deny = {k: list(v) for k, v in dict(spec.get("deny", {})).items()}
            allow = {k: list(v) for k, v in dict(spec.get("allow", {})).items()}
        except TypeError:
            continue
        pack.policy.param_rules.setdefault(
            tool, PolicyParamRules(deny=deny, allow=allow))
        n += 1
    return n


def build_app(ctx: AppContext) -> FastMCP:
    """装配完整 tessera-agent（V1 单域 = firmware）。"""
    pack = FirmwareDomainPack()
    apply_param_rules(pack, getattr(ctx.cfg, "policy_param_rules", {}))
    # D4（DEC-67①）：网关钩子链并入（config [hooks]；坏条目跳过不静默生效）
    ctx.hooks = HookChain(parse_rules(getattr(ctx.cfg, "hooks", None)))
    return assemble(ctx, [pack])
