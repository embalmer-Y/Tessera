# SPDX-License-License: Apache-2.0
"""固件域创作验证器（AG3 · LLD-agent-creation-workspace §4 的固件域首实现）。

装配关系：平台层 creation/ 零 import 本模块（导入图测试守卫）；
组合根（AG6 接线）构造 FirmwareCreationVerifier 注入 CreationLoop。
sim 面：sim_runner 注入点——生产接线随 AG6（sim APP 装载面消费）；
未注入而调用 = TA_E_NOT_CONFIGURED（诚实拒绝，不假日通过）。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tessera_agent.common.errors import (
    TA_E_NOT_CONFIGURED,
    TA_E_TSAP,
    TaError,
)
from tessera_agent.creation.verifier import (
    PackageOutcome,
    VerifyOutcome,
    artifacts_wasm,
    workspace_roots,
)
from tessera_agent.creation.workspace import Workspace
from tessera_agent.tools_tsap.tools import tsap_package
from tessera_agent.tools_tsap.wasm_build import (
    DEFAULT_MAX_BYTES,
    NATIVE_WHITELIST,
    compile_project_c,
    wasm_func_surface,
)

SimFn = Callable[[Workspace, dict[str, Any]], VerifyOutcome]

# HW-4 ③'（LLD-agent-hardware-targeting §7.3a · owner 2026-10-21 扩令）：源码导入 ⇔ manifest caps
# 声明一致性——LED 缺陷第一层（app 调 ts_gpio_write 但 manifest 只申报
# log → 权限层运行期拒，168 对 WRITE REJECTED）的机械补位：包装前 face
# 检查即拦，修复轮拿到结构化证据而非猜测。豁免（如实注记）：
# - ts_log_write：TEST 语义自动授予 log:write:0（appmgr/runtime.c IR-16
#   延续性）——生产语义批收紧时本豁免同步撤；
# - ts_net_publish/ts_time_ms：net 域与时间源不属 caps 数值面。
_NATIVE_CAP_MAP = {
    "ts_gpio_write": "gpio:", "ts_gpio_read": "gpio:",
    "ts_pwm_set": "pwm:", "ts_adc_read": "adc:",
    "ts_av_capture": "av:",
    "ts_fs_read": "fs:", "ts_fs_write": "fs:",
    "ts_fs_list": "fs:", "ts_fs_delete": "fs:",
    "ts_kv_save": "kv:", "ts_kv_load": "kv:",
    "ts_msg_send": "msg:", "ts_msg_recv": "msg:",
    "ts_power_set": "power:", "ts_power_get": "power:",
}


def caps_natives_violations(imports: set[str], caps: list[str]) -> list[str]:
    """导入面 ⇔ caps 声明一致性核对（零 LLM 机械面）。返回违规描述列表。"""
    out: list[str] = []
    for imp in sorted(imports):
        need = _NATIVE_CAP_MAP.get(imp)
        if need and not any(c.startswith(need) for c in caps):
            out.append(f"{imp} 需要 caps 声明 {need}*（当前 caps={caps}）")
    return out


def _from_ta_error(exc: TaError) -> VerifyOutcome:
    detail = exc.message
    extra = exc.detail.get("stderr") or exc.detail.get("detail")
    if extra:
        detail = f"{detail}\n{extra}"
    return VerifyOutcome(ok=False, detail=detail, facts=exc.detail)


def creation_sim_runner(ws, scenario: dict) -> VerifyOutcome:
    """SimFn 桥（DEC-82②）：适用门 → WasmSim 执行 → 判据核验。
    skip = ok+facts.sim_skipped 注记（不跑假 sim）；判据不过 = ok=False
    （evidence 回喂创作循环）。"""
    from tessera_agent.domain import wasm_sim

    try:
        wasm_sim.check_applicable(ws.load_project())
    except wasm_sim.SimSkip as exc:
        return VerifyOutcome(ok=True, detail=f"sim skip：{exc}",
                             facts={"sim_skipped": str(exc)})
    wasm = artifacts_wasm(ws)
    if not wasm.is_file():
        return VerifyOutcome(ok=False, detail="sim 目标缺失（artifacts/app.wasm）",
                             facts={})
    try:
        facts = wasm_sim.run_sim_criteria(wasm, scenario)
    except TaError as exc:
        return VerifyOutcome(ok=False, detail=str(exc), facts=exc.detail or {})
    return VerifyOutcome(ok=True, detail="sim 判据全过", facts=facts)


class FirmwareCreationVerifier:
    """工程清单驱动：compile（多文件聚合）→ face_check（产物复检）→ package（签名）。"""

    def __init__(self, sim_runner: SimFn | None = None) -> None:
        self._sim = sim_runner

    # ---- 工程文件集 ------------------------------------------------------

    @staticmethod
    def _project_files(ws: Workspace) -> dict[str, str]:
        project = ws.load_project()
        files: dict[str, str] = {}
        for name in project.get("files", []):
            p = ws.project_dir / name
            files[name] = p.read_text(encoding="utf-8")
        return files

    # ---- 验证链 ------------------------------------------------------------

    def compile(self, ws: Workspace) -> VerifyOutcome:
        try:
            project = ws.load_project()
            result = compile_project_c(
                self._project_files(ws),
                out_dir=str(ws.artifacts_dir),
                allowed_roots=workspace_roots(ws),
                exports=list(project.get("exports", [])),
                threads=int(project.get("threads", 1)),
                tier=str(project.get("tier") or "small"),
                needs=project.get("needs"),
            )
            return VerifyOutcome(ok=True, detail="编译通过（双编译一致）",
                                 facts=result)
        except TaError as exc:
            return _from_ta_error(exc)
        except OSError as exc:
            return VerifyOutcome(ok=False, detail=f"工程文件读取失败: {exc}")

    def face_check(self, ws: Workspace) -> VerifyOutcome:
        wasm = artifacts_wasm(ws)
        if not wasm.is_file():
            return VerifyOutcome(ok=False, detail="产物缺失（先 compile）")
        try:
            imports, exports = wasm_func_surface(wasm)
        except TaError as exc:
            return _from_ta_error(exc)
        bad = sorted(imports - NATIVE_WHITELIST)
        if bad:
            return VerifyOutcome(
                ok=False,
                detail=f"导入面越权（natives 白名单外）: {bad}",
                facts={"imports": sorted(imports)},
            )
        # HW-4 ③'：声明-调用一致性（调了 native 未申报 cap = 运行期权限
        # 拒——包装前拦截，LED 缺陷第一层的机械补位）
        caps = list(((ws.load_project().get("manifest") or {})
                     .get("caps")) or [])
        viol = caps_natives_violations(imports, caps)
        if viol:
            return VerifyOutcome(
                ok=False,
                detail="声明-调用不一致（caps 缺申报）:\n- " + "\n- ".join(viol),
                facts={"imports": sorted(imports), "caps": caps},
            )
        size = wasm.stat().st_size
        if size > DEFAULT_MAX_BYTES:
            return VerifyOutcome(
                ok=False,
                detail=f"wasm 尺寸 {size}B 超档位门 {DEFAULT_MAX_BYTES}B",
                facts={"size": size},
            )
        need = {"health_ping"}
        missing = sorted(need - exports)
        if missing:
            return VerifyOutcome(
                ok=False, detail=f"缺少必需导出: {missing}",
                facts={"exports": sorted(exports)},
            )
        return VerifyOutcome(
            ok=True, detail="面检查通过",
            facts={"size": size, "imports": sorted(imports),
                   "exports": sorted(exports)},
        )

    def simulate(self, ws: Workspace, scenario: dict[str, Any]) -> VerifyOutcome:
        if self._sim is None:
            raise TaError(
                TA_E_NOT_CONFIGURED,
                "sim 接线随 AG6（app_develop 升级/sim APP 装载面消费）——"
                "本验证器未注入 sim_runner，拒绝假日通过",
                domain="creation",
            )
        return self._sim(ws, scenario)

    def package(self, ws: Workspace, key_path: str) -> PackageOutcome:
        wasm = artifacts_wasm(ws)
        if not wasm.is_file():
            return PackageOutcome(ok=False, detail="产物缺失（先 compile）")
        try:
            project = ws.load_project()
            manifest = dict(project.get("manifest", {}))
            manifest.setdefault("app_id", project.get("app_id", ""))
            manifest.setdefault("app_ver", project.get("app_ver", "1.0.0"))
            manifest.setdefault("exports", list(project.get("exports", [])))
            result = tsap_package(
                str(wasm), manifest, key_path,
                out_dir=str(ws.artifacts_dir),
                allowed_roots=workspace_roots(ws),
            )
            return PackageOutcome(
                ok=True, detail="打包签名完成", facts=result,
                package_path=result["package_path"],
            )
        except TaError as exc:
            return PackageOutcome(ok=False, detail=str(exc), facts=exc.detail)
        except (OSError, ValueError) as exc:
            raise TaError(
                TA_E_TSAP, f"打包链异常: {exc}", domain="creation",
            ) from exc
