# R3 · Tessera Agent 基座选型调研（agent 运行时 / 框架 / MCP 封装）

> **状态**：v1.0.2 · 2026-09-22 · research 阶段产出（阶段白名单内）· **Q-14/Q-15 已裁 → DEC-33/34**（pi 基座 + 多域预留北极星；双层 MCP 工具面）；Q-16（ACP）补呈详解后仍待裁（`decisions.md` §二）。§4.6 长任务结论已被 R4 实现级细化（Tasks extension 客户端采用为零 → 自定义句柄+轮询），以 R4 为准。
> **任务来源**：owner 2026-09-22 指令——"我想请你先进行zephyr AI开发设计测试嵌入式程序的Agent的research和design工作，该Agent核心基于Opencode或PI Agent或者其他现有Agent或框架为基础进行设计，该Agent也要能够被封装为MCP被其他Agent调用，请你先进行一轮Resarch收集信息，调研我们选择什么方案是最适合我们的。"
> **核验方式**：3 个并行调研子代理经 WebSearch / WebFetch / GitHub API 于 **2026-09-22 实查**（非记忆复述）；关键来源清单见 §8，未能核验项以 ⚠️ 标注。

## 0. 背景（自包含）

Tessera 需要一个 **PC 侧 AI Agent**（DEC-12）：以 MCP server 形态封装"模块 API + 模拟器 + 构建工具链"；能力链 = 需求分析 → 软件设计 → 编程开发 → 模拟测试 → 部署；产出 = 业务 APP **与** 硬件配置（DEC-11）；模拟深度 V1 = native_sim + 外设桩（DEC-13）；LLM 由用户自选；宿主仅 Linux（DEC-32，修订 DEC-20）。Agent 产物无豁免权——与人类产物走相同的签名/权限/安全合同检查链（FOUNDING_PROMPT §6）。

owner 本次指令增加两项约束：① **Agent 核心不自研循环**，基于现有 agent/框架（点名 OpenCode、pi）；② **必须可封装为 MCP server 被其他 Agent 调用**。

本报告解决"基座选什么"（→ Q-14）与两个随生设计决策（MCP 工具面形态 → Q-15；ACP 二级接口 → Q-16）。Agent 的设计文档（HLD/LLD）待裁决后进行。

**术语（通俗）**：

- **agent 基座**：现成的"agent 运行时"——LLM 对话循环、工具调用、会话管理（常含文件编辑工具）都已做好；我们只挂 Tessera 专用工具（west 构建 / twister / 模拟器 / TSAP 打包签名 / 部署）并写封装层。
- **嵌入方式两型**：**库**（agent 循环跑在我们自己进程里，单进程）vs **服务/子进程**（基座独立运行，我们经 HTTP/JSON 协议驱动，两进程）。库 = 封装层薄、控制力强；服务 = 隔离好但封装厚。
- **MCP 双向**：作为 **client**（agent 去用别人的 MCP 工具）vs 作为 **server**（别人经 MCP 调用我们）。我们要的"被封装为 MCP"= server 侧。**没有任何候选原生自带 server 侧**——都需用官方 MCP SDK 自建外壳，这是各方案共同的固定工作量，差异在外壳与核心之间隔了几层。

## 1. 需求基线（评估准则）

| # | 准则 | 内容 | 出处 |
|---|---|---|---|
| 硬-1 | LLM 提供者无关 | OpenAI/Anthropic/Google/本地（Ollama、llama.cpp）等可换，不锁定单一厂商 | DEC-12 |
| 硬-2 | Linux 宿主 | 唯一支持平台 | DEC-32 |
| 硬-3 | 可嵌入 | 库（进程内）或服务/子进程驱动，须写明形态 | owner 2026-09-22 指令 |
| 硬-4 | 许可证宽松 | MIT / Apache-2.0 | 与 DEC-16 同精神 |
| 工-1 | 自定义工具机制 | 挂 Tessera 工具集（build/simulate/package/sign/deploy/provision…） | DEC-11/12 |
| 工-2 | 工具面控制 | 可禁用/精选内置工具；调用钩子可阻断——"Agent 无豁免"的强制落点 | FOUNDING_PROMPT §6 |
| 工-3 | MCP 双向 | client 侧（消费外部工具）+ server 侧（对外合同，自建外壳） | DEC-12 |
| 工-4 | 会话/重放 | 会话可导出/可纯内存——确定性合同（安全合同 9）在 Agent 侧的同构延伸 | AGENTS.md §6-9 |
| 工-5 | 活跃度/治理 | 维护主体、bus factor、版本纪律 | 工程常识 |
| 工-6 | 语言生态 | 与固件 Python 工具链（west/twister/pytest）的衔接成本 | docs/dev-environment.md |

