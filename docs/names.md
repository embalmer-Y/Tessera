# docs/names.md · Tessera 命名空间登记表

> 军规 6：跨文档标识符（DEC/Q/M/REQ/模块名/板名）登记于此；**新造先查碰撞**；禁裸单字母作跨文档标识符。
> 登记格式：标识符 | 含义 | 首次出现 | 状态。

## 1. 决策与问题编号

| 标识符 | 含义 | 首次出现 | 状态 |
|---|---|---|---|
| DEC-01 … DEC-16 | 已裁定决策（owner 2026-09-18 裁定） | FOUNDING_PROMPT §1 | 生效 |
| DEC-17 | APP 运行时 = WASM，实现采用 WAMR | decisions.md（Q-01 裁定） | 生效 |
| DEC-18 | 数据面协议 = zenoh（Zephyr 侧 zenoh-pico） | decisions.md（Q-02 裁定） | 生效 |
| DEC-19 … DEC-24 | 裁决批次 1（2026-09-20：Zephyr 4.4+持续跟进 / client+ARM64 宿主 / TSAP 包格式 / 断链参数延长且 prov 可配 / 双 slot+MCUmgr / GitHub CI） | decisions.md | 生效 |
| DEC-25 … DEC-26 | 裁决批次 2（2026-09-21：fast 解释器+WASI 关+AOT 保留 / 逻辑节点仅预留） | decisions.md | 生效 |
| DEC-27 … DEC-29 | 裁决批次 3（2026-09-21：Q-10 全项+WAMR 堆每板动态配置 / 板卡策略转向高性能并移出 RP2350 / 内存预算每板动态计算） | decisions.md | 生效 |
| DEC-30 | 裁决批次 4（2026-09-21：Q-11①-⑤ 按建议——sys 命令面 host-only / 共享写后写胜出+审计 / APP 状态不持久化 / 审计内存环形 / prov CBOR 只读）。**至此 Q-01…Q-12 全部裁毕** | decisions.md | 生效 |
| DEC-31 | Q-13 裁定（APP 线程模型：禁自建线程/编译期禁用/三层机制）+ C-1/C-2/C-3 确认与 M0 开工授权载体 | decisions.md | 生效 |
| DEC-32 | Agent 仅 Linux（修订 DEC-20）+ 开发环境迁 WSL2 + Windows 环境复原 | decisions.md | 生效 |
| DEC-33 | Agent 基座 = pi（进程内库内核）+ 官方 MCP TS SDK 门面 + 自研工具集（TypeScript）；多域 Agent 预留 + 北极星"自己生产自己"（机器人/Galatea） | decisions.md（Q-14 裁定） | 生效 |
| DEC-34 | MCP 工具面 = 双层（原子必开 + 高层任务 V1 先 2-3 个；长任务 Tasks 句柄化；工具面增删 = review 门） | decisions.md（Q-15 裁定） | 生效 |
| DEC-35 | ACP 二级人机接口：V1 不做，仅架构预留（编排层/传输解耦） | decisions.md（Q-16 裁定） | 生效 |
| DEC-36 | Agent 交互栈定案：MCP 唯一对外（stateless-first 纪律）+ 长任务自定义句柄轮询 + Agent Skills 分发 + 多域编排默认；**A2A v1.0 预留**（owner 要求显式记录） | decisions.md（Q-17 裁定） | 生效 |
| Q-01 | APP 运行时选型（→ R1） | FOUNDING_PROMPT §9 | 已裁 → DEC-17 |
| Q-02 | 数据面应用层协议选型（→ R2） | FOUNDING_PROMPT §9 | 已裁 → DEC-18 |
| Q-06、Q-07 | WAMR 执行模式 / 逻辑节点 V1 范围 | HLD v0.1 / decisions.md §二 | 已裁 → DEC-25/26 |
| Q-10 | LLD 批次默认值清单（15 组） | LLD v0.1 批次（design/） | 已裁 → DEC-27 |
| Q-11 | design review-01 语义批次 | design-review-01.md | 已裁 → DEC-29/30 |
| Q-12 | CI 平台与远端仓库托管（M0 前置） | 开发就绪度评估（2026-09-20） | 已裁 → DEC-24 |
| Q-13 | APP 线程模型与并发限制（禁自建线程/编译期禁用/三层机制） | owner 问询（2026-09-21） | 已裁 → DEC-31 |
| Q-14 | Agent 基座选型（A：pi 库内核 / B：OpenCode / C：goose / D：PydanticAI 自建） | R3（owner 指令 2026-09-22） | 已裁 → DEC-33 |
| Q-15 | MCP 工具面形态（原子层 / 高层任务层 / 双层） | R3 | 已裁 → DEC-34 |
| Q-16 | ACP 二级人机接口 V1 范围（详解已补呈：作用 + 实现方式） | R3 | 已裁 → DEC-35 |
| Q-17 | Agent 交互栈确认（①MCP 维持+实现纪律 ②长任务机制细化 ③Skills 分发 ④A2A 预留） | R4（owner 质疑触发，2026-09-22） | 已裁 → DEC-36 |
| Q-18 | Agent 实现语言（A：TS 维持 / B：Python 宿主+pi RPC / C：Python 自研 / D：Rust） | owner 问询（2026-09-22） | 待裁 |

