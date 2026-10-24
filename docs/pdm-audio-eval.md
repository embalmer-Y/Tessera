# MD1.2c · PDM 音频驱动扩展评估（单元 E）

> 2026-10-07 · 排期表 v1.30 单元 E（DEC-46 遗留：Sense 板麦克风支持面）。
> 结论先行：**技术路径可行（模块内最小 PDM RX 驱动，约一个交付会话）；
> 但当前无已承诺消费者（D 阶梯无音频 demo）——建议缓办，实施路径留档
> 供真实消费者出现时启用**。本评估零代码改动（军规 9）。

## 1. 需求与硬件事实

- **硬件**：XIAO ESP32S3 Sense 板载 MP34DT05TR-M PDM 麦克风（DEC-46 硬件
  即板载 Sense 版）。引脚待原理图核验（疑似 GPIO41 DATA / GPIO42 CLK——
  控制台占 43/44，41/42 空闲；实施批第一步须以 Seeed 原理图钉死）。
- **消费者盘点（本评估核心依据）**：D1-D9 全阶梯**无音频 demo**——D4/D6 =
  ADC/输入监视器面，D8 = 部署全生命周期，D9 = G3+断链时间线。av 类
  （DEC-47③）V1 语义 = 摄像头采集（ts_av_capture）。**音频无承诺交付物**。

## 2. 上游支持面（2026-10-07 钉版树核验）

| 层 | 现状 | 证据 |
|---|---|---|
| Zephyr v4.4 `i2s_esp32.c` | **零 PDM 支持**（无 pdm 字样） | drivers/i2s/i2s_esp32.c grep 零命中 |
| Sense 板 DT | **无麦克风节点**（Sense 变体只加摄像头） | xiao_esp32s3_procpu_sense.dts |
| hal_espressif `esp_hal_i2s` 组件 | **esp32s3 PDM 寄存器层齐全**：`i2s_ll_rx_enable_pdm`（rx_pdm_en + 硬件 PDM→PCM）、`i2s_ll_rx_set_pdm_dsr`（降采样率）、TX 侧 pcm2pdm 同在 | components/esp_hal_i2s/esp32s3/include/hal/i2s_ll.h（52 处 pdm） |
| include 路径 | `hal/i2s_ll.h` 已在 esp32s3 构建路径（树内 i2s_esp32.c 正在消费 i2s_ll_* 函数） | i2s_esp32.c:249/822/913 |

## 3. 方案选项

- **A) 模块内最小 PDM RX 驱动**（`ts-drv-pdm`，类比 TS_DRV_GPIO/PWM 先例）：
  DT overlay（mic 节点 + pinctrl + GPIO matrix 路由）+ i2s_ll.h 寄存器配置
  （PDM RX 使能 + 硬件降采样 → 16bit PCM）+ GDMA 通道（可参考树内 i2s_esp32.c
  的 DMA 脚手架，复制语义不补丁上游）+ 缓冲队列。~300-500 行 + bench 载体 +
  Kconfig。**零上游补丁**（纪律兼容）。工作量 ≈ 1 交付会话（含真机 bring-up
  2-3 轮迭代）；风险中（引脚核验 + 寄存器级首点）。
- **B) 上游贡献**（给 Zephyr i2s_esp32 加 PDM）：周期长（PR/评审/合入版本
  节奏），V1 时间线外——与 zenoh-pico issue 同为登记不提策略。
- **C) 缓办**（本建议）：路径留档（= A 的设计事实），消费者出现时按档实施。

## 4. 建议：C（缓办）

- **依据**：① 无已承诺消费者（§1）——投入即刻无验证出口（demo/判据皆无）；
② 剩余排期单元价值更高（B2 缺陷专项 / F 输入面 G3〔D9 依赖〕/ G 板级余项
〔MCUmgr OTA 已裁未实现〕）；③ 实施路径已钉死（§2/§3A），缓办零沉没成本。
- **触发条件**（满足其一时重开）：owner 指令音频需求；MD2 扩展含音频
  demo；P4 板音频面（单元 J 时一并核验 esp32p4 的 PDM 支持）；上游
  i2s_esp32 加 PDM（随 Zephyr 升级评估收割）。
- **重开时的设计既定点**（本评估沉淀）：模块内驱动（A 方案）；音频采集
  API 归属 av 类（`ts_av_capture` 音频变体或独立面）——涉权限文法/公共
  API = **门③呈递**（届时随实作批登记 Q）。

## 5. 影响与登记

- 排期表：单元 E 关闭（评估交付 + 缓办结论）；下一单元 F（输入面 G3 批）。
- 无代码/无格式/无权限面变更——无需门项。
- MD1.2 全部子项自此收口：a(SD)✅ b(摄像头)✅ d(传输 spike+DEC-47)✅
  e(ts-fs)✅ f(D-SD)✅ g(ts-av+publish)✅ h(D-AV 90%/DAV1)◐ c(PDM 评估)✅。
