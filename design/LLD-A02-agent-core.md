# LLD-A02 · 会话编排与 agent 核心 · v0.1 草案

> **上游**：HLD-agent §2/A02、§5（无豁免链）；决策 DEC-33/37（PydanticAI 基座）、DEC-35（ACP 预留）。事实基线 R5 §1。

## 1. SessionOrchestrator（平台层组件）

- 职责：高层工具（app_*）的会话生命周期——创建 PydanticAI 会话、注入域工具集与 skills、路由审批、导出审计、产出结构化结果。
- **Frontend 抽象（ACP 预留缝，DEC-35）**：`Frontend` 接口（send_event / await_approval / user_input）；V1 唯一实现 = `McpFrontend`（事件降级为任务日志行 + sys_pending_approvals 呈现）。后补 `AcpFrontend` 即接编辑器，不改编排层。
- 并发：V1 会话数上限〔Q-19 提案 6：2〕；每会话单任务串行。

## 2. PydanticAI Agent 构造

- `Agent(model=<config providers>, output_type=<per-phase DTO>, tools=[编辑工具 4 件 + 域工具适配], toolsets=[…], retries={output: 3}〔Q-19 提案 3〕)`。
- **模型参数**：默认 `parallel_tool_calls=False`（确定性，HLD §5.4）；温度等进提供者配置快照（审计）。
- **多轮**：`message_history=result.new_messages()` 显式传递（无隐式态）；会话 token 预算〔Q-19 提案 6：100k〕，超限任务失败并建议切分（V1 不做自动压缩，HLD §9）。
- 域工具适配：A03…A06 的工具函数包一层"会话视图"（同步参数校验 + TaskId 返回说明），确保模型见到统一句柄语义。

## 3. 审批闸（第一层强制；R5 §1 Hooks）

- 落点：`hooks.wrap_tool_execute`（全工具统一包装）+ `before_tool_execute`（类别策略表）；类别 = auto/confirm/strict（HLD §5.1，默认表随 A01 §2，可经 config `[policy]` 收紧不可放宽）。
- 行为：`auto` 直行；`confirm` 记审计直行（V1 会话内策略〔Q-19 提案 7〕；收紧为挂起由 config 控制）；`strict` → `raise ApprovalRequired` → Frontend 呈现 → sys_approve（token）→ 重入执行；拒绝/超时 → `SkipToolExecution` 返回拒绝结果给模型。
- **不可绕过性**：闸在编排层唯一入口上；产物侧另有工具内强制（tsap_package 必签名等，HLD §5.2）双层对冲。

## 4. 结构化产物（需求→设计阶段的强制校验）

- DTO（Pydantic 模型，版本化 `dto_version` 字段）：
  - `PlanDto`：app_develop 的计划产物——{requirements_summary, hw_demand[], safety_notes, test_plan, steps[]}。
  - `AppConfigDto`：硬件配置产物（映射 prov 语义子集 + TSAP manifest 字段）——与固件侧 schema 同源对齐（A05 §2 镜像）。
- 校验失败 → `ModelRetry`（预算内重试）；终仍失败 → 任务 failed（TA_E_ARGS）。

## 5. 编辑工具（自建最小编码集，DEC-37）

- `read_file(path, range?)`、`write_file(path, content)`、`apply_patch(path, diff)`（unified diff，严格格式+失败即错误不猜）、`exec(cmd, args[], timeout)`。
- 全部经 A00 run_proc/白名单纪律；exec 审批类别 = confirm（仅限 workspace 内、超时必填）；写操作产物路径必在 workspace。
- patch 失败率高时的改进（编辑格式升级）留 Q 另立。

## 6. 审计导出

- 会话结束（终态）即 `ModelMessagesTypeAdapter.dump_json` 追加至 sessions 流（A00 §3）；conversation_id = 高层任务 task_id 关联，双向可溯（工具流 session_id 字段）。

## 7. 测试要点（L7）

- 闸：三类策略矩阵；strict 挂起-批准/拒绝/超时三路径；策略表收紧不可放宽断言。
- DTO：合法/非法 PlanDto 与 ModelRetry 行为（录制回放，不耗真实 LLM——用 FakeModel 注入）。
- 编辑工具：apply_patch 严格性（模糊 diff 拒绝）；白名单越界拒绝。
- Frontend 抽象：McpFrontend 事件降级正确（审批呈现/日志行）。

## 8. 未决依赖

- Q-19 提案 3/6/7；A01（Frontend 的 MCP 呈现）；A07（skills 注入）；固件侧无依赖（会话层语言无关）。
