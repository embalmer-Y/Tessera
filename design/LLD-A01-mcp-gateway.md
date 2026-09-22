# LLD-A01 · MCP 网关（FastMCP 门面）· v0.1 草案

> **上游**：HLD-agent §2/A01；决策 DEC-34（双层）/DEC-36①②（stateless 纪律/长任务句柄）。事实基线 R5 §2（FastMCP 4.0.5）。

## 1. 实例化与运行形态

- `FastMCP("tessera-agent")`；传输 V1 = **stdio only**〔Q-19 提案 2〕（Streamable HTTP 预留——FastMCP 同部署已支持，开启属配置项不属代码变更）。
- 协议基线：默认 handshake 时代协商（2024-11-05…2025-11-25 任一客户端可连）；不依赖 elicitation/sampling/roots（DEC-36① 弃用规避）；长任务走自定义句柄（DEC-36②），不启用 fastmcp-tasks。
- 进程模型：单进程单事件循环；`tessera-agent` CLI 入口（`python -m tessera_agent`）启动即 stdio 服务。

## 2. 工具注册表（双层清单 = 公共 API 面，变更走 review 门）

### 2.1 原子层（19 个；`<域>_<动作>`；⚠ 全清单确认随 C-5/Q-19 提案 1）

| 工具 | 类别 | 句柄 | 入参（摘要）→ 返回（摘要） | 审批 |
|---|---|---|---|---|
| sys_ping | ro | 否 | – → {pong, version} | auto |
| sys_get_info | ro | 否 | – → {version, config 概要, providers 状态, 固件工作区状态} | auto |
| sys_pending_approvals | ro | 否 | – → [{approval_id, tool, args_digest, reason, expires_at}] | auto |
| sys_approve | ro* | 否 | {approval_id, decision: allow/deny, token} → {result} | auto（自身即审批动作，token 校验见 §4） |
| task_status | ro | 否 | {task_id} → {state, tool, created_at, ttl, result?, error?} | auto |
| task_log | ro | 否 | {task_id, offset?, limit?} → {lines[], truncated} | auto |
| task_cancel | 写 | 否 | {task_id} → {state} | auto |
| fw_workspace_status | ro | 否 | – → {branch, commit, dirty, boards[], 测试清单} | auto |
| fw_build | 写 | 是 | {board, target: app/tests, extra_args?} → {task_id} | confirm |
| fw_twister | 写 | 是 | {platform, tests?, extra_args?} → {task_id} | confirm |
| fw_pytest | 写 | 是 | {scope?} → {task_id} | confirm |
| sim_validate_scenario | ro | 否 | {scenario} → {errors[]} | auto |
| sim_run | 写 | 是 | {scenario, rebuild?} → {task_id} | confirm |
| tsap_keygen | 写 | 否 | {name, out_dir?} → {pub_key_path}（私钥仅写文件 0600，不返回） | strict |
| tsap_package | 写 | 是 | {wasm_path, manifest, key_path} → {task_id}（结果含包路径+签名摘要） | confirm |
| tsap_verify | ro | 否 | {package_path, pub_key} → {valid, manifest, checks[]} | auto |
| deploy_discover | ro | 否 | {timeout?} → [{cube_id, node, endpoints, version?}] | auto |
| deploy_status | ro | 否 | {cube_id} → {sys_get-info 快照, link, safety} | auto |
| deploy_push_app | 出界 | 是 | {cube_id, package_path} → {task_id} | strict |
| deploy_push_prov | 出界 | 是 | {cube_id, prov} → {task_id} | strict |

### 2.2 高层任务层（2 个；DEC-34 "V1 先 2-3 个"）

| 工具 | 编排（见 HLD S2/S5） | 审批 |
|---|---|---|
| app_develop | 需求→计划(PlanDto)→编码(经编辑工具)→fw_build/fw_twister→sim_run→tsap_package；返回 {task_id}，结果含产物路径+会话审计 ID | 链内各步按各自类别；strict 步挂起等宿主 |
| app_deploy | tsap_verify→deploy_discover→push_app→deploy_status 验证 | strict |

## 3. 长任务句柄接线（A00 TaskRegistry）

- 耗时类工具 handler：参数校验 → 创建 Task → `asyncio.create_task` 执行体 → **立即返回 {task_id, state:"working"}**（不阻塞超客户端超时：Claude Code 2 min 后台化/Codex 600s）。
- 结果获取：task_status（终态含 result）；task_log 流式排障；句柄 TTL 与状态机见 A00 §2。

## 4. 中间件栈（FastMCP Middleware，server 侧第二层闸）

顺序：Audit（工具流写入）→ Policy（参数白名单复核，兜底 A02 闸）→ RateLimit〔Q-19 提案 10：默认 30 调用/min/客户端〕→ Tool 执行 → OutputLimit（64 KiB 截断）。
审批呈现：agent 会话内 ApprovalRequired 挂起时，A01 同步暴露 `sys_pending_approvals`；`sys_approve` 需 **approval token**（宿主启动时环境变量注入〔Q-19 提案 7〕，防止其他 MCP 客户端代批）；等待超时〔Q-19 提案 4：10 min〕自动 deny。

## 5. 错误与兼容

- TaError → `isError + {domain, code, message, retryable}`（A00 §1）。
- tools/list 确定性排序（name 升序）——利于客户端缓存（2026-07-28 方向一致）。
- 工具描述：docstring 提供英文一句话 + 参数说明（PydanticAI/FastMCP 均从签名生成 schema；`require_parameter_descriptions` 纪律）。

## 6. 测试要点（L7）

- 每工具契约测试：正常/参数错/域错误/超时的返回形状矩阵（录制式，无需 LLM）。
- 句柄：立即返回时延 < 100ms 断言；TTL 到期；cancel 杀进程组验证。
- 中间件：限流触发；输出截断标记；审计行完整性。
- 审批：无 token 拒绝；超时自动 deny；并发多审批互不串扰。
- 兼容冒烟：至少 2 个真实 MCP 客户端（Claude Code + Codex CLI）连 stdio 跑通 sys_*/fw_build〔MA1 退出〕。

## 7. 未决依赖

- Q-19 提案 1/2/4/7/10；A02（高层工具的会话驱动）；A03…A06（原子工具实现）；工具面增删 = review 门（DEC-34）。
