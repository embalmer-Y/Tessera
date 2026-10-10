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
| DEC-38 | 2026-09-22 | **Q-19 裁定：13 项中 11 项按建议值（#1-5、#7-8、#10-13，见 Q-19 表）；#6/#9 修订**——**#6 会话上下文**：① 上下文压缩 **V1 即支持**（非后置）；② 上下文预算**随模型配置动态调整**（取模型 context window，不再固定 100k）；③ 默认压缩阈值 **70%**（达窗口 70% 触发：保留系统提示/skills 注入/近期轮次 + 远段摘要，压缩后仍超限才任务失败）；④ **最低要求值：模型 context window ≥ 32k tokens**（低于 = 配置错误，拒绝启动——系统提示+skills+工具 schema+最小工作集约需 20k）。**#9 输出截断**：截断限额**随动态上下文预算缩放**（单次工具返回上限 = 预算×5% 折算字节 ≈4 字符/token），**最低要求值：单次 ≥16 KiB、单行 ≥2 KiB**（单行 = max(2 KiB, 单次/16)） | owner 原文："我下面只列出不接受建议值的裁定项：6. 会话压缩需要在V1即被支持，同时预算上下文需要动态根据模型配置动态调整。默认压缩阈值70%，上下文预算需要设置最低要求值。9输出截断也需要按照动态上下文配置动态调整，但需要设置最低要求值。" 落地数值（32k / 5% / 16KiB / 2KiB）为 owner 授权 design 定的具体数（"需要设置最低要求值"），登记于本 DEC 作代码常量出处，偏差按 Q-19 惯例按行修订；设计文档同步：HLD §9 裁剪清单、LLD-A00 §5、LLD-A01 §4、LLD-A02 §2/§6 |
| DEC-39 | 2026-09-22 | **C-4/C-5 确认（Agent design 阶段退出）**：HLD-agent v0.1.1 与 LLD-A00…A07 批次（v0.1/v0.1.1）确认生效——含 C-5 内的 MCP 工具面清单（DEC-34 review 门首次定型）；**统一项目开发计划授权 + 开发启动**：固件 M 系与 Agent MA 系双轨统一规划（`docs/project-plan.md` 建立），MA0 即时开工 | owner 原文："HLD和LLD均已确认，请你开始重新规划项目开发计划包括之前的部分也纳入计划范围整个项目统一规划并着手开发。" 双轨并行不违背 DEC-15 阶段顺序（阶段一/二的内容顺序不变，执行节奏并行化，交叉依赖见计划 §4） |

## 二、问题登记（Q）

### 问题批次（参考项目借鉴 design 优化，2026-09-23 呈递并同日裁定 → DEC-40/41/42；owner 提供 NeuroLink/MatrixMechanic 前作并指令"优化现有 design"，设计修订落 `design/LLD-ts-net.md` v0.3 / `LLD-A06` v0.2）

#### Q-20 · 命令信封 v2（rid/幂等键/带内超时/调用方身份）

- **状态**：**已裁 → DEC-40**（2026-09-23 owner 条件指令：先调研 zenoh 可靠性——调研实查结论 = zenoh 无端到端恰好一次执行保证（TCP 仅传输层可靠；query 无重试无去重；reliability 旋钮 unstable 门控），按建议方案 A 采纳 + 两项调研衍生约束：命令面链路必须 TCP/TLS、固件拒绝 to>5000ms）。
- **背景**：现行 sys 命令请求仅 `{op, args}`（M3a.2 已实现，v1）——① 网络超时后调用方重发会**二次执行**（重试不安全）；② 回执无调用方关联（审计归因缺身份）；③ LLD 早已要求"命令超时上界 < 断链判定上界"〔DEC-22〕但无机制承载。NeuroLink（owner 前作）的请求信封（request_id/idempotency_key/timeout_ms/source）实证了同一问题的解法。
- **选项**：A. 完整容封 v2（详见 LLD-ts-net §4.2：`{ver,kind,rid,src,op,args{idem?,to?}}`；固件侧 4 项幂等回执缓存 LRU；v1/v2 按首键判别共存，v1 进弃用期）；B. 最小改（仅加 rid/to，不做幂等缓存——重试仍不安全）；C. 维持 v1。
- **建议**：**A**（已采纳）。幂等性是 deploy 类长链路（MA3 分块推送 + 重试）的正确性前提；缓存 4 项定容，内存代价可忽略。
- **影响**：cmd.c 请求解析扩展 + 幂等缓存；Agent `keys.py` 镜像信封构造；estop-clear 令牌语义不变；命令面 locator 形态校验（tcp//tls/ 前缀）。

**DEC-40 调研留档**（zenoh-pico 1.10.1 钉版实查）：① 传输层可靠性取决于链路——TCP/TLS 可靠有序，UDP unicast 尽力而为且 zenoh 无重传（全库无 retransmission 实现）；② QoS 旋钮非投递保证——congestion_control（DROP/BLOCK）为本端队列策略、priority 为排序、publisher/subscriber 的 reliability 字段 `#ifdef Z_FEATURE_UNSTABLE_API` 门控且文档自注 unstable（未启用）；③ query 仅客户端超时（默认 10000ms）无重试无去重——**关键失效模式**：命令已执行、回执因会话中断/延迟未达 → 调用方超时重发 → 应用层二次执行（端到端论证/两将军问题——恰好一次必须由应用层幂等承载）。

#### Q-21 · 控制租约（多方并发命令的准入仲裁）

- **状态**：**已裁 → DEC-41**（2026-09-23 owner："Q-21:采纳建议方案"——方案 A 采纳：V1 单租约 + TTL 10s + 续期幂等 + estop-clear/只读豁免 + 不联动安全态；写命令准入挂钩随 M2b.2；Kconfig `TS_NET_LEASE_TTL_MS=10000`）。
- **背景**：当前任何 host 侧命令直接执行，无控制权仲裁——多方（多个 Agent/工具/人工面板）并发操作同一 cube 时输出指令可交错。NeuroLink 的 lease_manager（resource+TTL 过期+优先级抢占）实证了该面的形态；TTL 过期天然处理控制方崩溃失权。
- **选项**：A. V1 单租约（`sys/lease-acquire/release/get`；TTL 默认 10s〔≈断链窗口 6s×1.5+余量〕；续期 = re-acquire 幂等；**写类命令须持租约**（挂钩随 M2b.2 写命令面），只读与 estop-clear 豁免——合同 5 优先；**不联动安全态**——安全态唯一判定源仍是 linkmon/estop，单源纪律）；B. NeuroLink 全形态（多资源粒度 + 优先级抢占）；C. 不做（多方并发靠 Agent 侧自律）。
- **建议**：**A**。单 cube 单控制方的现实负载不需要资源粒度与抢占；B 的复杂度留 V2 按需。
- **影响**：ts-net 新增 lease.c + sys 命令族三项；MA3 deploy_push_* 全程 acquire/续期/release；Kconfig `TS_NET_LEASE_TTL_MS`。

#### Q-22 · 事件/遥测版本化信封（固件→host 前向兼容）

- **状态**：**已裁 → DEC-42**（2026-09-23 owner："Q-22：采纳建议方案"——方案 A 采纳：`{"ver":1,"kind":…}` 信封 + kind 注册表唯一权威（LLD-ts-net §4.4）+ 消费端未知 kind 透传不解析；与 DEC-40 信封 v2 同批切换〔MA3 前〕）。
- **背景**：固件→host 方向的遥测/事件 payload 迟早演进（加字段/加事件类型）。MatrixMechanic（owner 前作）的 TLV"未知块跳过"与 NeuroLink 的 `{schema_version, message_kind}` 信封是两种解法；Tessera 确定性纪律下跳过未知键弱化机械验证，版本化信封的边界显式且可断言（LLD-ts-net §0 演进原则）。
- **选项**：A. 信封 v1（事件 `{"ver":1,"kind":32+evt_id,"t_ms","wall_ms",…}`、遥测 `{"ver":1,"kind":96,…}`；消费端未知 kind 透传存储不解析；kind 分级注册表 = LLD-ts-net §4.4 唯一权威，Agent keys.py 镜像）；B. 裸 TLV 跳过未知键（MatrixMechanic 原形态）；C. 维持裸 payload 演进靠 fw semver 整体升版。
- **建议**：**A**。命令面 fail-closed 不变 + 观测面前向兼容的"方向不对称"是本批收敛的核心原则；B 与确定性验证相斥。
- **影响**：pub.c payload 加信封（破坏性——消费端同步升版，随 Q-20 同批切换即可，两者都在 MA3 前落地）；kind 注册表进 names.md。

### 问题批次（Agent 轨道呈递，2026-09-22；**Q-14…Q-19 均已裁 → DEC-33…38；C-4/C-5 已确认 → DEC-39——待裁清零，impl 阶段（MA0 起）**）

#### Q-19 · Agent design 批次默认值与配置清单（2026-09-22 随 HLD/LLD 批次呈递）

- **状态**：**已裁 → DEC-38**（2026-09-22：11 项按建议；#6/#9 owner 修订——压缩 V1 即支持/动态预算/阈值 70%/最低 32k；截断动态化/最低 16KiB+2KiB）。
- **背景**：Agent 设计批次（`design/HLD-agent.md` v0.1 + `design/LLD-A00…A07` v0.1，共 9 份，DEC-33…37 的设计展开 + R3/R4/R5 事实落点）为可实施规格，需落一批工程默认值（依赖钉版/超时/限额/策略/工具链）；依军规 2"无 Q 不落盘"集中登记，设计文档内全部以〔Q-19 提案 n〕标注，裁决前不进代码常量。
- **选项**：A. 本清单批量裁决（逐项可例外，同 Q-10 先例）；B. 每项独立 Q（决策成本高）。
- **建议**：A。批准后即成为 agent/ 代码常量出处（`# 来源: Q-19`），实测偏差按行修订本表不另开 Q（除非语义变化）。

| # | 常量 | 提案值 | 推导 / 越界后果 |
|---|---|---|---|
| 1 | Python 依赖钉版 | `pydantic-ai-slim[openai,anthropic,google,mcp]` 2.x 钉 minor；`fastmcp` 4.x；`cbor2==6.1.4`；`pycose==1.1.0`；`cryptography>=42`；`eclipse-zenoh==1.10.1`（**三方同 minor**，DR-22）；`pytest-json-report` | R5 §6 定案 + DR-21/22 纪律；浮动 = 供应链与行为漂移 |
| 2 | MCP 传输 V1 | **stdio only**（Streamable HTTP 为配置位预留不启用） | DEC-36① 最保守路径；远端启用另立 Q |
| 3 | 结构化输出重试预算 | output retries = 3 | ModelRetry 默认 1 偏紧；过大会放大 token 成本 |
| 4 | 超时族 | 长任务 TTL 30 min；审批等待 10 min；deploy_discover 10 s；子进程默认 120 s；fw_build/fw_twister 30 min | CI 构建经验 + Claude Code 2 min 后台化/Codex 600 s 客户端现实；过短误杀、过长占位 |
| 5 | 任务日志环形缓冲 | 1000 行/任务 | 排障够用 + 内存有界；溢出标记截断 |
| 6 | 会话并发 / 上下文预算 | 并发 2；预算**动态**（取模型 context window，窗口 ≥32k 为最低要求，低于拒绝启动）；**压缩 V1 支持**：达窗口 70% 触发（保留系统提示/skills/近期轮次+远段摘要），压缩后仍超才失败 | **DEC-38 修订**（owner：压缩 V1 即支持 + 动态预算 + 阈值 70% + 最低要求值） |
| 7 | 审批 token 与 confirm 策略 | token 经宿主环境变量注入；confirm 类 V1 会话内直行（config 可收紧为挂起，**不可放宽 strict**） | 防 MCP 客户端代批；收紧自由度保留给部署方 |
| 8 | 审计保留 | V1 全量落盘不滚动 | 审计必成（无豁免链）；磁盘代价接受（单机开发场景） |
| 9 | 输出截断 | **动态**：单次工具返回上限 = 上下文预算 ×5% 折算字节（≈4 字符/token）；**最低要求值：单次 ≥16 KiB、单行 ≥2 KiB**（单行 = max(2 KiB, 单次/16)） | **DEC-38 修订**（owner：随动态上下文调整 + 最低要求值）；截断必标记 |
| 10 | 限流 | 30 工具调用/min/客户端 | 防失控循环（doom-loop 类）兜底 |
| 11 | lint 工具链 | ruff（含 asyncio 阻塞调用检查规则） | Python 生态事实标准；军规 10"lint 通过才算完成"落点 |
| 12 | sim_run 确定性 | 内建双跑比对，determinism 字段必出 | 合同 9 同构的最直接机械验证 |
| 13 | skill 同步检查 | 权威文档变更后 PR 检查脚本（skill 与源文档一致性） | 防 skill 双写真相漂移 |

- **影响**：MA0 起全部 agent/ 代码常量与 CI 配置出处；与 DEC-36/37 的纪律联动（钉版/截断/审批）。

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
- 2026-09-22 · **Agent design 批次交付**（owner 指令"开始进行HLD以及LLD"）：`design/HLD-agent.md` v0.1 + `LLD-A00…A07` v0.1（9 份）；登记待裁 **Q-19**（默认值清单 13 项）+ 呈递 **C-4**（HLD 确认）/ **C-5**（LLD 批次确认）。
- 2026-09-22 · **裁决批次 8**：Q-19 → **DEC-38**（11 项按建议；#6 上下文压缩 V1 即支持+动态预算+阈值 70%+最低 32k；#9 截断动态化+最低 16KiB/2KiB）；设计文档同步（HLD §9 / LLD-A00 §5 / LLD-A01 §4 / LLD-A02 §2/§6）。tag `dec-38`。**C-4/C-5 仍待 owner 确认**。
- 2026-09-22 · **裁决批次 9 / Agent design 阶段退出**：C-4/C-5 确认 → **DEC-39**；统一项目计划建立（`docs/project-plan.md`，固件 M 系 + Agent MA 系双轨）；**MA0 开工**。tag `dec-39`。
- 2026-09-23 · **参考项目借鉴批次**（owner 提供 NeuroLink/MatrixMechanic 前作，指令"结合参考项目优化现有 design"）：设计修订落盘 LLD-ts-net v0.3（演进原则/传输健康 zp 任务自省〔已定稿项〕/kind 注册表）+ LLD-A06 v0.2（deploy 分块传输 2-4KB + upload/verify/activate 分步安装 + 断点续传定稿方向）；登记待裁 **Q-20**（命令信封 v2：rid/幂等/带内超时/身份，建议 A）/ **Q-21**（控制租约：单租约+TTL+不联动安全态，建议 A）/ **Q-22**（事件遥测版本化信封：ver+kind 前向兼容，建议 A）。
- 2026-09-23 · **裁决批次 10（参考项目借鉴批次）**：Q-20 → **DEC-40**（owner 条件指令触发 zenoh 可靠性实查——结论无端到端恰好一次保证〔TCP 仅传输层/query 无重试无去重/reliability 旋钮 unstable〕→ 方案 A 采纳 + 命令面链路 TCP/TLS 约束 + 固件拒绝 to>5000ms）；Q-21 → **DEC-41**（方案 A：V1 单租约+TTL 10s+estop/只读豁免+不联动安全态）；Q-22 → **DEC-42**（方案 A：ver+kind 信封+注册表，与 DEC-40 同批切换）。设计同步 LLD-ts-net v0.3.1 / LLD-A06 v0.2.1。实现批次 = MA3 开工前。
- 2026-09-25 · **MA3.1 交付**（owner 指令"按照计划进行开发"）：固件部署命令面 sys/app-{begin,chunk,verify,activate}（写类 gated = v2+租约，DEC-41 首个落点）+ ts_appmgr_stage_* 分步链 + Agent deploy_{discover,status,push_app}（ZenohService 线程桥/keys 镜像/分块 idem 重试/租约闭环/tsap_verify 强制复验）；twister 8/8（37 用例）+ Agent pytest 44 + E2E（spec→TSAP→部署仿真立方体）全绿。实现细节修订：部署传输方向定稿为上传语义（请求携 data bstr）；get-info 增 node/cube 自报（通配发现身份以载荷为准——zenoh-pico 无 keyexpr 改写）；详见 LLD-A06 v0.2.2。
- 2026-09-25 · **MA3.2 交付（MA3 里程碑退出）**：A07 全量落地——skills 4 项 + loader 渐进披露 + SOURCES.lock 同步守卫（Q-19 #13/DEC-38 #13）；平台/域拆分（platform/compose/domain + 导入图测试，DEC-33 多域预留）；高层链 app_develop（PydanticAI 结构化产物 + skills 注入 + tsap 打包复验；wasm 边界 = M2b.2）/app_deploy（复验→发现→分块部署→确认）；A2A/ACP 接缝（core/peer.py）。Agent pytest 58 用例 + ruff 全绿。push_prov 例外随维护模式语义后批（LLD-A06 §6 登记）。
- 2026-09-25 · **M3b 交付（固件轨 M0…M3b 全绿）**：ts-power（供电槽/prov 只读预算/超预算事件/get-budget 实装/kind 97 遥测）+ ts-periph（描述符职责链/插拔→单通道 SAFE_FAULT——机制面 = safety 单通道 fault/recover 新 API）+ replay 集成场景（预算+插拔写轨迹/事件 golden）；twister 10/10（44 用例）/L5 6/6/pytest/zenoh overlay 构建全绿。实现批修复：power 通道描述符静态存储（栈上组装 = 悬垂）；net test_07 计入预算遥测记录。余项 = M2b.2（WAMR，需网络）与板级移植（前置 Zephyr SDK）。
- 2026-09-23 · **DEC-40/41/42 实现批次落地**（owner 指令"按计划继续开发"）：cmd.c 信封 v2（首键判别/rid 回带/4 项 idem LRU 回放不重执行/to>5000 拒绝/idem-op 一致性防御）+ lease.c（单租约/惰性过期/lease_id 单调/sys 三命令）+ pub.c 事件遥测 ver+kind 信封（遥测键 kind→dev 改名随批）+ ts_net_qos_t 穿透（安全事件 BLOCK+REAL_TIME）+ zenoh.c is_up 任务自省与 locator TCP/TLS 校验（缺省 locator udp→tcp 收敛）；twister 8/8（35 用例）/L5 6/6/pytest/L3 五验证点全绿（LLD-ts-net v0.3.2 §8）。
- 2026-09-25 · **impl-review-01 修复批交付**（owner 指令"严格按照大型项目标准规范修复这些问题"）：评审发现 F-1…F-8 全处置——F-1 periph/预算事件 net 外发兑现（pub.c 订阅七类 + extra 扁平对；**pubq PAYLOAD_MAX 64→128B**〔派生定容：预算事件 3 对 extra 最坏 ~96B，内存 +512B 静态，计入 DEC-29 板级 RAM 复核〕；LLD-ts-periph §3 承诺闭环）+ F-2 ts_periph_register 注册源静态表化（safety 持指针——与 slots.c M3b 修复同型；头文件生命周期契约）+ F-3 gated 按 suffix 回查回填 + sys_init 错误上抛（boot fail-safe）+ F-4 idem 回放判定后移至 key/op 匹配后（跨 key 同 idem 拒绝）+ F-8 clear_fault 复位语义定案（状态条件恢复 + 值不回写，v0.2.2 ③ 复核闭环）；F-5 注册链无回滚登记 LLD 已知限制；F-7 并发防护复核写入 project-plan M2b.2 开工前置；F-6 里程碑 tag 同批补打。文档：LLD-ts-net v0.3.5 / LLD-ts-periph v0.4 / LLD-ts-safety v0.2.3 / project-plan v1.6。回归：twister 10/10（46 用例：+net test_11 +periph test_04）/L5 6/6/pytest/ruff/skills 全绿。
- 2026-09-25 · **远端上线（DEC-24 落地）= M0 完整退出**：owner 提供 git@github.com:embalmer-Y/Tessera.git；origin 更换（旧 origin = M0 迁移期指向 Windows 快照的本地路径）；合并建仓初始提交（LICENSE 附录占位符风格差异保留本地 {yyyy} 版）；main + 23 tag 推送完成。CI（.github/workflows/ci.yml）四 job 全绿：repo-checks / l5-checks / agent-checks / native-build（runner 上 west v4.4.0 + twister 全量 10 套件 + ZEPHYR_TOOLCHAIN_VARIANT=host）。CI 修复链（三轮）：apt 主机构建依赖清单 → 真因 = 工具链变体未设探测 SDK（本地被 Windows SDK /mnt 互通掩盖）→ 显式 host 变体；调试通路 = 失败注解注入（公开 API 可读，常设）。仓库可见性 = public（如需 private 由 owner 在设置中调整，CI 无影响）。教训登记 dev-environment.md §5-7/8/9（v1.5）。

---

#### Q-23 · WAMR 宿主线程模型与并发收口（F-7 落点；M2b.2a 开工前置检查项）

- **背景**：impl-review-01 F-7 登记：ts_safety_commit 持锁（+ 末段 irq_lock 复查 forced），但 ts_safety_set_link / ts_safety_force_channel_fault / ts_safety_channel_recover、ts_power_request 预算检查→提交、pubq/事件发布面均按"单 net 线程 + 测试直调"假设无锁——当前接线安全。M2b.2 接入 WAMR 后，APP 代码若在与 net 分离的执行上下文运行，上述假设失效（迁移路径竞态改写 shadow/state、预算 TOCTOU 瞬时超限、pubq 环竞态）。LLD-ts-appmgr 既有定义"**每 APP 一个框架线程**"；DEC-31 已裁 APP **内**禁自建线程（wasm 侧 pthread/共享内存编译期不启用，本批已按此配置）；**宿主侧**线程模型未裁。
- **选项**：
  - **A（建议）**：每 APP 一个宿主框架线程（V1 单 APP = 单执行线程，低于 net 优先级、可抢占）+ 配套锁收口——commit_lock 扩展覆盖 set_link / force_channel_fault / channel_recover；预算检查纳入 commit_lock 内；pubq/事件总线加轻量互斥。estop ISR 路径（force_all_fault）保持无锁直达设计**不变**（合同 5）。
  - **B**：APP 执行串行化到 sysworkq（零锁改动）——长 APP 饿死 net_tick → 心跳缺失 → 误断链（方向 fail-safe 但功能不可用）；与 LLD"每 APP 一个框架线程"定义冲突。
  - **C**：V1 先 B、V2 迁 A——避免不了 A 的锁收口工作，反增语义切换与返工。
- **建议**：**A**。与 LLD/DEC-31 语义连续；锁收口范围小且可测（现有 47 用例回归 + 新增并发压力用例于 native_sim 实抢占环境）；规避 sysworkq 饿死。合同 9 不受影响（L4 重放本就单线程虚拟时钟）。
- **影响**：M2b.2a 接线批（appmgr → WAMR 调用线程 + natives 挂接）按裁定实现；本环境批（WAMR 2.4.5 接入/framework.wamr 冒烟）不依赖本项，已先行交付。

