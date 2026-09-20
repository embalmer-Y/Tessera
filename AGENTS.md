# AGENTS.md · Tessera 会话入口

> **本文件是什么**：每个开发会话（ZCode）的第一入口。由 K1 依据 `FOUNDING_PROMPT.md` v1.0（2026-09-18）改写生成。
> **权威顺序**：owner 最新裁决（`decisions.md` 中的 DEC）> `FOUNDING_PROMPT.md` > 本文件摘要。若本文件与上述冲突，以裁决/原文为准，并登记 Q 修正本文件。
> **维护规则**："当前状态"节每会话结束前更新；本文件的修改权在主会话。

## 1. 当前状态

- **2026-09-20（二） · design review-01 完成（17 项全处置）+ 设计深化批次交付，待 owner review；新增 Q-11、Q-10 增至 15 组**
  - 交付物：`design/design-review-01.md`（逐条审查报告）；缺陷修复批次（TS_FAIL_*/ts_ctx_t/ts_periph_kind_t/keyspace hb 补全/estop DT 绑定/断链恢复语义/审计消费策略）；深化批次（**HLD v0.2**：ts-store 模块行、§4.5 关键场景时序、§4.6 内存预算、sys 命令面、输入采集、V1 裁剪清单；**新增 LLD-ts-store**；LLD-ts-hal §5 input monitor；LLD-ts-appmgr mailbox/停止语义；LLD-ts-net sys 命令表）。
  - 登记增量：**Q-11**（语义批次 6 项）、Q-10 表 #14/#15、names.md（ts-store/TS_FAIL_*/ts_ctx_t/DR 族）。
  - 待办：① Q-03…Q-12 裁决 + HLD v0.2/LLD v0.2 确认 + 规范套件批准（tag `std-v1`）；② M0（west + native_sim + CI，依赖 Q-03/Q-10/Q-12；含 LICENSE 补齐与宿主环境验证）。
  - 禁区：HLD/LLD 确认与 Q 批次裁决前不进 impl。
- **2026-09-20 · LLD 批次（1+7 份）已交付，待 owner review；新增待裁 Q-10**
  - 交付物：`design/LLD-00-common.md`（错误码/线程模型/目录约定）+ 七模块 LLD（ts-core/ts-safety/ts-hal/ts-appmgr/ts-net/ts-power/ts-periph，各含 API 规格/状态机/并发/Kconfig/测试要点/未决依赖）；**Q-10**（LLD 默认值清单 13 组，`decisions.md`）。
  - 处置说明：owner 指令"编写 LLD"视为 design 阶段继续授权；HLD v0.1 与 Q-03…Q-09 **仍未逐条确认**——LLD 内一切未决项以〔Q-xx 提案〕标注，未落定（军规 2）。
  - 待办：① Q-03…Q-10 裁决 + HLD/LLD 确认 + 规范套件批准（tag `std-v1`）；② M0（west 工作区 + native_sim 空模块 + CI 骨架，依赖 Q-03/Q-10）。
  - 禁区：HLD/LLD 确认与 Q 批次裁决前不进 impl（流程 §2.4-②/③）。
- **2026-09-19 · K1 review 经 owner 推进指令视为通过；research v0.2 + HLD v0.1 + 规范套件 v0.1 已交付，全部待 owner review**
  - K1 门处置：owner 指令"深入 research → design → 规范文档"（2026-09-19）视为 K1 review 通过与阶段推进授权；如有误请 owner 纠正，本行即改。
  - 交付物：① research v0.2（R1/R2 增补 §5/§6 二次核验：WAMR 2.4.5/体积/集成、zenoh-pico 1.9/传输/TLS/足迹）；② `design/HLD-firmware-framework.md` v0.1（架构分层 + ts-* 七模块 + 合同逐条映射 + 里程碑 M1…M3）；③ `docs/std/`（README/testing/versioning/progress/coding）；④ 待裁批次 **Q-03…Q-09**（`decisions.md`）。
  - 待办：① Q-03…Q-09 裁决 + HLD 确认 + 规范套件批准（tag `std-v1`）；② M0（west 工作区 + native_sim 空模块 + CI 骨架，依赖 Q-03）；③ M1…M3 按 HLD 实施。
  - 禁区：HLD 确认与 Q 批次裁决前不进 impl（流程 §2.4-②/③）；规范套件 v0.1 未生效前按本文件既有规则执行。

## 2. 会话 bootstrap（每次会话固定执行）

1. 读本文件，重点是"当前状态"节；
2. 读 `decisions.md`，确认未裁 Q；
3. 读当前阶段文档（`docs/research/` 或 `design/`）；
4. 长会话上下文被压缩后，一律以文件现状为准续写，不以记忆续写。

## 3. 项目一句话（详见 FOUNDING_PROMPT §0）

**Tessera**：立方体智能 I/O 模块——基于 Zephyr RTOS 的模块化末端输入输出系统。业务逻辑以**可安装、可迁移的 APP** 形态运行（类安卓：APP 与板卡硬件解耦）；输入输出外设**可插拔**；多个立方体可经扩展面**并联为一个逻辑节点**；物理输出具备**安全限制**；配套 **MCP 形态 AI Agent** 完成"需求分析 → 软件设计 → 编程开发 → 模拟测试 → 部署"的完整编程链路。本项目完全由 AI（ZCode）开发，owner 负责裁决与 review。

## 4. 开发流程（摘要；全文见 FOUNDING_PROMPT §2）

