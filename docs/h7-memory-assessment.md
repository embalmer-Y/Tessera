# H7 内存评估 · 各配置内存需求确认 + STM32H743 适配性——评估报告

> **日期**：2026-10-02 · **性质**：owner 询问触发的评估（"内存需求非常紧张，确认各种配置 app 的内存需求，评估 stm32h7 是否符合需求"）——只测量不改产品代码。
> **数据源**：全部为**实构建/实运行**数字（S3 四配置 = 本会话重建的 linker 权威值；H743 = 本会话 nucleo_h743zi 实构建）。构建配方：`~/project/logs/{mem_probe_builds,h7_build}..sh` + `h7mem.conf`。

## 1. 各配置内存需求表（实测）

**ESP32-S3 侧**（dram0_0_seg 可用 **399108B ≈ 390KB**——512KB SRAM 扣 ROM/WiFi 保留后的链接域；cap 见各 map Memory Configuration）：

| 配置 | 内部 DRAM 占用 | 占比 | 外置 | 说明 |
|---|---|---|---|---|
| ① 框架核心+真驱动（safety/core/hal/periph + PWM/ADC 后端，无 APP） | ~65KB* | 16% | 无 | *periphbench 数字——**直启面未根引用 APP 面，WAMR 整树被 --gc-sections 回收**，仅代表"壳"；非框架+WAMR 代表值 |
| ② 框架+WAMR（无网面） | 154,912 | 38.8% | **PSRAM 承 256KB 实例堆** | psrambench 实测；**纯内部装不下**：关 PSRAM + 256KB 堆 → 溢出 14,548B（板级六实测） |
| ③ 网面（WiFi+zenoh+命令面，无 WAMR） | 394,808 | **98.9%** | 无 | netbench 实测（含系统池 188,416 = zenoh 会话峰值域〔板级七实测档位〕） |
| ④ 全配置（WiFi+zenoh+WAMR+flash 持久化） | 398,332 | **99.8%** | **PSRAM 承 256KB 实例堆** | deploybench 实测（板级十已裁剪：LOAD_MAX 2048/通道 8/池 188416） |

**S3 结论**：紧张是真实且结构性的——③ 网面单独就吃 98.9%，④ 全配置的内部需求 ≈ 398K + 262K(堆) ≈ **660KB > 390KB 可用**，因此 S3 全配置**必须 PSRAM**（这正式 DEC-27 的"实例堆入外部 RAM"分层纪律的量化根据：不是优化项，是装不下的硬约束）。256KB 堆是 DEC-27 目标值（64KB 池模式结构性不可行——线性内存一页即 64KB，板级六实证）。

**STM32H743 侧**（nucleo_h743zi 实构建，RAM 口径 = sram0/AXI-D1 512KB 默认链接域，FLASH = 2MB）：

| 配置 | sram0 占用 | 占比 | FLASH |
|---|---|---|---|
| ③' 网面（**ETH 替 WiFi**+zenoh+命令面） | **326,316** | **62.2%** | 233,252（11.1%） |
| ④' 全配置（推算） | **~388KB** | **~76%** | ~430–500KB（估） |

④' 推算：③' 实测 − 池后静态 ≈ 130KB + WAMR 静态 ~43KB（interp 11.1K + loader 15.2K + zephyr_thread 16.4K，S3 实测可移植）+ APP 线程栈 16KB + 装载缓冲 2KB + 池 196,608 ≈ **388KB in sram0**；**WAMR 实例堆 256KB 摆 D2 SRAM**（见 §2）。ROM 侧：H7 网面 233KB + WAMR/appmgr ARM 侧估 150–250KB（S3 psrambench 镜像 211KB 佐证量级）。

## 2. H743 容量事实（Zephyr v4.4 树内）

