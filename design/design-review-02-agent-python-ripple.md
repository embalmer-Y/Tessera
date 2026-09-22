# design-review-02 · Q-18（Agent 全 Python）涟漪审查

> **状态**：v1.0 · 2026-09-22 · 已处置（DR-18…DR-23）
> **任务来源**：owner 2026-09-22 指令（随 Q-18 裁定）——"同时请你完整review一边之前的design是否需要进行一定的调整。有调整的地方需要重新research。"
> **审查对象**：全部已生效设计面（`design/` 8 份规格 + `design-review-01`/`final-selfcheck` 存档 + `docs/std/` 5 份规范 + `docs/dev-environment.md`）× 变更（DEC-37：Agent 实现语言 TypeScript→Python、基座 pi→PydanticAI+FastMCP+自建编码工具集）。
> **方法**：① 全文触点 grep（TypeScript/Node/pi/Agent/MCP/skill/打包/zenoh 客户端/签名）逐一核对；② 受影响项派 2 路子代理实查补充核验（→ `docs/research/R5-agent-python-stack.md`）。

## 1. 总结论

**固件框架设计套件（HLD + 8 份 LLD）零改动。** 论证：Agent↔固件的一切合同都是**格式与协议**——TSAP 容器（DEC-21）、zenoh key 命名空间（DEC-18/26）、prov CBOR schema（DEC-30⑤）、sys 命令面（DEC-30①）、MCUmgr 通道（DEC-23）——两侧语言解耦是这些设计的既定性质；grep 实证 design/ 内**零** TypeScript/Node/pi/TS SDK 触点。需要调整的全部在 **Agent 轨道自身的输入层**（研究结论修订 + 规范套件两处待补节），且多数为"实施期增补"而非"现文档改正"。

## 2. 逐文档审查矩阵

| 文档 | 触点检查结果 | 结论/动作 |
|---|---|---|
| `design/HLD-firmware-framework.md` | Agent 仅里程碑级提及（DEC-15 阶段二）；zenoh 拓扑为固件侧职责（§3.5） | **零改动** |
| `design/LLD-00-common.md` … `LLD-ts-periph.md`（8 份） | grep 零语言/基座触点；TSAP 验签为固件侧（C/WAMR）职责，不含 Agent 侧实现假设 | **零改动** |
| `design/design-review-01.md` / `final-selfcheck.md` | 存档文件 | 不适用 |
| `docs/std/coding.md` | 适用范围原文即 "agent/ 与工具（Python）"——规范套件起草时已假设 agent 侧 Python，DEC-37 与之**一致而非冲突** | **零改动** |
| `docs/std/testing.md` | L7 = PC 侧 pytest（Agent/模拟器/工具链），Python 假设一致 | 零改动 |
| `docs/std/versioning.md` | §4 外部依赖钉住仅覆盖 west manifest（固件）；agent/ 的 Python 依赖钉版（pyproject/lock）无节 | **待补**（DR-18，agent 骨架批次增补，不阻塞 HLD） |
| `docs/std/progress.md` / `README.md` | 里程碑结构未涉语言 | 零改动 |
| `docs/dev-environment.md` | 固件 venv（Python 3.12）已列；agent 侧 venv/工具链未列 | **待补**（DR-19，agent 骨架批次增补——复用 WSL Python 3.12，独立 venv） |
| `docs/research/R3/R4` | pi/TS SDK 结论被 DEC-37 取代 | 修订记录标注（本批完成：R3→v1.0.3、R4→v1.0.2） |
| `decisions.md` DEC-33/36 原文 | 含 pi/TS 表述 | **不篡改原 DEC**；DEC-37 修订条款已登记（基座/语言变更 + ③ skills 加载改自建 + 闸落点改 PydanticAI hooks） |

## 3. 发现与处置（DR-18…DR-23）

| # | 发现 | 处置 | 时机 |
|---|---|---|---|
| DR-18 | versioning.md 缺 Python 依赖钉版节（agent/ 用 pyproject + lock；纪律同 west manifest：禁浮动引用、升级走显式提交+回归） | 增补 §（含 R5 §6 钉版清单落点） | agent 骨架批次 |
| DR-19 | dev-environment.md 缺 agent 开发环境（venv 隔离、pip 源、钉版安装） | 增补节 | agent 骨架批次 |
| DR-20 | DEC-36③ Skills 加载从"pi 原生"改为**自建 skill loader**（读 SKILL.md 目录注入会话；对外分发形态不变，仍是开放标准包） | Agent HLD 输入 | Agent HLD |
| DR-21 | TSAP Python 签名栈定案：`cbor2(canonical=True)` + `pycose` + `cryptography`；**纪律**：protected header 单键 `{1:-8}`（规避 pycose 非 canonical map 序）；**fallback**：DIY（cryptography+cbor2 手构 RFC 9052，约 30-60 行）与 pycose 双实现互验 | Agent HLD 工具规格输入 | Agent HLD |
| DR-22 | zenoh 客户端 = `eclipse-zenoh`（同步 API，asyncio 需线程包裹）；**三方同 minor 钉版纪律**（router/zenoh-python/zenoh-pico = 1.10.1）；Zenoh 2.0（计划 2026 H2）为联合升级风险项，**牵动固件 M3a** | 登记为 M3a 前置检查项 + Agent HLD 输入 | Agent HLD + M3a |
| DR-23 | asyncio 全链路纪律：工具内禁阻塞调用（exec/长命令必须 subprocess/线程池）；并行工具默认并发需按确定性合同显式选择（`sequential=True`/`parallel_tool_calls=False`） | Agent HLD 编码规范条目（并入 coding.md §Python 或 HLD 附录） | Agent HLD |

## 4. R5 核验摘要（详见 R5 报告）

- **审批闸超预期**：PydanticAI Hooks（`wrap_tool_execute`/`ApprovalRequired`/`requires_approval=True`）为 pi beforeToolCall 的**超集**（可阻断、可改写、可挂起待批）；FastMCP Middleware 提供 server 侧第二层闸。
- **agent 嵌入 MCP server**：PydanticAI 官方文档正名的模式（`@server.tool()` 内 `agent.run()`）；FastMCP 4 单部署覆盖 2024-11-05…2026-07-28 全 spec 版本——DEC-36① 的兼容基线要求直接满足。
- **长任务**：V1 维持自建句柄（进程内注册表 + status/log 查询工具）；FastMCP tasks（官方 Tasks 扩展实现）留作多进程阶段选项——与 DEC-36② 一致。
- **风险前三**：FastMCP 4 极新（钉版 + 保守特性面）；PydanticAI v2 年轻（minor 钉版 + ModelMessagesTypeAdapter 审计导出）；pycose 停滞（单键纪律 + DIY 双验）。

## 5. 结论

DEC-37 的变更半径完整收敛于 Agent 轨道：固件设计零改动、规范套件零冲突（两处实施期待补节）、Agent 轨道设计输入（R3/R4/R5 + DEC-33…37）已齐备——**Agent HLD 可以启动**。

## 修订记录

- v1.0 · 2026-09-22：初版（DR-18…DR-23 全处置；随批完成 R3/R4 修订标注与登记册同步）。
