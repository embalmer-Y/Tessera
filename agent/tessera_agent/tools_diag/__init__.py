# SPDX-License-Identifier: Apache-2.0
"""部署后诊断工具族（NV-1/NV-2）：判据分类 / 串口抓取 / 修复闭环编排 /
spec 质量门。"""

from tessera_agent.tools_diag.capture import reset_and_capture
from tessera_agent.tools_diag.classify import (
    DIAG_APP_NO_VERDICT,
    DIAG_APP_SILENT,
    DIAG_ENV_BOOT,
    DIAG_INSTALL_FAIL,
    DIAG_NO_VERDICT,
    DIAG_NOT_ACTIVE,
    DIAG_PASS,
    DIAG_WDT_RESET,
    DiagResult,
    classify_run,
)
from tessera_agent.tools_diag.repair import repair_loop
from tessera_agent.tools_diag.simreal_diff import (
    SimRealDiff,
    diff,
    normalize_real,
    normalize_sim,
)
from tessera_agent.tools_diag.spec_gate import SpecGateResult, check_spec

__all__ = [
    "classify_run", "reset_and_capture", "repair_loop", "DiagResult",
    "check_spec", "SpecGateResult",
    "SimRealDiff", "diff", "normalize_sim", "normalize_real",
    "DIAG_PASS", "DIAG_ENV_BOOT", "DIAG_INSTALL_FAIL", "DIAG_NOT_ACTIVE",
    "DIAG_WDT_RESET", "DIAG_APP_SILENT", "DIAG_APP_NO_VERDICT",
    "DIAG_NO_VERDICT",
]
