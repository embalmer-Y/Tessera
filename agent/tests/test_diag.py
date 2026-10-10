# SPDX-License-Identifier: Apache-2.0
"""NV-1 部署后诊断测试：分类器向量（历史真机失败形态）+ 修复闭环编排。

向量来源（每条注明历史单迹）：
- 坏卡 dsdbench：批 A 2026-10-10 诊断深化单迹（fs mount -5 / sd: Write
  failed / CMD13 BUSY 形态）
- 换卡 PASS：2026-10-11 dsd_PASS_newcard.txt 全文摘录
- 静默死：boardbench BB1 原型（ACTIVE 后无输出——健康链终止）
- 看门狗：wdtbench / inputdemo IR2-06 升级链形态
- 安装链负码：persistbench MD 批分步报码形态
编排用例全 mock（deploy_fn/capture_fn/app_develop 注入）——真机闭环走
gated 仓外验证（NV-1 交付单迹）。
"""
from __future__ import annotations

import asyncio

from tessera_agent.tools_diag import classify as dc
from tessera_agent.tools_diag import repair as rp

PASS_PAT = ["DS PASS"]


def _cls(text: str, pass_patterns=None, alive=("alive",)):
    return dc.classify_run(text, pass_patterns=pass_patterns or PASS_PAT,
                           alive_patterns=alive)


# ---- 分类器向量（历史真机形态）----

def test_classify_pass_newcard():
    """换卡后 D-SD 全链 PASS（2026-10-11 单迹摘录）。"""
    text = "\n".join([
        "DS0 dsdbench（MD1.2f：D-SD demo ts-fs 全链）",
        "sd: Maximum SD clock is under 25MHz, using clock of 20000000Hz",
        "DS1 SD mounted",
        "DS2 install r=0 state=2 slot=1",
        "DS3 APP ACTIVE app=tessera.demo.d-sd",
        "DS4 done marker seen",
        "DS5 data verify n=68 OK",
        "DS6 deny-file absent=1（白名单外写被拒的物理证据）",
        "DS PASS（写/读回/白名单拒绝/列目录全链）",
        "DS alive t=12810",
    ])
    r = _cls(text)
    assert r.category == dc.DIAG_PASS


def test_classify_env_boot_badcard():
    """坏卡形态（2026-10-10 批 A 诊断单迹）：挂载失败 → 环境层。"""
    text = "\n".join([
        "DS0 dsdbench（MD1.2f：D-SD demo ts-fs 全链）",
        "sd: Maximum SD clock is under 25MHz, using clock of 20000000Hz",
        "sd: Write failed",
        "fs: fs mount error (-5)",
        "DS FAIL mount r=-5",
        "DS FAIL no ACTIVE",
    ])
    r = _cls(text)
    assert r.category == dc.DIAG_ENV_BOOT
    assert "重生成" in r.repair_hint or "环境" in r.repair_hint


def test_classify_install_fail():
    """安装链分步负码（persistbench MD 批 begin/chunk/verify 报码形态）。"""
    text = "\n".join([
        "PB1 prov ok",
        "install begin r=-13",
        "PB FAIL install",
    ])
    r = _cls(text)
    assert r.category == dc.DIAG_INSTALL_FAIL


def test_classify_verify_reject():
    """verify 步负码（v2 验签拒收族——DEC-49② 后 v1 包被拒形态）。"""
    text = "\n".join([
        "boot step 5 store ok",
        "install chunk r=0 n=18",
        "install verify r=-22",
        "install state=0",
        "reboot",
    ])
    r = _cls(text)
    assert r.category == dc.DIAG_INSTALL_FAIL


def test_classify_not_active():
    """boot 链跑起来但 APP 未装载（caps 走查拒收/exports 缺失形态）。

    注：向量文本不得含 "ACTIVE" 子串（装载拒收的 log 形态是
    slot 空/拒收行，分类器按子串匹配）。"""
    text = "\n".join([
        "boot step 1 estop ok",
        "boot step 6 net ok",
        "wifi: associated, ip 192.168.2.13",
        "ts: session up",
        "slot0 empty, slot1 rejected: caps invalid",
        "idle loop",
    ])
    r = _cls(text, pass_patterns=["XX PASS"])
    assert r.category == dc.DIAG_NOT_ACTIVE


def test_classify_no_verdict_empty_window():
    """空窗/近乎无输出（连接或窗口问题）——不得误报装载失败。"""
    r = _cls("\n".join(["", "  ", "rst:0x1 (POWERON)"]))
    assert r.category == dc.DIAG_NO_VERDICT


def test_classify_wdt_reset():
    """看门狗复位（ACTIVE 后 task wdt 形态——wdtbench/IR2-06 家族）。"""
    text = "\n".join([
        "boot step 8 slot load ok",
        "TS3 APP ACTIVE app=demo.x",
        "app tick running",
        "task wdt: main thread hung",
        "system_fail: src=TS_WDT_APPMGR",
        "rst:0x10 (TWDT)",
    ])
    r = _cls(text)
    assert r.category == dc.DIAG_WDT_RESET


def test_classify_app_silent():
    """静默死（boardbench BB1 原型）：ACTIVE 后无任何输出（判据与心跳俱无）。"""
    text = "\n".join([
        "boot step 8 slot load ok",
        "TS3 APP ACTIVE app=demo.bench",
        "(此后再无输出——健康链终止形态)",
    ])
    r = _cls(text)
    assert r.category == dc.DIAG_APP_SILENT
    assert "健康链" in r.repair_hint or "配额" in r.repair_hint


