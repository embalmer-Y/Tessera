# R11 · 多渠道交互架构与开源 Agent 代码调研（V0.12.0 R11 单元 · DEC-66③）

> **本文件是什么**：四参考项目**代码级**调研（克隆学习，非文档调研——九十六批为文档级，本批为源码级）+ Tessera 多渠道交互（MCI）架构映射 + Web 客户端选型建议。门③呈递件 Q-48 的依据文档。
> **调研对象**（浅克隆 @ ~/project/deps/research/，commit 随批快照）：`sst/opencode`（多渠道 client/server 形态主角）、`openai/codex`（协议分层 + 审批模型）、`google-gemini/gemini-cli`（终端渲染与设计 token）、`Aider-AI/aider`（轻量 web 交互——反模式参照）。

## 1. 各项目交互层架构发现

### 1.1 opencode —— 协议优先单服务器 + 多端消费（形态主角）

- **架构**：单一 HTTP 服务器（effect HttpApi，OpenAPI schema 驱动）为核心唯一门面；TUI（React/Ink 形态 TS 包）、web（ui/ 包：components/data-display/feedback/forms/overlays 分层）、desktop 全部作为**客户端**消费同一 REST API + 同一事件流。客户端 SDK 经 OpenAPI codegen 生成（packages/protocol + client.ts）——协议先定义，多渠道客户端零漂移。
- **API 分组**（groupNames 实证）：session / message / **event** / **permission** / **form** / pty / fs / command / skill……——交互钩子（审批 permission + 问询 form）是**协议一等公民**，不是任何 UI 的私有物。
- **事件流**：core 总线（Bus）→ `event-feed.ts` 订阅者集合 → SSE 端点推送；所有端实时消费同一流（服务端广播，客户端零轮询）。
- **审批模型**：permission request 为**服务端实体**（Permission.ID + list/reply REST + 事件通知）；审批状态活在服务器，UI 只呈现与回传——多渠道下审批一致性由服务器保证。

### 1.2 codex —— 协议分层 + 审批决策语义

- **架构**：core（会话/执行）与 UI（tui/exec/app-server）之间以 `protocol` crate 为唯一契约；app-server 族（protocol/transport/client）= 第二服务器形态（IDE 集成用）。EventMsg 为**版本化类型化事件枚举**（`#[serde(rename = "task_started", alias = "turn_started")]`——v1/v2 wire 共存），事件分类学广（turn 生命周期/告警/上下文压缩/回滚/安全缓冲/token 计量）。
- **审批决策三维**：`ReviewDecision::Approved / ApprovedForSession / NetworkPolicyAmendment{...} / Deny`——**"本会话记住"** 维度（allow-session）显著降低审批疲劳，同时不落盘（会话域失效）。
- **分层启示**：协议 crate 独立 = 多端 + IDE + 未来 A2A 全走同一契约——与我们 DEC-42 版本化信封纪律同构，验证正确性。

### 1.3 gemini-cli —— 语义设计 token（简约好看的结构化做法）

- ui/ 主题层 = `semantic-tokens.ts` + `theme-manager.ts` + builtin 主题集：组件只消费**角色 token**（前景/背景/强调/成功/告警/危险），主题 = token→色值映射表——"好看"是结构化产出而非散落色值。web 客户端照此建 token 层即可低成本换肤。

### 1.4 aider —— 反模式参照（UI 包 CLI）

- `gui.py`（545 行，Streamlit）= 以 `CaptureIO(InputOutput)` 子类**抓 CLI 文本输出**喂网页——UI 包裹 CLI 的短期路线：实现快，但事件无结构（纯文本流）、交互钩子（审批/问询）被迫 CLI 化、多会话/多渠道无法扩展。**不采用**；其价值 = 反面教材 + 证明"IO 接缝"是最小可行缝（我们已有更优缝：MCP 面 + 事件日志）。

## 2. 吸收设计对照表（→ Tessera）

