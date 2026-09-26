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
| DEC-37 | Agent 实现 = 全 Python（PydanticAI + FastMCP + 自建编码工具集）；修订 DEC-33 基座条款（pi 未选用），北极星与落地约束沿用；动因 = owner 不熟 Node、自研代码须可 review | decisions.md（Q-18 裁定） | 生效 |
| DEC-38 | Q-19 裁定：11 项按建议；#6 上下文压缩 V1 即支持（动态预算取模型窗口、阈值 70%、最低 32k）；#9 输出截断动态化（预算×5%，最低 16KiB/2KiB） | decisions.md（Q-19 裁定） | 生效 |
| DEC-39 | C-4/C-5 确认（Agent design 阶段退出，含工具面清单定型）+ 统一项目计划授权（docs/project-plan.md 双轨）+ MA0 开工 | decisions.md | 生效 |
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
| Q-18 | Agent 实现语言（A：TS 维持 / B：Python 宿主+pi RPC / C：Python 自研 / D：Rust） | owner 问询（2026-09-22） | 已裁 → DEC-37 |
| Q-19 | Agent design 批次默认值与配置清单（13 项，随 HLD/LLD 批次呈递） | design/HLD-agent v0.1 批次 | 已裁 → DEC-38（#6/#9 修订） |

## 2. 任务与里程碑