- **主线**：research → owner 裁决 → design（规格）→ owner 确认 → impl（实现+测试）→ 阶段退出 review → 下一阶段。
- **阶段产出白名单**：research 只出 `docs/research/*.md` 与 Q 登记；design 只出 `design/` 规格与修订记录；impl 只出规格清单内代码 + 同批测试。**越权产出 = 立即撤回并留痕**。
- **单会话预算**：一个会话交付一个可验证交付单元；超出部分登记待办另起会话。
- **review 门**（必须停下等 owner，不得自裁）：① 一切选型与默认值（先登记 Q）；② 阶段退出（对照 DoD）；③ 公共 API / 文件格式 / 网络协议 / 权限模型变更；④ 安全合同任何改动；⑤ 技术栈变更（须证明阻塞性，附备选对比与迁移成本）。
- **呈递格式（强制，不自包含直接重写）**：背景（现状 + 为何是问题）→ 选项 → 建议 → 影响。
- **决策登记**：`decisions.md`；生命周期 Q-xx → owner 回复 → DEC-xx（附日期与原文）；编号不复用，REJECTED 留档。
- **默认值三问**（写任何常量前自答）：从哪来（Q/推导）？越界会怎样？改动破坏什么？

## 5. 工程纪律（军规十条，违反即流程缺陷）

1. **流程至上**：阶段白名单不越、review 门不闯。
2. **无 Q 不落盘**：未裁决的默认值/选型不得写成"已决定"，不得进代码常量。
3. **文字纪律**：只记录必要内容；必要内容必须**自包含**（现状 + 动因 + 后果三要素齐全），不带会话上下文也能读懂。
4. **编码纪律**：全库文本 UTF-8 无 BOM；批量文本操作显式指定编码；禁用依赖系统代码页的工具。
5. **git 纪律**：每交付单元一提交 + 会话结束兜底提交；里程碑与重大裁决打 tag；失败与回退留痕，禁改写历史。
6. **命名纪律**：跨文档标识符（DEC/Q/M/REQ/模块名/板名）登记于 `docs/names.md`；新造先查碰撞；禁裸单字母作跨文档标识符。
7. **测试同批**：实现与测试同一交付；失败如实报告，禁美化、禁把失败改写为"选择不行动"。
8. **结论落盘**：聊天与记忆不是项目状态；会话结束前把持久结论写入文档/登记册。
9. **顺手重构禁止**：任务外的发现登记不动手，不混入本批交付。
10. **交付即验证**：DoD 对照 + 构建/测试全绿 + lint 通过，才算完成；有缺口如实列出。

## 6. 安全与确定性合同（硬约束；HLD 可细化，不得削弱）

1. **三安全态**：每个输出通道（含受控供电）显式声明上电态 / 断链态 / 故障态；无声明不予注册。
2. **写入路径唯一**：一切输出必经保护层校验（限幅 / slew-rate / 限流）后才落驱动；绕过保护层的写入 = 缺陷（须可机械检查）。
3. **断链 fail-safe**：宿主/网络失联 → 输出进安全态；输入流不因保护而中断。
4. **看门狗**：超时 → 全输出安全态；每子系统独立喂狗（可定位卡死来源）。
5. **estop 硬件通道**：急停 ISR 直达安全态，**不经协议栈、不经调度排队**；响应时间上界可测；事后补发事件。
6. **初始化顺序固定**：任一步失败 → 全系统 fail-safe，不得半启动。
7. **受控供电**（DEC-03）纳入 1–6 同一合同（它是特殊形式的输出）。
8. **并联安全归属**（DEC-02 遗留题）：estop 与保护必须能在**本地立方体**独立生效，不依赖逻辑节点内部通信——这是逻辑节点拓扑设计的硬约束。
9. **确定性**：同一输入序列必得同一输出序列（重放测试机械验证）；禁依赖未播种随机、墙钟、容器迭代序。
10. **固件核心不学习**：安全参数、权限模型、输出限值不经运行时自适应修改；APP 权限清单是硬边界，越权访问一律拒绝并留痕。

## 7. 仓库地图

```text
AGENTS.md           本文件（会话入口）
FOUNDING_PROMPT.md  创始 prompt 原文（K1 起始输入，存档不删）
decisions.md        DEC/Q 登记册
docs/research/      调研文档（R1/R2 产出于此）
docs/names.md       命名空间登记表
docs/std/           开发规范套件（testing/versioning/progress/coding；v0.1 待 owner review，批准后 tag std-v1 生效）
design/             规格文档（HLD + LLD-00 + 七模块 LLD；均为 v0.1 草案待 owner 确认）
firmware/           Zephyr 工程（app/ module/ tests/；west 工作区在仓库之外初始化，Zephyr 树不进本仓库；M0 启动）
agent/              MCP server + 模拟器 + 构建工具链（PC 侧；DEC-15 第二阶段）
hardware/           立方体结构 / 连接器 / 电源资料（DEC-15 第三阶段启动）
legacy/             （可选）历史参考资料，NON-NORMATIVE；源自 Galatea 仓库 tag `physio-handoff`
```

## 8. 子代理纪律

委派子代理时提示词自包含；`AGENTS.md` / `decisions.md` / `design/` 的修改权只在主会话。

## 9. 会话结束检查单

- [ ] 交付单元已提交（git log 可溯）
- [ ] 持久结论已落盘（文档/登记册，而非聊天记录）
- [ ] `docs/names.md` 已登记本会话新标识符
- [ ] 本文件"当前状态"节已更新
- [ ] 如触发 review 门：已停在门内并按呈递格式（背景→选项→建议→影响）呈报 owner
