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
| Q-11 | design review-01 语义批次 | docs/history/review-archive.md（design-review-01 节） | 已裁 → DEC-29/30 |
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
| TaError / TA_E_* | Agent 结构化错误模型与错误码族（LLD-agent-common §1；MA1 实现） | agent/tessera_agent/common/errors.py | 已实现（MA1） |
| TaskRegistry / Task | 长任务句柄注册表（对齐 Tasks V2 语义；TTL/环形日志，LLD-agent-common §2） | agent/tessera_agent/common/tasks.py | 已实现（MA1） |
| ContextBudget / maybe_compress | 上下文预算（动态窗口/32k 最低/70% 压缩）与压缩助手（DEC-38 #6） | agent/tessera_agent/common/limits.py + core/session.py | 已实现（MA1） |
| ApprovalBroker / sys_pending_approvals / sys_approve | 审批代理与呈现（token 防代批，DEC-38 #7） | agent/tessera_agent/gateway/approvals.py | 已实现（MA1） |
| gated_tool / PolicyTable / PlanDto | 会话审批闸（工具包装层，等效 wrap_tool_execute）/类别策略表/结构化产物 DTO（LLD-agent-core） | agent/tessera_agent/core/session.py | 已实现（MA1；PydanticAI 原生 Hooks 可后替） |
| build_app / AppContext / run_server | FastMCP 网关装配与 stdio 入口（LLD-agent-mcp-gateway） | agent/tessera_agent/gateway/server.py | 已实现（MA1） |
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
| DR-xx | design review 发现编号族（DR-01…17 见 design-review-01；**DR-18…23 见 design-review-02**（Q-18 涟漪审查，全处置） | docs/history/review-archive.md（design-review 节） | 存档 |
| SC-xx | 最终自检发现编号族（当前 SC-01…04，全部处置） | docs/history/review-archive.md | 存档 |

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
| ts_res_t / TS_E_* | 框架错误码类型与错误码族（LLD-ts-common §2） | LLD 提案 |
| TS_EVT_* | 事件总线事件 ID 族（LLD-ts-core §4） | LLD 提案 |
| CONFIG_TS_* | 框架 Kconfig 前缀（LLD-ts-common §5） | LLD 提案 |
| TSAP | APP 包容器 magic（"TSAP" u32；格式随 Q-05 定稿） | LLD 提案 |
| ts_api_v1 / ts_perm_v1 | 版本化 APP 导入面 / 能力文法（破坏性变更须升 v2，门③） | LLD 提案 |
| ts-store | 存储抽象模块：分区/meta 掉电安全 kv/prov 只读/noinit（DR-01） | HLD v0.2 / LLD 提案 |
| TS_FAIL_* | 故障原因码族（u32：TS_FAIL_SRC_<<16｜细因，LLD-ts-common §2.1） | LLD 提案 |
| ts_ctx_t | APP 调用者不透明上下文（防伪造映射，LLD-ts-common §3.1） | LLD 提案 |
| ts_periph_kind_t | 外设描述符类别枚举（含 TS_PK_ADC，DR-13） | LLD 提案 |
| ts-core 公共 API 族（ts_time_ms/ts_time_test_bind/ts_evt_subscribe/ts_evt_publish/ts_wdt_register/ts_wdt_feed/ts_wdt_start/ts_core_boot/ts_boot_steps） | ts-core 对外 API（LLD-ts-core §2-5；M1 实现） | firmware/module/tessera/include/ts/core.h | 已实现（M1） |
| ts-safety 公共 API 族（ts_safety_register_channel/commit/readback/channel_state/force_all_fault/system_fail/set_link/clear_fault/estop_init/poweron_init/estop_deferred_publish/audit_copy/audit_dropped） | ts-safety 对外 API（LLD-ts-safety §2-5；M1 实现） | firmware/module/tessera/include/ts/safety.h | 已实现（M1） |
| ts 通道/审计类型族（ts_out_ch_t/ts_out_value_t/ts_ch_kind_t/ts_ch_state_t/ts_audit_entry_t/ts_driver_ops_t/ts_drivers/ts_driversim_writes/ts_write_rec_t） | ts-safety 数据模型与驱动分发（LLD-ts-safety §2/§6；M1 实现） | include/ts/safety.h + src/safety/ | 已实现（M1） |
| framework.core / framework.safety / framework.replay | M1 twister 用例（L1/L4 雏形；replay = 双通道确定性比对 + stdout JSONL 接口） | firmware/tests/{core,safety,replay} | 已实现（M1 全绿） |
| check_safety_contract.py | L5 安全合同机械检查脚本（五项，testing.md §3；CI 独立 job 一票否决） | firmware/tests/safety_check/ | 已实现（M1） |
| IR-xx | M1 实现自检发现编号族（IR-01…04 全处置：estop 清除死锁修复/审计一致性修复/两项记录） | docs/history/review-archive.md | 存档 |
| ts_trust_* API 族（ts_store_trust_load/validate/write/trust_test_reset/trust_corrupt_test + ts_trust_table_t + TS_TRUST_KEYS_MAX） | 信任根表持久化面（V0.8.0 EC2 · Q-43③/DEC-60；TUF root 同型全量替换） | firmware/module/tessera/include/ts/store.h + src/store/ts_trust.c | 已实现（EC2） |
| ts_appmgr_trust_update / ts_appmgr_trust_effective | 信任更新编排（COSE 现有效集签名 + ver 严格 N+1）与有效集构建 | include/ts/appmgr.h + src/appmgr/verify.c | 已实现（EC2） |
| sys/trust-update · sys/trust-get | 信任表网络命令面（gated+租约 / 未门控读回） | src/net/cmd.c + LLD-ts-net §4.3 | 已实现（EC2） |
| TS_EVT_TRUST_UPDATED | 信任表更新事件（安全类 QoS，extra {"ver"}；订阅十类） | include/ts/core.h + src/net/pub.c | 已实现（EC2） |
| deploy.trust_get / deploy.trust_update | Agent 信任工具（表 CBOR 手工构造 + cose.sign_diy + 租约闭环） | agent/tessera_agent/tools_net/deploy.py | 已实现（EC2） |
| tsap_tools.manifest_summary / install_permission_brief | 安装期权限呈报数据源与审批 brief（EC3 · Q-40③） | agent tools_tsap/tools.py + domain/firmware.py | 已实现（EC3） |
| gen_trust_fixtures.py / boot_pkg_devroot / trust_blob_* | EC2 测试夹具族（固定种子 + 测试根签名——机械生成纪律） | firmware/tests/app/ | 已实现（EC2） |
| L5 检查 7（slot 收口） | ts_store_slot_write/erase 调用点白名单 = pkg.c（侧载纪律机械保证） | firmware/tests/safety_check/check_safety_contract.py + testing.md §3 | 已实现（EC4） |
| IR-xx（续） | 实现自检发现编号族续（IR-05…20：M2a/M2b/MA0-MA2 审查——修复 10 项含验签 fail-closed/tsap 回绕/keygen 审批闸，登记 6 项） | docs/history/review-archive.md | 存档 |
| ts-net 公共 API 族（ts_net_set_ids/ts_net_key_{cmd,tel,evt,hb,sys}/ts_net_state/ts_net_backoff_ms/ts_net_session_poll/ts_net_pubq_{push,dropped,flush}/ts_net_linkmon_{tick,hb_host}/ts_net_link_up） + ts_net_transport_t（传输缝） | ts-net 对外 API 与传输抽象（LLD-ts-net §1-6；M3a.1 实现——真实现=zenoh-pico 1.10.1，测试注入桩） | firmware/module/tessera/include/ts/net.h | 已实现（M3a.1） |
| framework.net | ts-net L1/L2 用例（key/退避/pubq/会话/linkmon→safety 集成） | firmware/tests/net | 已实现（M3a.1 全绿） |
| ts-net M3a.2 族（ts_net_cmd_{register,dispatch}/ts_net_cmd_sys_init/ts_net_pub_{init,telem}/ts_net_init/cbor_min 内部族）+ ts_net_cmd_args_t | sys 命令面（host_only 7 项，DEC-30①/DR-03）+ 遥测/事件发布 + boot 接线 | include/ts/net.h + src/net/{cmd,pub,init,cbor_min}.c | 已实现（M3a.2） |
| ts_safety_summary / ts_time_wall_{set,ms} / ts_value_encode（公共化） | 安全汇总观测 / 墙钟数据字段（DR-08）/ 规范单字编码（审计遥测统一口径） | include/ts/{safety,core}.h | 已实现（M3a.2，sys 命令面支撑） |
| netlab / netlab_client.py | L3 联调镜像与客户端（native_sim↔zenohd 真实会话；prov 手工定稿键序烧入；复跑方法 dev-env §8） | firmware/tests/netlab | 已实现（L3 PASS 2026-09-23） |
| 命令信封 v2（ver/kind/rid/src/idem/to）+ kind 注册表（请求 1-15/回执 16-31/事件 32-95/遥测 96-127） | ts-net 命令面演进信封与消息类型编号（NeuroLink 借鉴）；v1 弃用期 | design/LLD-ts-net.md §4.2/§4.4 + src/net/cmd.c | 已实现（DEC-40/42，2026-09-23 批） |
| ts_net lease 族（sys/lease-{acquire,release,get} + ts_net_lease_{acquire,release,get,held_by} + CONFIG_TS_NET_LEASE_TTL_MS） | 控制租约：多方并发命令准入仲裁（NeuroLink lease_manager 借鉴；惰性过期；lease_id 单调；不联动安全态） | design/LLD-ts-net.md §4.5 + src/net/lease.c | 已实现（DEC-41，2026-09-23 批；M2b.2 写命令挂钩点 = ts_net_lease_held_by） |
| ts_net_qos_t（TS_NET_QOS_{BESTEFFORT,SAFETY}）+ ts_net_pubq_push_qos + transport.publish(qos) | 发布服务类穿透 pubq→传输（DEC-42 QoS 映射：安全事件 BLOCK+REAL_TIME，遥测/心跳缺省 DROP+DATA） | include/ts/net.h + src/net/{pubq,zenoh}.c | 已实现（DEC-42，2026-09-23 批） |
| 遥测 payload 键 dev（原 kind 改名）+ 事件 payload kind=32+evt_id | DEC-42 信封落地键名（消费端 Agent keys.py 镜像出处） | design/LLD-ts-net.md §5 + src/net/pub.c | 已实现（2026-09-23 批，消费端随批同步） |
| ts-appmgr 分步安装族（ts_appmgr_stage_{begin,chunk,verify,activate}）+ sys/app-{begin,chunk,verify,activate}/get-app + ts_cbor_bstr_ref + CONFIG_TS_NET_APP_CHUNK_MAX | 远程部署面固件侧（LLD-agent-deploy-net §3；upload→verify→activate；写类命令 gated = v2+租约） | include/ts/{appmgr,net}.h + src/{appmgr/pkg.c,net/cmd.c} | 已实现（MA3.1） |
| Agent deploy 族（tools_net/{keys,zenoh_service,deploy}.py：envelope/parse_reply/kind 镜像 + ZenohService 线程桥 + discover/status/push_app；MCP 工具 deploy_{discover,status,push_app}） | Agent 部署工具链（LLD-agent-deploy-net §1-3；分块分步推送 + 租约闭环 + idem 重试 + tsap_verify 强制复验） | agent/tessera_agent/tools_net + gateway/server.py | 已实现（MA3.1） |
| FakeCube / test_deploy_e2e.py（TESSERA_E2E_DEPLOY=1 门控） | 部署面单测语义桩与 E2E（MA3 退出标准断言：confirmed/slot 切换/容器自洽） | agent/tests | 已实现（MA3.1） |
| A07 skills 族（agent/skills/{tessera-workflow,tessera-build,tessera-tsap,tessera-safety}/SKILL.md + SkillRef/loader + skill_read 工具 + SOURCES.lock + sync_check） | 域知识包与渐进披露（开放标准目录；派生纪律 = 源文档摘要锁 + pytest 守卫，Q-19 #13/DEC-38 #13） | agent/skills + tessera_agent/skills | 已实现（MA3.2） |
| 平台/域拆分（platform.py：DomainPack/DomainPackBase/MountAPI/assemble + compose.py 组合根 + domain/firmware.py：FirmwareDomainPack/FirmwareDeployer/validate_tsap_manifest） | 多域预留架构（DEC-33：平台不 import 域——导入图测试守卫）；固件域 14 工具 + skills/policy/validators/deployer 声明 | agent/tessera_agent/{platform,domain} | 已实现（MA3.2） |
| app_chain 族（DevelopOutcome/app_develop/app_deploy MCP 工具） | DEC-34 高层链：spec→计划/manifest（结构化校验）→TSAP 打包复验；包→复验→发现定位→分块部署→确认（S5）；wasm 产物边界 = M2b.2 | agent/tessera_agent/domain/app_chain.py | 已实现（MA3.2） |
| ts-power 族（ts_pwr_slot_t/ts_power_{register_slot,request,slot_count,slot_get}/ts_power_budget_t/ts_power_budget_snapshot + CONFIG_TS_POWER_MAX_SLOTS） | 受控供电（DEC-03 合同 7）：槽注册→TS_CH_POWER 通道；预算 prov 只读 + readback 记账 + 峰值 + TS_EVT_POWER_BUDGET | include/ts/power.h + src/power/{slots,budget}.c | 已实现（M3b） |
| ts-periph 族（ts_periph_kind_t{TS_PK_*}/ts_periph_desc_t/ts_periph_{register,count,get,attach,detach} + ts_periph_evt_t + CONFIG_TS_PERIPH_MAX_DESCS） | 描述符职责链（uid/dt 双名解耦 DEC-04）+ 插拔（DETACH→单通道 SAFE_FAULT） | include/ts/periph.h + src/periph/{desc,hotplug}.c | 已实现（M3b） |
| ts_safety_force_channel_fault / ts_safety_channel_recover / ts_safety_test_reset | 单通道故障与恢复（periph DETACH 机制面）+ 测试隔离（通道表全清） | include/ts/safety.h + src/safety/channel.c | 已实现（M3b） |
| kind 97（功率预算快照）+ ts_pwr_budget_evt_t | 遥测区间分配（LLD-ts-net §4.4 权威；keys.py KIND_TELEMETRY_POWER 镜像） | design/LLD-ts-net.md §4.4 + src/net/pub.c | 已实现（M3b） |
| impl-review-01 / F-1…F-8 | impl 阶段评审报告与发现编号族（2026-09-25，对象 = DEC 批/MA3.1/MA3.2/M3b 四交付单元；验证全绿复现，8 项发现分级处置） | docs/history/review-archive.md | 已处置（修复批 2026-09-25 同日交付，F-5/F-7 为登记项） |
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
| HLD-agent / LLD-agent-common…A07 | Agent 轨道设计文档族（A00 公共/A01 网关/A02 核心/A03 固件工具/A04 模拟器/A05 TSAP/A06 部署/A07 skills+平台） | design/HLD-agent.md v0.1 批次 | v0.1 待 owner 确认（C-4/C-5） |
| TA_E_* | Agent 错误码族（TaError 结构化异常，LLD-agent-common §1） | LLD-agent-common 提案 |
| sys_* / task_* / fw_* / sim_* / tsap_* / deploy_* / app_* | Agent MCP 工具名族（原子层 19 + 高层 2，双层工具面 DEC-34；增删 = review 门） | LLD-agent-mcp-gateway §2 | 提案（随 C-5/Q-19） |
| DomainPack | 域工具包接口（工具集+skills+策略+校验器+部署器；固件域 = 首个实现，多域预留核心） | design/HLD-agent.md §6.1 / LLD-agent-skills-platform §3 | 提案 |
| Frontend / PeerTransport | 会话编排层传输抽象（ACP 预留缝，DEC-35）/ A2A 对等接入缝（DEC-36④ 记录点） | LLD-agent-core §1 / LLD-agent-skills-platform §4 | 提案（V1 仅接口预留） |
| SessionOrchestrator / TaskRegistry | 会话编排器（A02）/ 长任务句柄注册表（A00，对齐 Tasks V2 语义） | LLD-agent-core/A00 | 提案 |
| TsapManifestV1 / PlanDto / AppConfigDto | Agent 侧结构化产物模型（manifest 镜像 / 开发计划 / 硬件配置） | LLD-agent-tsap-tools §2 / LLD-agent-core §4 | 提案 |

