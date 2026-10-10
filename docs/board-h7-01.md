# board-h7-01 · H7 移植批：WeAct MiniSTM32H743 板级 bring-up（构建级）

> **状态**：v0.1 · 2026-10-10 · H7 板级移植交付单元报告（DEC-28 目标集第三板：ESP32-S3 → P4 → H7）。
> **DoD（本版 = 构建级）**：h7bench @ mini_stm32h743 构建绿（ts 框架最小面 + WAMR ARM/Thumb）；回归全绿。**真机判据待 owner 接板**（ST-LINK 烧录 + USART1 console；本页 §6 预案）。
> 关联：DEC-28（板卡目标集）、docs/h7-memory-assessment.md（容量评估 §4 前置项）、教训 30/31。

## 1. 板与目标

| 项 | 值 | 出处 |
|---|---|---|
| 载板 | WeAct Studio MiniSTM32H743 核心板（owner 持板） | owner 指令 |
| 芯片 | STM32H743VIT6（Cortex-M7 @480MHz，2MB 内部 flash，1MB RAM 多域） | 树内板 dts |
| 板载资源 | 8MB QSPI（W25Q64，本批不用）、ST7735 屏/DVP 连接器（不涉）、**无板载调试器** | 板 dts |
| Zephyr 板目标 | `mini_stm32h743`（树内 waveshare 旁 weact 板；stm32h743vitx pinctrl 在 hal_stm32 module dts 融合路径） | 本批确认 |
| WAMR target | `THUMBV7EM`（module CMakeLists 板映射登记；见 §3 教训） | 本批 |
| console | overlay 补 chosen = usart1（PA9 TX/PA10 RX，AF7）——板 dts 无 console chosen；排针引出经 USB-TTL（115200） | 本批 overlay |
| 工具链 | SDK 1.0.1 `arm-zephyr-eabi`（h7 评估批已装） | dev-env §2 |

## 2. 分区布局（h7bench overlay，内部 flash 2MB）

**H743 擦除块 = 128KB**（dtsi 事实）——P4/S3 的 4KB 粒度五分区模式不可平移：**每分区独占整扇区**（擦除互不伤害）：

| 分区 | 偏移 | 尺寸 | 说明 |
|---|---|---|---|
| （app 域） | 0x000000 | 768KB | Zephyr 镜像链接域（实测 h7bench 镜像 158KB——余量充分） |
| ts_prov_part | 0x0c0000 | 128KB | provisioning |
| ts_meta_part | 0x0c2000 | 128KB | meta 双副本（步距 64KB） |
| ts_slot_a_part | 0x0c4000 | 128KB | = CONFIG_TS_STORE_SLOT_SIZE（131072） |
| ts_slot_b_part | 0x0c6000 | 128KB | |
| ts_noinit_part | 0x0c8000 | 128KB | 复位留痕 |
| fw_b_part | 0x0ca000 | 224KB | MCUmgr 第二 slot 预留（V1 未接线） |

板载 QSPI 的 ext-flash slot0 声明原样保留（不消费）。五分区带 mapped-partition 兼容串（教训 30②）。

## 3. 本批教训（WAMR ARM 汇编）

**WAMR target 必须取 THUMB 系而非 ARM**：Zephyr ARM 构建全 `-mthumb`，而 WAMR `invokeNative_arm.s` 是 A32 汇编——汇编期即拒（`lo register required` / `Thumb does not support this addressing mode`）。`THUMBV7EM` 走 `invokeNative_thumb.s`（iwasm_common.cmake 的 `THUMB.*` 分支）。解释器-only（AOT=0/JIT=0）下该汇编不参与运行，仅过链接——与 P4 批"target 声明 = ABI 元数据"论证同构。

## 4. 构建级结果（2026-10-10）

- **h7bench 构建绿**：`west build -p -b mini_stm32h743`（overlay 拾取 ✓ / WAMR THUMBV7EM ✓ / ts 五分区 flash_map ✓）。
- 内存面（linker 实测）：FLASH **161,364B（158KB / 2MB = 7.6%）**；sram0 bss **357,597B（349KB / 512KB = 68%，含 WAMR 全局堆 262,144B）**——与 h7-memory-assessment §1-④' 推算吻合（该报告按网面全配置口径 388KB；本 bench 无网面为下界）。
- 回归：twister native_sim **15/15（77 用例）** + pytest 2/2（改动零触及 native 面）。
- h7bench = persistbench 源级复用（判据前缀 H7B；TSAP v2 包 `com.tessera.h7b` 928B——gen_h7_pkg.py 机械生成，测试根签名）。

## 5. 板级内存定值（h7bench 板 conf）

- `CONFIG_TS_STORE_SLOT_SIZE=131072`（= 扇区 128KB 耦合）；
- `CONFIG_TS_APP_THREAD_STACK=16384`（S3/P4 同值）；
- `CONFIG_MAIN_STACK_SIZE=8192`（P4 批 RV32 溢出教训的保守起值，ARM 侧待真机复核）。

## 6. 真机判据预案（待 owner 接板）

1. **接线**（已告知 owner）：①Type-C 供电；②ST-LINK（SWD：SWDIO→PA13、SWCLK→PA14、GND、3.3V）——烧录必需（板无调试器、H7 无 ROM USB DFU）；③USB-TTL 接 USART1（TX→PA10、RX→PA9、GND 共地，115200）。
2. **烧录**：ST-LINK 经 usbipd attach → WSL OpenOCD（`west flash` 默认 openocd runner）。
3. **判据**：H7B0→H7B1（prov 注入）→H7B2（v2 包安装）→暖复位→H7B3/H7B5（flash 自举 + WAMR@Cortex-M7 ACTIVE + 写链）→H7B PASS。
4. **已知风险**：①板 dts 声明 HSE 25MHz——WeAct 实板常见 12MHz 晶振，若 console 乱码即以 overlay 改 `&clk_hse`（12M + PLL 参数 M=12/N=480/P=2 保持 240MHz SYSCLK）；②stm32h7 flash 驱动写对齐（4B 垫片语义）真机复核。

## 7. 遗留与后续

- 真机判据（§6）= 下一交付单元（板接后）。
- WAMR 堆迁 D2 SRAM（sram1+sram2 合并 256KB——h7-memory-assessment §4-2）= 内存预算批。
- ETH 网面（板上无 PHY？WeAct 核心板无 RJ45——ETH 面需评估外接或弃用，网面按 H7 评估走 nucleo 的结论暂不可平移）= 联网批前评估。
