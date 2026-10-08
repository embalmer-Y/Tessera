# SPDX-License-Identifier: Apache-2.0
"""sim_run 执行器（LLD-A04 §2；M1 定稿的 L4 接口 + G5/单元 H 输入文件实装）。

流程：校验场景 → west build 构建 framework.replay 镜像（native_sim）→
**场景 inputs 落 replay_script.tsv（cwd = 构建目录；固件 test_00 脚本会话
读取——"输入文件进"接口自此实装，编译期内嵌场景仅作 twister 内建兜底）** →
直接执行测试二进制（stdout JSONL 写序列 + 退出码）→ 解析 → 期望评估
（eq/within/count）→ 双跑比对（determinism，合同 9 Agent 侧机械验证）→
报告（timeline_digest = 写序列 sha256 重放指纹）。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from tessera_agent.common.config import AgentConfig
from tessera_agent.common.errors import TA_E_ARGS, TA_E_SIM, TaError
from tessera_agent.common.proc import run_proc
from tessera_agent.tools_sim.scenario import Scenario

_JSONL_RE = re.compile(r'\{"t_ms":\d+,"ch":"[^"]+","value_u":\d+\}')
_FW_BUILD_TIMEOUT_S = 1800  # 来源: DEC-38 #4（同 fw_build 档）

# 脚本会话输出通道（固件 tests/replay test_00 注册面；LLD-A04 §1「通道名在
# 固件测试配置面内」的 V1 事实）
_SCRIPT_CHANNELS = frozenset({"rep_c", "rep_d"})


def script_lines(inputs: list) -> list[str]:
    """Scenario.inputs → 重放脚本行（G5/单元 H）。

    ch 命名空间约定（与固件脚本会话的行格式一一对应）：
      "link"   → ``<t> link <0|1>``（链路态）
      "estop"  → ``<t> estop``（急停；value 忽略；全通道 fault 值落驱动）
      "in:<n>" → ``<t> input <n> <mv>``（ADC 注入；首拍建基线无回显——
                 传输级变化语义，变化才发 INPUT_CHANGED）
      其他     → ``<t> commit <ch> <v>``（输出通道直驱；V1 = rep_c/rep_d，
                 slew 5/ms 限幅 0..1000——期望值按规格推导）
    """
    lines: list[str] = []
    for i in inputs:
        v = int(i.value) if isinstance(i.value, bool) else int(i.value)
        if i.ch == "link":
            lines.append(f"{i.t_ms} link {v}")
        elif i.ch == "estop":
            lines.append(f"{i.t_ms} estop")
        elif i.ch.startswith("in:"):
            inst = i.ch[3:]
            if not inst.isdigit() or int(inst) > 1:
                msg = f"输入实例越界（V1 = in:0/in:1）: {i.ch}"
                raise TaError(TA_E_ARGS, msg, domain="sim")
            if v < 0:
                msg = f"输入 mv 须非负（JSONL 采集域）: {i.ch}={v}"
                raise TaError(TA_E_ARGS, msg, domain="sim")
            lines.append(f"{i.t_ms} input {inst} {v}")
        elif i.ch in _SCRIPT_CHANNELS:
            lines.append(f"{i.t_ms} commit {i.ch} {v}")
        else:
            msg = f"输出通道不在固件脚本会话配置面（V1 = rep_c/rep_d）: {i.ch}"
            raise TaError(TA_E_ARGS, msg, domain="sim")
    return lines


def _west_bin(cfg: AgentConfig) -> str:
    return os.path.join(os.path.dirname(str(cfg.west_venv_python)), "west")


async def _replay_build(cfg: AgentConfig, build_dir: Path, log_fn) -> None:
    """构建 framework.replay 测试镜像（native_sim；复用既有 build 目录增量构建）。"""
    module = cfg.workspace_repo / "firmware" / "module" / "tessera"
    cmd = [
        _west_bin(cfg), "build", "-b", "native_sim",
        str(cfg.workspace_repo / "firmware" / "tests" / "replay"),
        "-d", str(build_dir), "--",
        f"-DZEPHYR_EXTRA_MODULES={module}",
    ]
    await run_proc(
        cmd, cwd=str(cfg.west_workspace), timeout_s=_FW_BUILD_TIMEOUT_S,
        budget=None, log_fn=log_fn,
    )


async def _replay_run_once(cfg: AgentConfig, build_dir: Path, log_fn) -> list[dict[str, Any]]:
    """直接执行重放测试二进制（M1 定稿 L4 接口：stdout JSONL + 退出码）。"""
    exe = build_dir / "zephyr" / "zephyr.exe"
    if not exe.is_file():
        msg = f"重放测试二进制不存在: {exe}"
        raise TaError(TA_E_SIM, msg, domain="sim")
    captured: list[str] = []

    def tap(line: str) -> None:
        captured.append(line)
        if log_fn is not None:
            log_fn(line)

    out = await run_proc(
        [str(exe)], cwd=str(build_dir), timeout_s=60, budget=None, log_fn=tap,
    )
    writes = []
    for line in captured:
        for m in _JSONL_RE.finditer(line):
            rec = json.loads(m.group(0))
            rec["value_u"] = int(rec["value_u"])
            rec["t_ms"] = int(rec["t_ms"])
            writes.append(rec)
    if not writes:
        msg = "二进制输出未解析到 JSONL 写序列"
        raise TaError(TA_E_SIM, msg, domain="sim", detail={"tail": out["tail"][-10:]})
    return writes


def _evaluate(writes: list[dict[str, Any]], exps: list) -> dict[str, Any]:
    results = []
    for e in exps:
        ch_writes = [w for w in writes if w["ch"] == e.ch]
        got = [w["value_u"] for w in ch_writes]
        ok = False
        detail: dict[str, Any] = {"op": e.op, "ch": e.ch, "values": got[:8]}
        if e.op == "eq" and got:
            ok = got[-1] == e.value
            detail["expected_last"] = e.value
        elif e.op == "within" and got:
            ok = abs(got[-1] - e.value) <= e.tolerance
            detail["expected_within"] = [e.value - e.tolerance, e.value + e.tolerance]
        elif e.op == "count":
            ok = len(got) == e.value
            detail["expected_count"] = e.value
        detail["pass"] = ok
        results.append(detail)
    failed = [r for r in results if not r["pass"]]
    return {"pass": not failed, "assertions": results, "failed": len(failed)}


async def sim_run(cfg: AgentConfig, scenario: dict, *, task_id: str, log_fn=None) -> dict:
    try:
        sc = Scenario(**scenario)
    except Exception as exc:  # noqa: BLE001
        raise TaError(TA_E_ARGS, f"场景非法: {exc}", domain="sim") from exc

    base = cfg.workspace_repo / "agent" / "build" / task_id
    build = base / "build"
    await _replay_build(cfg, build, log_fn)
    # 场景脚本落盘（cwd = 构建目录；固件脚本会话经 cwd 相对路径读取）——
    # 留档任务目录便于排查（task_id 唯一，无跨任务残留）。
    script = build / "replay_script.tsv"
    script.write_text("\n".join(script_lines(sc.inputs)) + "\n", encoding="utf-8")
    run1 = await _replay_run_once(cfg, build, log_fn)
    run2 = await _replay_run_once(cfg, build, log_fn)

    determinism = run1 == run2  # 双跑逐项一致（合同 9 Agent 侧机械验证）
    evaluation = _evaluate(run1, sc.expectations)
    digest = hashlib.sha256(
        json.dumps(run1, sort_keys=False).encode()
    ).hexdigest()[:16]

    report = {
        "scenario_inputs": len(sc.inputs),
        "writes": len(run1),
        "determinism": determinism,
        "timeline_digest": digest,
        "evaluation": evaluation,
    }
    if not determinism:
        msg = "确定性比对失败（两次运行写序列不一致）"
        raise TaError(TA_E_SIM, msg, domain="sim", detail=report)
    if not evaluation["pass"]:
        msg = f"场景断言失败 {evaluation['failed']} 项"
        raise TaError(TA_E_SIM, msg, domain="sim", detail=report)
    return report