## 6. 重命名登记册（2026-10-24 仓整理 · DEC-78——新旧映射唯一权威）

> 全库活文档引用已同步至新名；历史档案（docs/history/）与 evidence 留痕中的旧名以本表解读。
> 命名规范见 `docs/std/naming.md`。注：HLD-agent 文内节号 A00-A17 为文档内部结构编号（§2/A00 引用形态），非文件名——维持不改，对应 LLD 见下表。

**design/ 设计文档（19 件）**

| 旧文件名 | 新文件名 |
|---|---|
| LLD-00-common.md | LLD-ts-common.md |
| LLD-A00-common.md | LLD-agent-common.md |
| LLD-A01-mcp-gateway.md | LLD-agent-mcp-gateway.md |
| LLD-A02-agent-core.md | LLD-agent-core.md |
| LLD-A03-fw-tools.md | LLD-agent-fw-tools.md |
| LLD-A04-sim-harness.md | LLD-agent-sim-harness.md |
| LLD-A05-tsap-tools.md | LLD-agent-tsap-tools.md |
| LLD-A06-deploy-net.md | LLD-agent-deploy-net.md |
| LLD-A07-skills-platform.md | LLD-agent-skills-platform.md |
| LLD-A08-creation-workspace.md | LLD-agent-creation-workspace.md |
| LLD-A09-terminal-facade.md | LLD-agent-terminal-facade.md |
| LLD-A10-mci-channels.md | LLD-agent-mci-channels.md |
| LLD-A11-web-client.md | LLD-agent-web-client.md |
| LLD-A12-board-validation.md | LLD-agent-board-validation.md |
| LLD-A13-memory-planner.md | LLD-agent-memory-planner.md |
| LLD-A14-web-reshape.md | LLD-agent-web-reshape.md |
| LLD-A15-mcp-clients-and-post-hooks.md | LLD-agent-mcp-clients-and-post-hooks.md |
| LLD-A16-hardware-targeting.md | LLD-agent-hardware-targeting.md |
| LLD-A17-board-adaptation.md | LLD-agent-board-adaptation.md |

