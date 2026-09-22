# decisions.md · Tessera 决策登记册

> **生命周期**：`Q-xx`（待裁）→ owner 回复 → `DEC-xx`（已裁，附日期与原文）；编号不复用，REJECTED 留档。
> **呈递格式**（流程 §2.4 强制）：背景（现状 + 为何是问题）→ 选项 → 建议 → 影响。
> **默认值三问**（写任何常量前自答）：从哪来（Q/推导）？越界会怎样？改动破坏什么？
> 本文"§x.y"章节号指 `FOUNDING_PROMPT.md` 章节。

## 一、已裁定决策（DEC）

> DEC-01…16：**2026-09-18 owner 裁定**（K1 录入，原文见 `FOUNDING_PROMPT.md` §1）；DEC-17/18：**2026-09-19 owner 裁定**（原文见备注栏）；DEC-19…24：**2026-09-20 owner 裁定**（原文见备注栏）。

| # | 裁定日期 | 决策（原文） | 备注（含遗留设计题） |
|---|---|---|---|
| DEC-01 | 2026-09-18 | 每个立方体 = 独立智能模块：自带 MCU、Zephyr 固件、网络接口、电源路径 | — |
| DEC-02 | 2026-09-18 | 立方体四面扩展接口**含数据链路**；并联后的多立方体对外构成**一个逻辑节点** | 遗留设计题（HLD 必答）：逻辑节点内部拓扑（主从/协商）、跨立方体资源编址、安全仲裁归属；硬约束见安全合同第 8 条 |
| DEC-03 | 2026-09-18 | 对外供电**受控**：软件开关、限流、功率预算上报 | 供电视同"输出"，纳入安全合同（§5.7） |
| DEC-04 | 2026-09-18 | APP 访问硬件 = 框架统一 HAL API + **声明式权限清单**（类安卓 Manifest）；APP 之间仅经框架消息通道通信，禁止直接互访 | 权限模型变更触发 review 门（§2.4-③） |
| DEC-05 | 2026-09-18 | APP 安装 = 网络分发 + 签名 + 版本化 + 失败自动回滚 | — |
| DEC-06 | 2026-09-18 | 数据面通信**只走物理网络**（以太网 / WiFi）；**BLE 不考虑** | — |
| DEC-07 | 2026-09-18 | UART 完全退出数据面：仅作调试终端（Zephyr shell，类 Linux console）+ MCUmgr/SMP 救砖与 OTA 底线通道 | — |
| DEC-08 | 2026-09-18 | 数据面应用层协议选型**重开**（旧项目的 Zenoh 结论不复用） | → Q-02 / R2 |
| DEC-09 | 2026-09-18 | APP 运行时（WASM 虚拟机 vs LLEXT 原生 ELF vs 其他）**待研究** | → Q-01 / R1；owner 已知观察：WASM 运行时（如 wasm3）非 Zephyr 官方维护、不在 west 默认 manifest；LLEXT 官方在树但标注实验性 |
| DEC-10 | 2026-09-18 | 物理安全基线继承 §5 安全合同（旧项目调研结论，与任何上层项目无关，属产品安全本身） | 合同全文：`AGENTS.md` §6 |
| DEC-11 | 2026-09-18 | AI Agent 产出范围 = 业务 APP **与** 硬件配置（外设分配 / 引脚映射 / 安全参数）——**两者，owner 强调** | — |
| DEC-12 | 2026-09-18 | Agent 形态 = MCP server，封装"模块 API + 模拟器 + 构建工具链"；LLM 由用户自选；Agent 运行于 PC 侧 | — |
| DEC-13 | 2026-09-18 | V1 模拟测试深度 = native_sim 固件仿真 + 外设桩模型（数字孪生-lite）；真机在环后续再议 | — |
| DEC-14 | 2026-09-18 | 目标板集：ESP32-S3 / ESP32-P4 / STM32H7 / RP2350 + native_sim（CI 平台） | 各板网络能力差异（S3 原生 WiFi；P4 无无线电需配 C6 或用以太网；H7 有 EMAC 需外挂 PHY；RP2350 需外挂网络模块）——R2/HLD 的输入 |
| DEC-15 | 2026-09-18 | V1 交付顺序：**固件框架（native_sim 上可运行）→ AI Agent + 模拟器 → 硬件立方体定型** | 理由：硬件结构/连接器周期最长且依赖软件形态验证 |
| DEC-16 | 2026-09-18 | 独立开源仓库；许可证 Apache-2.0 | — |
| DEC-17 | 2026-09-19 | APP 运行时 = **WASM 虚拟机**，实现采用 **WAMR**（WebAssembly Micro Runtime，Apache-2.0，有官方 Zephyr 移植） | owner 原文："R1：我们选择WAMR。"；依据 R1 初步笔记（草稿 v0.1，`docs/research/R1-app-runtime.md`）裁定。遗留设计题（HLD 必答）：① 执行模式（解释器 vs AOT vs 混合）与按板预编译策略；② HAL API 绑定层——权限清单（DEC-04）如何映射为 wasm 导入函数/能力句柄（安全合同 10 的强制点）；③ wasm APP 打包与签名格式（DEC-05）；④ 四板 + native_sim 的内存占用/性能实测（R1 待补项转入）；⑤ "LLEXT 作框架原生插件"的混合形态**未裁定**，如采用须另立 Q |
| DEC-18 | 2026-09-19 | 数据面应用层协议 = **zenoh**，Zephyr 侧采用嵌入式实现 **zenoh-pico**（Apache-2.0，官方 Zephyr 模块） | owner 原文："R2：选择zenoh-pico。"；DEC-08 重开后经 R2 初步笔记（草稿 v0.1，`docs/research/R2-protocol.md`）裁定。遗留设计题（HLD 必答）：① Zephyr 上传输层组合（UDP 单/组播已证实，TCP 及其他待核验）与 WiFi 组播可靠性；② 安全通道配置（zenoh 认证/TLS 选项）与密钥管理（合同 10：不经运行时自适应）；③ 断链判定参数——心跳/保活 → 失联检测时限（合同 3，须过默认值三问）；④ 逻辑节点寻址（DEC-02 遗留题：网关立方体终结 vs 协议多跳）；⑤ RP2350 外挂网络模块适配（DEC-14）；⑥ PC 侧 Agent 的 zenoh 客户端封装（DEC-12） |
| DEC-19 | 2026-09-20 | Zephyr 版本基线 = **4.4**；并采用**持续跟进最新 stable** 的升级策略 | owner 原文："Q-03：4.4（不断支持最新的zephyr系统）。" 升级纪律不变：manifest 钉具体版本 + 升级走显式提交 + 全量回归（`docs/std/versioning.md` §4）——"持续跟进"是升级**意图**，不是浮动引用 |
| DEC-20 | 2026-09-20 | zenoh 拓扑 = V1 立方体 **client**；router 宿主 = Windows/Linux PC **与 ARM64 Linux 工业/机器人主板** | owner 原文："Q-04：V1 立方体 = client，连PC（windows/linux）ARM64工业/机器人主板（Linux）。" 影响：prov 的 locator 配置面（Q-11⑤ schema 适用）；Agent 侧（DEC-12）宿主形态扩至 ARM64 Linux；UDP/TCP 单播 + TLS 维持建议 |
| DEC-21 | 2026-09-20 | APP 包格式 = **单文件容器：wasm + manifest(CBOR) + COSE-Sign1(ed25519)** | owner 原文："Q-05：单文件容器：wasm + manifest(CBOR) + COSE-Sign1(ed25519)。"（Q-05 提案原文采纳）；ts-appmgr 验签与 Agent 打包工具据此实施（LLD-ts-appmgr §2 TSAP v1） |
| DEC-22 | 2026-09-20 | 断链判定机制不变（心跳 → 本地 fail-safe）；**参数因超长物理链路而延长，且改为部署期可配（prov）**。出厂默认提案：心跳间隔 **1000ms**、丢失阈值 **6**（检测上界 ≈6s）；WDT 独立 **10s**；M3 标定须含长链路场景 | owner 原文："Q-08：需要考虑超长的物理链接距离时间应当延长。" 工程注记：长距离传播时延本身可忽略（百米级以太网 <1ms），预算实际覆盖多跳/重传/干扰抖动/慢速桥接；安全权衡如实记录：检测窗口延长 = 失联后输出维持上次指令值更久（本地限幅/三安全态机制仍生效），故参数**必须部署期可配**，紧时限部署可收紧 |
| DEC-23 | 2026-09-20 | 存储分区 = **双 APP slot(a/b) + meta 区**（版本指针/回滚计数）；固件 OTA 走 **MCUmgr**，UART 为救砖底线 | owner 原文："Q-09：同意你的建议。"（= Q-09 提案 A 全文）；native_sim 以文件系统模拟分区（LLD-ts-store） |
| DEC-24 | 2026-09-20 | CI = **GitHub Actions**；远端 = GitHub 仓库（建议 public，与 DEC-16 一致）；LICENSE（Apache-2.0）随 M0 首批提交补齐 | owner 原文："Q-12：同意你的建议。" 远端地址待 owner 创建后提供（或授权 gh CLI 创建） |
| DEC-25 | 2026-09-21 | V1 WAMR 执行模式 = **fast 解释器 + WASI 全关**（框架自建 `ts_*` 最小导入面 = 权限硬边界落点）；**AOT 留作 Agent 构建期选项**（不改变单包分发型态） | owner 原文："Q-06：确定V1 = fast 解释器 + WASI 关 + AOT 留作构建选项。" 内存/性能实测（M2）据此基线 |
| DEC-26 | 2026-09-21 | 逻辑节点 V1 **仅预留，不实现多立方体并联**（命名空间 node 层 + 资源逻辑名间接层已就位；单立方体部署时 node = cube id） | owner 原文："Q-07：确定V1 仅预留逻辑节点、不实现并联。" DEC-02 遗留题（拓扑/编址/仲裁）推迟至硬件阶段前专项 HLD |
| DEC-27 | 2026-09-21 | Q-10 裁定：**14 项按建议值**（含 DEC-22 联动后的 WDT 10s 等）；**#10 WAMR 实例堆 = 每板动态配置**（板级配置/构建期生成，默认值见 HLD §4.6 每板表；M2 实测按行修订） | owner 原文："Q-10：其他按照推荐值，WAMR 堆需要根据板卡动态配置。" 分层纪律（框架安全数据必须内部 SRAM）随本 DEC 生效 |
| DEC-28 | 2026-09-21 | **板卡策略（修订 DEC-14）**：框架面向未来、优先高性能高配置板卡；资源不足的芯片/板卡放弃——**RP2350 移出目标集**（Zephyr 无 PSRAM 驱动 + 520KB SRAM，不符取向）。目标板集 = **ESP32-S3 / ESP32-P4 / STM32H7 + native_sim（CI）** | owner 原文："另外我要强调我们的框架主要面向未来，更多考虑高性能高配置板卡，如果某些板卡资源不足例如RP2350，则放弃该芯片/板卡。" DEC-18 备注"RP2350 外挂网络模块适配"随之关闭；后续高性能板（如新 ESP32/P 系列、H7+）可按此标准扩充 |
| DEC-29 | 2026-09-21 | Q-11⑥：**内存预算按板动态分配计算**——构建期按板生成预算表（分配规则与每板默认见 HLD §4.6），不再维护单一全局表 | owner 原文："Q-11：内存预算分配表需要根据不同板卡动态分配计算。"（Q-11①-⑤ 本轮回复未涉及，**仍待 owner 明示**） |
| DEC-30 | 2026-09-21 | Q-11①-⑤ 按建议值：① **sys 命令面 v1** = 7 命令，host-only（APP 能力文法不可达），estop-clear 需确认令牌；② **共享通道写 = 后写胜出 + 审计含 app_id**（不做独占 claim）；③ **APP 业务状态 V1 不持久化**（升级/回滚后归零）；④ **审计留痕 V1 = 内存环形 + get-audit 导出**（掉电丢失，接受此权衡）；⑤ **prov 数据模型 = CBOR schema v1**（运行时只读，仅烧录通道写） | owner 原文："对于Q-11，这些配置按照建议值"。至此 **Q-01…Q-12 全部裁毕**（对应 DEC-17…30，共 14 项裁决） |
| DEC-31 | 2026-09-21 | Q-13 按建议 A：V1 **禁止 APP 自建线程**（WAMR 线程/共享内存特性编译期不启用；ts_api_v1 不提供创建导入——"能力不存在"而非运行时配额）；并发 = 事件模型 + 语言内协作式并发 + APP 间 SMP 并行；预留 manifest v2 `threads` 字段（V1 不实现） | owner 原文："可以了我们现在开始开发把吧……"（"可以了"视为对 Q-13 建议 A 与人工检查三项的确认——如有误请 owner 纠正，本行即改）。**同批确认**：C-1 HLD v0.2.x / C-2 LLD v0.2.x 批次 / C-3 规范套件批准生效（tag `std-v1`）；M0 开工授权；开发环境 = `D:\Software\project\zephyrproject`（深查结论见 AGENTS.md 当前状态） |
| DEC-32 | 2026-09-21 | **Agent 运行平台仅 Linux**（Windows 不支持——修订 DEC-20 宿主范围，移出 Windows PC）；**开发环境整体迁移至 WSL2**（Ubuntu 24.04：仓库 `~/tessera` + Zephyr 工作区 `~/zephyrproject`）；Windows 侧 zephyr 环境复原至 owner 原状（main 检出） | owner 原文："既然如此我希望请你复原我在windows上的zephyr环境，然后将我们整个project迁移至wsl，并记录，当前我们的agent不支持在windows下运行只做linux支持。" 环境迁移记录见 `docs/dev-environment.md` |
| DEC-33 | 2026-09-22 | **Agent 基座 = pi（earendil-works/pi，MIT）作进程内库内核** + 官方 MCP TS SDK 2.x 门面 + 自研 Tessera 工具集（TypeScript，Node ≥22）；**架构必须为多域 Agent 预留**（未来引入 PCB AI Agent 开发、外壳/结构件开发等多种流程自动化）；**北极星目标：平台应用于机器人或 Galatea 项目时能完全自动化地"自己生产自己"** | owner 原文："Q-14：建议采用PI进行构建，同时需要为未来我们引入PCB AI Agent开发，外壳/结构件开发等多种流程的自动化预留，最终目标是该项目应用于机器人或我们的D:\Software\project\Galatea项目时能够完全自动化的自己生产自己。" 落地约束（Agent HLD 输入）：① V1 范围不变——固件域是第一个工具域；② 平台层（会话编排/任务管理/审计）与域工具集解耦，新域 = 新增工具包不改平台；③ 跨域组合走 MCP（DEC-34 双层天然支持：域 agent 互为 MCP server/client，可被上层编排 agent 驱动）；④ 北极星为方向约束，不扩大 V1 交付范围 |
| DEC-34 | 2026-09-22 | **MCP 工具面 = 双层**：原子工具层必开（build/simulate/package/sign/deploy/provision/query…——"Agent 无豁免"检查与可测性落点，人类与成品 agent 均可直接调用）+ 高层任务工具层 V1 先 2-3 个（develop_app 等，DEC-12 能力链交付形态）；全部长任务工具按 **MCP Tasks extension** 句柄化（taskId/ttlMs/pollIntervalMs + 轮询/订阅，旧客户端同步回落）；工具面增删 = Agent 特有 review 门 | owner 原文："Q-15：认可双层选择。" 事实依据 R3 §4.6/§7；具体工具清单在 Agent HLD 定稿（走门 ③ 公共 API 变更）。**实现机制已被 DEC-36② 细化**（Tasks extension 客户端采用为零 → 自定义句柄+轮询工具，语义对齐 Tasks V2） |
| DEC-35 | 2026-09-22 | **ACP 二级人机接口：V1 不做，仅架构预留**——会话编排层与传输解耦（Agent HLD 须明确该边界），后补 ACP 适配模块即可启用 Zed/JetBrains 人肉驱动 | owner 原文："Q-16 · ACP 人机接口（此前详解已呈，补 R4 证据后重呈）：我们进行预留。V1 不做。" 对象 = Zed/JetBrains 的 Agent Client Protocol（与已并入 A2A 的 IBM 同名 ACP 区分，names.md 已登记命名陷阱） |
| DEC-36 | 2026-09-22 | **Q-17 四子项全部采纳（Agent 交互栈定案）**：① 对外合同 = **MCP 唯一**（DEC-12 维持；stdio 起步 + Streamable HTTP 预留；实现纪律 = stateless-first 对齐 spec 2026-07-28 + 2025-11-25 兼容基线回归 + 规避弃用特性 Roots/Sampling/Logging/SSE/elicitation 依赖，"需更多信息"建模为工具结构化返回）；② 长任务 = **自定义任务句柄 + status/log 轮询工具**（语义对齐 Tasks V2 tasks/get/update/cancel，官方普及后平滑切换——细化 DEC-34 实现机制）；③ 领域能力分发 = **Agent Skills 开放标准**（SKILL.md；V1 随 agent 附最小固件域 skill 集；docs MCP server 可选后置）；④ 多域组合默认 = **上层编排 + 域 agent 各自 MCP 面**；**A2A v1.0 明确预留**（跨主体/长周期对等场景——如 Galatea 规模——时启用） | owner 原文："Q-17 · 交互栈确认：全部采纳，但要记录A2A的预留。" **A2A 预留记录点（owner 特别要求）**：本 DEC + `docs/names.md` A2A 行（生效·预留）+ Agent HLD 架构预留节（agent 身份/Agent Card/对等任务委托的接入缝）。watch 项：agentgateway（部署治理）、MCP roadmap agent 身份/委托线（DPoP/WIF/ID-JAG） |
| DEC-37 | 2026-09-22 | **Q-18 裁定 C：Agent 实现 = 全 Python（PydanticAI v2 + FastMCP 门面 + 自建最小编码工具集）**——修订 DEC-33 基座条款（pi 库内核 → Python 框架 + 自建循环；实现语言 TypeScript → Python）；DEC-33 北极星与落地约束（多域预留 / 平台层解耦 / 跨域组合走 MCP / V1 范围不变）**全部沿用**；owner 动因 = 完全不熟 Node，全部自研代码必须 owner 可 review | owner 原文："Q-18：C，同时请你完整review一边之前的design是否需要进行一定的调整。有调整的地方需要重新research。" 派生修订：① DEC-36③ Skills 加载从"pi 原生支持"改为**自建 skill loader**（对外分发形态不变）；② beforeToolCall 等效闸 = PydanticAI 工具包装/中间件（R5 核验落点）；③ Agent 侧 TSAP 打包签名（DEC-21）与 zenoh 客户端封装（DEC-18 备注⑥）改用 Python 栈（R5 核验 cbor2/COSE-Sign1/ed25519/zenoh-python）；④ Q-18 涟漪审查见 `design/design-review-02-agent-python-ripple.md`（固件设计套件零改动结论留档） |

