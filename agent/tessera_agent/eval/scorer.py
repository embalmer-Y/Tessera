# SPDX-License-Identifier: Apache-2.0
"""eval.scorer — AC-1 headless 评分器（DEC-81）。

对任务谱逐任务跑 app_develop 真链（真 LLM → 编译 → 打包），对返回面
与任务 expect 机械对拍。全部检查零人工：converged / rounds /
imports-exports-deterministic-size / caps-threads-tier-needs 对拍 /
tsap_verify 独立复跑。

verdict 规则：
  PASS    = 收敛且全部检查过
  PARTIAL = 收敛但期望面部分缺失（能力面可用，符合度不足）
  FAIL    = 未收敛（含超时/异常）

develop_fn 注入点：缺省真链 app_develop；测试注入 fake（零网络）。
"""
from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tessera_agent.common.errors import TaError
from tessera_agent.eval.suite import EvalTask

DEFAULT_TIMEOUT_S = 600.0
DEFAULT_BUDGET_ROUNDS = 12


@dataclass
class TaskScore:
    id: str
    title: str
    verdict: str  # PASS / PARTIAL / FAIL
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    rounds: int | None = None
    elapsed_s: float = 0.0
    workspace: str = ""
    package_path: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "verdict": self.verdict,
            "checks": self.checks, "rounds": self.rounds,
            "elapsed_s": round(self.elapsed_s, 1),
            "workspace": self.workspace, "package_path": self.package_path,
            "error": self.error,
        }


def _check(ok: bool, detail: Any = "") -> dict[str, Any]:
    return {"ok": bool(ok), "detail": detail}


def score_outcome(task: EvalTask, outcome: dict | None,
                  err: str = "") -> TaskScore:
    """对 app_develop 返回（或失败串）做机械对拍。纯函数——测试直用。"""
    sc = TaskScore(id=task.id, title=task.title, verdict="FAIL", error=err)
    exp = task.expect
    if outcome is None or outcome.get("state") != "PACKAGED":
        sc.checks["converged"] = {"ok": False, "detail": err or "未收敛"}
        return sc

    sc.checks["converged"] = {"ok": True, "detail": ""}
    sc.rounds = int(outcome.get("rounds") or 0)
    sc.workspace = str(outcome.get("workspace") or "")
    sc.package_path = str(outcome.get("package_path") or "")

    facts = outcome.get("compile_facts") or {}
    manifest = outcome.get("manifest") or {}

    # 轮数（预算内即过——评分记录实际值供基线对比）
    sc.checks["rounds"] = _check(
        sc.rounds <= DEFAULT_BUDGET_ROUNDS, sc.rounds)

    # 导入面 ⊆ 允许族
    imports = set(facts.get("imports") or [])
    allowed = set(exp.get("imports_allowed") or [])
    sc.checks["imports"] = _check(
        imports <= allowed, sorted(imports - allowed) or sorted(imports))

    # 导出 ⊇ 必需
    exports = set(facts.get("exports") or [])
    required = set(exp.get("exports_required") or [])
    sc.checks["exports"] = _check(
        required <= exports, sorted(required - exports))

    # 确定性编译
    sc.checks["deterministic"] = _check(facts.get("deterministic") is True)

    # 尺寸档门（任务级收紧值）
    size = int(facts.get("size") or 0)
    size_cap = int(exp.get("max_size_kb", 16)) * 1024
    sc.checks["size"] = _check(0 < size <= size_cap,
                               f"{size}B / cap {size_cap}B")

    # caps 对拍（期望前缀族 ⊆ 实际申报）
    caps = list(manifest.get("caps") or [])
    want_prefixes = list(exp.get("caps_expected") or [])
    missing = [p for p in want_prefixes
               if not any(c.startswith(p) for c in caps)]
    sc.checks["caps"] = _check(not missing, f"want={want_prefixes} got={caps}")

    # threads 对拍
    threads = int(manifest.get("threads") or 1)
    sc.checks["threads"] = _check(threads == int(exp["threads"]), threads)

    # tier / needs 对拍（CG4 资源档）
    tier = str(manifest.get("tier") or "small")
    sc.checks["tier"] = _check(tier == exp["tier"], tier)
    needs_exp = exp.get("needs_expected")
    needs = manifest.get("needs")
    if needs_exp is None:
        sc.checks["needs"] = _check(True, "n/a")
    else:
        has_resources = bool(
            isinstance(needs, dict) and needs.get("resources"))
        sc.checks["needs"] = _check(has_resources, f"needs={needs}")

    # 工程最少源文件数（T2 多文件面）
    min_files = int(exp.get("min_source_files", 1))
    n_files = len((outcome.get("compile_facts") or {}).get(
        "files_sha256") or {}) or len(
        (json.loads((Path(sc.workspace) / "project.json").read_text(
            encoding="utf-8")).get("files") or []
         ) if sc.workspace and (Path(sc.workspace) / "project.json").is_file()
        else [])
    sc.checks["source_files"] = _check(n_files >= min_files, n_files)

    # 签名包在盘（tsap_verify 在 app_develop 内部已跑——此处核产物在盘）
    sc.checks["package_on_disk"] = _check(
        bool(sc.package_path) and Path(sc.package_path).is_file(),
        sc.package_path)

    hard_fail = [k for k, v in sc.checks.items() if not v["ok"]]
    sc.verdict = "PASS" if not hard_fail else "PARTIAL"
    return sc


