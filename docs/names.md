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
| Q-20 … Q-31 | 板级/验签/审计/资源/多 APP 各批呈递（Q-20 挂钟/Q-21 审计/Q-22 分区/Q-23 环境/Q-24 双核/Q-25 代码生成/Q-26 硬件形态/Q-27 传输与 fs/Q-28 看门狗/Q-29 验签/Q-30 升级/Q-31 审计持久化） | decisions.md | 已裁 → DEC-44…DEC-52（自检 SC-15 补索引——此前未入册） |
| Q-32 … Q-37 | 多 APP 槽池（→DEC-53）/多开发者锁（→DEC-54 双批）/复杂 APP（→DEC-55）/真多线程（→DEC-55）/Agent 批（→DEC-57）/资源分级（→DEC-57） | decisions.md | 已裁（自检 SC-15 补索引） |
| Q-38 … Q-41 | Agent 创作循环/资源分级/信任链方向/standalone 泛化（R 批四呈递） | decisions.md | 已裁 → DEC-57（全 A + 质量优先条款） |
| Q-42 | prov v2/manifest v2 档位/门值（CG 门③） | decisions.md | 已裁 → DEC-59 |
| Q-43 | 信任根表 schema/存储/命令面（EC 门③） | decisions.md | 已裁 → DEC-60 |
| Q-44 | ES8311 音频面（K2 门③——第二板卡接入批） | decisions.md | 已裁 → DEC-61（owner 泛指令先例） |
| Q-46 | 本地确认路安装闸（F3 门③——五子项呈递停门） | decisions.md | 已裁 → DEC-62（②呈现面 owner 修订 = LVGL） |
| Q-47 | zenoh TLS 链路（P1-2 门③——五子项呈递停门） | decisions.md | **已裁 → DEC-63**（2026-10-16 按建议） |
| DEC-39 … DEC-56 | 统一计划/板级批/MD 批/V0.1-0.4 版本批/环境迁移/需求校准（通用域解放）各批裁决与交付登记 | decisions.md | 生效（自检 SC-15 补索引） |
| DEC-57 / DEC-58 / DEC-59 / DEC-60 | Q-38…41 全 A + 质量优先条款 / CG0 门④措辞 + 双 HLD / Q-42 三项按建议值 / Q-43 五项按建议值 | decisions.md | 生效 |
| DEC-61 | Q-44 ES8311 三子项按建议值（owner 泛指令先例） | decisions.md | 生效 |
| DEC-62 | Q-46/F3 开工（② LVGL 修订）+ tag 并入下版 + gcov 缓办 + P1 全批点向 + R10 留档 | decisions.md | 生效 |

## 2. 任务与里程碑

| 标识符 | 含义 | 首次出现 | 状态 |
|---|---|---|---|
| K1 | 仓库初始化（骨架 + git + AGENTS.md + decisions.md 录入） | FOUNDING_PROMPT §7 | 2026-09-19 完成，待 review |
| R1 | APP 运行时调研（wasm3/WAMR vs LLEXT vs 脚本类等） | FOUNDING_PROMPT §7 | 进行中（初步笔记已落盘） |
| R2 | 数据面协议选型调研 | FOUNDING_PROMPT §7 | 进行中（初步笔记已落盘） |
| R3 | Agent 基座选型调研（coding agent / 框架 / MCP 封装） | owner 指令（2026-09-22） | v1.0 落盘，随 Q-14/Q-15/Q-16 呈递待裁 |
| R4 | Agent 交互与接入方式调研（协议/实践/趋势） | owner 指令（2026-09-22，质疑 MCP 选型触发） | v1.0 落盘，随 Q-16 重呈 + Q-17 新登记待裁 |
| R5 | Agent Python 栈 HLD 级核验（PydanticAI/FastMCP/TSAP 签名栈/zenoh-python） | owner 指令（2026-09-22，Q-18 涟漪审查"有调整的地方需要重新research"） | v1.0 落盘，供 Agent HLD 与 design-review-02 使用 |
| R10 | HAL 扩展性与安全边界（owner 架构讨论留档：Zephyr 暴露八问题否决 / 安全边界 O(1) / 长尾解法 A 特权组件 + B 策略数据） | owner 2026-10-16 架构问询（DEC-62⑤） | v1.0 落盘，HAL 扩展门③在案依据 |
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
| ts_trust_* API 族（ts_store_trust_load/validate/write/trust_test_reset/trust_corrupt_test + ts_trust_table_t + TS_TRUST_KEYS_MAX） | 信任根表持久化面（V0.8.0 EC2 · Q-43③/DEC-60；TUF root 同型全量替换） | firmware/module/tessera/include/ts/store.h + src/store/ts_trust.c | 已实现（EC2） |
| ts_appmgr_trust_update / ts_appmgr_trust_effective | 信任更新编排（COSE 现有效集签名 + ver 严格 N+1）与有效集构建 | include/ts/appmgr.h + src/appmgr/verify.c | 已实现（EC2） |
| sys/trust-update · sys/trust-get | 信任表网络命令面（gated+租约 / 未门控读回） | src/net/cmd.c + LLD-ts-net §4.3 | 已实现（EC2） |
| TS_EVT_TRUST_UPDATED | 信任表更新事件（安全类 QoS，extra {"ver"}；订阅十类） | include/ts/core.h + src/net/pub.c | 已实现（EC2） |
| deploy.trust_get / deploy.trust_update | Agent 信任工具（表 CBOR 手工构造 + cose.sign_diy + 租约闭环） | agent/tessera_agent/tools_net/deploy.py | 已实现（EC2） |
| tsap_tools.manifest_summary / install_permission_brief | 安装期权限呈报数据源与审批 brief（EC3 · Q-40③） | agent tools_tsap/tools.py + domain/firmware.py | 已实现（EC3） |
| gen_trust_fixtures.py / boot_pkg_devroot / trust_blob_* | EC2 测试夹具族（固定种子 + 测试根签名——机械生成纪律） | firmware/tests/app/ | 已实现（EC2） |
| L5 检查 7（slot 收口） | ts_store_slot_write/erase 调用点白名单 = pkg.c（侧载纪律机械保证） | firmware/tests/l5/check_l5.py + testing.md §3 | 已实现（EC4） |
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
| framework.app / 夹具 APP 族（tests/app/appw/{native_app.c,build.sh,native_app.wasm} + app_wasm.h 生成件） | APP 运行时宿主端到端（生命周期/权限拒绝留痕/健康失败自停/boot slot 装载全链）；clang wasm32 带导入夹具（--allow-undefined）——Agent E2E 同源工件 | firmware/tests/app/ | 已实现（接线批 + M2b.2 收尾） |
| ts_appmgr_boot_start / app_load 步骤 / TS_APP_LOAD_MAX | boot 装载（HLD §4.4-8）：slot TSAP → manifest canonical 走查（fail-closed）→ caps ';' 组合 → wasm 装载运行；APP 故障不阻塞启动 | include/ts/appmgr.h + src/appmgr/slot.c + src/core/boot.c | 已实现（M2b.2 收尾，2026-09-26） |
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
- 2026-09-26 · **板级二交付登记**：Q-24（双核终验载体，待裁）；board-bench-01（docs/ 板级效率基准报告）；boardbench（firmware/tests/ 基准应用：appw/bench.c 夹具 + src/main.c 宿主计时；BB* console 行 = 数据格式）；教训 18/19（dev-env：WAMR xtensa 官方汇编陷出 / CCOUNT 计时源）。
- 2026-09-27 · **板级三交付登记**：DEC-44（Q-24 → A 裁决：native_sim 多核为准）；TS_DRV_GPIO（Kconfig 真机 GPIO 后端）；zephyr,user 绑定约定（uid + io-gpios）；boardbench BB5 系列（IO 三层对照）；L5 豁免 boardbench/main.c（裸基线对照层）；教训 20（ZEPHYR_USER_NODE 版本差）。
- 2026-09-27 · **板级四交付登记**：netbench（firmware/tests/ 基准：WiFi+zenoh 命令往返；NB* console 行）；netbench-01（docs/ 报告）；netbench_client.py（L0/L1/L2 三层探针）；教训 21（WiFi 五要点 + 反引号 heredoc 禁令）；zenohd 双实例（9955 板级 / 7447 L3）。
- 2026-09-28 · **板级五交付登记**：persistbench（firmware/tests/ 持久化验证应用；PB* console 行）；board-persist-01（docs/ 报告）；ts_*_part（DT 分区标签族：ts_prov_part/ts_meta_part/ts_slot_a_part/ts_slot_b_part/ts_noinit_part）+ fw_b_part（MCUmgr 预留）；TS_STORE_FLASH（Kconfig flash 后端）；ts_store_slot_erase（公共 API 增补）；framework.store.flash（twister 变体）；教训 22（flash 持久化六要点）。
- 2026-10-01 · **板级六交付登记**：psrambench（firmware/tests/ PSRAM 验证应用；PS* console 行）；board-psram-01（docs/ 报告）；TS_APP_PSRAM_HEAP（Kconfig：WAMR 实例堆入 PSRAM〔SMH_REG_ATTR_EXTERNAL〕）；TS_APP_WAMR_HEAP 默认 65536→262144（64KB 基线修正，池模式下结构性不可行）；教训 23（PSRAM 五要点）。
- 2026-10-01 · **板级七交付登记**：board-reconnect-01（docs/ 报告）；ts_net_session_media_down（公共 API 增补：承载断线下沉）；NB-R 场景（netbench 脚本化双断链；NBR* console 行）；ts-net 专用工作队列（net_wq）；教训 24（WiFi 重连四要点）。
- 2026-10-01 · **板级八交付登记**：estopbench（firmware/tests/ estop 真机验证应用；EB* console 行）；board-estop-01（docs/ 报告）；ts-estop-gpio alias（estop DT 绑定机制修订：aliases 替代 chosen）；estop-key（gpio-keys 子节点约定）；教训 25（estop 绑定与注入三要点）。
- 2026-10-02 · **板级九交付登记**：periphbench（firmware/tests/ PWM/ADC 真机验证应用；PP* console 行——军规 6 撞名自查后弃 PB* 改 PP*，persistbench PB* 不受影响）；board-periph-01（docs/ 报告）；TS_DRV_PWM / TS_DRV_ADC（Kconfig 真机后端对）；ts_drv_pwm_init / ts_drv_pwm_err_count（safety.h 公共 API 增补）；ts_adc_drv_init（hal.h 公共 API 增补）；pb-pwm / pb-adc（bench 通道逻辑名）；duty<<4（LEDC 寄存器字段口径）；教训 26（dev-env：LEDC/ADC 四要点）。
- 2026-10-02 · **板级十交付登记**：deploybench（firmware/tests/ 部署 E2E 板侧载体；DB* console 行——前缀撞名自查：现有 PB/NB/NBR/EB/BB/PS/PP 之外新增 DB，无碰撞）；board-deploy-01（docs/ 报告）；DEPLOY*（client.py 判定行前缀）；dbn/dbc（部署目标逻辑名）；com.tessera.e2e（E2E app_id，与 sim E2E 同名同夹具〔native_app.wasm〕）；app_init/app_tick/app_evt（manifest exports 权威名——板级十对齐 LLD §4，弃 init/tick/evt 漂移）；教训 27（dev-env：手抄二进制数组禁令 + 分区残留态）。