## 二、问题登记（Q）

### 问题批次（Agent 轨道呈递，2026-09-22；**Q-14…Q-18 均已裁 → DEC-33…37，待裁清零**）

#### Q-14 · Tessera Agent 基座选型（2026-09-22 呈递，owner 指令触发）

- **状态**：**已裁 → DEC-33**（2026-09-22：按建议 A 采用 pi；owner 附加北极星约束——多域 Agent 预留 + 最终"自己生产自己"）。
- **背景**：DEC-12（Agent = MCP server，封装"模块 API + 模拟器 + 构建工具链"，LLM 用户自选，PC 侧）、DEC-11（产出 = 业务 APP **与** 硬件配置）、DEC-13（模拟 = native_sim + 外设桩）、DEC-32（宿主仅 Linux）已定 Agent 的形态边界；能力链 = 需求分析 → 软件设计 → 编程开发 → 模拟测试 → 部署。owner 2026-09-22 指令：**Agent 核心基于现有 agent/框架**（点名 OpenCode、pi）**且必须可封装为 MCP server 被其他 Agent 调用**——自研循环被排除为主路线，需裁决基座选什么。调研事实（`docs/research/R3-agent-foundation.md`，2026-09-22 实查）：生态重大变化（OpenCode 迁库 anomalyco；pi 迁库 earendil-works 并公司化、Armin Ronacher 深度加入；MCP 治权移交 Linux Foundation AAIF，spec 现行版 2026-07-28）；**没有任何候选原生支持"自身暴露为 MCP server"——该外壳一律用官方 MCP SDK 自建**（各方案共同的固定工作量，差异只在壳与核心之间隔几层）；硬伤出局组：Claude Agent SDK（运行时闭源二进制 + 仅 Anthropic 协议模型，违反提供者无关）、Gemini CLI（锁 Google 系模型）、Crush（FSL 许可证含竞争限制）、Aider（2026-02 起停更 + 结对编辑器架构非 agent 运行时）、Amazon Q CLI（已归档）。
- **通俗解释**：**基座** = 现成的 agent 运行时（LLM 循环 + 工具调用 + 会话管理 + 文件编辑工具都做好了），我们只挂 Tessera 专用工具（构建/仿真/打包签名/部署）再封一层 MCP 壳。**嵌入两型**：库（agent 循环跑在我们自己进程里，单进程，封装薄、控制力强）vs 服务/子进程（基座独立运行，我们经 HTTP/JSON 驱动，两进程，封装厚）。**候选名对照**：OpenCode = 当前最流行开源 coding agent（原 sst 现 anomalyco，MIT，v1.18.x，208k stars，周更）；pi = "AI agent 工具箱"（原 badlogic 现 earendil-works，MIT，v0.87.x，108k stars，主打可拆开当库用）；goose = Block 的 MCP-first agent（Apache-2.0，Rust，v1.29.x，扩展体系=MCP server）。**"被封装为 MCP"** 指 server 侧（别人经 MCP 调我们），与 client 侧（agent 用别人的 MCP 工具）是两回事——前者都要自建。
- **选项**：A. **pi 作核心（进程内库：`createAgentSession`/`Agent` 类）+ 官方 MCP TS SDK 2.x 门面 + 自研 Tessera 工具集**（TypeScript，R3 方案 A）；B. **OpenCode 作核心（`opencode serve` + @opencode-ai/sdk 驱动）+ MCP 桥**（TypeScript，双进程，R3 方案 B）；C. **goose 作核心（headless/daemon 驱动）+ MCP 桥**（R3 方案 C）；D. **PydanticAI v2 + FastMCP v4 自建循环**（Python，R3 方案 D——唯一官方支持 agent 双向 MCP 的框架线，但会话/编辑工具/上下文全自建）；E. Claude Agent SDK + LiteLLM 代理双底层（违反硬-1 提供者无关，仅保底参考）。
- **建议**：**A**。理由（R3 §5/§6）：① 嵌入形态最优——单进程，MCP 门面进程内直接创建 agent 循环，无跨进程跳数，封装层最薄（B/C 都要驱动一个为"人类交互"设计的通用服务）；② 工具面控制最精——内置工具默认只开 read/write/edit/bash，`defineTool` 挂 Tessera 工具，`beforeToolCall` 钩子可阻断+改写 = "Agent 无豁免"检查链的强制落点；③ 会话可纯内存（`SessionManager.inMemory()`）+ JSONL 树结构 = 确定性合同（安全合同 9）在 Agent 侧的同构延伸（任务可重放审计）；④ 提供者无关达标（30+ 提供者、models.json 自定义 OpenAI-compatible 端点、llama.cpp 原生）；⑤ 风险可控——0.x 版本 churn 用"钉精确版本 + 自有薄抽象缝（AgentCore 接口）"隔离，核心可换（→B/C），MIT 允许极端时 fork 自维护；Armin Ronacher 将 pi 用作 OpenClaw 基座 + 生态 5,500+ 包，废弃风险实际较低。**B 为第一备选**（若更看重 1.x 成熟度、内置审批式权限引擎、最大社区，接受双进程封装厚度）。
- **影响**：agent/ 目录技术栈 = TypeScript（Node ≥22），npm 依赖钉版纳入 `docs/std/versioning.md` 纪律；固件 Python 工具链（west/twister/pytest/模拟器）经子进程复用不重写；MCP server 用官方 TS SDK 2.x scoped 包，长任务工具按 MCP Tasks extension 设计；若选 B/C/D，语言与封装层相应变化（D → Python）。