---

- 2026-09-26 · **M2b.2a 环境批交付（owner 指令"按照计划执行：M2b.2a"）**：WAMR **2.4.5 tag 钉版**接入（浅克隆 ~/project/deps/wamr，经 TS_WAMR_DIR 注入——仓库不含三方源码，zenoh-pico 同纪律）+ 模块构建配置按既有裁决落位（DEC-25 fast 解释器 + WASI 全关 + AOT/JIT 不启用；DEC-31 线程/共享内存编译期关；DEC-27 #10 池模式，native_sim 堆 64KB = HLD §4.6）+ 样例 APP（clang wasm32 自由固件 103B，health_ping/on_input）+ **framework.wamr 冒烟**（装载/零导入实例化 = WASI 关边界活体证明/调用/重放一致）。零上游补丁四要点留痕 dev-env v1.6 §3（include 传播/独立库 -w〔GB 撞名〕/通用 invokeNative〔.note.GNU-stack〕/stdout 钩子垫片）。CONFIG_TS_APP_WAMR 默认 n——接线批随 **Q-23** 裁定后落（appmgr 执行线程 + ts_* natives 挂接 + 租约挂钩）。回归：twister **11/11（47 用例）**/L5 6/6/pytest×2/ruff/skills 全绿；CI native-build 增 WAMR 检出步骤。

#### Q-23 实验补充（2026-09-26 · framework.wamrdemo 实证批，owner 指令"先做 demo 实验用真实运行数据确认"）

**实验环境**：native_sim（真实 pthread 抢占 + SMP 4 核真并行〔需显式 USE_SWITCH，否则 Kconfig 静默失效〕+ 真实时间对齐〔SLOWDOWN_TO_REAL_TIME，twister/TEST 下默认关〕）；负载 = busy.wasm（确定性算术循环，实测 ~1.1ns/迭代）。套件：framework.wamrdemo（4 用例全绿）。

**实测数据**：

| 实验 | 结果 | 判读 |
|---|---|---|
| ① 调用时延画像 | busy(1e3)≈1.4-4µs；busy(1e5)≈0.1-0.3ms；busy(1e6)≈1.1-1.9ms；busy(1e8)≈106-126ms（线性） | 事件处理器量级 = 微秒级；无界循环 = 百毫秒级且随规模线性放大——执行上下文必须与周期任务隔离 |
| ② B 方案（sysworkq 同队）饿死 | 周期任务（10ms 节拍）基线 max 迟到 ≈1.0-1.3ms；同队一次 busy(1e8) 后 = **101.9-113.6ms**（两轮复现，断言过） | **APP 执行时长全量转嫁为周期任务延迟**；真实 MCU 协作 sysworkq 语义下更糟（完全阻塞抢占线程）——B 方案实证不可行 |
| ③ 预算 TOCTOU 窗口 | 单请求全路径均值 = **203ns**（检查→提交窗口上界）；信号量栅栏同步起跑 4000 轮（4 核）实测超限 0 次 | 窗口客观存在但极窄；native_sim 唤醒串行化掩盖碰撞。**修订认知：锁收口紧迫性低于纸面预估**——但 ESP32-S3/P4 为真双核 SMP 板，长运行×海量请求下期望碰撞非零，收口仍必要（属廉价保险而非高危前置） |
| ④ A 方案（专用线程）通路 | 独立实例 10 轮完整执行 ✓；周期任务未停摆 ✓；迟到数值 = native_sim 伪影（忙循环冻结模拟时钟，真实 MCU 上 ISR 抢占忙线程） | A 形态执行通路可用；其并发优越性在 native_sim 上**不可忠实演示**（时间模型限制，如实标注），板级验证补 |

**修订后的建议（数据版）**：维持 **A**（每 APP 一个宿主框架线程 + 锁收口），但实施定位由"高危前置"改为"接线批顺带"——②证明 B 不可行是硬结论；③证明锁收口对象（203ns 窗口）成本低、可在接线批一并落（commit_lock 扩展 + 预算入锁 + pubq 互斥）并配并发压力回归用例；④的最终并发行为确认留板级里程碑（S3 双核实测）。

**过程教训（dev-env §5-10/11 登记）**：native_sim SMP 需 USE_SWITCH 显式开启（静默失效）；忙循环冻结模拟时钟——宿主墙钟（显式声明 clock_gettime）是唯一可信测量时基。

- 2026-09-26 · **裁决：Q-23 → DEC-43（方案 A + 实验数据版定位）**：owner 原文："同意维持方案A，我们采用xiao_esp32s3这块板卡进行真机测试我已经接入这块开发板，如果你需要可以直接使用"。裁定内容：① WAMR 宿主线程模型 = **每 APP 一个框架线程**（V1 单 APP 单执行线程，低于 net 优先级）；② 锁收口 = commit_lock 扩展覆盖 set_link/force_channel_fault/channel_recover/clear_fault + 供电预算检查入锁 + pubq 互斥，**随接线批一并落地**（实验证明窗口 203ns 窄、非高危前置）；estop ISR 路径保持无锁直达（合同 5 不变）；③ 并发压力回归入常设套件；④ A 方案最终并发行为确认 = **xiao_esp32s3 真机双核终验**（板卡已接入——板级里程碑启动）。同批：接线批第二单元（appmgr 执行线程 + ts_* natives + 写路径租约挂钩）随后续会话交付。

- 2026-09-26 · **DEC-43 实现批交付（锁收口 + 并发回归，owner 裁定后落地）**：① commit.c 重构（commit_impl + write_lock/commit_locked 受控暴露）；② 迁移路径纳入互斥——set_link / force_channel_fault / channel_recover（持锁双检 forced）/ clear_fault；③ ts_power_request 检查-提交原子化（全程 write_lock + commit_locked，TOCTOU 窗口 203ns 消除）；④ pubq 互斥（flush 锁内出队 + 锁外发送，防传输阻塞反压）；estop ISR 路径保持无锁直达（合同 5 不变）；锁序 write_lock → pubq 单向无环。**framework.conc 新套件**（SMP+USE_SWITCH）：test_01 对齐双冲 3000 轮超限 0+0（锁后硬保证——真 SMP 板判别力）、test_02 迁移×提交×恢复压力不变量（终态 ACTIVE/表完整/10000 提交计数闭合）、test_03 pubq 并发完整性（序号严格递增 + delivered+dropped==pushed 会计闭合）。回归：twister **13/13（54 用例）**/L5 6/6/pytest×2/ruff/skills 全绿；LLD-ts-safety v0.2.4 / ts-power v0.2.1 / ts-net v0.3.6 同步。板级前置就绪：espressif 工具链已装（~/opt 内），xiao_esp32s3 定为真机测试板（DEC-43④；WSL2 下 USB 串口不可见——烧录策略随板级会话裁定：usbipd-win 或 Windows 侧 esptool）。**下一单元 = 接线批第二单元**（appmgr 执行线程 + ts_* natives + 写路径租约挂钩）。

- 2026-09-26 · **接线批第二单元交付（APP 运行时宿主 + natives，M2b.2a 核心）——twister 14/14（57 用例）全绿**：runtime.c（每 APP 一框架线程〔DEC-43 A，V1 单活跃〕；mailbox DR-14 深度 8 满丢最旧+计数；停止 = 停投递→join 2s〔DEC-27 #15〕→强杀回收；健康探针连续〔DEC-27：3〕败自停→health_fail 回滚入口）+ natives.c（ts_api_v1 V1 子集：gpio_write/gpio_read/pwm_set/adc_read/time_ms/log_write；**ctx 由 exec_env user_data 注入防伪造**，wasm 传参仅占位）+ framework.app 套件 3 用例（生命周期端到端/调用期权限拒绝 + TS_EVT_PERM_DENIED 留痕〔合同 10〕/健康失败自停）+ 夹具 wasm（clang wasm32，--allow-undefined 导入）。**两项 V1 已知偏差登记 LLD-ts-appmgr v0.3 §7**：① WAMR natives 全局注册→调用期裁决（结构化装配留待 WAMR per-instance 支持）；② WAMR 平台模块生命周期怪癖（unload→reload / init→destroy→init 双复现失败）→ mod_cache 进程级复用规避（dev-env §5-12）。租约挂钩语义澄清：DEC-41 准入属 **net 命令面**（部署面已落），ts_api_v1 natives 按权威 LLD-ts-hal §3 = 权限裁决（无租约）。板卡通道打通：usbipd 附加 xiao_esp32s3 → /dev/ttyACM0（dev-env §5-13）。余项（M2b.2 收尾单元）：boot 步骤 8 slot 装载接线 + CONFIG_TS_APP_WAMR 默认翻转 + Agent E2E wasm 化。

- 2026-09-26 · **M2b.2 收尾单元交付（boot 装载 + 默认翻转 + E2E wasm 化）——twister 14/14（58 用例）全绿，M2b.2 全部完成**：① ts_appmgr_boot_start（slot.c）：active slot TSAP 容器 → manifest 走查（TsapManifest v1 canonical CBOR；未知键 fail-closed；caps 组合 ';' 串、app_id/app_ver 提取；stack_kb/heap_kb V1 消耗运行时常量〔已知限制登记 LLD〕）→ wasm 字节（CONFIG_TS_APP_LOAD_MAX=16K 结构性上限）→ app_start；装载成功置 STAGED→ACTIVE；② boot 步骤 8（app_load，尾部追加；core.h 计数条件化 4/5/5/6；**APP 故障不阻塞启动** = 合同 6 显式例外，HLD §4.4-8）；③ CONFIG_TS_APP_WAMR 默认翻 y（含 TS_APP_LOAD_MAX）；④ framework.app test_04（容器构造→分步安装→meta 切换→boot 装载→APP 写 gpio→app_id 断言）；⑤ Agent E2E wasm 化（真夹具 native_app.wasm 入 TSAP 包——E2E 与固件运行时同一工件）；⑥ mod_cache 复用改为内容比较（boot 缓冲与测试夹具两份拷贝场景）。过程修复（如实）：caps 分段循环末段越界（编译器 UB 检测 + 测试拦截）、manifest 键分支下标笔误、core 步骤守卫测试随新步骤更新。板级效率 DoD 六项固化 project-plan v1.10（owner 指令"真板检查多看架构运行效率"：解释器吞吐/native 陷出/写路径时延/邮箱时延/足迹对拍/双核终验）。


#### Q-24 · 真机双核终验载体（DEC-43④ 落点；板级二实证）

**背景**：DEC-43④ 约定 A 方案（每 APP 一框架线程）的最终并发行为确认 = xiao_esp32s3 真机双核终验。板级二单元（2026-09-26）构建实证：**Zephyr v4.4.0 的 ESP32-S3 无 SMP 支持**——kernel SMP 钩子 `arch_cpu_start` 无 esp32s3 实现（`CONFIG_SMP=y` 链接失败；v4.4.0 树内仅 esp32 经典款 soc/espressif/esp32/esp32-mp.c 实现）。espressif 在 Zephyr 的双核路径 = **AMP**（`SOC_ENABLE_APPCPU`：procpu/appcpu 各跑独立镜像经 IPM 通信），与 framework.conc 单调度器语义（DEC-43 线程模型）不符。效率 DoD 六项中 ①-⑤ 已在真机完成（docs/board-bench-01.md），⑥ 已降级为单核抢占并发实测（锁竞争 p95 无影响、尾部 +12µs、estop 并发中生效）。

**选项**：
- **A（建议）**：V1 双核终验以 **native_sim 多核**为准（framework.conc 已在 SMP=4 核真并行下常设运行，Q-23 批具备）；真机双核终验挂起，经 DEC-19 机制跟进 Zephyr ESP32-S3 SMP 落地后补做。
- B：购入 ESP32 经典款板（如 DevKitC/WROOM，v4.4.0 已支持 SMP）作双核终验载体——需 owner 采购，且 ESP32 经典款非 DEC-28 目标板（性能弱于 S3）。
- C：ESP32-S3 AMP 路径（appcpu 独立镜像 + IPM）——架构语义与单调度器并发模型不符，framework.conc 不适用，仅在未来需要"双立方体/异构核"形态时才有意义。

**建议**：A。零采购、零架构妥协；SMP 缺口属上游事实，跟进即可（与 RP2350 移出〔DEC-28〕同类处置）。

**影响**：⑥ 的真机双核数据延后（不阻塞 V1 任何里程碑——六项中五项已真机实测）；若 owner 选 B 需提供板卡。

---

- 2026-09-26 · **板级二单元交付（效率 DoD 真机实测 + WAMR xtensa 可用性修复）——twister 14/14（58 用例）/L5 6/6/pytest×2 全绿**：boardbench 基准应用（wasm 夹具 669B + 宿主 CCOUNT 计时 + 影子翻转检测）六项数据（docs/board-bench-01.md）：① 解释器吞吐 1043ns/iter（vs native_sim 1.1ns）② native 往返净 ~3.5µs ③ 写路径端到端 9.7µs/call（安全层净 ~5.2µs）④ mailbox p50=28µs/max=34µs ⑤ 足迹（text 82-91KB@flash / bss 92-113KB / 堆余 ~218KB）⑥ 单核抢占并发（锁竞争 p95 不变、尾部 +12µs、estop 并发中生效 + 可恢复）+ APP 冷启动 4.8ms。**WAMR xtensa 修复**：invokeNative 切官方汇编（`invokeNative_xtensa.s` + `-Wa,--noexecstack` 补注记；GENERAL C 版跨板不可靠——WAMR cmake 注释自认）。**失败可见性**：runtime.c app_init 异常路径补 WAMR 异常文本 printk。**事实登记**：ESP32-S3 无 SMP（Q-24 呈递）；k_cycle_get_64 本板冻结 → CCOUNT（dev-env 教训 18/19）；通道描述符须独立持久对象（注册存指针）。诊断插曲（如实）：invokeNative/解释器/栈深三轮误诊后定位为 bench 自身描述符别名 bug（低级但真实——native_sim 测试惯例掩盖该约束）。


#### Q-24 调研补充（2026-09-27 · owner 指令"深度调研我们选择的板卡哪些支持 SMP"；全部可复核）

**调研范围**：DEC-28 目标板集（ESP32-S3 / ESP32-P4 / STM32H7 + native_sim）+ 备选经典款。两层证据：钉版 v4.4.0 源码树/构建实测（本地）+ 上游状态（4.5 发布说明 / GitHub main 树 / Espressif 官方页）。

**逐板事实表**：