| 标识符 | 含义 | 首次出现 | 状态 |
|---|---|---|---|
| K1 | 仓库初始化（骨架 + git + AGENTS.md + decisions.md 录入） | FOUNDING_PROMPT §7 | 2026-09-19 完成，待 review |
| R1 | APP 运行时调研（wasm3/WAMR vs LLEXT vs 脚本类等） | FOUNDING_PROMPT §7 | 进行中（初步笔记已落盘） |
| R2 | 数据面协议选型调研 | FOUNDING_PROMPT §7 | 进行中（初步笔记已落盘） |
| R3 | Agent 基座选型调研（coding agent / 框架 / MCP 封装） | owner 指令（2026-09-22） | v1.0 落盘，随 Q-14/Q-15/Q-16 呈递待裁 |
| R4 | Agent 交互与接入方式调研（协议/实践/趋势） | owner 指令（2026-09-22，质疑 MCP 选型触发） | v1.0 落盘，随 Q-16 重呈 + Q-17 新登记待裁 |
| R5 | Agent Python 栈 HLD 级核验（PydanticAI/FastMCP/TSAP 签名栈/zenoh-python） | owner 指令（2026-09-22，Q-18 涟漪审查"有调整的地方需要重新research"） | v1.0 落盘，供 Agent HLD 与 design-review-02 使用 |
| MA0…MA3 | Agent 轨道里程碑（骨架/网关+核心+fw 工具/模拟器+TSAP/部署+skills+高层链） | design/HLD-agent.md §7 | MA0 ✓；**MA1 本地全绿（2026-09-22：ruff+pytest 26/26+FastMCP 客户端实测+fw_build 句柄化实测）**；MA2/MA3 待启动 |
| TaError / TA_E_* | Agent 结构化错误模型与错误码族（LLD-A00 §1；MA1 实现） | agent/tessera_agent/common/errors.py | 已实现（MA1） |
| TaskRegistry / Task | 长任务句柄注册表（对齐 Tasks V2 语义；TTL/环形日志，LLD-A00 §2） | agent/tessera_agent/common/tasks.py | 已实现（MA1） |
| ContextBudget / maybe_compress | 上下文预算（动态窗口/32k 最低/70% 压缩）与压缩助手（DEC-38 #6） | agent/tessera_agent/common/limits.py + core/session.py | 已实现（MA1） |
| ApprovalBroker / sys_pending_approvals / sys_approve | 审批代理与呈现（token 防代批，DEC-38 #7） | agent/tessera_agent/gateway/approvals.py | 已实现（MA1） |
| gated_tool / PolicyTable / PlanDto | 会话审批闸（工具包装层，等效 wrap_tool_execute）/类别策略表/结构化产物 DTO（LLD-A02） | agent/tessera_agent/core/session.py | 已实现（MA1；PydanticAI 原生 Hooks 可后替） |
| build_app / AppContext / run_server | FastMCP 网关装配与 stdio 入口（LLD-A01） | agent/tessera_agent/gateway/server.py | 已实现（MA1） |
| ts-store API 族（ts_store_init/meta_write/meta_read/prov_load/prov/noinit_put/noinit_get/slot_write/slot_read/slot_hash） | 存储抽象公共 API（LLD-ts-store §2-6；M2a 实现） | firmware/module/tessera/include/ts/store.h | 已实现（M2a） |
| ts_prov_t / ts_store_part_t / ts_store_test_reset / ts_store_prov_write_test | prov schema v1 数据模型 / 分区枚举 / 测试钩子（含烧录注入通道） | include/ts/store.h + src/store/ | 已实现（M2a） |
| tsap.h / tsap_view_t / TSAP_MAGIC / TSAP_HEADER_SIZE | TSAP v1 容器格式定稿（16 字节头/大端；M2a，DEC-21） | include/ts/tsap.h | 已实现（M2a） |
| ts_sha256 / ts_sha256_ctx_t | 自包含 SHA-256（slot 安装校验摘要；M2a，宿主向量对拍 hashlib 验证） | src/store/sha256.c | 已实现（M2a） |
| framework.store | M2a twister 用例（meta 撕裂/prov 校验/slot+sha 向量/noinit/tsap 头） | firmware/tests/store | 已实现（M2a 全绿） |
| TsapManifest / manifest CBOR schema v1 | Agent 侧 manifest 镜像（canonical CBOR；app_id/semver/health_ping 必含校验） | agent/tessera_agent/tools_tsap/manifest.py | 已实现（MA2） |
| cose 双实现族（sign_pycose/sign_diy/verify_both/sign_cross_verified） | COSE_Sign1(ed25519) 双实现互验（DR-21 单键纪律 + pycose 停更对冲） | agent/tessera_agent/tools_tsap/cose.py | 已实现（MA2） |
| Scenario / SimInput / SimExpectation | 仿真场景 schema v1（inputs 升序/eq-within-count） | agent/tessera_agent/tools_sim/scenario.py | 已实现（MA2） |
| sim_run 执行器（_replay_build/_replay_run_once） | L4 重放直接二进制执行（M1 接口）+ 双跑确定性 + 期望评估 + timeline_digest | agent/tessera_agent/tools_sim/runner.py | 已实现（MA2） |
| test_sim_e2e | MA2 退出 E2E（真实构建+双跑+断言；env TESSERA_SIM_E2E=1 启用） | agent/tests/test_tsap_sim.py | 已验证通过（2026-09-22） |
| project-plan | 统一项目开发计划（双轨 M 系 + MA 系，DEC-39 授权） | docs/project-plan.md | v1.0 生效 |
| M0 | west 工作区 + native_sim 空模块构建 + CI 骨架 | FOUNDING_PROMPT §7 | **本地全绿（2026-09-21，WSL：构建+twister 运行级+pytest）**；仅余 GitHub 远端推送（CI 上线） |
| M1 | ts-core + ts-safety（安全层最小闭环） | HLD §7 | **本地全绿（2026-09-22）：twister 4/4 配置 12 用例 + L5 5/5 + pytest；M1 退出 review 门已呈报** |
| M2 | ts-hal + ts-appmgr + WAMR 集成（拆 M2a：store/TSAP/slot；M2b：hal/权限/WAMR） | HLD §7 | 待启动（规格已生效） |
| M3 | ts-net + ts-power + 集成与重放测试（拆 M3a：net；M3b：power/periph/集成） | HLD §7 | 待启动（规格已生效） |
| kickoff | K1 首次提交的 git tag | FOUNDING_PROMPT §9 | 已打 |
| dec-wamr-zenoh | DEC-17/18 裁定登记提交的 git tag（重大裁决留痕，军规 5） | decisions.md 修订记录 | 已打 |
| dec-19-24 | 裁决批次 1（DEC-19…24）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| dec-25-26 | 裁决批次 2（DEC-25/26）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| dec-27-29 | 裁决批次 3（DEC-27…29）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| dec-30 | 裁决批次 4（DEC-30，Q 链全部裁毕）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| std-v1 | 规范套件批准生效的 git tag（C-3，2026-09-21） | decisions.md 修订记录 | 已打 |
| DR-xx | design review 发现编号族（DR-01…17 见 design-review-01；**DR-18…23 见 design-review-02**（Q-18 涟漪审查，全处置） | design/design-review-0*.md | 存档 |
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
| pi | AI agent 工具箱（earendil-works/pi，原 badlogic/pi-mono；MIT；v0.87.x；库嵌入一等）；R3 候选 A，**DEC-33 曾选定，DEC-37（Q-18：C 全 Python）改选 PydanticAI 后未选用**；B1 备选（Python 宿主 + pi 子进程经 pi-mcp-adapter 回接）留档 | 存档（未选用） |
| PydanticAI / FastMCP | Agent 基座（DEC-37）：pydantic-ai-slim + FastMCP 4（Apache-2.0）——Python 3.12 支持、审批闸 Hooks、agent 嵌入 MCP server 官方模式；事实见 R5 | 生效（选型） |
| TSAP Python 签名栈 | cbor2(canonical=True) + pycose + cryptography（DEC-21 的 Agent 侧实现路线，R5 §4；纪律：protected header 单键 {1:-8}；DIY fallback 双验） | R5 定案（Agent HLD 输入） |
| eclipse-zenoh（zenoh-python） | zenoh 官方 Python 绑定（Rust 核心封装，同步 API）；**三方同 minor 钉版**：router/zenoh-python/zenoh-pico = 1.10.1；Zenoh 2.0（计划 2026 H2）= 联合升级风险（牵动 M3a） | R5 定案（Agent HLD 输入） |
| goose | Block 开源 agent（block/goose，Apache-2.0，Rust，扩展体系=MCP server）；R3 候选 C | R3 呈递（待裁） |
| Codex CLI | OpenAI 开源 coding agent（Apache-2.0，app-server 形态）；R3 备查 | 存档（未选用，R3） |
| Claude Agent SDK / Gemini CLI / Crush / Aider / Amazon Q CLI | R3 出局组（闭源运行时+模型锁定 / 锁 Google / FSL 许可证 / 停更+非 agent 架构 / 已归档） | 存档（R3 排除） |
| Vercel AI SDK | R3 自建循环框架线候选（TypeScript）——Q-18 定全 Python 后不适用 | 存档（未选用） |
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
| ts-core 公共 API 族（ts_time_ms/ts_time_test_bind/ts_evt_subscribe/ts_evt_publish/ts_wdt_register/ts_wdt_feed/ts_wdt_start/ts_core_boot/ts_boot_steps） | ts-core 对外 API（LLD-ts-core §2-5；M1 实现） | firmware/module/tessera/include/ts/core.h | 已实现（M1） |
| ts-safety 公共 API 族（ts_safety_register_channel/commit/readback/channel_state/force_all_fault/system_fail/set_link/clear_fault/estop_init/poweron_init/estop_deferred_publish/audit_copy/audit_dropped） | ts-safety 对外 API（LLD-ts-safety §2-5；M1 实现） | firmware/module/tessera/include/ts/safety.h | 已实现（M1） |
| ts 通道/审计类型族（ts_out_ch_t/ts_out_value_t/ts_ch_kind_t/ts_ch_state_t/ts_audit_entry_t/ts_driver_ops_t/ts_drivers/ts_driversim_writes/ts_write_rec_t） | ts-safety 数据模型与驱动分发（LLD-ts-safety §2/§6；M1 实现） | include/ts/safety.h + src/safety/ | 已实现（M1） |
| framework.core / framework.safety / framework.replay | M1 twister 用例（L1/L4 雏形；replay = 双通道确定性比对 + stdout JSONL 接口） | firmware/tests/{core,safety,replay} | 已实现（M1 全绿） |
| check_l5.py | L5 安全合同机械检查脚本（五项，testing.md §3；CI 独立 job 一票否决） | firmware/tests/l5/ | 已实现（M1） |
| IR-xx | M1 实现自检发现编号族（IR-01…04 全处置：estop 清除死锁修复/审计一致性修复/两项记录） | design/impl-review-m1.md | 存档 |
| IR-xx（续） | 实现自检发现编号族续（IR-05…20：M2a/M2b/MA0-MA2 审查——修复 10 项含验签 fail-closed/tsap 回绕/keygen 审批闸，登记 6 项） | design/impl-review-m2a-ma2.md | 存档 |
| ts-net 公共 API 族（ts_net_set_ids/ts_net_key_{cmd,tel,evt,hb,sys}/ts_net_state/ts_net_backoff_ms/ts_net_session_poll/ts_net_pubq_{push,dropped,flush}/ts_net_linkmon_{tick,hb_host}/ts_net_link_up） + ts_net_transport_t（传输缝） | ts-net 对外 API 与传输抽象（LLD-ts-net §1-6；M3a.1 实现——真实现=zenoh-pico 1.10.1，测试注入桩） | firmware/module/tessera/include/ts/net.h | 已实现（M3a.1） |
| framework.net | ts-net L1/L2 用例（key/退避/pubq/会话/linkmon→safety 集成） | firmware/tests/net | 已实现（M3a.1 全绿） |
| ts-net M3a.2 族（ts_net_cmd_{register,dispatch}/ts_net_cmd_sys_init/ts_net_pub_{init,telem}/ts_net_init/cbor_min 内部族）+ ts_net_cmd_args_t | sys 命令面（host_only 7 项，DEC-30①/DR-03）+ 遥测/事件发布 + boot 接线 | include/ts/net.h + src/net/{cmd,pub,init,cbor_min}.c | 已实现（M3a.2） |
| ts_safety_summary / ts_time_wall_{set,ms} / ts_value_encode（公共化） | 安全汇总观测 / 墙钟数据字段（DR-08）/ 规范单字编码（审计遥测统一口径） | include/ts/{safety,core}.h | 已实现（M3a.2，sys 命令面支撑） |
| l3app / l3_client.py | L3 联调镜像与客户端（native_sim↔zenohd 真实会话；prov 手工定稿键序烧入；复跑方法 dev-env §8） | firmware/l3app | 已实现（L3 PASS 2026-09-23） |
| 命令信封 v2（ver/kind/rid/src/idem/to）+ kind 注册表（请求 1-15/回执 16-31/事件 32-95/遥测 96-127） | ts-net 命令面演进信封与消息类型编号（NeuroLink 借鉴）；v1 弃用期 | design/LLD-ts-net.md §4.2/§4.4 + src/net/cmd.c | 已实现（DEC-40/42，2026-09-23 批） |
| ts_net lease 族（sys/lease-{acquire,release,get} + ts_net_lease_{acquire,release,get,held_by} + CONFIG_TS_NET_LEASE_TTL_MS） | 控制租约：多方并发命令准入仲裁（NeuroLink lease_manager 借鉴；惰性过期；lease_id 单调；不联动安全态） | design/LLD-ts-net.md §4.5 + src/net/lease.c | 已实现（DEC-41，2026-09-23 批；M2b.2 写命令挂钩点 = ts_net_lease_held_by） |
| ts_net_qos_t（TS_NET_QOS_{BESTEFFORT,SAFETY}）+ ts_net_pubq_push_qos + transport.publish(qos) | 发布服务类穿透 pubq→传输（DEC-42 QoS 映射：安全事件 BLOCK+REAL_TIME，遥测/心跳缺省 DROP+DATA） | include/ts/net.h + src/net/{pubq,zenoh}.c | 已实现（DEC-42，2026-09-23 批） |
| 遥测 payload 键 dev（原 kind 改名）+ 事件 payload kind=32+evt_id | DEC-42 信封落地键名（消费端 Agent keys.py 镜像出处） | design/LLD-ts-net.md §5 + src/net/pub.c | 已实现（2026-09-23 批，消费端随批同步） |
| ts-appmgr 分步安装族（ts_appmgr_stage_{begin,chunk,verify,activate}）+ sys/app-{begin,chunk,verify,activate}/get-app + ts_cbor_bstr_ref + CONFIG_TS_NET_APP_CHUNK_MAX | 远程部署面固件侧（LLD-A06 §3；upload→verify→activate；写类命令 gated = v2+租约） | include/ts/{appmgr,net}.h + src/{appmgr/pkg.c,net/cmd.c} | 已实现（MA3.1） |
| Agent deploy 族（tools_net/{keys,zenoh_service,deploy}.py：envelope/parse_reply/kind 镜像 + ZenohService 线程桥 + discover/status/push_app；MCP 工具 deploy_{discover,status,push_app}） | Agent 部署工具链（LLD-A06 §1-3；分块分步推送 + 租约闭环 + idem 重试 + tsap_verify 强制复验） | agent/tessera_agent/tools_net + gateway/server.py | 已实现（MA3.1） |
| FakeCube / test_deploy_e2e.py（TESSERA_E2E_DEPLOY=1 门控） | 部署面单测语义桩与 E2E（MA3 退出标准断言：confirmed/slot 切换/容器自洽） | agent/tests | 已实现（MA3.1） |
| A07 skills 族（agent/skills/{tessera-workflow,tessera-build,tessera-tsap,tessera-safety}/SKILL.md + SkillRef/loader + skill_read 工具 + SOURCES.lock + sync_check） | 域知识包与渐进披露（开放标准目录；派生纪律 = 源文档摘要锁 + pytest 守卫，Q-19 #13/DEC-38 #13） | agent/skills + tessera_agent/skills | 已实现（MA3.2） |
| 平台/域拆分（platform.py：DomainPack/DomainPackBase/MountAPI/assemble + compose.py 组合根 + domain/firmware.py：FirmwareDomainPack/FirmwareDeployer/validate_tsap_manifest） | 多域预留架构（DEC-33：平台不 import 域——导入图测试守卫）；固件域 14 工具 + skills/policy/validators/deployer 声明 | agent/tessera_agent/{platform,domain} | 已实现（MA3.2） |
| app_chain 族（DevelopOutcome/app_develop/app_deploy MCP 工具） | DEC-34 高层链：spec→计划/manifest（结构化校验）→TSAP 打包复验；包→复验→发现定位→分块部署→确认（S5）；wasm 产物边界 = M2b.2 | agent/tessera_agent/domain/app_chain.py | 已实现（MA3.2） |
| ts-power 族（ts_pwr_slot_t/ts_power_{register_slot,request,slot_count,slot_get}/ts_power_budget_t/ts_power_budget_snapshot + CONFIG_TS_POWER_MAX_SLOTS） | 受控供电（DEC-03 合同 7）：槽注册→TS_CH_POWER 通道；预算 prov 只读 + readback 记账 + 峰值 + TS_EVT_POWER_BUDGET | include/ts/power.h + src/power/{slots,budget}.c | 已实现（M3b） |
| ts-periph 族（ts_periph_kind_t{TS_PK_*}/ts_periph_desc_t/ts_periph_{register,count,get,attach,detach} + ts_periph_evt_t + CONFIG_TS_PERIPH_MAX_DESCS） | 描述符职责链（uid/dt 双名解耦 DEC-04）+ 插拔（DETACH→单通道 SAFE_FAULT） | include/ts/periph.h + src/periph/{desc,hotplug}.c | 已实现（M3b） |
| ts_safety_force_channel_fault / ts_safety_channel_recover / ts_safety_test_reset | 单通道故障与恢复（periph DETACH 机制面）+ 测试隔离（通道表全清） | include/ts/safety.h + src/safety/channel.c | 已实现（M3b） |
| kind 97（功率预算快照）+ ts_pwr_budget_evt_t | 遥测区间分配（LLD-ts-net §4.4 权威；keys.py KIND_TELEMETRY_POWER 镜像） | design/LLD-ts-net.md §4.4 + src/net/pub.c | 已实现（M3b） |
| impl-review-01 / F-1…F-8 | impl 阶段评审报告与发现编号族（2026-09-25，对象 = DEC 批/MA3.1/MA3.2/M3b 四交付单元；验证全绿复现，8 项发现分级处置） | docs/impl-review-01.md | 已处置（修复批 2026-09-25 同日交付，F-5/F-7 为登记项） |
| 里程碑 tag 族（m0…m3b / ma0…ma3） | git annotated tag 指向各里程碑交付终态提交（军规 5；m0 完整退出仍待 CI 上线〔DEC-24〕——tag 标记本地交付点） | git tag -l 'm*' 'ma*' | 2026-09-25 补打（impl-review-01 F-6） |
| Q-23 / CONFIG_TS_APP_WAMR{,_HEAP} / TS_WAMR_DIR / tessera_wamr 库 / wamr_compat.c | WAMR 宿主线程模型与并发收口（F-7 落点，待裁）+ WAMR 接入配置族（M2b.2a 环境批：钉版 WAMR-2.4.5 源码根注入、独立三方库、Zephyr 4.4 API 兼容垫片） | decisions.md Q-23 + firmware/module/tessera/{Kconfig,CMakeLists.txt} + src/appmgr/wamr_compat.c | 环境批已交付（2026-09-26）；接线批待 Q-23 |
| framework.wamr / 样例 APP 族（tests/wamr/app/{sample.c,build.sh,sample.wasm} + wasm_bytes.h 生成件） | WAMR 装载/零导入实例化/调用/重放冒烟（DEC-25 边界活体证明）；clang wasm32 自由固件产物（103B） | firmware/tests/wamr/ | 已实现（M2b.2a 环境批） |
| framework.wamrdemo / busy.wasm 族（tests/wamrdemo/{app,src}） | Q-23 实证批：时延画像/B 方案 sysworkq 饿死/预算 TOCTOU 窗口（203ns）/A 通路对照（SMP+USE_SWITCH+真实时间对齐配置样板） | firmware/tests/wamrdemo/ + decisions.md Q-23 实验补充 | 已实现（2026-09-26，Q-23 证据留档） |
| DEC-43 / ts_safety_write_lock / ts_safety_commit_locked / framework.conc | Q-23 裁决（方案 A：每 APP 一框架线程 + 锁收口）+ 锁收口 API 族（commit_lock 受控暴露/持锁提交变体）+ 并发回归套件（对齐双冲/迁移×提交不变量/pubq 完整性） | decisions.md DEC-43 + src/safety/{commit,channel}.c + src/power/slots.c + src/net/pubq.c + firmware/tests/conc/ | 已实现（2026-09-26，真 SMP 板判别力随板级兑现） |
| ts_appmgr_app_{start,stop,evt,running,stats} / ts_app_rt_stats / ts_native_syms（natives.c） / mod_cache | APP 运行时宿主 API + ts_api_v1 wasm 导入面（ctx 注入防伪造，调用期权限裁决）+ WAMR 模块进程级复用（平台怪癖规避） | include/ts/appmgr.h + src/appmgr/{runtime,natives}.c | 已实现（接线批第二单元，2026-09-26） |
| framework.app / 夹具 APP 族（tests/app/appw/{native_app.c,build.sh,native_app.wasm} + app_wasm.h 生成件） | APP 运行时宿主端到端（生命周期/权限拒绝留痕/健康失败自停）；clang wasm32 带导入夹具（--allow-undefined） | firmware/tests/app/ | 已实现（接线批第二单元） |
| PeerTransport / Frontend / McpFrontend（core/peer.py） | A2A（DEC-36④）/ACP（DEC-35）接入缝——V1 仅协议 + 打桩冒烟 | agent/tessera_agent/core/peer.py | 已预留（MA3.2，实现属未来 Q） |
| NeuroLink / MatrixMechanic | owner 前作参考项目（zenoh 上层协议 / TLV 私有协议；借鉴不照搬，采纳走门③） | github embalmer-Y；WSL 克隆 ~/project/logs/tmp/ref/ | 参考存档（2026-09-23） |
| HLD-agent / LLD-A00…A07 | Agent 轨道设计文档族（A00 公共/A01 网关/A02 核心/A03 固件工具/A04 模拟器/A05 TSAP/A06 部署/A07 skills+平台） | design/HLD-agent.md v0.1 批次 | v0.1 待 owner 确认（C-4/C-5） |
| TA_E_* | Agent 错误码族（TaError 结构化异常，LLD-A00 §1） | LLD-A00 提案 |
| sys_* / task_* / fw_* / sim_* / tsap_* / deploy_* / app_* | Agent MCP 工具名族（原子层 19 + 高层 2，双层工具面 DEC-34；增删 = review 门） | LLD-A01 §2 | 提案（随 C-5/Q-19） |
| DomainPack | 域工具包接口（工具集+skills+策略+校验器+部署器；固件域 = 首个实现，多域预留核心） | design/HLD-agent.md §6.1 / LLD-A07 §3 | 提案 |
| Frontend / PeerTransport | 会话编排层传输抽象（ACP 预留缝，DEC-35）/ A2A 对等接入缝（DEC-36④ 记录点） | LLD-A02 §1 / LLD-A07 §4 | 提案（V1 仅接口预留） |
| SessionOrchestrator / TaskRegistry | 会话编排器（A02）/ 长任务句柄注册表（A00，对齐 Tasks V2 语义） | LLD-A02/A00 | 提案 |
| TsapManifestV1 / PlanDto / AppConfigDto | Agent 侧结构化产物模型（manifest 镜像 / 开发计划 / 硬件配置） | LLD-A05 §2 / LLD-A02 §4 | 提案 |

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
- 2026-09-22 · **裁决批次 7 登记**：DEC-37（Q-18：C 全 Python）、tag `dec-37`；pi 转存档（未选用，B1 备选留档）；新增 PydanticAI/FastMCP、TSAP Python 签名栈、eclipse-zenoh、R5、DR-18…23；Vercel AI SDK 存档。
- 2026-09-22 · **Agent design 批次登记**：HLD-agent/LLD-A00…A07、Q-19（默认值 13 项）、MA0…MA3、TA_E_*/工具名族/DomainPack/Frontend/PeerTransport/SessionOrchestrator/TaskRegistry/TsapManifestV1 等标识符族；C-4/C-5 呈递。
- 2026-09-22 · **裁决批次 8 登记**：DEC-38（Q-19：11 项按建议 + #6/#9 修订）、tag `dec-38`；Q-19 转已裁；设计文档同步（HLD v0.1.1 / LLD-A00·A01·A02 v0.1.1）。
- 2026-09-22 · **裁决批次 9 登记**：DEC-39（C-4/C-5 确认 + 统一计划 + MA0 开工）、tag `dec-39`；project-plan 标识符登记。
- 2026-09-22 · **M1 交付登记**：ts-core/ts-safety API 族与类型族、framework.{core,safety,replay} 用例、check_l5.py；M1 行更新为本地全绿（退出 review 门呈报）。
- 2026-09-22 · M1 自检登记：IR-01…04（design/impl-review-m1.md）；tag 当时无（2026-09-25 impl-review-01 F-6 已补打 m1 于交付终态提交）。
- 2026-09-22 · **MA1 交付登记**：TaError/TaskRegistry/ContextBudget/ApprovalBroker/gated_tool/PolicyTable/PlanDto/build_app 等标识符；MA1 状态 = 本地全绿（FastMCP 客户端 + fw_build 句柄化实测）。
