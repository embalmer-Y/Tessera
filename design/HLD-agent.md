# HLD · Tessera Agent（AI 开发 Agent）· v0.1 草案

> **状态**：v0.1 草案，待 owner review（C-4）；本文一切未决默认值以〔Q-19 提案 n〕标注，裁决前不进代码。
> **输入（已裁决策）**：DEC-11/12/13（Agent 产出/形态/模拟深度）、DEC-15（阶段二）、DEC-32（Linux）、DEC-33（基座选型 + 多域预留北极星；**DEC-37 修订为全 Python**）、DEC-34（双层 MCP 工具面）、DEC-35（ACP 预留）、DEC-36（交互栈定案）、DEC-37（PydanticAI + FastMCP + 自建编码工具集）。
> **研究事实源**：R3（基座）、R4（交互/生态）、R5（Python 栈 HLD 级核验）。
> **固件侧合同**（本设计的既有约束）：TSAP v1（DEC-21/LLD-ts-appmgr §2）、zenoh 命名空间（LLD-ts-net）、prov CBOR（DEC-30⑤）、sys 命令面 v1（DEC-30①）、native_sim（DEC-13）、安全与确定性合同（AGENTS.md §6）。

## 0. 任务与范围（自包含）

Tessera Agent = PC 侧（Linux/WSL）**全 Python 单进程程序**：封装"模块 API + 模拟器 + 构建工具链"（DEC-12），以 MCP server 形态供其他 AI 工具调用（ZCode/Claude Code/Cursor 等），能力链 = 需求分析 → 软件设计 → 编程开发 → 模拟测试 → 部署（DEC-11/12），产出 = 业务 APP（TSAP 包）**与** 硬件配置（DEC-11）。**北极星（DEC-33）**：平台层与域工具解耦，未来接入 PCB/结构件等域 agent，最终支撑"机器人/Galatea 级项目完全自动化自己生产自己"；V1 范围 = 固件域一个工具域。

**V1 不做**（裁剪清单见 §9）：ACP 适配（DEC-35 预留）、A2A（DEC-36④ 预留）、Streamable HTTP 远程门面、Temporal durable、多域、多客户端并发。

## 1. 系统上下文

```text
┌─────────────────┐   MCP (stdio)    ┌──────────────────────────────────────┐
│ MCP 客户端        │ ───────────────▶ │ tessera-agent（单进程，Python 3.12）    │
│ ZCode/Claude/    │ ◀─────────────── │  WSL: ~/project/tessera/agent/        │
│ Cursor/Copilot…  │  句柄+轮询/结果    │  （宿主 = owner 的 Linux/WSL 环境）      │
└─────────────────┘                  └──────┬───────────────────────────────┘
（人类：ACP 客户端 = 预留缝，DEC-35）             │ 子进程调用（只读白名单+审计）
                                            ▼
        ┌────────────────────────────────────────────────────────┐
        │ 开发工作区（既有资产，不复制）:                            │
        │  ~/project/tessera（本仓库: 固件源码/测试/规格）            │
        │  ~/project/zephyrproject（west 工作区 + .venv 工具链）     │
        └────────────────────────────────────────────────────────┘
                                            │ zenoh（部署/查询，MA3）
                                            ▼
                                     立方体（固件）/ zenohd router
```

## 2. 分层架构与模块清单

```text
┌─ 门面层 ──────────────────────────────────────────────┐
│ A01 mcp-gateway：FastMCP 4 门面（双层工具面/长任务句柄/审批呈现）│
├─ 会话编排层（平台层，与传输解耦 = ACP/A2A 预留缝）─────────┤
│ A02 agent-core：会话编排/审批闸/结构化产物/审计导出            │
│ A07 skills+platform：skill loader + DomainPack 接口 + 预留   │
├─ 域工具层（固件域 = 第一个 DomainPack）──────────────────┤
│ A03 fw-tools：workspace/build/twister/pytest 子进程封装      │
│ A04 sim-harness：native_sim 仿真驱动/场景/重放报告           │
│ A05 tsap-tools：打包/签名/验签（Python 栈）                  │
│ A06 deploy-net：zenoh 客户端/部署/查询                      │
├─ 公共 ────────────────────────────────────────────────┤
│ A00 common：错误模型/任务模型/审计/配置/编码纪律              │
└───────────────────────────────────────────────────────┘
```