| 板/SoC | SMP（v4.4.0 钉版） | 上游状态 | 证据 |
|---|---|---|---|
| **ESP32-S3**（xiao_esp32s3） | ❌ 无实现 | **无任何公开进展**：4.5 发布说明零提及；issue #83168 中"扩展到 S3"请求无维护者回应 | 本地构建 CONFIG_SMP=y 链接失败（arch_cpu_start 未定义）；soc/espressif/esp32s3 仅 AMP 文件（esp32s3-mp.c，SOC_ENABLE_APPCPU 门控） |
| **ESP32 经典款**（esp32_devkitc / esp_wrover_kit / ethernet_kit / threadbr） | ✅ **构建实证可用**（本会话实测：hello_world + SMP=y + 2 核 → 构建绿，arch_cpu_start/z_smp_init 符号入镜像；4.0 时代的损坏〔issue #83168〕在 4.4 已修） | Zephyr SMP 测试参考板之一（discussion #77131："multicore SMP tested mainly on esp32 and qemu_x86"）；但 **Espressif 官方支持页称 "SMP is currently non-functional"**（快照时效不明，可能指运行级不稳定）——两说并存，运行级需真板验证 | esp32-mp.c（#ifdef CONFIG_SMP，IPI 实现） |
| **ESP32-P4** | ➖ **SoC 支持不存在**（v4.4.0 soc/espressif 无 esp32p4） | **4.5 加入**（多块官方板：esp32p4_function_ev_board〔16MB flash + 8MB PSRAM〕、OLIMEX/Waveshare 等）；拓扑 = 双核 RISC-V HP@400MHz + LP@40MHz；**main 分支 soc/espressif/esp32p4 无任何 SMP/mp/cpu_start 文件**——HP/LP 为 AMP 双镜像（default_lpcore.ld / start_lpcore.S），HP 双核 SMP 未接线 | Zephyr 4.5 release notes + main 树目录 |
| **STM32H7**（H743 目标 / H745 双核变体） | ❌ **架构级不可能** | Zephyr SMP 实现清单 = riscv / cortex_a_r / x86 intel64 / arc / arm64 / intel_adsp / esp32(xtensa)——**无任何 Cortex-M**；H7 双核变体（M7+M4）= AMP 形态 | v4.4.0 树 arch/*/smp 实现清单 |
| **native_sim** | ✅ 实证（Q-23 批 SMP=4 核真并行常设于 CI） | — | framework.conc / framework.wamrdemo |

**关键判读**：
1. "等 Zephyr 给 S3 加 SMP"**不可预估周期**（无 PR、无 issue 响应、4.5 零提及）——原建议 A 的"跟进上游"分支实质弱化为无期限等待。
2. **体系内唯一今天就能在真芯片构建 SMP 的 = ESP32 经典款**（构建已实证；运行级因 Espressif 官方页"non-functional"表述存疑，需真板冒烟后才能挂 framework.conc）。
3. P4 升级到 Zephyr 4.5+ 可获得 SoC 支持（对 PSRAM/大 flash 有吸引力），但**不解决 SMP**（P4 HP 双核同样未接线）。
4. H7 上"双核终验"概念不适用（单核 SoC + M 核架构无 SMP）。

**修订建议（数据版）**：A'——V1 双核终验以 **native_sim 多核为准**（唯一已实证且常设运行的真并行载体）；若 owner 认为必须在真芯片上终验，则采购一块 **ESP32 经典款开发板**（esp32_devkitc-wrover 等，几十元级）作并发终验专用板，到货后流程 = SMP 运行级冒烟（官方页 non-functional 表述需先证伪/证实）→ 通过则挂 framework.conc + boardbench ⑥ 双核版。S3 继续承担 bring-up/效率/单核角色；"等 S3 SMP 上游"仅作观察项不作依赖。

**引用**：zephyr issue #83168（ESP32 SMP 4.0 时代损坏）/ discussion #77131（SMP 测试面）；Zephyr 4.5 release notes（P4 加入、S3 无 SMP 动静）；github main soc/espressif/esp32p4 目录（无 SMP 文件）；developer.espressif.com/software/zephyr-support-status（"SMP is currently non-functional"）。


- 2026-09-27 · **裁决：Q-24 → DEC-44（方案 A，基于板卡 SMP 深度调研）**：owner 原文："选择A，同时我需要请你进行真机测试确认现在我们的框架是否会导致IO操作延迟过高"。裁定内容：① V1 双核终验以 **native_sim 多核为准**（framework.conc 已在 4 核真并行常设于 CI）；② 不采购 ESP32 经典款板；③ "S3 SMP 上游落地"降级为观察项（DEC-19 跟进机制内关注，不作任何计划依赖）；④ S3 本板继续承担 bring-up/效率/单核角色。**同批新任务（owner 指令）= 真机 IO 延迟实测**：确认框架层（APP/权限/安全/审计）是否导致 IO 操作延迟过高——需最小真 GPIO 后端（driver_dispatch 板级替换点，L5 白名单内）+ 三层对照基准（裸 Zephyr GPIO / 经框架安全层 / 经完整 wasm APP 路径）。


- 2026-09-27 · **板级三单元交付（DEC-44 同批：真机 IO 延迟实测 + 最小真 GPIO 后端）**：① `CONFIG_TS_DRV_GPIO`（Kconfig 默认关，native_sim/CI 零影响）+ zephyr,user DT 绑定（uid 串匹配通道；GPIO9@xiao D10）——driver_dispatch.c 板级替换点（L5 白名单文件）内实现真写，sim 记录保留（L4 golden 连续性），L5 唯一写路径检查增 boardbench 裸基线豁免（对照层合法性，产品代码禁令不变）；② boardbench BB5 三层对照（board-bench-01 §1.5）：裸 gpio_pin_set_dt p50=204ns（4.9MHz）/ 框架安全层 5.75µs（174kHz，压测竞争下 p50/p95 零变化、max +66ns）/ 完整 wasm 路径 10.59µs（94kHz）——**判定：不过高**（100Hz 更新占周期 0.058%，两数量级裕量；位带式 >174kHz 走硬件外设通道为架构本意）；③ 过程实证教训登记 dev-env 教训 20（ZEPHYR_USER_NODE 为 4.5 API，4.4 须 DT_PATH(zephyr_user)；未定义宏在 DT 包装宏里被字面拼接产生连环假象）。回归：native_sim bench 构建 ✓ / L5 6/6 / pytest ✓ / twister 全量（见当日 CI）。


- 2026-09-27 · **板级四单元交付（owner 指令：WiFi+zenoh 命令往返实测）：上游 esp32s3 WiFi 打通 + 命令往返 p50≈12ms（省电关）——twister 14/14（58 用例）/L5/pytest/L3 五验证点全绿**：① 上游 Zephyr v4.4 esp32s3 WiFi 实测可用（west blobs fetch hal_espressif 预编译 blob + overlay 使能 wifi 节点；mbedTLS/PSA 依赖、非 SMP 约束）；② netbench 载体（firmware/tests/netbench/：WiFi STA→DHCP→prov 注入（TS_TEST 通道，定稿键序 CBOR）→ts-net/zenoh-pico 完整命令面；凭证经 cmake 变量注入仓库外，git grep 零泄漏验证）；③ 实测（docs/netbench-01.md，N=100×2 轮）：L0 路由本机 p50=0.10ms / **L1 sys 查询全路径 p50=12.0ms p95=28.6ms max=55ms** / L2 estop-clear 重命令 p50=13.5ms——**WiFi 省电为第一敏感项**（默认 modem-sleep：p50 66ms max≈105ms≈DTIM；NET_REQUEST_WIFI_PS 关闭后 5.5×；固件已默认关）；④ 判读：命令/Agent/API 级无感、断链窗占比 0.2%；闭环控制走板内路径（网络层定位为下发/遥测，与架构一致）；本地框架处理 µs 级占比 <0.1%；⑤ 过程修复：zenoh-pico 1.10.1 回调非 const（新工作区首编译即拦——此前 twister 假传输从未编 zenoh 面）→ 修复后 **L3 五验证点复跑 PASS（环境重建后首次，待办清账）**；WSL mirrored LAN 入站经 owner UAC 放行 Hyper-V 防火墙（Windows 本机自测不可作判据，教训 21③）；WAMR version.cmake 并行竞态判明（单套件重跑绿，非回归）。环境教训登记 dev-env 21（六要点）。

- 2026-09-28 · **板级五单元交付（prov/APP flash 持久化，AGENTS 二十三余项首项）：flash 后端入库 + 真机持久化全链验证 PASS——twister 15/15（65 用例）/L5 6/6/pytest 2/2 全绿**：① ts-store flash 后端（CONFIG_TS_STORE_FLASH + DT 五分区 ts_prov/meta/slot_a/slot_b/noinit〔carved 自 espressif AMP 布局空闲 slot1 区，boot/sys/slot0 与 esptool 偏移零变化〕+ fw_b 预留〔DEC-23〕）：ops 增 erase_off、逐 4B 字"读-比-写"垫片（同值跳过幂等/位子集校验/仅抹除态编程）、分区缺失与尺寸错配 = 构建期失败；② 上层适配：meta 副本步距动态化（分区尺寸/2）+ 写前范围擦除；noinit one-shot 读清（flash 持久介质防陈旧误报，RAM 掩盖缺口收敛）；ts_store_slot_erase 公共 API 增补 + stage_begin 安装前抹除（LLD-ts-store v0.3 同步）；prov 注入一体单次连续写（sim 程序一次语义拦截双写缺陷，prov.c 零写不变）；cbor_min 无条件编译（TS_NET=n 时 appmgr 依赖暴露，真实依赖修复）；③ CI 覆盖：framework.store.flash 变体（native_sim sim-flash，EXPLICIT_ERASE 比真机严格）7/7 PASS；④ 真机验证（docs/board-persist-01.md，persistbench 载体）：完整单迹 = 首启烧录会话（prov 注入 + 440B TSAP 分步安装 + activate + 暖复位）→ 复位后 prov/meta/slot 全出自 flash、APP 自 slot 装载运行 + evt 写路径全链 PASS；附带证据 = 跨固件重刷持久（west flash 不动分区）+ 中断会话一致性（半途复位 → step8 r=-7 不阻塞，无不一致激活）；⑤ 语义观察留痕：冷启动 poweron_init 后通道处 SAFE_POWERON 态，APP app_init 期写被拒（TS_E_STATE）= 合同 1/3 预期语义（ACTIVE 迁移 = set_link，正常部署由 linkmon 驱动；TS_NET 默认 y 时无传输压 linkloss 亦真机观测正确生效）；⑥ API 口径：PARTITION_ID/SIZE 现行宏（FIXED_PARTITION_* v4.4 弃用）。余项（板级六候选）：estop chosen overlay、PSRAM 挂接（HLD §4.6）、PWM/ADC 真驱动、WiFi 重连策略、生产 prov 烧录通道（esptool 直写/Agent push_prov MA3）。

- 2026-10-01 · **板级六单元交付（owner 指令"优先解决 PSRAM 挂接"）：WAMR 实例堆 256KB 入 PSRAM（DEC-27/HLD §4.6 兑现）——twister 15/15（65 用例）/L5 6/6/pytest 2/2 全绿**：① 两条事实修正（均有构建/源码证据）：早期"Zephyr 4.4 无 psram 节点"评估有误（psram0@esp32s3_common.dtsi + N8R8 dtsi 8MB；N8R8 八线须显式 SPIRAM_MODE_OCT，默认 QUAD 即 esp_init_psram 硬停）；WAMR-2.4.5 的 WASM_ENABLE_GLOBAL_HEAP_POOL 旗标无消费者——wasm_runtime_init() 实为系统分配器，"64KB 池基线"从未生效；② runtime.c 统一显式池：wasm_runtime_full_init(Alloc_With_Pool) 注入堆缓冲（PSRAM = shared_multi_heap_alloc(SMH_REG_ATTR_EXTERNAL)〔esp32s3 官方注册面〕；其余 = 内部静态池），零上游补丁；Kconfig TS_APP_PSRAM_HEAP（默认 n，native_sim/CI 零影响）；TS_APP_WAMR_HEAP 默认 65536→262144（池模式下 64KB 结构性不可行——线性内存一页即 64KB；twister 实证拦截后修正，HLD §4.6 表注记 + LLD-ts-appmgr v0.5）；③ 真机验证（psrambench，docs/board-psram-01.md）：8MB 八线 PSRAM 识别 + memtest OK；SMH 探针 buf=0x3c030060 读写一致（外部 RAM 地址域）；WAMR 池 buf=0x3c030060@256KB；APP 全链 PASS（init_res=0 直启面，与 persistbench 冷启 -4 互为对照）；④ 量化对照：PSRAM 开 = dram0_0_seg 38.8%（154928/399108）；PSRAM 关 + 256KB = 溢出 14548B（DEC-27 目标内部装不下的硬证据）；生产 app conf 升每板默认（44.7%）；⑤ PSRAM 分层纪律结构面成立：仅 WAMR 实例堆入 SMH 分配面，框架安全数据/core/zenoh/WAMR 控制面全留内部 SRAM。

- 2026-10-01 · **板级七单元交付（owner 指令"其次 WiFi 重连策略"）：双断链全链自愈 4.2/9.2s（真机）——twister 15/15（65 用例）/L5/pytest 全绿**：① 分层定稿（docs/board-reconnect-01.md §1）：WiFi 关联维持 = app glue（Zephyr esp32 驱动无自动重连；固定 2s 无抖动重试 + 断线 net_dhcpv4_restart〔esp32 口断线不清地址/租约，陈旧绑定态下重连同址无 ADDR_ADD 事件〕）；zenoh 会话恢复 = ts-net 自带退避（250/500/1000/2000，DEC-27）；检测加速 = **ts_net_session_media_down()** 新增公共 API（静默掉线 = 僵尸 TCP 半开：net_if 仍 up、读任务阻塞 recv、租期心跳在本地缓冲"成功"，is_up 自省分钟级才收敛——承载断线事件显式下沉，会话下一 poll 立即判 DOWN）；② 过程修复（三轮真机迭代，如实）：ts-net 周期体迁专用工作队列（sysworkq 上 zenoh 阻塞 open/close 饿死同队列 WiFi 重试工作，实证迟 18s；栈 4096/优先级 8 = DEC-43 线程序）；netbench net_mgmt 回调重入自激修复（回调内 PS/DHCP 请求 = connect/ADDR 事件每 ~40ms 风暴；纪律 = 回调只置标志 + k_work_submit）；③ 真机（NB-R 脚本化双断链，设备侧强制断开 = STA 视角与 AP 掉线等价）：#1 全链自愈 9222ms（含首关联 7s）/ #2 4230ms（快关联缓存 2s）→ NBR PASS cycles=2 + 心跳稳定；zenoh 同进程 close→re-open 生命周期首次实证可用；恢复后客户端 L1×30 零失败 p50 13.4ms（板级四基线 12.0ms 一致）；局限如实：真实 AP 断电场景未测（板级环境无 AP 控制）；④ LLD-ts-net v0.3.7 / dev-env 教训 24 / netbench 板 conf 系统池让 8KB 同步。

- 2026-10-01 · **板级八单元交付（owner 指令"依次解决剩余问题"第三项）：estop chosen 绑定真机验证 PASS（硬件链路 ×3）——twister 15/15（65 用例）/L5 6/6/pytest 全绿**：① 绑定机制修订（docs/board-estop-01.md）：v4.4 EDT 管道不发射非 zephyr 前缀 chosen 宏（dtlib 属性在、edtlib 弃——诊断法：dtlib 直读 dts vs edt.pickle 对比）——零补丁纪律下改走 **aliases**（`DT_ALIAS(ts_estop_gpio)`），模块 driver_dispatch.c 同步切换，DR-11 语义不变（LLD-ts-safety v0.2.5 留痕）；② 触发注入（无人工按键自动化）：io_mux 输入+输出双使能 + 翻转 GPIO 输出寄存器 → 引脚电平真实变化 → 中断完整硬件路径（bench 测试注入，产品唯一写路径不变）；③ 真机（estopbench，EB* 行）：**引脚沿 → ISR 直达 → fault 落通道 ≤20ms（轮询粒度上界）→ 锁存 → clear_fault + 显式 commit 恢复**，×3 轮全绿——合同 5（estop 不经协议栈/调度排队）真机首证；观测判据 = 通道三态 fault=true（false→true 唯一来源 = fault 直写）；④ 如实记录：TS_EVT_ESTOP 补发 = 0（deferred publish 属周期驱动接线，bench 直启面未接，framework.safety 测试已覆盖语义）；沿配置仍为上升沿占位（DR-11 prov 化 M2+ 待办不变）；⑤ 回归：twister 15/15 / L5 6/6（estop 调用图检查在宏切换后仍零违规）/ pytest 2/2。板级余项：PWM/ADC 真驱动、生产 prov 烧录通道（esptool 直写/Agent push_prov）。

- 2026-10-01 · **板级八收尾修复：WAMR version.h 竞态除根（b5852e6 的 native-build 失败归因）**：version.cmake 的 configure_file 写共享源码树（core/version.h），twister 15 并行套件的配置/编译竞争撕裂——CI 冷检出首现（板级四曾偶发、当时判"单套件重跑即绿非回归"，本批同症状复发后除根），本地热树掩盖。修复 = CI 检出 WAMR 后**串行 `cmake -P version.cmake` 预生成**（此后 configure_file 内容相同即不重写〔CMake 幂等语义〕，并行阶段写者归零；零上游补丁）。本地等价验证：冷树（rm version.h）+ 串行预生成 + 并行 twister **15/15 全绿**。dev-env 教训 21⑤ 表述更新（竞态已除根，旧处置作废）。

- 2026-10-02 · **板级九单元交付（AGENTS 二十七余项首项）：PWM/ADC 真驱动（ts-periph dispatch 板级后端）真机全链 PASS——twister 15/15（65 用例）/L5 6/6/Agent pytest 58+2s 全绿**：① PWM 真后端（CONFIG_TS_DRV_PWM，driver_dispatch.c = L5 白名单内；zephyr,user 绑定 pwm-uid+pwms 三元胞，LEDC 引脚路由经 pinctrl+channel 子节点）：写路径 = sim 记录〔L4 连续性〕+ pwm_set，失败进 ts_drv_pwm_err_count 观测计数（真机全程 0）；② ADC 真后端（CONFIG_TS_DRV_ADC，hal/api.c 输入面——合同 3 输入直读不经保护层，L5 输出写路径检查不辖输入面）：zephyr,user adc-uid+io-channels（官方文档示例模式），12bit/内部基准/12dB 衰减，mV = 通用换算 1100mV 口径（esp32 驱动 raw 预补偿：eFuse 校准+衰减反归一），读失败如实 TS_E_IO；③ **安全层存量欠账修复（本批被 bench 拦下）**：set_link(false) 断链迁移此前仅改 shadow = 物理输出滞留断链前值（HLD §4.5-S2 原文"声明值落驱动"欠账；fault 路径本就落驱动故 estop 真机未暴露）——修复 = !up 迁移声明值经 ts_drivers 落驱动，DR-04 恢复不回写不变；余项登记：注册期 poweron 值落驱动未接线（V1 各板 poweron 与硬件缺省一致未暴露，board-periph-01 §5）；④ **Kconfig 结构缺陷修复**：TS_POWER/TS_PERIPH 误嵌 if TS_NET 块（TS_NET=n 不可见；estopbench 未用 periph 故未暴露，periphbench 构建即被拦）——endif 上移回归 depends TS_HAL 本位；⑤ api 域收紧：ts_pwm_set hz 下界 100Hz（打包粒度，V1 桩曾静默接受）；⑥ 真机（periphbench，PP* 行，docs/board-periph-01.md）：LEDC duty 六点 ±1‰（含跨 hz 1000↔5000 重配 res 14↔13）/ 保护层限幅 900‰→700‰ 落硬件+TS_E_RANGE / 端点 0%·100% 停止态 / **断链 fail-safe linkloss 0% 落驱动真机首证** + 恢复显式重写 / ADC 轨到轨注入 0mV·3122mV（3.3V 饱和）；⑦ 板级八遗留即清：LEDC duty 寄存器字段 = ticks<<4（hal ledc_ll 直证；reg 头部位域注释误导）。文档：LLD-ts-safety v0.2.6 / LLD-ts-hal v0.2.2 / LLD-ts-periph v0.5 / project-plan v1.15（板级五~九收口补账 + §5 owner 待办清空）/ dev-env v2.8 教训 26。余项（板级十候选）：生产 prov 烧录通道（esptool 直写/Agent push_prov〔MA3〕）、Agent→真机完整部署 E2E、注册期 poweron 落驱动。

- 2026-10-02 · **owner 指令登记：ESP32-P4 移植暂缓**（原板级十候选 #8；Zephyr 升级评估〔前置〕一并后移）。下一单元按建议序 = Agent→真机完整部署 E2E（板级十）。

- 2026-10-02 · **板级十单元交付：Agent→真机完整部署 E2E 双轨首次闭环（DEPLOY PASS + DB PASS，双轮复现）——twister 15/15（65 用例）/L5 6/6/Agent pytest 58+2s 全绿**：① 载体 deploybench（板侧 DB*：WiFi glue〔netbench 板级七定稿〕+ prov flash 持久〔首启 TS_TEST 烧入〕+ ts_core_boot〔zenoh 命令面 + 步骤 8 slot 装载〕+ 激活检测自动暖复位 + DB6 运行宣告；三合一内存 = DEC-29 每板裁剪 TS_APP_LOAD_MAX 2048/TS_SAFETY_MAX_CHANNELS 8，池不动，PSRAM 承 WAMR 堆，dram 99.81%）+ client.py（**复用 MA3.1 deploy 链本体**：发现→keygen/打包〔tsap_verify 真 ed25519〕→租约闭环〔DEC-41〕→4×256B 分块〔idem+high_water〕→容器事实对拍→激活→复位后 get-app 对拍 state=ACTIVE+app_id+slot）；② **跨轨命名漂移修复**：Agent TsapManifest._EXPORTS_ALLOWED = init/tick/evt（LLD §2 笔误漂移；runtime lookup/夹具/LLD §4 三方均 app_*）照抄漂移面 = 拒绝一切真包，env 门控 sim E2E 默认跳过掩盖——白名单+三测试+LLD §2 对齐（LLD-ts-appmgr v0.5.1）；③ **get_info 惰性初始化打回装载结果修复**：boot_start 成功不置 initialized → 首次观测面读取把 ACTIVE 盲写回 STAGED + active_slot 不回填 = 槽位对拍必败——成功路径补 initialized=true + active_slot=meta（v0.5.2；真机首证）；④ 过程留痕：prov 手抄数组丢 6 字节（fail-closed 拦下；esptool 分区 dump 定位；改脚本机械生成+生成期走查验证）；换 bench 分区残留态 → 流程增 esptool erase_region；zenohd 后起会话自愈实证。文档：board-deploy-01 + LLD-ts-appmgr v0.5.1/0.5.2 + dev-env 教训 27 + project-plan v1.16。余项（板级十一候选）：生产 prov 烧录通道（esptool 直写/Agent push_prov）、注册期 poweron 落驱动、input monitor 真输入、MCUmgr 固件 OTA、Zephyr 升级评估（P4 暂缓随批）、H7 移植。

- 2026-10-02 · **H7 内存评估（owner 询问触发："内存需求非常紧张，确认各种配置内存需求，评估 stm32h7 是否符合需求"）——结论：H743 满足且无需外部 RAM**（docs/h7-memory-assessment.md）：① S3 实测四配置：框架+驱动 ~65KB（GC 壳值）/ 框架+WAMR 无网 38.8%（256KB 堆必须 PSRAM——纯内部溢出 14.5KB）/ 网面 WiFi+zenoh 98.9% / 全配置 99.8%+PSRAM——**S3 紧张是结构性的**（链接可用仅 390KB，全配置内部需求 ~660KB）；② H743 实构建（nucleo_h743zi，arm-zephyr-eabi 已装入 SDK）：网面 ETH 形态 **326KB/512KB=62.2%**（比 S3 WiFi 形态轻 68KB 余 186KB）+ FLASH 233KB/2MB；全配置推算 sram0 388KB(76%) + **D2 sram1+sram2 物理连续 256KB 恰容 WAMR 实例堆**（DEC-27 目标值不降配），内部合计 ~644KB/992KB(65%)，DTCM 128KB+SRAM4 64KB 未动；③ H7 前置工作项登记（报告 §4）：WAMR 板级分派映射（THUMBV7EM/invokeNative 验证）/ 堆摆放 linker region / ts flash 分区 overlay / DT 绑定平移 + ETH glue / FMC SDRAM 仅未来超 992KB 才需；④ 测量工件两例留痕：RAM slot 后端默认 2×256KB 真板直接构建即溢出（各 bench 显式收紧惯例确认；默认值是否下调 = 登记不动手）；直启 bench 未根引用的 APP 面被 --gc-sections 回收（足迹测量须用真跑 APP 载体）。

- 2026-10-02 · **owner 指令登记（计划调整）**：① H7 适配放弃；② P4 适配恢复（动机 = APP 复杂性余量；硬前置 = Zephyr 升级 4.5+，v4.4.0 无 esp32p4 支持〔Q-24 调研钉死〕，升级走门 ⑤）；③ 新增 MD demo 批（全部功能开发完成后：从简单到复杂 + 混合各一个小 demo）。

- 2026-10-02 · **Agent demo 就绪度评估交付（owner 指令 review 现有实现；docs/agent-demo-readiness-01.md，零代码改动）**：① **直答 owner 问：真实 LLM 调用从未实测**——证据 = 全部测试 FunctionModel 剧本 / agent/config.toml 从未创建（仅 example 模板）/ agent/audit/ 目录不存在（生产运行零痕迹）/ config.py 启动期 default_model 空即 ConfigError；补测需 owner 提供模型（ollama 本地或 OpenAI-compatible 端点，config.example.toml 已备注入说明）；② 已就绪面：部署链真机闭环 / 运行时四回调+mailbox / natives 6 个（gpio·pwm·adc·time·log）/ clang wasm32 工具链 / 模拟器 scenario+L4 重放 / skills 渐进披露；③ **缺口清单**：G1 APP 代码生成不在链内（app_develop V1 边界 = LLM 只产 manifest，wasm 由调用方提供——编程链断在第三环，demo 批最大前置，新工具 app_compile + 语义升级走门 ③）/ G2 真实 LLM 未测 / G3 input monitor 真输入（板级十三）/ G4 V1 单活跃 APP（多 APP 混合不可，demo 按单 APP 多能力设计）/ G5 模拟深度按需扩展；④ demo 阶梯 D1-D9 草案（简单 D1-D2 / 中 D3-D5 / 复杂 D6-D7 / 混合 D8-D9，双载体 = scenario 仿真 + 真机部署）；⑤ 建议 MD0 的真实 LLM 冒烟提前（不等 P4）。

- 2026-10-04 · **MD0-1 交付（owner 提供 AI API：minimax anthropic 兼容端点 / MiniMax-M3 / 上下文 1M〔owner 指令〕）：Agent 真实 LLM 冒烟双 PASS——app_develop 真实 LLM 全链首次贯通（SMOKE2 两轮复现 56.3s/29.6s）；pytest 58+2s/ruff 全绿**：① SMOKE1 = pydantic-ai→minimax 结构化输出管道 PASS；SMOKE2 = spec→真实 LLM（skills 渐进披露+read_skill）→DevelopOutcome→manifest 硬校验→打包签名→复验 全链 PASS；LLM 产出质量超预期（caps 精确最小权限 / test_plan 8 条自带军规风格 / steps 含 Q-登记与 review 门——skills 注入生效）；② **冒烟拦下三项产品缺陷并同批修复**：app_develop 缺输出上限（思考型模型耗尽 provider 缺省→链路开箱不可用；补 OUTPUT_MAX_TOKENS 16384）/ config 加载路径错（文档约定 agent/config.toml，代码找包内路径——配置从未能从文档位置加载；修 parents[2]）/ manifest 硬校验无反馈回路（一次一个错整链报废；补错误反馈+message_history 续跑回路预算 3 + caps 文法内联提示）；③ 密钥纪律：密钥仓外文件 600 权限 + env 注入（ANTHROPIC_API_KEY/ANTHROPIC_BASE_URL），config.toml（gitignored）仅模型串；提交前 git grep 零泄漏验证；④ **G2（真实 LLM 未测）关闭**；G1（APP 代码生成）仍为 MD0 最大前置，本轮 LLM 规格理解力为正面信号。文档：agent-llm-smoke-01 + dev-env v2.11 + plan v1.18。

- 2026-10-04 · **MD0-1 收尾：CI native-build 第三次咬人（890ff66，1/15 卡死）→ WAMR 竞态真根因钉死并除根**：本地冷树复刻（删 version.h → 预生成 → 并行 twister 全新目录）复现 8/15 报 version.cmake configure_file "No such file or directory"；单套件同条件绿 = 并发触发。**实证推翻板级八"串行预生成除根"结论**：同内容 configure_file 在共享输出路径仍有临时文件写删动作，15 并发进程竞争即撕裂（预生成只消除内容重写，未消除 temp 抖动）。**真除根 = 预生成 + chmod 444 只读屏障**（强制全部进程走"比较相同→零写"路径；本地冷树 15/15〔65 用例〕实证）。CI 步骤已改（预生成+只读两行）；dev-env 教训 21⑤ 第三次修订为终态（再生 version.h 须先 chmod 644）。

#### Q-25 · APP 代码生成链（G1）：工具面新增 app_compile + app_develop 产物契约扩展（门 ③——DEC-34 工具面变更须 owner 裁决）

**背景**：MD0 后 demo 批唯一大前置 = G1——app_develop 的 V1 边界是"LLM 只产出 manifest/计划，wasm 由调用方提供"（MA3 时代 wasm 工具链未定），"需求分析→设计→**编程开发**→部署"链断在第三环，所有"AI 生成 APP"类 demo 无法自动化。**仓外 spike 实证（2026-10-04，真 LLM MiniMax-M3 ×2 轮）**：LLM 一轮即写出合规 C 源（LED 呼吸灯：斜坡/回绕/确定性俱全，正确使用 __attribute__((export_name)) 与 natives extern 惯例）→ clang wasm32 一轮编译通过（7.9s/12.6s，wasm 239B/250B）→ 导入面 [ts_pwm_set] ⊆ natives 白名单 ✓、导出面四回调齐 ✓；另制成零依赖 wasm 面检查器（llvm-objdump-18 解析不了 strip 后 wasm，含已知好夹具——夹具对照校准通过）。

**选项**：
- **A（建议）**：① 新增 MCP 工具 **app_compile**（审批 auto——本地确定性构建、无网络无部署）：入参 C 源 + manifest；动作 = clang wasm32 自由固件 flags（appw/build.sh 同款）→ 零依赖 wasm 面检查（imports ⊆ natives 六白名单、exports ⊇ 四回调、尺寸 ≤ TS_APP_LOAD_MAX 对齐上限）→ 产物 wasm + 面报告；编译失败如实回传 stderr（供反馈回路）。② **app_develop 产物契约扩展**（向后兼容）：DevelopOutcome 增可选 `source_c` 字段，wasm_path 变可选——LLM 直接产源码时链内自动编译（同检查器），高层链直达"spec→可部署包"（DEC-34 S2 语义补全）。
- B：仅加 app_compile，app_develop 不动（调用方自编排 develop→compile→package）——面最小，但高层链仍断，demo 全链需三跳。
- C：LLM 直出 wasm 字节——不可行（二进制尺寸/结构不可控、无法审查），列此仅为排除留痕。

**建议**：A。spike 已证 LLM 侧就绪；编译反馈回路模式（错误文本 + message_history 续跑，预算 3）已在 MD0-1 验证同型。

**影响**：工具面 +1（app_compile；域归属 tsap/wasm 实现批定）；app_develop 输出向后兼容扩展；产物部署仍全走既有 deploy_push_app（strict 审批 + tsap_verify 不变——编译产物不豁免任何验签）；测试 = FakeModel 剧本 + 真 clang 子进程（agent-checks CI 需 clang，ubuntu runner 自带，实现批验证）；安全边界 = 导入面白名单 fail-closed（沙箱外符号一票拒绝）+ 编译仅产 wasm 不执行。

---

- 2026-10-04 · **CI native-build 间歇失败处置（d4060f9 #29 同 1/15 症状；#28/#30 同 workflow 绿）**：如实纠错——chmod 444 在本地两种语义（长期树/全新克隆）均 15/15，但 CI 仍间歇挂，"真除根"结论尚不成立（剩余偶发面 = runner 资源/负载域，本地不可复现）。既有注解只抓到进度行、真实死因不可见（logs API 403）——ffd50be 补失败诊断转储（twister 尾部 40 行 + 套件 build.log 错误块 + nproc/free 环境上下文进 step 日志；注解首错匹配面扩至 Build failure）。下次复发即可定位真因。现状：#30（ffd50be）四 job 绿。

- 2026-10-04 · **裁决：Q-25 → DEC-45（方案 A）**：owner 原文："按照方案A执行，请你再更多的研究其他 Agent Cli 的实现，学习他们的工程方法保证 coding 可靠性"。裁定：① 新增 MCP 工具 app_compile（auto 类）；② app_develop 产物契约扩展（可选 source_c，链内编译）；③ 附带研究指令 = 其他 Agent CLI 的 coding 可靠性工程方法调研并映射落地。

- 2026-10-04 · **G1 实现批交付（DEC-45）：APP 代码生成链落地——SMOKE3 真 LLM 全链双轮贯通（"需求→设计→编程→打包"AI 全链首次打通）；pytest 69+2s / ruff 全绿**：① **可靠性调研 → 八条工程决策（R1-R8）全落地**（docs/agent-codegen-reliability-01.md：Claude Code 可运行验证/Stop hooks 门、Codex OS 级沙箱、aider 编辑格式分级+lint/test 回路、Wink 故障分类）——验证阶梯四道确定性门（编译→白名单面检查→尺寸→**双编译字节一致**〔确定性自证，合同 9 精神延伸〕）+ stderr 完整反馈回路（预算 3）+ 整文件再生（弱格式域 whole 最可靠）+ 子进程时限/零执行/roots 白名单 + 产物 sha256/面报告入审计；② 实装：tools_tsap/wasm_build.py（零依赖 wasm 面解析器〔llvm-objdump-18 解析不了 strip 后 wasm，夹具对照校准〕+ compile_app_c 全检查链）+ app_compile 工具（auto）+ app_develop source_c 扩展（wasm_path 变可选，编译并入反馈回路，输出 compiled/compile_facts）+ CI agent-checks clang 显式保障；③ 测试 +11（69 passed，**无静默 skip**——板级十教训）；④ SMOKE3 ×2：第 1 轮 heap_kb=0 经反馈回路修正第 2 轮通过；两轮 646B/456B 均合规（白名单导入/四回调/双编译一致）；caps 精确最小权限 [gpio:write:0]；⑤ **MD0 前置全部完成**（真实 LLM 冒烟 + G1）——MD1 demo 阶梯解锁。

- 2026-10-05 · **MD1.1 交付（部分，如实）：demo 阶梯第一批 D1/D2/D3/D5/D7——五 demo 真 LLM 生成全过（产物入仓 agent/demos/）+ 验证基础设施全通 + D1/D2/D5 判据 PASS（D1 含 res=0 全链首证）；D3/D7 被 P1 缺陷阻塞（docs/demos-01.md）；pytest 69+2s/ruff 全绿**：① 生成链：五 spec → MiniMax-M3 → source_c → 链内编译 → 签名包，全部白名单合规（199-283B）；app_develop 健壮性两补：数组字段 {"item":X} 传输伪影三处确定性解包（schema BeforeValidator/链内/提示）+ 链外回路预算 3→4；② 载体：deploybench 并入 PWM 通道（板级九绑定，D3 限幅判据）+ 连续部署修复（DB6 alive 循环持续检测后续激活——板级十单次部署设计缺陷在 MD1 暴露）；③ **三项 demo 基础设施知识**：linkmon 判活 = host 心跳 publish（…/sys/hb-host 1s——此前所有 client 未发过 = 通道永远 SAFE 态写全 -4，判据盲区；md1_run3 心跳模板固化）；冷启装载时序（init 写必然落 SAFE 窗——行为写应放 tick/evt）；audit 64 环/16 快照窗口语义；④ **P1 缺陷登记（阻塞 D3/D7，专项 MD1.1b）**：连续激活流中写 meta copy0（seq 较小侧轮转）的激活在暖复位后装载旧 slot——三轮统计 D3(3rd)3/3、D7(5th)3/3 复现，写 copy1 的 0%，单推成功；esptool dump 证写已落盘 + activate 回读过 + 逻辑审计无果 → 定位方向 = 真机 flash 读路径复位前后差异/erase-write 时序窗；sim twister 仅覆盖 2 轮 meta 写（≥3 轮用例入 MD1.1b）。

- 2026-10-05 · **MD1.1b 交付（owner 指令"先解决该缺陷"）：P1 根治——meta 双副本读的共享缓冲 bug（一行修复）；metabench 受控复现六轮定位；真机五 demo 全 PASS（MD1.1 完整收口）；twister 15/15（65 用例）/L5/pytest 69+2s 全绿**：① **根因**：ts_store_meta_read 两次 read_rec 共用一个 data 缓冲——copy0 的 body 被 copy1 读取覆盖；当选 copy0（s0>=s1，即第 3/5/7… 次写后的启动）时 memcpy 给调用方的是 copy1 旧内容。触发面 = "双副本皆有效且 copy0 较新"（D3/D7 铁律 100% 的机制解释；板级五以来存在但 2 轮测试从未覆盖该分支）。修复 = data0/data1 分缓冲。② **metabench**（新载体 firmware/tests/metabench）：六轮写+暖复位+双副本十六进制打印——修复前 boot 盘上双副本正确而 meta_read 返回旧值（读路径缺陷铁证）；修复后六轮全对。③ **回归补口**：framework.store meta 往返 2→6 轮（≥3 轮覆盖 copy0 较新分支）；appmgr staged 用例此前**骑在 bug 上**（依赖陈旧读值碰巧对齐期望）——补 store reset 显式净基线。④ **D3 判据修正两处**：deploybench 通道上限 5000Hz|700‰→1000Hz|700‰（打包域 hz 占高 16 位，hz 域不重叠的限幅永不触发——打包域限幅语义留痕）；audit 聚合采样（斜坡周期 4s vs 16 条快照 1.6s，单快照抽样运气）；D7 装载谓词放宽 state∈{3,4}（装载后 2s 即回滚，==3 窗口撞不上）。⑤ 观察项：deploybench watch 同槽重推不触发复位（回滚后 meta 翻槽，再部署落回同槽——五连部署序天然换槽不受影响；手动重推场景需先翻转或硬复位，登记不动手）。**真机终态：D1/D2/D3/D5/D7 全 PASS（D3 限幅 23 条 -12+700‰ 聚合实证；D7 state=4 回滚确认）。**

#### Q-26 · 音视频传输 demo（zenoh）+ SD 卡读写 demo：硬件前置 + 能力面扩展（门 ③——ts_perm_v1 权限类扩展）

**背景**：owner 指令 demo 增加这两类。现状事实：① xiao_esp32s3（当前板）**无摄像头/麦克风/SD 卡座**——Seeed 的 Sense 版才带 OV2640 摄像头 + PDM 麦克风；② 固件 natives 面 = 六函数（gpio×2/pwm/adc/time/log），**无任何音视频采集与文件系统能力**；③ 两者都要求 ts_api_v1 扩展新权限类（如 av/fs）= ts_perm_v1 文法变更 = 权限模型变更（review 门 ③）+ zenoh 侧大块数据传输面（当前遥测 payload 上限 128B，视频帧需 MB 级分片策略）。

**选项**：
- **AV 传输**：A) owner 确认有/购 XIAO ESP32S3 **Sense** 版（带 OV2640 摄像头+麦克风，约 ¥60）——DVP 摄像头驱动 + JPEG 帧捕获 + zenoh 分片 pub（新事件/遥测类）；B) 无 Sense 用外接 I2S 麦克风模块先做**音频流** demo（音频先行，视频随 Sense 到货）；C) 两者都等硬件。
- **SD 卡**：A) 外接 microSD SPI 模块（约 ¥5-10）+ Zephyr disk/FS subsystem + ts-fs natives（文件枚举/读写 API，新 fs 权限类）——SD 槽位走 ts-periph 描述符注册（uid 逻辑名）；B) 暂不做。
- 建议：AV=A（Sense 版）或 B（音频先行）；SD=A。都需 owner 提供硬件；固件侧批 = natives/白名单/权限类扩展（本 Q 批准后实施）。

**影响**：ts_perm_v1 加类（av/fs）+ manifest 白名单扩展 + natives 白名单 NATIVE_WHITELIST 同步 + zenoh 大 payload 分片策略（视频帧 ~20-50KB/帧 vs 当前 128B 遥测——需分块遥测或专用帧通道）+ 两个新 demo（D-AV/D-SD）入 MD 批。

---

- 2026-10-05 · **裁决：Q-26 → DEC-46**：owner 原文："现在接入的即是带有摄像头和麦克风版本的sense版本，同时我已经插入sd卡板载sd卡卡槽"。裁定：硬件已具备（xiao_esp32s3 **Sense 版**：OV2640 摄像头 + PDM 麦克风 + 板载 microSD 卡槽含卡）——无需采购；MD1.2 批次开工（SD/摄像头/音频 bring-up + 能力面扩展随各批呈递）。

- 2026-10-05 · **MD1.2a 交付（DEC-46 首批）：SD 卡 bring-up 真机全链 PASS（SD PASS：7.5GB 卡识别 + FatFS 挂载 + 32KB 写读校验全等）**：① **重大事实**：Zephyr v4.4 树内有**官方 `xiao_esp32s3/esp32s3/procpu/sense` 板级变体**——OV2640（I2C1@0x30）+ lcd_cam DVP（chosen zephyr,camera）+ **SD 卡槽（spi2 CS=GPIO21/SCK7/MISO8/MOSI9，zephyr,sdhc-spi-slot + sdmmc-disk）DT 全就绪**，换板名即点亮；② sdbench（新载体 firmware/tests/sdbench，SD* console 行）：DISK_IOCTL 探卡 + fs_mount(/SD:) + 顺序写读 32KB（块标识防假阳性）+ 清理幂等；③ 过程教训：4KB×2 缓冲禁上主栈（首版 FATAL illegal instruction——大缓冲 + FatFS 深链超栈，转 static + 主栈 4K 后全绿）；Kconfig 符号 SPI_SDHC（非 SDHC_SPI）；fs_fat_t 实为 FATFS（ff.h）；④ **Zephyr 支持面结论（MD1.2 切分依据）**：SD ✓ 全链（本批实证）；**摄像头 ✓ 全链在树**（video_esp32_dvp + ov2640 sensor 驱动 + Sense DT——MD1.2b：cambench 帧捕获）；**音频 ✗ PDM 缺口**（i2s_esp32.c 零 PDM 支持——Sense PDM 麦克风需驱动扩展〔hal_espressif 有 i2s_std/pdm 组件可接〕，MD1.2c 评估呈递）；⑤ 能力面扩展（ts-fs natives + 权限类）随 demo 实现批呈递（Q-26 已裁方向，API 面细节届时走门 ③）。

- 2026-10-05 · **MD1.2b 交付：OV2640 摄像头 bring-up 真机全链 PASS（CB PASS：QQVGA RGB565 ×4 帧捕获 + 帧间 luma 差异实证真数据 + 首帧 38400B 落 SD 校验一致——MD1.2a/b 能力闭环）**：① cambench（新载体 firmware/tests/cambench，CB* console 行）：I2C SCCB 传感器 init → set_format(QQVGA RGB565) → 官方缓冲池路径（video_buffer_aligned_alloc ×4 → enqueue → stream_start → dequeue 轮转）→ luma 统计（帧间差异判真数据非死帧）→ 首帧写 /SD:/frame.raw + fs_stat 校验；② **关键路径事实**：**外部静态缓冲路径当前不可用**（自建 video_buffer 入队后 stream_start 报 gdma "Rx buffer not in DMA capable memory: 0"——缓冲地址实测在 DMA 域内且描述符链推演自洽，根因未钉死，登记观察项）；**官方 video_buffer_aligned_alloc 路径一次通**——V1 一律走池路径（官方样例同型）；③ Kconfig 门槛（真机实测）：DMA_ESP32_MAX_DESCRIPTOR_NUM 默认 16 不够（QQVGA 需 ≥10、QVGA 需 ≥38——本批 48）；VIDEO_BUFFER_POOL_HEAP_SIZE 默认不足（QQVGA ×4 帧需 256KB——含池结构开销）；VIDEO_BUFFER_POOL_NUM_MAX 同步；④ video_caps 自报 min_vbuf_count=200（上游驱动口径， informational）；⑤ Sense 板 chosen zephyr,camera = lcd_cam_dvp 全链生效（ov2640 I2C@0x30 + DVP DMA）。

- 2026-10-05 · **MD1.2 中期状态与下一步**：SD ✓（MD1.2a）+ 摄像头 ✓（MD1.2b）bring-up 完成；剩余 = **MD1.2d**（zenoh 传输面：视频帧 ~38KB vs 遥测 payload 128B 上限——分片通道设计 + ts-fs/ts-av natives 与 ts_perm_v1 权限类扩展，呈递门 ③）与 **MD1.2c**（PDM 音频：i2s_esp32 无 PDM 支持的驱动扩展评估）；D-SD/D-AV demo 随能力面落地。

- 2026-10-06 · **impl-review-02 交付（owner 指令"review 已开发内容风险 + 未裁决项盘点"；三路只读审查 + 主会话复核全部"高"级结论；零代码改动，只登记不动手）**：全库风险审查 3 高/8 中/N 低落 `docs/impl-review-02.md`（IR2-xx 编号族）。① **高**：IR2-01 看门狗合同（合同 4）整体空转——WAMR 无 fuel/超时、健康探针与 APP 同线程、`ts_wdt_register/feed` 生产零调用、wdt_start 后注册窗口被 boot 顺序阻断、全库无硬件 WDT 使能（system_fail 后永久挂死不自恢复；app_init/app_tick 死循环不可检测）；IR2-02 固件 COSE 验签结构桩——生产构建恒拒安装（部署面零可用）、TEST 构建两字节检查放行任意未签名 wasm+自声明 caps（当前全部真机验证均 TEST 语义——生产语义从未点亮）；同族：activate 整槽 hash 无对拍对象、boot 装载不验签；IR2-03 Agent PC 读面外泄链——compile_app_c 无 include 隔离（绝对路径 #include 探读主机任意文件→stderr 回喂 LLM）、wasm_path/key_path/package_path 读入路径不受 roots 白名单（全库仅 out_dir 受控）、max_bytes 调用方可放宽。② **中 8 项**：IR2-04 L5 正则不覆盖裸 `pwm_set(`；IR2-05 estop ISR 与 set_link/recover 覆盖窗口（commit.c 已有 irq_lock 复查范式未平移）；IR2-06 app_stop 强杀可留永久持有的 commit_lock（全输出写路径死锁）；IR2-07 回滚链不闭环（不验目标槽/不复位/meta 双损静默 slot0+回滚预算归零）；IR2-08 审计 actor 恒 0（DEC-40 src 未透传）；IR2-09 任务取消不终止子进程组；IR2-10 并发同 out_dir 固定文件名交叉污染；IR2-11 zenoh key 表达式注入（node/cube 无校验）。③ **正面实证**：写入路径唯一（gpio/pwm 驱动调用全库唯一于 driver_dispatch）、六 native 权限运行时 fail-closed 无绕过、**DEC-40/41/42 三项审查证实全部已实现且 fail-closed**（信封 v2/幂等回放/租约/遥测信封）、meta P1 修复在位（分缓冲）、断链物理落值、密钥零泄漏复核（WiFi 凭证串与 API 密钥 JWT 前缀两项 grep 模式全库 0 命中；config.toml gitignore 生效）；CI 四 job 绿（6a6e38c）。④ **未裁决项盘点 = 零**（Q-01…Q-26 全裁毕；Q-27〔MD1.2d〕尚未提交）；实现债（验签/看门狗/G3-G5/estop 沿/actor）与观察项清单见报告 §7。⑤ **处置建议呈 owner**（报告 §5，排期归 owner）：看门狗接线批最优先（含启动序与 APP 执行边界设计决策→门 ① 呈递）→ PC 读面加固批（纯工程不需 Q）→ 验签实装批（TSAP 头摘要字段 = 文件格式变更→门 ③，与板级十一生产 prov 通道天然同批）→ 小项打包（IR2-04/05/08）。

#### Q-27 · MD1.2d：zenoh 视频帧传输面 + ts-fs/ts-av natives + ts_perm_v1 权限类扩展（门 ③——权限模型/公共 API/协议面变更）

**背景**：DEC-46 已裁 MD1.2 批（SD ✓〔MD1.2a〕/ 摄像头 ✓〔MD1.2b〕bring-up 完成）；D-AV/D-SD demo 需要：① 大块数据上 zenoh（视频帧 38400B〔RGB565〕vs 遥测 payload 上限 128B〔pubq.c PAYLOAD_MAX〕）；② 固件 natives 面扩展（当前六函数：gpio×2/pwm/adc/time/log——无文件系统与音视频采集能力）；③ ts_perm_v1 权限文法扩展（当前 class 集 = gpio/pwm/adc/power〔hal.h:29-37〕，无 fs/av 类）。三者均为门 ③ 面（权限模型/公共 API/协议）。**实测数据底座**（本会话 avbench 真机，docs/av-transport-01.md）：≤1KB 分片 + 4ms 打拍 + 分片级重试 = 零错误，1KB 档 172KB/s（QQVGA RGB565 ≈4.5fps）；>2KB 走 zenoh-pico 碎片路径系统性失败（Z_BATCH_UNICAST_SIZE=2048 静态头）；BLOCK 语义在 Zephyr 端背压下不保数据（应用层重试必须）；视频池 256KB 入 PSRAM 与 DVP DMA 共存实证。

**选项**（按子项，各附建议）：

- **① 传输通道形态**：A) **专用帧分片通道**——`…/<cube>/av/<stream>/frame` 键上 publish 分片（帧头：frame_id/chunk_id/n_chunks/len + 校验和；消费端〔host/Agent〕重组），遥测面 128B 上限不动；B) 抬高遥测 payload 上限复用现有事件面（动已裁常量、事件环与消费端全部重评）；C) host 拉（query 分页拉取——双向握手复杂、帧率受限）。**建议 A**（面新增不动既有语义；与 DEC-42 kind 注册表对齐新增 av 类 kind）。
- **② 分片参数与帧格式**：chunk **1KB** + 发送线程打拍 **≥4ms** + 分片级重试（≤5×20ms）——全部来自实测；帧格式 **JPEG**（OV2640 硬件压缩，QQVGA ~5-10KB/帧 → 15-30fps 可行）vs RGB565（38400B → ~4.5fps，仅演示保底）。**建议**：V1 采集面双格式可配（DT/manifest 声明），demo 用 JPEG。
- **③ ts-av natives API 面（最小面）**：A) `ts_av_capture(frame_buf, buf_cap) → len`（阻塞取一帧到 APP 缓冲，格式/分辨率经 manifest 声明、宿主按板配置）——**单函数最小面**；B) 回调/流式推送面（mailbox 帧 ready 事件 + APP 取）——事件驱动但 API 面大。**建议 A 起步**（demo 需求即满足；evt 面随真实 APP 需求再扩——门 ③ 再呈）。
- **④ ts-fs natives API 面**：A) `ts_fs_list/ts_fs_read/ts_fs_write/ts_fs_delete`（路径字符串 + 偏移读写）四函数；B) POSIX 风 open/read/write/close 句柄面（完整但句柄生命周期进沙箱治理）。**建议 A**（无句柄 = 无泄漏面；SD 单分区 FAT；写走审计）。
- **⑤ ts_perm_v1 文法扩展**：新 class **`av`**（inst=0 摄像头；op=read）与 **`fs`**（op∈{list,read,write,delete}）。**fs 的难点 = 路径语义**：现有 inst 是 ≤31 的位图索引，不天然适配路径。A) **manifest caps 加 `fs` 专属字段**：`"fs_paths": ["/SD:/apps/…"]` 路径前缀白名单（数组），运行时前缀匹配 fail-closed——class 位图只管 op 级开关，路径授权走新字段；B) 目录树定长编号（inst=目录槽位，注册期映射）——免文法扩展但目录数 ≤32 硬限且语义晦涩；C) fs 全有或全无（class 一个位）——简单但权限粒度违背合同 10 精神。**建议 A**（文法清晰可校验；manifest 校验器/agent 侧同步）。
- **⑥ 同步面清单**（批准后随实现批）：agent `NATIVE_WHITELIST`/manifest 校验/`ts_perm_check` class 表/L5 常量出处检查同步；内存预算（视频池 PSRAM 256KB 档 + natives 缓冲）入 HLD §4.6 板级表；分片通道 kind 入 DEC-42 注册表；**发送纪律落点**：帧发送属 APP 侧逻辑还是宿主服务（av stream 线程）——**建议宿主侧 V1 不提供常驻流服务**，APP 经 ts_av_capture 取帧后自行分片 publish（publish 面本身已有 ts-net 通道，natives 需补 `ts_net_publish`〔读类、有速率限制〕——此为 natives 面新增第 7 函数，一并入本 Q 裁定范围）。

**建议**：①A + ②{1KB/4ms/重试≤5×20ms/JPEG 优先} + ③A + ④A + ⑤A + ⑥如上（含 ts_net_publish 新 native）。

**调研补充（2026-10-06 · owner 指令"zenoh-pico 限制查官方数据重新评估"；全部可复核）**：
- **版本面**：1.10.1（2025-09-07）为 **zenoh-pico 最新 release**——本项目已钉最新（DR-22），"升级解决碎片问题"路径不存在。1.10.0/1.10.1 changelog 自含碎片/批处理修复（#1305/#1306 fragment header reliability、#1166 batching segfault）——该区域上游活跃修复中。
- **官方配置语义**（zenoh-pico readthedocs config 页 + 仓库 CMakeLists.txt:307-308）：`Z_BATCH_UNICAST_SIZE`（默认 2048）官方描述 = "Any packet bigger than this **will be fragmented if possible**"——>2KB 走碎片是**设计行为**非缺陷；`Z_FRAG_MAX_SIZE`（默认 4096）= **接收侧**去碎片缓冲（"Any packet bigger than this cannot be received"）——即板端将来**收**大消息同样受 4096 默认上限（对称约束）；`Z_FEATURE_BATCH_TX_MUTEX`（默认 OFF）官方自述"提吞吐但风险 = 阻断 keepalive 致断连"——不采纳。
- **官方覆盖途径核实**：尺寸 token 的官方变更途径 = zenoh-pico 自身 CMake cache 变量（`-DBATCH_UNICAST_SIZE=…`）经 config.h.in 生成；**Zephyr 模块集成路径（zephyr/CMakeLists.txt）不做 config.h 再生成、无尺寸覆盖钩子**（本地源码核实——Zephyr 构建用 checked-in 快照 config.h，只映射 Z_FEATURE_* 开关）。抬批尺寸在 Zephyr 上无官方途径（需上游改进集成或本地补丁——后者违反零补丁纪律）。
- **上游已知议题（GitHub issues）**：**#1200（开放中，2026-04）**——payload 超批尺寸且 Z_FEATURE_FRAGMENTATION=0 时 z_put **静默返回 Z_OK**（上游已知批尺寸交互面缺陷——本项目实测为碎片开启下的 -100 失败，同问题族）；**#1129（2026-01）**——大传输中 socket 被关（与本项目 ENOTCONN 后续失败模式吻合）；#979（已关，19 评论）——碎片路径跨版本回归史；#295/#291——碎片数据重拷/大样本接收失败（历史）。
- **重新评估结论**：子项②建议值**不变且加强**——"chunk ≤1KB" 从"实测如此"升级为"实测 + 官方设计语义 + 上游已知议题"三重印证（≤1KB 使消息永不进碎片路径 = 始终运行在最稳路径；2KB 批/4KB 重组上限是官方为受限设备设计的默认约束）；PC 侧 router（Rust zenohd）rx 上限非瓶颈（本仓 router 配置实证 rx_buffer 65535/max_message_size 1GB）。**新增可选子项供裁**：是否就"Zephyr 集成缺尺寸覆盖钩子"提上游 issue（非 V1 阻塞——1KB chunk + JPEG 帧已满足 D-AV 需求；仅作上游回馈记录）。

**影响**：ts_perm_v1 文法（caps 结构加 fs_paths 字段——manifest/校验器/固件三方同步）；公共 API 面 +4~5 natives（ts_fs×4 / ts_av_capture / ts_net_publish）；DEC-42 kind 注册表 +av 类；固件 appmgr natives 接线 + 视频池板级配置；agent 工具链白名单/manifest 同步；D-AV/D-SD demo 解锁（MD1.2 实现批）；内存预算表更新。**全部为 V1 新增面，不动既有安全合同语义**（natives 全走 perm fail-closed 既有机制）。

---

- 2026-10-06 · **MD1.2d 呈递批交付（owner 指令"按照计划继续开发"）：avbench 传输 spike 真机 PASS + Q-27 呈递停门（六子项：传输通道形态/分片参数与帧格式/ts-av 面/ts-fs 面/ts_perm_v1 文法/同步面）**：① **载体**：`firmware/tests/avbench/`（AV* 行；WiFi→zenoh-pico 直连隔离测量→OV2640 捕获 4 帧持有→分片矩阵 {512,1K,2K,4K}×4 帧发布→PC 侧 av_recv.py 重组校验）；判据 = 支持档（≤1KB）零错误 + PC 4/4 帧完整（512B 87KB/s / 1KB 172KB/s 双档达成）；2048/4096 登记预期不支持。② **四项设计事实**（docs/av-transport-01.md）：**>2KB 碎片路径系统性失败**（Z_BATCH_UNICAST_SIZE=2048 静态生成头不可覆盖——chunk 上限钉 1KB）；**发送打拍 ≥4ms 必须**（背靠背任意尺寸崩，z_put -100 errno=0 未达系统调用）；**BLOCK 不保数据**（WiFi 降级时段实测——分片级应用层重试必须，≤5×20ms 实测可恢复）；**视频池 256KB 入 PSRAM + DVP DMA 共存**（SMH 属性 2；DEC-27 分层纪律内）+ WiFi+zenoh+视频池三合一 DRAM 共存（系统堆 188416 档）。③ **过程根因链**（教训入 dev-environment 候选）：sense 板四段名 conf 片段首版三段未生效→PSRAM 未使能→SMH choice 回调 NULL→PC=0 崩溃（寄存器实锤）；zenohd 绑 0.0.0.0；AP DHCP 快复位 ~50% 不应答（三轮重连根治）；cmake 字符串→C 宏须 target_compile_definitions 显式接线（裸值传入由 CMake 加引号——deploybench ROUTER 双层引号从未在 C 表达式用过故未现形）。④ **Q-27 呈递停门**（本节上方）：MD1.2d 全部设计决策六子项呈 owner 裁决——批准后 MD1.2 实现批（natives/权限类/分片通道 + D-AV/D-SD demo）。回归：repo pytest 2 / L5 6/6 / agent pytest 69+2s / ruff 全绿（avbench 为真机载体，无 twister 面）。

---

- 2026-10-06 · **裁决：Q-27 → DEC-47（方案 = 全部建议值；附带上游 issue 处置）**：owner 原文："暂时不提issue，按照你的推荐方案进行规划"。裁定内容：① 传输通道 = **A 专用帧分片通道**（`…/av/<stream>/frame` publish 分片；遥测 128B 上限不动；kind 入 DEC-42 注册表）；② 分片参数 = **1KB chunk + ≥4ms 打拍 + 分片级重试 ≤5×20ms + JPEG 优先**（V1 双格式可配；实测+官方语义+上游议题三重印证）；③ ts-av = **A 最小面 `ts_av_capture`**（阻塞取一帧到 APP 缓冲）；④ ts-fs = **A 四函数无句柄面**（ts_fs_list/read/write/delete；写走审计）；⑤ ts_perm_v1 = **A 新类 av/fs + `fs_paths` 前缀白名单字段**（manifest/校验器/固件三方同步）；⑥ 同步面 = NATIVE_WHITELIST/manifest 校验/L5 常量出处/kind 注册表/内存表 + **新增 native `ts_net_publish`**（读类 + 速率限制）。**上游 issue（Zephyr 集成缺尺寸覆盖钩子）暂不提**（登记观察项——非 V1 阻塞）。**排期指令**：impl-review-02 处置按推荐序（看门狗接线批〔设计决策走门①呈递〕→ PC 读面加固批〔纯工程〕→ 验签实装批〔门③〕→ 小项打包）与 MD1.2 实现批（DEC-47 落地）按 project-plan v1.25 排期表推进。

- 2026-10-06 · **计划修订批交付（DEC-47 后首单元）：MD1.2 实现批与审查债批次排期落盘（project-plan v1.25）**：① **MD1.2 实现批切分**（每会话一单元）：MD1.2e（ts-fs 能力面：四 natives + fs 类 + fs_paths + agent 同步 + 用例）→ MD1.2f（D-SD demo 真机）→ MD1.2g（ts-av + ts_net_publish 能力面）→ MD1.2h（D-AV demo：JPEG + PC 重组消费端）；MD1.2c（PDM）排后。② **审查债批次**：看门狗呈递批（Q-28：三源注册喂狗点/启动序修复/真机 task WDT 与 system_fail 复位闭环/APP 执行边界选型——门①）→ 看门狗实施批（estop 复查平移 IR2-05 + actor 透传 IR2-08 并入）→ PC 读面加固批（L5 正则 IR2-04 并入）→ 验签呈递批（Q-29：TSAP 头摘要 + ed25519 真验签 + 生产 prov 烧录通道同批——门③）→ 验签实施批。③ **观察项新增**：zenoh-pico Zephyr 集成尺寸钩子上游 issue（暂不提，DEC-47）。④ 后续候选保持：MD2 混合 demo（D8/D9）、输入面 G3 批（D4/D6 依赖）、Zephyr 升级 + P4（门⑤）、板级余项。

#### Q-28 · 看门狗接线批（IR2-01 根治方案；门 ①——安全合同 4 落地设计 + 一组默认值）

**背景**：impl-review-02 IR2-01（高）：看门狗合同整体空转——①`ts_wdt_register/feed` 生产零调用（三源枚举定义后从未接线）；②`wdt_start`（boot 步骤 3）后拒绝注册与 APP 装载（步骤 8）顺序冲突（wdt.c:33 `started` 检查）；③全库无硬件看门狗使能——`system_fail` 后 `k_sleep(K_FOREVER)` 所依托的"硬 WDT 兜底复位"不存在（force.c:56 注释自述），真机 fail-safe 后永久挂死；④APP 无执行边界——`app_init`/`app_tick` 死循环不可检测（健康探针同线程）。合同 4 要求"每子系统独立喂狗（可定位卡死来源）"，当前为静默失效（CI 不可见）。本 Q 呈四层防线方案与全部新增默认值。

**方案（四层防线，各子项附选项与建议）**：

- **① ts_wdt 注册窗口修复**：A) **静态预注册 + 动态激活**（建议）——`ts_wdt_start` 时按 Kconfig 周期预注册三源（注册表不可变，并发语义零新增）；增"激活"语义（registered 且未激活的源不参与逾期判定，子系统首次 `ts_wdt_feed` 即激活）——boot 步骤 3 启动巡检不被后续装载顺序阻塞，步骤 8 后 APP 线程首次喂狗激活 APPMGR 源。B) 放开注册（锁保护 + patrol 周期动态重算）——灵活但引入并发面与周期抖动。**建议 A**。
- **② 喂狗点接线（三源）**：SYWORK = patrol_work_cb 顶部（巡检自身运行即 sysworkq 活性证明，wdt.c:82）；NET = net_wq 驱动循环每轮（init.c:27）；APPMGR = runtime 主循环每轮（runtime.c:139，≤20ms mailbox 轮询上界）。**周期建议**（Kconfig 新默认）：SYWORK 1000ms / NET 2000ms（容忍 10×200ms 轮询周期）/ APPMGR 1000ms（容忍 10×100ms tick 周期）——巡检周期自动 = min/2 = 500ms。
- **③ APP 执行边界（核心选型）**：A) **WAMR 指令配额**（建议）——启用上游 cmake 开关 `WAMR_BUILD_INSTRUCTION_METERING=1`（config_common.cmake:676，**零补丁**；fast 解释器原生支持，超限抛 "instruction limit exceeded"〔wasm_interp_fast.c:95〕）+ 每次 `wasm_runtime_call_wasm` 前 `wasm_runtime_set_instruction_count_limit`；超限 → 调用返回 false → **既有** health_fails→3 连→回滚路径（不 abort、无 IR2-06 死锁面）。**预算建议**（Kconfig 新默认，按板级二 1043ns/iter 吞吐量级推算）：app_init 1,000,000（≈100-200ms 上界）/ app_tick 200,000（≈20-40ms）/ app_evt 200,000——真机基准批校准后可调。B) 仅软看门狗（APP 卡死→全系统 fail-safe→复位）——实现最简但坏 APP 复位整个立方体，违背"APP 级故障不阻塞系统"（HLD §4.4-8）既定例外精神。C) 独立看护线程 + abort——须先修 abort 持锁安全（IR2-06），复杂度最高。**建议 A，且 ②的 APPMGR 喂狗点保留为 wasm 外卡死（native 调用/mailbox 段）的分层防线**。
- **④ 硬件看门狗使能与复位闭环（真机）**：`CONFIG_TASK_WDT=y` + `TASK_WDT_HW_FALLBACK=y`（esp32 MWDT；`WDT_ESP32` 树内默认 y）+ ts_wdt 巡检注册一个 task_wdt 通道（软巡检卡死 → task_wdt 回调 → system_fail）→ **system_fail 内 noinit 故障留痕强实现**（force.c:11 弱桩接 store/noinit.c——IR2-R6 同批根治，复位后可归因）→ 停机停喂 → 硬 WDT 复位。**超时建议**：`TASK_WDT_MIN_TIMEOUT=5000` + `TASK_WDT_HW_FALLBACK_DELAY=5000` → 硬 WDT ≈10s（与既有常量 `TS_HARD_WDT_CAP_MS=10000`〔DEC-22/27 出处〕对齐）。native_sim 无 hw WDT：task_wdt 无回退仅软层（CI 语义），真机 = 全层——两平台语义差在文档如实登记。
- **⑤ 回归面**：twister framework.wdt 扩用例（激活语义/喂狗/逾期→WDT_WARN→system_fail 路径）；真机 wdtbench 新载体（故意死循环 APP → 指令配额终止 + 回滚实证；人为停喂 NET 源 → WARN→system_fail→**硬复位观测**〔复位后 noinit 读出归因〕）；estop 并发回归不退化。
- **⑥ 并入小项（排期已定）**：IR2-05（channel.c set_link/recover 补 commit.c 同款 irq_lock+forced 复查范式平移）+ IR2-08（commit actor 透传：net 面 src / APP 面 app_id）。

**建议**：①A + ②{1000/2000/1000ms} + ③A{1M/200k/200k} + ④{TASK_WDT+回退，5s+5s，noinit 强实现} + ⑤⑥如上。

**影响**：wdt.c（激活语义）/ runtime.c（喂狗 + 配额调用）/ init.c（NET 喂狗）/ force.c（noinit 强实现）/ 模块 WAMR 构建块 +1 上游开关（无补丁）/ 板级 conf（TASK_WDT 族）/ Kconfig 新默认 ~6 项（全部本 Q 裁定）；boot 步骤表不变；estop ISR 无锁直达不动（合同 5）；twister 全量回归 + 真机 wdtbench。**合同语义不变（落地既有合同 4，无削弱）**。

---

- 2026-10-06 · **裁决：Q-28 → DEC-48（全部按建议值）**：owner 原文："继续"（Q-28 呈递后首回复，按项目惯例 = 按建议执行）。裁定：①静态预注册+动态激活 ②喂狗周期 SYWORK/NET/APPMGR=1000/2000/1000ms ③**A WAMR 指令配额**（init 1,000,000 / tick·evt·health 200,000）④task_wdt 通道（callback=NULL→自动 sys_reboot；TASK_WDT_MIN_TIMEOUT=5000+FALLBACK_DELAY=5000；noinit 强实现）⑤⑥如呈递。

- 2026-10-06 · **看门狗实施批交付（DEC-48 落地，排期表单元 2）：四层防线全接线 + 真机 wdtbench 三整循环自证（WB PASS + 复位闭环）+ twister 15/15（65 用例）/L5/pytest 全绿**：① **L1**：wdt.c 静态预注册三源 + 动态激活（首次 feed 激活，未激活不判逾期——core 测试扩断言）；喂狗点接线 = SYWORK（巡检 cb 顶部）/ NET（net_wq 每轮）/ APPMGR（APP 线程入口+主循环每轮）——**生产零喂狗自此清零**（IR2-01 主账）。② **L2**：WAMR `WAMR_BUILD_INSTRUCTION_METERING=1`（上游开关零补丁）+ 每次调用前 `wasm_runtime_set_instruction_count_limit`；超限抛 "instruction limit exceeded" 走既有健康失败→回滚（无 abort 无死锁面）。③ **L3**：TS_CORE `select TASK_WDT`；巡检注册 task_wdt 通道（5s，callback=NULL→过期自动 sys_reboot）+ `TASK_WDT_HW_FALLBACK`（板级 chosen zephyr,watchdog→esp32s3 wdt0；kernel 死透时 MWDT ≈10s 兜底）。④ **L4**：`ts_store_noinit_record` 强实现（store/noinit.c 覆盖 force.c 弱桩——system_fail 复位原因入 noinit）；wdt_start 启动时读出上次留痕 printk 归因；system_fail 停机后通道无人喂 → sys_reboot 复位闭环（k_sleep 不停 k_timer）。⑤ **并入小项**：IR2-05（set_link/channel_recover 补 irq_lock+forced 复查——commit.c IR-02 范式平移，estop 抢入后通道保持 SAFE_FAULT）；IR2-08（`ts_safety_commit_a(uid,v,actor)` 新公共 API + audit actor 归因；ts-hal gpio/pwm 传 `c.app_id`，power/system 路径 actor=0；net 命令面现无直接 commit 落点——如实登记）。⑥ **真机验证**（wdtbench 新载体，Sense 板，WB* 行）：装载数学死循环 APP（tick `for(;;)` 夹具）→ state=3 ACTIVE → **指令配额 ~1s 内终止 → state=4 回滚 rb=1 → 系统存活（WB PASS）** → 阶段 C sysworkq 协作级自旋 → **task_wdt 通道 5s 复位（WB0 重现铁证）**——75s 内三整循环自证；task_wdt 直通复位路径无 noinit 留痕（ISR 上下文不可写 flash）——限制如实在档。⑦ 过程修正（如实）：wasm 夹具首版缺 `export_name` 属性（链接器默认不导出→boot E_PARAM）；WATCHDOG 才是 Zephyr WDT 子系统根符号（CONFIG_WDT 不存在）；判据窗口修正（配额终止 ~600ms 快于 200ms 轮询——ACTIVE 瞬态可错过，以回滚终态为判别器：配额失效则 tick 永挂永不回滚）。回归：twister **15/15（65 用例）**/L5 6/6/repo pytest 2/agent pytest 69+2s/ruff/密钥 grep 双零。

