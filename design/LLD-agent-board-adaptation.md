# LLD-agent-board-adaptation · BV2 新板卡适配域 · v0.1（设计批·门③呈递）

> **本文件是什么**：新板卡适配域（BV2）设计——DEC-68①「Agent 需要为新板卡进行适配」的实现域；BV1（板卡验证域，LLD-agent-board-validation）从**验证**延伸到**适配（移植）**。owner 裁决③（DEC-73）：「这就需要 Agent 有适配新硬件的能力」。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.1 设计批（门③呈递——裁决后开工；HW 域（LLD-agent-hardware-targeting）只负责把用户引到 BV2 门口并建工单，本域承接）。

## 1. 域定性

DEC-33 原则面继承：**确定性流水线为骨、LLM 只在语义理解处**——

- 适配件生成 = 模板化产物（Zephyr 官方板定义 → Tessera 接入件的**机械变换**为主 + LLM 填语义缺口：分区布局取舍/内存初值推导）；
- bring-up 判据 = BV1 C1-C6 复用（零新判据面——验证域已真机实战）；
- 原理图协作路 = **人工确认闸**（原理图正确性无机械判据，如实登记——DEC-33「唯一人工环节如实登记」同型）。

与 HW 域边界：HW-1 分支 B 检测到「Zephyr 收录/未收录」后建 BV2 工单（`BV2_QUEUED`/`SCHEMATIC_REQUIRED` 结构化中止）；本域消费工单 → 适配流水线 → 画像入目录 → 用户重回 clarify 分支 A 绑定。

## 2. 路径一：Zephyr 收录板（接入件生成 + BV1 bring-up）

输入 = 板卡 hint（工单）+ Zephyr 工作区（west_workspace）。产出 = Tessera 接入件五件套 + 板卡画像。

### 2.1 接入件清单（board-p4 playbook 的模板化——P4 适配批沉淀的人工步骤逐项对应）

| # | 接入件 | 来源（机械度） | 说明 |
|---|---|---|---|
| 1 | 板定义定位 | 机械 | `zephyr/boards/<vendor>/<board>/board.yml` → DTS/Kconfig/CPUID |
| 2 | 五分区 overlay | 模板+取舍 | ts 分区 carve（app 槽×N + trust + prov 尾部）——LLM 按板 flash 尺寸从布局模板族选择，owner 确认 |
| 3 | 板级 conf | 模板+推导 | 内存初值（NET_RX_STACK/SYSWORKQ/SHELL 4096 族——R1/R2/R3 规则=memory_audit 机械复核）+ PSRAM 有无 + wifi 驱动代际（P4 教训：legacy ESP-HOSTED vs HOSTED_MCU） |
| 4 | WAMR 架构映射 | 机械表 | CPU → WAMR 目标 + invoke thunk 分派（R3 /64 教训：按目标处理器映射 AARCH64/X86_64/xtensa） |
| 5 | prov/TS_TEST 通道 | 机械 | TS_TEST prov 缺省 + flash_prov offset 口径（教训 39 offset 陷阱注记） |

### 2.2 bring-up 判据链（BV1 复用 + 两级）

1. **构建级**：C0（LLD-agent-board-validation v2 方向，本域解锁 build.enabled=true——接入件齐备后板级构建 rc=0 + memory_audit R0-R7 全过）；
2. **板级**：BV1 C1-C6 全 PASS（C2 flash 身份按接入件期望值对拍；C6 探针包 = D9 标准冒烟）。

PASS → 画像入目录（`agent/boards/<id>.toml`，[hardware] 事实节由接入件同步生成——HW-4 面即刻生效）→ 工单闭环。

## 3. 路径二：未收录板（原理图人机协作）

输入 = owner 原理图/引脚表（PDF/图片/文本）。

1. **移植清单生成**（LLM 语义理解主战场）：外设树盘点 / 引脚冲突检测 / 驱动缺口风险（Zephyr driver 支持矩阵对拍）/ 供电与调试口 / flash-RAM 画像草案；
2. **协作式 DTS**：Agent 出 overlay 草案 + 逐项出处标注（原理图页码/网络名）——**每项待 owner 确认**（人工确认闸；未确认项不进构建）；
3. 后续并入路径一（接入件生成 → BV1 bring-up）。

诚实边界：原理图正确性无机械判据——协作产物全部「待确认」态标注；BV1 C2 flash 身份 = 首个机械事实锚点（接线后实测）。

## 4. 工具面与规模

- MCP `board_adapt`（strict——写工作区 + 板级构建；spawn 长任务 + D2 progress）：输入 hint/工单 → 分阶段（接入件 → 构建 → 待烧录指引）；
- 烧录/bring-up 段消费既有 `board_validate`（BV1）——零新执行面；
- 测试：接入件生成矩阵（收录板 fixture × 布局模板族）/ memory_audit 复核接线 / 工单两端到端（BV2_QUEUED→画像入目录→clarify 分支 A 可绑）/ 原理图协作待确认态矩阵；
- 规模 ~1.5 单元（v1 只做收录板路全链 + 未收录板路的移植清单生成；协作 DTS 逐项确认 UI 随 W2 渠道演进）。

## 5. 门③呈递点（三决策）

1. **接入件产出形态**：建议 = 生成到 `agent/adapt/<board>/` 工作区（可 review 后人工并入 firmware/tests/）vs 直接写入固件树（建议前者——适配件是**产物**不是源码，入树前过人工 review）；
2. **C0 解锁范围**：build.enabled 仅对 BV2 流水线内临时解锁（画像副本）vs 全局解锁 C0（建议前者——C0 全局化随 V0.14.0 P4 判定批）；
3. **v1 范围裁剪**：收录板路全链 + 未收录板路清单生成（建议）vs 两路全做（协作 DTS 确认面较大，建议随 W2 后批）。