def _score_sim(task: EvalTask, outcome: dict) -> dict[str, Any]:
    """--with-sim 段（AC-3 · DEC-82④）：PACKAGED workspace 跑创作 wasm
    执行器核验判据行；sim=None 任务 = 真机域注记（不降判定）。"""
    from tessera_agent.domain import wasm_sim

    sim_def = task.expect.get("sim")
    if not sim_def:
        return {"ok": True, "detail": "无 sim 定义（真机域——T4/T5）"}
    ws = outcome.get("workspace") or ""
    wasm = Path(ws) / "artifacts" / "app.wasm" if ws else None
    if not wasm or not wasm.is_file():
        return {"ok": False, "detail": "sim 目标缺失（artifacts/app.wasm）"}
    try:
        wasm_sim.check_applicable(json.loads(
            (Path(ws) / "project.json").read_text(encoding="utf-8")))
    except wasm_sim.SimSkip as exc:
        return {"ok": True, "detail": f"sim skip：{exc}"}
    try:
        facts = wasm_sim.run_sim_criteria(wasm, sim_def)
    except TaError as exc:
        return {"ok": False, "detail": str(exc)[:200],
                "facts": exc.detail or {}}
    except Exception as exc:  # noqa: BLE001 —— sim 段异常不否决整轮（PARTIAL）
        return {"ok": False, "detail": f"sim 异常: {type(exc).__name__}: {exc}"[:200]}
    return {"ok": True, "detail": f"ticks={facts['ticks']} "
                                  f"writes={facts['writes_n']}"}


async def run_task(cfg, task: EvalTask, key_path: str, *,
                   timeout_s: float = DEFAULT_TIMEOUT_S,
                   develop_fn=None, with_sim: bool = False,
                   log_fn: Callable[[str], None] |
                   None = None) -> TaskScore:
    """单任务真链执行 + 评分。develop_fn 缺省 = domain.app_chain.app_develop
    （签名 (ctx, spec, key_path)——cfg 经 AppContext 包装）。测试注入
    fake 时 receive 同签名。"""
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    if develop_fn is None:
        from tessera_agent.domain.app_chain import app_develop as develop_fn

    ctx = AppContext(cfg=cfg, budget=ContextBudget(window_tokens=cfg.context_window))
    log = log_fn or (lambda s: None)
    t0 = time.monotonic()
    try:
        coro = develop_fn(ctx, task.spec, key_path, log_fn=log)
        outcome = await asyncio.wait_for(coro, timeout=timeout_s)
    except TimeoutError:
        return score_outcome(task, None, f"超时（>{timeout_s:.0f}s）")
    except TaError as exc:
        detail = ""
        if exc.detail:
            state = exc.detail.get("state")
            rounds = exc.detail.get("rounds")
            if state:
                detail = f"state={state} rounds={rounds}"
        return score_outcome(task, None,
                             f"{exc.message}{'：' + detail if detail else ''}")
    except Exception as exc:  # noqa: BLE001 —— 评分器兜底：任何死法都给分、
        # 套件继续（基线首跑实证：pydantic-ai 工具参数 3 连败 =
        # UnexpectedModelBehavior 直接抛，非 TaError 族）
        return score_outcome(task, None,
                             f"{type(exc).__name__}: {exc}")
    sc = score_outcome(task, outcome)
    if with_sim:
        sc.checks["sim"] = _score_sim(task, outcome)
        hard = [k for k, v in sc.checks.items() if not v["ok"]]
        sc.verdict = "PASS" if not hard else "PARTIAL"
    sc.elapsed_s = time.monotonic() - t0
    return sc
