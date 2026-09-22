# R4 · Tessera Agent 交互与接入方式调研（协议 / 实践 / 趋势）

> **状态**：v1.0.2 · 2026-09-22 · research 阶段产出（阶段白名单内）· **Q-16/Q-17 已裁 → DEC-35/36**（ACP：V1 不做仅预留；交互栈 4 子项全采纳 + **A2A v1.0 预留显式登记**）。**DEC-37（Q-18：C）修订**：Agent = 全 Python（PydanticAI + FastMCP），§5 交互栈图中"pi 原生支持 skills"改为自建 skill loader、MCP 门面 SDK 为 FastMCP/官方 Python SDK——分层结构与各层选择**不变**。Agent 轨道 research 阶段落定（R3+R4+R5）。
> **任务来源**：owner 2026-09-22 指令——"对于MCP的选择只是基于我自己的知识进行的选择，这不一定是最新的最前沿以及最合适的方式，请你再进行第二轮research，看看我们要做的这个Agent如何交互以及如何接入其他AI工具更好。我们要找到最新的技术和趋势，选择前沿方案，这是一个面向未来的项目。"
> **核验方式**：3 个并行调研子代理经 WebSearch/WebFetch/GitHub API 于 **2026-09-22 实查**（官方 roadmap/changelog/论文原文多为直接抓取）；来源见 §8，未能核验项以 ⚠️ 标注。
> **与 R3 的关系**：R3（`R3-agent-foundation.md`）解决"基座选什么"（已裁 → DEC-33 pi）；R4 专攻"交互与接入层"（对外协议/人机接口/长任务/能力分发/多域组合），并对 R3 §4.6 的长任务结论作实现级细化。

## 0. 背景（自包含）

DEC-12（2026-09-18）定 Agent 形态 = MCP server，封装"模块 API + 模拟器 + 构建工具链"。owner 指出该选择基于其既有知识，未必是最新最前沿，要求第二轮调研重新校验"Agent 如何交互、如何接入其他 AI 工具"。本报告回答：①2026-09 时点 agent 互操作的真实格局；②前沿实践对我们的实现纪律要求；③未来（多域 agent 组合、直至"自己生产自己"北极星，DEC-33）应押注与规避什么。

## 1. 总结论（先答 owner 的问题）

**MCP 的选择没有过时——它不仅仍是唯一事实标准，而且刚刚完成一次激进的现代化（2026-07-28 大版本）并被捐入中立基金会。** 真正需要吸收的更新是四件事：

1. **协议战争已经收敛，格局制度化**：MCP（工具面）+ A2A v1.0（agent 间）+ AGENTS.md（仓库指令）同入 **Linux Foundation AAIF**（Agentic AI Foundation，2025-12-09 成立，OpenAI 联合创立）；**Agent Skills（SKILL.md）成为领域能力分发开放标准**（Anthropic 2025-12-18 开放，45+ 工具支持，**pi 内核原生支持**）；IBM 的同名 ACP 已并入 A2A、Agent Protocol 休眠、ANP/AG-UI 未成气候——**没有颠覆者，但分层栈成形了**。
2. **MCP 自身断代（2026-07-28）**：协议核心全面 stateless 化（删除 initialize 握手/会话头）、MRTR 取代服务器发起请求、**弃用 Roots/Sampling/Logging**（12 个月窗口）——新写 MCP server 必须按新形态设计，同时兼容旧客户端（2025-11-25 语义为兼容基线）。
3. **长任务的官方与现实落差**：官方 Tasks extension **客户端采用 ≈ 零**（Temporal 专文《MCP Tasks: Why Aren't Any Agents Supporting Them?》，2026-08）——现实惯例 = 工具**立即返回任务句柄 + 独立 status/log 轮询工具**；Claude Code 对超 2 分钟的工具调用自动转后台，Codex 默认 600s 超时——立即返回是唯一安全模式。
4. **Tessera 生态位被三组证据锁定**：① **Quilter Project Speedrun**（2026）：AI 全自动布局的 i.MX8M Mini 主板已制造 10 套全部点亮、Linux 稳跑三个月——但**固件 bring-up 全程人工**（428 人时布局降到 38.5 人时，固件不在其中）；② **IoT-SkillsBench**（arXiv 2603.19583，Duke 系）：真机验证的嵌入式 agent 基准，**专家编写的 skills 使跨平台成功率接近满分**；③ **ESP-IDF v6.0 官方 MCP server**（`idf.py ai-cli --mcp`，2026-04）：构建系统内嵌 stdio server 暴露 set-target/build/flash/monitor，五大客户端实测——**与 Tessera 计划架构同构**。"AI agent 端到端开发嵌入式固件"的生态位在 2026-09 仍空置，但窗口正被产业从两侧（EDA agent 化 / 工具链 MCP 化）逼近。

