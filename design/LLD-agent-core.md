# LLD-agent-core · 会话编排与 agent 核心 · v0.2.2 草案

> **上游**：HLD-agent §2/A02、§5（无豁免链）；决策 DEC-33/37（PydanticAI 基座）、DEC-35（ACP 预留）。事实基线 R5 §1。

## 1. SessionOrchestrator（平台层组件）

- 职责：高层工具（app_*）的会话生命周期——创建 PydanticAI 会话、注入域工具集与 skills、路由审批、导出审计、产出结构化结果。
- **Frontend 抽象（ACP 预留缝，DEC-35）**：`Frontend` 接口（send_event / await_approval / user_input）；V1 唯一实现 = `McpFrontend`（事件降级为任务日志行 + sys_pending_approvals 呈现）。后补 `AcpFrontend` 即接编辑器，不改编排层。
- 并发：V1 会话数上限〔Q-19 提案 6：2〕；每会话单任务串行。

## 2. PydanticAI Agent 构造

- `Agent(model=<config providers>, output_type=<per-phase DTO>, tools=[编辑工具 4 件 + 域工具适配], toolsets=[…], retries={output: 3}〔Q-19 提案 3〕)`。
- **模型参数**：默认 `parallel_tool_calls=False`（确定性，HLD §5.4）；温度等进提供者配置快照（审计）。
- **多轮**：`message_history=result.new_messages()` 显式传递（无隐式态）。
- **上下文预算与压缩（DEC-38）**：预算**动态**取自模型配置的 context window（启动校验：窗口 **≥32k tokens**，低于 = 配置错误拒绝启动——系统提示+skills+工具 schema+最小工作集约需 20k）；会话使用达窗口 **70%** 触发**压缩**：保留系统提示/skills 注入/近期轮次（阈值内预算的后段），远段经一次固定提示的模型调用压缩为摘要（摘要进审计流，原始历史保留在导出文件不丢弃）；压缩后仍超限 → 任务失败（TA_E_ARGS 类，提示切分）。
- 域工具适配：A03…A06 的工具函数包一层"会话视图"（同步参数校验 + TaskId 返回说明），确保模型见到统一句柄语义。

## 3. 审批闸（第一层强制；R5 §1 Hooks）

- 落点：`hooks.wrap_tool_execute`（全工具统一包装）+ `before_tool_execute`（类别策略表）；类别 = auto/confirm/strict（HLD §5.1，默认表随 A01 §2，可经 config `[policy]` 收紧不可放宽）。
- 行为：`auto` 直行；`confirm` 记审计直行（V1 会话内策略〔Q-19 提案 7〕；收紧为挂起由 config 控制）；`strict` → `raise ApprovalRequired` → Frontend 呈现 → sys_approve（token）→ 重入执行；拒绝/超时 → `SkipToolExecution` 返回拒绝结果给模型。
- **不可绕过性**：闸在编排层唯一入口上；产物侧另有工具内强制（tsap_package 必签名等，HLD §5.2）双层对冲。

### 3.1 审批参数规则（Q-38⑤，DEC-57；v0.2.1 措辞修正）

- PolicyTable 条目扩展可选 `param_rules: {allow: {<参数名>: [<值>]}, deny: {…}}`（示例：`deploy_push_app: {allow: {cube: ["xiao-1"]}}`）。
- **求值序（唯一权威，A01/MCP 与 A09/终端同链）**：deny 规则命中 → 拒（TA_E_APPROVAL_DENIED，detail 含命中规则）→ allow 规则命中 → **strict 自动放行**（owner 已批 Q-38⑤ 原义：白名单参数免逐次审批——如「仅允许目标 cube=开发板」的部署）→ 无规则命中 → 类别策略。〔v0.2.1 修正：初版「allow 只免参数级问询、不越过 strict」与 owner 批准语义相悖，按批准义实现（AG6 落地）〕
- **只可收紧**（deny 恒优先于 allow）：参数规则不得使 strict 类降级为 auto/confirm；config `[policy.param_rules]` 载体、人工维护、运行时不自修改（合同 10 同构）。多值参数匹配 = 精确等值（无通配——可预测性优先，通配需求实证后另立 Q）。
- 测试要点：求值序矩阵（deny>allow>类别）/allow 自动放行断言/多参数交叉（全命中才 allow）。

### 3.2 安装期权限呈报（V0.8.0 EC3 · Q-40③/DEC-60③）