#### Q-15 · MCP 工具面形态（对外暴露粒度，2026-09-22 呈递）

- **状态**：**已裁 → DEC-34**（2026-09-22：双层）。
- **背景**：DEC-12 定 Agent = MCP server，但对外暴露什么粒度未定——这决定"其他 Agent 调用 Tessera Agent"时的职责分界。上层调用方（ZCode/Claude Code/Cursor/goose…）本身是强 agent：若只给原子工具，"智能"在调用方；若给高层任务工具，Tessera Agent 内部（其 LLM 由用户在 Agent 侧配置）跑完整能力链后交付。工具面变更属 Agent 特有 review 门（FOUNDING_PROMPT §6 / AGENTS.md），首次定型须 owner 裁决。另实测各 MCP 客户端超时仅 7~60s，而完整开发链分钟~小时级——长工具必须按 **MCP Tasks extension**（2026-07-28 spec 转正：`tools/call` 立即返回任务句柄 taskId/ttlMs/pollIntervalMs，客户端轮询或订阅通知，旧客户端回落同步路径）设计。
- **通俗解释**：**原子工具** = 一个动作一个工具（构建固件/跑仿真/打包签名/部署……），像一组 API，调用方自己编排；**高层任务工具** = 一句话交任务（"开发一个温控 APP"），Tessera Agent 内部跑需求分析→设计→编程→模拟后交付产物，像外包；**双层** = 两种都开。
- **选项**：① 仅原子层（约 10-15 个：workspace/build/simulate/package/sign/deploy/provision/query-status/get-audit…）；② 仅高层任务层（2-4 个：develop_app/design_hw/deploy_package）；③ 双层——原子必开 + V1 先 2-3 个高层任务工具。
- **建议**：③。原子层是"Agent 无豁免"与可测性的落点（每步产物可单独检查/重放，人类也可直接用 MCP 客户端调用，还是成品 coding agent 作前端的天然接口）；高层层是 DEC-12 能力链的交付形态（调用方省心）；全部长工具统一按 Tasks 句柄化。
- **影响**：agent/ 的 MCP server 工具注册结构与文档；高层工具的进度报告语义；后续每次工具面增删均走 review 门。

#### Q-16 · ACP 二级人机接口（V1 范围，2026-09-22 呈递；同日 owner 问询触发补呈详解）

