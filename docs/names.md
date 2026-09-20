# docs/names.md · Tessera 命名空间登记表

> 军规 6：跨文档标识符（DEC/Q/M/REQ/模块名/板名）登记于此；**新造先查碰撞**；禁裸单字母作跨文档标识符。
> 登记格式：标识符 | 含义 | 首次出现 | 状态。

## 1. 决策与问题编号

| 标识符 | 含义 | 首次出现 | 状态 |
|---|---|---|---|
| DEC-01 … DEC-16 | 已裁定决策（owner 2026-09-18 裁定） | FOUNDING_PROMPT §1 | 生效 |
| DEC-17 | APP 运行时 = WASM，实现采用 WAMR | decisions.md（Q-01 裁定） | 生效 |
| DEC-18 | 数据面协议 = zenoh（Zephyr 侧 zenoh-pico） | decisions.md（Q-02 裁定） | 生效 |
| DEC-19 … DEC-24 | 裁决批次 1（2026-09-20：Zephyr 4.4+持续跟进 / client+ARM64 宿主 / TSAP 包格式 / 断链参数延长且 prov 可配 / 双 slot+MCUmgr / GitHub CI） | decisions.md | 生效 |
| Q-01 | APP 运行时选型（→ R1） | FOUNDING_PROMPT §9 | 已裁 → DEC-17 |
| Q-02 | 数据面应用层协议选型（→ R2） | FOUNDING_PROMPT §9 | 已裁 → DEC-18 |
| Q-06、Q-07 | design 阶段待裁（2026-09-20 已补通俗解释，待 owner 裁决） | HLD v0.1 / decisions.md §二 | 待裁 |
| Q-10 | LLD 批次默认值清单（线程优先级/栈/队列/容量/探针与回滚参数等 15 组） | LLD v0.1 批次（design/） | 待裁 |
| Q-11 | design review-01 语义批次（sys 命令面授权/共享写语义/APP 状态裁剪/审计简化/prov 模型/内存预算） | design-review-01.md | 待裁 |
| Q-12 | CI 平台与远端仓库托管（M0 前置） | 开发就绪度评估（2026-09-20） | 待裁 |

## 2. 任务与里程碑

| 标识符 | 含义 | 首次出现 | 状态 |
|---|---|---|---|
| K1 | 仓库初始化（骨架 + git + AGENTS.md + decisions.md 录入） | FOUNDING_PROMPT §7 | 2026-09-19 完成，待 review |
| R1 | APP 运行时调研（wasm3/WAMR vs LLEXT vs 脚本类等） | FOUNDING_PROMPT §7 | 进行中（初步笔记已落盘） |
| R2 | 数据面协议选型调研 | FOUNDING_PROMPT §7 | 进行中（初步笔记已落盘） |
| M0 | west 工作区 + native_sim 空模块构建 + CI 骨架 | FOUNDING_PROMPT §7 | 未启动 |
| M1 | ts-core + ts-safety（安全层最小闭环） | HLD v0.1 §7 | 提案（待 HLD 确认） |
| M2 | ts-hal + ts-appmgr + WAMR 集成 | HLD v0.1 §7 | 提案（待 HLD 确认） |
| M3 | ts-net + ts-power + 集成与重放测试 | HLD v0.1 §7 | 提案（待 HLD 确认） |
| kickoff | K1 首次提交的 git tag | FOUNDING_PROMPT §9 | 已打 |
| dec-wamr-zenoh | DEC-17/18 裁定登记提交的 git tag（重大裁决留痕，军规 5） | decisions.md 修订记录 | 已打 |
| dec-19-24 | 裁决批次 1（DEC-19…24）登记提交的 git tag | decisions.md 修订记录 | 已打 |
| DR-xx | design review 发现编号族（当前 DR-01…17，全部处置） | design/design-review-01.md | 存档 |

## 3. 板名（DEC-14 目标板集）

| 标识符 | 含义 | 网络能力备注 |
|---|---|---|
| ESP32-S3 | Espressif 目标板 | 原生 WiFi |
| ESP32-P4 | Espressif 目标板 | 无无线电，需配 ESP32-C6 或用以太网 |
| STM32H7 | ST 目标板 | 有 EMAC，需外挂 PHY |
| RP2350 | Raspberry Pi 目标板 | 需外挂网络模块 |
| native_sim | Zephyr 仿真平台 | CI 平台 |

## 4. 项目与外部名称