- 2026-10-06 · **PC 读面加固批交付（排期表单元 3，纯工程无 Q）：IR2-03 根治 + IR2-04/09/10/11 并入——agent pytest 74+2s（+5 用例）/ruff/L5 6/6 全绿**：① **预处理读面封死**（wasm_build.py）：`_gate_source` 拒绝一切 `#include` 与 `__has_include`（自由固件零依赖约定——natives 经 extern 声明；#include 探读主机任意文件 + clang 诊断回显源文本 → stderr 回喂 LLM 的外泄链根除；放宽须走门 ③）。② **读入路径白名单**（tools.py `_read_within`）：tsap_package 的 wasm_path 与 tsap_verify 的 package_path（roots 提供时）必须落 allowed_roots——堵"读任意主机文件打包外送"；**密钥/公钥路径豁免**（仓外密钥纪律〔私钥内容永不出进程；公钥公开材料〕——不对称如实在档）；gateway tsap_verify 与 app_chain 两处验签传入 ctx.roots()。③ **max_bytes 服务端钳制**：`min(max_bytes, DEFAULT_MAX_BYTES=16384)`——调用方（含 LLM）传大值不可放宽。④ **zenoh key 注入防御**（keys.py `_validate_seg`）：node/cube/cmd/uid 段白名单 `[A-Za-z0-9._-]{1,48}`（禁 `/ * # $` 空白）。⑤ **进程纪律**：_run_clang 改 Popen+start_new_session+超时杀整进程组（IR2-09 孙进程不遗留）；proc.py 补 CancelledError 路径杀进程组（task_cancel/TTL 不再留孤儿 west/clang）。⑥ **并发隔离**（IR2-10）：compile_app_c 按真实 out_dir 路径互斥锁（固定文件名交叉污染双编译一致性检查的面消除）。⑦ **L5 正则补口**（IR2-04）：OUTPUT_DRIVER_RE 增裸 `pwm_set(`/`pwm_set_dt(` 变体（本库 PWM 落驱动即裸形态——原正则机械防线缺口；driver_dispatch.c 白名单不变，负样本验证无误报）。测试：+5（include 三门 + 钳制 + 读面白名单往返）+ tsap 读面用例；密钥 grep 双零。