- **状态**：**已裁 → DEC-35**（2026-09-22：V1 不做，仅架构预留）。
- **背景**：ACP（Agent Client Protocol，Zed+JetBrains 共治，v1 stable / v2 draft）= "agent 客户端"与"agent"之间的标准协议，与 MCP 互补（ACP = 客户端 ↔ agent 的人机集成；MCP = agent ↔ 工具/被其他 AI 调用）；主要 coding agent 均已支持（goose/OpenCode/Gemini 原生；pi 经社区适配器 svkozak/pi-acp）。
- **通俗讲解（2026-09-22 补呈）**：
  - **ACP 是什么**：类比 LSP——LSP 让任何编辑器能接任何语言服务器，ACP 让任何"agent 客户端"能接任何 agent。传输 = JSON-RPC over stdio：客户端（编辑器）把 agent 作为**子进程**启动，双方交换结构化消息。
  - **它解决的问题**：每个 coding agent 各有自己的 CLI/TUI，人类想在编辑器里用 agent，就得"每个编辑器 × 每个 agent"逐对写集成。ACP 统一了消息集——**agent 汇报**："我要读这个文件 / 我要跑这条命令 / 我改了这些文件（diff）/ 这个操作需要批准 / 任务进行到哪"；**客户端负责渲染**：对话窗、diff 视图、权限弹窗、进度条。编辑器实现一次 ACP 就能接所有 ACP agent；agent 实现一次 ACP 就能被所有客户端驱动。
  - **对 Tessera Agent 的作用（有/无对比）**：
    - **无 ACP（现状计划）**：与 Agent 交互两条路——① MCP 客户端（ZCode/Claude Desktop/Cursor 等）调它的 MCP 工具，交互对象是**另一个 AI**，owner 看到的是工具调用日志；② 我们若自带 CLI，则是纯文本日志界面。
    - **有 ACP**：owner 在 Zed/JetBrains 里**对话式人肉驱动同一个 Agent**——实时看到它每一步调了什么工具、每个文件的 diff、逐条批准/拒绝权限请求。同一个 agent 核心、两种前端：MCP 面向 AI 调用方，ACP 面向人类。
    - **延伸价值**：调试/演示体验质变（agent 行为可视化，排查"它为什么这么做"不再翻日志）；不绑定任何特定 MCP 客户端；未来 PCB/结构件域 agent（DEC-33）同样可挂 ACP 让工程师人肉介入——多域预留的自然延伸。
  - **实现方式（本计划中的形态）**：
    - **位置**：tessera-agent 单进程内，ACP 适配模块与 MCP 门面**平级**，都坐在"会话编排层"之上（架构预留点即在此：编排层不绑定单一传输，加一种前端 = 加一个适配模块）。
    - **数据流**：适配模块订阅 pi 会话事件（`subscribe`：消息/工具调用/diff）→ 翻译成 ACP 通知下发编辑器；编辑器里的用户输入 → `prompt()`/`steer()`；权限应答（允许/拒绝）→ `beforeToolCall` 钩子的放行/拒绝——与"Agent 无豁免"检查链共用同一闸口。
    - **进程模型**：编辑器把 tessera-agent 作为子进程拉起（stdio 上跑 JSON-RPC）；与 MCP 门面（独立长驻进程）互不干扰，同一份会话/工具实现。
    - **pi 侧先例**：官方 pi-acp 已移出 monorepo，现行社区适配器 svkozak/pi-acp = 桥接 `pi --mode rpc`（JSONL over stdio）——证明"pi 会话 ↔ ACP 消息"的翻译模式可行；我们是在自己进程内直接挂会话层做同样的事（少一层 RPC）。
    - **成本/风险**：适配模块约数百行 TS + 一组会话翻译测试；ACP v2 尚在 draft（v1 stable），接口仍有演进——**后补者天然吸收协议演进成本**，这是建议 V1 不做的理由之一。
- **选项**：A. V1 不做，仅架构预留（会话编排层与传输解耦，后补适配模块即可启用）；B. V1 即附带 ACP 适配（Zed/JetBrains 从第一天可人肉驱动 Tessera Agent）。
- **建议**：A。V1 主合同是 MCP（DEC-12）；ACP 是人机体验增强、不影响能力面；解耦到位后补成本低；v2 draft 期的协议演进由后补者吸收。
- **影响**：A 几乎零额外成本（解耦本就是应做架构，仅要求 HLD 明确编排层/传输边界）；B 增一个适配模块与测试面，换来 V1 期间的可视化调试体验。
- **R4 证据补强（2026-09-22 重呈）**：Zed ACP 客户端已达 **80+**（JetBrains 官方内建、VS Code 系经扩展、各聊天软件桥），agent 侧 30+，另有 ACP Registry；v2 draft（2026-07-20）演进中（摆脱 turn 模型、结构化 diff），官方建议生产不默认开 v2。**命名陷阱**：Q-16 对象是 Zed/JetBrains 的 ACP（编辑器↔agent）；IBM 的同名 Agent Communication Protocol（agent↔agent）已于 2025-08 并入 A2A 消亡，勿混淆。建议不变：A（V1 不做仅预留）。

#### Q-17 · Tessera Agent 交互栈确认（2026-09-22 呈递，R4 结论）

- **状态**：**已裁 → DEC-36**（2026-09-22：四子项全部采纳 + A2A 预留显式记录）。
- **背景**：owner 指出 DEC-12 的 MCP 选择基于其既有知识、未必最新最前沿，指令第二轮调研（R4，`docs/research/R4-agent-interaction.md`）。R4 结论：**MCP 不但没过时，反而刚完成现代化大版本（2026-07-28 stateless 断代）并已捐入 Linux Foundation AAIF 中立治理**；协议战争已收敛为分层栈（MCP+A2A v1.0+AGENTS.md 同伞 AAIF；Agent Skills 成能力分发开放标准；无颠覆者）。但 2026-07-28 断代 + 客户端现实差异要求实现纪律更新，另有 Skills 分发一项新增建议——涉及选型与对 DEC-34 的实现级细化，按门 ① 呈递。
- **通俗解释**：
  - **AAIF / open agentic stack**：Linux Foundation 旗下基金会（2025-12 成立），Anthropic 捐 MCP、OpenAI 捐 AGENTS.md、Google 系 A2A 2026-08 入会——三大件同伞，事实上的"agent 互操作标准栈"；R4 判定协议层无颠覆者，押注该栈 = 押注主流。
  - **stateless-first**：2026-07-28 起 MCP 协议去会话化（服务器不保存连接状态、能力随每次请求携带）——新 server 从第一天按此设计，同时兼容旧客户端（以 2025-11-25 语义为回归基线）。
  - **长任务现实**：官方 Tasks extension 虽转正但**尚无客户端支持**（实测惯例 = 工具立即返回任务号 + 独立查询工具轮询；Claude Code 超 2 分钟自动转后台、Codex 硬超时 600s）——立即返回是唯一安全模式。
  - **Agent Skills**：SKILL.md 目录格式的"领域能力包"开放标准（Anthropic 2025-12 开放，45+ 工具支持，**pi 内核原生支持**）——把固件域知识（构建流程/军规/TSAP/命名空间）打包分发，任何 agent 拿到即懂我们的工具链；学术基准 IoT-SkillsBench（378 次真机实验）证明专家 skills 使嵌入式 agent 成功率接近满分。
- **选项（4 子项，可整体"按建议"或逐项例外）**：
  - ① **对外合同维持 MCP 唯一**（DEC-12 不变）：stdio 起步 + Streamable HTTP 预留；实现纪律 = stateless-first（对齐 2026-07-28）+ 2025-11-25 兼容基线回归 + 规避弃用特性（Roots/Sampling/Logging/SSE/elicitation 依赖，"需更多信息"建模为工具结构化返回）。
  - ② **长任务机制细化**（DEC-34 实现细节修订）：不依赖 Tasks extension（客户端采用为零），落地为**自定义任务句柄 + status/log 轮询工具**；内部语义对齐 Tasks V2（tasks/get/update/cancel），官方普及后平滑切换。
  - ③ **领域能力分发采用 Agent Skills 开放标准**：V1 随 agent 附最小固件域 skill 集；文档型知识可选配套 docs MCP server（Espressif 官方先例，解决模型训练截止问题）。
  - ④ **多域组合模式**：默认 = 上层编排 + 域 agent 各自 MCP 面（agents-as-tools，2026 生产主流）；**A2A v1.0 仅预留**（跨主体/长周期对等场景，如 Galatea 规模）；AGENTS.md 维持现状（已 AAIF 标准）。watch：agentgateway（部署治理）、MCP roadmap 的 agent 身份/委托线。