## 2. 任务与里程碑

| 标识符 | 含义 | 首次出现 | 状态 |
|---|---|---|---|
| K1 | 仓库初始化（骨架 + git + AGENTS.md + decisions.md 录入） | FOUNDING_PROMPT §7 | 2026-09-19 完成，待 review |
| R1 | APP 运行时调研（wasm3/WAMR vs LLEXT vs 脚本类等） | FOUNDING_PROMPT §7 | 进行中（初步笔记已落盘） |
| R2 | 数据面协议选型调研 | FOUNDING_PROMPT §7 | 进行中（初步笔记已落盘） |
| R3 | Agent 基座选型调研（coding agent / 框架 / MCP 封装） | owner 指令（2026-09-22） | v1.0 落盘，随 Q-14/Q-15/Q-16 呈递待裁 |
| R4 | Agent 交互与接入方式调研（协议/实践/趋势） | owner 指令（2026-09-22，质疑 MCP 选型触发） | v1.0 落盘，随 Q-16 重呈 + Q-17 新登记待裁 |
| M0 | west 工作区 + native_sim 空模块构建 + CI 骨架 | FOUNDING_PROMPT §7 | **本地全绿（2026-09-21，WSL：构建+twister 运行级+pytest）**；仅余 GitHub 远端推送（CI 上线） |
| M1 | ts-core + ts-safety（安全层最小闭环） | HLD §7 | 待启动（规格已生效） |
| M2 | ts-hal + ts-appmgr + WAMR 集成（拆 M2a：store/TSAP/slot；M2b：hal/权限/WAMR） | HLD §7 | 待启动（规格已生效） |
| M3 | ts-net + ts-power + 集成与重放测试（拆 M3a：net；M3b：power/periph/集成） | HLD §7 | 待启动（规格已生效） |
| kickoff | K1 首次提交的 git tag | FOUNDING_PROMPT §9 | 已打 |
| dec-wamr-zenoh | DEC-17/18 裁定登记提交的 git tag（重大裁决留痕，军规 5） | decisions.md 修订记录 | 已打 |
| dec-19-24 | 裁决批次 1（DEC-19…24）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| dec-25-26 | 裁决批次 2（DEC-25/26）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| dec-27-29 | 裁决批次 3（DEC-27…29）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| dec-30 | 裁决批次 4（DEC-30，Q 链全部裁毕）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| std-v1 | 规范套件批准生效的 git tag（C-3，2026-09-21） | decisions.md 修订记录 | 已打 |
| DR-xx | design review 发现编号族（当前 DR-01…17，全部处置） | design/design-review-01.md | 存档 |
| SC-xx | 最终自检发现编号族（当前 SC-01…04，全部处置） | design/final-selfcheck.md | 存档 |

## 3. 板名（DEC-14 目标板集；**DEC-28 修订**：RP2350 移出，策略转向高性能高配置）