## 2. 协议全景（2026-09 事实卡）

### 2.1 MCP（Model Context Protocol）——维持首选

- **治理**：2025-12-09 Anthropic 捐入 **AAIF**（Linux Foundation directed fund，OpenAI/Block 联合创立）；BDFL David Soria Parra / Den Delimarsky，多公司 core maintainers。Tier 1 SDK 月下载近 5 亿（TS/Python 各破 10 亿）。
- **版本链**：2024-11-05 → 2025-03-26 → 2025-06-18 → 2025-11-25 → **2026-07-28（当前）** → draft。2026-07-28 要点：① stateless 核心（删 initialize/Mcp-Session-Id，能力随 `_meta` 每请求携带；新增 `server/discover`）；② extensions 框架（Tasks / MCP Apps / Auth / **Skills over MCP**）；③ MRTR 取代服务器发起请求（elicitation 改为 `InputRequiredResult` 重试模式）；④ **弃用 Roots/Sampling/Logging**（约 2027-07 移除）与 RFC7591 动态注册；⑤ `subscriptions/listen` 统一通知流、结果缓存字段、OTel 传播、确定性工具列表。
- **官方 roadmap（2026-08-22，五优先域）**：① Agentic Messaging Primitives（Triggers/Events/webhook 推送；**Tasks（SEP-2663）走向并入核心**）；② HTTP-native 传输统一（**HTTP over stdio**——本地 server 也走 HTTP/2 over stdin/stdout；ETag 缓存）；③ **Agent 身份与企业安全**（DPoP、Workload Identity Federation、ID-JAG，对接 IETF WIMSE）；④ primitives 改进（tools/call 返回形状重设计、progressive discovery）；⑤ SDK DX（extension contract、spec+一致性测试生成 SDK 实验）。
- **Registry**：官方 registry.modelcontextprotocol.io 仍 **preview**（2025-09 起；收录量各口径 3k~9.6k）；发布 = `server.json` manifest + GitHub 流程。尽早上车可占名。
- **MCP Apps**（`io.modelcontextprotocol/ui` 扩展）：对话内沙箱 iframe UI，10+ 客户端支持（Claude/Copilot/Cursor/ChatGPT…）——若未来要图形看板可后置采用。**WebMCP** 是另一回事：W3C Web ML CG 提案，让**网页**向 agent 暴露工具（Chrome origin trial 2026-02），与本地/服务端 agent 场景无关。
- **客户端能力现实**：Streamable HTTP 普遍支持（SSE 弃用）；elicitation 仅 Claude Code/VS Code 成熟；sampling 已弃用；structuredContent 支持广但返回形状待重设计。
- **对 Tessera**：维持唯一对外合同；实现纪律见 §5。

### 2.2 A2A（Agent2Agent）——预留