- 2026-10-07 · **MD1.2e 交付（排期表单元 4，DEC-47④⑤ 落地）：ts-fs 能力面——四 natives + fs 权限类 + fs_paths 前缀白名单三方同步 + twister 15/15（66 用例，+1）/agent pytest 74+2s/L5 全绿**：① **固件**：`src/hal/fs.c`（无句柄四函数 list/read/write/delete，Zephyr fs API 后端——部分写=失败、无 O_APPEND）；**双层裁决 fail-closed**：class/op 位图（`fs:list/read/write/delete:0`，inst 占位）+ `ts_fs_paths_bind` 前缀白名单（manifest `fs_paths` 数组→';' CSV 随装载绑定；**前缀边界 = 前缀后须 '/' 或恰好等长——防 "/SD:/apps" 授权 "/SD:/apps-secret" 绕过**；未绑定=全拒）；越权经既有 TS_EVT_PERM_DENIED 留痕；写/删 printk 归因留痕（安全审计环属输出通道面——fs 写入环扩展登记待办，随真实消费需求再裁）。② **natives**：ts_fs_read/write/list/delete 四导入（wasm 指针 validate_app_addr + 内嵌 NUL 拒绝；`CONFIG_TS_HAL_FS` 门控注册与编译——未使能构建拒收含 fs_paths 的 manifest〔fail-closed〕）。③ **manifest 三方同步**：agent `TsapManifest.fs_paths` 可选字段（绝对路径/禁 ../去重排序校验；缺省=无授权不携带键）；CBOR 往返含 from_cbor；slot.c 走查新增 fs_paths 键（非绝对/含 .. 拒绝装载）；`NATIVE_WHITELIST` +4。④ **用例**：framework.app 新 test_05_fs_gates（类解析/未知 op 拒/未绑定拒/前缀边界三态/授权→后端 IO〔native_sim 无挂载如实〕/op 位图缺项拒）。⑤ Kconfig：`TS_HAL_FS`（默认 n，select FILE_SYSTEM）+ `TS_HAL_FS_PATHS_MAX=256`。真机面（挂载 FAT 上读写）随 MD1.2f（D-SD demo）验证。

