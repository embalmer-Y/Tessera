# R12 · 板卡选择/硬件设计调研 · v0.1

> **本文件是什么**：DEC-68② 调研单元（owner：「Agent 应有应对新需求的能力，按需求进行板卡选择或硬件设计」——调研产出，不实施）。V0.13.0 R12 单元。
> **消费方**：未来「需求 → 选型」Agent 能力域（DomainPack 候选）+ BV1 画像扩展 + R13 结构件域前哨。

## 1. 输入盘点（平台已有资产 = 调研地基）

| 资产 | 对选型域的价值 |
|---|---|
| **BV1 板卡画像**（`agent/boards/*.toml`——LLD-A12 七节：serial/flash/boot/zenoh/caps/smoke/build） | 能力目录的**种子 schema**——每接入一块板即自然沉淀一条目录记录 |
| **memory_audit + memory-baseline**（LLD-A13/MP） | 选型判定的**硬门**：候选板的 RAM/PSRAM/FLASH ≥ 目标配置档最低需求（docs/memory-baseline.md 三档总账直接消费） |
| **caps 自报**（sys/get-info tiers/slot_pool_kb） | 运行时能力实测面（装机后校准目录记录——BV1 C5 已消费） |
| **twister 套件 + 工具链映射**（xtensa/host/riscv 经验） | 「该板能不能跑起来」的构建域事实（P4 判定批将补 RISC-V 实测） |
| **真机判据库**（AK/DB/NVD 判据行 + periph 责任链） | bring-up 成本画像（外设驱动自研史 = 工作量估计依据） |

## 2. 能力目录 schema v0（建议形态）

BV1 画像的**超集**——选型目录记录 = 画像 + 选型维度（向后兼容，`agent/boards/` 画像升版即入目录）：

```toml
[hardware]                          # 选型维度（新增节）
soc = "esp32s3"                     # SoC 族（工具链映射键）
ram_kb = 390                        # 内部 RAM（= memory-baseline DRAM 口径）
psram_kb = 8192                     # 外置 PSRAM（0 = 无）
flash_mb = 16
peripherals = ["wifi", "ble", "i2s", "i2c", "spi", "lcd", "sd", "audio_in"]
price_band = "c"                    # 价位带（a<b<c<d；采购决策输入）
availability = "market"             # market | constrained | eol
power_ma = 500                      # 典型功耗（供电设计输入）
form = "devkit"                     # devkit | som | custom
```

**原则**：目录记录的每字段都须有**机械可校验来源**（实测/数据手册页码）——无来源字段不入目录（R10 需求门控同纪律：目录可信度 = 生存前提）。

## 3. 需求 → 选型判定链（v0 设计）

```
用户需求（四节 spec 或大白话）
 → ① 资源需求抽取（复用 clarify 缺口分析——【资源】节 + 判据含的外设）
 → ② 能力目录匹配（peripherals ⊇ 需求 ∧ soc 工具链在册 ∧ availability ≠ eol）
 → ③ 内存可行性硬门（memory_audit：候选板 ram_kb/psram_kb ≥ 配置档最低
     〔memory-baseline 三档〕——最小可行配置上的静态账复算）
 → ④ 排序（价格带/功耗/bring-up 成本画像）→ 候选清单 + 理由
 → ⑤ 实测闭环（BV1 全链验证——目录记录回填 caps/串口/flash 真硅）
```

**定性（诚实）**：①-③ 是**确定性流水线**（BV1/LLD-A13 同族——机械判定，无 LLM）；④ 排序权重是策略面（owner 可配置）；⑤ 是 BV1 既有域。**LLM 只在需求抽取（①）的语义理解处出现**——与 clarify 域同型。

## 4. 硬件设计建议边界（DEC-68② 后半）

- **可交付（建议面）**：模块级选型建议（SoC/模组/外设型号 + 电源/接口预算）+ 与现有目录的外设驱动代价评估（自研史对照：es8311 域内自研六坑 → 「codec 类外设 = 高代价」标记）。
- **边界外**：原理图级/PCB 级设计——非确定性域（无机械判据门），且 owner 供应链/商务约束不可编码。若未来需要，走「LLM 建议 + 人工裁决」形态，本域只提供约束面（§3 判定链的反向使用：给定候选模块清单 → 接口/内存可行性核对）。
- **与 R13 的接缝**：选型产出（板卡外形/接口位置）= 结构件设计的输入（开孔/散热依据）。

## 5. 缺口与路线（登记不实施）

1. 目录记录 < 5 块板时判定链价值有限——**随接入增长**（atk/xiao 首两条，P4 RISC-V 板第三条）；
2. `[hardware]` 节 schema 定稿随首个消费者（选型域立项时门③）；
3. 内存可行性硬门依赖 memory-baseline **跨芯片行回填**（P4 判定批）——此前非 ESP32-S3 候选的判定 = 推定态（如实标注）；
4. 价格带/供货数据 = 人工维护面（无可靠机械来源，不入自动判定链）。