| 模块 | 职责 | 规格文档 |
|---|---|---|
| A00 common | 错误模型（TA_E_*）、任务模型（对齐 Tasks V2 语义）、审计双流、配置、asyncio/子进程纪律 | `LLD-A00-common.md` |
| A01 mcp-gateway | FastMCP 实例、工具注册表（§2.1 双层清单）、长任务句柄、中间件、审批呈现工具对 | `LLD-A01-mcp-gateway.md` |
| A02 agent-core | SessionOrchestrator、PydanticAI Agent 构造、审批闸（Hooks）、结构化产物校验、提供者配置、会话审计导出 | `LLD-A02-agent-core.md` |
| A03 fw-tools | fw_* 工具（west/twister/pytest 子进程封装、流式日志、超时/白名单） | `LLD-A03-fw-tools.md` |
| A04 sim-harness | sim_* 工具（场景文件、native_sim 运行、确定性比对、L4 重放对接） | `LLD-A04-sim-harness.md` |
| A05 tsap-tools | tsap_* 工具（manifest 镜像 schema、cbor2+pycose+DIY 双验、密钥管理） | `LLD-A05-tsap-tools.md` |
| A06 deploy-net | deploy_* 工具（zenoh-python 封装、三方同 minor 纪律、sys 命令消费） | `LLD-A06-deploy-net.md` |
| A07 skills+platform | skill loader、V1 最小 skill 集、DomainPack 接口、A2A/ACP 接入缝 | `LLD-A07-skills-platform.md` |

### 2.1 MCP 工具面（双层，DEC-34；完整规格见 A01）

**原子层（V1 = 19 个，命名 `<域>_<动作>`）**：sys_*（4：ping/get_info/pending_approvals/approve）、task_*（3：status/log/cancel）、fw_*（4：workspace_status/build/twister/pytest）、sim_*（2：validate_scenario/run）、tsap_*（3：keygen/package/verify）、deploy_*（4：discover/status/push_app/push_prov）。
**高层任务层（V1 = 2 个）**：app_develop（需求→…→打包全链编排）、app_deploy（包→部署→验证）。
长任务工具（fw/sim/app/tsap/deploy 的耗时类）统一**立即返回任务句柄**，经 task_* 查询（DEC-36②）。

## 3. 决策映射（DEC → 架构落点）

| DEC | 落点 |
|---|---|
| DEC-33/37 | 全 Python 单进程；平台层（A00/A02/A07）与域工具（A03…A06）解耦 = DomainPack；北极星预留见 §6 |
| DEC-34/36① | A01 = FastMCP 4（单部署覆盖全 spec 版本；V1 只用 stdio + handshake 时代语义）；双层工具面 |
| DEC-36② | A00 任务模型（对齐 Tasks V2：working/input_required/completed/failed/cancelled）+ A01 句柄轮询工具 |
| DEC-36③ | A07 skill loader（自建，DEC-37 修订）+ skills 分发包 |
| DEC-36④ | A07 A2A 接入缝（§6.2）；多域组合默认 = 上层编排 + 域 agent 各自 MCP 面 |
| DEC-35 | A02 Frontend 抽象（MCP 门面为唯一 V1 实现；ACP 适配器 = 后补模块）（§6.3） |
| 无豁免（FOUNDING_PROMPT §6） | 三层强制：审批闸（A02 Hooks）→ 工具内校验（产物必经签名/检查）→ 审计留痕（A00 双流）；§5 |

## 4. 关键场景时序（摘要）

- **S1 原子直调**：MCP 客户端 `fw_build` → A01 校验参数/中间件 → A03 spawn 子进程（venv west）→ 立即返回 taskId → 客户端 `task_status` 轮询 → 结果（build 产物路径+摘要）。
- **S2 全链开发**：客户端 `app_develop(spec)` → A02 创建 agent 会话（PydanticAI）→ 模型经审批闸调用 fw_*/sim_*/tsap_* 工具迭代 → 结构化产物（PlanDto/AppConfigDto 校验，ModelRetry 兜底）→ tsap_package 签名 → 返回任务句柄，产物路径+审计 ID 入结果。
- **S3 审批**：模型请求 deploy_push_prov（强制审批类）→ 闸挂起（ApprovalRequired）→ A01 暴露 sys_pending_approvals → 宿主/客户端 sys_approve（带 token）→ 闸放行或超时拒绝。
- **S4 长任务**：任何 >〔Q-19 提案 5〕秒工具 = 句柄化；task_log 分页流式取日志。
- **S5 部署**：app_deploy → tsap_verify 复验 → deploy_discover 定位立方体 → push_app（分块+回执）→ deploy_status（sys_get-info 确认版本/健康）。

## 5. 安全与豁免链（Agent 无豁免）

1. **审批闸**（A02）：工具分三类策略——`auto`（只读：sys_get_info/task_*/fw_workspace_status/sim_validate…）、`confirm`（变更工作区：fw_build 等——V1 由会话策略配置〔Q-19 提案 7〕）、`strict`（出界：deploy_*、tsap_keygen——必须宿主显式批准，超时拒绝）。
2. **工具内强制**（真正的硬边界）：tsap_package 拒绝无签名输出；deploy_push_* 复验签名后才传输；sim_run 场景先过 schema 校验。闸可被绕过的风险由"产物必经工具"对冲——agent 无法绕过 tsap_package 产出可部署包。
3. **审计双流**（A00）：①会话流（ModelMessagesTypeAdapter JSONL，conversation_id/run_id）；②工具流（每次调用：工具名/参数摘要/结果状态/时长/审批人）。V1 全量落盘不滚动〔Q-19 提案 8〕。
4. **确定性同构**（合同 9 在 Agent 侧）：默认 `parallel_tool_calls=False`；提供者配置快照入审计（模型/温度/seed 若有）；模拟验证走 A04 确定性比对。
5. **不学习同构**（合同 10）：审批策略/限值只来自 config（人工维护），运行时不自修改。

