# SPDX-License-License: Apache-2.0
"""固件域创作验证器（AG3 · LLD-A08 §4 的固件域首实现）。

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


def _from_ta_error(exc: TaError) -> VerifyOutcome:
    detail = exc.message
    extra = exc.detail.get("stderr") or exc.detail.get("detail")
    if extra:
        detail = f"{detail}\n{extra}"
    return VerifyOutcome(ok=False, detail=detail, facts=exc.detail)


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