- 2026-10-04 · **G1 交付登记（DEC-45）**：app_compile（MCP 工具，auto 类：C 源→wasm+面检查）；wasm_build（agent 模块：compile_app_c / wasm_func_surface / NATIVE_WHITELIST 六白名单）；source_c（DevelopOutcome 字段：LLM 产 C 源）；SMOKE3（真 LLM 代码生成全链冒烟代号）；R1-R8（Agent CLI 可靠性调研→工程决策映射，docs/agent-codegen-reliability-01.md）；agent-codegen-reliability-01（docs/ 报告）。

- 2026-10-05 · **MD1.1 交付登记**：agent/demos/D1-D7（demo 产物族：spec/app.c/app.wasm/manifest.json/*.tsap/md1.pub——私钥仓外）；hb-host 心跳（Agent→板链路判活 publish 面，md1_run3 模板）；demos-01（docs/ 报告）；MD1.1b（P1 专项：连续激活 copy0 装载错位）；dbpwm（deploybench PWM 通道 uid）。

- 2026-10-05 · **MD1.1b 交付登记**：metabench（firmware/tests/ P1 受控复现载体：六轮 meta 写+复位读+双副本十六进制打印；MB* console 行）；data0/data1（meta.c 分缓冲修复标识）；D-AV / D-SD（音视频/SD 卡 demo 代号——Q-26 呈递）；Sense 版（XIAO ESP32S3 Sense，带 OV2640+PDM 麦——Q-26 硬件选项）。

- 2026-10-05 · **MD1.2a 交付登记**：sdbench（firmware/tests/ SD bring-up 载体；SD* console 行）；sense 板变体（xiao_esp32s3/esp32s3/procpu/sense——Zephyr 官方 Sense DT：OV2640+DVP+SD 槽全就绪）；DEC-46（Q-26 裁决：硬件即板载）；cambench（MD1.2b 摄像头 bring-up 载体代号）。

- 2026-10-05 · **MD1.2b 交付登记**：cambench（firmware/tests/ 摄像头 bring-up 载体；CB* console 行）；frame.raw（cambench 首帧落盘工件）；video_buffer_aligned_alloc 池路径（V1 摄像头缓冲唯一路径——外部静态缓冲不可用）。

- 2026-10-06 · **impl-review-02 交付登记**：impl-review-02（docs/ 报告：全库风险审查，M0→MD1.2b 已交付内容）；IR2-xx（审查发现编号族——与 impl-review-01 的 IR-xx 以 IR2 前缀区分，编号不复用）。

- 2026-10-06 · **MD1.2d 呈递批登记**：avbench（firmware/tests/ 视频帧 zenoh 分片传输真机载体；AV* console 行——前缀撞名自查：现有 AV 未占用，无碰撞）；av-transport-01（docs/ 报告）；Q-27 六子项（MD1.2d 呈递：传输通道/分片参数/ts-av 面/ts-fs 面/ts_perm_v1 扩展/同步面）；ts_av_capture / ts_fs_list·read·write·delete / ts_net_publish（Q-27 提案 natives——批准后生效）；fs_paths（ts_perm_v1 提案新字段）；avbench/frame（bench 键空间，非产品 keyspace）；Z_BATCH_UNICAST_SIZE（zenoh-pico 静态批缓冲 2048——chunk 上限根因）。

- 2026-10-06 · **DEC-47 + 计划修订批登记**：DEC-47（Q-27 裁决：六子项全部建议值 + 上游 issue 暂不提）；MD1.2e/f/g/h（MD1.2 实现批单元名：ts-fs 面/D-SD demo/ts-av+publish 面/D-AV demo）；Q-28（看门狗接线呈递——IR2-01 根治，门①）；Q-29（验签实装呈递——TSAP 头摘要+ed25519+生产 prov 通道，门③）；ts-fs / ts-av（能力面模块代号）。

- 2026-10-06 · **Q-28 呈递登记**：四层防线（Q-28 方案框架：L1 软看门狗/L2 指令配额/L3 task_wdt+硬件回退/L4 noinit 留痕+真复位）；WAMR_BUILD_INSTRUCTION_METERING（WAMR 上游 cmake 开关——指令配额编译门）；wasm_runtime_set_instruction_count_limit（WAMR API：每次调用前设预算）；instruction limit exceeded（超限异常文本——走既有健康失败/回滚路径）；wdtbench（真机载体代号——Q-28 批交付）；静态预注册+动态激活（ts_wdt 注册窗口修复方案）；TS_WDT_SYWORK 喂狗点（patrol_work_cb 顶部）。

- 2026-10-06 · **看门狗实施批登记（DEC-48）**：DEC-48（Q-28 裁决：全部建议值）；wdtbench（firmware/tests/ 真机载体；WB* console 行——撞名自查：WB 未占用）；TS_WDT_NET_PERIOD_MS / TS_WDT_APPMGR_PERIOD_MS / TS_WDT_SYWORK_PERIOD_MS / TS_WDT_CHANNEL_MS（Kconfig 新默认：2000/1000/1000/5000）；TS_APP_INSTR_INIT / TS_APP_INSTR_TICK（Kconfig 指令预算：1,000,000/200,000）；ts_safety_commit_a（公共 API：带 actor 归因的提交）；wdt.spin.bench（夹具 app_id，wdt_pkg.h 机械生成）；wdt0/chosen zephyr,watchdog（esp32s3 硬件 WDT 接线约定）；WATCHDOG（Zephyr WDT 子系统根符号——CONFIG_WDT 不存在，教训）。

- 2026-10-06 · **PC 读面加固批登记**：_gate_source / _read_within（agent 侧读面白名单双门：预处理 include 禁令 + 路径白名单）；IR2-03 处置态 = 已根治（impl-review-02 高项①消账；IR2-04/09/10/11 同批消账）。

- 2026-10-07 · **MD1.2e 交付登记**：ts_fs_list / ts_fs_read / ts_fs_write / ts_fs_delete（公共 API + natives，DEC-47④）；TS_PERM_CLASS_FS / TS_PERM_OP_LIST / TS_PERM_OP_DELETE（ts_perm_v1 新类与新 op）；fs_paths（manifest 新字段：路径前缀白名单）；ts_fs_paths_bind / ts_fs_path_allowed（绑定与裁决 API）；TS_HAL_FS / TS_HAL_FS_PATHS_MAX（Kconfig）；framework.app test_05_fs_gates。

- 2026-10-07 · **MD1.2f 交付登记**：D-SD（demo 代号：SD 卡读写安全演示）；dsdbench（firmware/tests/ 真机载体；DS* console 行）；tessera.demo.d-sd（demo app_id）；dsd.txt / dsd-done.txt / dsd-deny.txt（判据工件路径）；apps-data（fs_paths 白名单工作目录约定）。

- 2026-10-07 · **MD1.2g 交付登记（单元 A）**：ts_av_capture / ts_av_publish / ts_av_config_bind（ts-av 公共 API，hal/av.c）；TS_PERM_CLASS_AV（ts_perm_v1 新类，op = read）；TS_AV_FMT_JPEG / TS_AV_FMT_RGB565（采集格式枚举）；TS_HAL_AV / TS_HAL_AV_TIMEOUT_MS（Kconfig）；avq / ts_net_avq_push·flush·dropped·reset（av 分片通道队列，net/avq.c）；ts_net_key_av（key 构造：…/av/<id>/frame——DEC-47① 专用帧分片通道，stream = 数值 app_id）；TS_NET_PUBLISH_MAX_BYTES / MIN_GAP_MS / RETRY_MAX / RETRY_DELAY_MS / TS_NET_AVQ_DEPTH（Kconfig 族——出处 DEC-47②）；av_fmt / av_w / av_h（manifest 可选键，与 caps av: 互为充要）；framework.app test_06_av_gates / framework.net test_12_avq。

- 2026-10-07 · **MD1.2h 部分交付登记（单元 B）**：D-AV（demo 代号：摄像头帧采集与分片发布演示）；avdemo（firmware/tests/ 真机载体；DA* console 行）；demo.d.av（demo app_id）；dav / dvc（avdemo prov node/cube id——tessera/dav/dvc/av/1/frame）；dav_recv.py（PC 侧帧重组消费端，仓外）；**DAV1**（缺陷登记：av 流压力下 APP 线程无声冻结——3/3 复现，看门狗链按设计收口；专项批 B2）；**DAV2**（上游缺口登记：esp32 DVP 驱动不支持 JPEG 变长帧——pitch=0 → 零长 DMA；demo 走 DEC-47② RGB565 保底，JPEG 随单元 J 重估）；B2（DAV1 专项调试批——排期表单元）。

- 2026-10-07 · **Q-29 呈递登记（单元 C，门③ 停门）**：Q-29（IR2-02 根治：固件 ed25519 真验签〔①B 内置极简 C verify——A=PSA 作实施首查〕+ TSAP 头摘要字段〔②A fmt_ver=2 + 32B sha256(manifest‖wasm)〕+ 生产 prov 烧录通道〔③A esptool 直写〕+ TEST 语义收口〔④A 真验签 + 测试根〕）；TSAP v2（文件格式第二版代号——v1 包 v2 固件 fail-closed 拒收）。

- 2026-10-07 · **验签实施批登记（单元 D，DEC-49 落地）**：TSAP v2（文件格式第二版：flags 位驱动 32B sha256 摘要区——v1 拒收）；ts_appmgr_verify_slot / ts_appmgr_check_digest / ts_appmgr_root_key（验签管线公共内面，appmgr/verify.c）；tweetnacl（vendored 第三方 ed25519——tweetnacl.cr.yp.to 20140427，Public Domain，见 crypto/PROVENANCE.md）；ts-test-root（固定测试根密钥对——agent/tests/fixtures，测试信任 ≠ 生产信任）；TS_VERIFY_SCRATCH（Kconfig：验签双区 scratch）；tnacl_selftest（tweetnacl 内建向量自测钩子）；fixture_pkg / boot_pkg（预签 v2 测试夹具）；flash_prov.py（生产 prov 直写工具，agent/tools）；re_sign_fixtures.py（仓内夹具/演示批量重签链，仓外）。消账：IR2-02（固件验签结构桩）/ IR2-07（回滚闭环）/ 板级十一生产 prov 通道。

- 2026-10-08 · **输入面 G3 批登记（单元 F）**：ts_input_evt（INPUT_CHANGED 载荷 v2：{inst, old_mv, new_mv}）；ts_adc_sample_fw（框架侧 ADC 采样——input monitor 观测路径）；ts_hal_input_test_inject（测试注入钩子）；ts_wdt_deactivate（DEC-48① 对称面：源去激活）；ts_safety_estop_edge_of（estop 边沿映射）；inputdemo（firmware/tests/ 真机载体；ID* console 行）；demo.d4.adcreport / demo.d6.hysteresis（D4/D6 demo app_id）；D4 / D6（demo 代号：ADC 变化上报 / 滞回控制环）。消账：IR2-06 / G3 / estop 沿 prov 化（M2a 遗留）。

- 2026-10-09 · **G2 登记补充**：otabench（firmware/tests/ 真机载体；OTA* console 行）；sysbuild（Zephyr 多镜像构建：mcuboot 子镜像 + 应用镜像同链产出）；SB_CONFIG_BOOTLOADER_MCUBOOT（sysbuild Kconfig：启用 mcuboot 子镜像）；slot1_partition（DT nodelabel 固定名——Zephyr 签名链 dt_nodelabel 约束）；CONFIG_MCUBOOT_IMGTOOL_SIGN_VERSION（Kconfig：签名版本内嵌镜像头）；ota_client.py / ota_serial.py（PC 侧 SMP 客户端，仓外）；otab_wifi.conf（WiFi 凭证仓外片段——otabench 用 ENV 注入而非此文件）。

- 2026-10-09 · **单元 H 登记（G4/G5 批）**：replay_script.tsv（重放脚本文件契约——LLD-A04 §2 输入文件接口载体；行格式 t_ms + link/estop/input/commit）；in:（scenario ch 命名空间前缀：ADC 注入/回显通道，V1 = in:0/in:1）；rep_c / rep_d（replay 脚本会话输出通道——golden 会话 rep_a/rep_b 之外独立注册）；script_lines（agent runner：inputs→脚本行映射 + 配置面校验）；test_00_script_file_session / test_boot_quarantine_refusal / test_08_activate_while_running（本单元三用例）；隔离标记（meta.rollback_count = LIMIT+1 = boot 拒载判据——运行时计数仍如实 LIMIT）。消费：G4（单活跃语义收口）/ G5（模拟深度）。

- 2026-10-09 · **单元 I 登记（MD2：D8/D9）**：linkdemo（firmware/tests/ 真机载体：D9 断链时间线——LD*/D9* console 行）；d8_client.py（deploybench D8 网络驱动：三段部署链 + hb-host 心跳线程〔linkmon 判活——MD1 模式〕+ 动态 slot 链式期望）；demo.d9.linkloss / demo.d8.lifecycle（v1/v2/v2bad 三版本——D8 版本区分经 active_slot 链）；agent/scenarios/（d9-linkloss.json / d8-v1-ramp.json——LLD-A04 §1 场景入库首例）；d9 keep/block/out（D9 APP 判据行族）；LEDC 0% 特例路径（Zephyr pwm_led_esp32 duty 0/100 走 STOP——判据见教训 29）。消费：D8/D9（MD2 demo 阶梯收官两级）。