**docs/ 报告（16 件——\*-01 序号后缀撤除/描述化）**

| 旧 | 新 |
|---|---|
| agent-cli-research-01.md | agent-cli-research.md |
| agent-codegen-reliability-01.md | agent-codegen-reliability.md |
| av-transport-01.md | av-transport.md |
| board-bench-01.md / board-deploy-01.md / board-estop-01.md | board-bench.md / board-deploy.md / board-estop.md |
| board-h7-01.md / board-p4-01.md / board-periph-01.md | board-h7.md / board-p4.md / board-periph.md |
| board-persist-01.md / board-psram-01.md / board-reconnect-01.md | board-persist.md / board-psram.md / board-reconnect.md |
| demos-01.md / netbench-01.md / zephyr-upgrade-eval-01.md | demos.md / netbench.md / zephyr-upgrade-eval.md |
| md12c-pdm-eval.md | pdm-audio-eval.md |

**agent/demos/（16 目录——纯序号目录名禁用）**

| 旧 | 新 |
|---|---|
| D1 / D2 / D3 / D4 / D5 | demo-led-blink / demo-heartbeat / demo-pwm-breath / demo-adc-report / demo-security-overreach |
| D6 / D7 / D8 / D9 | demo-hysteresis / demo-health-rollback / demo-lifecycle / demo-linkloss |
| D-AG7 / D-AK4 / D-AV / D-PDM | demo-thermo / demo-resource-push / demo-audio-video / demo-pdm-audio |
| D-SD / D-THR / P4W | demo-sd-storage / demo-threads / demo-p4-probe |

