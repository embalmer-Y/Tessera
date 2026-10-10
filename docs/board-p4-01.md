# board-p4-01 · P4 适配批：ESP32-P4-WIFI6-DEV-KIT 框架 bring-up

> **状态**：v1.0 · 2026-10-10 · P4 板级移植交付单元报告（DEC-50/DEC-28 目标集）。
> **DoD**：ESP32-P4-WIFI6-DEV-KIT（Waveshare）上 ts 框架最小面（core/safety/store/appmgr + WAMR）自举运行；prov/APP/meta flash 持久化跨复位；判据 = p4bench 全链 PASS。**判定：达成。**
> 关联：DEC-28（板卡策略：P4 在目标集）、DEC-50（v4.5.0-rc1 + P4 载板定版）、DEC-49②（TSAP v2 容器）、教训 30（v4.5 分区兼容串）。

## 1. 板与目标

| 项 | 值 | 出处 |
|---|---|---|
| 载板 | ESP32-P4-WIFI6-DEV-KIT（Waveshare） | owner 裁决（DEC-50） |
| 芯片 | ESP32-P4 v3.1（eco6 ROM），HP 双核 RV32 @ 400MHz + LP 核 | esptool 实测 |
| flash / PSRAM | GD 16MB / 32MB（PSRAM 挂接待后续批） | bootloader 实测 |
| Zephyr 板目标 | `esp32p4_wifi6_dev_kit/esp32p4/hpcore`（v4.5 斜杠限定语法；hpcore/lpcore 双变体） | 树内 waveshare 板 |
| WAMR target | `RISCV32`（module CMakeLists 板映射表显式登记；解释器-only 下仅 ABI 元数据，AOT=0 无 invokeNative 面） | DEC-25 |
| 烧录/控制台 | CH343 桥 COM/UART Type-C 口 = /dev/ttyACM0（esptool 下载模式实测即 UART0）；console 经 overlay 重指 uart0（板默认 = 原生 USB-Serial-JTAG，需另接 USB 口） | 本批实测 |
| 工具链 | Zephyr SDK 1.0.1 `riscv64-zephyr-elf`（setup.sh -t 单组件补装） | 本批补装 |

无线面（C6 伴芯 esp-hosted）**不在本批**——P4 无线 = 后续联网批。

## 2. 分区布局（p4bench overlay）

4.5 默认 16M 布局（`partitions_0x2000_default_16M.dtsi`）原样保留（boot/sys/slot0/lpcore×2/storage/coredump，esptool 偏移零变化）；slot1（0x7e0000..0xfa0000，7936KB）删除并以 ts 五分区 + fw-b 预留替代（persistbench 同语义）：

| 分区 | 偏移 | 尺寸 | 说明 |
|---|---|---|---|
| ts_prov_part | 0x7e0000 | 4KB | provisioning |
| ts_meta_part | 0x7e1000 | 8KB | meta 双副本（步距 4KB） |
| ts_slot_a_part | 0x7e3000 | 32KB | = CONFIG_TS_STORE_SLOT_SIZE |
| ts_slot_b_part | 0x7eb000 | 32KB | |
| ts_noinit_part | 0x7f3000 | 4KB | 复位留痕 |
| fw_b_part | 0x7f4000 | 736KB | MCUmgr 第二 slot 预留（V1 未接线） |

五分区全部带 `compatible = "zephyr,mapped-partition"`（v4.5 `PARTITION_ID` 宏要求，教训 30）。

## 3. 板级差异定值（p4bench 板 conf）

- `CONFIG_MAIN_STACK_SIZE=8192`：RV32 调用帧比 Xtensa 深，4096 在安装链（meta 读 → slot 擦写）实测溢出（sp 越栈底 0x230 → Illegal instruction @ 数据表）；8192 实测定值。
- `CONFIG_TS_STORE_SLOT_SIZE=32768` / `CONFIG_TS_APP_THREAD_STACK=16384`：与 S3 persistbench 同过渡值（PSRAM 挂接前）。

## 4. 本批修复的存量缺陷（升级批遗漏补全）

1. **六 bench overlay 缺 mapped-partition 兼容串**（avdemo/dsdbench/linkdemo/metabench/persistbench/wdtbench，各 5 节点）：升级批只改了三 bench；`PARTITION_ID()` 引用面在 4.5 下重构建即挂。本批机械补齐（30 行）。
2. **persistbench 自构造 TSAP 包为 v1 格式**（`build_tsap` 手写头 fmt_ver=1/flags=0/无 digest/COSE 空壳）：DEC-49② v2 固件 fail-closed 拒收 v1——persistbench 自 DEC-49② 落地起即坏（真机 bench 不在 CI 构建面，静默漏网）。本批换 `gen_p4b_pkg.py` 机械生成的 v2 包（测试根签名），p4bench 同源复用；v1 构造器删除。

## 5. 真机判据（p4bench，2026-10-10 实测单迹）

```
P4B0 persistbench
P4B1 first boot: prov absent (rc=-8) -> provision session
P4B1 prov burned: node=pb-dev cube=cube-pb
P4B2 app staged: slot=1 total=928 hw=928 -> warm reset   ← TSAP v2 包（com.tessera.p4b）
P4B3 boot: prov from flash node=pb-dev                    ← 复位后全状态出自 flash
P4B4 boot done -> link up (glue, no-host bench)
P4B5 app active: id=com.tessera.p4b ver=0.1.0 slot=1     ← WAMR 在 RV32 上装载运行
P4B5 diag: init_res=-4 (SAFE_POWERON 写拒绝 = 冷启动预期，合同 2/3 生效)
P4B5 app_evt(1) -> gpio=1 ... P4B5 app_evt(0) -> gpio=0  ← wasm→native→safety→通道 全链
P4B PASS prov+meta+slot persisted across reset
P4B alive t=6013 ...                                      ← 存活循环
```

验证口径：`esptool erase_region 0x7e0000 0x7c000`（回干净首启）→ RTS 复位 → 串口抓全程（`~/project/logs/p4_firstboot.py`，串口重开竞速窗口见教训 31）。

## 6. 回归与 CI

- twister native_sim **15/15（77 用例）**全绿（`--extra-args=ZEPHYR_EXTRA_MODULES=...` 标准口径）。
- pytest 仓库检查 2/2。
- persistbench S3 @ v4.5.0-rc1 构建绿（本批 §4 修复的构建级验证；S3 真机复验待板换线后顺带）。
- CI 无变化（native 面；P4 交叉构建与 S3 同口径留本地——runner 不装 SDK，成本决策既有）。

## 7. 遗留与后续

- P4 无线面（C6 伴芯 esp-hosted over HCI）= 联网批（依赖 ts-net 板级映射）。
- PSRAM 32MB 挂接（WAMR 堆迁 PSRAM，DEC-27 分层）= 内存预算批。
- P4 ADC/PWM/真外设绑定 = 外设批（Waveshare 引脚图确认后）。
- D-AV 帧证据（摄像头排线）独立于此批，待 owner 硬件动作。
