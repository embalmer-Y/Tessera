# SPDX-License-Identifier: Apache-2.0
"""逻辑节点编排器（V0.4.x 补批 M16，DEC-54①/Q-35 方案 A）。

LN（Logical Node）= Agent 层编排对象：多 cube 并联为一个业务单元。
固件零改动（zenoh 键空间天然支持按成员寻址）；V1 安全合同不变——每 cube
独立 fail-closed 闭环，组语义 = 本层策略：
  - ln_create/ln_list/ln_remove：成员注册表（内存态——MCP server 生存期）；
  - ln_deploy：**顺序扇出** push_app 至各成员（非原子——部分失败如实逐
    成员呈现，聚合视图标注 deployed/failed/skipped）；
  - ln_status：逐成员组合快照（deploy.status）→ 聚合视图 + 降级判定
    （成员不可达 = linkloss 降级位，policy.continue 显示继续语义提示）；
  - ln_estop_clear：组恢复操作——扇出 sys/estop-clear（confirm 硬令牌，
    幂等安全）。
已知限制（Q-35 如实登记）：Agent 单点（编排可用性依赖 PC 侧）；组操作
非原子（顺序执行，失败成员部分应用）。
"""
from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tessera_agent.common.errors import TA_E_ARGS, TaError
from tessera_agent.tools_net import deploy, keys


@dataclass
class LnMember:
    node: str
    cube: str


@dataclass
class LogicalNode:
    ln_id: str
    members: list[LnMember]
    linkloss_policy: str = "continue"  # continue | pause（降级语义提示）

    def find(self, node: str, cube: str) -> bool:
        return any(m.node == node and m.cube == cube for m in self.members)


class LnRegistry:
    """内存态注册表（MCP server 生存期；持久化随真实多 cube 部署批再议）。"""

    def __init__(self) -> None:
        self._nodes: dict[str, LogicalNode] = {}

    def create(self, ln_id: str, members: list[tuple[str, str]],
               linkloss_policy: str = "continue") -> LogicalNode:
        if not ln_id or len(ln_id) > 32 or any(c not in
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                for c in ln_id):
            msg = f"ln_id 非法（1-32 字符，[A-Za-z0-9-_]）: {ln_id!r}"
            raise TaError(TA_E_ARGS, msg, domain="lno")
        if linkloss_policy not in ("continue", "pause"):
            msg = f"linkloss_policy ∈ continue|pause: {linkloss_policy!r}"
            raise TaError(TA_E_ARGS, msg, domain="lno")
        if not members:
            msg = "members 不可为空（LN ≥ 1 成员）"
            raise TaError(TA_E_ARGS, msg, domain="lno")
        if ln_id in self._nodes:
            msg = f"ln_id 已存在: {ln_id!r}"
            raise TaError(TA_E_ARGS, msg, domain="lno")
        seen: set[tuple[str, str]] = set()
        mlist: list[LnMember] = []
        for node, cube in members:
            if not node or not cube or (node, cube) in seen:
                msg = f"成员非法或重复: {node}/{cube}"
                raise TaError(TA_E_ARGS, msg, domain="lno")
            seen.add((node, cube))
            mlist.append(LnMember(node=node, cube=cube))
        ln = LogicalNode(ln_id=ln_id, members=mlist,
                         linkloss_policy=linkloss_policy)
        self._nodes[ln_id] = ln
        return ln

    def remove(self, ln_id: str) -> None:
        if ln_id not in self._nodes:
            msg = f"ln_id 不存在: {ln_id!r}"
            raise TaError(TA_E_ARGS, msg, domain="lno")
        del self._nodes[ln_id]

    def get(self, ln_id: str) -> LogicalNode:
        if ln_id not in self._nodes:
            msg = f"ln_id 不存在: {ln_id!r}"
            raise TaError(TA_E_ARGS, msg, domain="lno")
        return self._nodes[ln_id]

    def list(self) -> list[dict[str, Any]]:
        return [{"ln_id": ln.ln_id,
                 "members": [{"node": m.node, "cube": m.cube} for m in ln.members],
                 "linkloss_policy": ln.linkloss_policy}
                for ln in self._nodes.values()]


# MCP server 生存期单例（内存态注册表；组合根经 build_app 装配时引用）
REGISTRY = LnRegistry()


# ---- 编排操作（svc = ZenohService；逐成员诚实扇出）--------------------------


def _fanout(ln: LogicalNode, op_desc: str, per_member: Callable[[LnMember], Any],
            log: Callable[[str], None]) -> dict[str, Any]:
    """顺序扇出：成员失败不中断后续（非原子如实）；聚合逐成员结果。"""
    results: list[dict[str, Any]] = []
    failed = 0
    for m in ln.members:
        entry: dict[str, Any] = {"node": m.node, "cube": m.cube}
        try:
            entry["result"] = per_member(m)
            entry["ok"] = True
        except TaError as exc:
            entry["ok"] = False
            entry["error"] = exc.to_payload()
            failed += 1
            log(f"{op_desc} 成员失败 {m.node}/{m.cube}: {exc.message}")
        results.append(entry)
    return {"ln_id": ln.ln_id, "op": op_desc, "members": results,
            "failed": failed, "ok": failed == 0}


def ln_deploy(registry: LnRegistry, svc, ln_id: str, package_path: str,
              pub_key_path: str, *, app: int = 1,
              log_fn: Callable[[str], None] | None = None) -> dict[str, Any]:
    """组部署：顺序扇出 push_app（非原子——聚合视图标注 deployed/failed）。"""
    log = log_fn or (lambda s: None)
    ln = registry.get(ln_id)

    def one(m: LnMember) -> dict[str, Any]:
        return deploy.push_app(svc, m.node, m.cube, package_path,
                               pub_key_path, app=app, log_fn=log)

    return _fanout(ln, "deploy", one, log)


def ln_status(registry: LnRegistry, svc, ln_id: str,
              log_fn: Callable[[str], None] | None = None) -> dict[str, Any]:
    """组状态聚合：逐成员四合一快照；不可达 = linkloss 降级位。"""
    log = log_fn or (lambda s: None)
    ln = registry.get(ln_id)

    def one(m: LnMember) -> dict[str, Any]:
        return deploy.status(svc, m.node, m.cube)

    out = _fanout(ln, "status", one, log)
    degraded = [e["node"] + "/" + e["cube"] for e in out["members"]
                if not e["ok"]]
    out["degraded_members"] = degraded
    out["linkloss_policy"] = ln.linkloss_policy
    if degraded and ln.linkloss_policy == "pause":
        out["policy_hint"] = ("pause 策略：降级成员存在——编排操作（如组部署）"
                              "应暂停直至恢复（owner 策略语义，本层提示）")
    return out


def ln_estop_clear(registry: LnRegistry, svc, ln_id: str,
                   log_fn: Callable[[str], None] | None = None) -> dict[str, Any]:
    """组恢复：扇出 sys/estop-clear（confirm 硬令牌；幂等安全——V1 合同
    内操作，不引入新安全语义）。"""
    log = log_fn or (lambda s: None)
    ln = registry.get(ln_id)
    tag = secrets.token_hex(3)

    def one(m: LnMember) -> dict[str, Any]:
        from tessera_agent.tools_net.deploy import _cmd_ok
        return _cmd_ok(svc, m.node, m.cube, "estop-clear",
                       f"ln-ec-{tag}"[:keys.RID_MAX], confirm="estop")

    return _fanout(ln, "estop-clear", one, log)
