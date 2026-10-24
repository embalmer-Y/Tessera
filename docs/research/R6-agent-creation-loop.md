# R6 · Agent 创作循环架构调研（DEC-56 通用域解放 · R 批①）——Agent 批设计输入

> **日期**：2026-10-13 · **触发**：DEC-56（Agent 双角色 + 智能内化）· **消费方**：Agent 批（plan §11d，V0.6.0 候选）design。
> **方法**：本会话已完成 `docs/agent-cli-research.md`（Codex/opencode/Gemini CLI/Claude Code 四路实抓 + ZCode 自省 + aider R1-R8 基础）——本文不重复其事实，只做**面向 Tessera 的映射决策**；本地事实经代码核证（platform/domain/gateway/core/skills/tools_diag/tools_tsap/tools_net）。
> **结论先行**：Agent 批的架构动作 = 三件——①**内环改造**（app_develop 的单工位 LLM → 多轮创作循环：工作区 scoped 文件面 + 计划/进度 + sim 自测迭代）；②**独立门面**（终端 CLI：交互循环 + 终端审批呈现 + 会话持久化）；③**外环接线**（MCP 面复用不动，A2A/ACP 缝维持预留）。安全模型重划 = 创作面放宽、交付门不撤。

## 1. 目标形态（DEC-56 定案的边界）

```
人（终端）──tessera-agent run "需求"──┐
                                    ├─▶ Agent 进程（创作循环 = 智能）
外部 AI CLI ──MCP──▶ 33 域工具面 ───┘        │
                                             ▼
                              创作工作区（agent/workspace/<app_id>/）
                                多文件工程 · scoped 文件工具 · sim 自测
                                             │
                                             ▼
                              交付管线（确定性门，一个不撤）
                                编译→面检查→尺寸→双编译一致→验签→部署→判据
```

三个角色边界：**创作循环里的 LLM = 有编辑自由的开发者**；**交付管线 = 机器验收**；**外部 AI CLI（经 MCP）与终端人（经 CLI）= 同一循环的两个入口**。

## 2. CLI 调研 → Tessera 的直接映射（设计事实，出处 = agent-cli-research）

| 业界共识 | Tessera Agent 批采纳形态 |
|---|---|
| 编辑格式两族：唯一串替换（Claude/opencode/ZCode）vs patch 文法（Codex apply_patch） | 工作区文件编辑 = **唯一串替换式**（实现最简、与弱模型兼容；小文件仍整文件再生——R3 域内已证可靠，按文件大小分档） |
| 会话持久化全员（resume/fork/checkpoint） | **任务级持久化**：app 开发任务状态（工作区文件 + 轮次历史 + 进度）落盘 JSONL/JSON 快照——重启 `--resume`；不做对话级回放（V1 冗余） |
| 计划外显（update_plan/todo 族） | **plan 状态机工具**：spec→工程分解→步骤 pending/done，进度同时喂给 LLM 上下文与终端呈现 |
| 诊断自动回喂（opencode LSP 模式 = 第一杠杆） | **编译 stderr + sim 判据 diff + 部署后串口证据自动附在工具结果后**——repair_loop 从"外环手动转"改为"内环自动转"（有界轮次） |
| 审批参数级粒度（specifier 规则） | PolicyTable 升级：工具级三类（auto/confirm/strict）维持 + **strict 类增参数白名单规则**（如 deploy 目标 cube 限定）——补业界差距的最小面 |
| 上下文余量自省（Codex get_context_remaining） | budget 已有内部账——暴露为内部工具 + 终端 status 行 |
| 问询工具（AskUserQuestion 族） | **终端门面内置**：循环中需要人裁决（spec 歧义/判据确认/strict 审批）时在终端呈现选项；MCP 面维持 pending_approvals 轮询语义 |
| 多代理（writer/reviewer） | **暂不引入**（复杂 APP 批实证收敛不足再加——R3 复审结论维持；域内确定性门已占 reviewer 位） |

## 3. 现有架构资产盘点（复用/改造/新建）