| 标识符 | 含义 | 网络能力备注 |
|---|---|---|
| ESP32-S3 | Espressif 目标板 | 原生 WiFi；PSRAM 2–8MB（Zephyr 官方支持） |
| ESP32-P4 | Espressif 目标板 | 无无线电，需配 ESP32-C6 或用以太网；PSRAM 待核验 |
| STM32H7 | ST 目标板 | 有 EMAC，需外挂 PHY；FMC SDRAM 待核验 |
| RP2350 | （原目标板，**DEC-28 移出**：Zephyr 无 PSRAM 驱动 + 520KB SRAM，不符高性能取向） | 存档 |
| native_sim | Zephyr 仿真平台 | CI 平台 |

## 4. 项目与外部名称

| 标识符 | 含义 | 状态 |
|---|---|---|
| Tessera | 本项目工作名（拉丁语"马赛克镶嵌片"）；owner 一句话可全局替换，替换时同步 FOUNDING_PROMPT §0 与全部出现处 | 生效 |
| Galatea | 旧母项目（本固件子项目的剥离来源；仓库 `D:\Software\project\Galatea`）；与本项目当前无开发耦合，但为 **DEC-33 北极星的未来应用目标**之一（完全自动化"自己生产自己"） | 未来应用目标（DEC-33） |
| physio-handoff | Galatea 仓库 git tag，存旧子项目历史资料（NON-NORMATIVE，事实可复用、结论不复用） | 仅历史引用 |
| WAMR | WebAssembly Micro Runtime（Intel 主导，Apache-2.0，官方 Zephyr 移植）；DEC-17 选定的 APP 运行时实现 | 生效（选型） |
| zenoh / zenoh-pico | zenoh 协议及其嵌入式实现 zenoh-pico（Apache-2.0，官方 Zephyr 模块）；DEC-18 选定的数据面协议 | 生效（选型） |
| router 宿主平台 | zenohd router 部署面：**Linux PC**、ARM64 Linux 工业/机器人主板（DEC-20；DEC-32 修订：Windows 移出） | 生效 |
| LLEXT | Zephyr 在树可加载 ELF 子系统（实验性）；R1 候选 B，未被选用；如未来作框架内部机制须另立 Q | 存档（未选用） |
| wasm3 | WASM 解释器（MIT，最低维护期）；R1 候选 A1，未被选用 | 存档（未选用） |
| OpenCode | 开源 coding agent（anomalyco/opencode，原 sst/opencode；MIT；v1.18.x）；R3 候选 B | R3 呈递（待裁） |
| pi | AI agent 工具箱（earendil-works/pi，原 badlogic/pi-mono；MIT；v0.87.x；库嵌入一等）；R3 候选 A（**建议**） | R3 呈递（待裁） |
| goose | Block 开源 agent（block/goose，Apache-2.0，Rust，扩展体系=MCP server）；R3 候选 C | R3 呈递（待裁） |
| Codex CLI | OpenAI 开源 coding agent（Apache-2.0，app-server 形态）；R3 备查 | 存档（未选用，R3） |
| Claude Agent SDK / Gemini CLI / Crush / Aider / Amazon Q CLI | R3 出局组（闭源运行时+模型锁定 / 锁 Google / FSL 许可证 / 停更+非 agent 架构 / 已归档） | 存档（R3 排除） |
| Vercel AI SDK / PydanticAI / FastMCP | R3 自建循环框架线（方案 D 相关底座）；**Q-18 修订后 PydanticAI + FastMCP 为推荐基座（选项 C）** | Q-18 候选 C（待裁） |
| OpenHands | Python 全栈自主 agent 平台（web 形态，非嵌入库）——Q-18 Python 版图排查结论：非内核候选 | 存档（不选用） |
| ACP | Agent Client Protocol（**Zed/JetBrains** 共治，v1 stable / v2 draft；编辑器↔agent 标准协议，客户端 80+）。**命名陷阱**：与 IBM 的同名 Agent Communication Protocol（agent↔agent，2025-08 已并入 A2A）不同物 | 生效（DEC-35：V1 不做，架构预留） |
| A2A | Agent2Agent 协议（Google→Linux Foundation，v1.0.1；2026-08-17 入 AAIF；Azure/AWS/GCloud 产品级采用）；agent 对等协作，与 MCP 互补。**预留记录（owner 要求，DEC-36④）**：跨主体/长周期对等场景（如 Galatea 规模）启用；Agent HLD 须落架构预留节（agent 身份/Agent Card/对等任务委托接入缝） | 生效（DEC-36 预留） |
| AAIF | Agentic AI Foundation（Linux Foundation，2025-12-09 成立；MCP/AGENTS.md/A2A 治理伞 = "open agentic stack"） | R4 事实 |
| Agent Skills（SKILL.md） | 领域能力包开放标准（agentskills.io，Anthropic 2025-12-18 开放；45+ 工具支持，**pi 内核原生支持**） | 生效（DEC-36③：V1 附最小固件域 skill 集） |
| MCP Registry | 官方 MCP server 注册表（registry.modelcontextprotocol.io，2025-09 起 preview） | 分发通道（上线时占名，工程事项） |
| AGENTS.md | 仓库级 agent 指令标准（OpenAI 捐 AAIF；20+ 工具读取；本仓库现行实践） | 生效（维持） |
| Zephyr MCP 子系统 | Zephyr 树内 MCP server 库（`subsys/net/lib/mcp`，仅 latest 文档存在、v4.4.0/4.5.0 不可用） | 升级观察项（随 DEC-19 跟进策略） |
| ESP-IDF Tools MCP | Espressif 官方 `idf.py ai-cli --mcp`（v6.0，2026-04，五大客户端实测）+ 文档 MCP server——Tessera 架构同构先例 | R4 引证 |
| IoT-SkillsBench | 嵌入式 agent 真机基准（arXiv 2603.19583；专家 skills 使跨平台成功率接近满分） | R4 引证 |
| Quilter Project Speedrun | AI 设计主板制造闭环先例（2026：AI 布局→10 套全部点亮；**固件 bring-up 全人工** = Tessera 生态位佐证） | R4 引证 |
| WebMCP / AG-UI / agentgateway / MCP Apps | R4 判定：WebMCP（网页向 agent 暴露，无关）/ AG-UI（前端事件流，非必需）/ agentgateway（AAIF 流量网关，watch）/ MCP Apps（对话内 UI，后置可选） | 存档 / watch |
| MCP Tasks extension | MCP 长任务扩展（2026-07-28 spec 转正：任务句柄+轮询+订阅通知）；Agent 长工具设计基线 | R3 设计输入 |