- 2026-10-09 · **单元 J 登记**：zephyr-upgrade-eval-01（升级评估报告：钉版链对照/P4 阻塞性论证/迁移成本十项/选项 ABC）；Q-30（门⑤：Zephyr 4.5 升级时点 + P4 适配前置）；esp32p4x（Zephyr 板目标：P4 v3.x 硅变体——采购裁决点）；LTS4（= Zephyr 4.6，2027-04 计划）。消费：单元 J（技术栈门）。

- 2026-10-09 · **B2 批登记**：教训 29.5（zenoh locator/Reply API/陈旧声明三教训族）；qprobe.py / qstall_repro.py（仓外调试载体——双向探针/受控复现）；rollback_count 随载恢复（boot_start 装载路径语义补全）。消费：B2（查询面停滞根因批）。

- 2026-10-10 · **DAV1 登记**：WDT-WARN 栈转储（runtime.c 诊断探针：APPMGR 饿死/自旋类缺陷的常设定位面——状态串/优先级/当前线程/全栈文本域字扫描 + 离线 addr2line）；SCCB 忙等（DAV1 根因：上游 esp32 video 驱动内摄像头 I2C 轮询——APP native 内自旋）。消费：DAV1（冻结专项）。

- 2026-10-10 · **升级批登记（单元 J 执行）**：教训 30（v4.5 迁移三教训：west blobs fetch hal_espressif / mapped-partition 兼容串 + appcpu/lpcore 冲突分区 / WAMR autoconf 包含域）；教训 31（P4 批六教训：斜杠限定 target / SDK 单工具链补装 / console 重指 uart0 / WSL /tmp 竞速 + 首启观测编排 / RV32 main 栈 / twister EXTRA_MODULES + 管道假绿）。

- 2026-10-10 · **P4 适配批登记（单元 J 收口）**：p4bench（firmware/tests/ 真机载体：P4 bring-up——P4B* console 行；persistbench 源级复用）；esp32p4_wifi6_dev_kit/esp32p4/hpcore（v4.5 斜杠限定板目标——Waveshare ESP32-P4-WIFI6-DEV-KIT HP 核）；com.tessera.p4b（P4 bring-up demo app_id）；RISCV32（WAMR 板映射新条目——P4 HP 核 RV32，解释器-only 无 invokeNative 面）；board-p4-01.md（P4 bring-up 报告）；gen_p4b_pkg.py（p4bench/persistbench v2 包生成器，仓外——tsap_package 测试根签名 + C 头输出）。消账：J 单元 P4 面（DEC-28 板卡集 P4 首证）；DEC-49② 漏网修复（persistbench v1 包 + 六 bench 兼容串）。

- 2026-10-10 · **H7 移植批登记（构建级）**：h7bench（firmware/tests/ 载体：H7 bring-up——H7B* console 行；persistbench 源级复用）；mini_stm32h743（树内板目标：WeAct Studio MiniSTM32H743 核心板，STM32H743VIT6）；THUMBV7EM（WAMR 板映射新条目——ARM target 在 -mthumb 下汇编期拒，THUMB 分支取 invokeNative_thumb.s）；com.tessera.h7b（H7 demo app_id）；board-h7-01.md（H7 bring-up 报告）；gen_h7_pkg.py（h7bench v2 包生成器，仓外）。消账：DEC-28 板卡目标集第三板开题（构建级绿；真机待板）。

- 2026-10-10 · **P4 PSRAM 批登记**：p4psram（firmware/tests/ 载体：P4 PSRAM 挂接——P4P* console 行；psrambench 源级复用）；SPIRAM_MODE_HEX（P4 专属 16 线 PSRAM 模式——QUAD/OCT Kconfig 不可选）；EXTEMEM 0x48000000（P4 外部 RAM 地址域——S3 为 0x3c000000，探针断言随板改）。消费：board-p4-01 §7 第二项（PSRAM 挂接）。