def test_classify_app_no_verdict():
    """APP 存活但判据未达（判据行格式错/阈值不可达——修复闭环主场景）。"""
    text = "\n".join([
        "TS3 APP ACTIVE app=demo.y",
        "app tick n=1",
        "app alive t=1000",
        "app alive t=2000",
        "app alive t=3000",
    ])
    r = _cls(text)
    assert r.category == dc.DIAG_APP_NO_VERDICT


def test_classify_pass_beats_late_reset():
    """判据达成后出现的复位循环不改判（bench 契约：PASS 行即达成）。"""
    text = "\n".join([
        "TS3 APP ACTIVE app=demo.z",
        "DS PASS",
        "DS alive t=12810",
        "task wdt: sweep",
        "rst:0x10",
    ])
    assert _cls(text).category == dc.DIAG_PASS


# ---- 修复闭环编排（全 mock）----

class _LoopHarness:
    """repair_loop 测试脚手架：mock app_develop / deploy / capture。"""

    def __init__(self, monkeypatch, serial_texts, develop_calls=None):
        self.serial_texts = list(serial_texts)
        self.deployed: list[str] = []
        self.develop_calls = develop_calls if develop_calls is not None else []
        self.develop_results: list[dict] = []

        async def fake_develop(ctx, spec, key_path, out_dir="agent/build", *,
                                wasm_path=None, repair_feedback="", model=None,
                                log_fn=None):
            self.develop_calls.append({"spec": spec,
                                       "repair_feedback": repair_feedback})
            out = {"package_path": f"/pkg/round{len(self.develop_calls)}.tsap"}
            self.develop_results.append(out)
            return out

        async def fake_deploy(package_path):
            self.deployed.append(package_path)
            return {"confirmed": True}

        monkeypatch.setattr("tessera_agent.domain.app_chain.app_develop",
                            fake_develop)
        self.deploy_fn = fake_deploy
        self.capture_fn = lambda: (self.serial_texts.pop(0)
                                   if self.serial_texts else "")


PASS_TEXT = "TS3 APP ACTIVE app=d\nDS PASS\nDS alive t=100"
SILENT_TEXT = "TS3 APP ACTIVE app=d\n（无后续输出）"
ENVCARD_TEXT = "sd: Write failed\nfs: fs mount error (-5)\nDS FAIL mount r=-5"


def test_repair_loop_first_round_pass(monkeypatch):
    h = _LoopHarness(monkeypatch, [PASS_TEXT])
    out = asyncio.run(rp.repair_loop(
        None, spec="S", key_path="k", out_dir="o",
        pass_patterns=PASS_PAT, deploy_fn=h.deploy_fn,
        capture_fn=h.capture_fn))
    assert out["status"] == rp.STATUS_PASS
    assert out["rounds_used"] == 1
    assert len(h.develop_calls) == 1        # 无重生成
    assert h.develop_calls[0]["repair_feedback"] == ""


def test_repair_loop_silent_then_pass(monkeypatch):
    h = _LoopHarness(monkeypatch, [SILENT_TEXT, PASS_TEXT])
    out = asyncio.run(rp.repair_loop(
        None, spec="S", key_path="k", out_dir="o",
        pass_patterns=PASS_PAT, deploy_fn=h.deploy_fn,
        capture_fn=h.capture_fn))
    assert out["status"] == rp.STATUS_PASS
    assert out["rounds_used"] == 2
    assert len(h.develop_calls) == 2        # 一次重生成
    fb = h.develop_calls[1]["repair_feedback"]
    assert dc.DIAG_APP_SILENT in fb and "修复方向" in fb
    assert out["history"][0]["category"] == dc.DIAG_APP_SILENT
    assert h.deployed == ["/pkg/round1.tsap", "/pkg/round2.tsap"]


def test_repair_loop_env_fail_no_regen(monkeypatch):
    """环境层失败不烧 LLM 轮次（立即终止）。"""
    h = _LoopHarness(monkeypatch, [ENVCARD_TEXT])
    out = asyncio.run(rp.repair_loop(
        None, spec="S", key_path="k", out_dir="o",
        pass_patterns=PASS_PAT, deploy_fn=h.deploy_fn,
        capture_fn=h.capture_fn))
    assert out["status"] == rp.STATUS_ENV_FAIL
    assert len(h.develop_calls) == 1


def test_repair_loop_budget_exhausted(monkeypatch):
    """轮次耗尽如实失败（max_rounds=1：一次修复机会）。"""
    h = _LoopHarness(monkeypatch, [SILENT_TEXT, SILENT_TEXT])
    out = asyncio.run(rp.repair_loop(
        None, spec="S", key_path="k", out_dir="o",
        pass_patterns=PASS_PAT, deploy_fn=h.deploy_fn,
        capture_fn=h.capture_fn, max_rounds=1))
    assert out["status"] == rp.STATUS_FAIL
    assert out["rounds_used"] == 2          # 首轮 + 1 次修复
    assert len(h.develop_calls) == 2


def test_repair_loop_deploy_error(monkeypatch):
    """部署层异常立即终止（不消耗修复轮次）。"""
    h = _LoopHarness(monkeypatch, [PASS_TEXT])

    async def boom(package_path):
        from tessera_agent.common.errors import TA_E_ARGS, TaError
        raise TaError(TA_E_ARGS, "cube 离线", domain="app_deploy")

    out = asyncio.run(rp.repair_loop(
        None, spec="S", key_path="k", out_dir="o",
        pass_patterns=PASS_PAT, deploy_fn=boom, capture_fn=h.capture_fn))
    assert out["status"] == rp.STATUS_DEPLOY_ERROR
    assert len(h.develop_calls) == 1