- **建议**：①②③④ 全部采纳。①④ 为确认与预留（零新增成本）；② 是 R4 发现的现实约束修正（不采纳则长工具在真实客户端上必超时）；③ 新增但低成本高收益（pi 原生支持 + 学术佐证 + 解决训练截止痛点）。
- **影响**：Agent HLD 交互层规格（stateless 设计/句柄式返回/弃用规避清单）；agent/ 增 skills 目录与最小 skill 集；后续上线时 MCP Registry 占名（工程事项，不另开 Q）。

#### Q-18 · Agent 实现语言（TypeScript/Node vs Python vs Rust，2026-09-22 呈递，owner 问询触发）

- **状态**：**已裁 → DEC-37**（2026-09-22：C——全 Python，PydanticAI + FastMCP + 自建编码工具集；修订 DEC-33 基座条款）。
- **背景**：DEC-33 定 Agent 基座 = pi（进程内库）+ 官方 MCP TS SDK 门面 + 自研工具集，实现语言随之 = TypeScript/Node。owner 问询：可否改为 Python 或 Rust 开发？语言选择与基座用法**强耦合**：pi 只以 TS 库形式存在（R3 §4.1 实查：包 @earendil-works/pi-coding-agent 内含 SDK，`createAgentSession`/`Agent` 类 import 使用；另有 `pi --mode rpc` 子进程 JSONL 模式供非 Node 宿主集成）；换语言 = 换 pi 的使用方式或换基座。语言运行时性能不构成决策因素（Agent 是 PC 侧编排器，瓶颈在构建/仿真子进程）。
- **通俗解释（关键耦合点）**：选 TS 不是因为 Node 本身更优，而是 **pi 这个 agent 内核只有 TS 库形态**——只有同语言直接 import，才能拿到 DEC-33 的两个决定性优势：单进程最薄封装（MCP 门面与 agent 循环同进程，无跨进程跳数）+ `beforeToolCall` 进程内钩子（可阻断/改写工具调用 = "Agent 无豁免"的宿主侧闸）。换语言的两条路：① pi 照用但降级为**子进程经 RPC（stdio JSONL）驱动**——基座保留，多一层进程间通信；权限闸改为"自定义工具内部强制 + 一个小型 pi 扩展（JS，随 pi 子进程加载）兜底内置工具"；② 弃 pi 换语言原生框架（Python = PydanticAI + FastMCP 自建循环，即 R3 方案 D；Rust ≈ 全自研）。
- **选项**：
  - A. **维持 TypeScript/Node**（DEC-33 不变）：pi 进程内库——最薄封装、钩子全控、单进程。
  - B. **Python 宿主 + pi RPC 子进程**：保留 pi 基座；MCP 门面改用官方 Python SDK / FastMCP（Tier-1 成熟）；与固件工具链（west/twister/pytest）同生态，胶水层可原生调用同语言异常处理而非子进程 JSON 解析；代价 = 一层 RPC + 强制点移位（工具内 + JS 小扩展）。
  - C. **Python 全自研**（PydanticAI v2 + FastMCP，R3 方案 D）：纯 Python；但会话管理/文件编辑工具/上下文策略全自建，违背 owner"基于现有 agent"指令精神。
  - D. **Rust**：pi 不可用；goose crate 无稳定公共 API（R3 ⚠️未核验其承诺）；MCP Rust SDK（rmcp，goose 所用）成熟度低于 TS/Python Tier-1；基本等于全自研——工程量最大、迭代最慢。
- **建议**：**A 维持**（DEC-33 理由仍然成立：pi 进程内嵌入是决定性优势，语言是基座的从属选择；固件 Python 工具链经子进程复用的成本已评估可接受——west/twister 本就是 CLI 优先设计）。若 owner 更看重**与固件 Python 工具链同生态**或团队 Python 熟悉度，**B 是可接受变体**（保留基座决策，仅语言层修订；且强制点移入工具内部反而更硬——闸在产物必经路径上）。C/D 不建议。
- **影响**：选 A 无变化；选 B → DEC-33 语言条款修订（TypeScript → Python 宿主 + pi RPC），agent/ 结构 = FastMCP/官方 Py SDK 门面 + pi 子进程管理器 + JS 小扩展（进程内闸）+ Python 工具集，Agent HLD 按此展开；选 C/D → 基座决策重开（须重新走门 ⑤ 技术栈变更）。
- **owner 动因澄清与建议修订（2026-09-22）**：owner 原文——"主要原因在于我对node完全不熟悉，是否有基于Python的Agent框架可以使用？"——**owner 对全部自研代码的 review 可读性成为一等约束**，重新评估。
- **Python 框架版图（应答 owner 问询）**：① **PydanticAI v2**（MIT，pydantic 公司，极活跃）= 最适合的 Python agent 框架：类型安全工具调用与结构化输出（可强制 agent 产出经校验的 plan/硬件配置——恰合本项目纪律）、多提供者（含本地 **OllamaModel**）、**原生 Temporal 持久执行**（每步事件日志、故障后恢复/重放——契合审计与确定性重放需求）、官方支持 agent 嵌入 MCP server（与 FastMCP 协同，R3 实查为唯一双向 MCP 框架线）；② OpenAI Agents SDK（0.x，OpenAI 优先）；③ Strands（AWS，MCP-first SDK）；④ smolagents（HF，轻量）；⑤ CrewAI/AG2/LangGraph = 编排框架，过重。**关键事实：Python 生态没有健康的"成品 coding agent 内核"**——aider 停更且为结对编辑器架构（R3 出局）；OpenHands 是平台非嵌入库；pi/OpenCode/goose 均非 Python。Python 路线的固有代价 = 自建文件编辑/shell 工具与会话日志（V1 评估为有界工作量：本项目强纪律工作流对"自由编码"依赖度低，编码工具只需 read/write/apply_patch/exec 四件）。
- **建议修订（2026-09-22，替代原建议 A）**：改推 **C（PydanticAI + FastMCP 全 Python）**——owner 约束（完全不熟 Node）使"全部自研代码可 review"的权重高于 pi 内核便利；单 Python 进程（无 RPC 跳数、无任何 JS）；类型化输出与持久执行是正收益。**B 细化为 B1 备选**：Python FastMCP 门面+工具 + pi 子进程，工具经 pi-mcp-adapter 以 MCP 回接（自研代码仍全 Python，pi 为原封二进制依赖）——若 HLD 复核发现自建编码工具面风险超预期再启用。A 降为"无语言约束时的技术最优"；D 维持不建议。
- **影响（修订后）**：选 C → DEC-33 基座条款修订（pi 库内核 → **PydanticAI 框架 + 自建最小编码工具集**，语言 = Python，仍满足 owner"基于现有 Agent 或框架"原始指令——"或框架"明文在列）；agent/ = 单 Python 进程（FastMCP 门面 + PydanticAI agent 循环 + 自建工具集 + skills 分发）；HLD 须复核自建三项工作量清单（编码工具/会话日志/上下文管理）。

### 问题批次（design 阶段呈递；Q-01…Q-13 均已裁）

#### Q-13 · APP 线程模型与并发限制（2026-09-21 呈递，owner 问询触发）

- **状态**：**已裁 → DEC-31**（2026-09-21：按建议 A，禁止自建线程 + 三层限制机制）。
- **背景**：LLD-ts-appmgr 定义"每 APP 一个框架线程"，owner 问询：① APP 能否自建更多线程？② 若不能，一个线程是否够用？③ 是否应设计更合理的限制方式？事实核验（2026-09-21）：WAMR **内建 wasm pthread 库但默认关闭**（需编译开启 `WAMR_BUILD_LIB_PTHREAD` + wasm 以 `-pthread --shared-memory` 编译；每线程独立辅助栈，默认上限 4）；部分嵌入式打包配置不含线程支持。
- **选项**：A. V1 **禁止 APP 建线程**——WAMR 线程/共享内存特性编译期不启用 + ts_api_v1 不提供创建导入；并发 = 事件模型 + 语言内协作式并发 + APP 间并行（SMP）。B. V1 即开放（manifest 声明 max/stack + 运行时计数限制）。C. 按能力部分开放。
- **建议**：A。限制方式三层：① **编译期禁用**（"能力不存在"强于"运行时配额"，与符号装配硬边界同哲学）；② manifest 预算（现有 stack/heap 字段覆盖单线程）；③ **版本化预留**（manifest v2 增 `threads:{max,stack}`，权限门控后开 WAMR 特性——V1 不实现）。理由：单线程对业务编排足够；开放线程引入 APP 级竞态 → 破坏合同 9 重放确定性；线程资源失控（栈不可预算）；健康探针/卸载 join/trap 归属语义复杂化。
- **影响**：LLD-ts-appmgr §5（已按 A 预写〔Q-13 提案 A〕标注）、HLD §3.4 一行；manifest v1 定稿**不含** threads 字段；M2 健康探针标定需考虑长计算分块约定（tick 有界工作量）。

#### Q-03 · Zephyr 目标版本