- 2026-10-15 · **V0.8.0 生态批登记（EC1-5）**：ts_trust（信任根表模块文件名——避开与 ts-trust 模块名混称：存储子域文件，非新框架模块）；ts_trust_part / ts-trust（DT 分区 nodelabel/label——8KB 双副本乒乓）；TS_STORE_TRUST / TS_TRUST_TABLE_MAX（Kconfig）；TS_EVT_TRUST_UPDATED（core.h 事件）；sys/trust-update·trust-get（net 命令）；trust_get/trust_update（Agent deploy 工具）；manifest_summary/install_permission_brief（EC3 呈报面）；boot_pkg_devroot/trust_blob_*/trust_dev_pub（测试夹具）；gen_trust_fixtures.py（夹具生成器，仓内）。消费：Q-43/DEC-60。

- 2026-10-10 · **P4 无线面批登记**：esp_hosted（Zephyr 4.5 驱动族：drivers/misc/esp_hosted_mcu〔RPC/SDIO 传输〕+ drivers/wifi/esp_hosted〔WiFi 管理栈对接〕）；esp-hosted-mcu v3.0.9（C6 协处理器固件仓库——owner Windows EIM 环境构建，工作副本 D:/Software/project/esp_hosted，仓外）；STREAM/PACKET/SW_AGGR（C6 SDIO datapath 三态——Zephyr host 语义 = STREAM，定值入 cp sdkconfig.defaults.esp32c6）；flash_c6.bat / build_c6.bat（C6 构建烧录脚本，仓外 esp_hosted 工作副本）；eh_cp_wifi_sta（cp 工程产物名）；CH340@COM9（owner 的 C6 烧录/console 串口工具）。消费：P4 无线面（半程——数据面缺陷定案登记 decisions）。

- 2026-10-15 · **自检 SC-15**：§1 补登 DEC-39…60 / Q-20…43 索引（区间行——此前批次漏登）；§2 补 V0.8.0 生态批行；§5 补 EC 批 API 族行。

- 2026-10-16 · **§11f 板级/形态/Agent 批登记**：TS_APP_PSRAM_LOAD_BUF / TS_APP_PSRAM_VERIFY_BUF（Kconfig——大档装载/验签缓冲 PSRAM 化，K5）；ESP_SPIRAM_HEAP_SIZE 板级抬升（atk 4MB）；ts_periph 自报面（caps peripherals 数组，F4）；akcodec（atk 外设 uid）；AK7-AK9/AKF1-AKF2/AKC/AKL（atkbench console 判据行族：SD 挂载/peripherals 注册/合成 force/本地 estop 清除/arb 席位）；deploy.post_deploy_check + diag.capture_window（G2/D3 部署后诊断自动回喂）；LnRegistry(persist_path) + TESSERA_LNO_REGISTRY（G1/D1 注册表持久化 + env 重定向）；D-AK4（demo——资源推送消费端）；akbench（第二板载体——dnesp32s3b）。消费：Q-44/DEC-61、plan §11f。

- 2026-10-16 · **F3-1 LCD bring-up 批登记**：ui_lcd.c/h + ak_ui_init/ak_ui_screen/ak_ui_thread_fn（atkbench LCD 呈现面——LVGL 9.5 @ Zephyr glue，消息队列编排单线程纪律，UI 线程 prio 12）；ak_bl_on（XL9555 OP0=0x02/CF0=0x06 bit7 裸 I2C 背光——Awinic 交错寄存器图，与 es8311.c SPK_EN 同图）；AKU1（atkbench console 判据行：LCD+LVGL init）；LV_Z_MEM_POOL 定案（16384 文本面下限——教训 36②）；af31_lcd_console.txt（F3-1 证据）；R10-hal-scalability.md（HAL 扩展性与安全边界——DEC-62⑤）。消费：Q-46/DEC-62、plan §11f F3。

- 2026-10-16 · **F3-2/3 安装闸批登记**：local_confirm/lconf（prov v2 第三尾键 12 对——store）；TS_E_PENDING -13（err.h 结构化中间态）；TS_EVT_PENDING_INSTALL/INSTALL_CONFIRMED/INSTALL_REJECTED/INSTALL_TIMEOUT + ts_pending_evt_t（core.h 四态 payload {slot,entry}）；ts_appmgr_confirm_pending/reject_pending/pending_active/pending_summary + struct ts_appmgr_pend + TS_APPMGR_PENDING_TIMEOUT_MS（appmgr 闸——LLD-ts-appmgr §5c）；ts_app_info_t.pending_slot（加性挂起面）；AKP1-AKP4/AKPC/AKPR（atkbench 判据行：挂起/确认/拒绝/超时 + 本地确认/拒绝）；af3_gate_console.txt（timeout 路真机证据）；TS_E_PENDING/TS_E_PENDING 常量 + pending_local_confirm（agent deploy 面）；gen_ak_prov.py v2 12 对升级（仓外）。消费：Q-46/DEC-62、plan §11f F3。

- 2026-10-16 · **P1-1 APP 间消息批登记**：ts_perm_check_msg + msg_targets 名单 + TS_PERM_OP_SEND + TS_PERM_MSG_TARGETS_MAX/NAME_MAX（hal perm msg:send:<app_id> 名单形态——IR-11 收口，LLD-ts-hal v0.2.5）；ts_appmgr_msg_send/recv/pending + TS_APP_EVT_MSG（0x4D53475A 取件通知）+ TS_APPMGR_MSG_SLOTS/MSG_MAX + ts_appmgr_rt_by_str（appmgr 消息路由——LLD-ts-appmgr v0.9 §5d）；ts_msg_send/ts_msg_recv（natives + Agent NATIVE_WHITELIST/约定块镜像）；test_16（hal 名单矩阵）/test_15（app 双实例路由）/TestMsgNativesMirror（agent 面镜像）。消费：plan §11g P1-1、HLD §3.4。

- 2026-10-16 · **P1-5 S8 串联批登记**：post_deploy_check pass_patterns 判据面（criteria_pass 三态——S8 终止条件）；CreationLoop.repair/S8_REPAIR_MAX/上轮小结回喂复用（creation/loop.py 重构 _converge_and_package 共用体）；TerminalFrontend.repair（门面修复轮入口）；CLI run --serial-port（部署→判据窗→miss 自动修复轮→再部署 ≤2 窗）。消费：plan §11g P1-5、HLD-agent §4 S8（v0.2.2）。

- 2026-10-16 · **P1-3/P1-4 批登记**：ts_power_set/ts_power_get（natives——ts-power 层 wasm 暴露 + Agent 白名单/约定镜像）；counter ✂️（裁剪清账——零消费者实证，HLD §9 对照表首例日落）。消费：plan §11g P1-3/P1-4。

