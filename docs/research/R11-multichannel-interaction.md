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