- v0.3（2025-07）→ **v1.0.0（2026-03-12，首个 stable）** → v1.0.1（2026-05）；**2026-08-17 加入 AAIF**（与 MCP 同伞，官方 "open agentic stack"）。150+ 支持组织（2026-04）。
- **生产采用（可点名）**：Azure AI Foundry/Copilot Studio（2026-02 用 A2A **替换**旧 Connected Agents 机制）、AWS Bedrock AgentCore（2025-11 起，含跨云 A2A v1.0 实战）、Google Cloud ADK/Agent Engine、华为 Celia、腾讯微信。
- v1.0 要点：应用协议与传输绑定分离（JSON-RPC/gRPC/REST）、OAuth 现代化、签名 Agent Card、`tasks/list` 分页。**roadmap（2026-09-15）**：v1.1 增强、**BiDi 双向流**、**A2A CLI 与 coding harness 集成（#1929——正主动接入编码 agent 生态）**、elicitation/多轮 HITL、TCK 兼容性套件、六语言 SDK。
- **与 MCP 组合**：官方双方一致表述互补分层——"MCP = agent→tools（垂直），A2A = agent↔agent（水平）"。
- **对 Tessera**：兄弟域 agent（PCB/CAD）与固件 agent 的**对等**组合预留 A2A；若只是"被调用的工具"，MCP 面即够（见 §4.2 多 agent 主流模式）。

### 2.3 ACP——命名陷阱与现状（Q-16 对象）

- **两个 ACP，必须区分**：① **Zed/JetBrains 的 Agent Client Protocol**（编辑器↔coding agent，JSON-RPC over stdio）——Q-16 讨论的对象，**活跃且爆发**；② IBM 的 Agent Communication Protocol（agent↔agent）——**2025-08-29 已并入 A2A**，消亡；另有 Agentic Commerce Protocol 也叫 ACP（Google/Shopify 支付），无关。
- **Zed ACP 现状**：v1 stable；**v2 draft（2026-07-20）**——摆脱 turn 模型、任意时刻 session/update、结构化 diff、可扩展权限提示；无固定稳定时间表，官方建议生产别默认开 v2。治理 = Zed+JetBrains 双 BDFL（目标转独立基金会，无时间表）。
- **采用面**：客户端 **80+**（JetBrains AI Assistant 内建、Zed、Qt Creator、VS Code 系〔含 Cursor/Windsurf 经扩展〕、Neovim/Emacs、Obsidian、Jupyter、Telegram/Discord/Slack/飞书桥…）；agent 侧 30+（goose/OpenCode/Gemini/Codex/Copilot preview…；**Claude 经 Zed 官方 adapter；pi 经社区 pi-acp adapter**）。另有 ACP Registry（CDN JSON 分发）。

### 2.4 AGENTS.md——维持现状（已被制度确认）

OpenAI 2025-12-09 与 MCP 同日捐入 AAIF；20+ 工具读取（Codex/Gemini CLI/Cursor/Claude Code/Aider/Kiro…），60k+ 开源仓库在用；ZCode 亦读（本仓库即以 AGENTS.md 为会话入口——一手证据）。与 MCP 正交互补（静态指令 vs 动态工具面）。**Tessera 现行做法即是标准，无需变更。**

### 2.5 Agent Skills（SKILL.md 开放标准）——新增采纳建议

- Anthropic 原创，**2025-12-18 开放为独立标准**（agentskills.io + github.com/agentskills；Apache-2.0/CC-BY-4.0；未捐 AAIF，与 MCP 侧 "Skills over MCP" 扩展两条线合流中）。
- **45+ 工具支持**：Claude Code、ChatGPT & Codex、Cursor、Gemini CLI、Copilot、VS Code、Goose、OpenCode、**pi** 等；生态实践成潮（Laravel Boost 以 skills 官方分发、Google Cloud 官方 skills 仓库、Spring AI 内建）。
- **学术佐证（对 Tessera 最重要）**：**IoT-SkillsBench**（arXiv 2603.19583，2026-03）——3 平台/23 外设/42 任务/378 次真机实验：**精炼的人类专家 skills 使嵌入式 agent 跨平台成功率接近满分**；无 skills 或 LLM 自生成 skills 明显更差。
- **对 Tessera**：固件域知识（构建流程、军规、TSAP 格式、zenoh 命名空间、安全合同）打包为 SKILL.md 随 agent 分发 = 零成本顺主流，且解决"模型训练截止后不懂 Zephyr 4.4 钉版/私有协议"问题（Espressif 文档 MCP server 的同款动机）；pi 内核原生支持。