- **状态**：**已裁 → DEC-19**（2026-09-20：4.4 + 持续跟进最新 stable）。
- **背景**：DEC-01 定 Zephyr 但未定版本基线；west manifest、外部模块（WAMR/zenoh-pico）兼容面、native_sim/CI 行为随版本变化（当前最新为 4.4，2026-04 发布、配 Zephyr SDK 1.0；3.7 为 LTS 但已近维护尾期）。不定版本 M0 无法初始化工作区。
- **选项**：A. 4.4（最新 stable）；B. 3.7 LTS（旧，外部模块新特性可能不兼容）；C. 4.x 中间版（若确有 LTS 分支，待核验）。
- **建议**：A（4.4）：WAMR 与 zenoh-pico 均活跃跟踪主线，native_sim/CI 基线最新；V1 周期内若 4.x 出新 LTS 再评估迁移（显式提交+全量回归）。
- **影响**：west manifest 基线与 SDK 安装；依赖升级策略（`docs/std/versioning.md`）。

#### Q-04 · zenoh 部署拓扑与传输

- **状态**：**已裁 → DEC-20**（2026-09-20：client；宿主含 ARM64 Linux 工业主板）。
- **背景**：DEC-18 定 zenoh/zenoh-pico 但未定端点角色与传输组合。zenoh 有 client（连 router）与 peer（对等）角色；Zephyr 上 UDP 单/组播、TCP 均可用（R2 v0.2 核验），TLS 经 mbedTLS（`Z_FEATURE_LINK_TLS` 默认 OFF，须显式开）。拓扑决定断链语义与 Agent 侧形态。
- **选项**：A. V1 立方体 = client，连 PC 侧 zenohd router（UDP/TCP 单播 + TLS）；peer/组播发现留逻辑节点阶段。B. V1 即 peer 对等（组播 scouting，无 router）。C. 混合。
- **建议**：A：断链判定单跳清晰、Agent 天然在 router 侧、实现面最小；WiFi 组播可靠性未实测前不押 B。
- **影响**：ts-net 实现面；Q-08 标定环境；Agent（DEC-12）封装对象；未来 peer 迁移成本（M3 评估）。

#### Q-05 · APP 包格式与签名方案

- **状态**：**已裁 → DEC-21**（2026-09-20：单文件容器 TSAP）。
- **背景**：DEC-05 要求网络分发+签名+版本化+回滚；DEC-17 定 WASM 后包 = wasm + manifest + 签名，格式未定。Agent 产物（DEC-11）与固件 ts-appmgr 双向依赖该格式，属公共文件格式（门 ③）。
- **选项**：A. 单文件容器：wasm 模块 + manifest(CBOR) + COSE-Sign1(ed25519)；B. tar/zip 多文件 + 独立签名；C. 复用 OCI 等成熟 artifact（嵌入式生态不适配）。
- **建议**：A：CBOR+COSE 为 IETF 嵌入式标准栈；ed25519 验签快、密钥小；打包（Agent 侧）与验签（固件侧）均可自动化。
- **影响**：ts-appmgr 验签实现；Agent 打包工具；根公钥烧录体系（合同 10）；版本比较与回滚规则（联动 Q-09）。

#### Q-06 · WAMR 执行模式与 WASI 裁剪

- **状态**：**已裁 → DEC-25**（2026-09-21：fast 解释器 + WASI 关 + AOT 留作构建选项）。
- **背景**：DEC-17 定 WAMR；执行模式与 WASI 开关未定。核验数据（R1 v0.2）：classic ~56KB / fast ~59KB（≈2× 性能）/ AOT 运行时 ~29KB（文件更大、按架构预编译、需 wamrc）；WASI 是 CVE 集中面（2.4.x 修 poll_oneoff 堆溢出）且扩大攻击/权限面。
- **选项**：A. fast 解释器 + WASI 关（框架自建最小 `ts_*` 导入面）；B. AOT 优先；C. classic（省 ~3KB、性能减半）。
- **建议**：A 起步：单一 wasm 包保持跨板迁移（DEC-04）；AOT 留作 Agent 构建期优化选项；WASI 全集关，权限面最小。
- **影响**：内存预算（M2 实测四板余量）；Agent 工具链复杂度；WAMR 升级回归范围。

**通俗解释（2026-09-20 补呈）**

- **执行模式 = WAMR 用什么方式跑同一个 wasm 文件**，三种：① **classic 解释器**——逐条"同声传译"字节码：最小（~56KB）但最慢；② **fast 解释器**——加载时先预处理成更快的形式再执行：+3KB 体积换约 2× 速度，仍是"翻译"；③ **AOT**——在 PC 上用 wamrc 工具**提前编译**成每种芯片的原生机器码：运行时最小（~29KB）、RAM 最省、接近原生速度，但**同一个 APP 要为每种板子生成一份**（分发复杂化）。
- **WASI = wasm 的标准系统接口库**（文件/时钟/网络等一套标准函数）。开了它 APP 能力大但：体积增大；沙箱上开的口子变大（与合同 10"权限清单是硬边界"相悖——我们要的是 APP 只能调用清单内的函数）；且 WAMR 的 WASI 实现恰是 CVE 集中处（2.4.x 刚修 poll_oneoff 堆溢出）。
- **建议重申**：V1 = **fast 解释器**（一个 wasm 包全板通用，符合"APP 与板卡解耦"）+ **WASI 全关**（改为框架自建一小套 `ts_*` 函数，APP 只能调用权限清单授权的函数——权限硬边界正落在这里）；AOT 不删除，留作将来性能不够时的 Agent 构建期选项。

#### Q-07 · 逻辑节点 V1 范围

- **状态**：**已裁 → DEC-26**（2026-09-21：V1 仅预留，不实现并联）。
- **背景**：DEC-02 要求多立方体并联为逻辑节点（拓扑/编址/仲裁为遗留题）；V1 主战场 native_sim 单实例（DEC-13/15），连接器与硬件形态第三阶段才定型。
- **选项**：A. V1 仅命名空间与接口预留（key 首段 node 层、资源编址经 ts-periph 间接化），不实现并联；B. V1 即实现 native_sim 多实例并联模拟。
- **建议**：A：避免硬件形态未定时固化协议细节；预留成本已消化在 HLD。
- **影响**：DEC-02 遗留题推迟至硬件阶段前专项 HLD；选 B 则 M3 范围显著扩大。

**通俗解释（2026-09-20 补呈）**

- **"逻辑节点" = 多个立方体拼在一起后，对外装作"一个设备"**（DEC-02 的核心）。例：1 个立方体 8 路 I/O；4 个拼成 2×2 大方块，立方体之间经扩展面里的数据线互通——理想形态是对网络/Agent 呈现"**一个** 32 路 I/O 节点"：一次连接、一个地址空间，不用关心某路 I/O 物理上在哪个立方体里。
- 由此产生三个必答题（DEC-02 遗留题）：① **内部谁当"班长"**（选一个立方体对外当网关，还是对等协商）；② **跨立方体编址**（第 3 个立方体上的 gpio5 叫什么名字——命名空间里预留的 `node` 段就是干这个的）；③ **安全仲裁**（estop 与保护必须每个立方体**本地**独立生效，内部连线断了也不能失控——安全合同第 8 条硬约束）。
- **Q-07 只问一件事：V1（现在这个 native_sim 仿真阶段）要不要就把多立方体联合行为做出来？** 建议：**不做，只预留**（命名空间 node 层 + 资源逻辑名间接层已就位）。理由：立方体怎么拼、扩展口里走什么线，要到第三阶段硬件定型才知道；现在实现等于在猜测上盖楼，硬件定型后大概率返工。

#### Q-08 · 断链判定参数（默认值呈递）

- **状态**：**已裁 → DEC-22**（2026-09-20：机制不变、参数延长且改 prov 可配；出厂默认 1000ms×6≈6s，WDT 10s）。
- **背景**：合同 3 要求失联→输出进安全态且检测时限有界可测。zenoh 链路 keepalive 参数可配（默认值待回源核验）。值过短→抖动误触发；过长→失控窗口大。
- **选项（初值提案）**：心跳间隔 500ms / 连续丢失阈值 4 / 检测上界 ≈2s（含实现裕量）；WDT 周期独立设 5s（防喂狗伪造，与心跳解耦）。
- **建议**：采纳初值进 M3 实测标定（WiFi/以太网抖动分布），标定后按默认值三问复核再定稿。
- **影响**：ts-net↔ts-safety 联动阈值；Agent 命令超时上界；重放测试虚拟时钟注入。

#### Q-09 · 存储分区与 OTA 策略

- **状态**：**已裁 → DEC-23**（2026-09-20：双 APP slot + meta；MCUmgr/UART 底线）。
- **背景**：DEC-05 要求 APP 版本化+回滚；DEC-07 定 UART MCUmgr/SMP 为救砖与 OTA 底线；固件自身 OTA 与分区表未裁，M2 依赖分区定义。
- **选项**：A. 双 APP slot(a/b) + meta 区（版本指针/回滚计数）+ 固件双 slot（MCUmgr img_mgmt，UART 底线、zenoh 通道后续可选）；B. 单 slot+备份区；C. APP 外置存储。
- **建议**：A：A/B 切换回滚最稳；native_sim 以文件系统模拟分区；meta 区仅验签成功后原子更新。
- **影响**：flash 预算（板间差异→slot 尺寸按板可配）；bootloader 信任链（M2 细化）；安全参数区烧录纪律（合同 10）。