**firmware/（目录与脚本）**

| 旧 | 新 |
|---|---|
| firmware/l3app/（l3_client.py） | firmware/tests/netlab/（netlab_client.py） |
| firmware/tests/l5/check_l5.py | firmware/tests/safety_check/check_safety_contract.py |
| firmware/tests/pytest/test_l5_self.py | firmware/tests/pytest/test_safety_contract_self.py |

**tools/board/（16 脚本——会话代号前缀撤除）**

| 旧 | 新 | 用途 |
|---|---|---|
| ak_tls_e2e.py | e2e_tls.py | TLS mTLS 部署 E2E |
| ak1_deploy_check.py | e2e_deploy_smoke.py | atk 板部署冒烟 |
| ak3_trust_e2e.py | e2e_trust_chain.py | 信任链 T0-T7 |
| ak4_res_e2e.py | e2e_resource_push.py | net+SD 资源推送 |
| ak5_large_e2e.py | e2e_large_deploy.py | 206KB 大档全链 |
| ak6_ln_e2e.py | e2e_ln_fanout.py | 双板 LN 扇出/聚合 |
| cg7_deploy_check.py | e2e_contract_spotcheck.py | 合同泛化 spot check |
| ma_demo.py | demo_multiapp.py | 多 APP 并行部署 |
| ag7_demo.py | demo_llm_creation.py | 真 LLM 多文件创作 |
| dp_demo.py / dt_demo.py | demo_pdm.py / demo_threads.py | PDM / 多线程 demo |
| gen_ak_prov.py | gen_prov_image.py | prov 分区映像生成 |
| gen_p4w_probe.py | gen_p4_probe.py | P4 探针包生成 |
| p4w_udp_echo.py | p4_udp_echo.py | P4 UDP 回声对拍 |
| ak_holder2.py | console_holder.py | 韧性串口持有器 |
| nvd_demo.py | nvd_acceptance.py | 新机验收全链（NVD） |