- 2026-10-16 · **P1-2 TLS 批登记（DEC-63）**：zenoh-pico-tls.patch（仓携带补丁——六文件：config.h 宏守卫/Kconfig ZENOH_PICO_LINK_TLS/CMake 特性行+mbedtls 链接/zephyr.h _tls_sock 分立槽/tls_stream.c 4.x 迁移 + BIO 心跳弱钩 z_tls_handshake_progress_hook）；TS_NET_TLS（Kconfig 门控）；TS_PROV_TLS_CA_MAX/CERT_MAX/KEY_MAX（768/768/256——EC P-256 DER 实测 + 余量）；ts_prov_tls_t + ts_store_prov_tls()（独立只读面）；prov 15 对（tls_ca/tls_cert/tls_key）；ts_rd_bstr_len（变长 bstr）；flash_prov --lconf/--tls-ca/cert/key + PKCS8 设备私钥形态；gen_tls_certs.sh（tools/board）；zenohd TLS 并存口 9956（transport/link/tls/* 配置键）。证据 p1_tls_blocker_console.txt（阻断定位）。

- 2026-10-17 · **V0.10.0 R1 断链重连健壮化批登记（DEC-64）**：ts_wdt_grace/ts_wdt_grace_active（core 声明式阻塞豁免窗 + 测试接缝——LLD-ts-core v0.2.3 §5）；TS_WDT_GRACE_CAP_MS（60s 钳制内部常量）；TS_NET_OPEN_BUDGET_MS（Kconfig 15000——open 阻塞体喂狗豁免预算）；test_17_open_grace_wiring（framework.net 接线用例）。消费：plan §11h R1、arm64_rebuild §8。

- 2026-10-17 · **V0.10.0 R2 TLS 单向化批登记（DEC-64②）**：NET_CONTEXT_RCVTIMEO（Zephyr Kconfig——TS_NET_ZENOH select，pico SO_RCVTIMEO 轮询设计硬性前提）；NET_MAX_CONTEXTS 12→4（atkbench 板级——RCVTIMEO 静态面 140B 溢出实证）；r2_tls_oneway_root_cause.txt（复现/TCP 解剖/根因链/黑洞 A/B 判据）。消费：plan §11h R2、一四二④ 根因闭合。

- 2026-10-17 · **V0.10.0 R4 健壮性小项批登记（DEC-64③）**：nvd_demo.py 参数化面（--window/--node/--cube/--port + 仓库根路径派生）；zenohd-tls.service（systemd 用户单元—— linger 常驻/失败自启/`\"` 转义语义）；checklist ⑦ 板型口径行。消费：plan §11h R4。

- 2026-10-18 · **R5 UART 交互终端需求登记（owner）**：R5（plan §11h——无外设板本地交互源：F3 confirm/reject + CG3 席位 + F2 本地清除的 UART 终端载体；设计批门③未排期）。消费：owner 2026-10-18 指令。

- 2026-10-18 · **V0.10.0 R3 批登记（DEC-64④）**：WAMR /64 invokeNative 根治（GENERAL C thunk × 寄存器分类路径契约错配——INVOKE_NATIVE_GENERAL=0 + 宿主映射 AARCH64/X86_64 + -Wa,--noexecstack）；垃圾常数 0xaa0803f0a9467bfd 归因闭合。消费：plan §11h R3、arm64_rebuild §7。

- 2026-10-18 · **V0.11.0 R5 设计批登记（DEC-65）**：LLD-ts-interact.md（新 LLD——单 UART 三合一/ts 命令集 v1 七条/TS_INTERACT 门控）；tsi 判据行前缀（`[tsi] <cmd> rc=`）。消费：owner 2026-10-18 泛指令、plan §11h R5-U。

- 2026-10-18 · **V0.11.0 R5-I 批登记（DEC-65）**：src/interact/ts_interact.c/.h（薄命令层——ts_interact_confirm/reject/arb/estop_clear/log_level 核心面 + SHELL 门控命令表）；framework.interact 套件（testcase 3 用例 + INTERACT DONE 判据行）；TS_INTERACT/TS_INTERACT_LOG_LEVEL（Kconfig）；r5_interact_console.txt（真机证据）；[tsi] 判据行族；build_prov12 栈越界缺陷根治（cap 契约 + pb 256——app/interact 两套件同修）。消费：plan §11h R5-I、DEC-65。

- 2026-10-18 · **V0.11.0 R5-V 僵尸自愈收口登记（DEC-65）**：zp_transport_is_open（pico 补丁新访问器——api.c 定义 + primitives.h 声明，传输态本体 liveness，补丁六→九文件 pristine 可重放）；is_up 三判据（执行器任务活性 ×2 + 传输态——1.10.1 执行器模型 zp_*_task_is_running 语义漂移根因）；NET_CONTEXT_SNDTIMEO（TS_NET_ZENOH select + tcp_zephyr.c SO_SNDTIMEO 对称补丁）；serial_capture.py（单读者抓取——复位+抓取同进程纪律；仓外驱动 ~/project/logs/ 惯例）；r5v_zombie_heal_console.txt（僵尸破案 + 路由器重启注入自愈判决 + NVD 复验）。消费：plan §11h R5-V、LLD-ts-net v0.4.7。

- 2026-10-18 · **V0.11.0 R5-V 真机批收口登记（DEC-65）**：CONFIG_ZENOH_PICO_THREADS_NUM=2（atkbench 板级——pico 预分配 pthread 栈池 4→2 槽，map 实证 system.c 32KB→16KB，执行器单线程设计）；CONFIG_SHELL_STACK_SIZE=4096 / CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE=4096 / CONFIG_STACK_SENTINEL=y（双栈真机定案——confirm 链 EXCCAUSE 0 野跳根因 + sysworkq 建链窗溢出 SENTINEL 点名）；stage_commit 包身份提取（pkg.c——staged manifest app_id/app_ver → ts_app_info_t/[tsi] verdict 行保真）；flash_prov esptool≥5 二进制名解析 + 写前 erase-region 4KB + --offset 0x5f0000（ATK prov 分区）纪律；r5v_verdicts_console.txt（F3 终端确认/拒绝四判据 + NVD 复验 + 双栈定案）。消费：plan §11h R5-V、LLD-ts-interact v0.2、LLD-ts-appmgr v0.9.2。

- 2026-10-18 · **V0.11.0 D2 计划/进度 MCP 外显登记（DEC-65⑤）**：Task.progress（common/tasks.py——运行体结构化进度面，snapshot 同源携带）；note_loop_progress（domain/app_chain.py——创作循环事件→进度键单一映射源：plan/round/loop_state/repairing/evidence_count/last_evidence/final）；task_progress（platform.py MCP 工具——{task_id, state, progress}，auto 类）。消费：plan §11h D2、LLD-A01 v0.x（task_* 平台面）。

- 2026-10-19 · **V0.12.0 Agent 协同批立项 + MCI 需求登记（DEC-66）**：MCI（Multi-Channel Interaction——三层渠道模型：Transport × Renderer × Interaction）；R11-multichannel-interaction.md（四参考项目代码级调研——opencode/codex/gemini-cli/aider）；Q-48（MCI 定案 + W1 web 客户端选型 + D4 allow-session 审批语义 + SSE 推送面——门③呈递）。消费：plan §11h G 表、DEC-66。

- 2026-10-19 · **V0.12.0 D7/D4 交付 + A10/A11 落稿登记（DEC-67）**：QuestionBroker/Question/sys_pending_questions/sys_answer（gateway/questions.py + platform.py——问询 MCP 一等实体，单次应答契约/枚举 fail-closed/超时 default）；plan_confirm（app_develop 参数——plan 事件经问询实体确认，abort = TA_E_POLICY detail.state=ABORTED）；CreationLoop._emit 异步感知；HookChain/HookRule/HookVerdict/parse_rules（gateway/hooks.py——pre 裁决 deny/observe，prefix* 前缀，首匹配）；allow-session（sys_approve decision 三维——会话域记住集 _session_allowed 不落盘）；LLD-A10-mci-channels.md / LLD-A11-web-client.md（v0.1 首稿）。消费：plan §11h G 表 v1.122、DEC-67。

- 2026-10-19 · **V0.12.0 W1 web 客户端交付登记（DEC-67②）**：agent/web/（index.html/tokens.css/app.css/mcp.js/app.js——零构建 ES modules 前端；tokens = 语义角色层深浅色；mcp.js = 手写 MCP-over-HTTP 客户端含 mcp-session-id 维持 + SSE 帧兼容解析）；gateway/web.py（WEB_DIR/mount_web/build_frame 差分帧/event_stream SSE 流——TaskRegistry.list_tasks 消费）；run_server http 分支（共享 AppContext 组装——/web + /events + /mcp 同源）；判据行着色正则表（VERDICT_RULES——零改写仅样式）。消费：plan §11h G 表 v1.123、LLD-A10/A11、DEC-67。

- 2026-10-19 · **V0.12.0 D5 决策链回放器交付登记（DEC-67①）**：audit_replay.py（load_timeline/render_timeline——持久审计 JSONL 时间线，条目语义派生 sys_approve=审批/sys_answer=问询，STATE_GLYPH）；replay CLI 子命令（--day/--task-id/--tool/--limit/--json）；sys_timeline（platform.py MCP 工具——W1 时间线 tab 同源）；W1 时间线 tab 点亮（tl-load 按钮加载）。消费：plan §11h G 表 v1.124、DEC-67、R11 §8.5。

- 2026-10-19 · **DEC-68 通用化三需求登记**：BV1（板卡验证域——Board Validation Verifier + 板卡画像面；首任务 P4 判定批实测）；R12（板卡选择/硬件设计调研）；R13（结构件 3D 打印设计调研——DEC-33 结构件域前哨）。消费：plan §11h H 表、DEC-68。

- 2026-10-19 · **V0.13.0「Agent 自主化批」立项登记（owner：「v4.5.0 还需等待一周——重点放在 Agent」+ DEC-68 执行注记修订）**：BV1 提前（首任务改现役板自验 atkbench/xiao，P4 判定降第二任务随 v4.5.0 平移批）；A3（SSE 事件总线直推 + W1 多任务视图）；A5/D6（MCP 客户端——外部工具桥接默认 strict + [mcp_clients]）；A4/D4b（post 观察钩子）；R12/R13 并入调研单元。消费：plan §11h I 表 v1.126、DEC-68 注记修订。

- 2026-10-19 · **V0.13.0 BV1-D 板卡验证域设计批登记（DEC-68①）**：LLD-A12-board-validation.md（v0.1——确定性检查流水线定性〔不硬套 CreationLoop；DEC-33 原则面继承：结构化证据/事件审计同源/VerifyOutcome 同型〕；板卡画像 schema agent/boards/*.toml〔serial/flash/boot/zenoh/caps/smoke/build 七节声明式——R12 能力目录种子〕；检查项目录 v1 = C0 构建/烧录前级 + C1 串口在场 + C2 flash 身份 + C3 boot/console + C4 zenoh 连通 + C5 caps 消费 + C6 部署 E2E 冒烟；SKIP 双型〔派生 vs 声明〕+ DEGRADED 判定；board_validate MCP strict + validate CLI；板态变更披露合同〔C6 探针驻留不自动还原——画像 smoke 节即显式授权〕）。消费：plan §11h I 表、DEC-68①。

- 2026-10-19 · **V0.13.0 BV1-I 板卡验证域实现登记（DEC-68①）**：domain/board_validation.py（BoardProfile 七节画像 fail-closed 装载/CheckResult-BoardReport 双形态/BoardTransport 协议/LiveTransport〔esptool 双形态 chip 解析 + 仓相对路径解析 + C6 ctx 装配〕/validate 流水线——C1-C6 + SKIP 双型派生链 + stop_on_fail + progress_cb）；agent/boards/atk-dnesp32s3b.toml + xiao-esp32s3.toml（画像入仓）；board_validate（firmware.py MCP strict+spawn+D2 progress）/ validate（__main__.py CLI 退出码 0/1/2）；test_board_validation.py 33 用例（FakeTransport 全矩阵）。消费：plan §11h I 表 v1.128、LLD-A12 v0.1.1。

- 2026-10-19 · **V0.13.0 BV1-R 真机自验登记 + 板级缺陷新登记（验证域首战抓获）**：atk 全链 C1-C5 全 PASS 稳定复现（boya 16MB 身份/CONNECTED/akn-akc/caps slot_pool=2048KB 实测校准入画像）+ xiao 板不在场形态按设计工作；**新缺陷 = 部署分块突发 → esp32_wifi_adapter ENOMEM（R5-I 同象）→ rx_q[0] 栈溢出 FATAL 崩机**（确定性复现——新鲜板态同崩；板侧串口全文实抓；C6 如实 FAIL 不掩蔽——降级分块不作为）；证据 docs/evidence/bv1_atk_console.txt + bv1_c6_crash_console.txt。板级专项候选：R5-I「DRAM 系统性重平」残余 + rx_q 栈面新形态。消费：plan §11h I 表 v1.128。

- 2026-10-19 · **DEC-69 web 渠道产品反馈六点登记（owner）**：界面观感/普通用户文案与受众定位/对话式交互（用户消息入流 + Agent 状态指示）/多端响应式/左侧设置栏/双模式需求输入（开发者全细节含 log；普通模式 = LLM 需求澄清阶段——创作循环前置能力增量，spec 门不变）。落点 = W2 web 渠道重塑（plan §11h A3 范围扩充 + W1 验收 UX 反馈四条），设计批门③待呈递。消费：DEC-69、plan v1.130。

- 2026-10-19 · **V0.13.0 FIX-1 板级部署崩机专项登记（BV1-R C6 破案）**：NET_RX_STACK_SIZE 4096（atkbench——rx_q 线程栈缺省 1500B 被部署突发压穿 = FATAL 根因）；STATIC_TX/SPIRAM heap 两轮否定实验（教训 41——驱动/hal 双层 TX buffer Kconfig 映射存疑，登记上游核实）；prov lconf 1→0 复原（安装闸 F3 残留撤守）；deploy.py chunk 租约瞬断自愈（lease required → force renew 同 idem 重发）；全链 C1-C6 PASS + twister 17/17 + agent 263+2s。教训 41/42 入册 dev-env v2.30。消费：plan §11h FIX-1 行 v1.132、dev-env v2.30。

- 2026-10-19 · **DEC-70 通用内存规划需求登记（owner）**：MP 专项（① 跨芯片构建期内存审计/规划程序——栈/池/堆静态账核对 + 溢出预警 + BV1 画像内存维度；② 最低内存需求基线——按配置档 DRAM/PSRAM/FLASH，实测推导）；atk map 重平合流为首应用。消费：DEC-70、plan §11h MP 行 v1.133。

- 2026-10-19 · **V0.13.0 MP 通用内存规划专项登记（DEC-70/71）**：LLD-A13-memory-planner.md（v0.1——构建期确定性审计定性〔BV1 同族非 LLM 创作任务〕；跨芯片 = GNU ld map + Kconfig .config 两芯片无关接口；三层账本 = region〔占用/保留窗/余量——IRAM 镜像窗不入可用〕+ 具名对象〔input 三行式解析 + 符号归并 `_k_thread_stack_*`/`kheap_*`/`_k_mem_slab_buf_*`/`thread_stack_area`〕+ config 内存意图账〔\*STACK_SIZE/\*HEAP\*/\*POOL\* 全量扫描〕）；规则目录 v1 RULES_VERSION=1 = R0 声明≠生效〔prj.conf 声明 vs .config 生效对照〕/ R1 NET_RX_STACK≥4096〔FIX-1〕/ R2 SYSTEM_WORKQUEUE≥4096〔SENTINEL 案〕/ R3 SHELL≥4096〔EXCCAUSE 0 案〕/ R4 wifi TX 池峰值 >堆 50%〔ENOMEM 噪声案，WIFI_FRAME_EST_BYTES=1600〕/ R5 TLS 堆≥65536〔P1-2 -80 案〕/ R6 region slack≥2048 / R7 ESP32_WIFI_STATIC_TX_BUFFER 观察〔教训 41〕；memory_audit（domain/memory_audit.py——AuditError/MemObject/Finding/MemoryReport 三态 overall + CLI `tessera-agent memory-audit` 退出码 0/1/2 + MCP memory_audit confirm 本地只读）；夹具 map_atk_excerpt.map（真图摘录锚定）；docs/memory-baseline.md v0.1（三档实测总账——最小 net PASS/标准 PASS/全外设 WARN-R5 接受态）；pkg.c stage_commit WAMR=n 门控（M7 遗留断链修复）；netbench/deploybench 板级 conf 防御双 4096 + 堆重平（139264/131072）+ atk TX 上限 16。消费：plan §11h I 表 v1.134、LLD-A13、decisions DEC-71。