## 6. 多域预留与北极星（DEC-33）

### 6.1 DomainPack 接口（A07）
固件域实现为第一个 DomainPack：注册（工具集 + skill 包 + 审批策略 + 产物校验器 + 部署器）。未来 PCB/结构件域 = 新增 DomainPack，不改平台层。跨域组合默认 = 上层编排 agent 把各域 agent 当工具（各自 MCP 面）。

### 6.2 A2A 预留（DEC-36④，owner 要求显式记录）
接入缝：A02 Frontend 抽象旁预留 `PeerTransport` 接口（Agent Card 生成 + 对等任务委托）；启用条件 = 跨主体/长周期对等场景（Galatea 规模）。V1 仅留接口与数据模型注释，不实现。

### 6.3 ACP 预留（DEC-35）
Frontend 抽象：会话编排层不绑定传输——V1 唯一实现 = MCP 门面；后补 ACP 适配模块（事件翻译 + 权限应答回注）即可让 Zed/JetBrains 人肉驱动同一会话。

## 7. 里程碑（Agent 轨道：MA-x；与固件 M-x 并行）

| # | 内容 | 依赖 | 退出标准 |
|---|---|---|---|
| MA0 | agent/ 骨架（包结构/config/CI 接线）+ DR-18/19 补节（versioning/dev-env） | 无（可与 M1 并行） | CI 绿（pytest+lint）；Q-19 已裁 |
| MA1 | A00+A01+A02+A03：网关/编排/审批闸/审计/fw_* 最小集 + sys_*/task_* | MA0 | MCP 客户端实测：build/twister 句柄化跑通；审批流实测 |
| MA2 | A04+A05：sim 场景运行/重放报告 + TSAP 打包签名验签（双实现互验） | MA1；固件 M1（L4 重放雏形）；固件 M2a（TSAP 格式定稿） | 往返签名测试绿；smoke 场景确定性比对绿 |
| MA3 | A06+A07：zenoh 部署通道 + skill 集 + app_develop/app_deploy 高层链 | MA2；固件 M3a（ts-net） | 端到端：spec→APP 包→部署到 native_sim/router 仿真立方体 |

## 8. 测试策略总览（对齐 docs/std/testing.md）

- L7（PC 侧 pytest）为主战场：每模块单测 + 工具契约测试（参数/返回/错误矩阵）；A05 含畸形包矩阵（对齐固件 L1）；A04 确定性比对（同输入序列两次运行逐字节一致）。
- 集成：MA1 起每里程碑配 MCP 客户端冒烟（脚本化）；MA3 端到端。
- CI（GitHub Actions，DEC-24）：lint（ruff〔Q-19 提案 11〕）+ pytest；不依赖 LLM 的测试全绿为准，LLM 相关用录制回放（提供者响应 fixture）。

## 9. V1 范围裁剪清单（超出即另立 Q）

不做：Streamable HTTP 远程门面（stdio only）；Temporal/FastMCP-tasks（自建句柄）；ACP/A2A 实现（预留缝）；多域 DomainPack（接口预留）；多客户端并发会话（上限 2，DEC-38）；docs MCP server（后置可选）；MCP Registry 上架（MA3 后工程事项）。**上下文压缩 V1 即支持**（DEC-38 修订：动态预算 + 阈值 70%，见 LLD-A02 §2）。

## 10. 未决依赖与呈递

- **Q-19**（Agent design 默认值与配置清单，随本批次呈递，见 decisions.md）：包钉版/传输/超时与限额/审批策略默认/审计保留/lint 工具等 12 项。
- **C-4**：HLD-agent v0.1 确认；**C-5**：LLD-A00…A07 v0.1 批次确认。
- 固件侧对齐项：APP 下发通道语义（A06 §未决——待固件 LLD-ts-appmgr 安装入口定稿后对齐，MA3 前完成）。

## 修订记录

- v0.1 · 2026-09-22：初版（owner 指令启动 Agent design；输入 DEC-33…37 + R3/R4/R5；Q-19/C-4/C-5 呈递）。
- v0.1.1 · 2026-09-22：Q-19 → DEC-38 同步——§9 裁剪清单移除"不做上下文压缩"（改为 V1 支持，动态预算+阈值 70%）；会话并发上限出处标注 DEC-38。