**agent/scenarios/（2 件）**：d8-v1-ramp.json → lifecycle-ramp.json；d9-linkloss.json → linkloss.json。

**删除件与去向**

| 删除件 | 去向/理由 |
|---|---|
| design/ + docs/ 九份评审/自检档（design-review-01/02、impl-review-m1/m2a-ma2、impl-review-01/02/03、final-selfcheck ×2） | **docs/history/review-archive.md**（分节合并逐字保留——IR/IR2/DR/SC 发现编号溯源链不断） |
| docs/migration-x86.md | 删除（x86 机已销毁；env-rebuild-checklist = 唯一重建总单） |
| docs/agent-llm-smoke-01.md / docs/agent-demo-readiness-01.md | 删除（结论已消费入 dev-environment/demos） |
| agent/decisions.md | 删除（陈旧孤儿副本——权威 = 根 decisions.md） |
| legacy/ / hardware/（空占位目录） | 删除 |
| agent/boards/atk-dnesp32s3b.toml | 删除（同板合并入 dnesp32s3b.toml——2026-10-24 去重登记，先于本整理） |

**AGENTS/plan/names 历史正文**：AGENTS §1 旧条目 → docs/history/agents-status-archive.md；plan 旧批次计划与修订 → docs/history/plan-archive-2026-10.md；names 旧修订 → docs/history/names-revisions-archive.md（均逐字搬运）。**docs/evidence/ 留痕文件名一律不回溯**（历史审计链——索引见 docs/evidence/README.md）。

## 修订记录
- 2026-10-24 · **全仓整理与命名规范化登记（owner 指令 → DEC-78；plan L 表第二单元）**：§6 重命名登记册新立（LLD-A 系 19 件→LLD-agent-\*/LLD-ts-common、docs \*-01 16 件去号、demos 16 目录→demo-\*、l3app→firmware/tests/netlab、tests/l5→tests/safety_check、tools/board 16 脚本描述化、scenarios 2 件——新旧映射唯一权威）；删除件去向登记（九份评审/自检档→docs/history/review-archive.md 合并保 IR/IR2/DR/SC 溯源、migration-x86 删除〔checklist 唯一总单〕、agent/decisions.md 孤儿删除等）；AGENTS/plan/names 历史正文逐字归档 docs/history/（搬运非改写——历史登记不回溯原则维持）；命名规范新立 docs/std/naming.md + evidence README 索引（evidence 文件名不回溯）；DR-xx/SC-xx 登记行出处列改指 review-archive。HLD-agent 文内节号 A00-A17 维持（文档内部结构非文件名）。消费：plan v1.155、AGENTS 一五七。
- 2026-10-21 · **V0.13.0 BV2-D 设计批 + 版本收口登记**：LLD-agent-board-adaptation.md（v0.1 门③三决策点呈递——接入件产出形态/C0 解锁范围/v1 裁剪；两路径 = 收录板接入件五件套〔板定义定位/五分区 overlay/板级 conf〔memory_audit R0-R7 机械复核〕/WAMR 架构映射/prov 通道〕+ BV1 bring-up 两级〔构建级 C0 + 板级 C1-C6〕→ 画像入目录；未收录板原理图人机协作〔移植清单 + 协作 DTS 待确认态〕）；HLD-agent **v0.2.3 深度修订**（§1 MCI 三层四渠道 + 四铁律/§2 A10 + 交互域 + 工具面九增/§4 S9-S12/§5.4 安全面六增/§7 现状注记/§9 裁剪更新）；README 仓库地图对齐（agent 343/design A00-A17/docs 行）；**tag fw-v0.13.0**（附注式本地，push 待 owner）。V0.13.0 = 16 单元全 ✅。消费：plan v1.142、AGENTS 一五〇。

- 2026-10-21 · **V0.14.0 P4 联网批立项登记（owner：「先尝试解决P4的wifi问题，我将帮你接入esp32p4开发板；esp32s3已经被移除」）**：plan §11h J 表 v1.143（P4-W0 环境备料/P4-W1 C6 对齐+bring-up/P4-W2 数据面判据矩阵+树内根治）。**攻击面变更定案（树内盘点）**：v4.5.0-rc1 树内全新代 esp-hosted-mcu 驱动全家桶——drivers/misc/esp_hosted_mcu（transport：SDIO/SPI + buf-config TLV tag 0x1b 协商〔SW_AGGR 四字节 stride walk / STREAM byte-tight / PACKET / 缺 tag 兜底 byte-tight〕）+ drivers/wifi/esp_hosted_mcu（WIFI_ESP_HOSTED_MCU——DT espressif,esp-hosted-mcu-wifi）+ drivers/bluetooth/hci/hci_esp_hosted_mcu.c；零外部模块（west 无 esp-hosted 条目仍可构建）；waveshare esp32p4_wifi6_dev_kit DTS 已接新绑定（sdhc1 SDIO 4-bit@40MHz CLK18/CMD19/D0-3=14-17 + reset gpio1 22 + BT HCI 节点）。**病灶承接（教训 32⑤）**：2026-10-10 旧批 = 旧 esp_hosted 驱动（Arduino protobuf 代）+ C6 v3.0.9 STREAM 强制绕行（CONFIG_EH_TRANSPORT_CP_SDIO_MODE_STREAM）→ RPC 控制面通 / DHCP 数据面死 3/3；上游 #121767/#121772 域。**新攻击计划** = 新驱动 × C6 stock rel-3 default（SW_AGGR）原生协商——撤销 STREAM 强制；E0 无板构建面 / E1 板到 C6 重烧 + P4 烧录 + 判据链〔SLC ready→buf-config→握手→wifi_connect→DHCP〕/ E2 数据面矩阵〔DHCP/ping/TCP/zenoh CONNECTED/BV1 C1-C6〕+ 树内自研根治兜底（可 upstream）。**板态域变更**：esp32s3（atk）物理移除——atk 画像维持不删（BV1 C1 如实 FAIL 按设计工作）；依赖 atk 的板级面全部转 P4；riscv64-zephyr-elf 工具链补装（教训 31②）。消费：plan v1.143、AGENTS 一五一、教训 31/32。