### 2.6 新兴协议判定表（真伪与势能）

| 名字 | 状态 | 一句话判断 |
|---|---|---|
| WebMCP | W3C Web ML CG 提案，Chrome origin trial | 网页向 agent 暴露工具；与本地/服务端 agent 无关 |
| MCP Apps | MCP 官方扩展，10+ 客户端 | 对话内 UI；Tessera 图形看板可后置采用 |
| ANP（Agent Network Protocol） | 社区+学术，无生产采用 | 去中心化愿景，势能弱 |
| Agent Protocol（agentprotocol.ai） | **已休眠**（dormant） | 先例已死 |
| IBM ACP | **2025-08 并入 A2A** | 消亡（注意与 Zed ACP 同名不同物） |
| AG-UI（CopilotKit） | 存在，未跨厂商铺开 | agent→前端事件流；自建 Web UI 才需要 |
| agentgateway | AAIF stack 成员（流量网关/控制面） | 未来多 agent 部署的入口治理层，watch |
| AP2（Agent Payments） | Google Cloud+PayPal 生产 | 支付域，与 Tessera 无关 |
| NIST AI Agent Standards | 政策框架（2026-02） | 背景噪音，暂无工程约束力 |
| Umwelt / OmniAgent / agentory | ⚠️未能核验为协议层标准 | 不存在或不构成标准 |

## 3. 前沿集成实践（客户端差异与最佳实践）

### 3.1 各客户端通道与兼容差异

- **Claude Code**：MCP 为首选通道（stdio/Streamable HTTP/OAuth/Channels 推送）；**插件 = 打包分发单元**（bundle skills+agents+hooks+MCP 配置，marketplace 机制）；工具输出 10k token 警告/25k 上限（server 可经 `_meta` 提至 50 万字符）；**工具调用超 2 分钟自动转后台 `/tasks`**。
- **Codex**：`config.toml [mcp_servers.*]`（stdio/HTTP+OAuth）；**默认请求超时 600s**；官方 skills 体系已上（2026）。
- **GitHub Copilot**：GitHub App 式 Extensions 已于 2025-11 **日落，官方转向 MCP**；VS Code/VS agent mode 用 `.vscode/mcp.json`。
- **Cursor/Windsurf**：stdio+HTTP+OAuth；Cursor 有逐工具启用/禁用 UI；Windsurf 已演变为 Devin Desktop。
- **必须绕开的差异清单**：Tasks extension（**全不支持**）；elicitation（仅 Claude Code/VS Code 成熟，跨客户端应建模为工具结构化返回——MRTR 的 `InputRequiredResult` 恰好形式化了该模式）；resources/prompts 支持参差（关键能力全部走 tools）；SSE（弃用）；工具数量克制（工具定义消耗上下文，影响选择准确率）。

### 3.2 长任务实践（对 DEC-34 的实现级细化）

- **Tasks extension 客户端采用为零**（Temporal Cornelia Davis 专文，2026-08：V1 要求客户端重状态管理，无一家实现；V2 刚随 2026-07-28 落地）。
- **2026 现实惯例**：工具**立即返回任务句柄 + 独立 status/log 查询工具（poll）**（FastMCP background tasks 即此模式的框架化）；Claude Code 2 分钟自动后台化兜底分钟级调用；Codex 600s 硬超时 → 立即返回是唯一安全模式。
- **面向未来**：内部任务模型对齐 Tasks V2 语义（`tasks/get`/`tasks/update`/`tasks/cancel`），官方普及后平滑切换。→ **Q-17②**。

### 3.3 "agent 作为工具"先例与分发