## 2. 生态重大变化（2026-09-22 实查；修正一年前的旧认知）

1. **OpenCode 迁库**：sst/opencode → **anomalyco/opencode**（SST 团队重组为 Anomaly 公司，GitHub transfer 自动重定向，无社区分裂）。
2. **pi 迁库并公司化**：badlogic/pi-mono → **earendil-works/pi**；npm scope @mariozechner/* → **@earendil-works/***；Mario Zechner 创立 Earendil Inc.，**Armin Ronacher（mitsuhiko）已成为第二号贡献者**（715 commits），并将 pi 用作其 OpenClaw 项目基座。
3. **MCP 治理转移**：2025-12-09 Anthropic 将 MCP 捐给 Linux Foundation 旗下 **Agentic AI Foundation（AAIF）**（与 Block、OpenAI 共创）；中立治理，MCP 作为对外合同更稳。
4. **MCP spec 当前版 = 2026-07-28**：协议核心 stateless 化（移除会话握手）、**Tasks extension 转正**（长任务句柄+轮询+订阅）、正式 extensions 框架；官方 TS SDK 已重构为 2.x scoped 包（2026-07-27），Python SDK 2.2.0。
5. **长任务有了官方答案**：Tasks extension——`tools/call` 立即返回任务句柄（taskId/ttlMs/pollIntervalMs），客户端轮询或订阅通知。对分钟级的固件构建/仿真/部署工具直接适用（实测各家 MCP 客户端超时仅 7~60s，长工具必须异步化）。
6. **Amazon Q Developer CLI 已归档**（2025-12 更名 Kiro CLI，原仓库停止维护）——排除名单+1。

## 3. 候选全景

| 候选 | 定位 | 许可证 | 最新版（核验日期） | 嵌入形态 | 提供者无关 | 自身暴露为 MCP server | 判定 |
|---|---|---|---|---|---|---|---|
| **pi**（earendil-works/pi） | agent 工具箱（库+CLI） | MIT | v0.87.0（2026-09-21） | **库（进程内）** + RPC 子进程 | ✅（30+，含本地 llama.cpp 原生） | ✗（需自建，可单进程内完成） | **入围 A（推荐）** |
| **OpenCode**（anomalyco/opencode） | 全功能 coding agent | MIT | v1.18.32（2026-09-21） | 仅服务/子进程（HTTP REST+SSE） | ✅（75+） | ✗（官方仅 `opencode acp`；需自建跨进程桥） | **入围 B（备选）** |
| **goose**（block/goose） | MCP-first agent | Apache-2.0 | v1.29.1（2026-09） | daemon + headless CLI + ACP；Rust crate 无 API 稳定承诺 | ✅（最强：15+，Ollama/LM Studio/llama.cpp） | ⚠️未能核验 | 入围 C |
| Codex CLI（openai/codex） | coding agent | Apache-2.0 | 0.157.0-alpha（2026-09-22） | app-server JSON-RPC（内部协议，无稳定承诺） | 🟡 配置层可用（ollama/lmstudio/model_providers） | ✗ | 备查 |
| Claude Agent SDK | SDK | SDK 层 MIT / **运行时闭源二进制** | 0.3.278（2026-09-19） | 库（实质 spawn 闭源二进制） | ❌ 仅 Anthropic 协议模型 | CLI 层有 `claude mcp serve`（中等置信度） | **出局** |
| Gemini CLI（google-gemini） | coding agent | Apache-2.0 | v0.16.3（2026-09-19） | 库（@google/gemini-cli-core）+ headless | ❌ 锁 Google 系 | ✗ | **出局** |
| Crush（charmbracelet） | coding agent | **FSL-1.1-MIT**（竞争限制） | v0.95.0（2026-09） | CLI + serve（内部架构） | ✅ | ✗ | **出局（许可证）** |
| Aider（Aider-AI） | 结对编辑器 | Apache-2.0 | v0.86.2（2026-02，**此后停更**） | Python 弱库（无稳定性契约） | ✅（LiteLLM） | ✗（无任何 MCP） | **出局** |
| Amazon Q CLI（aws） | coding agent | MIT | 2025.12.17（**已归档**） | 仅 CLI | ❌ 锁 Amazon | ✗ | **出局** |

框架线（不基于成品 agent、自建循环的底座）：Vercel AI SDK v7 / PydanticAI v2 / OpenAI Agents SDK / mcp-agent（**停更**，排除）/ LangGraph（对我们场景过重）——见 §4.5。

## 4. 重点候选事实卡

### 4.1 pi（earendil-works/pi）——推荐核心

- **是什么**："AI agent toolkit: unified LLM API, agent loop, TUI, coding agent CLI"。设计取向 = 最小可组合件，官方明确支持四种运行模式：interactive / print-JSON / **RPC（子进程 JSONL）** / **SDK（嵌入你自己的 app）**。
- **治理/活跃度**：Earendil Inc.（Mario Zechner）；108k stars；v0.87.0（2026-09-21 发布，查询当日仍有提交）；贡献者日常多作者（Mario 3745 / Armin Ronacher 715 / …），但 Mario 仍占 ~70% commits。生态：pi.dev 包注册表 5,548 个包。
- **许可证**：MIT（LICENSE 原文核验）。
- **包清单**（monorepo，npm scope @earendil-works/*）：`pi-coding-agent`（CLI+**内含 SDK**）、`pi-agent-core`（Agent 类+工具执行+状态）、`pi-ai`（统一多 provider LLM API）、`pi-tui`、`pi-durable`（持久会话/任务）、`chord`（应用组合运行时）、`pi-client`/`pi-protocol`/`pi-server`（**experimental**，framed CBOR 远程 session）。注意：官方包清单中已**无** pi-acp/pi-mcp（见下）。
- **嵌入 API（对工-1/工-2 关键）**：`createAgentSession({model, customTools, sessionManager, systemPromptOverride, …})` → `prompt()/steer()/abort()/subscribe()`；更底层 `pi-agent-core` 的 `Agent` 类带 **`beforeToolCall`/`afterToolCall` 钩子（可阻断、可原地改写工具参数）**——"Agent 无豁免"检查链的落点。
- **内置工具与控制**：read/write/edit/bash/grep/find/ls/powershell 共 8 个，**默认只启用 4 个**（read/write/edit/bash）；`tools:[...]` 精确选择、`noTools:"all"|"builtin"`、`excludeTools`；自定义工具 `defineTool({name, description, schema, execute})`；内置工具工厂可单独复用/替换。
- **提供者**：API-key 一大批（Anthropic/OpenAI/Azure/Gemini/Vertex/Bedrock/DeepSeek/Groq/OpenRouter/ZAI 等）+ 订阅登录（Claude Pro/Max、ChatGPT、Copilot）+ **llama.cpp router server 原生支持**；自定义 endpoint 走 `~/.pi/agent/models.json`（OpenAI/Anthropic/Google 兼容 API 均可）。
- **会话/重放（对工-4 关键）**：session = JSONL 文件、树结构（id/parentId 原地分支）、格式 v1→v3 自动迁移；**`SessionManager.inMemory()` 可完全无持久化跑纯内存**——确定性/重放测试友好。
- **MCP**：官方核心**不含** MCP（设计哲学：用自身 extension/tools API，MCP 交生态）。client 侧用社区 `pi-mcp-adapter`（pi 生态下载量第一，约 972K/月）。server 侧（我们的主需求）= 我们自己进程内 new agent 循环 + 官方 MCP SDK 直接挂——**单进程完成，无跨进程跳数**。
- **ACP**：官方 pi-acp 已移出 monorepo；现行 = 社区适配器（svkozak/pi-acp 等，桥接 `pi --mode rpc`），Zed/agentclientprotocol.com 官方收录。
- **风险**：① 版本 0.x，API/格式仍有 churn（session 已到 v3、npm scope 刚迁移；⚠️旧 scope @mariozechner/* 是否继续发版未核验）；② 无内建权限系统（审批需我们在封装层自建——钩子机制够用）；③ Mario 主导度高（bus factor 已因 Armin 加入而缓解）；④ 贡献策略特殊（新贡献者 PR 默认自动关闭、维护者每日审阅——对下游使用者无直接影响）。

### 4.2 OpenCode（anomalyco/opencode）——备选核心

- **是什么**：当前最流行的开源 coding agent（自报 208k stars/950 contributors）；公司 Anomaly（前 SST）驱动，商业化线 = Zen/Go/Enterprise（开源核心 MIT 不变）。
- **活跃度**：v1.18.32（2026-09-21），约每周 1–2 个 release，查询当日仍在提交。
- **架构**：严格 client/server 分离——TUI 只是 server 的一个 client；`opencode serve` = headless HTTP REST 服务器（默认 127.0.0.1:4096，OpenAPI 3.1 spec 挂 `/doc`，事件流走 SSE）。**官方 SDK 仅 JS/TS**（@opencode-ai/sdk，类型由 OpenAPI spec 生成，可自动拉起 server）。**无进程内库模式**——agent 核心永远跑在 opencode server 进程里。
- **插件**：JS/TS 模块，可**注册自定义工具**（tool() helper）、订阅事件（session.idle、tool.execute.before/after 等）、拦截 compaction 提示词。
- **提供者**：基于 Vercel AI SDK + Models.dev，75+ providers；自定义 OpenAI-compatible endpoint（baseURL+models 映射）；Ollama/llama.cpp/LM Studio 官方文档直接给配置。
- **MCP**：client 一等公民（stdio local + remote HTTP/SSE 含自动 OAuth、动态添加 server 的 API）。**自身暴露为 MCP server：无官方支持**——最接近的原生能力是 `opencode acp`（把 OpenCode 作为 ACP server）。要做 MCP server 需自建桥（社区已有同类 SDK 包装先例）。
- **权限**：审批式权限引擎（allow/ask/deny 三态、per-tool 与输入模式匹配、ask 可程序化应答）——比 pi 完善，是它的显著优势。
- **风险**：① 子进程/服务驱动 = 封装层厚（跨进程 HTTP + SSE，为一个通用 server 的体量买单）；② 公司商业节奏驱动产品快速演进（SDK 已到 /v2），API 漂移压力大于 pi；③ 历史事件：2025 年曾因逆向 Claude Code 内部 API 被 Anthropic 法律施压移除集成（已了结，说明其对第三方协议边界 historically 激进）。

### 4.3 goose（block/goose）——入围 C

- Apache-2.0；Block 公司驱动；Rust workspace + Tauri 桌面端；v1.29.1（2026-09），月度 minor 高频迭代。
- 嵌入：① `goosed` daemon；② `goose run --headless`（官方 headless，面向 CI/脚本/subagent）；③ **ACP 为所有客户端主接口**（Zed/JetBrains/Neovim 等可驱动）；④ Rust crate 库形态存在但 **crates.io 公共 API 稳定性 ⚠️未核验**。
- 提供者面**最强**：goose 官方 + Claude Code + Codex CLI + Custom OpenAI-compatible 四类 15+ 家；本地三层（Ollama / LM Studio / llama.cpp + HuggingFace 模型管理）。
- MCP：client ✅✅（**extensions 体系 = MCP server**，内置 20+、社区 100+，基于 Rust 官方 rmcp SDK）；**自身作为 MCP server ⚠️未能核验**（确认的对外通道只有 ACP/daemon/headless）。
- 自定义工具 = 把工具做成 MCP server 装为 extension——与我们"反正要自建 MCP server"的路线天然咬合。
- 风险：嵌入协议（daemon/ACP）无稳定性承诺；Rust 工具链对我们（Python/TS 生态）是额外负担；版本高速迭代。

### 4.4 出局组速记（硬伤 → 出处见 §8）

- **Claude Agent SDK**：工具/hook/子代理机制是标杆，但**运行时为闭源 Claude Code 二进制**（npm 平台二进制分发，Anthropic 商业条款）+ **仅 Anthropic 协议模型**（API/Bedrock/Vertex；非 Anthropic 只能靠 LiteLLM 类代理翻译）——踩中硬-1 与硬-4 两条红线。
- **Gemini CLI**：core 库+headless 双通道、嵌入文档七者最佳，但**锁 Google 系模型**（不支持任意 OpenAI-compatible base URL）——踩中硬-1。
- **Crush（Charm）**：技术形态接近（提供者强、MCP client、非交互模式），但许可证 **FSL-1.1-MIT**（源码可用、禁止竞争性使用，2 年后才转 MIT）——不满足硬-4。
- **Aider**：Apache-2.0 + LiteLLM 100+ 模型达标，但架构是"git 结对编辑器"非 agent 运行时（无自定义工具面/权限/子代理）、**2026-02 起停更**、无 MCP——基座要素缺失。
- **Amazon Q Developer CLI**：仓库已归档（2025-12 更名 Kiro CLI）、锁 Amazon 模型——双杀。

### 4.5 自建框架线（若不走成品 agent）

| 框架 | 版本（日期） | 许可 | 语言 | MCP client | agent 嵌入 MCP server | 判定 |
|---|---|---|---|---|---|---|
| Vercel AI SDK | v7（2026-06-25） | Apache-2.0 | TS | ✅ 稳定（@ai-sdk/mcp 2.x，含 elicitation/工具漂移检测） | ❌ 无原语 | 可行但需自建会话/编辑工具/上下文 |
| PydanticAI | v2.47.0（v1=2025-10） | MIT | Python | ✅ | ✅ **唯一官方支持 agent 双向参与 MCP**（与 FastMCP 协同） | 自建线最佳（方案 D） |
| OpenAI Agents SDK | 0.22.3（仍 0.x） | MIT | Python | ✅ | ❌ | OpenAI 优先，次选 |
| mcp-agent（lastmile） | 0.0.21（2025-05） | Apache-2.0 | Python | ✅ | 部分 | **停更 8 个月**，排除 |
| LangGraph | 1.0（2025-10） | MIT | Python | 适配器 | 适配器 | 图编排器，对单 agent 工具循环过重 |

自建线的共同代价：会话管理、文件编辑工具、上下文压缩策略都要自己写——这正是"基座"要省掉的工作，与 owner 指令（基于现有 agent）相悖，仅作对照保留。

### 4.6 协议层现状

- **MCP**：治权已转 Linux Foundation AAIF（中立）；spec 当前版 **2026-07-28**（stateless 核心、Tasks 转正、extensions 框架；Roots/Sampling/Logging 弃用）。SDK：**官方 TS 2.x scoped 包**（@modelcontextprotocol/{core,client,server,…}，2026-07-27 起）、Python 2.2.0；FastMCP Python v4（PrefectHQ）、FastMCP TS 4.x（punkpeye）。客户端覆盖：Claude Code/Desktop、Cursor、Windsurf、VS Code、Codex、Zed 全支持——"写一次 server 处处可用"成立。
- **长任务**：**Tasks extension**（io.modelcontextprotocol/tasks）——工具调用立即返回 `{resultType:"task", taskId, ttlMs, pollIntervalMs}`；`tasks/get` 幂等轮询、`tasks/update` 补输入、`tasks/cancel` 协作取消、`notifications/tasks` 订阅推送；能力协商渐进增强（旧客户端自动走同步阻塞路径）。**Tessera 的构建/仿真/部署类工具（分钟级）必须按此设计**（宿主客户端超时实测 7~60s）。
- **ACP（Agent Client Protocol）**：Zed+JetBrains 共治（BDFL 双 lead，目标转独立基金会），v1 stable / v2 draft；40+ agent 支持（goose/OpenCode/Gemini 原生；pi/Claude Code/Codex 经适配器）；客户端含 Zed 内置、JetBrains 官方、VS Code/Neovim 社区。定位与 MCP 互补（ACP=客户端↔agent 的编辑器集成；MCP=agent↔工具）。→ Q-16。
- **A2A（Agent2Agent）**：Google 捐 Linux Foundation，spec v1.0.1（2026-05-28），150+ 组织。定位 = 对等 agent 协作，与 MCP 互补。我们单体固件 Agent 无多 agent 对等需求，**仅 watch item**，不立项。

## 5. 对比矩阵（核心候选 × 准则）

| 准则 | **A：pi（库）** | B：OpenCode（服务） | C：goose（daemon/headless） | D：PydanticAI 自建 |
|---|---|---|---|---|
| 硬-1 提供者无关 | ✅ 30+ + models.json + llama.cpp 原生 | ✅ 75+ + 自定义 endpoint | ✅✅ 15+ 含三层本地 | ✅（经 provider 抽象） |
| 硬-2 Linux | ✅ | ✅ | ✅ | ✅ |
| 硬-3 嵌入形态 | ✅✅ **进程内库**（+RPC 子进程备选） | 🟡 仅子进程/服务（HTTP+SSE） | 🟡 daemon/headless/ACP；crate 无承诺 | ✅ 库（但全部自建） |
| 硬-4 许可证 | MIT | MIT | Apache-2.0 | MIT |
| 工-1 自定义工具 | ✅✅ defineTool + 工具工厂复用 | ✅ 插件 tool() | ✅（做成 MCP extension） | ✅（自写） |
| 工-2 工具面控制 | ✅✅ 默认仅 4 工具、精确增删、beforeToolCall 可阻断改写 | ✅ 权限引擎 allow/ask/deny（最完善） | 🟡 extension 粒度 | ✅（全自控） |
| 工-3 MCP | client=社区适配器；server=**单进程自建（最薄）** | client=原生一等；server=跨进程桥 | client=原生一等；server=⚠️未核验 | client=原生；server=官方姿势（FastMCP） |
| 工-4 会话/重放 | ✅✅ JSONL 树 + inMemory() 纯内存 | ✅ server 内置会话/分享 | 🟡 会话在 daemon 内 | 🔧 自建 |
| 工-5 治理/活跃 | Earendil Inc. + Armin；0.x churn | Anomaly 公司；1.x 高频演进 | Block；1.x 高频演进 | Pydantic 公司；2.x |
| 工-6 语言 | TypeScript（Node≥22） | TypeScript | Rust（桥可 TS） | Python |
| Agent 无豁免落点 | beforeToolCall 钩子（我们写） | 权限引擎+插件钩子 | extension 边界 | 工具实现内部 |
| 主要风险 | 0.x API 漂移；无内建权限 | 子进程封装厚；商业节奏 | crate 无 API 承诺；Rust 生态 | 自建工作量=基座本要省掉的 |

## 6. 方案组合

### 方案 A（推荐）：pi 库内核 + 官方 MCP TS SDK 门面 + 自研 Tessera 工具集（TypeScript）

```text
[MCP 客户端：ZCode / Claude Code / Cursor / goose / …]   ← 人类也可直接用 MCP 客户端调原子工具
        │  MCP（stdio 起步；Streamable HTTP 预留；长工具走 Tasks extension）
┌───────▼─────────────────────────────────────────┐
│ tessera-agent（自研，单进程，Node ≥22，Linux）      │
│  · MCP 门面：官方 TS SDK 2.x scoped 包             │
│  · 会话编排 / 任务管理（Tasks）/ 审计日志             │
│  · agent 核心：pi 库（createAgentSession）          │
│     ├ 内置工具精选（默认 read/write/edit/bash）      │
│     ├ Tessera 工具（defineTool）：                  │
│     │   workspace/build/simulate/package/sign/     │
│     │   deploy/provision/query/get-audit…          │
│     │   └ spawn 子进程调 Python 工具链：             │
│     │      west build / twister / pytest / 模拟器    │
│     └ beforeToolCall 钩子 = "Agent 无豁免"强制检查点 │
│  · （可选后补）pi-mcp-adapter：agent 消费外部 MCP 工具 │
└─────────────────────────────────────────────────┘
```

要点：单进程 = 封装层最薄；工具面全可控（内置只开 4 个 + 自定义工具 + 可阻断钩子）；会话可纯内存/JSONL 导出（重放审计）；提供者无关达标；West/twister/pytest 等 Python 资产经子进程复用，不重写。风险缓解：pi 钉精确版本 + 我们定义薄抽象缝（AgentCore 接口：prompt/tools/hooks/session），核心可换（→OpenCode 服务模式或 goose），MIT 允许极端时 fork 自维护。

### 方案 B：OpenCode 服务内核（`opencode serve` + @opencode-ai/sdk + MCP 桥）

双进程：MCP 门面进程经 HTTP/SSE 驱动 opencode server。优势：1.x 成熟度、权限引擎现成、社区最大。代价：封装层厚、为通用交互 server 的体量买单、API 随商业节奏演进快。

### 方案 C：goose 内核（headless/daemon 驱动）

提供者面最强、extensions=MCP 的哲学与我们咬合。代价：Rust、嵌入协议无稳定性承诺；更适合作为"外部成品 agent 直连 Tessera 原子工具"的**客户端**（与 A 不冲突，是 Q-15 原子层的自然用户）。

### 方案 D：PydanticAI + FastMCP 自建（Python）

唯一官方支持 agent 双向 MCP 的框架线；但会话/编辑工具/上下文全自建，违背 owner"基于现有 agent"指令精神；且 Python 侧 pi/OpenCode 的成熟工具链享受不到。

## 7. 结论与建议（→ decisions.md Q-14/Q-15/Q-16）

1. **基座**：建议方案 A（pi）；B（OpenCode）为第一备选；C/D 保留对照；其余候选硬伤出局（§4.4）。
2. **MCP 工具面**：建议双层——原子工具必开（"Agent 无豁免"+可测性+人类可直接用），高层任务工具 V1 先 2-3 个（develop_app 等）；长工具统一按 Tasks extension 设计 + 同步 fallback。
3. **ACP**：V1 不做，架构预留（MCP 门面与 agent 核心解耦后补成本低）；A2A 维持 watch item。
4. 上述三项均属 review 门 ①（选型）/ Agent 特有门（MCP 工具面），依呈递格式全文登记 decisions.md 待裁。

## 8. 来源清单（关键项）

- OpenCode：opencode.ai（docs: server/sdk/cli/plugins/mcp-servers/providers/permissions）；github.com/anomalyco/opencode（LICENSE=MIT、releases v1.18.32/2026-09-21、API 元数据）；sst→anomalyco 迁移佐证（Pinggy 2026-08、Firecrawl 2026-08、arcbjorn 2026-07）。
- pi：github.com/earendil-works/pi（LICENSE=MIT、packages/ 实查、README 四模式、docs/sdk.md、docs/rpc.md、docs/session-format.md、docs/extensions.md）；pi.dev/packages（5,548 包）；pi-mcp-adapter 下载量；svkozak/pi-acp；zed.dev 与 agentclientprotocol.com 收录页；Armin Ronacher 博客（lucumr.pocoo.org，2026-01）；Pragmatic Engineer（2026-04，OpenClaw 基座报道）。
- goose：github.com/block/goose（README=Apache-2.0、releases v1.29.1）；goose-docs.ai（headless/extensions）；ACP 主接口 issue #7309；JetBrains ACP 公告。
- 出局组：anthropics/claude-agent-sdk-typescript + npm（0.3.278、平台二进制、仅 Anthropic 协议）；code.claude.com CLI reference（claude mcp serve，中等置信度）；github.com/google-gemini/gemini-cli（v0.16.3、锁 Google）；github.com/charmbracelet/crush（FSL-1.1-MIT）；Aider-AI/aider（v0.86.2=2026-02 后停更）；aws/amazon-q-developer-cli（已归档）。
- MCP/协议：blog.modelcontextprotocol.io（2026-07-28 spec、TS SDK 2.0 scoped、roadmap）；tasks.extensions.modelcontextprotocol.io（Tasks spec）；anthropic.com（MCP 捐 AAIF）；hidekazu-konishi.com（spec 版本时间线）；Cloudflare 博客（2026-07-28 解读）；workos.com（MCP 异步任务实践）。
- 框架：github.com/vercel/ai（v7）；github.com/pydantic/pydantic-ai（v2.47.0）；github.com/openai/openai-agents-python（0.22.3）；github.com/lastmile-ai/mcp-agent（停更）；PrefectHQ/fastmcp（v4.0.5）；npm fastmcp（punkpeye 4.20.16）。
- ACP/A2A：agentclientprotocol.com（spec v1 stable/v2 draft、治理、agents/clients 页）；github.com/a2aproject/A2A（v1.0.1）。

## 修订记录

- v1.0 · 2026-09-22：初版。3 路并行调研（OpenCode/pi 深查；goose/Crush/Aider/Claude Agent SDK/Codex/Gemini/Amazon Q；MCP/ACP/A2A/框架生态）汇总成文；Q-14/Q-15/Q-16 呈递。
- v1.0.1 · 2026-09-22：裁决登记——Q-14 → **DEC-33**（pi 基座；owner 附加北极星：多域 Agent 预留 + "自己生产自己"）；Q-15 → **DEC-34**（双层工具面）；Q-16 补呈详解（作用 + 实现方式，decisions.md §二）后仍待裁。
- v1.0.2 · 2026-09-22：R4（`R4-agent-interaction.md`）对本报告 §4.6 长任务结论作**实现级细化**——Tasks extension 客户端采用为零，落地改为自定义句柄+轮询工具（语义对齐 Tasks V2），见 R4 §3.2/§5 与 Q-17②。