| 标识符 | 含义 | 状态 |
|---|---|---|
| Tessera | 本项目工作名（拉丁语"马赛克镶嵌片"）；owner 一句话可全局替换，替换时同步 FOUNDING_PROMPT §0 与全部出现处 | 生效 |
| Galatea | 旧母项目（本固件子项目的剥离来源）；与本项目无开发耦合 | 仅历史引用 |
| physio-handoff | Galatea 仓库 git tag，存旧子项目历史资料（NON-NORMATIVE，事实可复用、结论不复用） | 仅历史引用 |
| WAMR | WebAssembly Micro Runtime（Intel 主导，Apache-2.0，官方 Zephyr 移植）；DEC-17 选定的 APP 运行时实现 | 生效（选型） |
| zenoh / zenoh-pico | zenoh 协议及其嵌入式实现 zenoh-pico（Apache-2.0，官方 Zephyr 模块）；DEC-18 选定的数据面协议 | 生效（选型） |
| router 宿主平台 | zenohd router 部署面：Windows/Linux PC、ARM64 Linux 工业/机器人主板（DEC-20） | 生效 |
| LLEXT | Zephyr 在树可加载 ELF 子系统（实验性）；R1 候选 B，未被选用；如未来作框架内部机制须另立 Q | 存档（未选用） |
| wasm3 | WASM 解释器（MIT，最低维护期）；R1 候选 A1，未被选用 | 存档（未选用） |

## 5. 模块名 / API 名 / 文件格式名

（固件框架模块名 = HLD v0.1 提案态，待 owner 确认后转"生效"；跨文档引用时标注提案态。）

| 标识符 | 含义 | 状态 |
|---|---|---|
| ts-core | 框架核心：初始化编排/事件总线/单调时间/喂狗注册表 | HLD 提案 |
| ts-safety | 安全层：输出保护/三安全态/estop/fail-safe/WDT 框架 | HLD 提案 |
| ts-hal | 统一外设 HAL（权限执行点） | HLD 提案 |
| ts-appmgr | APP 生命周期管理 + WAMR 宿主 | HLD 提案 |
| ts-net | zenoh-pico 数据面封装（命名空间/命令-回执/心跳监视） | HLD 提案 |
| ts-power | 受控供电（DEC-03，经 ts-safety） | HLD 提案 |
| ts-periph | 外设描述与插拔管理（V1 桩） | HLD 提案 |
| ts_time_ms | 单调时间服务 API（合同 9 唯一时间源） | HLD 提案 |
| ts_safety_commit | 唯一写路径出口 API（合同 2） | HLD 提案 |
| ts_res_t / TS_E_* | 框架错误码类型与错误码族（LLD-00 §2） | LLD 提案 |
| TS_EVT_* | 事件总线事件 ID 族（LLD-ts-core §4） | LLD 提案 |
| CONFIG_TS_* | 框架 Kconfig 前缀（LLD-00 §5） | LLD 提案 |
| TSAP | APP 包容器 magic（"TSAP" u32；格式随 Q-05 定稿） | LLD 提案 |
| ts_api_v1 / ts_perm_v1 | 版本化 APP 导入面 / 能力文法（破坏性变更须升 v2，门③） | LLD 提案 |
| ts-store | 存储抽象模块：分区/meta 掉电安全 kv/prov 只读/noinit（DR-01） | HLD v0.2 / LLD 提案 |
| TS_FAIL_* | 故障原因码族（u32：TS_FAIL_SRC_<<16｜细因，LLD-00 §2.1） | LLD 提案 |
| ts_ctx_t | APP 调用者不透明上下文（防伪造映射，LLD-00 §3.1） | LLD 提案 |
| ts_periph_kind_t | 外设描述符类别枚举（含 TS_PK_ADC，DR-13） | LLD 提案 |

## 修订记录

- 2026-09-19 · K1 建立：登记 DEC/Q 编号、任务号、板名、项目名。
- 2026-09-19 · Q-01/Q-02 裁定登记：新增 DEC-17/18、git tag `dec-wamr-zenoh`、外部选型名（WAMR、zenoh/zenoh-pico、LLEXT、wasm3）。
- 2026-09-19 · design 阶段登记：Q-03…Q-09 待裁批次、里程碑 M1…M3、固件模块名 ts-*（提案态）。
- 2026-09-20 · LLD 批次登记：Q-10 默认值清单、标识符族（TS_E_*/TS_EVT_*/CONFIG_TS_*/TSAP/ts_api_v1/ts_perm_v1）。
- 2026-09-20 · review-01 深化登记：Q-11 语义批次、DR 编号族、ts-store/TS_FAIL_*/ts_ctx_t/ts_periph_kind_t。
- 2026-09-20 · 就绪度评估登记：Q-12（CI 平台与远端托管）。
- 2026-09-20 · 裁决批次 1 登记：DEC-19…24、tag `dec-19-24`、router 宿主平台；Q-06/Q-07 仍待裁（已补解释）。