- **先例**：`claude mcp serve`（Claude Code 官方把自身跑成 stdio MCP server，"agents all the way down" 编排基座）；Vercel agent-browser（CLI 自带 `mcp` 子命令）；Nous Hermes Agent（导入他框架 agent 含其 MCP 配置与 skills）。
- **分发惯例（新 server 上线清单）**：npm 双分发包 + 各客户端一行配置片段（`claude mcp add`/`.mcp.json`/`config.toml`/`.cursor/mcp.json`）+ `server.json` 进官方 Registry（preview，尽早上车占名）+ 社区目录（Smithery/PulseMCP/glama）；Claude Code 侧可加发 plugin（bundle MCP+skills 进 marketplace）。

### 3.4 嵌入式工具链 agent 化先例（对 Tessera 直接相关）

- **ESP-IDF v6.0（Espressif，2026-04）= 厂商标杆**：`idf.py ai-cli --mcp` 启动 stdio server（构建进 idf.py），暴露 set-target/build/flash/monitor/项目状态，宣称五大客户端实测；另发**官方文档 MCP server**（`@espressif/mcp-server-docs`：search_docs/getting_started/latest_idf_version——解决模型训练截止后文档过时）；还有 ESP Private AI Agents Platform（2025-12）。**"原子工具 + 使用指引/文档"分层与 Tessera 计划同构。**
- **Zephyr**：树内有 **MCP server 库**（`subsys/net/lib/mcp`，spec 2025-11-25，`mcp_server_add_tool()`，含 LED 样例）——⚠️ 仅存在于 latest 文档（v4.4.0/v4.5.0 文档页 404），Tessera 钉 v4.4.0 **用不到**；登记为 Zephyr 升级观察项（与 DEC-19 持续跟进策略呼应）。社区 PC 侧已有 zephyr_mcp / mcp-zephyr-west（包装 west）。
- **调试器**：dbgprobe-mcp-server（有状态 debug probe）、J-Link MCP（VS Code Marketplace 正式条目）、ADI CodeFusion "AI Debug Assistant"。
- **ST/NXP**：ST 重心在 edge AI（STM32Cube.AI Studio），无官方 coding-agent 工具（第三方 CubeMX .ioc MCP server 存在）；NXP 明显落后。

## 4. 趋势与垂直先例

### 4.1 路线图交叉点（2026→2027 标准化方向）

① agent 间通信 → A2A 独占；② 长任务生命周期 → MCP Tasks（并入核心路线）与 A2A task lifecycle/BiDi 双线并行；③ **agent 身份与委托**（MCP 侧 DPoP/WIF/ID-JAG ↔ A2A 侧 W3C DID）= 最可能形成统一标准的新领域；④ 发现 → A2A Agent Card/注册表整合 + MCP progressive discovery。

### 4.2 多 agent 组合：2026 主流 = 层级编排

- **Anthropic 工程实证**（2025-06）：orchestrator-worker 在研究类评测 +90.2%，token ≈15×；**明确不适合**需共享上下文/强相互依赖的任务与"多数编码任务"。产品化形态 = Claude Code **Agent Teams**（同构会话集群 + 共享任务板，2026）。
- OpenAI Agents SDK：handoffs 与 agents-as-tools 双模式；LangGraph 1.x 定位"运行时层"而非通信协议；goose 有 subagents/flock。
- **共识**：编排器把子 agent 当工具（MCP 面）= 默认生产模式；**A2A 对等留给跨组织/跨供应商/长周期场景**；纯对等分布式非主流。
- **对 Tessera**：多域（固件/PCB/CAD）组合默认走"上层编排 + 域 agent 各自 MCP 面"；A2A 预留（Galatea 规模/跨主体时启用）。

### 4.3 硬件域 agent 化（北极星可行性证据）