## 5. 模块名 / API 名 / 文件格式名

（固件框架模块名 = HLD v0.1 提案态，待 owner 确认后转"生效"；跨文档引用时标注提案态。）

| 标识符 | 含义 | 状态 |
|---|---|---|
| ts-core | 框架核心：初始化编排/事件总线/单调时间/喂狗注册表 | HLD 提案 |
| ts-safety | 安全层：输出保护/三安全态/estop/fail-safe/WDT 框架 | HLD 提案 |
| ts-hal | 统一外设 HAL（权限执行点） | HLD 提案 |
| ts-appmgr | APP 生命周期管理 + WAMR 宿主 | HLD 提案 |
| ts-net | zenoh-pico 数据面封装（命名空间/命令-回执/心跳监视） | HLD 提案 |
| ts-power | 受控供电（DEC-03，经 ts-safety） | HLD 提案 |
| ts-periph | 外设描述与插拔管理（V1 桩） | HLD 提案 |
| ts_time_ms | 单调时间服务 API（合同 9 唯一时间源） | HLD 提案 |
| ts_safety_commit | 唯一写路径出口 API（合同 2） | HLD 提案 |
| ts_res_t / TS_E_* | 框架错误码类型与错误码族（LLD-00 §2） | LLD 提案 |
| TS_EVT_* | 事件总线事件 ID 族（LLD-ts-core §4） | LLD 提案 |
| CONFIG_TS_* | 框架 Kconfig 前缀（LLD-00 §5） | LLD 提案 |
| TSAP | APP 包容器 magic（"TSAP" u32；格式随 Q-05 定稿） | LLD 提案 |
| ts_api_v1 / ts_perm_v1 | 版本化 APP 导入面 / 能力文法（破坏性变更须升 v2，门③） | LLD 提案 |
| ts-store | 存储抽象模块：分区/meta 掉电安全 kv/prov 只读/noinit（DR-01） | HLD v0.2 / LLD 提案 |
| TS_FAIL_* | 故障原因码族（u32：TS_FAIL_SRC_<<16｜细因，LLD-00 §2.1） | LLD 提案 |
| ts_ctx_t | APP 调用者不透明上下文（防伪造映射，LLD-00 §3.1） | LLD 提案 |
| ts_periph_kind_t | 外设描述符类别枚举（含 TS_PK_ADC，DR-13） | LLD 提案 |

