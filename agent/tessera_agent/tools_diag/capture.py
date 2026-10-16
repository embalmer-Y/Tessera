# SPDX-License-Identifier: Apache-2.0
"""串口判据抓取（NV-1；真机面，环境门控）。

复位（RTS 脉冲）→ 窗口读全文 → 返回文本交 classify_run 分类。抓取
编排复用批 A 定式（esptool --after no_reset / RTS 手动复位——教训 22⑥：
esptool 尾部硬复位会抢跑首启观测窗口）。

pyserial 懒导入（agent venv 已装 3.5；CI 环境不装也能导入本模块——
只有真调用才需要）。
"""
from __future__ import annotations

import time


def reset_and_capture(
    port: str,
    seconds: float,
    *,
    baud: int = 115200,
    rst_hold_s: float = 0.1,
) -> str:
    """复位目标板并抓取启动后 seconds 秒的串口全文（阻塞函数）。

    调用方在事件循环内须经 asyncio.to_thread（ASYNC 规约）。
    """
    import serial  # 懒导入：CI 无串口环境不触发

    with serial.Serial(port, baud, timeout=1) as s:
        # ESP32 系：RTS 线接 EN——拉低保持即复位，释放即启动
        s.dtr = False
        s.rts = True
        time.sleep(rst_hold_s)
        s.rts = False
        buf = b""
        t0 = time.monotonic()
        while time.monotonic() - t0 < seconds:
            buf += s.read(4096)
    return buf.decode("utf-8", "replace")


def capture_window(
    port: str,
    seconds: float,
    *,
    baud: int = 115200,
) -> str:
    """被动窗口抓取（G 批 D3：部署后诊断自动回喂——不复位）。

    开埠本身在部分适配器（CH340 一键下载电路）产生复位脉动——失败路径
    诊断场景可接受（正在诊断的板子复位后恰好提供启动窗分类证据；F3
    登记在案）。健康路径不应调用本函数（调用方门控：post-check 仅在
    get-app 非 ACTIVE 时触发）。
    """
    import serial  # 懒导入：CI 无串口环境不触发

    with serial.Serial(port, baud, timeout=1) as s:
        buf = b""
        t0 = time.monotonic()
        while time.monotonic() - t0 < seconds:
            buf += s.read(4096)
    return buf.decode("utf-8", "replace")