| RAM 域 | 容量 | 地址 | 默认链接 | 评估用途 |
|---|---|---|---|---|
| sram0（AXI D1） | **512KB** | 0x24000000 | ✓（zephyr,sram） | 框架+网面+池+WAMR 静态（§1 ④' 388KB/76%） |
| sram1+sram2（D2） | 128+128KB | 0x30000000/0x30020000 | 否（DT 声明未链） | **物理连续 256KB = WAMR 实例堆恰好**（合并 region = 链接器工作项） |
| sram3（D2） | 32KB | 0x30040000 | 否（`&mac memory-regions` 专用） | ETH DMA 描述符（板 dts 已绑定） |
| DTCM | 128KB | — | chosen zephyr,dtcm（未用） | 可选：safety 热数据（DEC-27 纪律内=内部 SRAM） |
| SRAM4（D3） | 64KB | 0x38000000 | 否 | 可选：noinit/日志 |
| **内部合计** | **~992KB** | | | 全配置无需外部 RAM |
| FMC SDRAM | 可扩 | — | 否 | DEC-28"待核验"路径——**按需才需要**（见 §4-③） |

nucleo_h743zi 板 dts：ETH MAC+RMII PHY **status okay**（板上 RJ45）——网面可走以太网，替代 S3 的 WiFi（免 WiFi blob/省静态）。**arm-zephyr-eabi 工具链已装入 SDK 1.0.1**（本评估安装）。

## 3. 结论

**STM32H743 满足全部配置的内存需求，且无需外部 RAM**：
- 网面（以太网形态）实测 326KB/512KB（62%），比 S3 的 WiFi 形态（394KB/390KB≈满）**轻 68KB 且有 186KB 余量**；
- 全配置（含 DEC-27 目标 256KB WAMR 堆）= sram0 388KB（76%）+ D2 256KB 堆，**总内部占用 ~644KB / ~992KB（65%）**，余 DTCM 128KB + SRAM4 64KB 未动；
- FLASH：全配置镜像估 ≤500KB，DEC-23 双固件 slot（2×~500KB）+ ts 分区 84KB ≈ 1.1MB < 2MB ✓；
- 对比根因：S3 紧张 = 链接可用 DRAM 仅 390KB（512KB 扣保留）且无第二链接域；H743 = 512KB 全链 + 多域，**内部容量约为 S3 的 2.5 倍**。

## 4. H7 移植前置工作项（顺序=建议批次；非本次评估范围）

1. **WAMR 板级分派映射**（模块 CMakeLists 现对未映射板 FATAL——防静默错配的既定设计）：`nucleo_h743zi → THUMBV7EM? + invokeNative ARM 汇编验证`（WAMR 官方 ARM 路径；native C 版传参可靠性教训同板级二）。
2. **WAMR 堆摆放**：sram1+sram2 合并 linker region（256KB 连续）+ 堆缓冲 section 重定向（DEC-27 分层纪律：APP 沙箱独立域 = S3 PSRAM 的 H7 对应物）；或过渡期堆 128KB@sram1（降配运行）。
3. **ts-store flash 分区 overlay**（H7 2MB 布局：boot+双 fw slot+ts 五分区）+ esptool→STM32CubeProgrammer 烧录链。
4. **estop/PWM/ADC DT 绑定**（zephyr,user/aliases 模式平移）+ ETH 网面 glue（无 WiFi 重连面——更简单）。
5. 备选：FMC SDRAM 挂接（DEC-28 待核验）——**仅当未来 APP 并发/堆预算超出内部 992KB 时才需要**（V1 全配置不需要）。

## 5. 本次测量方法备注（可复现）

- S3 对照构建：`bash ~/project/logs/mem_probe_builds.sh`（netbench/psrambench 重建取 linker 值）。
- H7 构建：`bash ~/project/logs/h7_build.sh`（l3app @ nucleo_h743zi，`h7mem.conf` 覆盖：ETH_NATIVE_TAP=n / TS_APP_WAMR=n / TS_STORE_SLOT_SIZE=4096）。
- **测量工件两例（如实登记）**：① l3app 在真板直接构建会因 RAM slot 后端默认 **2×256KB** 溢出 318KB——native_sim 语义默认值不适合真板（各 bench 显式收紧的既有惯例再次确认；RAM 后端默认值是否该降 = 顺手登记不动手）；② 直启 bench（periphbench 型）未被 main 根引用的 APP 面会被 --gc-sections 回收——测足迹须用真跑 APP 的载体（psrambench/deploybench 型），periphbench 的 65KB/99KB 数字是"壳"值。
