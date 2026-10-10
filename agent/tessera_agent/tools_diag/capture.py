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