- **无头设备路（已实现）**：安装类 strict 审批（deploy_push_app / app_deploy / ln_deploy）请求 reason **强制携带包声明权限面**——`install_permission_brief`（domain/firmware.py；数据源 = `tsap_tools.manifest_summary`〔容器头 + manifest 解析，不含验签——显示面；真授权门 = 部署链 tsap_verify 复验 + 固件验签链〕）产出一行摘要：APP id/ver、tier、caps、fs_paths、needs.resources、threads、wasm 尺寸。坏包（不可读/容器损）= 审批前拦截（TaError 如实）。brief 日志在审批请求前无条件入 task_log（可审计——含 allow 白名单放行场景）。
- **有本地交互设备路（deferred——设备形态批）**：本地确认 UI 消费同一摘要数据面（manifest_summary 单一事实源——两路呈报内容一致）；本地确认事件经 arb 本地席位（CG3 机制）入固件——接线随本地交互外设（LLD-ts-safety §5b/§9a 既定）。
- 安卓先例对照（R9 §4）：install-time 确认在嵌入式无成熟公开先例（先行者位置）——本设计以「审批数据面与设备能力自报（CG5-A caps）同源」自证一致性。

## 4. 结构化产物（需求→设计阶段的强制校验）

- DTO（Pydantic 模型，版本化 `dto_version` 字段）：
  - `PlanDto`：app_develop 的计划产物——{requirements_summary, hw_demand[], safety_notes, test_plan, steps[]}。
  - `AppConfigDto`：硬件配置产物（映射 prov 语义子集 + TSAP manifest 字段）——与固件侧 schema 同源对齐（A05 §2 镜像）。
- 校验失败 → `ModelRetry`（预算内重试）；终仍失败 → 任务 failed（TA_E_ARGS）。

## 5. 编辑工具（自建最小编码集，DEC-37）

> **v0.2 注**：创作循环的编辑工具族 = **LLD-agent-creation-workspace §3 ws_\* 四动词**（唯一锚定替换 + roots 钳制——R6/R7 证据定案）；本节原始规格（apply_patch/exec 形态）**作废留档**——实现从未走通用 exec/patch 面（域封闭纪律），ws_* 为正式继承者。

## 5a. 创作循环编排触点（v0.2 · DEC-57）

- `app_develop` 升级为 A08 循环后端：入参/返回契约不变（spec→任务句柄），内部 = spec_check 门 → A08 建工作区 → 循环（§LLD-agent-creation-workspace §5）→ PACKAGED；循环过程经 task_log 轮事件流观测（MCP/终端两门面同源）。
- SessionOrchestrator 增创作任务类型：PydanticAI Agent 构造 = 系统提示（`_develop_system_prompt` + 循环纪律段）+ 工具面（ws_* + read_skill + verifier 结果由引擎注入非工具）+ `parallel_tool_calls=False`；轮间 message_history 维持 + 70% 压缩（§2 既有机制上移一层，存活项 = LLD-agent-creation-workspace §5.4）。
- repair_feedback 入参（NV-1 既有）兼容：非空时作为首轮证据块注入（S8 场景——部署后诊断再入循环）。

## 6. 审计导出

- 会话结束（终态）即 `ModelMessagesTypeAdapter.dump_json` 追加至 sessions 流（A00 §3）；conversation_id = 高层任务 task_id 关联，双向可溯（工具流 session_id 字段）。

## 7. 测试要点（L7）

- 闸：三类策略矩阵；strict 挂起-批准/拒绝/超时三路径；策略表收紧不可放宽断言。
- DTO：合法/非法 PlanDto 与 ModelRetry 行为（录制回放，不耗真实 LLM——用 FakeModel 注入）。
- **上下文（DEC-38）**：70% 阈值触发压缩（FakeModel 注入长历史）；压缩保留段正确（系统提示/近期轮次/远段摘要）；压缩后仍超限失败路径；模型窗口 <32k 拒绝启动；预算动态随模型配置变化。
- 编辑工具：apply_patch 严格性（模糊 diff 拒绝）；白名单越界拒绝。
- Frontend 抽象：McpFrontend 事件降级正确（审批呈现/日志行）。

## 8. 未决依赖

- DEC-38（#3/6/7 常量出处）；A01（Frontend 的 MCP 呈现）；A07（skills 注入）；固件侧无依赖（会话层语言无关）。

## 修订记录

- v0.2.2 · 2026-10-15：**EC3（安装期权限呈报）**——§3.2：安装类 strict 审批 reason 强制携带 manifest_summary 权限面（无头路实现）；本地确认路数据面同源、接线随设备形态批。用例 test_manifest_summary_fields_and_errors + test_install_permission_brief_format。
- v0.2 · 2026-10-13：**AG1 修订（DEC-57）**——§3.1 审批参数规则（求值序唯一权威/只可收紧/精确等值）；§5 编辑工具规格作废注（ws_* 继承，LLD-agent-creation-workspace §3）；§5a 创作循环编排触点（app_develop 升级/轮事件流/repair_feedback 兼容）。
- v0.1.1 · 2026-09-22：DEC-38 同步——§2 上下文管理重写（动态预算 + 70% 压缩 + 32k 最低窗口；替换原"固定 100k 超限失败"）；§7 增上下文测试要点。
- v0.1 · 2026-09-22：初版。