#### Q-10 · LLD 批次默认值清单（2026-09-20 随 LLD 呈递）

- **状态**：**已裁 → DEC-27**（2026-09-21：14 项按建议；#10 WAMR 堆每板动态配置）。

- **背景**：LLD v0.1 批次（`design/LLD-00…LLD-ts-periph`）为可实现的规格，需落一批工程默认值（线程优先级/栈尺寸/队列与容量/探针与回滚参数等）。依军规 2"无 Q 不落盘"，逐项开 Q 将碎片化，故集中为一个可批量裁决的清单；LLD 中全部以〔Q-10 提案 n〕标注，**裁决前不进代码常量**。
- **选项**：A. 本清单批量裁决（逐项可例外）；B. 每项独立 Q 呈递（约 20 项，决策成本高）。
- **建议**：A。下表逐项含提案值与推导；批准后即成为代码常量出处（`/* 来源: Q-10 */`），后续调值走默认值三问 + 本条目修订。

| # | 常量 | 提案值 | 推导 / 越界后果 |
|---|---|---|---|
| 1 | 线程优先级（sysworkq / ts_net / ts_app / main） | 3 / 5 / 8 / 10 | 分层 = 安全巡检 > 通信 > 业务 > 监督；APP 永远抢不过框架（响应上界可推导）；颠倒则断链/喂狗延迟不可控 |
| 2 | 栈：sysworkq / ts_net / ts_app 上限 | 2048B / 4096B / 8KB | native_sim 经验起点；M1/M2 实测校准；过小=溢出（确定性灾难），过大=并发预算浪费 |
| 3 | 事件队列深度（ISR→sysworkq） | 16 | 事件率上界估算（遥测 200ms + 命令突发）；满 = 丢事件留痕（观测损失，非安全损失） |
| 4 | 每事件类型订阅上限 | 4 | V1 订阅者 = 框架内部模块数；满 = 启动期暴露 |
| 5 | 硬 WDT 周期 | min(2×max(子源周期), 10s) | DEC-22 延长为 10s 上界；过短=误复位，过长=卡死窗口大 |
| 6 | ts-safety 通道容量 / 审计深度 | 32 / 64 | V1 立方体 I/O 规模上界估计；审计深度 = 遥测合流周期内最大提交数 ×2 |
| 7 | ts-hal 实例容量 / ts-periph 描述符容量 | 24 / 24 | 与 V1 外设桩规模一致；不匹配 = 注册链断裂 |
| 8 | APP 健康探针周期 / 超时次数 | 1000ms / 3 | 业务 APP 响应预算 ≈ 3s 内必答；短则误杀，长则坏 APP 占位久 |
| 9 | 回滚计数上限 | 3 | 防"坏包循环回滚"的业界惯例 3 次；超限进 QUARANTINED |
| 10 | WAMR 实例堆上限 / APP 并发数 / tick 周期 | **每板可配**：内部 SRAM 基线 64KB；启用 PSRAM 池的板默认 256KB / 4 / 100ms | 2026-09-21 owner 问询 PSRAM 后修订：64KB 为 RP2350（520KB，Zephyr 无 PSRAM 驱动）与 native_sim 的基线；ESP32-S3 起 Zephyr 官方支持 SPIRAM，WAMR Alloc_With_Pool 池可放 PSRAM → 放宽；**分层纪律：框架安全数据（安全表/审计/喂狗/网络控制结构）必须内部 SRAM，仅 APP 沙箱内存可入 PSRAM**（事实与来源见 R1 §5.6；数值 M2 实测定） |
| 11 | ts-net 重连退避表 | 250/500/1000/2000ms 循环 | 固定表禁随机抖动（合同 9）；最长退避 < 断链检测上界（DEC-22 ≈6s）量级 |
| 12 | 遥测快照周期 / 发布缓冲 / 链路恢复滞回 | 200ms / 8 / 2 周期 | 快照 ≤ 心跳周期一半（观测新鲜度）；缓冲满丢最旧计数（尽力而为语义）；滞回防链路抖动乒乓 |
| 13 | ts-power 供电槽上限 | 4 | V1 立方体扩展面供电槽数估计 |
| 14 | ts-hal 输入轮询周期 | 100ms | 输入变化观测新鲜度；过短 = 空转开销，过长 = 遥测滞后（DR-02） |
| 15 | APP mailbox 深度 / 卸载 join 超时 | 8 / 2000ms | 事件突发缓冲；join 超时强杀防卸载挂死（DR-14） |

- **影响**：M1 起的全部代码常量出处；实测偏差时按行修订本表（不新开 Q，除非语义变化）；与 Q-08 参数的耦合关系如表内 #5/#11/#12。

#### Q-11 · design review-01 语义批次（2026-09-20 呈递）

- **状态**：**已裁**——⑥ → DEC-29（每板动态预算）；①-⑤ → **DEC-30**（2026-09-21，按建议值）。

- **背景**：design review-01（`design/design-review-01.md`，DR-01…17）暴露一批**语义级**设计决策未定义（非数值类，不属 Q-10）：sys 命令面与 estop 清除授权、多 APP 共享输出通道的写语义、APP 状态持久化裁剪、审计留痕 V1 简化、provisioning 数据模型、内存预算分配。不定义则 M1 实现无据。
- **选项**：A. 本批次批量裁决（逐项可例外，见建议列）；B. 每项独立 Q（6 项，决策成本高）。
- **建议**：A，全部按 review-01 提案：① sys 命令面 v1 = get-info/get-link/get-safety/get-budget/get-audit/set-time/estop-clear，**host-only**（APP 能力文法不可达），estop-clear 需确认令牌；② 共享通道写语义 = V1 **后写胜出 + 审计含 app_id**（不做独占 claim，避免死锁面；DR-05）；③ APP 业务状态 V1 **不持久化**（升级丢失，DR-15）；④ 审计留痕 V1 = 内存环形 + get-audit 导出（**掉电丢失**，DR-07）；⑤ prov 数据模型 v1（CBOR：node/cube id、router locators、根公钥×2、zenoh 凭证、功率预算、estop 触发沿；运行时只读、烧录通道写，DR-01）；⑥ 内存预算分配表按 HLD §4.6（数值为分配基线，实测按行修订不另开 Q，DR-06）。
- **影响**：ts-store/ts-hal/ts-net/ts-safety 的实现依据；HLD v0.2 与 LLD v0.2 对应节；与 Q-04（locator/凭证）、Q-05（根公钥）、Q-09（分区）耦合。

#### Q-12 · CI 平台与远端仓库托管（2026-09-20 呈递，M0 前置）

- **状态**：**已裁 → DEC-24**（2026-09-20：GitHub + Actions）。
- **背景**：M0 需建 CI 骨架与代码远端；仓库现为纯本地（无 remote）；`docs/std/testing.md` v0.1 定义了 CI job 结构但未点名平台（开发就绪度评估发现的基础设施选型缺口，属门 ①）。
- **选项**：A. GitHub + GitHub Actions；B. GitLab + GitLab CI；C. 自托管（Gitea/Woodpecker 等）。
- **建议**：A：与 DEC-16 开源定位一致、公开仓免费、Zephyr 社区 CI 先例与 twister 集成参考最多、artifact 留存便利；仓库建议 public 起步（与 Apache-2.0 定位一致），owner 创建远端后提供地址。
- **影响**：M0 CI 骨架的实现对象；`versioning.md` §5 产物命名/留存落地点；LICENSE 文件随 M0 首提交补齐（DEC-16 执行项，非裁决）。

### 已裁（留档）

#### Q-01 · APP 运行时选型（→ R1）

- **状态**：**已裁 → DEC-17**（2026-09-19：APP 运行时 = WASM，实现采用 WAMR）。
- **背景**：DEC-04 要求 APP 与板卡解耦、声明式权限、APP 间仅经框架消息通道隔离；DEC-09 裁定运行时待研究。现状：候选（WASM 解释器 / LLEXT 原生 ELF / 脚本类等）在维护度、沙箱强度、性能、架构覆盖（DEC-14 板集横跨 x86 仿真、Cortex-M、RISC-V、Xtensa）、west 接入成本上差异显著，尚未系统对比。该选型是 APP 打包格式、权限边界落点、Agent 产物形态的前置条件。
- **选项**：A. WASM 解释器（wasm3 / WAMR / wasmi 等）；B. LLEXT 原生 ELF；C. 脚本语言（MicroPython / Lua 等）；D. 混合或自研加载器。
- **建议**：（留档）未及正式呈报——owner 于初步笔记阶段直接裁定，见 DEC-17。
- **影响**：APP 分发与签名对象（DEC-05）；权限清单到沙箱边界的映射（安全合同第 10 条）；实时/性能预算划分；Agent 生成物格式与工具链（DEC-11/12）；目标板覆盖（DEC-14）。

