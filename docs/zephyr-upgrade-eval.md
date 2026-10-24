# Zephyr 升级评估（v4.4.0 → 下一 stable）· 单元 J（门⑤呈递底稿）

> **日期**：2026-10-09 · **性质**：技术栈变更评估（流程门⑤——呈 owner 裁决，未裁不动）
> **结论先行**：v4.4.0 **就是当前最新 stable**（无"落后"）；升级的**唯一硬驱动 = ESP32-P4 目标板**（4.4.0 的 espressif HAL 无 esp32p4，P4 不可移植；支持随 v4.5 发布）。zenoh 三方 1.10.1 已是上游最新，升级不联动版本变更。建议 = v4.5 正式发布后即升（DEC-19 既定方向），P4 适配解耦为后续独立批。

## 1. 现状钉版链（2026-10-09 实测）

| 组件 | 钉版 | 上游最新 | 状态 |
|---|---|---|---|
| Zephyr | v4.4.0（2026-04-14 发布，EOL 2027-04-12） | v4.4.0 | **一致** |
| Zephyr SDK | 1.0.1 | 1.0.1 | 一致 |
| zenohd / eclipse-zenoh / zenoh-pico | 1.10.1（DR-22 三方同 minor） | 1.10.1（git ls-remote 实测） | **一致** |
| WAMR | 2.4.5 | 2.4.5（钉版纪律，怪癖家族 3 型在案） | 钉版 |

上游版本线（官方 releases 页）：**4.5 计划 2026-10（本月）**，release notes / migration guide 已出 working draft；**4.6 = 2027-04，LTS4**；5.0 = 2027-10 起。4.4.0 的 EOL（2027-04-12）恰与 4.6 发布月重合——"停在 4.4 直到 LTS4"窗口极窄。

## 2. 阻塞性论证（为什么会有这次评估）

**P4 目标板是唯一硬驱动**（DEC-28 目标集 = ESP32-S3 / ESP32-P4 / STM32H7 + native_sim）：

- v4.4.0 树内 espressif HAL 的 soc 列表 = esp32/c2/c3/c5/c6/h2/s2/s3——**无 esp32p4**；
- upstream main（2026-10-09 实测浅拉取）已有 `boards/espressif/esp32p4_function_ev_board` 与 **`esp32p4x_function_ev_board`（v3.x 硅变体）**——随 v4.5 发布；
- 排期表单元 J 含"批准后 P4 适配"，其前置即本次升级。

其余候选驱动全部**不成立**（升级不解决，如实排除）：

| 已知缺口 | main 现状 | 结论 |
|---|---|---|
| qemu 板 twister 元数据缺失（运行级测试不执行） | qemu_cortex_m3.yaml 与 4.4.0 **逐字节相同** | 升级不修——运行级测试继续走 native_sim/CI |
| DAV2（esp32 DVP 无 JPEG 变长帧，MD1.2h 保底 RGB565） | video_esp32_dvp.c 仅 1 处 include 改名 | 升级不修——demo 保底路径不变 |
| WAMR zephyr 平台怪癖家族（教训 12/28） | WAMR 侧问题 | 与 Zephyr 版本无直接关联 |

## 3. zenoh 联动结论

- zenoh-pico 上游最新 tag = **1.10.1**（`git ls-remote` 实测；早前 web 检索的"1.7.x 最新"为陈旧索引，勿采信）——三方链（DR-22）已在最新，**升级不触发 zenoh 版本变更**；
- Zenoh 2.0 仍处 roadmap 阶段（未发布）——计划 §4 的"共同 watch"项继续观察；
- 联动面收窄为一条：**zenoh-pico 1.10.1 在 4.5 新 Kconfig/构建面下的构建复验**（`include/zenoh-pico/config.h` 生成件重生成——dev-env §7 既有纪律）。

## 4. v4.5 迁移成本面（我们触碰面逐项；据官方 migration guide 4.5 草案）

