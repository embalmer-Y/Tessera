# LLD-A14 · W2 web 渠道重塑 · v0.2

> **本文件是什么**：W2 web 渠道重塑低层设计——V0.13.0 A3 单元设计批（DEC-69 六点产品反馈 + W1 人工验收 UX 反馈四条 + SSE 直推 + 多任务视图；owner「开始进行W2 web重塑设计」点向）。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.2（2026-10-19 实现批同步修订——W2-1..4 全单元落地〔DEC-72 门③过裁〕：EventBus+钩子+sys_tasks+phase 派发实装于 common/events.py·common/tasks.py·gateway/*·platform.py；前端五文件重构；clarify 域 + app_clarify 实装；agent 302+2s 全绿）。v0.1 设计批（门③呈递）。

## 1. 定位与输入

**W2 = web 渠道从「运维观测台」重塑为「对话式产品界面」**。W1（LLD-A11 v0.1.2）验证了渠道底座（MCP-over-HTTP + SSE + 零构建前端）与数据面（D2/D4/D5/D7 同源）的成立；W2 不动底座契约，重塑**呈现层与一段 Agent 能力**。

**输入清单（全部登记在案）**：

| 来源 | 内容 |
|---|---|
| DEC-69① | 界面观感简陋 |
| DEC-69② | 受众 = 非专业用户；进度/会话流文案过于专业、无帮助 |
| DEC-69③ | 对话式交互缺失（用户消息入流 + Agent 工作状态指示） |
| DEC-69④ | 多端响应式布局 |
| DEC-69⑤ | 左侧设置栏 |
| DEC-69⑥ | 双模式需求输入——开发者模式全细节含 log / 普通模式 LLM 需求澄清（**Agent 能力增量**） |
| W1 验收四条 | 计划项不打卡 / LLM 静默期无心跳 / 时间线无过滤不尾随 / 诊断轮询污染审计流 |
| V0.12.0 余项 | SSE 轮询差分 → 内部事件总线直推 + 多任务视图 |

**设计参照**（R11 调研在档）：opencode「协议优先、渠道=客户端」（底座已立，不动）；gemini-cli semantic-tokens（token 层升级）；QwenPaw design.md「设计语言文档」方法论（本批 tokens v2 即落此法）；codex ReviewDecision 三维审批（W1 已落 allow-session，不动）。

## 2. 架构总览（三层各变动什么）

| MCI 层 | W1 现状 | W2 变动 |
|---|---|---|
| Transport（MCP-over-HTTP） | FastMCP http_app + 手写 mcp.js | **不变**（工具面 + 新增 `app_clarify`/`sys_tasks`） |
| Interaction（D2/D4/D5/D7 面） | 轮询差分读 registry/brokers | **加事件总线**（发布钩子）——读取面不变 |
| Renderer（web/ 五文件） | 四区观测台 | **重塑**（对话流/状态灯/双模式/设置栏/响应式/tokens v2） |

原则三条：① **服务端闸不动**——strict 审批、hooks 拦截、审计同源对 web 渠道照旧（渠道=客户端，安全在服务端）；② **判据行保真合同不变**（LLD-A10 §3）——原始证据流逐字保留，普通模式是**叠加摘要层**而非改写；③ **spec 门不变**——普通模式的澄清产物仍过 NV-2 spec 门 + 判据派生，创作循环主体零改动。

## 3. 基建：事件总线与 SSE v2（W2-1）

### 3.1 EventBus（`common/events.py`——零依赖层）

```python
class EventBus:
    def publish(self, kind: str, data: dict) -> None          # 同步发布（生产者侧不阻塞）
    def subscribe(self) -> AsyncIterator[Event]                # 每订阅者独立队列
    def replay(self, after_seq: int, limit: int) -> list[Event]  # 环形缓冲重放
```

- **发布模型**：sync `publish` 入 `asyncio.Queue`（每订阅者一个；`loop.call_soon_threadsafe` 兼容工作线程发布——TaskRegistry 的 append_log 在 worker 线程）。
- **慢消费者策略**：队列上限 512，溢出丢最旧 + 插入 `kind=resync` 事件（客户端收到即全量快照重对齐）——观测渠道宁可重对齐不可假死。
- **重放**：环形缓冲 512 条 + 单调 seq；SSE `id:` 字段带 seq，重连经 `Last-Event-ID` 续传——**消除 W1「重连即清空」**。

### 3.2 发布钩子（缺省零行为变化）

| 源 | 事件 | 注入方式 |
|---|---|---|
| TaskRegistry.append_log | `task.log` {task_id, lines} | registry 构造参数 `bus: EventBus \| None`（缺省 None = 现行为逐字节等价） |
| Task.state / progress 变更 | `task.state` {task_id, state, progress} | registry 内部变更点（state 迁移 + progress.update） |
| QuestionBroker.ask / answer | `question.opened` / `question.closed` | 同上钩子参数 |
| ApprovalBroker.request / decide | `approval.requested` / `approval.decided` | 同上 |
| app_develop 循环（loop.py 已有事件流） | `task.phase` {task_id, phase, note} | CreationLoop 事件回调 → Task.progress 既有通道，新增 phase 字段 |

组装点 = gateway/compose.py（构造 EventBus → 注入三处；ctx.events 挂载）。CLI/测试路径不注入 = 零变化（与 approvals token 缺省形态同规）。

### 3.3 /events v2

- 连接 = 首帧全量快照（现状语义保留）+ 之后总线直推（0.5s 轮询删除）；
- `?task_id=` 过滤保留；`Last-Event-ID` 续传；15s `: ping` 注释行保活；
- 帧型：`task_log` / `state` / `question.*` / `approval.*` / `task.phase` / `resync` / `tasks`（任务列表签名变化时）。

## 4. 对话式呈现层（W2-2——DEC-69①②③④⑤ + W1 四条）

### 4.1 信息架构（从四区观测台 → 对话流主导）

```
┌────────┬──────────────────────────────┬──────────┐
│ 设置栏  │  会话流（对话气泡 + 折叠日志）   │ 任务列表  │
│ (⑤)    │  [用户] 发起需求/应答/审批动作   │ (多任务)  │
│ 主题    │  [Agent] 阶段摘要 + 状态灯      │ 当前任务  │
│ 模式    │  [卡片] 问询/审批（置顶强调）    │ 历史(≥1) │
│ 密钥    │  [开发者] 原始判据行（折叠）     │ ───────  │
│ ...    ├──────────────────────────────┤ 时间线    │
│        │  composer（底部，双模式输入）    │ (过滤+尾随)│
└────────┴──────────────────────────────┴──────────┘
```

### 4.2 Agent 状态指示（③ + LLM 心跳）

- **状态灯**（header 常驻 chip）：`空闲 / 规划中 / 实现中（第 N 轮）/ 验证中 / 修复轮 / 等待您确认 / 等待审批 / 打包中 / 部署中 / 已完成 / 失败`——由 task.state × progress.loop_state × pending 问答派生（单一映射表，server 侧派发 `task.phase`，前端零推导）。
- **活动心跳**：progress 增 `last_activity_ts`（loop 每事件刷新）；前端显示「运行中 · 上次活动 Xs 前」，>30s 无活动转为呼吸灯提示（LLM 长思考期不显得假死——W1 反馈直接闭环）。
- **计划项打卡**：progress.plan 项状态扩 `active`（当前进行项）；事件 `task.phase` 增量推送打卡。

### 4.3 会话流双形态（② + ⑥的呈现面）

- **用户气泡**：发起（需求摘要）、问询应答、审批决定、澄清答复——全部入流（③）；
- **Agent 气泡**：阶段摘要（人类可读一句话 + 关键数字：轮次/证据数/判据命中）——来源 = `task.phase` 事件；
- **原始日志**：`task_log` 帧在**开发者模式**渲染为等宽判据行（着色正则沿用）；**普通模式折叠**为「查看详细日志」抽屉（证据流本体不改写——保真合同：日志抽屉即逐字原文）；
- **文案层**（②）：`web/copy.js` 术语映射表（spec→需求单 / 判据→验收检查 / strict 审批→安全确认 / 槽位→安装位 / 激活→启用……）+ 阶段摘要模板；普通模式默认走映射，开发者模式原文。

### 4.4 设置栏（⑤）

左侧抽屉（移动端 = 汉堡展开）：主题（浅/深/跟随系统——tokens v2 手动覆盖能力）、模式（普通/开发者——⑥）、计划确认缺省开关、签名私钥路径、网关地址显示、关于（版本/协议面）。持久化 = localStorage（零后端存储面——密钥不落存储红线不变，token 本就内存态）。

### 4.5 响应式（④）

- ≥1024px：三栏（设置 / 会话流 / 任务+时间线）；
- 768-1023px：两栏（设置收起为图标栏）；
- <768px：单栏 + 底部 composer 固定 + 设置/任务/时间线为抽屉；触控目标 ≥44px；SSE 断线重连提示条。

### 4.6 时间线与多任务（W1 四条余项）

- 时间线：工具过滤下拉（tool 维度）+ 类型过滤 + **尾随开关**（开启时经 `task.log` 外的审计事件流增量刷新——审计 JSONL 本身不变）；
- 多任务：`sys_tasks` MCP 工具（registry.list_tasks 快照——id/工具/状态/时间）；任务列表侧栏点击切换附看（`/events?task_id=`）；进行中任务 >1 时状态灯聚合显示。

### 4.7 诊断轮询纪律（W1 第四条）

post_deploy_check 判据窗/部署诊断的重复轮询行打 `kind=diag` 标（deploy 链 log_fn 已有 `[dep]` 前缀可派生）；前端普通模式不渲染 diag 行（开发者模式折叠区可见）；审计流本体不动（回放域事实完整优先）。

## 5. 双模式需求输入（W2-3——DEC-69⑥，Agent 能力增量）

### 5.1 需求澄清域（`domain/clarify.py`）

**定性**：创作循环的**前置阶段**——LLM 驱动但产物过确定性门；与 CreationLoop 同族（非关键路径确定性流水线——如实注记，BV1 同款定性纪律）。

```
raw 需求文本
  → ① 缺口分析（LLM 结构化输出：四节模板逐项完备性 + 追问点列表）
  → ② 澄清轮（≤3 轮，QuestionBroker 逐项问询——复用 D7 面，问询卡即 UI）
  → ③ spec 合成（LLM 依答复生成四节 spec）
  → ④ spec_check 门（NV-2 既有工具——硬伤阻塞，判据引号串机读派生不变）
  → ⑤ 确认问询（合成 spec 全文呈现 → proceed / 重新澄清）
  → ⑥ 交棒 app_develop（spec 门与判据派生零改动）
```

- **面**：MCP `app_clarify`（spawn 长任务 + D2 progress + 问询卡自然复用；返回键含 task_id/synthesized_spec/rounds）；前端普通模式 composer 提交 → app_clarify → 确认卡 → 自动 app_develop。开发者模式 composer 直填 spec 走现路径。
- **预算**：澄清轮计 LLM 调用预算（ContextBudget 既有）；轮次上限 3 + 总问询数上限 8（防循环）。
- **失败语义**：LLM 不可用（无 key）→ 结构化错误提示「切换开发者模式直填 spec」；spec_check 不过 → 澄清域如实返回错误（不静默降级）。
- **安全**：问询/确认走 QuestionBroker（无 token 便利面语义不变——安全边界仍是 strict 审批 + 服务端闸）。

### 5.2 前端模式切换

设置栏切模式；composer 占位文案随模式切换（普通 = 「描述你想让设备做什么…」/开发者 = 四节模板提示）；普通模式下高级项（密钥/计划确认）折叠隐藏。

## 6. tokens v2（①——观感升级）

- 色板扩层：背景/表面/表面凸起三级 elevation + 语义色（ok/warn/danger/accent）+ 对话气泡专用角色；间距/圆角/动效 token 化（150ms ease-out 微动效：卡片入场/状态灯呼吸）；
- 主题 = token 重映射（架构不变），新增手动主题选择（⑤）；
- 排版：UI 字体族不变，新增 display 级（状态灯/标题）与 bubble 级字阶。

## 7. 批内切分与规模重估（门③呈递核心）

| 单元 | 内容 | 规模 |
|---|---|---|
| **W2-D** ✅ 本批 | LLD-A14 设计批 | ~0.5 |
| **W2-1** 基建 | EventBus + 发布钩子（registry/questions/approvals）+ /events v2（快照/续传/resync/心跳）+ sys_tasks 工具 + 测试 | ~1 |
| **W2-2** 呈现层 | 会话流重构（气泡/状态灯/心跳/计划打卡）+ tokens v2 + 双主题 + 设置栏 + 响应式三档 + 文案层 + 时间线过滤尾随 + 诊断帧纪律 + 前端静态守卫测试 | ~1.5 |
| **W2-3** 双模式 | clarify 域（缺口分析/澄清轮/spec 合成/门/确认交棒）+ app_clarify MCP 面 + 前端模式切换 + 测试（剧本化 runner） | ~1.5 |
| **W2-4** 收口 | 多任务视图 + 回归定格 + LLD-A10/A11 修订（MCI 注记）+ 计数对齐 | ~0.5 |
| **合计** | | **~5 单元**（原 A3 估 ~1 不再适用——DEC-69 六点为能力增量而非打磨） |

执行序 W2-1 → W2-2 → W2-3 → W2-4（W2-2 与 W2-3 可在 W2-1 后并行）；每单元 twister + agent pytest + ruff + sync 回归（军规 10）。真机部署链不涉——纯 Agent 侧批，BV1 自验不受影响。

## 8. 测试策略

- **W2-1**：EventBus 单测（扇出/慢消费者 resync/重放/线程发布）；registry/broker 钩子「bus=None 零变化」对照组；/events v2 端到端（真实 uvicorn：快照帧/续传/心跳/多订阅）——test_web 既有四测扩展；
- **W2-2**：服务端 phase 派发表单测；前端零 Node 维持——静态守卫测试扩展（新文件存在/ES import 路径/根绝对 URL 纪律/copy.js 键完备性对 phase 枚举）；
- **W2-3**：clarify 域剧本化 runner 测试（缺口分析→两轮澄清→合成过门→确认→交棒；spec_check 拒路；轮次上限；LLM 缺失结构化错误）；app_clarify MCP 注册事实；
- **回归**：agent 全量 + twister 17/17 + ruff + L5 + sync（本批零固件面）。

## 9. 非目标（登记）

i18n 多语言（v1 仅中文文案层）/ 桌面通知 / 会话内文件上传 / A2A 渠道 / pi 渠道（M1 维持 HOLD——W2 体验后再议）/ 服务端持久化会话历史（localStorage 即可——审计 JSONL 已是完整事实源）。

## 10. v2 方向（登记不实施）

流式 token 级输出（LLM 生成过程可见——需 MCP 面增流式语义，跨批评估）/ 多会话并行任务对比视图 / clarify 记忆（同类需求澄清历史复用）/ web 端 board_validate 报告可视化。