- **Quilter Project Speedrun**（2026-04~08）：AI 物理驱动布局布线复刻 NXP i.MX8M Mini（SOM+底板各 8 层），Sierra 制造 10 套**全部一次点亮**、Linux 跑 3 个月；布局 428 报价工时 → 38.5 人时。**关键缺口：固件 bring-up（Part 5）纯人工完成**；58 条 DFM/DFA 教训中 48 条来自人工环节（文档/库/BOM）。
- **EDA/CAD 域 MCP 化已成事实**：KiCad 多个 MCP server（含 kicad-mcp-pro，Adafruit 报道）；OpenSCAD 专用 MCP；FreeCAD 原生 AI workbench；Siemens **Fuse** EDA AI Agent（2026-03，2026-07 升级 self-verifying workflows）；flux.ai/JITX/DeepPCB 各路线并存。
- **机器人侧就绪**：Open Robotics 官方背书的 **native ROS 2 MCP server**（2026-06）——Galatea 接入层已备。
- **工业界共识口径**：Gartner 2030 制造业预测用 **"semi-autonomous + 人授权"**（半自治）；AAS+OPC UA+LLM 学术架构强制每个机器动作经人授权——与 Tessera "Agent 无豁免"合同同构。**"AI 全自动自我制造"级别公开案例不存在（self-replicating 仍属理论），但全部单项构件已存在、无人完成组合。**

### 4.4 嵌入式固件 AI 自动化现状（生态位判断)

- 最接近的学术工作 = IoT-SkillsBench（§2.5）；最接近的厂商实践 = Espressif《Developing a Zephyr IoT app with AI》（2026-06：spec→plan→execute→commit→test 循环 + journal/git 留痕——与 Tessera 纪律几乎同构）。
- Zephyr 社区态度：官方文档站集成 Kapa.ai；贡献指南含 AI 使用指引（欢迎但须负责披露）；2026-09 开始防御低质量 AI 贡献。无排斥。
- **结论：**"AI agent 端到端全自动开发嵌入式固件（需求→设计→编码→HIL 测试→部署）"的公开成熟项目不存在——Tessera 定位的生态位空置，窗口正被两侧逼近。

## 5. Tessera 交互栈建议（R4 结论）

```text
┌─ 人类 ──────────────────────────────────────────────┐
│  ACP（Zed/JetBrains，v1）· IDE/编辑器人机面 → Q-16    │
├─ 仓库指令 ─────────────────────────────────────────┤
│  AGENTS.md（AAIF 标准，已实践，维持）                 │
├─ AI 调用方（ZCode/Claude Code/Cursor/Copilot/…）─────┤
│  MCP（唯一对外合同，DEC-12 维持）                     │
│   · stdio 起步 + Streamable HTTP 预留                │
│   · stateless-first（对齐 2026-07-28）+             │
│     兼容基线 2025-11-25 语义回归                      │
│   · 长任务 = 自定义句柄+轮询工具（对齐 Tasks V2 语义）│
│   · 规避：Roots/Sampling/Logging/SSE/elicitation 依赖│
│   · 双层工具面（DEC-34）+ 输出大小/超时纪律           │
├─ 能力知识分发 ──────────────────────────────────────┤
│  Agent Skills（SKILL.md 开放标准，pi 原生支持）       │
│   · V1 附最小固件域 skill 集（构建/军规/TSAP/命名空间）│
│   · 文档型知识可选配套 docs MCP server（Espressif 先例）│
├─ 未来多域组合（固件/PCB/CAD，DEC-33 北极星）─────────┤
│  默认：上层编排 + 域 agent 各自 MCP 面（agents-as-tools）│
│  预留：A2A v1.0（跨主体/长周期对等，如 Galatea 规模）  │
│  watch：agentgateway（部署治理）、MCP roadmap（身份/委托）│
└──────────────────────────────────────────────────────┘
```

## 6. 对已裁 DEC 的影响

- **DEC-12（MCP 形态）**：维持，无需修订——R4 证实其为最前沿选择而非过时方案。
- **DEC-34（双层工具面）**：核心语义不变（双层 + 长任务句柄化）；**实现机制细化**（Q-17②）：不依赖 Tasks extension（客户端采用为零），落地为自定义句柄+轮询工具，语义对齐 Tasks V2 以备平滑迁移。
- **Q-16（ACP）**：证据补强后重呈（客户端 80+、pi 社区 adapter 现成；同时澄清与 IBM ACP 的同名陷阱）。

