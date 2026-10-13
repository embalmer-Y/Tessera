# LLD-A09 · 终端门面（terminal-facade）· v0.1（AG1）

> **上游**：HLD-agent v0.2 §2.3（Frontend 第二实现）；决策 DEC-56/57（DEC-12 v1.1 双角色 · Q-38②）、DEC-35（Frontend 抽象）。
> **模块定位**：平台层门面——人直接驱动的交互式终端；与 A01 MCP 门面共享 compose 根（AppContext/audit/tasks/PolicyTable/approvals **一字不差**，无第二套语义）。

## 1. 文件布局与装配

```text
agent/tessera_agent/cli/
  __init__.py
  facade.py      # TerminalFrontend（Frontend Protocol 实现——core/peer.py）
  render.py      # 渲染层（进度/问询/审批/终报——纯函数，可测）
agent/tessera_agent/__main__.py（增）  # `tessera-agent run` 子命令
```

装配：`build_terminal_app(ctx)` —— 同一 `AppContext` 构造（compose 根复用）；**CLI 进程内禁起 HTTP/MCP 门面**（单门面进程纪律，资源与审计清晰）。

## 2. Frontend Protocol 实现

`TerminalFrontend` 实现 core/peer.py 既有 `Frontend` 协议面（会话启动/进度事件/问询/审批呈现/终报）——A01 的 McpFrontend 为第一实现，本模块为**第二实现**（HLD §6：DEC-35 缝首次兑现；未来 ACP 适配器为第三）。事件消费 = A00 任务事件流 + A08 轮事件（§1 单一来源，两门面同源）。

## 3. 命令面（`tessera-agent` CLI 增 `run` 子命令）

```text
tessera-agent run "<需求文本>" [--resume <task_id>] [--yes] [--json] [--plan-confirm]
                    [--board <dbn>] [--deploy]      # --deploy = 收敛后自动走 app_deploy（strict 审批仍拦）
```

- 默认交互模式；`--yes` = 问询全取默认选项（**strict 审批不豁免**——安全默认，Q-38② 既定）；`--json` = JSONL 流式输出（CI 消费，每行一事件）；`--plan-confirm` = PLANNING 后暂停等确认（config 默认开）。
- 退出码：0 = CONVERGED+PACKAGED（--deploy 时含部署判据命中）；1 = FAILED（证据路径在终报）；2 = 参数/环境错误。

## 4. 交互契约（时序）

```text
需求输入 → spec_check 门（errors 阻塞级 → 交互修正提示）
  → PLANNING 完成 → [计划呈现 + 确认]（--plan-confirm）
  → 逐轮进度：轮号/状态迁移/计划项变化/证据摘要（编译✓ sim✗ 等一行式）
  → 交互点三处：
     ① spec 歧义问询（选项呈现，默认项标注）
     ② strict 审批（approval_id + args_preview + reason 呈现；token 经 getpass 无回显输入）
     ③ 判据确认（终报前——判据表呈现，owner 认可判据行）
  → 终报：状态/判据命中行/产物路径（wasm+tsap）/工作区路径/审计 ID/预算用量
```

- **审批语义**：`sys_approve(approval_id, decision, token)` 同一调用链——终端 getpass 输入即"人在场"（DEC-57 观察项：委托人假设在终端形态下成立——token 从未离开本进程环境）。
- SIGINT：第一次 = 当前轮完成后快照 + 优雅退出（提示 `--resume <task_id>`）；第二次 = 立即快照退出（快照原子写保证一致）。

## 5. 渲染层（render.py——纯函数）

- 进度行式渲染（非全屏 TUI——**可维护性取舍**：无 curses 依赖、输出可重定向、--json 同源）；计划项 checkbox；证据摘要 = detail 首行 + 计数。
- 渲染函数纯输入输出（事件→字符串），单测直接断言字符串——**交互逻辑与渲染分离**（测试面最大化）。

## 6. 生命周期与并发

- 单任务单会话（V1：终端会话一次驱动一个创作任务——HLD §9 裁剪清单）；长编译/sim 经 verifier 同步调用 + asyncio.to_thread（A00 子进程纪律），渲染层收到轮事件流。
- 任务注册表绑定：创作任务 = TaskRegistry 既有句柄（MCP 侧 task_status 可观测终端任务——**两门面互观测**，审计统一）。

## 7. 错误与恢复

- 需求/spec 错误 → 交互修正循环（预算 3——MD0-1 既有模式平移）。
- LLM 提供者错误 → 轮重试 1 次后 FAILED（快照保留可 resume）；网络错误同路径。
- resume 失败（SNAPSHOT_STALE）→ 如实报 + 引导新任务。

## 8. 测试要点（L7；零 LLM/零网络）

- 渲染纯函数：事件→输出字符串矩阵（计划/证据/终报）。
- 交互脚本化：stdin 注入序列（FunctionModel 剧本驱动 A08 循环）——三交互点全覆盖（问询默认/审批 token 对错/判据确认）。
- 模式矩阵：--yes（strict 仍拦断言）/--json 事件流 schema/--resume 续跑端到端/SIGINT 优雅退出快照。
- 装配：TerminalFrontend 与 McpFrontend 共享 PolicyTable 同源断言（审批语义一字不差）。

## 9. 未决依赖

- AG4 消费本规格实现；A08 快照/轮事件（AG3）为运行依赖；`--deploy` 联动 app_deploy 既有 strict 链零改动。

## 修订记录

- v0.1 · 2026-10-13：初版（AG1；HLD-agent v0.2 §2.3 展开；C-7 呈递）。