### Q-02 · 数据面应用层协议选型（→ R2）

- **状态**：**已裁 → DEC-18**（2026-09-19：数据面协议 = zenoh，Zephyr 侧用 zenoh-pico）。
- **背景**：DEC-08 裁定重开（旧项目 Zenoh 结论不复用，事实可复用）；DEC-06 限定数据面只走以太网/WiFi；DEC-07 UART 退出数据面。协议须承载：设备发现、命名空间与编址、命令-回执语义、安全通道、断链判定（喂安全合同第 3 条 fail-safe）、多立方体逻辑节点（DEC-02）。现状：候选（MQTT / CoAP / WebSocket / 裸 TCP+序列化 / Zenoh-pico / DDS 等）未在"Zephyr in-tree 支持度 × 安全 × 确定性 × 逻辑节点承载 × 板覆盖"维度上系统对比。
- **选项**：A. MQTT(+TLS)；B. CoAP(+OSCORE/DTLS)；C. WebSocket(+TLS)；D. 裸 TCP/UDP + CBOR/Protobuf 自定义语义；E. Zenoh（zenoh-pico）；F. DDS；G. 组合（如发现层 + 数据层分离）。
- **建议**：（留档）未及正式呈报——owner 于初步笔记阶段直接裁定，见 DEC-18。
- **影响**：Agent 与模块间 API（DEC-12）；断链心跳与检测时限（安全合同第 3/5 条的参数来源）；多立方体编址（DEC-02 遗留题）；证书/密钥管理与分发；Zephyr 网络栈裁剪与内存占用。

## 三、修订记录

- 2026-09-19 · K1 录入：DEC-01…16（2026-09-18 owner 裁定）+ 待裁 Q-01/Q-02（依 `FOUNDING_PROMPT.md` §9-2）。
- 2026-09-19 · owner 裁定 Q-01/Q-02 → **DEC-17**（APP 运行时 = WASM / WAMR）、**DEC-18**（数据面协议 = zenoh / zenoh-pico）；R1/R2 初步笔记转为选型事实存档，其实测/核验类待补项与两项 DEC 的遗留设计题移交 design 阶段。
- 2026-09-19 · design 阶段呈递：HLD 固件框架 v0.1（`design/HLD-firmware-framework.md`）+ 待裁批次 **Q-03…Q-09**（Zephyr 版本 / zenoh 拓扑 / APP 包格式 / WAMR 模式 / 逻辑节点范围 / 断链参数 / 存储与 OTA）。
- 2026-09-20 · LLD 批次呈递：`design/LLD-00-common.md` + 七模块 LLD v0.1 + 待裁 **Q-10**（LLD 默认值清单 13 组）。
- 2026-09-20 · design review-01（17 项，`design/design-review-01.md`）+ 深化批次：HLD v0.2、LLD v0.2、新增 ts-store；Q-10 表增 #14/#15，新增待裁 **Q-11**（语义批次 6 项）。
- 2026-09-20 · 开发就绪度评估后登记 **Q-12**（CI 平台与远端托管，M0 前置）；待裁全景 = Q-03…Q-12 + HLD/LLD 确认 + 规范套件批准。
- 2026-09-20 · **裁决批次 1**：Q-03/04/05/08/09/12 → **DEC-19…24**（含 owner 补充语义：Zephyr 持续跟进最新、router 宿主扩至 ARM64 Linux 工业主板、断链参数因超长物理链路延长且 prov 可配）；Q-06/Q-07 补通俗解释后仍待裁；Q-10/Q-11 与 HLD/LLD/规范确认仍待裁。tag `dec-19-24`。
- 2026-09-21 · **裁决批次 2**：Q-06 → **DEC-25**（fast 解释器 + WASI 关 + AOT 保留）、Q-07 → **DEC-26**（逻辑节点仅预留）。tag `dec-25-26`。仍待裁：Q-10/Q-11 + C-1/C-2/C-3。
- 2026-09-21 · Q-10 #10 修订（owner 问询 PSRAM 触发）：WAMR 实例堆改**每板可配**（内部 SRAM 基线 64KB / PSRAM 池板 256KB），并确立**内存分层纪律**（框架安全数据必须内部 SRAM，仅 APP 沙箱内存可入 PSRAM）；事实核验见 R1 §5.6。
- 2026-09-21 · **裁决批次 3**：Q-10 → **DEC-27**（14 项按建议 + WAMR 堆每板动态配置）、Q-11⑥ → **DEC-29**（内存预算每板动态计算）、板卡策略 → **DEC-28**（面向高性能高配置，**RP2350 移出目标集**，DEC-14 修订）。tag `dec-27-29`。仍待裁：Q-11①-⑤ + C-1/C-2/C-3。
- 2026-09-21 · **裁决批次 4**：Q-11①-⑤ → **DEC-30**（按建议值）。**至此 Q-01…Q-12 全部裁毕（DEC-17…30）**；仅余 C-1 HLD / C-2 LLD / C-3 规范套件三项文档确认，确认后 M0 开工。tag `dec-30`。
- 2026-09-21 · 登记待裁 **Q-13**（APP 线程模型与并发限制——owner 问询"APP 能否建线程/单线程是否够/限制方式"触发；建议 A：编译期禁用 + 三层限制机制）。
- 2026-09-21 · **impl 阶段启动**：Q-13 → **DEC-31**；owner 指令"可以了，开始开发"一并确认 **C-1 HLD / C-2 LLD / C-3 规范套件批准生效（tag `std-v1`）**；M0 开工，开发环境 = `D:\Software\project\zephyrproject`。
- 2026-09-21 · **DEC-32**：Agent 仅支持 Linux（修订 DEC-20，Windows 宿主移出）；开发环境整体迁 **WSL2 Ubuntu 24.04**（仓库 `~/tessera`、工作区 `~/zephyrproject`），Windows zephyr 环境复原；记录于 `docs/dev-environment.md`。
- 2026-09-22 · **Agent 轨道启动**（owner 指令）：R3 基座选型调研落盘（`docs/research/R3-agent-foundation.md` v1.0，三路并行实查）；登记待裁 **Q-14**（Agent 基座选型，建议 A：pi 库内核 + 官方 MCP TS SDK 门面）/ **Q-15**（MCP 工具面形态，建议双层）/ **Q-16**（ACP 二级接口，建议 V1 不做）。
- 2026-09-22 · **裁决批次 5（Agent 轨道首批）**：Q-14 → **DEC-33**（pi 基座 + 多域 Agent 预留 + 北极星"应用于机器人/Galatea 时完全自动化自己生产自己"）、Q-15 → **DEC-34**（双层 MCP 工具面 + 长任务 Tasks 句柄化）；Q-16 按 owner 要求补呈详解（作用 + 实现方式）后**仍待裁**。tag `dec-33-34`。
- 2026-09-22 · **R4 交互与接入方式调研**（owner 质疑 MCP 选型触发，`docs/research/R4-agent-interaction.md` v1.0）：MCP 确认为前沿正确选择（协议格局已收敛为 AAIF open agentic stack）；登记待裁 **Q-17**（交互栈确认 4 子项：MCP 维持+实现纪律 / 长任务机制细化 / Skills 分发 / A2A 预留）；**Q-16 重呈**（R4 证据补强）。
- 2026-09-22 · **裁决批次 6（Agent 轨道交互栈）**：Q-16 → **DEC-35**（ACP：V1 不做仅预留）、Q-17 → **DEC-36**（交互栈 4 子项全采纳 + A2A 预留显式登记，owner 特别要求）。tag `dec-35-36`。**Agent 轨道待裁 Q 清零**——research 阶段落定，下一交付单元 = Agent design（HLD）。
- 2026-09-22 · 登记待裁 **Q-18**（Agent 实现语言：TS 维持 / Python 宿主+pi RPC / 全自研，owner 问询"可否改为 python 或 rust"触发；建议 A 维持，B 为可接受变体）。
- 2026-09-22 · **Q-18 建议修订**（owner 澄清动因"完全不熟 Node"）：改推 **C（PydanticAI + FastMCP 全 Python）**，B 细化为 B1 备选（pi 子进程经 MCP 回接）；补核验 PydanticAI 事实（Ollama 本地支持、原生 Temporal 持久执行）；Python 版图应答入 Q-18 条目。
- 2026-09-22 · **裁决批次 7**：Q-18 → **DEC-37**（全 Python：PydanticAI + FastMCP + 自建编码工具集；修订 DEC-33 基座条款，北极星与落地约束沿用）。同批启动：**Q-18 涟漪审查**（design 全量 review，结论留档 `design/design-review-02-agent-python-ripple.md`）+ **R5 补充核验**（PydanticAI/FastMCP HLD 级事实、TSAP Python 签名栈、zenoh-python）。tag `dec-37`。