| # | 发现 | 来源 | Tessera 吸收 | 落点 |
|---|------|------|--------------|------|
| 1 | 协议优先单服务器，多端消费同一 API+事件流 | opencode | **MCI 主形态定案依据**：MCP gateway = 唯一服务器（已有）；渠道 = 客户端（Terminal 前端已有；web 为新客户端）——核心与工具面零改动 | LLD-A10 |
| 2 | 事件总线 → SSE 推送端点 | opencode | 现状 task_log 为拉式轮询；MCI 增**推送面**（SSE/Streamable HTTP 通知）——D2 进度面与事件流的推送化 | LLD-A10/A11 |
| 3 | 审批 = 服务端一等实体（ID + list/reply + 事件） | opencode | ApprovalBroker 已同构（approval_id + sys_pending_approvals + sys_approve）——**验证现状正确**；D7 问询照此形态入 MCP（question request ID + answer 回传） | D7/LLD-A10 |
| 4 | 审批决策三维（一次/会话内记住/拒绝） | codex | sys_approve decision 语义扩展候选（allow-session）——降审批疲劳不落盘；**随 D4 门③子呈递**（涉审批语义） | D4 |
| 5 | 版本化事件信封 + 事件分类学 | codex EventMsg | 维持 DEC-42 信封；事件分类参考（turn 生命周期/告警/预算/回滚类）——note_loop_progress 已落 5 类，扩展随用随加 | 已有 |
| 6 | 语义设计 token（角色映射主题） | gemini-cli | web 客户端建 token 层（简约好看的结构化实现 + 未来换肤零成本） | LLD-A11/W1 |
| 7 | 反模式：UI 包 CLI 抓文本流 | aider | 不采用——保持协议优先（MCP 面），web 客户端为 gateway 客户端而非 CLI 包皮 | — |

## 3. Tessera MCI 架构映射（Q-48 呈递正文要点）

**三层渠道模型**（DEC-35 Frontend 缝的显式化演进，纯增量归位）：

```text
Channel（渠道） ≡ Transport × Renderer × Interaction
  Transport:   stdio（现 MCP 默认）| HTTP+Streamable（已在，HLD §9）| SSE 推送（新增面）| 未来 WS/串口桥
  Renderer:    TerminalFrontend（已有）| WebFrontend（W1 新建）| 未来（IDE/面板）
  Interaction: 问询（question request ID + answer）/ 审批（approval_id 已有）/ 进度（task_progress 已有）
               ——三者皆 MCP 面一等公民（opencode permission/form 同型）
```

- **关键事实**：Transport 与 Interaction 两层今天已存在（FastMCP stdio/HTTP 双形态 + ApprovalBroker + task_progress）——MCI 不是重建，是**把散在两 Frontend 实现里的呈现/交互契约显式化为协议**，web 客户端 = 第三个纯增量消费者。
- **web 客户端数据面全部现成**：task_progress（D2）+ task_log/事件流 + sys_pending_approvals/sys_approve + D7 问询（本批补）+ D5 时间线——W1 是纯前端工作。

## 4. Web 客户端选型两案（Q-48 裁点）

| | 案 A：静态单页 + 原生 ES 模块（推荐） | 案 B：React/Vite SPA |
|---|---|---|
| 形态 | 单 index.html + 模块化 JS + 语义 token CSS；SSE 消费事件流 | 组件树 SPA（gemini-cli 同族形态） |
| 构建链 | **零**（浏览器直接跑；ARM 机/CI 零新增） | Node 工具链入仓 + CI 面扩大 |
| 简约好看 | 语义 token + 少量手写组件——够 W1 形态 | 生态成熟、后续复杂交互快 |
| 风险 | 复杂交互手写成本（回放时间线等） | 构建链维护 + 仓体积 |
| 建议 | **W1 v1 采用**；复杂度超出时再评估迁移 B（token 层可平移） | 备选 |

## 5. 与本项目纪律的对齐

- 门③：Q-48 呈递（MCI 三层定案 + web 选型 + D4 审批语义扩展 allow-session）→ owner 裁后 LLD-A10/A11 落稿 → W1 实现。
- 安全边界：web 客户端 = gateway 新消费者——**审批 token 语义不变**（TESSERA_AGENT_APPROVAL_TOKEN；「持有 token ≠ 主人本人」缺口维持记录不开发）；HTTP 绑定默认 127.0.0.1 维持（外网暴露 = owner 显式 + 自担）。
- 合同 9/10 不受影响（固件侧零改动）。

## 6. pi（badlogic/pi-mono）深评——make-vs-buy 评估（owner 2026-10-19 问：「是否应直接引入 pi 而不自研」）

