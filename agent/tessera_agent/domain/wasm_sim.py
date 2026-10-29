# SPDX-License-Identifier: Apache-2.0
"""domain/wasm_sim — 创作 wasm 的 PC 侧执行器（AC-3 · DEC-82①）。

SimFn 预留缝的实现（FirmwareCreationVerifier(sim_runner)——AG6 时代错误
信息明言「sim 接线随 AG6」）：wasmtime 装载 artifacts/app.wasm，natives
stub 面供给 import（按 module.imports 反射生成——签名变化自适应），tick
循环驱动 app_init/app_tick/health_ping（FIX-2 教训域：带 ctx 调用），
采集 ts_log_write 判据行 + gpio/pwm 写序列，判据规则机械核验。

sim 适用门（诚实面，DEC-82①）：threads>1 / needs.resources 非空 = skip
（线程档与资源外置属真机/部署管线域——不跑假 sim，facts.sim_skipped 注记）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tessera_agent.common.errors import TA_E_SIM, TaError
from tessera_agent.domain.criteria import judge_lines

TICK_PERIOD_MS = 10
DEFAULT_TICKS = 600


class SimSkip(Exception):
    """sim 不适用（threads/resources 档）——调用方转 skip 注记，非失败。"""


def check_applicable(project: dict[str, Any]) -> None:
    """manifest 适用门：不适用 = SimSkip（诚实 skip 面）。"""
    manifest = project.get("manifest") or {}
    threads = int(manifest.get("threads") or 1)
    needs = manifest.get("needs") or {}
    if threads > 1:
        raise SimSkip(f"threads={threads}（线程档真机域——sim 不支持）")
    if isinstance(needs, dict) and needs.get("resources"):
        raise SimSkip("needs.resources 非空（资源外置部署管线域——sim 不支持）")


class WasmSim:
    """单次装载执行。用法：sim = WasmSim(wasm_path); result = sim.run(ticks)。"""

    def __init__(self, wasm_path: str | Path) -> None:
        import wasmtime

        self._wasmtime = wasmtime
        self.engine = wasmtime.Engine()
        self.module = wasmtime.Module.from_file(self.engine, str(wasm_path))
        self.store = wasmtime.Store(self.engine)
        self.log_lines: list[str] = []
        self.writes: list[dict[str, Any]] = []
        self._now_ms = 0
        self._gpio_state: dict[int, int] = {}
        self._memory: Any = None
        stubs = self._build_stubs()
        self.instance = wasmtime.Instance(
            self.store, self.module, stubs)

    # ---- natives stub 面 -------------------------------------------------

    def _read_cstr(self, ptr: int, length: int) -> str:
        mem = self._memory
        raw = bytes(mem.read(self.store, ptr, ptr + max(0, length)))
        return raw.decode("utf-8", errors="replace")

    def _write_i32(self, ptr: int, value: int) -> None:
        self._memory.write(self.store, value.to_bytes(4, "little"), ptr)

    def _build_stubs(self) -> list[Any]:
        """按 module.imports 顺序反射生成 stub——签名形状自适应。"""
        wasmtime = self._wasmtime
        funcs: list[Any] = []
        for imp in self.module.imports:
            if not hasattr(imp.type, "params"):
                funcs.append(0)  # 全局/内存 import 不在 v1 面
                continue
            params = list(imp.type.params)
            results = list(imp.type.results)
            fn = self._stub_for(imp.name, params, results)
            ftype = wasmtime.FuncType(params, results)
            funcs.append(wasmtime.Func(self.store, ftype, fn))
        return funcs

    def _stub_for(self, name: str, params: list, results: list):
        """名字分派语义 stub；未实现族 = 负错误码（形状自适应）。"""
        i32 = lambda *_a: -1  # noqa: E731

        def i64_ret(*_a: int) -> int:
            return 0

        def ts_log_write(ctx: int, lvl: int, ptr: int, length: int) -> int:
            self.log_lines.append(self._read_cstr(ptr, length))
            return 0

        def ts_time_ms() -> int:
            return self._now_ms

        def ts_gpio_write(_ctx: int, inst: int, v: int) -> int:
            self._gpio_state[inst] = 1 if v else 0
            self.writes.append({"ch": f"gpio:{inst}", "value_u": 1 if v else 0,
                                "t_ms": self._now_ms})
            return 0

        def ts_gpio_read(_ctx: int, inst: int, out_ptr: int) -> int:
            self._write_i32(out_ptr, self._gpio_state.get(inst, 0))
            return 0

        def ts_pwm_set(_ctx: int, inst: int, _hz: int, permille: int) -> int:
            self.writes.append({"ch": f"pwm:{inst}", "value_u": permille,
                                "t_ms": self._now_ms})
            return 0

        def ts_adc_read(_ctx: int, _inst: int, out_ptr: int) -> int:
            self._write_i32(out_ptr, 0)
            return 0

        semantic = {
            "ts_log_write": (ts_log_write, "i32"),
            "ts_time_ms": (ts_time_ms, "i64"),
            "ts_gpio_write": (ts_gpio_write, "i32"),
            "ts_gpio_read": (ts_gpio_read, "i32"),
            "ts_pwm_set": (ts_pwm_set, "i32"),
            "ts_adc_read": (ts_adc_read, "i32"),
        }
        if name in semantic:
            return semantic[name][0]
        # 未实现族：i64 结果 = 0，i32 结果 = -1（负错误码），无结果 = no-op
        if not results:
            return (lambda *a: None)
        return i64_ret if str(results[0]) == "i64" else i32

    # ---- 执行与判定 -------------------------------------------------------

    def _call(self, exports: Any, store: Any, name: str) -> None:
        """按 wasm 实际签名调用回调（FIX-2 教训反向：宿主 argc 须匹配
        param cells——模型产物 app_tick 可能无参〔eval T1 实证〕）。"""
        fn = exports[name]
        n = len(list(fn.type(self.store).params))
        args = [0] * n
        fn(store, *args)

    def run(self, ticks: int = DEFAULT_TICKS,
            tick_period_ms: int = TICK_PERIOD_MS) -> None:
        exports = self.instance.exports(self.store)
        try:
            self._memory = exports["memory"]
        except KeyError as exc:
            raise TaError(TA_E_SIM, "wasm 无 memory export（非 clang 产物？）",
                          domain="sim") from exc
        self._call(exports, self.store, "app_init")
        for i in range(ticks):
            self._now_ms = i * tick_period_ms
            self._call(exports, self.store, "app_tick")
        names = [e.name for e in self.module.exports]
        if "health_ping" in names:
            self._call(exports, self.store, "health_ping")


def run_sim_criteria(wasm_path: str | Path,
                     scenario: dict[str, Any]) -> dict[str, Any]:
    """SimFn 语义：装载 + tick 循环 + 判据核验。scenario 键：
    ticks（缺省 600）/ verdict_patterns（必填非空——无判据 = 拒绝假通过）/
    monotonic（可选 pattern）。返回 facts dict；判据不过 = TaError(TA_E_SIM)。
    """
    patterns = list(scenario.get("verdict_patterns") or [])
    if not patterns:
        raise TaError(TA_E_SIM, "sim scenario 缺 verdict_patterns（拒绝假通过）",
                      domain="sim")
    sim = WasmSim(wasm_path)
    try:
        sim.run(ticks=int(scenario.get("ticks", DEFAULT_TICKS)))
    except TaError:
        raise
    except Exception as exc:  # noqa: BLE001 —— 执行器面异常（签名不匹配/
        # trap 等）TaError 化（判据失败与执行失败同通道，evidence 回喂）
        raise TaError(TA_E_SIM, f"sim 执行失败: {type(exc).__name__}: {exc}",
                      domain="sim") from exc
    rules: list[dict[str, Any]] = [
        {"type": "present", "pattern": p, "min_count": 1} for p in patterns]
    mono = scenario.get("monotonic")
    if mono:
        rules.append({"type": "monotonic", "pattern": mono})
    rep = judge_lines(sim.log_lines, rules)
    if not rep.overall_ok:
        tail = "\n".join(sim.log_lines[-8:])
        raise TaError(TA_E_SIM, "sim 判据未全过",
                      domain="sim",
                      detail={"rules": rep.rules, "log_tail": tail,
                              "writes_n": len(sim.writes)})
    return {"verdict_lines": sim.log_lines[-16:], "writes_n": len(sim.writes),
            "ticks": int(scenario.get("ticks", DEFAULT_TICKS)),
            "rules": rep.rules}