- 2026-10-19 · **V0.13.0 W2-D web 渠道重塑设计批登记（DEC-69/W1 验收反馈输入）**：LLD-A14-web-reshape.md（v0.1 门③呈递——MCI 三层变动定位〔Transport 不变/Interaction 加事件总线/Renderer 重塑〕；EventBus 零依赖层〔common/events.py——sync publish 线程安全/每订阅者队列 512 慢消费者 resync/环形缓冲重放〕；registry/brokers 发布钩子 bus=None 零行为变化；/events v2 = 快照+Last-Event-ID 续传+15s 心跳；Agent 状态灯派发表〔server 侧单源——task.state × loop_state × pending 派生 11 态〕+ last_activity_ts 活动心跳；plan 项 active 态打卡；文案层 web/copy.js 术语映射〔判据行保真合同不变——普通模式叠加摘要层，日志抽屉逐字原文〕；设置栏 localStorage〔主题/模式/密钥路径/计划确认〕；响应式三档 1024/768 断点；时间线 tool 过滤+尾随；diag 帧纪律；**双模式需求澄清域** domain/clarify.py〔缺口分析→澄清轮≤3/问询≤8→spec 合成→NV-2 spec_check 门不变→确认交棒 app_develop——app_clarify MCP spawn 面〕；sys_tasks 多任务工具；tokens v2 elevation/动效 token 化）。规模重估 ~5 单元（W2-1 基建/W2-2 呈现层/W2-3 双模式/W2-4 收口）。消费：plan §11h I 表 v1.135、DEC-69。

- 2026-10-19 · **V0.13.0 W2 实现批登记（DEC-72 门③过裁）**：common/events.py（EventBus——publish 线程安全/subscribe 句柄 _Subscription〔replay+__anext__+close〕/resync 慢消费者策略/环形缓冲重放）；TaskRegistry bus 钩子（task.created/state/log + note_progress 单一进度入口 + last_activity_ts）；QuestionBroker（question.opened/closed）/ApprovalBroker（approval.requested/decided）钩子；AppContext.events 装配接线（__post_init__ attach）；gateway/web.py v2（build_snapshot/build_tasks_frame/derive_phase 11 态单源/event_stream 直推+Last-Event-ID 续传+15s 心跳+10s 对账兜底/_event_frame 映射）；sys_tasks（platform.py）；web/ 五文件 v2（index.html 三栏+设置抽屉+任务栏/app.js 对话流+状态灯+心跳+双模式 composer/copy.js 文案层 PHASES+TERMS+phaseSummary+heartbeatText/tokens.css v2 elevation+双主题+手动覆盖/app.css 响应式三档 1024/768）；domain/clarify.py（clarify_and_develop 五步——GapAnalysis/ClarifyQuestion/SpecDraft FunctionModel 可剧作 + SPEC_REPAIR_MAX=1 门修复 + restart=TA_E_POLICY state=RESTART + CLARIFY_FAILED 结构化）；app_clarify（firmware.py MCP confirm）；tests test_events.py 6 + test_clarify.py 5 + test_web.py v2 迁移。消费：plan §11h I 表 v1.136、LLD-A14 v0.2、LLD-A11 v0.2、DEC-72。

- 2026-10-19 · **V0.13.0 A5+A4 交付登记（owner 泛指令续推）**：LLD-A15-mcp-clients-and-post-hooks.md（v0.1）；gateway/mcp_clients.py（MCPClientDomainPack——sanitize_server/_client_for 三传输〔url/command/_inline 测试面〕/list_external_tools/call_external_tool 60s 超时；x_<server>_list/x_<server>_call 前缀命名空间；strict 工具体双闸）；config AgentConfig.mcp_clients（[mcp_clients] 表解析）；compose 按配置注册；gateway/hooks.py post 面（HookRule.when=post 仅 observe/HookChain.post 全匹配/HookChain.summarize 400B 截断）；platform audited finally 段 hook.post 事件外发；test_mcp_clients.py 6 + test_hooks.py +3。消费：plan §11h I 表 v1.137、LLD-A15、DEC-12 v1.1。

- 2026-10-19 · **V0.13.0 R12/R13 调研交付登记（DEC-68②③）**：docs/research/R12-board-selection.md（v0.1——能力目录 schema v0 = BV1 画像超集 `[hardware]` 节〔soc/ram_kb/psram_kb/flash_mb/peripherals/price_band/availability/power_ma/form——每字段机械可校验来源纪律〕+ 判定链五步〔需求抽取→目录匹配→内存可行性硬门〔memory-baseline 消费〕→策略排序→BV1 实测闭环〕+ 硬件设计建议边界〔模块级可交付/原理图级边界外〕）；docs/research/R13-structural-design.md（v0.1——结构件域定性 = DEC-33 CreationVerifier 第三域形态 + CadQuery 倾向路线对比 + 可打印性检查目录 v0 七条〔壁厚/悬垂/桥接/公差/流形闭合/打印行程/薄壁——网格级机械检查〕+ `[physical]` 画像节 fail-closed + StructuralVerifier compile/check/package 同构）。消费：plan §11h I 表 v1.138、DEC-68。