> 浅克隆同批（MIT © 2025 Mario Zechner；最后提交 2026-10-18——极活跃；monorepo：agent/ai/chord/codemode/coding-agent/durable/env/evals/**mcp**/telemetry/**tui**）。

### 6.1 实证事实

- **MCP client 一等公民**：stdio + **streamable HTTP**（legacy SSE 明确不支持——我方 FastMCP HTTP = Streamable，形态精确匹配）；`pi mcp add <name> --url …` + bearer/env；`exposure/toolExposure` 逐服务器工具暴露控制；`/mcp` 会话内管理。
- **自定位 = 「极简可扩展 agent harness」**：有意不带 sub-agents/plan mode；扩展点 = extensions（**生命周期钩子全覆盖**：input/before_agent_start/tool_call〔**可授权或修改工具调用**〕/tool_result/before_provider_request/…）+ skills + prompt templates + themes + packages（npm/git 分发）。
- **RPC/SDK**：`--mode rpc` = JSONL 子进程协议（命令/响应/事件 + 扩展 UI 记录转发）；SDK = 进程内 TS——两者皆面向「自建 UI」而非自带 UI。
- **无 web UI**：当前包列表无 web 包（早期 pi-web 已重构掉）——**「引入 pi 即得 web」不成立**；web 仍需自建（在我方 MCP-HTTP 或 pi SDK 之上）。
- **会话**：JSONL + id/parentId **树结构**（原地分叉 /tree + 分支摘要）；/export HTML/JSONL。
- **安全哲学（关键差异）**：security.md 原文——「**does not ask for approval before every tool call**」「safety comes from limiting files/credentials/processes/network…**watching the transcript…do not create a security boundary**」= OS 边界哲学，无逐调用审批（`tool_call` 扩展钩子可自建闸，但非缺省形态）。
- **运行时**：Node/Bun（本 ARM 机现无 Node——引入需装 Node + pi npm 包；pi.dev 安装脚本可钉依赖）。

### 6.2 评估结论（三维判定）

**① 整体替代 tessera-agent = 否决**。理由：(a) 我方 Agent 的差异化在**域网关**而非聊天循环——确定性创作循环（spec 门/计划/ws_* 编辑/verifier 插件/真机部署修复轮）+ 严格审批（token + 审计 + 参数规则）+ 信任链/L5 机械检查 + 多 cube LN，全部与 Python 域代码深耦合；pi 化 = 以 TS 重写数月工作量，换来的通用循环我们**并不缺**（循环本就跑在服务端 app_develop 内）。(b) pi 安全哲学与我方制造级门禁正交（无逐调用审批缺省形态）——替代即降级。(c) 制造关键路径耦合到快迭代第三方 harness——版本漂移风险不可接受。

**② 引入 pi 作为第二交互渠道 = 采纳**。pi `mcp add --url` 直连我方 FastMCP Streamable HTTP 网关 → owner 立得打磨好的日常 TUI（主题/会话树/压缩/多 provider）覆盖**全部域工具**；同时 = 我方 MCP server 面（DEC-12 角色一）**首个真实外部消费者**——MCI「渠道=客户端」论点获实证，D6「真实消费者出现再启」判据被部分触发。成本 ~0.5 单元（装 Node + pi 接入 + 工具暴露配置 + 严格审批双通道演练 + 全链验收）。风险与缓释：版本钉住；严格审批在 pi 侧 = 长阻塞 + 他渠道批 token（**双通道批准 = 更强而非更弱**，如实文档化）；pi 无逐调用审批 = **服务端闸（D4）为真边界**——价值上升。

**③ W1 web 客户端照旧自研**（pi 无 web）；Q-48 案 A（静态单页 + 语义 token）不变。D5 回放器维持自研（我方审计与 pi 会话树是两类证据）。

### 6.3 吸收对照表增补

| # | 发现 | 来源 | 吸收 |
|---|------|------|------|
| 8 | MCP client streamable HTTP + 工具暴露控制 | pi mcp.md | M1 单元接入面；toolExposure 分级思路 → 域工具只读面默认放行（param_rules 同向） |
| 9 | `tool_call` 扩展钩子可授权/修改调用 | pi extensions | pi 侧闸 = 可选第二道；**服务端 gateway 闸（D4）为主边界**——架构注记 |
| 10 | 会话树 JSONL（id/parentId + 分支摘要） | pi session-format | D5 时间线设计参考（分支语义对我方审计为超集需求，取线性即可） |
| 11 | 「安全 = OS 边界」哲学 | pi security.md | 与制造门禁哲学的**显式对照**入 LLD-A10：两哲学可分层共存（pi 渠道自由 + 服务端域闸强制） |

## 7. QwenPaw 深评（owner 2026-10-19 指定重点参照；pi 吸收待定）

> agentscope-ai/QwenPaw（前身 CoPaw，阿里 AgentScope 团队）：Python 3.11+，Apache 2.0，1052 文件 / **350k LOC**，提交极活跃（克隆当日仍有提交）。定位 = 个人 AI 助理：多渠道（钉钉/飞书/微信/Discord/Telegram/iMessage/QQ/MQTT/Matrix/Mattermost/OneBot）+ 三层记忆（ReMe）+ 心跳任务 + 技能市场 + Tauri 桌面端。

### 7.1 渠道架构（本批最有价值的参照——MCI 的 Python 成品）

- **契约极小 + 基类厚供给**：`BaseChannel` 必实现仅 ~5 面（`from_config` / `start` / `stop` / `send(to_handle, text, meta)` / `resolve_session_id(sender_id, meta)`——入站→会话路由）；基类内建重机械：消息**防抖合流**（native payload debounce/merge）、**流式分发**（start/delta/end + tracker）、**每渠道 ACL 闸**（`_access_control_gate`）、群提及检测、workspace 注入。新渠道 = 薄子类。
- **Renderer 独立层**（`channels/renderer.py`）：Message → 渠道可发部件（text/audio/image/file/video/refusal 六类 Content），按渠道 style/capabilities（markdown/emoji/code fence）裁剪——**MCI Renderer 层的成品实现**。
- **console = 渠道插件**（`channels/console/channel.py`）：本地控制台也是一个 BaseChannel 子类，且自身是 HTTP 客户端（POST /api/console/chat）——**「服务端优先、渠道=客户端」的第三例独立验证**（opencode/QwenPaw/我方 gateway 同构）。
- **ChannelAddress 统一路由**（`schema.py`）：`kind+id → to_handle`（"discord:ch:123"）——出站寻址归一。

### 7.2 安全面（与 pi 相反的哲学——与我方同向）

- `governance/`：audit / **detectors**（危险命令检测）/ policy / **resource_governor** / tool_registry / tool_adapter——Tool Guard 的服务端实现。
- `sandbox/`：全 OS 内核沙箱族（bubblewrap/linux/macos/windows appcontainer/elevated）+ runtime_boundary。
- **MCP 逐工具访问策略**：`app/mcp/schemas.py` 的 MCPAccessPolicy / MCPAccessRule / **MCPToolAccessOverride** / MCPToolDefaultPolicy + 管理 API（routers/mcp.py）——MCP 客户端工具闸的成品参照（对应我方 policy.param_rules 的 MCP 化方向）。
- 每渠道 ACL（白名单谁可与 agent 说话）。

### 7.3 其他值得吸收

- **design.md = 视觉/交互设计语言文档**（token 优先级/主题继承/排版/间距几何/交互语法——含「MAGNETIC ENABLE RAIL」等模式的 anatomy/行为序列/实现配方/键盘与无障碍/评审标准）——**W1「简约好看」的方法论直接参照**（把设计语言作为仓内权威文档）。
- heartbeat 任务 / cron 渠道派发（to_handle 映射）/ portability（导入导出）——远期参考。

### 7.4 引入判定

- **作为 MCI 参照物 = 一级**（渠道契约/renderer/逐工具策略/设计语言四件直接吸收进 LLD-A10/A11）。
- **作为引入物（第二渠道运行时）= 比 pi 更重**：350k LOC 完整助手框架，自带循环/记忆/技能体系与我方核心大面积重叠；Qwen 模型生态倾向（支持 14+ provider 含 Anthropic 兼容，但主场在 QwenPaw-Flash）；引入即运行第二个「助手宇宙」。
- **pi 吸收待定（owner 裁）**下，两者的共同替代项浮现：**W1 web 客户端先行**（案 A 零新增运行时——消解「Python+Node 双运行时」顾虑），harness 引入决策（pi / QwenPaw / 都不）推迟到 W1 真实体验之后。

### 7.5 吸收对照表增补

| # | 发现 | 来源 | 吸收落点 |
|---|------|------|----------|
| 12 | 渠道契约「小必需面（5 方法）+ 基类厚供给」 | QwenPaw BaseChannel | LLD-A10 Channel 协议形态（Frontend Protocol v2 演进模板） |
| 13 | Renderer 独立层 + 渠道能力裁剪（六类 Content + style/caps） | QwenPaw renderer.py | LLD-A10 Renderer 层（D2 进度/事件 → 渠道部件） |
| 14 | MCP 逐工具访问策略（Override/DefaultPolicy）+ 管理 API | QwenPaw app/mcp | D4 策略面 + policy.param_rules 的 MCP 化参照 |
| 15 | governance（detectors/audit/resource_governor） | QwenPaw | D4 hook 检测器语义参照 |
| 16 | design.md 设计语言文档（token 优先级/交互语法/实现配方/评审标准） | QwenPaw | LLD-A11/W1 方法论——设计语言先于代码 |
| 17 | console-as-channel（渠道自身也是服务器客户端） | QwenPaw | TerminalFrontend 归位验证（第三例，MCI 论点巩固） |