## 修订记录

- 2026-09-19 · K1 建立：登记 DEC/Q 编号、任务号、板名、项目名。
- 2026-09-19 · Q-01/Q-02 裁定登记：新增 DEC-17/18、git tag `dec-wamr-zenoh`、外部选型名（WAMR、zenoh/zenoh-pico、LLEXT、wasm3）。
- 2026-09-19 · design 阶段登记：Q-03…Q-09 待裁批次、里程碑 M1…M3、固件模块名 ts-*（提案态）。
- 2026-09-20 · LLD 批次登记：Q-10 默认值清单、标识符族（TS_E_*/TS_EVT_*/CONFIG_TS_*/TSAP/ts_api_v1/ts_perm_v1）。
- 2026-09-20 · review-01 深化登记：Q-11 语义批次、DR 编号族、ts-store/TS_FAIL_*/ts_ctx_t/ts_periph_kind_t。
- 2026-09-20 · 就绪度评估登记：Q-12（CI 平台与远端托管）。
- 2026-09-20 · 裁决批次 1 登记：DEC-19…24、tag `dec-19-24`、router 宿主平台；Q-06/Q-07 仍待裁（已补解释）。
- 2026-09-21 · 裁决批次 2 登记：DEC-25/26、tag `dec-25-26`；仍待裁 Q-10/Q-11 + C-1…C-3。
- 2026-09-21 · 裁决批次 3 登记：DEC-27…29、tag `dec-27-29`；§3 板表更新（RP2350 移出）；仍待裁 Q-11①-⑤ + C-1…C-3。
- 2026-09-21 · 裁决批次 4 登记：DEC-30、tag `dec-30`——**Q-01…Q-12 全部裁毕（DEC-17…30）**；仅余 C-1/C-2/C-3 文档确认。
- 2026-09-21 · DEC-32 登记（tag `dec-32`）：Agent 仅 Linux、环境迁 WSL（`docs/dev-environment.md` 建立为环境事实源）；M0 本地全绿。
- 2026-09-21 · 登记 Q-13（APP 线程模型，owner 问询触发）。
- 2026-09-22 · R3 登记：任务行 R3、待裁 Q-14/Q-15/Q-16（Agent 轨道）；外部名 OpenCode/pi/goose/Codex CLI/出局组/框架线/ACP/A2A/MCP Tasks extension。
- 2026-09-22 · **裁决批次 5 登记**：DEC-33（pi 基座 + 多域预留 + 北极星）、DEC-34（双层 MCP 工具面）、tag `dec-33-34`；Q-14/Q-15 转已裁；Galatea 状态更新（未来应用目标）。
- 2026-09-22 · R4 登记：任务行 R4、待裁 Q-17（交互栈确认）；外部名 AAIF/Agent Skills/MCP Registry/AGENTS.md/Zephyr MCP 子系统/ESP-IDF Tools MCP/IoT-SkillsBench/Quilter Project Speedrun/新协议判定组；ACP/A2A 行更新（命名陷阱、AAIF 归属）。
- 2026-09-22 · **裁决批次 6 登记**：DEC-35（ACP 预留）、DEC-36（交互栈定案 + **A2A 预留显式记录**）、tag `dec-35-36`；Q-16/Q-17 转已裁——**Agent 轨道待裁 Q 清零**。
- 2026-09-22 · 登记待裁 Q-18（Agent 实现语言，owner 问询触发）。
- 2026-09-22 · Q-18 建议修订登记：PydanticAI + FastMCP 升为推荐（选项 C）；OpenHands 存档登记。
