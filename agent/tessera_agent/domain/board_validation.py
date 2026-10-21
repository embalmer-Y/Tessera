# SPDX-License-Identifier: Apache-2.0
"""板卡验证域（LLD-A12 · DEC-68①；V0.13.0 BV1-I）。

确定性检查流水线：输入板卡画像 + 传输面（串口/zenoh/部署链），输出
结构化 bring-up 报告。板卡验证非 LLM 创作任务——不硬套 CreationLoop；
继承 DEC-33 原则面（结构化证据不截断不美化 / 事件审计同源 /
CheckResult 对齐 VerifyOutcome 同型）。

检查项目录 v1（C0 构建前级随 V0.14.0 P4 判定批接入——画像声明
build.enabled=true 拒装载，fail-closed 不留桩）：C1 串口在场 →
C2 flash 身份 → C3 boot/console → C4 zenoh 连通 → C5 caps 消费 →
C6 部署 E2E 冒烟。SKIP 双型：派生（前置未过——periph 破案纪律：
物理失联 ≠ 验证失败）vs 声明（画像节缺失）。overall 判定：任一
FAIL = FAIL；零 FAIL 有 SKIP = DEGRADED；全 PASS = PASS。

串口独占纪律（三读抢数教训）：C2（esptool）与 C3（抓取）分相串行，
验证全程不与他方并发持口。本模块为同步实现——事件循环调用方经
asyncio.to_thread（MCP 层既定规约）。
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from tessera_agent.domain import app_chain
from tessera_agent.tools_net import deploy as net_deploy
from tessera_agent.tools_net.zenoh_service import ZenohService

CHECK_ORDER: tuple[str, ...] = ("C1", "C2", "C3", "C4", "C5", "C6")
CHECK_TITLES = {
    "C1": "串口在场",
    "C2": "flash 身份",
    "C3": "boot/console",
    "C4": "zenoh 连通",
    "C5": "caps 消费",
    "C6": "部署 E2E 冒烟",
}
# 画像未声明的可选节 = 声明 SKIP（该检查不适用本板——≠ 失败）
_OPT_IN_SECTIONS = ("caps", "smoke")

_EVIDENCE_TAIL = 300  # boot 全文过长者取尾段（总量入 facts——不静默）
_FAIL_EVIDENCE_RENDER = 10


class ProfileError(ValueError):
    """画像装载失败（缺文件/TOML 非法/未知字段 fail-closed/必填缺失）。"""


# ---- 板卡画像 schema v1（agent/boards/<board_id>.toml）----------------------

_ALLOWED: dict[str, set[str]] = {
    "board": {"id", "description"},
    "serial": {"port", "baud"},
    "flash": {"adapter", "chip", "size_kb"},
    "boot": {"reset", "ready_patterns", "timeout_s"},
    "zenoh": {"expect_discover", "cube"},
    "caps": {"tiers", "min_slot_pool_kb"},
    "smoke": {"package_path", "pub_path", "criteria", "window_s"},
    "build": {"enabled", "app_target"},
    # HW-4（LLD-A16 §7.1 · v1.1 加性）：引脚级硬件事实（选入节）
    "hardware": {"zephyr_board", "soc", "ram_kb", "psram_kb", "notes", "pin"},
}
_REQUIRED_SECTIONS = ("board", "serial", "flash", "boot", "zenoh")

#: HW-4 物理通道域（与 caps class 同空间；逻辑域 power/fs/log/kv/msg/sys 不核对）
HW_PHYSICAL_DOMAINS = ("gpio", "pwm", "adc", "av")


@dataclass(frozen=True)
class SerialSpec:
    port: str
    baud: int = 115200


@dataclass(frozen=True)
class FlashSpec:
    adapter: str = "esptool"
    chip: str = ""
    size_kb: int = 0


@dataclass(frozen=True)
class BootSpec:
    reset: bool = True
    ready_patterns: tuple[str, ...] = ()
    timeout_s: float = 90.0


@dataclass(frozen=True)
class ZenohSpec:
    expect_discover: bool = True
    cube: str = ""  # 期望 cube_id（固件自报）；空 = 恰一在线即本板


@dataclass(frozen=True)
class CapsSpec:
    tiers: tuple[str, ...] = ()
    min_slot_pool_kb: int = 0


@dataclass(frozen=True)
class SmokeSpec:
    package_path: str
    pub_path: str
    criteria: tuple[str, ...]
    window_s: float = 90.0


@dataclass(frozen=True)
class BuildSpec:
    enabled: bool = False
    app_target: str = ""


@dataclass(frozen=True)
class HardwarePin:
    """引脚级硬件事实（HW-4 · LLD-A16 §7.1）——source 必填（R12「每字段
    机械可校验来源」延伸：无来源的引脚声明拒装载）。"""

    name: str
    domain: str
    instance: int
    source: str
    desc: str = ""


@dataclass(frozen=True)
class HardwareSpec:
    zephyr_board: str = ""
    soc: str = ""
    ram_kb: int = 0
    psram_kb: int = 0
    notes: str = ""
    pins: tuple[HardwarePin, ...] = ()

    def bound(self, domain: str, instance: int) -> HardwarePin | None:
        """通道域×实例是否有物理绑定（门与判据感知的唯一真相源）。"""
        for p in self.pins:
            if p.domain == domain and p.instance == instance:
                return p
        return None

    def domain_pins(self, domain: str) -> tuple[HardwarePin, ...]:
        return tuple(p for p in self.pins if p.domain == domain)


@dataclass(frozen=True)
class BoardProfile:
    """板卡期望的声明式清单（验证域可移植单元；R12 能力目录种子）。"""

    id: str
    description: str
    serial: SerialSpec
    flash: FlashSpec
    boot: BootSpec
    zenoh: ZenohSpec
    caps: CapsSpec | None = None
    smoke: SmokeSpec | None = None
    build: BuildSpec = field(default_factory=BuildSpec)
    hardware: HardwareSpec | None = None  # 选入节；None = 画像无事实（HW-4 面跳过）
    path: str = ""


def load_profile(path: str | Path) -> BoardProfile:
    """装载画像；未知节/未知键一律拒绝（防拼写静默失效——fail-closed）。"""
    p = Path(path)
    if not p.is_file():
        raise ProfileError(f"画像文件不存在: {p}")
    try:
        raw = tomllib.loads(p.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ProfileError(f"TOML 解析失败: {exc}") from exc
    for section in raw:
        if section not in _ALLOWED:
            raise ProfileError(f"未知画像节 [{section}]（fail-closed）")
    for section, required in _REQUIRED_SECTIONS_MAP().items():
        if section not in raw:
            raise ProfileError(f"缺必需节 [{section}]")
        for key in required:
            if key not in raw[section]:
                raise ProfileError(f"[{section}] 缺必需键 {key}")
        unknown = set(raw[section]) - _ALLOWED[section]
        if unknown:
            raise ProfileError(f"[{section}] 未知键 {sorted(unknown)}（fail-closed）")
    board_id = str(raw["board"]["id"])
    if not board_id:
        raise ProfileError("[board] id 不能为空")
    flash = FlashSpec(
        adapter=str(raw["flash"].get("adapter", "esptool")),
        chip=str(raw["flash"]["chip"]),
        size_kb=int(raw["flash"]["size_kb"]),
    )
    if not flash.chip or flash.size_kb <= 0:
        raise ProfileError("[flash] chip/size_kb 须为非空期望值")
    boot = BootSpec(
        reset=bool(raw["boot"].get("reset", True)),
        ready_patterns=tuple(str(x) for x in raw["boot"]["ready_patterns"]),
        timeout_s=float(raw["boot"].get("timeout_s", 90.0)),
    )
    if not boot.ready_patterns:
        raise ProfileError("[boot] ready_patterns 不能为空")
    build = BuildSpec(
        enabled=bool(raw.get("build", {}).get("enabled", False)),
        app_target=str(raw.get("build", {}).get("app_target", "")),
    )
    if build.enabled:
        raise ProfileError("[build] enabled=true 未接入（C0 前级随 V0.14.0 "
                           "P4 判定批；当前拒装载不留桩）")
    caps_raw = raw.get("caps")
    smoke_raw = raw.get("smoke")
    hw_raw = raw.get("hardware")
    hardware = None
    if hw_raw is not None:
        pins: list[HardwarePin] = []
        for i, pin in enumerate(hw_raw.get("pin", [])):
            unknown = set(pin) - {"name", "domain", "instance", "desc", "source"}
            if unknown:
                raise ProfileError(
                    f"[hardware.pin[{i}]] 未知键 {sorted(unknown)}（fail-closed）")
            for key in ("name", "domain", "instance", "source"):
                if key not in pin:
                    raise ProfileError(f"[hardware.pin[{i}]] 缺必需键 {key}")
            if str(pin["domain"]) not in HW_PHYSICAL_DOMAINS:
                raise ProfileError(
                    f"[hardware.pin[{i}]] domain 须为物理域 "
                    f"{HW_PHYSICAL_DOMAINS}，当前 {pin['domain']!r}")
            if not str(pin["source"]).strip():
                raise ProfileError(
                    f"[hardware.pin[{i}]] source 必填（R12 来源纪律——无来源"
                    "的引脚声明拒装载）")
            pins.append(HardwarePin(
                name=str(pin["name"]), domain=str(pin["domain"]),
                instance=int(pin["instance"]), source=str(pin["source"]),
                desc=str(pin.get("desc", ""))))
        hardware = HardwareSpec(
            zephyr_board=str(hw_raw.get("zephyr_board", "")),
            soc=str(hw_raw.get("soc", "")),
            ram_kb=int(hw_raw.get("ram_kb", 0)),
            psram_kb=int(hw_raw.get("psram_kb", 0)),
            notes=str(hw_raw.get("notes", "")),
            pins=tuple(pins),
        )
    return BoardProfile(
        id=board_id,
        description=str(raw["board"].get("description", "")),
        serial=SerialSpec(port=str(raw["serial"]["port"]),
                          baud=int(raw["serial"].get("baud", 115200))),
        flash=flash,
        boot=boot,
        zenoh=ZenohSpec(
            expect_discover=bool(raw["zenoh"].get("expect_discover", True)),
            cube=str(raw["zenoh"].get("cube", "")),
        ),
        caps=None if caps_raw is None else CapsSpec(
            tiers=tuple(str(x) for x in caps_raw.get("tiers", ())),
            min_slot_pool_kb=int(caps_raw.get("min_slot_pool_kb", 0)),
        ),
        smoke=None if smoke_raw is None else SmokeSpec(
            package_path=str(smoke_raw["package_path"]),
            pub_path=str(smoke_raw["pub_path"]),
            criteria=tuple(str(x) for x in smoke_raw["criteria"]),
            window_s=float(smoke_raw.get("window_s", 90.0)),
        ),
        build=build,
        hardware=hardware,
        path=str(p),
    )


def _REQUIRED_SECTIONS_MAP() -> dict[str, tuple[str, ...]]:
    return {
        "board": ("id",),
        "serial": ("port",),
        "flash": ("chip", "size_kb"),
        "boot": ("ready_patterns",),
        "zenoh": (),
    }


def list_profiles(boards_dir: str | Path) -> list[str]:
    """枚举画像目录下的画像 id（*.toml 文件名 stem，排序稳定）。"""
    d = Path(boards_dir)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.toml"))


# ---- 结果形态（CheckResult 对齐 VerifyOutcome 同型——LLD-A12 §1）-------------

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


@dataclass
class CheckResult:
    check: str
    verdict: str  # "PASS" | "FAIL" | "SKIP"
    detail: str = ""
    evidence: list[str] = field(default_factory=list)  # 原文行（不截断不美化）
    facts: dict[str, Any] = field(default_factory=dict)
    dur_ms: int = 0
    derived_skip: bool = False  # True = 派生 SKIP（前置未过）vs 声明 SKIP（节缺失）

    def to_json(self) -> dict[str, Any]:
        return {"check": self.check, "verdict": self.verdict,
                "detail": self.detail, "evidence": self.evidence,
                "facts": self.facts, "dur_ms": self.dur_ms,
                "derived_skip": self.derived_skip}


@dataclass
class BoardReport:
    board_id: str
    description: str
    started_at: float
    dur_s: float
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def overall(self) -> str:
        verdicts = [c.verdict for c in self.checks]
        if FAIL in verdicts:
            return FAIL
        if SKIP in verdicts:
            return "DEGRADED"
        return PASS

    def to_json(self) -> dict[str, Any]:
        return {"board_id": self.board_id, "description": self.description,
                "started_at": self.started_at, "dur_s": self.dur_s,
                "overall": self.overall,
                "checks": [c.to_json() for c in self.checks]}

    def render(self) -> str:
        """人读形态（Renderer 契约：判据/证据行逐字——仅样式级组织）。"""
        lines = [f"Board {self.board_id}"
                 + (f" [{self.description}]" if self.description else "")
                 + f": {self.overall} ({self.dur_s:.1f}s)"]
        for c in self.checks:
            title = CHECK_TITLES.get(c.check, c.check)
            row = f"  [{c.check}] {c.verdict} {title} ({c.dur_ms}ms)"
            if c.detail:
                row += f" — {c.detail}"
            lines.append(row)
            if c.verdict == FAIL:
                for ev in c.evidence[:_FAIL_EVIDENCE_RENDER]:
                    lines.append(f"        | {ev}")
                if len(c.evidence) > _FAIL_EVIDENCE_RENDER:
                    lines.append(f"        | …共 {len(c.evidence)} 行（全量见 JSON）")
        return "\n".join(lines)


# ---- 传输面协议（检查项唯一 I/O 缝——FakeBoard 注入即全矩阵 sim 级）-----------

@runtime_checkable
class BoardTransport(Protocol):
    """板卡传输面：真机实现 = LiveTransport；测试 = FakeTransport。"""

    def port_ready(self, port: str) -> tuple[bool, str]: ...

    def flash_identity(self, port: str, chip: str) \
            -> tuple[bool, dict[str, Any], list[str]]: ...

    def boot_capture(self, port: str, baud: int, seconds: float,
                     reset: bool) -> tuple[bool, list[str]]: ...

    def discover(self, timeout_s: float) \
            -> tuple[bool, list[dict[str, Any]]]: ...

    def node_snapshot(self, node: str, cube: str) \
            -> tuple[bool, dict[str, Any]]: ...

    def deploy_smoke(self, node: str, cube: str, package_path: str,
                     pub_path: str, criteria: list[str], serial_port: str,
                     window_s: float) -> tuple[bool, dict[str, Any]]: ...


def _find_esptool(cfg: Any) -> str | None:
    """esptool ≥5 二进制名纪律（flash_prov 同款）：venv bin 优先，PATH 兜底。"""
    venv_bin = Path(cfg.west_venv_python).parent
    for cand in (venv_bin / "esptool", venv_bin / "esptool.py"):
        if cand.is_file():
            return str(cand)
    for name in ("esptool", "esptool.py"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _resolve_repo_path(cfg: Any, path: str) -> Path:
    """画像内仓相对路径 → 绝对（基准 = workspace_repo——与 CWD 无关）。"""
    p = Path(path)
    if p.is_absolute():
        return p
    return Path(getattr(cfg, "workspace_repo", ".")) / p


class LiveTransport:
    """真机传输面：串口（pyserial/esptool/capture）+ zenoh（tools_net）+ 部署链。

    全方法同步阻塞——调用方经 asyncio.to_thread。deploy_smoke 需 ctx
    （app_deploy 复验/发现链）；未注入 = 该检查结构化失败（不静默）。
    """

    def __init__(self, cfg: Any, ctx: Any = None,
                 log_fn: Any = None) -> None:
        self._cfg = cfg
        self._locator = cfg.router_locator
        self._ctx = ctx
        self._log = log_fn or (lambda s: None)

    def port_ready(self, port: str) -> tuple[bool, str]:
        if not port:
            return False, "画像未配置串口路径（serial.port 为空——板未接线？）"
        if not os.path.exists(port):
            return False, f"串口不存在: {port}"
        try:
            import serial  # 懒导入：CI 无串口环境不触发

            with serial.Serial(port, 115200, timeout=0.2):
                pass
            return True, "port open ok"
        except Exception as exc:  # noqa: BLE001 —— 持有器占用等如实归因
            return False, (f"串口打开失败（持有器占用？——单读者纪律）: "
                           f"{type(exc).__name__}: {exc}")

    def flash_identity(self, port: str, chip: str) \
            -> tuple[bool, dict[str, Any], list[str]]:
        exe = _find_esptool(self._cfg)
        if exe is None:
            return False, {}, ["esptool 未找到（zephyr venv bin 与 PATH 均无）"]
        try:
            proc = subprocess.run(  # noqa: S603 —— 固定参数构造
                [exe, "--chip", chip, "-p", port, "flash-id"],
                capture_output=True, text=True, timeout=60,
            )
        except Exception as exc:  # noqa: BLE001
            return False, {}, [f"{type(exc).__name__}: {exc}"]
        text = (proc.stdout or "") + (proc.stderr or "")
        lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
        facts: dict[str, Any] = {}
        # esptool 5.x 双形态：`Chip is ESP32-S3`（老）/ `Chip type:  ESP32-S3 (QFN56)`
        m_chip = (re.search(r"Chip is ([A-Za-z0-9-]+)", text)
                  or re.search(r"Chip type:\s*([A-Za-z0-9-]+)", text))
        m_size = re.search(r"Detected flash size: (\d+)(KB|MB)", text)
        if m_chip:
            facts["chip"] = m_chip.group(1)
        if m_size:
            facts["size_kb"] = (int(m_size.group(1))
                                * (1024 if m_size.group(2) == "MB" else 1))
        ok = proc.returncode == 0 and "chip" in facts and "size_kb" in facts
        return ok, facts, lines[-80:]

    def boot_capture(self, port: str, baud: int, seconds: float,
                     reset: bool) -> tuple[bool, list[str]]:
        from tessera_agent.tools_diag import capture as diag_capture

        try:
            if reset:
                text = diag_capture.reset_and_capture(port, seconds, baud=baud)
            else:
                text = diag_capture.capture_window(port, seconds, baud=baud)
        except Exception as exc:  # noqa: BLE001
            return False, [f"{type(exc).__name__}: {exc}"]
        lines = text.splitlines()
        return True, (lines if len(lines) <= _EVIDENCE_TAIL
                      else lines[-_EVIDENCE_TAIL:])

    def discover(self, timeout_s: float) \
            -> tuple[bool, list[dict[str, Any]]]:
        try:
            with ZenohService(self._locator) as svc:
                return True, net_deploy.discover(svc, timeout_s=timeout_s)
        except Exception as exc:  # noqa: BLE001
            return False, [{"error": f"{type(exc).__name__}: {exc}"}]

    def node_snapshot(self, node: str, cube: str) \
            -> tuple[bool, dict[str, Any]]:
        try:
            with ZenohService(self._locator) as svc:
                return True, net_deploy.status(svc, node, cube)
        except Exception as exc:  # noqa: BLE001
            return False, {"error": f"{type(exc).__name__}: {exc}"}

    def deploy_smoke(self, node: str, cube: str, package_path: str,
                     pub_path: str, criteria: list[str], serial_port: str,
                     window_s: float) -> tuple[bool, dict[str, Any]]:
        if self._ctx is None:
            return False, {"deploy_error": "ctx 未注入（MCP 面专供——CLI 亦须装配）"}
        pkg = _resolve_repo_path(self._cfg, package_path)
        pub = _resolve_repo_path(self._cfg, pub_path)
        out: dict[str, Any] = {}
        try:
            d = asyncio.run(app_chain.app_deploy(
                self._ctx, str(pkg), str(pub), node, cube,
                log_fn=self._log))
            out["deploy"] = {k: d.get(k) for k in
                             ("node", "cube", "app_id", "slot")}
        except Exception as exc:  # noqa: BLE001
            return False, {"deploy_error": f"{type(exc).__name__}: {exc}"
                                          f"（安装链失败）"}
        # V0.14.0 P4-W2 实证语义修订：激活后**无条件暖复位**（CG7 正典
        # 语义「激活暖复位 ACTIVE」——同 app 重部署场景 state 已 ACTIVE
        # 但跑的是旧内容，条件复位会漏；自 flash 装载 = 最强合同）。热
        # 切换板行为并入正典（atk 窗 90s 实测覆盖 boot）。复位 = RTS
        # 脉冲（教训 42 DTR/RTS 显式管理）。
        try:
            self._log("[c6] 激活完成——暖复位走自 flash 装载（CG7 语义）")
            self._serial_reset(serial_port)
            out["post_reset"] = True
        except Exception as exc:  # noqa: BLE001
            out["reset_error"] = f"{type(exc).__name__}: {exc}"
        try:
            with ZenohService(self._locator) as svc:
                out["post"] = net_deploy.post_deploy_check(
                    svc, node, cube, serial_port=serial_port,
                    window_s=window_s, pass_patterns=list(criteria))
        except Exception as exc:  # noqa: BLE001
            out["post_error"] = f"{type(exc).__name__}: {exc}"
        return True, out

    def _serial_reset(self, port: str, baud: int = 115200) -> None:
        """RTS 脉冲复位（pyserial；DTR 保持低——教训 42 时序纪律）。"""
        import time as _t

        import serial  # noqa: PLC0415 —— 方法内惰性（CLI 面不强制 pyserial）

        ser = serial.Serial(port, baud, timeout=1)
        ser.dtr = False
        ser.rts = True
        _t.sleep(0.1)
        ser.rts = False
        ser.close()


# ---- 检查项（C1-C6；依赖链 = LLD-A12 §3 表 + §4.1 派生 SKIP 规则）--------------

def _norm_chip(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _skip(check: str, detail: str, *, derived: bool) -> CheckResult:
    return CheckResult(check=check, verdict=SKIP, detail=detail,
                       derived_skip=derived)


def _c1_serial(profile: BoardProfile, tr: BoardTransport) -> CheckResult:
    t0 = time.monotonic()
    ok, why = tr.port_ready(profile.serial.port)
    return CheckResult(
        check="C1", verdict=PASS if ok else FAIL, detail=why,
        evidence=[] if ok else [why],
        facts={"port": profile.serial.port},
        dur_ms=int((time.monotonic() - t0) * 1000))


def _c2_flash(profile: BoardProfile, tr: BoardTransport) -> CheckResult:
    t0 = time.monotonic()
    ok, facts, evidence = tr.flash_identity(profile.serial.port,
                                            profile.flash.chip)
    got_chip = _norm_chip(str(facts.get("chip", "")))
    want_chip = _norm_chip(profile.flash.chip)
    match = (ok and got_chip == want_chip
             and int(facts.get("size_kb", 0)) == profile.flash.size_kb)
    detail = (f"chip={facts.get('chip')} size={facts.get('size_kb')}KB "
              f"期望 chip={profile.flash.chip} size={profile.flash.size_kb}KB")
    return CheckResult(
        check="C2", verdict=PASS if match else FAIL, detail=detail,
        evidence=evidence, facts=facts,
        dur_ms=int((time.monotonic() - t0) * 1000))


def _c3_boot(profile: BoardProfile, tr: BoardTransport) -> CheckResult:
    t0 = time.monotonic()
    ok, lines = tr.boot_capture(profile.serial.port, profile.serial.baud,
                                profile.boot.timeout_s, profile.boot.reset)
    missing = [p for p in profile.boot.ready_patterns
               if not any(p in ln for ln in lines)]
    verdict = PASS if ok and not missing else FAIL
    detail = ("就绪判据全命中: " + "; ".join(profile.boot.ready_patterns)
              if verdict == PASS else
              f"未命中判据: {missing}" if missing else "抓取失败")
    return CheckResult(
        check="C3", verdict=verdict, detail=detail, evidence=lines,
        facts={"ready_patterns": list(profile.boot.ready_patterns),
               "lines_total": len(lines),
               "evidence_scope": ("full" if len(lines) <= _EVIDENCE_TAIL
                                  else f"tail{_EVIDENCE_TAIL}")},
        dur_ms=int((time.monotonic() - t0) * 1000))


def _c4_zenoh(profile: BoardProfile, tr: BoardTransport) \
        -> tuple[CheckResult, dict[str, Any]]:
    """回执附 env（{node, cube, snapshot}）供 C5/C6 消费。"""
    t0 = time.monotonic()
    ok, nodes = tr.discover(timeout_s=10.0)
    if not ok:
        return CheckResult(
            check="C4", verdict=FAIL,
            detail=f"discover 失败: {nodes[0].get('error', '?') if nodes else '?'}",
            evidence=[str(n) for n in nodes],
            dur_ms=int((time.monotonic() - t0) * 1000)), {}
    cubes = [(n.get("node_id", ""), n.get("cube_id", "")) for n in nodes]
    if profile.zenoh.cube:
        hit = [nc for nc in cubes if nc[1] == profile.zenoh.cube]
    else:
        hit = cubes  # 空 = 恰一在线即本板
    if len(hit) != 1:
        why = (f"期望 cube={profile.zenoh.cube} 未在线"
               if profile.zenoh.cube else
               f"在线 cube 数={len(cubes)}（未指名 cube 时须恰一——"
               f"多板在线请在画像 [zenoh] cube 回填自报名）")
        return CheckResult(
            check="C4", verdict=FAIL, detail=why,
            evidence=[str(n) for n in nodes], facts={"cubes": cubes},
            dur_ms=int((time.monotonic() - t0) * 1000)), {}
    node, cube = hit[0]
    ok2, snap = tr.node_snapshot(node, cube)
    if not ok2:
        return CheckResult(
            check="C4", verdict=FAIL,
            detail=f"命令面快照失败: {snap.get('error', '?')}",
            evidence=[str(snap)], facts={"node": node, "cube": cube},
            dur_ms=int((time.monotonic() - t0) * 1000)), {}
    res = CheckResult(
        check="C4", verdict=PASS,
        detail=f"node={node} cube={cube} 命令面回执全通",
        facts={"node": node, "cube": cube, "fw": snap.get("get-info", {})
               .get("fw") if isinstance(snap.get("get-info"), dict) else None},
        dur_ms=int((time.monotonic() - t0) * 1000))
    return res, {"node": node, "cube": cube, "snapshot": snap}


def _caps_of(snap: dict[str, Any]) -> dict[str, Any]:
    """caps 块提取（get-info 回执嵌套优先，扁平键兜底——固件两代形态）。"""
    info = snap.get("get-info")
    if not isinstance(info, dict):
        return {}
    caps = info.get("caps")
    if isinstance(caps, dict):
        return caps
    flat = {k: info[k] for k in ("tiers", "slot_pool_kb",
                                 "max_linear_memory_kb") if k in info}
    return flat


def _c5_caps(profile: BoardProfile, env: dict[str, Any],
             pre: list[CheckResult]) -> CheckResult:
    t0 = time.monotonic()
    if profile.caps is None:
        return _skip("C5", "画像未声明 [caps] 节（声明 SKIP）", derived=False)
    c4 = next((r for r in pre if r.check == "C4"), None)
    if c4 is None or c4.verdict != PASS:
        return _skip("C5", "前置 C4 未过（派生 SKIP）", derived=True)
    snap = env.get("snapshot", {})
    caps = _caps_of(snap)
    if not caps:
        return CheckResult(
            check="C5", verdict=FAIL,
            detail="固件 get-info 未自报 caps 块（旧固件？）",
            evidence=[str(snap.get("get-info"))][:20],
            dur_ms=int((time.monotonic() - t0) * 1000))
    got_tiers = [str(x) for x in caps.get("tiers", [])]
    want_tiers = [str(x) for x in profile.caps.tiers]
    missing = [t for t in want_tiers if t not in got_tiers]
    pool = int(caps.get("slot_pool_kb", 0))
    ok = not missing and pool >= profile.caps.min_slot_pool_kb
    detail = (f"tiers={got_tiers} slot_pool={pool}KB "
              f"（期望 ⊇{want_tiers} ≥{profile.caps.min_slot_pool_kb}KB）")
    return CheckResult(
        check="C5", verdict=PASS if ok else FAIL, detail=detail,
        facts={"caps": caps},
        dur_ms=int((time.monotonic() - t0) * 1000))


def _c6_smoke(profile: BoardProfile, tr: BoardTransport, env: dict[str, Any],
              pre: list[CheckResult]) -> CheckResult:
    t0 = time.monotonic()
    if profile.smoke is None:
        return _skip("C6", "画像未声明 [smoke] 节（零板态扰动）", derived=False)
    c4 = next((r for r in pre if r.check == "C4"), None)
    if c4 is None or c4.verdict != PASS:
        return _skip("C6", "前置 C4 未过（派生 SKIP——部署链不可达）",
                     derived=True)
    node, cube = env["node"], env["cube"]
    ok, out = tr.deploy_smoke(
        node, cube, profile.smoke.package_path, profile.smoke.pub_path,
        list(profile.smoke.criteria), profile.serial.port,
        profile.smoke.window_s)
    if not ok:
        return CheckResult(
            check="C6", verdict=FAIL,
            detail=f"部署失败: {out.get('deploy_error', '?')}",
            evidence=[str(out)],
            facts={"board_state_note": "部署链失败——板态未变更或部分变更，"
                                       "以 get-app 复核为准"},
            dur_ms=int((time.monotonic() - t0) * 1000))
    post = out.get("post", {})
    cp = post.get("criteria_pass")
    facts = {"deploy": out.get("deploy"), "get_app_before_note":
             "v1 不自动还原——探针包驻留 ACTIVE 槽（画像 smoke 节即显式授权）"}
    if cp is True:
        return CheckResult(
            check="C6", verdict=PASS,
            detail=f"部署+判据命中: {profile.smoke.criteria}",
            evidence=[str(post.get("diag", {}))],
            facts=facts, dur_ms=int((time.monotonic() - t0) * 1000))
    if cp is None:
        return CheckResult(
            check="C6", verdict=SKIP,
            detail="部署成功但判据窗抓取失败——未验证（≠ 未命中，如实区分）",
            evidence=[str(post.get("diag_error", ""))],
            facts=facts, derived_skip=True,
            dur_ms=int((time.monotonic() - t0) * 1000))
    diag = post.get("diag", {})
    return CheckResult(
        check="C6", verdict=FAIL,
        detail=f"判据 miss: {profile.smoke.criteria}",
        evidence=[f"{diag.get('category')}: {diag.get('summary')}",
                  str(diag.get("repair_hint"))],
        facts=facts | {"diag": diag},
        dur_ms=int((time.monotonic() - t0) * 1000))


# ---- 流水线 ------------------------------------------------------------------

def validate(
    profile: BoardProfile,
    transport: BoardTransport,
    *,
    checks: list[str] | None = None,
    stop_on_fail: bool = False,
    progress_cb: Any = None,
) -> BoardReport:
    """执行检查流水线（同步阻塞——调用方经 asyncio.to_thread）。

    依赖链：C1 FAIL = 终止（物理域）；C3 FAIL → C4 派生 SKIP；
    C4 非 PASS → C5/C6 派生 SKIP。stop_on_fail = 首个 FAIL 后全收
    （余项记派生 SKIP）。progress_cb({check, verdict, done, total,
    verdicts}) 逐检查回调（MCP 层映射 Task.progress / D2 面）。
    """
    selected = list(checks) if checks else list(CHECK_ORDER)
    unknown = [c for c in selected if c not in CHECK_ORDER]
    if unknown:
        raise ProfileError(f"未知检查项: {unknown}（合法 = {list(CHECK_ORDER)}）")
    t0 = time.monotonic()
    results: list[CheckResult] = []
    env: dict[str, Any] = {}

    def c3_failed() -> bool:
        return any(r.check == "C3" and r.verdict == FAIL for r in results)

    def c4_passed() -> bool:
        return any(r.check == "C4" and r.verdict == PASS for r in results)

    def report_so_far() -> BoardReport:
        return BoardReport(
            board_id=profile.id, description=profile.description,
            started_at=t0, dur_s=time.monotonic() - t0, checks=list(results))

    def emit(name: str, res: CheckResult) -> None:
        results.append(res)
        if progress_cb is not None:
            progress_cb({
                "stage": "board_validate", "check": name,
                "verdict": res.verdict, "done": len(results),
                "total": len(selected),
                "verdicts": {r.check: r.verdict for r in results},
            })

    for name in selected:
        if stop_on_fail and any(r.verdict == FAIL for r in results):
            emit(name, _skip(name, "stop_on_fail 提前收（派生 SKIP）",
                             derived=True))
            continue
        if name == "C1":
            res = _c1_serial(profile, transport)
            emit(name, res)
            if res.verdict == FAIL:
                for rest in selected[selected.index(name) + 1:]:
                    emit(rest, _skip(rest, "前置 C1 未过——串口物理域终止"
                                     "（派生 SKIP）", derived=True))
                break
            continue
        if name == "C2":
            emit(name, _c2_flash(profile, transport))
            continue
        if name == "C3":
            emit(name, _c3_boot(profile, transport))
            continue
        if name == "C4":
            if c3_failed():
                emit(name, _skip("C4", "前置 C3 未过——链路域派生 SKIP",
                                 derived=True))
            else:
                res, env = _c4_zenoh(profile, transport)
                emit(name, res)
            continue
        if name == "C5":
            emit(name, _c5_caps(profile, env, results))
            continue
        if name == "C6":
            emit(name, _c6_smoke(profile, transport, env, results))
            continue
    return report_so_far()