- 2026-10-19 · **DEC-73 硬件定向 + HW-D 设计批登记**：LLD-A16-hardware-targeting.md（v0.1 门③——clarify 前置硬件定向槽 S0 四分支〔需求提及绑定/目录外如实告知/未提及在线发现确认〔get-info board=CONFIG_BOARD 自报消费 + 画像 [hardware].board_target 映射〕/不清楚联网选型调研〕；web_search 工具面 provider 链〔auto=TAVILY_API_KEY 在位→Tavily else ddgs 兜底；config [web_search]；none=离线结构化〕；S0c 调研 agent = PydanticAI + web_search + 内存基线机械预筛 + 选型记录推定态标注；诚实边界 = 机械门只在本地目录内生效）。消费：plan v1.139、DEC-73、R12 判定链。

- 2026-10-19 · **DEC-73 三裁决修订登记（LLD-A16 v0.2）**：QwenPaw websearch 模式采纳（SearchProvider ABC/TavilyProvider keyless 匿名 REST〔X-Tavily-Access-Mode: keyless〕/工厂未知值 raise；弃 ddgs）；硬件定向流程 v0.2（需求分析先行→是否有板三路→Zephyr 收录检查→原理图协作路径→能力缺口外接或换板；在线默认绑定废弃）；BV2 新板适配域（P4 playbook Agent 化 + BV1 判据链 + 原理图人机协作）。消费：plan v1.140、DEC-73 修订。

- 2026-10-21 · **HW-4「Agent 级硬件事实全面优化」待开发项登记（owner 扩令：「应该在Agent层面全面进行优化」——W2 验收 LED 缺陷记为待开发项）**：LED 缺陷全链根治于 Agent 层五面——① 板卡画像引脚级事实节（板载 LED/按键/外设→通道域×实例映射，每字段机械可校验来源〔DTS/原理图/实测判据行〕——R12 来源纪律延伸；atk 画像补 LEDB=IO4∈akpwm 实证）；② 创作链硬件事实注入（app_develop 提示携带目标板可用通道/实例/约束面——LLM 不再凭空假设「gpio 0 = 板载 LED」）；③ caps×画像机械核对门（manifest 申请通道实例画像无物理绑定→装前拒 TA_E_POLICY——编译门/判据门双盲区〔soft-pass/hard-invalid〕机械补位）；④ 判据生成硬件感知（S8 判据行引用通道须过物理存在性核对）；⑤ 部署后硬件回执诊断（WRITE REJECTED 族聚类→自动诊断回喂修复轮——D3/hook.post 同源消费）。快改方案（重生成 app 加 pwm cap）owner 裁废弃——治理根因不做单点演示修补。落点 = plan §11h I2 表 HW-4 ~1 单元；LLD-A16 v0.3 门③补呈随开工。消费：plan v1.141、AGENTS 一五〇。

- 2026-10-21 · **V0.13.0 HW-1..4 实现批登记（owner「完成V0.13剩余部分」）**：gateway/websearch.py（SearchProvider ABC/TavilyProvider keyless〔X-Tavily-Access-Mode: keyless〕+ Bearer 升级 + 401/429/432 回退 + 工厂 raise + scrub_query 凭据打码）；domain/hardware.py（画像目录/caps×画像机械门/【目标硬件】段/Zephyr 收录检索〔board.yml 归一化匹配〕/选型内存预筛 512KB 口径/能力缺口核对）；domain/clarify.py S0 硬件定向槽（mention 恰一命中绑目录/Zephyr 收录→BV2_QUEUED/未收录→SCHEMATIC_REQUIRED/主问询+research 分支）+ 能力核对（外接/换板/如实标注）；domain/firmware_creation.py face_check 声明-调用一致性门（_NATIVE_CAP_MAP gpio/pwm/adc/av/fs/kv/msg/power——log 豁免 = TEST 语义 IR-16，net/time_ms 豁免）；domain/board_validation.py [hardware] 节 v1.1（HardwarePin source 必填 + HW_PHYSICAL_DOMAINS）；domain/app_chain.py 直填 spec 自动追加【目标硬件】；tools_net/deploy.py post_deploy_check 硬件写拒扫描 + 判据降级；domain/firmware.py web_search MCP（confirm）+ hardware_gate（deploy_push_app/app_deploy 审批前）；config [agent] board_profile + [web_search] provider；boards/atk-dnesp32s3b.toml [hardware] LEDB=pwm:0 实证（source = 原理图+overlay+w2_hb 168 对 REJECTED 实测）。**LED 缺陷根因精化**：缺陷包 caps 仅 log:write:0 而源码调 ts_gpio_write——第一层 = 声明缺失（TEST 自动授予仅 log，runtime.c IR-16）；物理缺绑定 = 第二层（验收记录归因精化）。真像锚：缺陷包 caps×atk 画像 → gpio REJECT/pwm PASS；face_check 拦未申报 native。消费：plan v1.142、LLD-A16 v0.3。

- 2026-10-21 · **V0.13.0 BV2-D 设计批 + 版本收口登记**：LLD-A17-board-adaptation.md（v0.1 门③三决策点呈递——接入件产出形态/C0 解锁范围/v1 裁剪；两路径 = 收录板接入件五件套〔板定义定位/五分区 overlay/板级 conf〔memory_audit R0-R7 机械复核〕/WAMR 架构映射/prov 通道〕+ BV1 bring-up 两级〔构建级 C0 + 板级 C1-C6〕→ 画像入目录；未收录板原理图人机协作〔移植清单 + 协作 DTS 待确认态〕）；HLD-agent **v0.2.3 深度修订**（§1 MCI 三层四渠道 + 四铁律/§2 A10 + 交互域 + 工具面九增/§4 S9-S12/§5.4 安全面六增/§7 现状注记/§9 裁剪更新）；README 仓库地图对齐（agent 343/design A00-A17/docs 行）；**tag fw-v0.13.0**（附注式本地，push 待 owner）。V0.13.0 = 16 单元全 ✅。消费：plan v1.142、AGENTS 一五〇。

- 2026-10-21 · **V0.14.0 P4 联网批立项登记（owner：「先尝试解决P4的wifi问题，我将帮你接入esp32p4开发板；esp32s3已经被移除」）**：plan §11h J 表 v1.143（P4-W0 环境备料/P4-W1 C6 对齐+bring-up/P4-W2 数据面判据矩阵+树内根治）。**攻击面变更定案（树内盘点）**：v4.5.0-rc1 树内全新代 esp-hosted-mcu 驱动全家桶——drivers/misc/esp_hosted_mcu（transport：SDIO/SPI + buf-config TLV tag 0x1b 协商〔SW_AGGR 四字节 stride walk / STREAM byte-tight / PACKET / 缺 tag 兜底 byte-tight〕）+ drivers/wifi/esp_hosted_mcu（WIFI_ESP_HOSTED_MCU——DT espressif,esp-hosted-mcu-wifi）+ drivers/bluetooth/hci/hci_esp_hosted_mcu.c；零外部模块（west 无 esp-hosted 条目仍可构建）；waveshare esp32p4_wifi6_dev_kit DTS 已接新绑定（sdhc1 SDIO 4-bit@40MHz CLK18/CMD19/D0-3=14-17 + reset gpio1 22 + BT HCI 节点）。**病灶承接（教训 32⑤）**：2026-10-10 旧批 = 旧 esp_hosted 驱动（Arduino protobuf 代）+ C6 v3.0.9 STREAM 强制绕行（CONFIG_EH_TRANSPORT_CP_SDIO_MODE_STREAM）→ RPC 控制面通 / DHCP 数据面死 3/3；上游 #121767/#121772 域。**新攻击计划** = 新驱动 × C6 stock rel-3 default（SW_AGGR）原生协商——撤销 STREAM 强制；E0 无板构建面 / E1 板到 C6 重烧 + P4 烧录 + 判据链〔SLC ready→buf-config→握手→wifi_connect→DHCP〕/ E2 数据面矩阵〔DHCP/ping/TCP/zenoh CONNECTED/BV1 C1-C6〕+ 树内自研根治兜底（可 upstream）。**板态域变更**：esp32s3（atk）物理移除——atk 画像维持不删（BV1 C1 如实 FAIL 按设计工作）；依赖 atk 的板级面全部转 P4；riscv64-zephyr-elf 工具链补装（教训 31②）。消费：plan v1.143、AGENTS 一五一、教训 31/32。