- 2026-10-07 · **MD1.2f 交付（排期表单元 5）：D-SD demo 真机全链 PASS——真 LLM 生成 ts-fs APP → Sense 板 SD 实机五步状态机（写 68B/读回校验一致/白名单外拒绝/列目录/完成标记）+ 宿主独立复核双证据；twister 15/15（66 用例）/agent 74+2s/L5 全绿**：① **生成链**（真 LLM MiniMax-M3）：D-SD spec → app_develop 全链（manifest 含 fs_paths + fs caps；包 5586B）；提示词补 fs natives 四签名与 fs_paths 文法（app_chain 系统提示）；传输伪影解包字段扩 fs_paths（同 {"item"} 包装）；manifest 校验器路径正则补冒号（Zephyr 磁盘挂载点 /SD: 形态）。② **载体**：dsdbench（DS* 行；sense 板；SD 挂载 + 目录预备 + 安装 + boot 装载 + 宿主复核线程）：DS PASS 判据含**独立证据**——宿主侧读 dsd.txt 逐字节验证（n=68 = DSD-+64 数字）+ deny 文件物理不存在（/SD:/etc/dsd-deny.txt 未被创建 = 白名单拒绝的物理证据，非仅 APP 自报）。③ **真机首验抓出真缺陷并根治**：fs_paths 绑定双形态不一致——boot 链走 ts_fs_paths_bind(1,…) 置 ctx_bound=false 后无人置 true → 一切路径拒绝（wr-rc=-3）；修复 = 去 ctx_bound 标志、纯 app_id 匹配（0xFFFF=未绑定）。**教训**：sim 用例（test_05_fs_gates）走 bind_ctx 形态恰好绕过 boot 链形态= 测试形态与装载链形态不一致的盲区；真机首验价值实证。④ 过程修正（如实）：dsdbench 首版误用非 sense 板名（FF_VOLUMES=0 编译错）；漏 CONFIG_WATCHDOG=y（chosen 设备符号缺失）；LLM 首轮 strstr 引 #include 撞读面门（spec 明示手写循环后过）。⑤ 产物入仓：agent/demos/D-SD/（spec/app.c/app.wasm/manifest.json/*.tsap/md1.pub——私钥仓外）；仓外工具 dsd_gen.py/run_dsd_gen.sh/gen_dsd_pkg.sh/dsdb_build.sh/dsdb_flash.sh。

- 2026-10-07 · **CI 事故处置（62bd757/e89c578 agent-checks 两连挂；已根治 be320cd 四 job 绿）**：根因 = MD1.2f 提交的 git add 按路径圈定，漏两类文件——① sync_check --update 刚改写的 SOURCES.lock（同型失误第二次〔4fd4e3a 首次〕）；② fs 面两源文件（app_chain.py 提示词/fs_paths 解包、manifest.py 冒号正则——D-SD 产物生成所依赖的工作树版本未入库）。**可观测性副产**：agent-checks 补 pytest 失败摘要进注解（-vv 全展开 + FAILED/E 行 ::error::——ffd50be native-build 同理）；本地三口径（venv/根目录/全新克隆）不可复现，靠全新克隆 + editable 安装的完整 CI 序列复现方定位。**教训（军规 5 强化）**：涉及锁同步的提交一律 git add -A 或显式含 agent/skills/SOURCES.lock；圈定路径的 git add 在多目录改动批次禁用。

- 2026-10-07 · **owner 指令登记（范围 + 节奏，随全库复检交付）**：① **硬件阶段三（立方体结构/连接器/电源）排除出开发范围**——板级固件面（S3 余项/P4 适配）保留；② 剩余全量单元重构为 **project-plan v1.30 §7 排期表（A…J）**，按规划连续开发；③ **每交付单元后汇报总进度与阶段进度**。**同日复检结论落点**：IR2-06/IR2-07 在 v1.25 排期表无落点（流程遗漏）→ IR2-07 并入单元 D、IR2-06 并入单元 F；fs_paths 条目长度 agent≤64 vs 固件≤63（fail-closed 边缘不一致）→ 单元 A 对齐；ts_fs 三语义边缘（EOF 间隙/列表尾分隔符/无 stop 解绑）→ impl-review-02 §8 附记登记不动手；本地全量回归脚本补 WAMR 预生成+chmod 444 预处理（仓外工具，防 version.cmake 并行竞态误报——本轮 14/15 errored 即此因，单套件复跑 1/1 绿 + CI 同提交绿双证据排除代码回归）。

- 2026-10-07 · **MD1.2g 交付（排期表单元 A，DEC-47③⑥落地）：ts-av + ts_net_publish 能力面——采集/发布读类双 native + avq 分片通道 + av 权限类 + manifest av_* 三方同步；twister 15/15（68 用例，+2）/agent 76+2s/L5 6/6/ruff 全绿**：① **固件**：`src/hal/av.c`（ts_av_capture 阻塞取一帧〔chosen zephyr,camera 官方池路径；无 chosen 板 TS_E_IO 如实；超时 400ms < APPMGR 喂狗 1000ms——采集停顿先失败不升级看门狗〕+ ts_av_publish 权限面；配置绑定 = manifest av_fmt/av_w/av_h 随载 ts_av_config_bind——未声明 TS_E_STATE fail-closed）；`src/net/avq.c`（APP 线程入队 + net_wq 单线程冲刷 = zenoh-pico 非线程安全面的并发规避；信封 CBOR {fid,cid,n,crc32,d}；打拍 4ms/重试 ≤5×20ms/chunk≤1KB 全部 DEC-47② 值经 Kconfig；满队 TS_E_BUSY 背压 + DOWN 期自弃计数；重试耗尽止冲刷限本 tick 时长）；cbor_min 增 put_bstr；keyspace 增 ts_net_key_av（…/av/\<id\>/frame，stream = 数值 app_id——避免字符串段注入面）；net_tick 接 avq_flush。② **natives**：ts_av_capture "(iii)i" / ts_net_publish "(iiiiii)i"（validate_app_addr 纪律；TS_HAL_AV 门控注册）。③ **agent 同步**：manifest.py av_fmt/av_w/av_h（互为充要 model_validator + 16..800 值域）+ **fs_paths 总长 ≤255B 前置校验**；NATIVE_WHITELIST +2；app_chain 提示词（双 native 签名 + 打拍语义说明：宿主打拍、BUSY 重发）。④ **用例**：framework.app test_06_av_gates（类文法/未配置拒/配置域/无摄像头后端 IO/发布参数门/越权拒）+ framework.net test_12_avq（key/信封逐字段解码/队满背压/DOWN 自弃/重试成功路径）。⑤ **并入（复检发现②）**：fs_paths 长度对齐——固件走查 pfx[64]→[68]（agent 校验器上限 64 条目今可装载）+ agent 总长前置校验。⑥ 文档：LLD-ts-hal v0.2.3（fs 补记 + av 面）/LLD-ts-net v0.3.8（key_av + avq）/LLD-ts-appmgr v0.5.3（manifest av_* 键）/HLD §4.6 av 面增补（视频池 256KB@PSRAM + avq 4KB@DRAM）。⑦ 工具加固（复检发现④）：本地全量回归脚本固化 WAMR version.h chmod 444 预处理——本轮并行全量 15/15 无竞态实证。真机面（真摄像头 JPEG 采集 + PC 帧重组消费）随 MD1.2h（D-AV demo）。

- 2026-10-07 · **MD1.2h 部分交付（排期表单元 B，如实）：D-AV demo 链路 90% 打通——真 LLM 一轮生成 PASS（demo.d.av，rgb565，包 7046B）+ avdemo 载体入库（WiFi/zenoh/flash 五分区/视频池 PSRAM/看门狗）+ 真机实证至第 5 分片发布；**DA PASS 判据被 DAV1 缺陷阻塞（专项批 B2）**。① **真机已证**：安装/装载/ACTIVE 全链 ✓；ts_av_capture 真帧捕获 ✓（avdiag：cap r=0 len=38400）；ts_net_publish 分片入队与 avq 冲刷 ✓（pub c=0..4 r=0；帧分片经 zenoh 到达 PC 前线程冻结）。② **DAV1（缺陷登记）**：av 流发布压力下 APP 线程无声冻结——3/3 复现，冻结点 = 第 3-5 次分片发布后，无异常转储；看门狗安全链按设计工作（APPMGR 逾期 → system_fail → noinit 留痕 0x00020001 → task_wdt 复位——合同 4/6 真机实证）。伴随线索：zenoh open 期 `k_thread_stack_free` 报 "tid is in use!"（dynamic.c:126——zenoh-pico MULTI_THREAD pthread 栈释放竞态嫌疑）+ DVP ISR 上下文 WRN 并发。**嫌疑集**：zenoh 会话 pthread 动态栈竞态 / net_wq 冲刷与 zenoh 后台任务交互 / ISR 上下文日志并发。**B2 专项批**：addr2line + 控制变量二分（avq 深度 1/禁冲刷直推/独立会话对照 avbench）。③ **DAV2（上游缺口登记）**：Zephyr v4.4 esp32 DVP 驱动不支持 JPEG 变长帧——`video_esp32_enqueue` 按定长 `bytesused = pitch×height` 尺寸 DMA，而 JPEG 官方语义 pitch=0（video_common.c:536）→ 零长 DMA 永无帧；完成回调亦不回填实际字节数。demo 按 DEC-47② 已裁保底路径用 RGB565（38 分片/帧）；JPEG 恢复依赖上游驱动改进（随 Zephyr 升级评估〔单元 J〕重估）。④ **载体**：firmware/tests/avdemo/（prov blob 机械生成走查验证——gen_dav_prov.py；DRAM 档 122880 实证：188416+32KB slot 溢出 60KB → 131072+16KB 溢 3KB → 122880 过）；PC 消费端 dav_recv.py（仓外——CBOR 信封解码/重组/crc32/RGB565 非死帧判据）。产物 agent/demos/D-AV/ 入仓（dav.pub 提交、私钥仓外）。回归：twister 15/15（68）/L5/pytest/ruff 全绿（临时诊断 printk 已移除）。

#### Q-29 · IR2-02 根治：固件 ed25519 真验签 + TSAP 头摘要字段（文件格式 v2）+ 生产 prov 烧录通道（门 ③——文件格式/公共 API/信任模型变更；排期表单元 C）

**背景**：impl-review-02 IR2-02（高，双面）：① 生产语义——固件 COSE 验签为结构桩（pkg.c 两字节结构检查），生产构建**恒拒一切安装** = 部署面不可用；② TEST 语义——放行任意未签名 wasm + 自声明 caps，**迄今全部真机验证（D1-D7/D-SD/D-AV）均 TEST 语义**。同族缺口：activate 整槽 hash 无对拍对象、boot 装载不验签、根公钥经 TS_TEST 写入（无生产烧录通道）。Agent 侧已有真 ed25519（tsap_verify：pycose + DIY 四象限互验）——**签名链只有一半是真的**。

**选项**（四子项，各附建议）：

- **① 固件验签实现**：A) mbedtls/PSA ed25519——钉版树核查：**tf-psa-crypto core 无 ed25519 软实现痕迹**（grep 零命中；实施首步再深查 PSA 配置面，若可启用则优先——零新增代码）；B) **内置极简 C ed25519 verify**（~600 行公版参考实现移植〔Apache-2.0/MIT 许可〕，纯软件确定性，与 Agent 侧 DIY 实现对拍互验〔双实现纪律同 COSE〕；零上游依赖零补丁）；C) 仅头内 sha256 摘要（无不对称验签——只防误损不防伪造，**不满足 IR2-02，排除**）。**建议 B**（A 作实施首查项：PSA 若可开启则改用 A）。
- **② TSAP 头摘要字段（文件格式变更）**：A) **fmt_ver=2：16B 头后追加 32B sha256(manifest‖wasm)**（rsv u16 → flags=1；Agent tsap_package/verify 同批双向同步）；B) 头不动，装载后由固件自算 hash 存 meta（activate 对拍用）——格式零变更但对拍依赖运行时状态、离线工具不可校验；C) TSAP v2 全新容器布局（破坏面大）。**建议 A**：格式一次到位、PC/固件/离线三方可独立校验；**v1 包 v2 固件 fail-closed 拒收**（仓内 demo 同批重打包——机械脚本重产，无手工迁移）。
- **③ 生产 prov 烧录通道（根公钥落 ts-prov 分区）**：A) **esptool 直写脚本**（gen_prov.py 机械生成含真 pk0 的 prov blob + 分区直写 + 上板走查验证——制造期纪律，不进运行时 API 面）；B) Agent push_prov 工具（需维护模式语义〔LLD-A06 §6 遗留登记〕——运行时面大）；C) bootloader 期校验（超 V1）。**建议 A**（B 登记后续候选）。
- **④ TEST 语义收口**：A) **TEST 构建改真验签 + 固定测试根密钥**（demo/测试链继续可用——包须以测试根签名；根除"完全未签名 + caps 自声明"形态）；B) 维持现状（TEST 放行任意包——双语义面永续）。**建议 A**（安全语义统一，代价 = 测试包多一步签名，demos 链已有密钥）。

**默认值三问**（sha256）：从哪来 = TSAP/COSE 生态惯例 + 树内既有（zenoh TLS/mbedtls）；越界 = 无（摘要长度非安全参数）；改动 = v2 格式兼容面（v1 拒收 = fail-closed 设计点）。

**建议**：①B（A 首查）+ ②A（fmt_ver=2 + 32B sha256）+ ③A（esptool 直写）+ ④A（TEST 真验签 + 测试根）。

**影响**：TSAP 文件格式 v1→v2（门 ③ 本呈递）；固件 appmgr（pkg.c 真验签 + slot.c v2 走查 + activate hash 对拍）；Agent tsap 工具（package/verify v2 同步 + v1 只读兼容期）；仓内 demo 全部重打包（D-SD/D-AV/测试夹具机械重产）；**IR2-02 消账 + 生产部署链语义首次点亮 + 板级十一"生产 prov 通道"同批消账**；实施批 = 排期表单元 D（并入 IR2-07 回滚闭环）。批准后执行 D；有例外项请明示。

- 2026-10-07 · **裁决：Q-29 → DEC-49（四子项全部按建议值）**：owner 原文："按照计划继续执行"（Q-29 呈递后首回复，按项目惯例 = 按建议执行）。裁定：①固件真验签 = **B 内置极简 C ed25519 verify**（PSA 作实施首查——可启用则改用 A）②TSAP 头摘要 = **fmt_ver=2 + 32B sha256(manifest‖wasm)**（rsv→flags=1；v1 包 fail-closed 拒收，仓内 demo 机械重打包）③生产 prov 通道 = **esptool 直写脚本**（制造期纪律；push_prov 登记后续候选）④TEST 语义 = **真验签 + 固定测试根密钥**。实施批 = 排期表单元 D（并入 IR2-07 回滚闭环：目标槽验证/回滚后重载/meta 双损如实失败）。

- 2026-10-07 · **验签实施批交付（排期表单元 D，DEC-49 落地 + IR2-07 并入）：TSAP v2 + 固件真 ed25519 验签（tweetnacl）+ TEST 语义收口 + 回滚闭环——twister 15/15（70 用例，+2）/agent 76+2s/L5 6/6/ruff 全绿；真机 dsdbench DS PASS 全链复验（xtensa 首跑真验签）**：① **PSA 首查结论**：钉版树 tf-psa-cico/mbedtls-3.6 无 ed25519 软实现痕迹 → 按 DEC-49①B 走内置 tweetnacl（tweetnacl.cr.yp.to 20140427 快照 809 行，Public Domain，逐字节未改，仅 crypto_sign_open 消费；出处 crypto/PROVENANCE.md）。② **TSAP v2**（DEC-49②）：头 16B（rsv→flags，bit0=1）+ 32B sha256(manifest‖wasm) + manifest + wasm + COSE；v1 包 fail-closed 拒收（无兼容装载）；agent tsap_package/verify 双向同步（v1 只读兼容期）；仓内 demo/夹具全部重签（测试根）。③ **验签管线**（appmgr/verify.c）：头 v2 → 摘要重哈希对拍 → COSE_Sign1 逐元素解析（phdr 精确 {1:-8}，DR-21）→ Sig_structure 构造（与 cose.py DIY 字节级对拍）→ tweetnacl 验签 + COSE 内嵌副本与裸段逐块比对（防"签 A 装 B"）；boot 快校验 = 摘要重哈希（毫秒级，全量验签在安装/激活）。④ **TEST 语义**（Q-29④）：TEST 构建验签对象 = 固定测试根（f084a4e5…477a；密钥对仓内 agent/tests/fixtures/ts-test-root.{key,pub}——测试信任 ≠ 生产信任，公开材料）；生产 = prov pk0（cmd.c 既有通道自动生效）。⑤ **IR2-07 回滚闭环**：目标槽先全量验签（空/坏槽 = 如实 E_IO 不翻转）+ 翻转后暖复位装载（生产路径；TEST 构建保留状态机断言）+ meta 双损如实 E_IO（boot 拒绝静默装载 slot 0；install 走显式恢复路径 printk 可观测）+ meta 增 content_digest[32]（boot 快校验对象）。⑥ **调试过程三教训**（真机拦下，均留档）：tweetnacl crypto_sign_open 的 m 出参**不可与 sm 别名**（验证前即以 m[32..64)=pk 作暂存——单 scratch 双区布局修复）；Sig_structure 前缀按 payload 实际长度选 bstr 头（<256 = 0x58 单字节，非恒 0x59）；**net_wq/主栈 4096 被 tweetnacl ~1KB 局部压穿**（dsdbench 真机 EXCCAUSE 28 = 栈溢出现场迟爆——net_wq 4096→8192 + benches 主栈 8192 + 生产 app prj 同步）。⑦ **③A 生产 prov 通道**：agent/tools/flash_prov.py（esptool 直写 + CBOR 键序走查 + cbor2 往返自检）——制造期纪律，push_prov 登记后续候选。⑧ **夹具重产链**：fixture_pkg/boot_pkg（预签 v2，gen_fixture_pkg.py）+ tests/appmgr 篡改矩阵（digest/manifest/wasm/sig/v1 六拒收 + sha256 NIST 向量 + tweetnacl 内建向量）+ tests/net 部署面共享夹具 + wdt_pkg/dsd_pkg/dav_pkg 重签（测试根）。板级 TS_VERIFY_SCRATCH 双区调档（wdt 1024/dsd 6144/avd+deploy 7168）。**IR2-02 消账（最后高风险项）+ 生产部署链语义首次点亮 + 板级十一"生产 prov 通道"消账**。

- 2026-10-07 · **MD1.2c 交付（排期表单元 E）：PDM 音频驱动扩展评估——结论 = 缓办（docs/md12c-pdm-eval.md，零代码改动）**：① 上游面核验：树内 i2s_esp32 零 PDM；Sense 板 DT 无麦克风节点；hal_espressif esp_hal_i2s 组件的 esp32s3 i2s_ll.h **PDM 寄存器层齐全**（rx_pdm_en + 硬件 PDM→PCM 降采样 + TX pcm2pdm）且 include 路径已在构建上（树内驱动消费中）。② 实施路径钉死：模块内最小 PDM RX 驱动（ts-drv-pdm 先例 = TS_DRV_GPIO/PWM；i2s_ll + GDMA + 硬件降采样 → 16bit PCM；~300-500 行，≈1 会话含真机 bring-up；零上游补丁）。③ **缓办依据**：D1-D9 全阶梯无音频 demo（D4/D6=ADC 面，D8=全生命周期，D9=G3+断链）——即刻投入无验证出口；B2/F/G 价值更高；路径留档零沉没成本。④ 重开触发：owner 音频指令 / MD2 含音频 demo / 单元 J 时 P4 音频核验 / 上游 i2s_esp32 加 PDM（升级收割）。重开时音频 API 归属 av 类设计 = 门③呈递。**MD1.2 全部子项自此收口**（a/b/d/e/f/g ✅，h ◐=DAV1 待 B2，c ✅=评估+缓办）。

- 2026-10-08 · **输入面 G3 批交付（排期表单元 F）：input monitor ADC 真值化 + 事件→APP mailbox 路由 + IR2-06 根治 + estop 沿 prov 化 + D4/D6 demo 真机全链——twister 15/15（73 用例，+3）/agent 76+2s/L5/ruff 全绿**：① **G3 路由**（已裁实现债落地）：input.c 重写为 ADC 实例轮询（真后端经 ts_adc_sample_fw 框架侧采样；变化语义 = **传输级**——与上拍不同即发，阈值/滞回语义归 APP 逻辑，框架零新默认值）；TS_EVT_INPUT_CHANGED 载荷 v2 = {inst, old_mv, new_mv}（旧 bool 载荷零消费者）；ts-appmgr 订阅路由进 APP mailbox（payload = inst<<16|mv；sysworkq 上下文 k_msgq_put 线程安全，满丢最旧 DR-14）。② **IR2-06 根治**：app_stop join 超时**不再 k_thread_abort**（持锁点截断 = k_mutex 无 owner-death 回收 → 全输出写路径永久死锁）——改弃管升级：线程留在原地停喂 TS_WDT_APPMGR → 软看门狗逾期 → system_fail（noinit 归因）→ task_wdt 复位闭环（DEC-48 分层）；返回 E_TIMEOUT，资源不回收重启即净。③ **estop 沿 prov 化**（DR-11 收口/M2a 遗留）：estop_trigger_flags 0=上升（兼容）/1=下降/2=双沿/其他 fail-safe 上升+留痕；boot 步骤 1 先于 net_init → estop_init 显式 prov_load（幂等）。④ **DEC-48① 对称面补全（真机拦下）**：ts_wdt_deactivate(src)——APP stop 后 APPMGR 源去激活（停后无人喂 = 预期态不判逾期；否则 stop 后 1000ms 逾期→复位，D6 永不上场——inputdemo 实证）。⑤ **D4/D6 demo 真机全链**（真 LLM 一轮过：demo.d4.adcreport 5506B / demo.d6.hysteresis 6718B，测试根签名）：D4 = ADC 变化上报（**D4-DONE reports=8** + d4 evt inst/mv 真值行）；D6 = 滞回控制环（**d6 clamp rc=-12 限幅实证** + 滞回输出 **rc=0 真实落驱动** + **D6-DONE changes=6**）；真值源 = GPIO2 悬空拾噪（71-91mV 实测带——阈值 20mV/滞回带 82/76 按实测调参，全量程 0/3.3V 轨到轨注入 = owner 物理操作〔板级九 PB6 同型〕）。⑥ **载体**：inputdemo bench（deploybench 通道面 + dsdbench 内嵌安装 + 无 WiFi/zenoh 本地判据；两包顺序跑 D4→stop→D6〔进程内换包 = TEST 放行〕）。**过程三修**（真机拦下）：注册序 = 实例号（ADC 须先注册占 inst 0——caps 域对齐）；watcher 线程栈 4096→8192（D6 install 验签深度 = D 单元同型教训第三次）；无网面 set_link 声明（persistbench 同型——否则输出写恒 E_STATE）。IR2-06 消账（impl-review-02 中风险八项全清）。

- 2026-10-08 · **CI 事故处置（034c810 l5-checks 挂；本地同脚本绿）**：根因 = **L5 执行口径差**——CI 自仓库根跑 ，本地回归脚本自 l5 目录跑，脚本对 driver_dispatch 的禁用符号正则（printk/net_\* 族）在两种 CWD 下扫到同一文件，但**注释文本同样计入**——单元 F 在该文件新增的 printk 调用（estop 边沿 fail-safe 留痕）与注释里的字面 "net_init" 双踩线，本地脚本历史输出被 tail 截断掩盖（脚本早先也报同错——本地"6/6"结论误读，如实更正）。修复：printk 调用与 include 移除（fail-safe 上升静默化——观测面 = framework.safety 用例 + 部署期 prov 校验）+ 注释改写（"net_init"→"网络步骤"）。教训：**本地回归脚本的 L5 步必须与 CI 同口径（自仓库根）**；L5 结论须看完整输出非 tail。