- 2026-10-21 · **V0.14.0 P4-W1 判决 PASS 登记（owner「我已经接入了开发板」——当日首跑即绿）**：p4wifibench 入仓（firmware/tests/p4wifibench——判据行驱动 CONNECT/DHCP/UDP RTT/ALIVE + net shell；凭据 Kconfig 构建期注入〔/tmp conf 600——PSK 红线，west 错误回显泄露面教训：命令行不携凭据〕）；tools/board/p4_udp_echo.py（host 侧 UDP 回声对拍器）；CH343 身份链（by-id 5B90122202 / GD 16MB c8:4018 / esptool RTS 自动复位链免人工）；判据链 = CONNECT OK → DHCP OK ip=192.168.2.29 → UDP RTT 5/5（host 双源独立对拍）→ ICMP 3/3 0% loss（net ping -c 3——该树选项在前语法）→ ALIVE 稳定 × 两 boot 复跑。**结论 = 教训 32⑤「上游驱动 RX 数据帧缺陷」在新代 esp_hosted_mcu 驱动上不复存在**；C6 stock 重烧降级可选加固（buf-config TLV × 现存 STREAM 固件原生协商）。build 期三坑：应用 Kconfig 须 source "Kconfig.zephyr"（否则全树符号 undefined）/ 4.5 wifi_mgmt 符号 = NET_REQUEST_WIFI_CONNECT（INTERFACE_CONNECT 不存在）/ zsock_recv 4 参（flags 必传）；net_if_ipv4 形状（unicast 内联数组 / gw 裸 in_addr）。证据 docs/evidence/p4w1_console.txt。消费：plan v1.144、AGENTS 一五二。

- 2026-10-21 · **V0.14.0 P4-W2 收口登记（owner「按照计划完成V0.14.0的开发」）**：firmware/tests/p4bench/p4net.conf（EXTRA_CONF 网络面：TS_NET/zenoh + esp_hosted_mcu + POSIX pthread 族 + NET_MAX_CONTEXTS 4 + 堆 49152〔4096 缺省 = z_open rc=-78 _Z_ERR_SYSTEM_OUT_OF_MEMORY 实测；131072 = sram0_0_seg 溢出 79968B → 48KB 余量推算〕）+ p4bench CMakeLists 凭据文件注入面（P4BENCH_CREDS_FILE include——west 回显泄露面教训，命令行不携凭据）+ main.c P4BENCH_NET 块（WiFi/DHCP 先行 + P4W2 判据行）；agent/boards/p4-wifi6.toml（BV1 画像——[hardware] 在位引脚未采 = HW-4 门生效形态）；agent/demos/demo-p4-probe/（探针 app.c log-only + fixture 测试根签名包 + gen_p4_probe.py 入仓生成器）；tools/board/p4_udp_echo.py。**信任链实证**：自造测试钥被 TEST 板如实拒（status=-9 TS_E_INVALID_SIG；板侧 sm 指纹 pk0=f084a4e5 = verify.c 编译内固定测试根 = agent/tests/fixtures/ts-test-root——TEST 构建工厂根非 prov pk0 纪律入册）；**compile_app_c 存量缺陷修复**：required_exports 从不传导出旗标（单文件路径导出面恒缺）→ _run_clang_files exports 接线 + 1 用例。**BV1 C6 语义补丁**：激活后无条件暖复位（CG7「激活暖复位 ACTIVE」正典——同 app 重部署场景条件复位漏判）+ RTS 脉冲复位助手（教训 42 DTR/RTS 纪律）。**FIX-2 候选登记**：探针 meta 下板复位循环（~15-20s 周期交替 probe/P4B；P4B meta 稳定 90s+）——疑似健康回退族/bench-vs-app 互扰，root cause 随板级专项。证据 docs/evidence/p4w2_console.txt。消费：plan v1.145、AGENTS 一五三、tag fw-v0.14.0。