- 2026-10-21 · **V0.14.0 P4-W1 判决 PASS 登记（owner「我已经接入了开发板」——当日首跑即绿）**：p4wifibench 入仓（firmware/tests/p4wifibench——判据行驱动 CONNECT/DHCP/UDP RTT/ALIVE + net shell；凭据 Kconfig 构建期注入〔/tmp conf 600——PSK 红线，west 错误回显泄露面教训：命令行不携凭据〕）；tools/board/p4w_udp_echo.py（host 侧 UDP 回声对拍器）；CH343 身份链（by-id 5B90122202 / GD 16MB c8:4018 / esptool RTS 自动复位链免人工）；判据链 = CONNECT OK → DHCP OK ip=192.168.2.29 → UDP RTT 5/5（host 双源独立对拍）→ ICMP 3/3 0% loss（net ping -c 3——该树选项在前语法）→ ALIVE 稳定 × 两 boot 复跑。**结论 = 教训 32⑤「上游驱动 RX 数据帧缺陷」在新代 esp_hosted_mcu 驱动上不复存在**；C6 stock 重烧降级可选加固（buf-config TLV × 现存 STREAM 固件原生协商）。build 期三坑：应用 Kconfig 须 source "Kconfig.zephyr"（否则全树符号 undefined）/ 4.5 wifi_mgmt 符号 = NET_REQUEST_WIFI_CONNECT（INTERFACE_CONNECT 不存在）/ zsock_recv 4 参（flags 必传）；net_if_ipv4 形状（unicast 内联数组 / gw 裸 in_addr）。证据 docs/evidence/p4w1_console.txt。消费：plan v1.144、AGENTS 一五二。

- 2026-10-21 · **V0.14.0 P4-W2 收口登记（owner「按照计划完成V0.14.0的开发」）**：firmware/tests/p4bench/p4net.conf（EXTRA_CONF 网络面：TS_NET/zenoh + esp_hosted_mcu + POSIX pthread 族 + NET_MAX_CONTEXTS 4 + 堆 49152〔4096 缺省 = z_open rc=-78 _Z_ERR_SYSTEM_OUT_OF_MEMORY 实测；131072 = sram0_0_seg 溢出 79968B → 48KB 余量推算〕）+ p4bench CMakeLists 凭据文件注入面（P4BENCH_CREDS_FILE include——west 回显泄露面教训，命令行不携凭据）+ main.c P4BENCH_NET 块（WiFi/DHCP 先行 + P4W2 判据行）；agent/boards/p4-wifi6.toml（BV1 画像——[hardware] 在位引脚未采 = HW-4 门生效形态）；agent/demos/P4W/（探针 app.c log-only + fixture 测试根签名包 + gen_p4w_probe.py 入仓生成器）；tools/board/p4w_udp_echo.py。**信任链实证**：自造测试钥被 TEST 板如实拒（status=-9 TS_E_INVALID_SIG；板侧 sm 指纹 pk0=f084a4e5 = verify.c 编译内固定测试根 = agent/tests/fixtures/ts-test-root——TEST 构建工厂根非 prov pk0 纪律入册）；**compile_app_c 存量缺陷修复**：required_exports 从不传导出旗标（单文件路径导出面恒缺）→ _run_clang_files exports 接线 + 1 用例。**BV1 C6 语义补丁**：激活后无条件暖复位（CG7「激活暖复位 ACTIVE」正典——同 app 重部署场景条件复位漏判）+ RTS 脉冲复位助手（教训 42 DTR/RTS 纪律）。**FIX-2 候选登记**：探针 meta 下板复位循环（~15-20s 周期交替 probe/P4B；P4B meta 稳定 90s+）——疑似健康回退族/bench-vs-app 互扰，root cause 随板级专项。证据 docs/evidence/p4w2_console.txt。消费：plan v1.145、AGENTS 一五三、tag fw-v0.14.0。

- 2026-10-22 · **V0.15.0 立项 + FIX-2 根治登记（owner「我已经完成review，请你继续开发」——DEC-74 BV2 门③三裁决按建议值；V0.14.0 四提交 + tag fw-v0.14.0 随令推送）**：**FIX-2 板载插桩破案**——root cause 三连（同根 WAMR 调用契约）：① appmgr/runtime.c call0() 以 argc=0 调 wasm_runtime_call_wasm，WAMR 契约 argc ≥ function->param_cell_num（wasm_interp_classic.c:7397）——约定签名 app_tick(int ctx)（1 cell）每 tick 必陷 "invalid argument count 0, must be no smaller than 1"；无参 fixture tick（app_tick(void)）恒过 = sim 套件/bench 全绿、带参 app 必死（V0.4 起存量，首例带参 tick app = P4 探针）；② WAMR 实例异常位跨调用存活（wasm_call_function 以异常位判成败）——一次 trap 毒化后续全部调用（health_ping 实际执行成功亦判败）；③ health_probe 不设指令配额（继承上次调用余量）。**故障闭环** = tick 每陷 → health_fails 累积 → 3 败健康回退 → meta 翻槽（TS_TEST 构建静默无打印不复位——slot.c 两分支皆 #if !defined(CONFIG_TS_TEST)）→ app 线程退出 → APPMGR 喂狗停 → 巡检 system_fail(TS_FAIL_WDT(1)) → noinit 0x00020001 → task_wdt 复位（rst:0xc）；「meta 交替 probe/P4B」= 每次 C6 重跑重新激活探针；bench 包无参 tick 健康恒过 = bench meta 稳定。**修复**（runtime.c 23+/15-）：call0 撤除、tick 经 call1 带 ctx（argc=1 ≥ 任意 ≤1 参 cell；WAMR 对无参钳制不扰——bench 零变化）+ call1 失败 wasm_runtime_clear_exception（毒化破除）+ health_probe 显式 INSTR_TICK 配额/argc=1 带 ctx/失败清异常（返回值经 argv[0] 回传语义保持）。**顺带 agent 抓取面修复**：post_deploy_check 增 reset_before_capture（缺省 False 行为不变；True = 单端口会话 reset_and_capture）——BV1 deploy_smoke 弃「_serial_reset 关口 → capture_window 再开」两段式（CH343 快速关/开竞态 → 抓取窗零字节 no_verdict 假 FAIL，真机实测复现），_serial_reset 方法撤除；+1 用例（旗标路由断言）。**板上闭环**：探针 INIT + ALIVE t=11s 首印、tick 连跳 fail 恒 0、零复位零回退、槽乒乓按设计（probe@slot1）；bench 同固件 P4B PASS；**BV1 C4+C6 PASS——P4 板 C1-C6 全链首次全绿（93.3s）**。**入册事实**：meta 双副本乒乓快照纪律（单读 copy0 会误判「meta 未变」——REC_HDR seq/len/crc16 + copy1@stride）；P4 烧录布局（ROM 自 0x2000 简单引导 app〔CONFIG_BOOTLOADER_OFFSET_IN_FLASH=0x2000〕；west flash = 单产物 write_flash 0x2000 zephyr.bin；误写 0x0 = 0x2000 处真 app 被镜像中段字节覆盖 → ROM "invalid header: 0x028777b3"〔即镜像 0x2000 偏移内容〕→ HP WDT boot 循环；恢复 = erase_region 0 0x2000 + write_flash 0x2000）。**DEC-74** = LLD-A17 §5 三决策按建议值（接入件 agent/adapt/ 工作区/C0 流水线内临时解锁/v1 收录板全链+未收录清单）+ V0.15.0 立项（§11h K 表）。证据 docs/evidence/fix2_p4_probe_console.txt。消费：plan v1.146、AGENTS 一五四。

- 2026-10-22 · **V0.15.0 BV2-I 交付登记（DEC-74 门③三裁决落地——LLD-A17 §2/§3/§4 实现收口）**：`domain/board_adapt.py` 新建——**收录板路全链**：locate_board（hardware.check_zephyr_inclusion 同源归一化双向子串匹配；未命中 = AdaptError stage=locate 转未收录路）/ plan_partitions 布局模板族（键 = flash_kb：16384 = **P4 playbook 真锚**〔carve 0x7e0000/prov 4KB/meta 8KB/slot 32KB×2/noinit——测试与在树 p4bench overlay 逐偏移对拍〕；8192 = 8MB 保守兼容同构；4096 = 最小档 slot 减半 16384；未知尺寸 fail-closed 不发明）/ render_overlay（P4 playbook 同构模板：/delete-node/ slot1 + ts 五分区 mapped-partition + fw-b 预留，擦除块对齐 assert）/ render_board_conf（内存初值家族 + _WAMR_ARCH_NOTES 架构表〔riscv main 栈 8192 = P4 实测深帧口径/xtensa/arm 4096〕）/ prov.json（教训 39 offset 陷阱注记随行）/ workorder.json 工单 + c0_preflight 机械预检（齐备性/擦除块对齐/越界/slot 尺寸耦合——C0 真实构建 = 流水线会话内执行，DEC-74② 不全局解锁）。**install_profile owner 闸**（DEC-74①：owner_approved=False 恒拒零落盘；草稿推定态如实标注——实测值待 bring-up 回填；**BV1 load_profile 可装载 = clarify 分支 A mention 绑定同源消费——工单两端闭环测试**）。**MCP `board_adapt`**（strict——写 agent/adapt/ 工作区；mode=included/schematic；审批呈现 + spawn 长任务 + note_progress D2 同汇）。**未收录板路**：migration_checklist 五项骨架（外设树盘点/引脚冲突/驱动缺口/供电调试口/flash-RAM 画像）全 pending-confirm 态 + **go_build 恒 False**（原理图无机械判据 = DEC-33 唯一人工环节如实登记；BV1 C2 = 接线后首个机械锚）。测试 +11（test_board_adapt.py——定位/布局矩阵/真锚对拍/五件套/防篡改/owner 闸/工单链/待确认态/MCP 注册）。HLD-agent v0.2.4（§2.1 工具面 +board_adapt + §7 现状注记）；README 计数（agent 346/adapt 行）。消费：plan v1.147、DEC-74、AGENTS 一五四。