| 资产 | 现状 | Agent 批处置 |
|---|---|---|
| `platform.py` + `domain/` + `gateway/compose.py` | 平台/域拆分已就位（DEC-33 北极星结构） | **复用不动**——创作循环作为 domain 层新组件挂入 |
| `gateway/approvals.py`（token 审批闸） | 单 token，委托人假设缺口已登记（2026-10-13 观察项） | 终端门面下 token = 终端进程内交互（人在场）；AI 客户端接入纪律随 ZCode 集成呈递——本批不动闸本体 |
| `core/tasks.py`（TaskRegistry 句柄化） | 任务句柄/日志/取消 | **复用**：创作循环 = 一种长任务；`task_log` 增量即终端实时输出源 |
| `common/limits.py`（ContextBudget + maybe_compress 70%） | 任务内压缩 | **复用**：会话级自动压缩 = 阈值触发同机制上移一层 |
| `domain/app_chain.py`（app_develop 单工位） | spec→LLM(JSON)→校验→编译→打包，反馈预算 3 | **改造为内环**：DevelopOutcome 产物落工作区文件；反馈回路扩展编译/sim 证据；轮次预算上调（建议 8-12，随实测调） |
| `tools_diag/`（capture/classify/repair/spec_gate/simreal_diff） | repair_loop 已有编排（deploy→capture→classify→feedback） | **接线**：从外环工具面调用改为内环自动步骤（sim 证据 = sim_run 结果判据 diff；真机证据 = 部署后 capture） |
| `skills/`（4 skill + loader + SOURCES.lock） | 渐进披露 | **复用**：创作循环系统提示 = 文法内联 + skills 按需读（不变）；新增"工程模板"类 skill（多文件工程骨架） |
| `core/peer.py`（A2A/ACP 协议缝） | 预留（DEC-35/36④） | **不动**：随生态批评估 |
| `gateway/server.py`（stdio + HTTP 门面） | MCP 双传输 | **复用**：新增第三门面 = 终端 CLI（复用同一 compose 根——三门面共享 ctx/audit/tasks） |

**新建件**：①`tessera_agent/cli/`（终端交互循环：需求输入→进度呈现→审批交互→结果汇报）；②`agent/workspace/`（gitignore；按 app_id 隔离的多文件工程目录）+ scoped 文件工具（read/write/edit/list，roots 钳制在 workspace + 仓库只读白名单〔框架头文件/文档〕）；③会话快照持久化（workspace 同级 `.session/`）。

## 4. 关键设计输入（三条硬约束）

1. **scoped 文件面的安全边界**：LLM 文件工具可达 = `agent/workspace/<app_id>/**`（读写）+ 仓库白名单只读集（`firmware/module/tessera/include/`、`agent/skills/`、`docs/*.md`）。读面纪律维持 IR2-03 五道门（`#include` 探读禁令等只对**仓库面**生效；工作区面 = 新代码，无秘密无凭据——CI 纪律：workspace 永不入仓）。写面 roots 钳制防路径逃逸（`_resolve_within` 既有纪律平移）。
2. **交付门不撤清单**（创作自由度的对价，一条不少）：clang 钉版 flags 编译、natives 白名单面检查、尺寸门（数值重定后仍硬）、双编译字节一致、TSAP 签名复验、真机/sim 判据行匹配。**LLM 在创作循环里无论多自由，进不了交付管线的产物不可能上板**——这是"创作面放宽、交付面收紧"的机械保证。
3. **多文件→单 wasm 工程链**：交付物仍是单 wasm（TSAP 容器不变——DEC-21）；工程组织 = 工作区多 .c/.h → 编译步骤聚合 clang 单命令多文件（或逐文件 .o + wasm-ld——具体链 R7 调研定）。manifest/caps 语义不变。

## 5. 呈递（Q-38 · Agent 批设计决策——随本文登记 decisions.md）

1. **内环形态**：建议 = app_develop 升级为工作区创作循环（计划→编辑→编译→sim→迭代，轮次预算 8-12）+ repair 证据自动回喂；备选 = 保持单工位仅加文件面（保守，复杂 APP 收敛力不足——不建议）。
2. **独立 CLI 门面**：建议 = `tessera-agent run "需求"`（交互式：进度实时呈现 + 审批终端确认 + 结果汇报；`--resume` 续跑）；审批 = 终端内 token 交互（人在场语义成立）。
3. **scoped 文件工具面**：建议 = 按上述 roots 方案新增 read/write/edit/list 四件（域内动词，非通用 shell）；仓库面维持只读白名单。
4. **会话持久化**：建议 = 任务级快照（工作区 + 轮次摘要 + 进度状态），重启可续；不做对话级 checkpoint/回放（留候选）。
5. **审批粒度**：建议 = PolicyTable 增参数白名单规则（strict 类先行）；审批闸本体（双通道加固）维持观察项不开发。

## 6. 来源

- `docs/agent-cli-research.md`（本会话四路实抓调研——本文全部业界事实的出处）
- 本地核证：`agent/tessera_agent/{platform,domain/firmware,domain/app_chain,gateway/approvals,gateway/server,core/session}.py`、`tools_diag/`、`tools_tsap/wasm_build.py`、`skills/`
- 决策依据：DEC-56 / DEC-11/12 v1.1 / DEC-33（平台域解耦）/ DEC-34（双层工具面）/ DEC-38 #6（上下文压缩）