| # | 变更 | 我们的面 | 风险/成本 |
|---|---|---|---|
| 1 | **Espressif 板级重构**：per-module dtsi（esp32_<module>.dtsi）与模块 Kconfig（如 SOC_ESP32S3_WROOM_N8）移除；flash reg/ranges 与 PSRAM size 须在板 DTS 声明 | xiao_esp32s3 = 树内板（上游自迁）；我们的板 overlay（ts 五分区 + zephyr,user 绑定）不动板 DTS 本体 | **中**——PSRAM 声明语义变化需真机实测（板级六 PSRAM 链复验）；native_sim 无涉 |
| 2 | CMake 最低 3.28 | 本机 4.4.3 | 零 |
| 3 | CONFIG_STD_C11/C99 移除 | 模块/测试用标准 C | 零 |
| 4 | 板目标命名清理（esp32_devkitc、esp32c6 等） | xiao_esp32s3 不在清单；但 db_build 等脚本用全限定名 `xiao_esp32s3/esp32s3/procpu` | 零（发布时复核一次） |
| 5 | native_sim TAP ethernet 转 DT 实例化 | **Agent deploy E2E（TAP zeth，TESSERA_E2E_DEPLOY）受影响** | **中**——迁移项：TAP 网络改 DT 声明 + e2e 复跑 |
| 6 | ADC（mec/xec 系）、PWM（stm32/nxp 系）驱动变更 | 未触碰这些 SoC；esp32 LEDC 驱动无涉 | 零 |
| 7 | 输入子系统 gpio-keys 属性改名 | 我们输入面 = ADC 轮询（G3），非 gpio-keys | 零 |
| 8 | MCUmgr / Twister / task_wdt / sysbuild 段（指南被截断未取全） | G2 SMP-UDP、twister 15 套件、DEC-48 task_wdt、MCUboot sysbuild | **未知→低**——升级批首日按指南原文逐段核对（清单项，非风险放大项：这些面上游以兼容为主） |
| 9 | SDK 最低版本 | SDK 1.0.1 | 发布时核对（4.5 若要求新 SDK = 一次性 apt/下载安装） |
| 10 | WAMR zephyr 平台层 | wamr_compat 垫片（__stdout_hook_install）+ version.cmake 竞争（教训：chmod 444） | 低——垫片条件编译面复核 + 怪癖家族撤实验（教训 12/28 既定动作） |

**预估升级批体量**：west 重钉 + 模块/测试适配 + 全量回归（twister 15 套件 ×2 + agent pytest + L5 + CI 四 job）+ 真机复验（inputdemo/linkdemo/deploybench 三 bench + PSRAM 链）≈ **1-2 会话**。P4 适配（bring-up/分区/通道/外设映射）为后续独立批（1-2 会话 + owner 提供 P4 实板终验）。

## 5. 选项与建议（呈 owner 裁决）

- **选项 A（建议）：v4.5 正式发布后即升**——符合 DEC-19（持续跟进最新 stable）既裁方向；月内可执行；P4 随之解锁，P4 适配批按 owner 板卡到位时间排期。代价 = 每半年一次 stable 追随成本（本节体量）。
- **选项 B：跳过 4.5，等 4.6 LTS4（2027-04）**——LTS 生命周期长、追随频率低；但 P4 冻结至 2027-04，且 4.4.0 EOL（2027-04-12）与 4.6 发布同月——衔接窗口零裕量（若 4.6 跳票即裸奔 EOL），风险实际更高。
- **选项 C：维持 4.4.0 不动**——违反 DEC-19 已裁纪律，P4 永久阻塞。不建议。

**附加裁决点**：P4 采购硅版本——Espressif 已发 P4 v3.x 硅刷新（Zephyr 侧 esp32p4x 板对应新硅、esp32p4 板目标 v1.3 旧硅）；owner 采购 P4 板时请报硅版本，适配批按此选板目标。

## 6. 证据与复验入口

- 版本线：docs.zephyrproject.org/releases（4.4.0=2026-04-14/EOL 2027-04-12；4.5=2026-10 计划；4.6=2027-04 LTS4）
- P4 缺位/在位：v4.4.0 `modules/hal/espressif/zephyr/soc/` 无 esp32p4；main `boards/espressif/esp32p4_function_ev_board` + `esp32p4x_function_ev_board`（浅拉取 ee3cfaf89a3 实测）
- qemu/DAV2 不修结论：`git diff v4.4.0 FETCH_HEAD` 相应文件（yaml 逐字节相同 / dvp 仅 include 改名）
- zenoh-pico 1.10.1 最新：`git ls-remote --tags origin | sort -V | tail`
- 迁移面：官方 migration-guide-4.5（working draft，2026-10-09 抓取）