## 7. 呈递（decisions.md §二）

- **Q-17（新登记）**：交互栈确认 4 子项——①MCP 维持 + 实现纪律（stateless-first/兼容基线/弃用规避）；②长任务机制细化（修订 DEC-34 实现细节）；③Agent Skills 作为领域能力分发；④多域组合模式（编排默认 + A2A 预留 + AGENTS.md 维持）。
- **Q-16（重呈）**：ACP 二级人机接口，选项与建议不变（A：V1 不做仅预留），补 R4 证据。

## 8. 来源清单（关键项）

- MCP：specification/2026-07-28 changelog；development/roadmap（2026-08-22）；blog.modelcontextprotocol.io（2026-07-28、Registry preview 2025-09-08）；extensions/apps；registry/about；Cloudflare MCP v2 解读；Anthropic 捐赠公告；AAIF（aaif.io）。
- A2A：github.com/a2aproject/A2A（releases v1.0.0/v1.0.1、docs/roadmap.md 2026-09-15）；a2a-protocol.org；LF 150+ 组织新闻稿（2026-04）；aaif.io/blog/a2a-joins-aaif（2026-08-17）；Azure Foundry / AWS AgentCore 文档与实战。
- ACP：agentclientprotocol.com（v2 draft 公告 2026-07-20、clients/agents/registry/governance）；IBM ACP 并入 A2A 公告（lfaidata.foundation 2025-08-29）。
- AGENTS.md / Skills：OpenAI co-founds AAIF 公告（2025-12-09）；agentskills.io；VentureBeat（2025-12-18 开放）；Simon Willison（Codex 支持 skills）；Spring AI/Laravel Boost 实践。
- 客户端实践：code.claude.com/docs（mcp/plugins）；developers.openai.com/codex/mcp；github.blog（Copilot Extensions 日落 2025-11）；cursor.com；devin.ai（Wave 11）；modelcontextprotocol.info/clients；Temporal 博文（Tasks 无客户端支持，2026-08）。
- 嵌入式先例：developer.espressif.com（Tools MCP 2026-04、Docs MCP 2026-04、Private AI Agents 2025-12、Zephyr+AI 2026-06）；docs.zephyrproject.org latest MCP API（4.4/4.5 404 核验）；J-Link Marketplace；ADI AI Debug Assistant。
- 趋势/垂直：Anthropic multi-agent 工程博文（2025-06）；code.claude.com Agent Teams；quilter.ai Project Speedrun 系列（2026-04~08）+ github.com/xjordanx/speedrun；Siemens Fuse（news.siemens.com 2026-07）；KiCad MCP（forum.kicad.info 2026-01、kicad-mcp-pro/Adafruit 2026-04）；OpenSCAD MCP（skywork.ai）；FreeCAD AI workbench（forum 2026-02）；Open Robotics native ROS 2 MCP（discourse 2026-06）；robotmcp/ros-mcp-server；IoT-SkillsBench（arXiv 2603.19583 + github.com/iot-agent/iot-skillsbench）；Gartner Manufacturing Predictions 2026（2026-01）；MDPI AAS-OPC UA-LLM（2026）。

## 修订记录

- v1.0 · 2026-09-22：初版。3 路并行调研（协议全景 / 前沿集成实践 / 路线图+多 agent+垂直先例）汇总成文；呈递 Q-17（新登记）+ Q-16（重呈）。
- v1.0.1 · 2026-09-22：裁决登记——Q-16 → **DEC-35**（ACP：V1 不做仅预留）、Q-17 → **DEC-36**（四子项全采纳 + A2A 预留显式记录）。Agent 轨道 research 阶段落定。
- v1.0.2 · 2026-09-22：DEC-37（Q-18：C 全 Python）修订标注——§5 图中 agent 内核 pi 与"pi 原生 skills"表述由 PydanticAI + 自建 skill loader 替代（R5 §3 适配判定），MCP 门面 SDK = FastMCP（Python）；分层栈与各层协议选择不变。