- 2026-10-22 · **V0.15.0 立项 + FIX-2 根治登记（owner「我已经完成review，请你继续开发」——DEC-74 BV2 门③三裁决按建议值；V0.14.0 四提交 + tag fw-v0.14.0 随令推送）**：**FIX-2 板载插桩破案**——root cause 三连（同根 WAMR 调用契约）：① appmgr/runtime.c call0() 以 argc=0 调 wasm_runtime_call_wasm，WAMR 契约 argc ≥ function->param_cell_num（wasm_interp_classic.c:7397）——约定签名 app_tick(int ctx)（1 cell）每 tick 必陷 "invalid argument count 0, must be no smaller than 1"；无参 fixture tick（app_tick(void)）恒过 = sim 套件/bench 全绿、带参 app 必死（V0.4 起存量，首例带参 tick app = P4 探针）；② WAMR 实例异常位跨调用存活（wasm_call_function 以异常位判成败）——一次 trap 毒化后续全部调用（health_ping 实际执行成功亦判败）；③ health_probe 不设指令配额（继承上次调用余量）。**故障闭环** = tick 每陷 → health_fails 累积 → 3 败健康回退 → meta 翻槽（TS_TEST 构建静默无打印不复位——slot.c 两分支皆 #if !defined(CONFIG_TS_TEST)）→ app 线程退出 → APPMGR 喂狗停 → 巡检 system_fail(TS_FAIL_WDT(1)) → noinit 0x00020001 → task_wdt 复位（rst:0xc）；「meta 交替 probe/P4B」= 每次 C6 重跑重新激活探针；bench 包无参 tick 健康恒过 = bench meta 稳定。**修复**（runtime.c 23+/15-）：call0 撤除、tick 经 call1 带 ctx（argc=1 ≥ 任意 ≤1 参 cell；WAMR 对无参钳制不扰——bench 零变化）+ call1 失败 wasm_runtime_clear_exception（毒化破除）+ health_probe 显式 INSTR_TICK 配额/argc=1 带 ctx/失败清异常（返回值经 argv[0] 回传语义保持）。**顺带 agent 抓取面修复**：post_deploy_check 增 reset_before_capture（缺省 False 行为不变；True = 单端口会话 reset_and_capture）——BV1 deploy_smoke 弃「_serial_reset 关口 → capture_window 再开」两段式（CH343 快速关/开竞态 → 抓取窗零字节 no_verdict 假 FAIL，真机实测复现），_serial_reset 方法撤除；+1 用例（旗标路由断言）。**板上闭环**：探针 INIT + ALIVE t=11s 首印、tick 连跳 fail 恒 0、零复位零回退、槽乒乓按设计（probe@slot1）；bench 同固件 P4B PASS；**BV1 C4+C6 PASS——P4 板 C1-C6 全链首次全绿（93.3s）**。**入册事实**：meta 双副本乒乓快照纪律（单读 copy0 会误判「meta 未变」——REC_HDR seq/len/crc16 + copy1@stride）；P4 烧录布局（ROM 自 0x2000 简单引导 app〔CONFIG_BOOTLOADER_OFFSET_IN_FLASH=0x2000〕；west flash = 单产物 write_flash 0x2000 zephyr.bin；误写 0x0 = 0x2000 处真 app 被镜像中段字节覆盖 → ROM "invalid header: 0x028777b3"〔即镜像 0x2000 偏移内容〕→ HP WDT boot 循环；恢复 = erase_region 0 0x2000 + write_flash 0x2000）。**DEC-74** = LLD-agent-board-adaptation §5 三决策按建议值（接入件 agent/adapt/ 工作区/C0 流水线内临时解锁/v1 收录板全链+未收录清单）+ V0.15.0 立项（§11h K 表）。证据 docs/evidence/fix2_p4_probe_console.txt。消费：plan v1.146、AGENTS 一五四。

- 2026-10-22 · **V0.15.0 BV2-I 交付登记（DEC-74 门③三裁决落地——LLD-agent-board-adaptation §2/§3/§4 实现收口）**：`domain/board_adapt.py` 新建——**收录板路全链**：locate_board（hardware.check_zephyr_inclusion 同源归一化双向子串匹配；未命中 = AdaptError stage=locate 转未收录路）/ plan_partitions 布局模板族（键 = flash_kb：16384 = **P4 playbook 真锚**〔carve 0x7e0000/prov 4KB/meta 8KB/slot 32KB×2/noinit——测试与在树 p4bench overlay 逐偏移对拍〕；8192 = 8MB 保守兼容同构；4096 = 最小档 slot 减半 16384；未知尺寸 fail-closed 不发明）/ render_overlay（P4 playbook 同构模板：/delete-node/ slot1 + ts 五分区 mapped-partition + fw-b 预留，擦除块对齐 assert）/ render_board_conf（内存初值家族 + _WAMR_ARCH_NOTES 架构表〔riscv main 栈 8192 = P4 实测深帧口径/xtensa/arm 4096〕）/ prov.json（教训 39 offset 陷阱注记随行）/ workorder.json 工单 + c0_preflight 机械预检（齐备性/擦除块对齐/越界/slot 尺寸耦合——C0 真实构建 = 流水线会话内执行，DEC-74② 不全局解锁）。**install_profile owner 闸**（DEC-74①：owner_approved=False 恒拒零落盘；草稿推定态如实标注——实测值待 bring-up 回填；**BV1 load_profile 可装载 = clarify 分支 A mention 绑定同源消费——工单两端闭环测试**）。**MCP `board_adapt`**（strict——写 agent/adapt/ 工作区；mode=included/schematic；审批呈现 + spawn 长任务 + note_progress D2 同汇）。**未收录板路**：migration_checklist 五项骨架（外设树盘点/引脚冲突/驱动缺口/供电调试口/flash-RAM 画像）全 pending-confirm 态 + **go_build 恒 False**（原理图无机械判据 = DEC-33 唯一人工环节如实登记；BV1 C2 = 接线后首个机械锚）。测试 +11（test_board_adapt.py——定位/布局矩阵/真锚对拍/五件套/防篡改/owner 闸/工单链/待确认态/MCP 注册）。HLD-agent v0.2.4（§2.1 工具面 +board_adapt + §7 现状注记）；README 计数（agent 346/adapt 行）。消费：plan v1.147、DEC-74、AGENTS 一五四。

