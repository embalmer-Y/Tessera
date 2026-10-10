# SPDX-License-Identifier: Apache-2.0
"""修复闭环编排（NV-1）：部署 → 抓取判据 → 分类 → 反馈重生成 → 重部署。

「编程链路」最后一环：部署后的真机失败不再依赖人工读串口——分类器
（classify.py）把失败形态翻译成修复方向，注入 app_develop 的
repair_feedback 上下文重生成，闭环直到判据 PASS 或轮次预算耗尽。

分层（可测性）：
- 部署/抓取经注入的 deploy_fn/capture_fn（测试 mock；生产 closure =
  app_chain.app_deploy + capture.reset_and_capture）——编排逻辑本身在
  CI 全量测试（真机面见 tests 的 gated 用例与仓外验证脚本）。
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from tessera_agent.common.errors import TA_E_ARGS, TaError
from tessera_agent.platform import AppContext
from tessera_agent.tools_diag import classify as diag
from tessera_agent.tools_diag import spec_gate

#: 部署动作失败（找不到板/确认不一致）——部署链层，与 APP 代码无关
#: （包结构问题在 tsap_verify 已拦），不消耗 LLM 修复轮次
STATUS_DEPLOY_ERROR = "deploy_error"
#: 环境层失败（介质/网络）——重生成不救济，立即终止
STATUS_ENV_FAIL = "env_fail"
STATUS_PASS = "pass"
STATUS_FAIL = "fail"

#: 进入 LLM 重生成的类别（其余立即终止）
_REPAIRABLE = {
    diag.DIAG_INSTALL_FAIL, diag.DIAG_NOT_ACTIVE, diag.DIAG_WDT_RESET,
    diag.DIAG_APP_SILENT, diag.DIAG_APP_NO_VERDICT, diag.DIAG_NO_VERDICT,
}


async def repair_loop(
    ctx: AppContext,
    *,
    spec: str,
    key_path: str,
    out_dir: str,
    pass_patterns: list[str] | None = None,
    deploy_fn: Callable[[str], Awaitable[dict[str, Any]]],
    capture_fn: Callable[[], str],
    node: str | None = None,
    cube: str | None = None,
    max_rounds: int = 2,
    model: Any = None,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """spec →（生成/部署/抓取/分类，失败带反馈重生成）→ 判据 PASS。

    :param pass_patterns: 判据子串；None = 从 spec【判据】节机读派生
        （NV-2 质量门——spec 即判据单一事实源；派生不出 = 硬错）
    :param max_rounds: 修复轮次预算（默认 2 = 首修 + 兜底；来源 = NV-1
        设计值——历史失败形态单类缺陷一轮可修。越界代价 = LLM 轮次与
        时延；调用方可按需收紧/放宽）
    :param deploy_fn: async (package_path) -> 部署结果 dict（异常 = 部署层失败）
    :param capture_fn: () -> 串口全文（阻塞函数，内部经 to_thread 调度）
    :return: status/rounds_used/history/package_path/last_category
    """
    from tessera_agent.domain import app_chain

    log = log_fn or (lambda s: None)
    if pass_patterns is None:
        gate = spec_gate.check_spec(spec)
        pass_patterns = gate.pass_patterns
        if not pass_patterns:
            msg = ("spec 无可机读判据（【判据】节引号串缺失）且未显式给 "
                   "pass_patterns——修复闭环无判据可依")
            raise TaError(TA_E_ARGS, msg, domain="repair_loop",
                          detail={"errors": gate.errors})
    history: list[dict[str, Any]] = []

    # 首轮生成（app_develop 内部已有产物校验反馈回路——格式/编译错误
    # 在链内闭环，这里的修复轮只处理「部署后运行时」失败）
    dev = await app_chain.app_develop(
        ctx, spec, key_path, out_dir, model=model, log_fn=log)
    package_path = dev["package_path"]

    last_category = ""
    total = 1 + max_rounds
    for rnd in range(1, total + 1):
        try:
            await deploy_fn(package_path)
        except TaError as exc:
            history.append({"round": rnd, "category": STATUS_DEPLOY_ERROR,
                            "summary": str(exc), "action": "abort"})
            log(f"round {rnd}: deploy error → {exc}")
            return {"status": STATUS_DEPLOY_ERROR, "rounds_used": rnd,
                    "history": history, "package_path": package_path,
                    "last_category": STATUS_DEPLOY_ERROR}

        text = await asyncio.to_thread(capture_fn)
        result = diag.classify_run(text, pass_patterns=pass_patterns)
        last_category = result.category
        history.append({
            "round": rnd, "category": result.category,
            "summary": result.summary,
            "evidence_head": result.evidence[:8],
            "action": "pass" if result.category == diag.DIAG_PASS else
                      ("regenerate" if result.category in _REPAIRABLE else "abort"),
        })
        log(f"round {rnd}: {result.category} — {result.summary}")

        if result.category == diag.DIAG_PASS:
            return {"status": STATUS_PASS, "rounds_used": rnd,
                    "history": history, "package_path": package_path,
                    "last_category": result.category}
        if result.category not in _REPAIRABLE:
            # 环境层（env_boot）与部署层——LLM 重生成不救济
            return {"status": STATUS_ENV_FAIL, "rounds_used": rnd,
                    "history": history, "package_path": package_path,
                    "last_category": result.category}
        if rnd == total:
            break

        feedback = (f"失败类别：{result.category}\n修复方向：{result.repair_hint}\n"
                    f"串口证据行（截选）：\n"
                    + "\n".join(result.evidence[:12]))
        dev = await app_chain.app_develop(
            ctx, spec, key_path, out_dir, repair_feedback=feedback,
            model=model, log_fn=log)
        package_path = dev["package_path"]

    return {"status": STATUS_FAIL, "rounds_used": total, "history": history,
            "package_path": package_path, "last_category": last_category}
