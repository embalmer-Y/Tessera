# SPDX-License-Identifier: Apache-2.0
"""eval.suite — AC-1 能力评估基准任务谱（DEC-81；plan v1.161 L 表）。

任务谱 T1-T5 = 创作链能力标尺：T1 单文件 log-only（基线面）→ T2 多文件
工程（R7 §2 聚合链）→ T3 caps 真写入（声明-调用一致性）→ T4 threads 档
（M19/DEC-55）→ T5 resources 外置（CG4/Q-39② large 档）。

spec 文本 = 真实需求措辞（不出现内部术语 ts_native/caps 之外的引导外的
实现指令——创作自由度留给模型，评分只对**期望轮廓**机械对拍）。
expect 键（评分器对拍面，全部机械可判）：
  imports_allowed  导入面允许族（⊆ NATIVE_WHITELIST；模型可少用不可越）
  exports_required 必需导出（框架回调四件套或下限）
  caps_expected    期望申报的 caps 前缀族（缺省 []——log 豁免不列）
  threads          期望 manifest.threads
  tier             期望 manifest.tier（small 缺省）
  needs_expected   期望 manifest.needs 键（T5 resources 外置）
  min_source_files 工程最少源文件数（T2 多文件面）
  max_size_kb      wasm 尺寸上限（档门内的任务级收紧；缺省按 tier 门）
"""
from __future__ import annotations

from dataclasses import dataclass, field

T1_SPEC = """为立方体设备写一个心跳计数 APP：
APP 被激活后每累计 10 个 tick 通过日志输出一行 "HB n=<累计 tick 数>"
（十进制、无其它前后缀）；计数值在 APP 生命周期内持续累加。取一个
固定的上报节拍，保证日志行间隔均匀稳定。"""

T2_SPEC = """为立方体设备写一个滑动窗口平均滤波 APP：
对外部输入值序列做窗口为 8 的滑动平均。输入序列由 APP 内部确定性
生成器模拟（无随机）：第 k 个输入值 = (k*37) % 251。每处理 40 个输入
经日志输出一行 "AVG k=<已处理数> avg=<当前窗口均值，保留 1 位小数>"。
工程要求：滤波逻辑独立成模块（filter 模块：初始化 + 递进更新两个
接口），主模块只做调度与上报——分模块多文件组织，头文件放 include/ 目录。"""

T3_SPEC = """为立方体设备写一个输出通道自检 APP：
APP 激活后按固定节拍翻转一个数字输出通道（开 1s / 关 1s 交替），
并同步读一次通道电平做回读核对。每完成 5 个完整周期经日志输出一行
"TOGGLE cycles=<已完成周期数>"。需要申报数字输出权限；确定性运行，
上电从全关开始。"""

T4_SPEC = """为立方体设备写一个双线程并行累加 APP：
主线程创建一个工作线程，两线程各自对同一共享计数器做原子累加
（各 1000 次，内存序安全）；主线程 join 工作线程后经日志输出一行
"PARALLEL total=<最终计数>"（应为 2000）。要求申报多线程，工作线程
经线程原语创建（非主 tick 路径），join 后再上报。"""

T5_SPEC = """为立方体设备写一个校准系数查表 APP：
校准表（16 项，每项 = 索引 0-15 → 增益系数 ×10 的整数值，内容用
1..16 的平方）作为只读数据文件由部署管线外置推送，不编译进 wasm；
APP 激活后从文件系统读取整张表到内存，随后每 20 tick 取当前 tick
计数值模 16 为索引，经日志输出一行 "CAL idx=<索引> gain=<查表值>"。
需要申报文件读取权限，并以 large 档声明资源需求（资源路径前缀
/config/）。"""


@dataclass
class EvalTask:
    id: str
    title: str
    spec: str
    expect: dict = field(default_factory=dict)


def _e(**kw) -> dict:
    """expect 缺省补全（评分器侧再兜底——此处显式声明任务差异面）。"""
    base = {"caps_expected": [], "threads": 1, "tier": "small",
            "needs_expected": None, "min_source_files": 1}
    base.update(kw)
    return base


SUITE: list[EvalTask] = [
    EvalTask("T1", "单文件 log-only 基线（心跳计数）", T1_SPEC, _e(
        imports_allowed=["ts_log_write", "ts_time_ms"],
        exports_required=["health_ping", "app_init", "app_tick"],
        max_size_kb=16,
    )),
    EvalTask("T2", "多文件工程（滑动平均 + 独立滤波模块）", T2_SPEC, _e(
        imports_allowed=["ts_log_write", "ts_time_ms"],
        exports_required=["health_ping", "app_init", "app_tick"],
        min_source_files=2,
        max_size_kb=16,
    )),
    EvalTask("T3", "caps 真写入（输出通道自检）", T3_SPEC, _e(
        imports_allowed=["ts_gpio_write", "ts_gpio_read", "ts_time_ms",
                         "ts_log_write"],
        exports_required=["health_ping", "app_init", "app_tick"],
        caps_expected=["gpio:"],
        max_size_kb=16,
    )),
    EvalTask("T4", "threads 档（双线程并行累加）", T4_SPEC, _e(
        imports_allowed=["ts_thread_start", "ts_thread_join", "ts_log_write",
                         "ts_time_ms"],
        exports_required=["health_ping", "app_init", "app_tick"],
        threads=2,
        max_size_kb=16,
    )),
    EvalTask("T5", "resources 外置（large 档校准查表）", T5_SPEC, _e(
        imports_allowed=["ts_fs_read", "ts_time_ms", "ts_log_write"],
        exports_required=["health_ping", "app_init", "app_tick"],
        caps_expected=["fs:"],
        tier="large",
        needs_expected={"resources": True},
        max_size_kb=256,
    )),
]

_EXPECT_KEYS = frozenset(_e().keys()) | {
    "imports_allowed", "exports_required", "max_size_kb"}


def select(ids: list[str] | None) -> list[EvalTask]:
    """按 id 选择子集；None/空 = 全谱。未知 id = ValueError（fail-closed）。"""
    if not ids:
        return list(SUITE)
    by_id = {t.id: t for t in SUITE}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise ValueError(f"未知任务 id: {unknown}（可用: {sorted(by_id)}）")
    return [by_id[i] for i in ids]