- 2026-10-23 · **BV2 适配流水线真板首实战登记（owner「请先开始BV2实战，需要我做什么」+「评估供电是否足够」+「自行完成剩余开发项」）**：**全链闭环**——双板同接（owner Self-Powered hub；供电静态〔lsusb Self Powered + dmesg 零过流〕+ 带载〔双板 WiFi 同网 + 部署突发 + LN 扇出全程零 brownout/零 WDT〕双证）；atk flash-id 实测（ESP32-S3 双核 + PSRAM 8MB OCT + boya 16MB JEDEC 68:4018 = 一四三档案全同）；**BV2 流水线生成五件套 = 板级面唯一来源**（deploybench 经 EXTRA_DTC_OVERLAY_FILE/EXTRA_CONF_FILE 消费 agent/adapt/dnesp32s3b/ 生成件——零手写板级件；dram0 溢出 25164B 实测 → heap 98304 MP 每板预算纪律敲定）；prov 重生成（内嵌陈旧 x86 路由 tcp/192.168.2.91:9955 → cbor2 确定性编码重生成 tcp/192.168.2.101:9957，逐字段对拍原 blob）；**第二板入 LN 网**（DB2 prov burn=0 node=dbn cube=dbc → CONNECTED 9957）；**BV1 C1-C6 全 PASS（185.3s）**→ agent/boards/dnesp32s3b.toml 入目录（owner「自行完成」委托记 + 草稿全文随批呈递）；**双板 LN 双 ACTIVE PASS**（bv2-ln = cube-p4+dbc；扇出双 confirmed + 暖复位 + 聚合 state=3×2 零降级）。**实战回填生成器三缺口**：① esp32s3 &wifi 使能（soc 分派）② PWM 硬依赖面（deploybench main.c 无桩符号——pwm_led_pin 调用方硬件事实参数 + ledc/pinctrl/zephyr_user 绑定，HW-4 source 纪律）③ 网络内存家族（net 模板恒开：R1/R2 4096 + xtensa main 8192〔教训 31⑤〕+ PSRAM 卸载家族）；BV1 C4 probe_cube 直查兜底（单 `*` 选择子双板可靠）；deploybench -C 初始缓存须 CACHE 形式 set()（普通 set() 作用域不外溢 = 空凭据 rc=-22，一三二同型）。**观察项**：全通配查询单回执 quirk（atk 只应答单 `*`、尾通配 0 回执——zenoh 路由/pico 声明交互域；显式 id 面全通）；双板网络画像 cube 空值语义歧义（须显式回填）。证据 docs/evidence/bv2_first_board_console.txt。消费：plan v1.153（§11h L 表新立——V0.16.0 累积池首单元，DEC-75）、AGENTS 一五五。

- 2026-10-24 · **板卡画像同板去重合并登记（owner 指令「atk-dnesp32s3b / dnesp32s3b 这两个应该是一块板子」——fix 类卫生笔）**：正点原子 ATK DNESP32-S3B V1.1 = Zephyr 收录板 alientek/dnesp32s3b——agent/boards/ 双画像（atk-dnesp32s3b.toml〔BV1 手工〕+ dnesp32s3b.toml〔BV2 实战流水线〕）实为同板（串口 by-id CH343 5909066900 全同 / boya 16MB 真硅同源 / atk 画像 [hardware].zephyr_board="dnesp32s3b_esp32s3" 即收录键；重复根源 = BV2 为同板新开流水线画像）。**合并方向 = 保留 dnesp32s3b.toml（流水线规范名——install_profile 生成 agent/boards/<Zephyr 板名>.toml，保留 atk- 前缀名会在下次 BV2 再生成时重现重复）**：吸收 atk 物理事实（[hardware] LEDB=pwm:0〔source 补 BV2 adapt overlay LEDC_CH0_GPIO4 同源〕/ boya JEDEC 出处 / 持有器与 C0 注记）+ 现行镜像态取 BV2 值（zenoh.cube=dbc 显式回填〔一五五观察项④就此板闭合〕/ caps min_slot_pool_kb=32 注记 atkbench 产线镜像 2048 重烧后回填 / smoke=P4W 架构中立探针）；atk-dnesp32s3b.toml 删除。**附带修复**：HW-1 _match_catalog 恰一命中门——「ATK DNESP32-S3B」全名此前双命中（norm 同时含于 atkdnesp32s3b 与 dnesp32s3b）拒绝绑定转收录检查路，去重后恰一命中恢复 profile 绑定；test_hardware 画像路径 / test_clarify ×2（提及改全名 + 断言改 dnesp32s3b）/ clarify._match_catalog 文档串 / LLD-agent-board-validation §2 示例 id（v0.1.2）随改。**验证**：受影响套件（clarify/hardware/board_validation/board_adapt）71 全绿 + ruff 干净 + 目录匹配 sanity 矩阵恰一命中。**迁移注记**：本地 config [agent] board_profile 若仍指 atk-dnesp32s3b 须改 dnesp32s3b（load_bound_profile 缺文件静默跳过）。消费：plan v1.154、AGENTS 一五六。

> 更早修订登记（2026-09-22…2026-10-21）已归档 `docs/history/names-revisions-archive.md`（2026-10-24 仓整理）。