- 2026-10-08 · **G1 交付（板级余项批前半，单元 G 拆分）：注册期 poweron 值落驱动——板级九遗留观察项收口；twister 15/15（74 用例，+1）/agent/L5 全绿；真机寄存器级证据 PASS**：① 实现：（boot 步骤 2）对每通道 poweron 值**直写驱动**（单线程 boot 上下文无锁竞争；与 estop/recover 同纪律不经 commit——合同 1 三态落驱动的 poweron 面）；此前仅置 shadow，物理值依赖"驱动复位缺省 = 声明"的隐含假设，声明≠缺省即静默漂移。② sim 用例：framework.safety test_poweron_writes_driver（注册→init→写序列恰一笔 = 声明值）；附带修复 full_scenario 显式净基线（容量算术对前序注册敏感）。③ 真机（inputdemo 扩展判据）：dbpwm poweron 改 300‰ 特异值 → **ID1a：set_link 前 LEDC 物理 duty = 299‰（want 300，±3‰ 容差 OK）**——寄存器直读（periphbench 同口径）；过程修：inputdemo overlay 补  子节点（漏 timer 声明 → res=0 哨兵，D6 rc=0 一直在跑 = 写经缺省通道——如实登记）。D4/D6 全链不回归。④ **单元 G 拆分登记**：G2 = MCUmgr 固件 OTA（DEC-23：双 slot + MCUboot + SMP；工作区 mcuboot 在位且 esp32s3 有板级支持）——独立单元下会话开工（sysbuild + imgtool 签名 + SMP UDP + PC 客户端 + 真机 OTA 全链，体量 1-2 会话）。


- 2026-10-09 · **G2 部分交付（如实）：MCUmgr OTA——构建链与 MCUboot 引导全链打通（sysbuild + imgtool 签名 + mcuboot 双 slot + SMP UDP 服务器 + 真机启动 1.0.0）；**OTA 上传步骤被 WSL2 Hyper-V 防火墙阻挡（owner 一行 UAC 手动步骤）**。① **构建链**：west build --sysbuild（SB_CONFIG_BOOTLOADER_MCUBOOT=y → mcuboot 子镜像 37KB@0x0 + 签名应用 647KB@slot0 0x20000）；imgtool 版本内嵌（CONFIG_MCUBOOT_IMGTOOL_SIGN_VERSION，v1.0.0 真机自报 img-ver=1.0.0 ✓）。② **分区**：otabench overlay = AMP 4M 原位恢复 slot1_partition@0x170000(1344K OTA 槽) + ts 五分区后移 0x2C0000（**nodelabel 必须 = slot1_partition**——Zephyr 签名链 dt_nodelabel 固定名，起别名即 CMake 拒绝）。③ **WiFi 凭证注入**：sysbuild 不转发任意 cmake -D 到子镜像（三次实验证：UNINITIALIZED cache 空壳/IMAGE 前缀名/env→cmake ENV{} 可靠）——**最终 = CMakeLists ENV{OTAB_WIFI_SSID} 直读**。④ **SMP UDP 全链**：依赖链显式（ZCBOR/NET_BUF/CRC——缺任一 = MCUMGR 族静默失配 = SMP 不监听；真机超时教训）；板侧 smp_udp Started IPv4 ✓ + IP 自报 + alive 稳定。⑤ **阻挡点**：WSL2 mirrored 模式 Hyper-V 防火墙阻入站 UDP 回包（ping 通/出站到板通/回包断）——**owner 一行 UAC**：New-NetFirewallHyperVRule -Name SMP -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol UDP -LocalPort Any -Action Allow（或在 .wslconfig firewall=false——需 WSL 重启）。⑥ **串口 SMP 不可用（平台限制）**：esp32s3 USB serial JTAG 控制台 非 UART_CONSOLE → UART_CONSOLE_MCUMGR 透传不适用（树内实现仅在 uart_console.c 有 SMP 帧检测；DEC-23 UART 救砖底线在 S3 USB-JTAG 控制台上须换实现面——登记）。⑦ **PC 客户端**：ota_client.py（UDP）/ ota_serial.py（串口）两版仓外——SMP 线格式自研（BE 8B 头 + CBOR + base64 + CRC16-ITU）。

- 2026-10-09 · **单元 H 交付（G4/G5 批）：单活跃 APP 语义收口 + 模拟器深度增强——twister 15/15（77 用例，+3）/agent 77+2s/E2E 仿真/L5/ruff 全绿；板级生产构建（inputdemo@xiao_esp32s3 PSRAM）绿**。① **G4 激活即停**（撕裂态收口）：stage_activate 在 meta 翻转前停运行 APP（DR-14 升级停止语义）——旧缺陷 = 翻转后旧包继续运行而观测面（sys/get-app）报 STAGED/新槽（板侧 deploybench DB4 观测线程重启 = 本缺陷的 workaround 佐证）；停后装载周期 = 下次 boot（WAMR 换包怪癖已知偏差②——不热换）；卡死（E_TIMEOUT）生产照常翻转（WDT 升级重启收敛）/TEST 如实返回。② **G4 隔离拒载**（LLD §2「QUARANTINED 拒载」boot 面落地）：rollback 拒绝第 4 次时持久化标记 meta.rollback_count = LIMIT+1；boot_start 见标记 → 拒载 + 观测面如实 QUARANTINED（E_ROLLBACK_LIMIT）——旧缺陷 = 每次上电重载已知坏包（一次/boot 循环）；计数 == LIMIT（第 3 次回滚落地态）不拒（允许恰好 3 次回滚，与 runtime 语义一致）；解除 = 新安装（activate 重置计数）。③ **G5 输入文件实装**（LLD-A04 §2 三件事之首——M1 约定从未落地，scenario inputs 此前不驱动重放仅评期望）：固件 replay 新增脚本会话（test_00：外部 replay_script.tsv 在场按脚本驱动 / 不在场内建脚本走同一文件读取链 = twister/CI 全链覆盖；golden 会话让位保输出流纯净）；行格式 = link/estop/input/commit；JSONL = 输出写（rep_c/rep_d）+ 输入回显（in:N）按 t_ms 归并（同拍序固定 = 确定性）；agent runner 增 script_lines 映射（ch 命名空间校验：in:N 实例域/mv 非负/commit 通道在配置面）+ 脚本落盘；scenario schema v1 零变更（ch 字符串域约定；channel_kind 扩展位仍留 M3b）。④ **测试**：appmgr +test_boot_quarantine_refusal（拒载判据 = E_ROLLBACK_LIMIT vs E_IO 门鉴别 + 标记持久化）；app +test_08_activate_while_running（激活即停/持久面同步/停后运行面健全——不经 boot_start，见⑤）；replay +test_00（内建脚本 golden = 规格推导 100/155/100/7 + 输入回显恰一次）；agent +test_sim_script_mapping（映射矩阵）+ E2E 重写为脚本驱动（writes=6 = rep_c×4+rep_d fault×1+in:0×1）。⑤ **WAMR 怪癖第三型（登记）**：进程内二次 ts_appmgr_boot_start 产出的实例导出查找恒空（控制变量五组定位：字节/指针/缓存命中无关；直调 app_start 免疫）——dev-env 教训 28；生产无暴露面（boot 每进程一次，重载 = 暖复位）；test_08 规避 = 直调启动考察 activate 语义。⑥ **顺带登记（不动手）**：boardbench 板级构建 dram0 溢出 88KB @HEAD 复现（先于本单元——单元 D 栈增长族累积；现行板级载体 = inputdemo/deploybench 不受影响；boardbench 若复用需先内存再平）；decisions.md G2 条目损坏重复行清除（前会话 heredoc 残留）。⑦ G2 维持 ◐：板活（ping 通）但 SMP UDP 回包仍被 Hyper-V 防火墙阻挡（image_list 超时复测）——owner UAC 一行待办不变。


- 2026-10-09 · **单元 I 交付（MD2 混合 demo）：D9 全链 PASS + D8 部分交付（~90%，链路全证 + 单 clean-pass 跑受查询面停滞阻塞）——twister 15/15（77）/agent 77+2s/L5/ruff 全绿**。① **D9（输入-逻辑-输出 + 断链时间线）全链 PASS**：真 LLM 滞回+阻塞重试自愈 APP（demo.d9.linkloss，350/700‰ 双态基线）；仿真载体 = agent/scenarios/d9-linkloss.json（单元 H 输入文件接口首批真消费者——link 0/1 时间线：rep_c [500,0(linkloss),500] + in:0 断链期回显 = 合同 3 仿真证据，双跑确定性 ✓）；真机载体 = linkdemo bench（inputdemo 同型单装载）——**全部判据绿**：armed duty_hw=349@350 ✓ → 断链 d9 block rc=-4 + **linkloss 硬件 0%（CONF0 SIG_OUT_EN=0/IDLE_LV=0——LEDC 0% 特例路径，教训 29）** ✓ → 恢复 d9 out recovered=1 + D9-DONE ✓ + duty_hw=349 复活 ✓ + **断链窗 3.5s 内 d9 evt ×26 = 合同 3（输入流不因保护中断）APP 级证据**。② **D8（全生命周期混合）链路全证**：真 LLM 三版本（demo.d8.lifecycle v1 上行斜坡/v2 下行/v2bad 健康恒病）；v1 网络部署全链（upload/verify/activate/**G4 激活即停真机首证**/暖复位/装载 DB6）✓；v2 升级全链 ✓（**hb-host 心跳补上后 v2 写 rc=0 真落驱动**——d8 out 300..0 rc=0 + keep rc=0）；v2bad → 健康探针 3 败 → **meta 翻转回 slot0 + 复位 + v2 复活**（console DB6 slot=0）✓。③ **D8 拦下的存量缺陷（修复交付）**：Agent deploy.py 容器对拍 v1 残留公式（cose_off 16+ml+wl——网络链自板级十未跑、单元 D v2 迁移漏改；D8 真机对拍首跑即拦）→ TSAP_CONTENT_OFF 权威常量修复 + mock 同步（agent 测试 10/10）；deploybench 内存重平（模块静态面增长超板级十 748B 余量 → dram0 溢出 29460：LOAD_MAX 2048→4096〔v2 wasm 2.1KB 逼近旧限〕+ 系统池 188416→156672）。④ **新发现登记（不动手，B2 邻接）**：**健康回滚路径 WDT 竞态**——rollback 的全量验签（tweetnacl，运行在已停喂狗的 APP 线程）可超 APPMGR 软看门狗窗 → task_wDT 复位先于 rollback 打印（meta 先写 = 终态收敛正确；noinit reason=0x20001 留痕；机制修正属看门狗设计面 → 呈递候选）；**查询面停滞**——长会话/多次暖复位后板侧 zenoh queryable 停响应（put/发布正常，query 超时或空回包；重启会话不复现于新 boot）——根因未明，D8 唯一余项（clean-pass 单跑）受阻于此；get-app 无 app_ver 字段（版本观测缺口——D8 以 active_slot 链式区分 + APP init 行辅助）。⑤ **LLM 生成质量双发现**（约束已硬化入 gen_d89.py）：手写数值转换丢 0 值（while(n) 型）；再生成可能把 if 链改独立 if（armed/recovered 同拍串触发）——spec 须显式 else-if 串联 + 单次 log 完整行。⑥ D8 ◐ 判据面：D8a/D8b/D8c 链证据齐（console + client 双源），差 = 带心跳 client 的 clean-pass 单跑（D8 PASS 行）+ get-app rollback_count=1 终态对拍——受阻于④查询面停滞，随 B2 邻接批收口。


- 2026-10-09 · **单元 J 交付：Zephyr 升级评估（v4.4.0 → 下一 stable，含 zenoh 联动）——docs/zephyr-upgrade-eval-01.md；Q-30 呈递停门（门⑤）**。事实基线：v4.4.0 即当前最新 stable（2026-04-14，EOL 2027-04-12）；zenoh 三方 1.10.1 = 上游最新（升级零联动）；4.5 计划本月发布、4.6=2027-04 LTS4。**阻塞性论证：P4 目标板（DEC-28）在 4.4.0 不可移植**（espressif HAL soc 列表无 esp32p4），支持随 4.5 落地（main 实测 esp32p4 + esp32p4x 双板在树）；升级不解决的既有缺口如实排除（qemu twister 元数据 main 未修 / DAV2 main 仅 include 改名）。迁移成本面：最大项 = Espressif 板级 DT/Kconfig 重构（PSRAM 声明语义——真机实测项）+ native_sim TAP 转 DT（Agent E2E 迁移项），预估升级批 1-2 会话（含全量回归 + 三 bench 真机复验 + WAMR 怪癖家族撤实验）。**Q-30（门⑤呈递）**：背景 = DEC-19 已裁"持续跟进最新 stable"，4.5 本月发布，P4 适配以升级为前置；选项 = A 4.5 发布后即升（P4 解锁，DEC-19 既定方向）/ B 跳 4.5 等 4.6 LTS4（P4 冻结至 2027-04 且 4.4 EOL 与 4.6 同月零裕量）/ C 维持 4.4.0（违 DEC-19 + P4 永久阻塞，不建议）；**建议 = A**；影响 = 月内一个升级批（1-2 会话）+ P4 适配独立批（另 1-2 会话 + owner 提供 P4 实板〔请附硅版本：espressif 已发 v3.x 硅刷新，esp32p4x 板对应新硅〕）。附裁决点：P4 采购硅版本。**停门：owner 裁 Q-30 前不动技术栈。**


- 2026-10-09 · **B2 批交付（查询面停滞根因 + 修复；D8 clean-pass 环境受限如实登记）——twister 15/15（77）/agent 77+2s/L5/ruff 全绿**。① **「查询面停滞」根因定论 = agent 侧双缺陷（板与路由器无责）**：受控实验（双向探针：裸 zenoh 会话订阅见板 alive/telemetry、get-info 直查得完整有效回执——发布与查询路径在板侧全通）逐层剥离后定位——(a) **zenoh locator 语法**：1.10.1 正式语法 ，旧式  解析为协议 "tcp:" → 会话开失败且间歇性表现（ZenohService 中心归一化修复）；(b) **Reply API 漂移**：1.10.1 Reply = ok/err/replier_id（无 err_payload），错误回执路径一踩即 AttributeError，异常中断 get 迭代后会话残留未消费状态 → 后续调用挂起 = 停滞假象（按 1.10.1 取 err.payload + finally 排空修复）；(c) 环境放大器：暖复位后路由器残留陈旧 queryable 声明（WSL mirrored NAT 拖死 TCP）→ 通配发现可被死 peer 超时拖垮（client 加点对点直查兜底）。教训 29.5。② **rollback_count 随载恢复（存量缺陷修复）**：boot_start 装载路径仅恢复 state/slot、从不恢复计数——flash meta 实测 {slot:1,count:1} 而运行时 get-app 报 0（D8 终态对拍拦下）；修复 = 装载成功路径同步 meta.rollback_count + framework.app test_04 增断言（8/8）。③ **D8 各段双证齐**：v1 部署 / v2 升级（G4 激活即停）/ v2bad 健康回滚 → v2 复活 + **rollback_count=1 终态对拍 ✓**（修复后实测 last={slot:1,count:1}）；**单跑 D8 PASS 行仍缺 = 环境窗口**（当晚家宽 AP 劣化：WiFi 关联 8→68s 随机漂移，三段链需 4 次重连全落窗内——多轮尝试各段分别通过但未能一次连贯；链路逻辑无缺陷，择网络平峰期一跑即收）。④ d8_client 加固交付：hb-host 心跳线程（linkmon 判活——MD1 既有模式补携带）+ v2bad 瞬态语义修正（健康回滚 ~3s 翻转，瞬态 ACTIVE 不作硬判据——终态为判据）+ 直查兜底。⑤ DAV1（av 冻结）未启动——B2 主体（查询面）已完成；DAV1 独立会话再开（登记）。


- 2026-10-10 · **G2 完整收口（M0 以来最后一个硬件验证余项）：MCUmgr OTA 全链真机 PASS——v1.0.0 运行 → SMP UDP 上传 v2.0.0（1686 包/647344B）→ slot1 pending+permanent → 复位 → MCUboot「Swap type: perm」→ v2.0.0 运行（OTA0/alive 双证）**。排障战果（四层洋葱，逐层实证）：① **原「Hyper-V 防火墙」诊断推翻**——owner 已开规则（Get-NetFirewallHyperVProfile 实测 DefaultInbound=Allow，规则本就多余）；② **WSL mirrored 入站 UDP 中继缺陷**（独立铁证：宿主自发包至 192.168.2.90:9999 的 WSL 监听不达）→ 客户端移 Windows 侧运行（宿主栈状态化 UDP 正常）；③ **PC 客户端双字节缺陷（G2 全程零回包真凶）**：SMP 头组字段应为 u16（格式串少一个 H=7B 头被板静默丢）+ WRITE 操作码应为 2（旧值 1 = READ_RSP → 服务端 ENOTSUP=rc8——自定义组 64 read/write 探针一锤定音「WRITE 全灭 READ 全通」）；④ **smp_udp pre-IP 绑定缺陷（板侧）**：SYS_INIT 早期（WiFi 前）启动的 UDP 套接字在 esp32 上收不到后续单播（线上铁证：请求出线+ARP 通+板零回包；独立 :9999 探针口通 → 锁定 smp 层）→ 修复 = 拿到 IP 后 smp_udp close+open 重启（OTA2b）——入仓。附加：Zephyr 4.4 img state confirm 语义 = {hash, confirm:bool}（旧 test/confirm 双键 = EINVAL）；上传块 ≤ 512-CBOR 头（NETBUF_SIZE 截断静默丢）；首包擦槽 ~1s（长超时窗）。教训并入 29.5（zenoh/网络族）。v2 上传后 SMP 不应答 = 该镜像系 G2 期构建（无 OTA2b 修复）——台架胶水缺陷已定案，非新问题。


- 2026-10-10 · **D8 单跑 PASS 行补收（单元 I 唯一余项闭环）**：网络平峰期一跑即过——v1 初装 → v2 升级（G4 激活即停）→ v2bad 健康回滚 → **v2 复活 slot 翻转 + rollback_count=1 终态对拍 ✓ → D8 PASS**（console + client 双源）。**MD2（D8/D9）自此全绿**；排期表 v1.30 全部单元 A–J 触达完毕（唯 Q-30 裁决与 DAV1 会话在外）。


- 2026-10-10 · **DAV1 交付（av 流 APP 线程冻结专项）：根因定案 + 防御链实证 + 诊断探针入仓——twister 15/15（77）/agent 77+2s/L5/ruff 全绿**。① **冻结复现与定位（诊断探针 = runtime.c WDT_WARN 订阅：dump 冻结线程状态串/优先级/当前线程/全栈文本域字 → 离线 addr2line）**：APP state=queued prio=10 + 栈帧链 app_thread_entry → wasm_interp → native_av_capture/native_net_publish → **i2c_ll_write_txfifo（esp32 摄像头 SCCB/I2C 轮询忙等）**——冻结点在上游 esp32 video 驱动内的传感器 I2C 路径（APP 线程自旋于 native 内，native 执行不受 wasm 指令计量约束〔计量只在解释器层〕）。② **控制变量（单元 B 原怀疑方向全部排除）**：本轮冻结发生于任何发布之前（PC 消费端 chunks_seen=0）——**avq 深度/打拍/重试与 zenoh 发送全链无罪**；本轮冻结近首帧（每 boot 一冻，9 连冻复现；单元 B 期曾 ~10 帧后冻 = 摄像头总线稳定度随环境漂移〔EMI/排线接触嫌疑〕）。③ **防御链实证**：L1 软看门狗（APPMGR 1000ms）每次如期拦截 → system_fail noinit 留痕 → 复位重启循环——合同 4/DEC-48 分层防线在此缺陷上的行为 = 设计如一。④ **判据修订（D-AV 全链 PASS）**：阻塞不在框架/网络面——剩余条件 = 摄像头硬件稳定度（owner 动作：Sense 板摄像头排线重插/抗扰检查；上游驱动 I2C 忙等 = 零补丁纪律内登记不修）。防御链已验证 + 帧证据尽力而为（单元 B 期 10 帧全链曾通）。⑤ 诊断探针为常设可观测性改进（CONFIG_XTENSA 门控，native_sim 惰性）——后续任何 APPMGR 饿死/自旋类缺陷同法可诊。


- 2026-10-10 · **D-AV 帧证据跨复位累计尝试（如实）：未收口——摄像头当晚零帧交付**。① 方法落地：dav_recv.py 增跨复位累计（fid 回卷 → generation 键，避免覆写/混装；窗口 240→900s，仓外工具）；② 实测：13 boot / 11 到 DA3 ACTIVE / 12 到「stream started」，**chunks_seen=0**——每 boot 摄像头 DMA 即「Frame dropped. No buffer available」且 APP 卡死于 SCCB（唯一可读 WDT-WARN 转储与 DAV1 同点位；其余 boot 的诊断输出被日志系统丢弃〔console 洪泛下 messages dropped〕）；③ 结论：帧证据收口**确实只剩摄像头硬件动作**（当晚较单元 B 期〔曾真帧+发布〕进一步劣化 = DAV1 环境漂移判断再证）；④ Q-30 状态更新：上游 **v4.5.0-rc1 已 tag**（正式 v4.5.0 未发）——建议 A 的执行时点临近，owner 裁决后即可进入升级批。


- 2026-10-10 · **DEC-50（Q-30 裁决，owner 原文）**：「请你直接采用v4.5.0-rc1，P4板卡采用的是ESP32-P4-WIFI6-DEV-KIT最新版」。解读：① 升级时点 = **不等正式 v4.5.0，直接钉 v4.5.0-rc1**（建议 A 的 rc1 变体——DEC-19「跟进最新 stable」的时点裁量；正式版发布后再平移）；② **P4 载板 = ESP32-P4-WIFI6-DEV-KIT（最新版）**——适配批板目标按此选（含 C6 伴芯 WiFi6 套件；Zephyr 内 P4 无线面 = C6 伴芯路径，首批以有线/串口面 bring-up 为界，联网面后续批）。执行：升级批即开（工作区切换 + 全量回归 + 三 bench 真机复验）；P4 适配批随后独立批。


