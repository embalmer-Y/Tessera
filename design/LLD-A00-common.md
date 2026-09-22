# LLD-A00 · 公共基座（错误/任务/审计/配置/纪律）· v0.1 草案

> **上游**：`HLD-agent.md` §2/A00。未决默认值以〔Q-19 提案 n〕标注。
> **实现语言**：Python 3.12（WSL venv），包结构 `agent/tessera_agent/`（子包 common/gateway/core/tools_fw/tools_sim/tools_tsap/tools_net/skills）。

## 1. 错误模型

- 异常基类 `TaError`，结构化字段：`domain`（模块名）、`code`（`TA_E_*`）、`message`、`retryable: bool`、`detail: dict`。
- 错误码族 `TA_E_*`（登记 names.md）：

| 码 | 含义 | retryable |
|---|---|---|
| TA_E_INTERNAL | 内部异常（兜底） | false |
| TA_E_ARGS | 参数校验失败（Pydantic 校验错误转换） | false |
| TA_E_TASK_NOT_FOUND / TA_E_TASK_STATE | 句柄不存在 / 状态不允许该操作 | false |
| TA_E_TIMEOUT | 子进程/工具超时 | true |
| TA_E_PROC_FAIL | 子进程非零退出（build/twister 等） | false |
| TA_E_LOG_TRUNCATED | 日志/输出超限截断（非错误，提示位） | false |
| TA_E_APPROVAL_DENIED / TA_E_APPROVAL_TIMEOUT | 审批拒绝 / 等待超时 | false |
| TA_E_ZENOH / TA_E_TSAP / TA_E_SIM | 域错误（细分见各 LLD） | 视 |
| TA_E_POLICY | 策略禁止（白名单外路径/命令） | false |

- MCP 呈现：A01 把 TaError 转为工具结构化错误返回（`isError` + `{domain, code, message, retryable}`），**不抛裸异常**。

## 2. 任务模型（长任务句柄，DEC-36②）

- `TaskId` = `t-{8 字节随机 hex}`（一次性，不预测）；创建即入进程内注册表 `TaskRegistry`（单进程内存 dict + asyncio.Lock）。
- 状态机（对齐 MCP Tasks V2 语义）：`working → completed | failed | cancelled`；`working` 可进 `input_required`（审批等待），应答后回 `working`。
- 字段：`id, tool, args_digest, state, created_at, ttl, log: RingBuffer, result, error`。
- TTL 默认〔Q-19 提案 4：30 min〕，到期转 `failed`（原因 TA_E_TIMEOUT）；`task_cancel` = 协作式（终止子进程组 + 置 cancelled）。
- 日志环形缓冲：每任务〔Q-19 提案 5：1000 行〕；`task_log` 分页（offset/limit），溢出标记 TA_E_LOG_TRUNCATED。
- **重启丢失语义**：V1 进程内注册表不持久化（单进程 stdio 形态下客户端随进程重启）；与 DEC-36②"自定义句柄"决策一致，持久化留多进程阶段。

## 3. 审计（双流）

- **会话流**：每次 agent 会话导出 `ModelMessagesTypeAdapter` JSONL → `agent/audit/sessions/{date}/{conversation_id}.jsonl`（R5：官方要求用 TypeAdapter 抗 minor 字段演进）；文件头含提供者快照（model/参数）。
- **工具流**：每次工具调用（含原子层直调）一行 JSON → `agent/audit/tools/{date}.jsonl`：`ts, task_id, session_id?, tool, args_digest, state, dur_ms, approval?`。参数只存摘要（sha256 + 截断预览），**不落密钥/令牌**。
- 保留策略：V1 全量不滚动〔Q-19 提案 8〕；写入失败 = 工具调用失败（审计必成）。

## 4. 配置（agent/config.toml + 环境变量）

- 段：`[agent]`（workspace 路径、审计目录）、`[providers]`（默认模型串如 `openai:…`/`anthropic:…`/`ollama:…`；自定义 base_url）、`[policy]`（工具审批类别覆盖表）、`[zenoh]`（router locator、TLS 配置引用）、`[limits]`（Q-19 各值）。
- **密钥纪律**：API key 一律环境变量/`.env`（gitignore），config.toml 只存非敏感配置；config.toml 入库为模板 `config.example.toml`。
- 加载顺序：默认值 < config.toml < 环境变量；启动时校验（缺 providers 即 sys_get_info 报 not_configured）。

## 5. 子进程与 asyncio 纪律（DR-23）

- 一切外部命令经 `run_proc()`：`asyncio.create_subprocess_exec`（**禁 shell=True**）、参数列表化、`cwd`/`env` 显式、超时必填、stdout/stderr 流式入任务日志；超时杀进程组（start_new_session=True + killpg）。
- 路径白名单：可读写路径必须位于 workspace 根内（`Path.resolve()` 前缀校验，违反 = TA_E_POLICY）。
- 输出截断（DEC-38：**随动态上下文预算缩放**）：单次工具返回上限 = 会话上下文预算 ×5% 折算字节（≈4 字符/token），**最低 16 KiB**；单行上限 = max(2 KiB, 单次上限/16)；超限截断+标记（TA_E_LOG_TRUNCATED）。预算来源与压缩见 A02 §2。
- 全库 UTF-8 显式编码（军规 4）；禁阻塞调用进事件循环（lint 检查项）。

## 6. 测试要点（L7）

- TaskRegistry：状态机全迁移 + 非法迁移拒绝 + TTL 到期 + 并发锁。
- TaError → MCP 结构化错误转换矩阵。
- run_proc：超时/非零退出/大输出截断/白名单越界（TA_E_POLICY）。
- 审计：双流写盘、密钥不落盘（内容扫描断言）、写失败即调用失败。

## 7. 未决依赖

- DEC-38（#5/9 常量出处——日志环形 1000 行/截断动态公式）；A01（注册表消费方）；A02（会话流与预算来源方）。

## 修订记录

- v0.1 · 2026-09-22：初版。
- v0.1.1 · 2026-09-22：DEC-38 同步——§5 输出截断改动态公式（预算×5%，最低 16 KiB/2 KiB），固定值移除。