- 2026-10-10 · **升级批交付（DEC-50：Zephyr v4.4.0 → v4.5.0-rc1）——native_sim twister 15/15（77 用例）全绿 + 三板级 bench 构建绿 + inputdemo 真机复验核心判据绿**。① 工作区：zephyr checkout v4.5.0-rc1 + west update 全模块 + west blobs fetch hal_espressif（教训 30①）；zenoh-pico 1.10.1 原样（三方钉版不随 Zephyr 动）+ WAMR 2.4.5 原样（TS_WAMR_DIR 外部依赖）。② 仓库内适配三处：模块 CMakeLists 补 WAMR autoconf.h 包含域（教训 30③）；三 bench overlay 分区节点补 mapped-partition 兼容串 + otabench 删默认布局 appcpu/lpcore 冲突分区（教训 30②）；deploybench 系统池 156672→151552（4.5 静态面再平）。③ **回归全绿**：twister native_sim 15/15（77——全测试面零代码改动过升级）+ agent 77+2s + L5 6/6 + ruff。④ 真机复验（inputdemo @ xiao_esp32s3，rc1 镜像）：boot 链（prov→install→装载→APP 运行）✓；**ID1a poweron-duty 寄存器级 299‰@300 OK**（LEDC 物理路径与 4.4 一致）✓；WAMR APP 双包顺序运行（D4 报告/事件真值流 → stop → D6 限幅 rc=-12 + 滞回装载）✓；G4 槽切换（ID2→ID3→ID4）✓——D4-DONE/D6-DONE 全链判据依赖物理噪声注入（单元 F 既有约束：当晚噪声带 15-31mV 不跨阈），框架面无回归。⑤ WAMR 怪癖家族撤实验：native_sim 双 boot_start 怪癖（教训 28）在 rc1 仍按规避（twister 各二进制单 boot 不触发；不属回归面）。正式 v4.5.0 发布后平移（delta 预期极小）。P4 适配批（ESP32-P4-WIFI6-DEV-KIT）下会话开。


- 2026-10-10 · **P4 适配批交付（board-p4-01：ESP32-P4-WIFI6-DEV-KIT 框架 bring-up 真机全链 PASS；J 单元收口）**。① 板与目标：Waveshare ESP32-P4-WIFI6-DEV-KIT（P4 v3.1 双核 RV32@400MHz + LP 核，GD 16MB flash + 32MB PSRAM〔挂接待后续批〕）；Zephyr 目标 = esp32p4_wifi6_dev_kit/esp32p4/hpcore（v4.5 斜杠限定语法）；SDK 1.0.1 补装 riscv64-zephyr-elf 单工具链（setup.sh -t）；WAMR 板映射表登记 RISCV32（解释器-only，AOT=0 无 invokeNative 面）。② p4bench（persistbench 源级复用，判据前缀 P4B）：五分区 carved 自 16M 默认布局 slot1 区 @0x7E0000（lpcore/storage/coredump 原样保留）；console 经 overlay 重指 uart0（板默认 = 原生 USB-Serial-JTAG 需另接线；CH343 COM 口实测 = UART0 与 esptool 同口，单线判据）；MAIN_STACK_SIZE=8192（RV32 帧深于 Xtensa，4096 在安装链实测溢出——Illegal instruction @ bss 数据表 = 栈溢出回跳指纹）。③ 真机判据全链 PASS：P4B1 prov 注入 → P4B2 v2 包安装（928B）→ 暖复位 → P4B3 prov 出 flash → P4B5 APP ACTIVE（com.tessera.p4b）+ app_evt 写链 gpio 1/0 → P4B PASS + 存活循环——WAMR 在 RV32 上装载运行 WASM 全链首证。④ 顺带修复存量缺陷两族（升级批/DEC-49② 漏网）：六 bench overlay 缺 mapped-partition 兼容串（avdemo/dsdbench/linkdemo/metabench/persistbench/wdtbench——4.5 重构建即挂）；persistbench 自构造包为 v1 格式（DEC-49② v2 fail-closed 后即坏，真机 bench 不在 CI 构建面静默漏网）——换 gen_p4b_pkg.py 机械生成 v2 包（测试根签名），v1 构造器删除。⑤ 回归全绿：twister native_sim 15/15（77，标准 EXTRA_MODULES 口径——教训 31⑥ 管道假绿险情登记）+ pytest 2/2 + persistbench S3 @rc1 构建绿（真机复验待板换线顺带）。⑥ 后续批：P4 无线（C6 伴芯 esp-hosted）/PSRAM 挂接/真外设绑定；D-AV 帧证据待 owner 摄像头硬件动作。


- 2026-10-10 · **H7 移植批交付（构建级，board-h7-01 v0.1；真机判据待 owner 接板）**。① 板裁决落地：owner 指令「743板子采用mini_stm32h743」——WeAct Studio MiniSTM32H743 核心板（STM32H743VIT6）即树内板目标 mini_stm32h743（DEC-28 目标集第三板）。② h7bench（persistbench 源级复用，H7B* 判据）：五分区 carved 自内部 flash 尾 @0xC0000——H743 擦除块 128KB，每分区独占整扇区（P4/S3 的 4KB 粒度模式不可平移）；slot = 131072（扇区耦合）；console 补 chosen = usart1（PA9/PA10，板 dts 无 console 声明）；MAIN_STACK 8192 保守起值。③ WAMR 板映射登记 THUMBV7EM：ARM target 在 Zephyr 全 -mthumb 下汇编期拒（invokeNative_arm.s = A32 汇编），THUMB 分支取 invokeNative_thumb.s；解释器-only 下不参与运行仅过链接（P4 论证同构）。④ 构建级实测：FLASH 158KB/2MB（7.6%）、sram0 349KB/512KB（68%，含 WAMR 堆 256KB）——h7-memory-assessment 推算吻合。⑤ 回归全绿：twister 15/15（77）+ pytest 2/2。⑥ 真机预案（board-h7-01 §6）：ST-LINK 烧录（板无调试器）+ USART1 console；已知风险 = 板 dts HSE 25M 声明 vs WeAct 实板常见 12M 晶振（乱码即 overlay 修正）+ flash 写对齐真机复核。owner 已接板线（ST-LINK/USB-TTL/Type-C）中——真机判据下一单元收口。


- 2026-10-10 · **P4 PSRAM 挂接批交付（真机全链 PASS；board-p4-01 §7 遗留清单第二项收口）**。① owner 裁决：H7 真机测试暂停（手头暂无 ST-LINK），转其他任务——H7 真机判据挂起待器件（board-h7-01 §6 预案不变）。② p4psram（psrambench 源级复用，P4P* 判据）：P4 SPIRAM = HEX 16 线模式（Kconfig P4 专属默认，QUAD/OCT 不可选）；WAMR 堆 256KB = S3 板级六同值（DEC-27；更大值属内存预算批不越权定）；MAIN_STACK 8192（教训 31⑤）。③ 真机判据全链 PASS（2026-10-10 实测）：P4P1 SMH 探针 buf=0x48000060 读写一致（EXTEMEM 域地址证据）→ wamr pool heap buf=0x48000060 (psram/smh)（WAMR 堆自 PSRAM 分配）→ P4P3 APP 全链（init/evt 写链）→ P4P PASS init_res=0 evt_seen=1 heap=256KB@PSRAM + 存活循环。④ 回归全绿：twister 15/15（77）+ pytest 2/2。⑤ P4 板余项：无线面（C6 伴芯 esp-hosted）/真外设绑定；H7 真机（待 ST-LINK）。


- 2026-10-10 · **P4 无线面批交付（部分达成 + 上游缺陷定案；教训 32）**。① 板链全通：Waveshare P4-WIFI6-DEV-KIT 的 C6 伴芯（ESP32-C6FH8）固件链落地——owner Windows EIM 环境（IDF v6.1 + C:/Espressif 工具区）+ esp-hosted-mcu v3.0.9 cp 工程（esp32c6 target）构建 + owner 手动烧录（IO9+RST 进模，CH340@COM9）；C6 SDIO datapath 定值 STREAM（SW_AGGR 需 host 协商而 Zephyr 驱动不发；PACKET 为上游死代码）。② P4 侧（netbench @ esp32p4）：esp_hosted 面全链真机证据——版本握手 coprocessor firmware v3.0.9 + wifi_connect rc=0 + connect_result/associated 事件回传 3/3 稳定 + C6 侧确认执行 host RPC 并连接 WiFi 成功（connected with cemetery）。③ **上游缺陷定案（阻塞项）**：Zephyr 4.5 esp_hosted 驱动（drivers/wifi/esp_hosted + misc/esp_hosted_mcu，Arduino 贡献新驱动）RPC 控制帧通而 UDP/TCP 数据帧基本不通——DHCP 3/3 挂（唯一过 DHCP 一例 zenoh TCP 亦挂）；固件侧/协议侧/硬件侧已逐层排除（C6 日志为独立证据），属 Zephyr 上游驱动数据面成熟度问题——NB 全链判据（NBR PASS）挂起为外部依赖，呈递候选 = 报 Zephyr upstream issue（owner 裁决是否提交）。④ 顺带修复两存量缺陷（构建面）：zenoh-pico 平台头裸 include version.h（4.5 legacy 头移除同族——tessera 模块 CMake 生成头包含域提为模块级）；无 WAMR 构建面缺 ts_appmgr_app_running/app_stop 符号（单元 H 引入后未覆盖——slot.c 无 WAMR 桩）。⑤ 回归全绿：twister 15/15（77）+ pytest 2/2 + netbench P4 构建绿。⑥ 观察项：P4 无线面后续 = 上游驱动修复跟进（或升级 Zephyr 平移时复测）；P4 真外设绑定仍待开。


- 2026-10-10 · **DEC-51（owner 裁决，板卡集收缩 + issue 授权 + S3 回归主力板）**：「请你帮我进行起草issue并提交，然后搁置P4和H7的适配只做esp32s3，以及剩余的后续工作，usb我已经移除了p4接入了s3」。解读：① **板卡集收缩 = S3 单板**（xiao_esp32s3 为唯一真机目标；P4/H7 移植成果保留在库——p4bench/h7bench/p4psram/netbench-P4 板文件与全部文档留档不撤，但后续不再投入适配工作——修订 DEC-28 目标集『S3/P4/H7』为『S3-only』执行期形态；P4 无线面 esp_hosted 上游缺陷 issue 授权起草并提交 zephyrproject-rtos/zephyr）；② H7 真机判据（board-h7-01 §6 预案）维持挂起（无 ST-LINK）；③ S3 已重新接入（usbipd 7-4）——persistbench @4.5 真机复验（板级遗留项）即行。

- 2026-10-10 · **persistbench S3 @4.5 真机复验批交付（DEC-51 后首个 S3 单元；板级遗留项收口）**。① 复验发现并修复存量缺陷：**4.5 调用帧深于 4.4——verify 链（tweetnacl ed25519）在 4096 main 栈实测挂死**（症状 = 分步心跳停在 verify 不返回；与 P4 教训 31⑤ 同型——P4 为 Illegal instruction、S3 为静默挂死）；修复 = persistbench 板 conf MAIN_STACK_SIZE=8192，**全 S3 bench 板 conf 批量同型防御**（12 个补 8192 + inputdemo/linkdemo/persistbench 原有 8192——15/15 覆盖）。② 真机判据全链 PASS：PB1 prov 注入 → PB2 v2 包安装（verify done）→ 暖复位 → PB3 flash 自举 → PB5 APP ACTIVE（com.tessera.persist）+ 写链 → PB PASS。③ persistbench main.c 安装链分步报码（p4bench 同型移植，合取式换分步）。④ 诊断期两坑登记：esptool erase/write 后 hard-reset 触发固件首启秒写回（读回『没擦掉』假象——判定须 --after no_reset + 手动复位编排）；WAMR version.h 只读屏障曾被解除（10-09 批操作遗留 644）→ 15 并发竞争复燃（framework.store 构建失败）——chmod 444 恢复后 15/15（77）全绿。⑤ 回归：twister 15/15（77）+ pytest 2/2。

- 2026-10-10 · **Zephyr upstream issue 提交完成（P4 无线面缺陷上报）**：https://github.com/zephyrproject-rtos/zephyr/issues/121767（drivers: wifi: esp_hosted — 控制面通/数据面挂；环境 v4.5.0-rc1 + ESP32-P4/C6 SDIO + esp-hosted-mcu v3.0.9 STREAM；证据链 = 版本握手/关联 3/3 + C6 侧独立日志 + DHCP 3/3 挂 + PKT_LEN 轮询空转）。owner 经 gh device 授权（embalmer-Y）后由会话提交。后续跟进 = 上游回复/修复后 P4 无线面复测（板卡集 S3-only 期间该 issue 为外部跟踪线索）。

- 2026-10-10 · **D-AV @4.5 复测（板形态确认 + 采集执行——硬件动作前不可收定论不变）**。① 板形态确认：当前接入 S3 = sense 版（camera chosen 有效 + 视频流启动实证）。② avdemo @4.5 首构建绿（升级批漏建补全）：双 EXTRA_MODULES + zenoh overlay 口径；DRAM 溢出 3868B → 系统池 98304→94208 调档。③ 复测单迹：DA1 wifi_connect 0 → DAw associated → DA1b/DA1c 安装 → **[av] stream started (160x120 rgb565)**（摄像头 DMA 活）→ DA2 session CONNECTED → DA3 APP ACTIVE（部分轮次）→ 复位循环 + dav_recv chunks_seen=0；另轮 DHCP 超时（网络间歇观察）。④ 定论：与 2026-10-07/10 DAV1 完全同象（流启动而零帧——上游 esp32 video 驱动 SCCB 忙等 + 摄像头硬件接触），**非 4.5 回归**；帧证据收口条件维持 = owner 摄像头排线重插/抗扰物理动作（方法〔分代键累计〕持续有效，动作后一跑即收）。

- 2026-10-10 · **D-AV 采集执行 + 新缺陷定案（owner 摄像头连接修复后）**。① 采集执行：擦 prov（此前被 persistbench 复验批覆盖为 pb-dev——两 bench 共用 ts-prov 分区，键前缀不匹配即零接收的根因之一）后 dav_recv 收到 chunk——**帧已能采集并发布**（chunk 数据 = 真实 RGB565 像素，160x120）。② **新缺陷定案（主阻塞）**：**Zephyr 4.5 下 zenoh-pico 板→路由方向 1KB payload 发送 100% crc 损坏**——证据链：板侧信封 crc 正确（全零 1024B 块的板侧值 efb5af2e = zlib.crc32 标准值——算法一致实证）+ 数据为真实帧内容 + PC↔PC 自环 20/20 无损（路由/接收端无责）+ 心跳小包通（尺寸相关）；4.4 同码同链路帧曾通（单元 B 实证）= **4.5 回归**，损坏点 = 板侧发送路径（zenoh-pico TCP 分段 send 或 4.5 socket/WiFi 驱动面）。256B 绕行档已建（TS_NET_PUBLISH_MAX_BYTES=256）但板侧 dequeue 风暴与网络间歇（DHCP 部分轮超时）双重干扰下未获验证。③ 摄像头面：dequeue timeout 风暴与出帧态交替（DAV1 电气/上游驱动面持续）。④ D-AV 帧证据收口条件更新：**新主阻塞 = 上述 4.5 发送损坏**（upstream 域——与 #121767〔P4 esp_hosted 接收侧〕可能同根 4.5 网络栈，关联观察）；摄像头电气态已由 owner 修复（连接良好）。

- 2026-10-10 · **esp32 video 驱动缺陷上报（owner 指令记录）：zephyrproject-rtos/zephyr#121774**——首帧后帧产出永久停摆（Frame dropped. No buffer available 风暴 + dequeue 无限超时；buffer 计量失衡嫌疑——应用两 buffer 均在队未被取时驱动即报无 buffer）。背景：owner 摄像头排线修复后首帧可出（内容为有效 RGB565），停摆层随即清晰暴露 = DAV1 定案的上游驱动面。另注：WSL 网络改直连（代理关闭）——裸环境 gh/curl 可用，显式代理变量的调用失败（教训候选 33）。

- 2026-10-10 · **批 A 首批交付（owner 裁决：S3 全 bench @4.5 真机回归收口——impl-review-03 R1 处置；3.5/7 件达成，续批待办）**。① **netbench @4.5 PASS**：DRAM 溢出 33036B → 系统池 188416→153600（板 conf 入仓）；真机 NBR 判据（WiFi/DHCP/会话 + 强制断链自愈 #1 2693ms + alive 稳态 = PASS 后唯一代码路径）；池实证充足。② **linkdemo @4.5 PASS**（一次绿）：armed 349‰ → linkloss 0% 特例路径 → D9-DONE recovered → 复跑 349‰ + alive（d9_pkg 已 v2 无需换）。③ **deploybench @4.5 PASS（双证）**：板侧 DB PASS（构建一次绿——4.5 内存面 151552+8192 成立）+ PC 侧 D8 三段部署链全绿（v1 初装 D8-DONE → v2 上传 4716B/256B 分块 verify/激活 G4 即停 → v2 运行 D8-DONE → v2bad 健康回滚 → v2 复活 count=1 → **D8 PASS**——B2 时代遗留的单跑 PASS 行至此在 4.5 补齐）。④ **otabench @4.5 半程**：sysbuild 构建烧录绿 + 启动链（WiFi/IP 192.168.2.13/SMP :1337/smp_udp restart 修复路径生效）+ **SMP 上传链全绿**（Windows 侧 ota_client 1685 包 646676B + verify + test/confirm 回包语义正常）；**swap 执行待查**——复位后 MCUboot 直接启 slot0（无 swap 日志）——test 标记写入疑点（4.5 mcuboot trailer 面待查，批 A 续首项）。⑤ 三坑登记：**ts-prov 覆盖第三次**（avdemo 的 dav/dvc 覆盖 deploybench 的 dbn/dbc——多 bench 共用 ts-prov 分区换烧前必擦，教训 33 候选）；**路由器死声明清台复用**（29.5③ 处置 = pkill+重起 zenohd 即恢复点对点）；d8 的 v2 后 find 60s 窗口在重启抖动下偏紧（批 A 续可放宽）。⑥ 待办（批 A 续）：otabench swap 待查 + 小 bench 七件（boardbench/estopbench/periphbench/psrambench/metabench/wdtbench/dsdbench）@4.5 逐一。

- 2026-10-10 · **批 A 续交付（S3 bench @4.5 真机回归——6/8 全绿 + 2 遗留登记；impl-review-03 R1 收口）**。① **otabench @4.5 全链 PASS**（OTA0 img-ver=2.0.0 swap 运行 + alive）：swap 未执行根因三连定案——**4.5 mcumgr img state API 变化**（"test" 键移除、confirm 变 bool——ota_client 适配：test={hash,confirm:false}；旧格式回 MGMT_ERR_EINVAL=3 实证）；**同版镜像测试设计缺陷**（同 hash 双槽 → test 按 hash 解析到 active slot 被拒——需不同版本镜像，本批 2.0.0 实证 swap）；SMP reset UDP 间歇丢（RTS 手动复位绕行）。② **estopbench @4.5 PASS**（EB PASS 硬件沿×3 + ISR 直达/锁存/补发/恢复）——顺带修复存量编译缺陷：ts_safety_estop_edge_of 无前置声明（safety.h 补——真机 estop 面自单元 F 引入起未被任何构建面覆盖，native 面 DT 无节点编不到该路径）。③ **periphbench @4.5 PASS**（PP PASS：duty 全档对拍 99/250/500/699‰ 绿）。④ **psrambench @4.5 PASS**（PS PASS：SMH 0x3c03 域 + 堆@PSRAM + evt 全链）。⑤ **metabench @4.5 PASS**（MB 链 + 暖复位双副本校验 + alive 稳态=PASS 后唯一路径）。⑥ **wdtbench @4.5 判据达成**（WDT-WARN diag 探针 @4.5 顺带验证 + 复位循环 = DEC-48 看门狗链形态）。⑦ 遗留二项：**boardbench ◐**（BB-init 绿 30009us + WAMR 池已迁 PSRAM（DRAM 溢 97812B→DEC-27 迁移修复）；BB1 busy POLL TIMEOUT——APP evt 投递链 4.5 疑点待专项查）；**dsdbench ✗ 构建受阻**（4.5 fatfs FF_VOLUMES 生成链 + SPI_SDHC 依赖警告——SDMMC/fatfs 模块面 4.5 迁移缺口，需专项适配）。⑧ 批 A 总战果：S3 主体 bench @4.5 真机基线恢复（netbench/linkdemo/deploybench/otabench/estopbench/periphbench/psrambench/metabench/wdtbench 9 绿 + 2 遗留）；回归 twister 15/15（77）+ pytest 2/2。

- 2026-10-10 · **批 A 收尾专项（boardbench BB1 定案 + 全链 PASS；dsdbench 构建面通——介质层待 owner）**。① **boardbench @4.5 全链 PASS**（BB PASS + running=1；BB1 吞吐 1189ns/iter〔4.4 时代 1043ns 同量级 = 无 4.5 性能回归〕、BB2 native 往返 4735ns、BB3 写路径 10468ns、BB4/BB5 分布、BB6 estop 并发安全——全链 @4.5 基线数字刷新）。② **BB1 根因定案（诊断探针实证）**：300000 iters ≈ 9M 指令**超 DEC-48③ 指令配额** → wasm 异常 → APP 被健康链终止（BB1 diag：running=0/evt_seen=1/health_fails=12——「静默死」形态；非 4.5 回归：配额引入〔Q-28③A〕晚于 bench 定参且 4.4 期 boardbench 未复跑）。修复 = BUSY_ITERS 300000→30000（配额内最大量级样本；注释定案）+ BB1 diag 探针回缩。③ **dsdbench 构建面通**：前判「fatfs/SDMMC 4.5 迁移缺口」修正——根因 = 构建命令板 target 漏 /sense qualifier（SD 节点在 sense 变体 dts——FF_VOLUMES 由 DT 磁盘枚举生成〔zephyr_fatfs_config.h 覆盖链〕）；/sense 重构建绿 + 烧录后 SD 物理链路通（clock 协商 20MHz）——**挂载写失败（fs mount -5，自动 MKFS 写卡失败）= 介质层**（写保护/卡态），已呈 owner 检查卡（LOCK 位置/PC 格式化 FAT32/换卡）。④ 回归：twister 15/15（77）+ pytest 2/2。

- 2026-10-10 · **dsdbench 诊断深化（信号完整性假说排除——卡本体实锤，待 owner 换卡）**：SDHC DBG 日志实证写失败形态 = 写命令后卡进永久 BUSY（CMD13 轮询 ~25 次 × 200ms 超时）；sdhc-spi-slot 节点 spi-max-frequency 降 4MHz 实验（实测时钟生效 4MHz）写仍同败——**时钟速率/信号完整性假说排除**；microSD 无物理写锁（写保护假说前已排除）。结论 = **卡本体（坏卡/卡死态/驱动不兼容卡）**，唯一处置 = owner 换卡（或 PC 格式化救回尝试）。诊断档（DBG 日志 + 4MHz 实验）已回滚，标准版固件（20MHz）已烧录就位——换卡后复位即跑 D-SD 全链。
