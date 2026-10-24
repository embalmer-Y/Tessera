# docs/history/review-archive.md · 历史评审与自检档案（合并归档）

> **本文件是什么**：2026-10-24 仓整理（DEC-78）将九份一次性评审/自检报告合并为
> 单一档案——原文逐字保留，节标题保留原文件名（IR-xx / IR2-xx 发现编号为代码
> 出处注释所引，溯源链不断）。历史登记不回溯：正文内容未做任何改写。


---

## 原 `design/final-selfcheck.md`（2026-09-21）

# 最终自检报告（final-selfcheck）· 2026-09-21 · 交 owner 人工检查前执行

> **目的**：在 owner 人工检查（C-1/C-2/C-3 文档确认）前，对全库做最后一轮机械 + 交叉自检。
> **方法**：① 机械扫描（残留未决标注/编码/git 状态/tag）；② 登记册 ↔ 设计文档 ↔ 命名登记三方核对；③ 流程门状态核对。
> **结论**：**4 项发现，全部当场处置完毕；未发现阻断性问题，具备交付人工检查条件。**

## 一、机械检查结果

| 检查项 | 结果 |
|---|---|
| 全库 UTF-8 无 BOM | ✅（扫描通过） |
| git 工作区 | ✅ 干净（本报告批次提交前） |
| tag 完备性 | ✅ kickoff / dec-wamr-zenoh / dec-19-24 / dec-25-26 / dec-27-29 / dec-30 共 6 个，与 decisions.md 修订记录一一对应 |
| 设计文档残留未决标注 | ✅ 清零（处置 SC-02 后复扫为空） |

## 二、发现与处置（SC 编号族，已登记 names.md）

| # | 严重度 | 发现 | 处置 |
|---|---|---|---|
| SC-01 | 中 | names.md 中 Q-12 状态滞后（仍标"待裁"，实际已裁 → DEC-24） | ✅ 已改为"已裁 → DEC-24" |
| SC-02 | 中 | design/ 内约 30 处"〔Q-xx 提案〕"标注未随裁决收敛（Q-04→DEC-20、Q-05→DEC-21、Q-08→DEC-22、Q-09→DEC-23、Q-10→DEC-27）——读者会误以为仍是未决值 | ✅ 全量替换为 DEC 编号并复扫清零；LLD-00 头部"未决承载"说明改为"出处规则（DEC-27）" |
| SC-03 | 低 | HLD/LLD 修订记录缺 2026-09-20/21 裁决同步行（git 有痕、文档无痕） | ✅ 全部补齐（HLD v0.2.1、LLD v0.2.1/v0.1.1） |
| SC-04 | 低 | HLD §4.3 看门狗仍写旧值 5s，与 DEC-22 的 10s 矛盾（值级不一致，比标注滞后更严重） | ✅ 修正为〔DEC-22：10s〕 |

## 三、登记册 ↔ 设计核对（Q 全链映射）

| Q | → DEC | Q | → DEC |
|---|---|---|---|
| Q-01（运行时） | DEC-17（WAMR） | Q-07（逻辑节点） | DEC-26（仅预留） |
| Q-02（协议） | DEC-18（zenoh-pico） | Q-08（断链参数） | DEC-22（延长+prov 可配） |
| Q-03（Zephyr 版本） | DEC-19（4.4+持续跟进） | Q-09（存储/OTA） | DEC-23（双 slot+MCUmgr） |
| Q-04（zenoh 拓扑） | DEC-20（client+ARM64 宿主） | Q-10（默认值 15 组） | DEC-27（14 项按建议+每板堆） |
| Q-05（包格式） | DEC-21（TSAP） | Q-11（语义 6 项） | DEC-29/30（每板预算+①-⑤ 按建议） |
| Q-06（执行模式） | DEC-25（fast+WASI 关+AOT 留） | Q-12（CI/远端） | DEC-24（GitHub Actions） |

- **Q-01…Q-12 全部裁毕**（对应 DEC-17…30，共 14 项，全部附 owner 原文与日期）。
- 设计文档（HLD v0.2.1 + LLD-00 v0.2.1 + 八模块 LLD）内的全部数值/语义出处均可追溯到 DEC 编号；各 LLD 未决依赖行已收敛（多数清零）。

## 四、流程门状态

- **当前唯一开着的门**：C-1（HLD v0.2.1 确认）/ C-2（LLD v0.2.1 批次确认）/ C-3（规范套件批准 → tag `std-v1`）。
- 三项确认后 M0 开工（west 4.4 + native_sim + GitHub Actions + LICENSE + 宿主环境验证）；远端地址待 owner 提供（DEC-24）。

## 五、owner 人工检查指引（建议阅读顺序，约 30–40 分钟）

1. `decisions.md` §一 **DEC-19…30 十行**（5 分钟）——核对每行语义与您四轮裁决的意图一致，尤其补充语义三处：DEC-19"持续跟进"、DEC-20"ARM64 宿主"、DEC-22"延长+可配"；
2. `AGENTS.md` §1 当前状态（1 分钟）——流程位置与待办；
3. `design/HLD-firmware-framework.md` **v0.2.1**（10 分钟）——重点 §2 分层图、§4.1 合同映射表、§4.4 初始化顺序、§4.5 关键时序、§4.6 每板预算表；
4. LLD 抽查两份核心：`LLD-ts-safety.md`（唯一写路径/estop/三安全态）、`LLD-ts-appmgr.md`（TSAP 验签/符号过滤装配/回滚）（10 分钟）；
5. `docs/std/` 四件规范（8 分钟）——批准即生效（testing 的五项机械检查是后续所有 impl 的硬门）；
6. 可选：`docs/research/R1-app-runtime.md` §5.6（PSRAM 事实）、`design/design-review-01.md`（17 项审查存档）。

## 修订记录

- 01 · 2026-09-21：首次最终自检（SC-01…04 全处置），交 owner 人工检查。


---

## 原 `design/impl-review-m1.md`（2026-09-22）

# impl-review-m1 · M1 实现自检记录

> **状态**：v1.0 · 2026-09-22 · owner 指令"请你进行review检查然后继续进行开发"触发（M1 退出 review 门内的自检处置留痕）。
> **对象**：提交 `59b0a82`（M1 交付）的 firmware/module/tessera 源码 + 测试 + L5 脚本。
> **方法**：逐文件复查（重点：并发路径、estop 竞争、锁存生命周期、审计一致性、L5 脚本边界）。

## 发现与处置（IR-01…IR-04）

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| IR-01 | **缺陷（高）** | `ts_safety_clear_fault` 在 `forced≠0` 时直接拒绝，而没有任何路径复位 forced → **estop 一次即永久锁死**（重启前 clear 永远失败）。LLD §5 原意是"复位只经 clear_fault 发生"，非"clear 也被拒" | 已修：clear_fault = 锁存唯一释放路径（复位 forced + estop 补发宣布位 + 条件恢复状态）；测试更新（清除→恢复 ACTIVE→写路径恢复→二次 estop 可再锁存） |
| IR-02 | 缺陷（中） | commit 末段临界区发现 forced 置位时跳过写回，但返回值/审计仍记 TS_OK——审计会记录一次从未落驱动的"成功"提交 | 已修：`written` 标志，未写回 → res=TS_E_STATE 并如实审计 |
| IR-03 | 限制（记录） | `ts_safety_audit_copy` 无锁读取环形（与 commit 并发理论上可撕裂） | V1 已知限制：单读消费（遥测/导出，M3 接入时加锁或经 sysworkq 串行化）；native_sim 单核抢占下实际风险极低 |
| IR-04 | 说明（记录） | estop ISR 的 DT 粘合（driver_dispatch.c `#if DT_NODE_EXISTS` 分支）在 native_sim 无节点 → 未被执行覆盖 | 板级移植阶段（真机 estop 引脚）补 HIL 验证；已列板级前置项 |

## 复验（全绿）

- L5：5/5；app @ native_sim 构建绿；twister **4/4 配置 100%**（含更新后的 estop 释放/再锁存用例）；仓库 pytest 绿；编码检查绿。

## 结论

IR-01/02 修复后，M1 交付满足退出条件（本地全绿 + DoD 对照 + 收敛留痕完整）；IR-03/04 登记为已知限制/后续验证项。M1 退出随本记录 + owner"继续开发"指令生效。

## 修订记录

- v1.0 · 2026-09-22：初版（IR-01…04 全处置）。


---

## 原 `design/impl-review-m2a-ma2.md`（2026-09-22）

# impl-review-m2a-ma2 · MA0/MA1/MA2 + M2a/M2b 实现审查记录

> **状态**：v1.0 · 2026-09-22 · owner 指令"review 之前几次未进行 review 的代码，确认没问题后继续开发"触发。
> **对象**：MA0（814a6ce）/ MA1（9183bf3）/ M2a（cc65dc9）/ MA2（4b07964）/ M2b（04bed8c）五笔交付的 agent 侧（tessera_agent 全包）与固件侧（ts-store/TSAP/ts-hal/ts-appmgr）代码 + 测试。
> **方法**：逐文件复查（重点：安装链安全语义、边界/整数回绕、错误传播、fail-open/fail-closed 方向、设计符合性对照 HLD/LLD、密钥纪律）。编号接续 impl-review-m1（IR-01…04）。

## 一、已修复缺陷（IR-05…IR-14，随本批交付）

| # | 级别 | 位置 | 发现 | 处置 |
|---|---|---|---|---|
| IR-05 | **缺陷（高）** | `src/appmgr/pkg.c` | `verify_cose_minimal` 为 **fail-open 桩**：只查 COSE 结构前缀（0xd2/0x84）即返回 TS_OK——真实验签（M2b.2）接入前，任何带伪 COSE 头的包都可安装 | 改 **fail-closed**：非 `CONFIG_TS_TEST` 构建一律 TS_E_INVALID_SIG；测试构建（全部 twister 套件）仍走结构级通过以驱动 slot/meta 链路测试 |
| IR-06 | **缺陷（高）** | `include/ts/tsap.h` | 边界检查 `v->cose_off + 1 > len` 在 cose_off==UINT32_MAX 时 u32 回绕为 0 → 越界检查失效，pkg.c 后续以回绕长度做 OOB 读 | u64 域比较（`total + 1 > (uint64_t)len`）；新增用例：总长恰为 UINT32_MAX 的构造头必须拒绝 |
| IR-07 | 加固（中） | `src/store/part.c`、`src/store/slot.c` | `off + len > size` 在 u32 域可回绕（内部调用方当前均为小值，防御性） | 统一改减法形式 `off > size \|\| len > size - off` |
| IR-08 | 缺陷（中） | `src/hal/api.c` | `ts_pwm_set` 的 hz 打包进 u16（值/100）无域检查：hz>6,553,500 静默截断；permille>1000 无检查 | 超域 → TS_E_PARAM；新增用例（pwm 范围 + 打包值经安全层往返一致） |
| IR-09 | 缺陷（中） | `src/appmgr/slot.c` | 回滚路径 `ts_appmgr_meta_write` 返回值被忽略——写失败时运行态已切 slot 而持久 meta 未切（分叉） | 传播错误 + 运行态全量回退（slot/计数/状态，状态取 prev_state 而非硬编码 ACTIVE） |
| IR-10 | 缺陷（低） | `src/store/prov.c` | prov 的 estop 标志 u32→u8 静默截断 | >0xFF → TS_E_IO（拒绝整条 prov） |
| IR-11 | 文字（低） | `src/hal/perm.c` | 注释声称支持 `"*"` 与 "msg name V1 按 0 处理"，代码实态是数值文法、其余 fail-closed 拒绝 | 注释改为实态（不允许声明未实现的能力形态） |
| IR-12 | 文字/接口（低） | `src/store/noinit.c`、`tools_sim/runner.py`、`gateway/server.py` | ① noinit 注释残留"文件路径"字样（RAM 后端前史）；② runner docstring 仍称"west twister 运行"（实态=west build + 直接二进制）；③ `sim_run(rebuild=…)` 参数从未生效（静默死参数） | ①② 注释修正；③ 移除参数（对齐 HLD 工具面，非语义变更） |
| IR-13 | 缺陷（中） | `tools_tsap/tools.py` | `tsap_package` 产物目录无白名单（keygen 有）——可向白名单外写 .tsap 产物 | 提炼 `_resolve_within` 共用助手，keygen/package 同纪律；新增越界拒绝用例；server 侧白名单根 = workspace（`AppContext.write_roots`，默认 workspace、测试注入 tmp 根） |
| IR-14 | **缺陷（高，设计符合性）** | `gateway/server.py` | HLD §5.1 将 `tsap_keygen` 列为 **strict 类**（必须宿主显式批准，超时拒绝），但 MCP 网关面直行执行——审批闸基础设施（ApprovalBroker/sys_approve）在位却无工具过闸（core 层 `gated_tool` 存在但服务 agent 内循环，MA3 才有消费者） | tsap_keygen 改 **句柄化 + input_required**：任务挂起 → `sys_pending_approvals` 呈现 → `sys_approve`（token）→ 放行执行 / deny·超时 → 任务 failed(TA_E_APPROVAL_DENIED)、无密钥产出；E2E 双路径测试（MCP 客户端实测） |

## 二、登记不修（后续单元处置）

| # | 级别 | 发现 | 去向 |
|---|---|---|---|
| IR-15 | 限制（记录） | `pkg.c` 安装链计算整槽 hash 但未持久化/未与 manifest 比对——启动期无 slot 完整性校验 | M2b.2（manifest CBOR 解码 + wasm hash 比对 + 启动期校验一并落地） |
| IR-16 | 限制（记录） | `ts_log_write` 未过权限裁决（V1 空桩） | M3 日志面真实化时接入 sys 类裁决 |
| IR-17 | 限制（记录） | Agent 侧 manifest `caps` 未做 ts_perm_v1 文法预校验（固件装时拒绝，fail-closed，仅反馈偏晚） | MA3 app_develop 链（早期反馈） |
| IR-18 | 限制（记录） | scenario `t_window_ms` 字段未参与期望评估（runner 只取末值） | M3/MA3 输入注入联动 |
| IR-19 | 限制（记录） | `ts_appmgr_install` 无 app_id 唯一性检查（当前无运行时加载方，重复安装=覆盖语义未定义）；`ts_hal_bind_context` 无重复 app_id 查重 | M2b.2 WAMR 生命周期时定 |
| IR-20 | 限制（记录） | `ts_store_noinit_put` 返回 void（写失败不可观测；留痕 best-effort 语义，丢失=下轮 fresh） | 留观（低风险诊断面） |

## 三、复验（全绿）

- twister @ native_sim：**7/7 配置 26/26 用例 100%**（含 IR-06/IR-08 新用例）
- L5 机械检查：**6/6**（prov 零写不受 IR-10 影响）
- 生产构建：app @ native_sim（无 CONFIG_TS_TEST，含 IR-05 fail-closed 分支）编译链接绿
- 固件 pytest 2/2；agent pytest **34 passed + 1 skipped**（E2E 仿真按设计 env 门控）+ ruff 全绿
- 编码检查：UTF-8 无 BOM 违规 0

## 四、结论

五笔交付中登记的已知限制（WAMR=M2b.2、msg 类文法、deploy_* 未实现）与文档一致；本次发现的实质缺陷集中在**安全边界的方向性**（fail-open 桩、审批闸未接线、边界回绕）与**错误传播**（回滚 meta、参数截断），全部随本批修复并补测试。审查后 M2a/M2b/MA0-MA2 达到"本地全绿 + DoD 对照"退出条件；M2b.2（WAMR）仍为登记的未完成依赖（IR-05/15/19 与其关联）。

## 修订记录

- v1.0 · 2026-09-22：初版（IR-05…20 全处置：修复 10 项 + 登记 6 项）。


---

## 原 `design/design-review-01.md`

# design review-01 · 全库逐条审查报告（2026-09-20）

> **审查范围**：`AGENTS.md`、`decisions.md`、`docs/names.md`、`docs/research/R1、R2`、`design/HLD + LLD-00 + 七模块 LLD`、`docs/std/` 五件。
> **方法**：交叉一致性（HLD↔LLD↔规范↔登记册）、合同映射完备性（十条逐条追）、跨模块契约闭环（A 引用的能力 B 是否定义）、命名登记完备。
> **处置状态图例**：✅ 已修复（本文档批次内完成，见"去向"列）｜📋 登记 Q（随 Q-10 增行/Q-11 呈递）｜✂️ 记入 V1 裁剪清单（HLD §1）。
> **严重度**：高 = 安全语义或跨模块契约缺失；中 = 机制缺失但有明确补救路径；低 = 一致性/完备性问题。

## 一、发现清单

| # | 严重度 | 位置 | 发现（现状 + 为何是问题） | 处置 | 去向 |
|---|---|---|---|---|---|
| DR-01 | 高 | 全库 | **provisioning 与存储无统一抽象**：router locator、node/cube ID、根公钥、zenoh 凭证、功率预算等散见各 LLD 引用"烧录配置/安全参数分区"，但无格式、写入路径、完整性保护、掉电安全定义——合同 10"参数不经运行时修改"无强制落点 | ✅ | 新增 `LLD-ts-store`（分区模型 + prov 只读 + meta 掉电安全 kv + noinit）；Q-11⑤ |
| DR-02 | 高 | HLD §3.5 / LLD-ts-net §5 | **输入遥测机制缺失**：遥测合流只消费 commit 审计（输出侧）；gpio-in/adc 的周期采集与变化上报无归属——输入流"不因保护中断"有通道但无观测面 | ✅ | LLD-ts-hal §5 input monitor（sysworkq 周期 + 变化上报）；Q-10 #14 |
| DR-03 | 高 | HLD §3.5 | **sys 命令面未定义**：命名空间有 sys class，但版本/链路/安全态查询、estop-clear、墙钟设置均无命令定义——Agent 运维面（DEC-12）无接口 | ✅ | HLD §3.5 补 + LLD-ts-net §4 sys 命令表；授权模型 Q-11① |
| DR-04 | 高 | HLD §4.2 / LLD-ts-safety §3 | **断链恢复语义未定义**：SAFE_LINKLOSS→ACTIVE 后输出是否自动回写断链前值未明确——恢复瞬间意外动作属安全语义，必须显式 | ✅ | 明确"不自动回写，shadow 保持安全值，恢复须显式 commit"（LLD-ts-safety §3） |
| DR-05 | 中 | LLD-ts-hal | **共享通道写语义未定**：两个 APP 持有同一通道写权限时行为未定义（互相覆盖？独占？） | 📋 | Q-11②：V1 后写胜出 + 审计含 app_id（不做 claim） |
| DR-06 | 中 | HLD | **内存预算表缺失**：WAMR 堆/zenoh/框架静态无分配基线——RP2350（520KB SRAM 最小板）能否容纳 4×64KB APP 堆无依据 | ✅ | HLD §4.6 预算表（提案值随 Q-11⑥，实测按行修订） |
| DR-07 | 中 | LLD-ts-safety §4 | **审计/留痕持久化缺失**：合同 10"越权拒绝并留痕"——留痕在内存环形缓冲，谁消费、溢出如何、掉电是否保留未定义 | ✅✂️ | 消费 = ts-net 遥测合流 + sys:get-audit 导出；V1 不落盘（掉电丢失）记入 HLD §1 裁剪；Q-11④ |
| DR-08 | 中 | 全库 | **墙钟来源未定义**：只禁其入控制路径，但遥测数据字段的时间戳来源（谁设置墙钟）无定义 | ✅ | sys:set-time（host-only，仅数据字段）；LLD-ts-net §4 |
| DR-09 | 中 | LLD-00 §2 vs LLD-ts-core/safety | **TS_FAIL_* 原因码族被使用但未定义**（TS_FAIL_BOOT_<idx>/TS_FAIL_WDT_<src>）——内部不一致 | ✅ | LLD-00 §2.1 定义（u32：来源<<16｜细因） |
| DR-10 | 中 | LLD-ts-hal §3 | **ts_ctx_t 跨模块类型未定义**：调用者上下文是权限裁决的根，但其结构与防伪造约束不在公共约定 | ✅ | LLD-00 §3.1（opaque 句柄，原生侧映射，wasm 侧整数 id） |
| DR-11 | 低 | LLD-ts-safety §5 | estop GPIO 的 devicetree 绑定与配置细节未写（boot 步骤 1 归属 ts-safety 但无 DT 契约） | ✅ | LLD-ts-safety §5（`ts,estop-gpio` chosen 节点） |
| DR-12 | 低 | LLD-ts-net §3 | keyspace 缺 hb/hb-host/sys 构造器（HLD §3.5 已引用，LLD 未列全） | ✅ | LLD-ts-net §3 补 |
| DR-13 | 低 | LLD-ts-periph §2 | 描述符 kind 复用 ts_ch_kind_t 但 adc 无枚举值（纯输入不进 ts-safety 的表示不一致） | ✅ | 独立 `ts_periph_kind_t`（含 TS_PK_ADC，仅注册 ts-hal 输入侧） |
| DR-14 | 低 | LLD-ts-appmgr §5 | APP 线程 tick/evt 串行化与卸载停止语义未说明（事件并发投递？卸载如何 join？） | ✅ | LLD-ts-appmgr §5 补 mailbox（Q-10 #15）+ join 超时强杀 |
| DR-15 | 低 | HLD §1 | APP 业务状态持久化缺失未声明为裁剪（升级丢状态是行为，应显式告知） | ✂️ | HLD §1 V1 裁剪清单；Q-11③ |
| DR-16 | 低 | docs/std/testing.md | lint 仅列 clang-format/ruff，缺 C 静态分析（cppcheck） | ✅ | testing.md §6 补 |
| DR-17 | 低 | LLD-ts-core §2/§5 | noinit 复位留痕读写依赖存储能力但无归属模块 | ✅ | 并入 DR-01（ts-store noinit 接口） |

## 二、审查结论

1. **研究/登记册/规范套件**（R1、R2、decisions、names、std）：未发现语义级缺陷；std 与 LLD 的机械检查挂点一致（testing.md §3 ↔ LLD-ts-safety §6/§8）。
2. **设计主体**（HLD+LLD）：结构完整、合同映射闭环，但存在 1 项结构性缺失（DR-01 存储层）与 3 项安全语义待显式化（DR-03/04/07），17 项已全部处置（13 修复 / 1 裁剪 / 3 并入 Q）。
3. **登记册增量**：Q-10 表新增 #14/#15 两行数值；新增 **Q-11**（语义批次 6 项）；names.md 登记 ts-store、TS_FAIL_*、ts_ctx_t、DR 编号族。

## 修订记录

- 01 · 2026-09-20：首次全库审查（17 项），随设计深化批次交付。


---

## 原 `design/design-review-02-agent-python-ripple.md`

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


---

## 原 `docs/impl-review-01.md`（2026-09-25）

# impl-review-01 · impl 阶段评审报告（2026-09-25）

> **范围**：owner 指令"对之前的开发进行一次 review"。对象 = 2026-09-25 会话四个交付单元：
> ① DEC-40/41/42 实现批（486427c）② MA3.1 部署面（760ddcb）③ MA3.2 skills/平台域/高层链（0773731）④ M3b ts-power/ts-periph/集成重放（4abcdf7）。
> **方法**：验证全量复跑 + 代码走查（safety/power/periph/net/agent 主链文件）+ 文档一致性核对。
> **结论**：验证声明全部复现（全绿属实）；无 P1 阻断项；**8 项发现**（F-1…F-8，分级见下），其中 F-1 为规约-实现差距、F-2 为潜伏缺陷（与 M3b 已修复的悬垂同类）。修复批建议见 §4，待 owner 批准后作为下一交付单元执行。

## 1. 验证复现（2026-09-25 实测）

| 验证项 | 声明 | 复现结果 |
|---|---|---|
| twister（native_sim，10 套件） | 10/10、44 用例 | ✅ 10/10 配置、44/44 用例 passed，29.31s，无告警 |
| L5 机械检查 | 6/6 | ✅ 6/6（唯一写路径/三态完备/禁用模式/常量出处/estop 路径/prov 零写） |
| 固件 pytest | 2/2 | ✅ 2 passed |
| Agent pytest | 58 passed + 2 skipped | ✅ 58 passed, 2 skipped（E2E 门控 skip，符合设计） |
| ruff（agent） | 干净 | ✅ All checks passed |
| skills 同步 | 一致 | ✅ 源文档与 SOURCES.lock 一致 |

工作树干净（`git status` 空）；`[dbg]` 调试 printk 无残留（工作树与 HEAD 均为零处——开发期调试输出已在提交前清除）。

## 2. 发现清单（按严重度）

分级：P1 阻断 / P2 应修 / P3 登记择机 / P4 观察。

### F-1（P2 · 规约-实现差距）periph/预算事件未经 net 外发

- **现状**：`LLD-ts-periph.md:38` 承诺 DETACH 语义含"key 下线通告（**事件外发**）"；但 `src/net/pub.c` 的事件订阅表（ESTOP/SAFE_STATE_CHANGED/PERM_DENIED/INPUT_CHANGED 四类）未包含 `TS_EVT_PERIPH_DETACH/ATTACH` 与 `TS_EVT_POWER_BUDGET`——三事件仅上事件总线（测试直订可见），不经 zenoh 外发。
- **根因澄清**：pub.c:110 注释"事件总线容量 4——四类全占"系**误读**——`src/core/events.c` 的订阅表为 `subs[id][CONFIG_TS_CORE_MAX_SUBS]`，容量按**事件类型分桶**（各 4 位），四类订阅各占不同桶各 1 位，容量充足。即外发是可实现而未实现（遗漏），非容量受限。
- **后果**：外部观察者（Agent/运维面）看不到插拔归因（哪路外设被拔）与供电预算拒绝事件；通道进 SAFE_FAULT 的**状态迁移**有外发（SAFE_STATE_CHANGED）但缺"为何迁移"的归因。DEC-42 的 kind=32+evt_id 信封机制已就绪，仅缺订阅接线。
- **处置建议**：下交付单元补三事件订阅（复用 pub.c `push_evt` 通用路径，payload 携 uid/kind）+ 修正 pub.c 容量注释 + net 测试断言外发信封。

### F-2（P2 · 潜伏缺陷）ts_periph_register 的 GPIO/PWM 路径注册调用方内存指针

- **现状**：`src/periph/desc.c:67` 将 `&d->safe`（**调用方**传入的描述符内嵌通道）注册进 ts-safety；`src/safety/channel.c:55` 存的是指针（`slot->desc = ch`）。调用方若栈上组装 `ts_periph_desc_t` 即悬垂——与 M3b 实现批在 `src/power/slots.c` 已修复的悬垂**同类**（slots.c 改为静态 `pwr_slot_rec` 内嵌通道并留注释）。
- **现状下未爆的原因**：当前调用方（板初始化桩/测试）均用静态存储描述符；POWER 路径经 `ts_power_register_slot` 有静态拷贝，安全。
- **后果**：API 契约含隐式生命周期要求且未在头文件声明；板级移植/新测试极易踩中（正是 M3b 调试期实际踩过的坑）。
- **处置建议**：改为先落静态表再注册——`descs[desc_count] = *d` 后以 `&descs[desc_count].safe` 注册（与 slots.c 同型修复，成功才 `desc_count++`）；或在 `include/ts/periph.h` 契约注释显式声明"描述符（含 safe 通道与 uid 字符串）须静态存储"。

### F-3（P3 · 装配序耦合）sys 命令表 gated 位按数组下标回填

- **现状**：`src/net/cmd.c:951-953` `ts_net_cmd_sys_init` 先逐个 `ts_net_cmd_register`（填首个空位），再 `table[i].gated = sys_cmds[i].gated`——隐式假设注册按序占 0…N。若未来任何框架模块在 sys_init 之前注册命令（表头偏移），gated 位将**错位到别的命令**：最坏情况部署类写命令（app-begin/chunk/verify/activate）未门控 = 绕过租约准入。
- **现状下未触发**：sys_init 是唯一注册方且表为空起步。
- **处置建议**：注册后按 suffix 回查填位（`find_cmd(sys_cmds[i].suffix)->gated = …`，找不到即 BUILD_ASSERT 级装配错误），消除下标耦合。

### F-4（P3 · 语义顺序）idem 回放检查先于 key/op 匹配与租约门控

- **现状**：`src/net/cmd.c:868-885` 幂等命中即回放，先于 886 行 key/op 双重匹配与 898 行租约门控。
- **风险评估**：副作用安全——回放不重执行（DEC-40 本义），缓存回执对应一次**已通过门控**的历史执行，租约过期后重发同 idem 不产生新副作用。残余问题仅语义层面：同 idem 携同 op 可在**别的 key** 上得到回执（如 get-info 的回执出现在 get-budget key 上，调用方自混淆，同信任域内无越权）。
- **处置建议**（可选，低优先）：把 key/op 匹配挪到 idem 检查之前，回放语义更严；不改亦不构成缺陷。

### F-5（P3 · 已知限制）ts_periph_register 注册链无回滚

- **现状**：`src/periph/desc.c:69-83` 末段 `ts_hal_register_dev` 失败时，已注册的 power 槽/safety 通道无注销 API，残留半注册态——同 uid 重试将永远撞名（`TS_E_PARAM`），需重启恢复。
- **影响评估**：板初始化为编译期静态声明、初始化失败即全系统 fail-safe（合同 6），运行期无重试路径，实际影响低。
- **处置建议**：登记为 V1 已知限制（本报告即登记），不为 V1 增加注销面；板级移植若引入动态注册再议。

### F-6（P2 · 流程）里程碑退出未打 tag（军规 5）

- **现状**：现存 tag 全为裁决/规范批次（kickoff、std-v1、dec-19-24…dec-39、dec-wamr-zenoh）；M1/M2a/M2b/M3a/M3b/MA0…MA3 各退出点提交均无 tag。m0 曾有"CI 上线后打"的明确约定（DEC-24 关联），其余里程碑无此约定。
- **后果**：里程碑边界只能靠提交信息考古，违反军规 5"里程碑与重大裁决打 tag"。
- **处置建议**：对历史里程碑退出提交**补打 tag**（`git tag m1 <sha>` 等，不改写历史，安全）；此后每里程碑退出即打（写入各里程碑 DoD 检查单）。具体 sha 清单在修复批中列出呈 owner。

### F-7（P3 · 潜伏，M2b.2 前置检查项）多线程接入前的并发防护复核

- **现状**：`ts_safety_commit` 持 `commit_lock` + 末段 irq_lock；但 `ts_safety_set_link`/`force_channel_fault`/`channel_recover`（`src/safety/channel.c:94-160`）直接遍历/改写通道表**无锁**；`ts_power_request` 的预算检查→提交（`src/power/slots.c:84-106`）存在 TOCTOU 窗口；lease/idem 缓存按"分发串行"假设无锁（有注释）。
- **现状安全的原因**：当前唯一运行期写入方 = net 单线程（zenoh 回调串行分发）+ 测试直调；estop ISR 路径为原子置位设计。
- **后果**：M2b.2 WAMR 多线程 APP 接入后，并发 commit × set_link/recover 可竞态改写 shadow/state；并发 power_request 可瞬时超预算（两笔各过检查后先后提交）。
- **处置建议**：列入 **M2b.2 DoD 前置检查项**——接入前裁定：扩展 commit_lock 覆盖迁移路径 / 或规定 APP 侧写路径全部经 net 命令面单线程化（后者与"APP 直调 hal 能力"的范围裁定耦合，届时登记 Q）。

### F-8（P4 · 观察项）clear_fault 语义复核未闭环

- **现状**：`src/safety/channel.c:162-179` `ts_safety_clear_fault` 仅迁移状态不回写输出值（clear 后物理输出保持 fault 安全值直至下次显式 commit）。代码注释声明"LLD §3 状态机图未明示复位目标态……语义随 M3 net 联调复核"——M3a/M3b 已退出，该项复核未在文档闭环。
- **评估**：行为与 DR-04（恢复不自动回写、须显式 commit）精神一致，倾向**确认现实现为定案语义**，但需把"待复核"注释转为 LLD 正式条款。
- **处置建议**：修复批中同步 LLD-ts-safety（clear_fault 复位语义定案：状态迁移 + 值不回写）+ 移除代码内"待复核"注。

## 3. 走查通过项（正面确认）

- **安全合同映射**：唯一写路径四段完整（限幅→slew→限流→末段临界区复查 forced，`commit.c`）；供电预算 prov 只读、未加载 = 0 = 全拒（缺省即安全侧）；estop 锁存期 `channel_recover` 拒绝（`TS_E_STATE`）；三安全态齐备 + 安全值自身须落 limits 的注册校验；L5 六项机械检查全过。
- **slots.c 静态存储修复**正确、注释留痕、decisions.md 如实登记该缺陷（军规 7 合规）。
- **lease.c** 与 DEC-41 完全一致（惰性过期、lease_id 单调不复用、同 holder 幂等续期、他人不可代还）。
- **cbor 解析 fail-closed**：`ts_cbor_tstr` 超长即拒（`v >= cap` → false），rid/src/idem 无截断别名风险；v1/v2 首键判别 + 未知键/超集/重复键全拒；v1 携 v2 专属键（idem/to/offset/data）拒绝 → 部署面不可能经 v1 绕过。
- **deploy.py**：租约 finally 闭环（release 失败记录 + TTL 兜底说明）；分块 idem + 仅可重试错误重试；verify 事实对拍 fail-closed（缺键即不等）；闭包默认参绑定避开晚绑定坑；自动发现"恰一在线"策略。
- **平台域纪律**：platform.py 零域 import 有 AST 导入图测试守卫；组合根显式注册；app_develop"无签名不产出"硬点在工具内（链外直调同样强制）。
- **文档同步**：names.md 4 新行 / decisions.md M3b 条目（含缺陷如实记录）/ project-plan v1.5 / LLD-ts-power v0.2、LLD-ts-periph v0.3、LLD-ts-net v0.3.4 均与代码一致。

## 4. 处置建议（修复批 = 建议的下一交付单元，待 owner 批准）

| 项 | 动作 | 规模预估 |
|---|---|---|
| F-1 | pub.c 补订阅 PERIPH_DETACH/ATTACH + POWER_BUDGET（push_evt 通用路径，payload 携 uid/kind/预算三元组）+ 修容量注释 + net 测试断言 | 小（净增 ~40 行 + 测试） |
| F-2 | desc.c 改静态表注册（先 `descs[desc_count]=*d` 再注册 `&descs[desc_count].safe`）或头文件契约注释 | 小 |
| F-3 | sys_init 按 suffix 回查填 gated 位 + 装配断言 | 极小 |
| F-8 | LLD-ts-safety clear_fault 语义定案 + 移除代码"待复核"注 | 极小（纯文档 + 注释） |
| F-6 | 历史里程碑补打 tag（sha 清单呈 owner 核后执行） | 极小 |
| F-4 | （可选）key/op 匹配前移至 idem 检查前 | 极小 |
| F-5/F-7 | 登记（本报告即登记处）；F-7 写入 M2b.2 DoD 前置检查项（project-plan 补一行） | 极小 |

批内验证：twister 全量 + L5 + pytest ×2 + ruff + skills sync（与本报告 §1 同口径）。

## 5. 处置结果（2026-09-25 修复批，owner 批复"严格按照大型项目标准规范修复这些问题"）

F-1/F-2/F-3/F-4/F-8 代码修复 + F-6 十个里程碑 tag 补打（m0…m3b/ma0…ma3）+ F-5/F-7 登记落位（LLD 已知限制 / project-plan M2b.2 开工前置检查项）；新增测试 framework.net test_11 + framework.periph test_04 + test_07 扩展；派生定容一处（pubq PAYLOAD_MAX 64→128B，溯源见 LLD-ts-net §5）。回归全绿：twister 10/10（46 用例）/ L5 6/6 / pytest ×2 / ruff / skills sync。文档同步：LLD-ts-net v0.3.5 / LLD-ts-periph v0.4 / LLD-ts-safety v0.2.3 / project-plan v1.6 / decisions.md 修复批条目 / AGENTS.md（十三）。明细见上述登记处。

---
*登记：docs/names.md（impl-review-01）；AGENTS.md 当前状态已同步。修复批未获批准前不动代码（军规 9）。*


---

## 原 `docs/impl-review-02.md`（2026-10-06）

# impl-review-02 · 全库风险审查（M0→MD1.2b 已交付内容）

> **本文件是什么**：2026-10-06 owner 指令"review 已开发内容是否有其他风险 + 列出未裁决项"的交付报告。
> **方法**：三路只读审查（ts-appmgr/WAMR 宿主面、Agent PC 工具面、store/net/hal/safety 面）+ 主会话对全部"高"级结论逐条亲自复核（grep/读源）。发现编号 **IR2-xx**（impl-review-01 的 IR-xx 不复用）。
> **纪律**：本报告只登记不动手（军规 9）；处置建议见 §5，排期归 owner。全部结论附 file:line 证据。

## 1. 总评

- **安全合同的"机械可查面"执行扎实**：写入路径唯一性、三安全态、断链物理落值、estop 直达纯净、权限运行时 fail-closed、命令面/租约/幂等 fail-closed 均验证成立（§6 正面清单）。
- **两条最重要的缺口是 CI 看不见的静默失效**：①看门狗合同（合同 4）整体空转——生产代码零注册零喂狗、全库无硬件 WDT 使能；②固件侧 COSE 验签为结构桩——生产构建恒拒安装（部署面零可用），TEST 构建放行任意未签名 wasm。三路审查中两个独立方向都撞见了 WDT 缺口（交叉印证）。
- **必须如实登记的框架性事实**：当前所有真机验证（板级四~十、MD1.1/1.2 全部）均在 `CONFIG_TS_TEST` 语义下进行——**生产语义（真验签、生产 prov 通道）从未被点亮**。CI 全绿 ≠ 安全合同闭环。
- **DEC-40/41/42 三项（命令信封 v2 / 控制租约 / 遥测信封）审查证实全部已实现**且 fail-closed（此前疑为"已裁未实现"，现澄清为实现完备；仅 src→审计归因一处欠账，IR2-08）。
- **Agent PC 侧的系统性盲点**："白名单只管写出、不管读入"——`out_dir` 有 roots 白名单，而 `wasm_path/key_path/package_path` 读入路径与 `#include` 预处理读面全部不受约束，构成 prompt-injection 威胁模型下的主机敏感文件外泄链（IR2-03）。

## 2. 高风险（3 项）

### IR2-01 · 看门狗合同（安全合同 4）整体空转——静默失效

**现状**（多证据链，主会话逐条复核）：
1. WAMR 无任何执行边界：构建旗标无指令计量（`firmware/module/tessera/CMakeLists.txt:110-118` 无 `WASM_ENABLE_INSTRUCTION_METERING`），runtime 全文无 `wasm_runtime_set_timeout` 类调用——`wasm_runtime_call_wasm` 为无界同步调用（`src/appmgr/runtime.c:78/86/100/122/143/153`）。
2. 健康探针与 APP 同线程（`runtime.c:139-161` 主循环内）：`app_init`/`app_tick` 死循环时 `health_probe` 永不执行——健康机制只覆盖"能返回但返回异常"。
3. `ts_wdt_register`/`ts_wdt_feed` 生产代码零调用（全库 grep 仅 `src/core/wdt.c:31/45` 定义 + `tests/core` 测试调用）——`TS_WDT_NET/APPMGR/SYWORK` 三源枚举定义后从未接线；无源注册时巡检空转（`wdt.c:55-57` 跳过未注册源）。
4. 注册窗口结构性冲突：`wdt_start` 在 boot 步骤 3（`src/core/boot.c:80`），APP 装载在其后（`boot.c:86`），而 `wdt_start` 后拒绝注册（`wdt.c:33` `started` 检查）——即使将来想注册 `TS_WDT_APPMGR` 也会被启动顺序阻断。
5. 全库无硬件看门狗使能（grep `CONFIG_WDT*` 全 prj.conf/board conf 零命中）：`system_fail` 停机后 `k_sleep(K_FOREVER)` 所依托的"硬 WDT 兜底复位"（`src/safety/force.c:56-59` 注释自述）不存在——真机 fail-safe 后**永久挂死不自恢复**。
6. 唯一强停机制 `ts_appmgr_app_stop`（`runtime.c:335-337`）生产无调用方（net 命令表无 app-stop 命令，`src/net/cmd.c:941-955`）。

**后果**：恶意/故障 APP 死循环 = APP 功能永久死亡且系统无感知；net_wq 卡死同样不可检；fail-safe 态无自愈路径。违反合同 4"每子系统独立喂狗（可定位卡死来源）"与合同 6 的可恢复性预期。
**涉及**：`wdt.c` / `boot.c` / `runtime.c` / `force.c` / 板级 prj.conf。

### IR2-02 · 固件侧 COSE 验签为结构桩——生产不可用 / TEST 无界放行（同根两面）

**现状**（主会话复核）：`src/appmgr/pkg.c:15-36` `verify_cose_minimal` 仅查 `cose[0]==0xd2 && cose[1]==0x84` 两字节；`#ifndef CONFIG_TS_TEST` 生产构建恒 `return TS_E_INVALID_SIG`（pkg.c:30-32，fail-closed 纪律注释自述"TODO M2b.2：ed25519 验签接入后移除"）。
同族缺口：
- activate 的"整槽 hash 校验"无对拍对象：`pkg.c:166-174` 算出 sha 后仅检查读操作成功，从不与任何期望摘要比较（TSAP 头无摘要字段，`include/ts/tsap.h:22-24`）；boot 装载（`src/appmgr/slot.c:109-241`）不验签不验 hash，直接装载 active slot 字节。
- 根公钥来源"prov 或测试注入"（pkg.c:3 注释）依赖生产 prov 烧录通道（板级十一候选，未开工）。

**后果**：生产镜像无法安装任何 APP（部署面零可用）；TEST/联调镜像可执行任意未签名 wasm 且 **caps 来自包内 manifest 自声明**（合同 10"APP 权限清单是硬边界"在当前所有真机验证配置下退化为自报制）。
**注**：真实现若需 TSAP 头加摘要字段 = **文件格式变更 = review 门 ③**，须 Q 呈递。

### IR2-03 · Agent PC 侧"读面"外泄链（威胁模型 = LLM prompt injection）

**现状**（三段证据）：
1. `compile_app_c` 无 include 隔离：`agent/tessera_agent/tools_tsap/wasm_build.py:40-43` CLANG_FLAGS 无 `-nostdinc` 类限制——C 源 `#include "/home/…/.ssh/id_rsa"`、`#include "/proc/self/environ"`（含 `ANTHROPIC_API_KEY`）不受 allowed_roots 约束（该白名单只管 out_dir）；clang 诊断会回显出错行源文本 → stderr 尾部 4000 字符完整进错误 detail（`wasm_build.py:130-133`）→ 回喂 LLM（`domain/app_chain.py:163-166`）并进任务日志（`firmware.py:282-283` docstring 自述）。
2. 读入路径全裸：`tools_tsap/tools.py:60/69/101/124`——`wasm_path`/`key_path`/`package_path`/`pub_key_path` 仅 `expanduser + is_file()`，全库唯一走 `_resolve_within` 白名单的只有 out_dir（`tools.py:25-33`）。`tsap_package`（confirm 类）可把主机任意 blob 读入、签进 TSAP 包落到 workspace 再外送；`key_path` 任意化破坏"签名密钥受控"假设。
3. `app_compile` 的 `max_bytes` 由调用方（LLM）提供（`firmware.py:277-279`），可反向放宽 agent 侧 16KB 尺寸门（`wasm_build.py:46-47` 注释自称"按调用方参数收紧"，实际调用方=被审查对象）。

**后果**：被注入的 LLM 无需逃逸沙箱即可把主机敏感文件内容送出（经 stderr 回喂上下文 / 经 TSAP 包落盘外送）。当前单用户开发环境实际暴露面有限，但该链路将随 Agent 走向"机器人/Galatea 自产"北极星（DEC-33）成为硬边界缺陷。
**缓解现状**：subprocess 全列表传参无 shell、产物不执行、out_dir 逃逸拦截——写出面纪律良好（§6）；缺的是读入面。

## 3. 中风险（8 项）

| # | 描述 | 证据 | 要点 |
|---|------|------|------|
| IR2-04 | L5 check_1（唯一写路径）正则不覆盖裸 `pwm_set(` | `firmware/tests/l5/check_l5.py:30-33` 正则只匹配 `pwm_set_(cycles\|duty\|pulse\|ticks)`；实际调用 `src/safety/driver_dispatch.c:149` 是裸 `pwm_set(` | PWM 的合同 2 机械防线缺口——任何文件新增裸 `pwm_set(` 不会被 L5 拦截，退化为 code review。当前代码本身无越权写（已验证），缺的是检查工具 |
| IR2-05 | estop ISR 与状态迁移的覆盖窗口 | `src/safety/channel.c:107-114`（set_link：检查态→写驱动间无 forced 复查）、`channel.c:164-171`（recover 同型）；对比 commit 路径已有 irq_lock+末段复查范式（`commit.c:130-140`） | estop 抢入后迁移路径继续写，可把 fault 值覆盖为 linkloss 值且 fault 语义静默丢失（`clear_fault` 只迁移 SAFE_FAULT 通道，`channel.c:192-197`）。窗口极窄但合同 5 是最高优先级。附带：estop ISR 链内调 `pwm_set` 的 ISR 安全性无断言保证（`driver_dispatch.c:149/210-216`）——板级移植雷 |
| IR2-06 | `app_stop` 强杀可死锁全部输出写路径 | `runtime.c:335-339`：`k_thread_abort` 后立即销毁 exec_env/instance；若线程恰持 `commit_lock`（`commit.c:15-21` `K_FOREVER`）被杀，Zephyr k_mutex 无 owner-death 回收 → 永久死锁 | 发生在"处理失控 APP"的补救路径上；WAMR 半执行态销毁属 UB。触发窗口窄、后果重 |
| IR2-07 | 回滚链不闭环 | `slot.c:72` 翻转 `active_slot ^= 1` 前不验证目标槽含有效 TSAP 包；回滚后无重载/复位（系统无复位触发源，IR2-01⑤ 同根）；`slot.c:27-30` meta 双副本皆损时静默 `active_slot=0` + `rollback_count` 归零返回 TS_OK——违背 store 层"两副本皆损→调用方 fail-safe"约定（`meta.c:127-128`） | 坏 APP 回滚后系统无限期无业务逻辑；持久层严重损坏被掩盖且回滚预算复位 |
| IR2-08 | 审计归因缺口：actor 恒 0 | `src/safety/commit.c:46` `.actor = 0, /* M1 恒 system */`；`cmd.c:541` 注释宣称"src 进审计 payload"未兑现 | APP 成功输出与 net 写命令均无法归因到 app_id/src——合同 10 留痕价值减半；DEC-40 的 src 信号已可用未透传 |
| IR2-09 | 任务取消不终止子进程组 | `common/tasks.py:106-124` 仅 cancel asyncio Task；`platform.py:224-226` docstring 声明"终止子进程组"不符；`wasm_build.py:124-126` `_run_clang` 无 `start_new_session`（对照 `common/proc.py:52-59` 既有纪律） | 取消 fw_build（west 30min 档）后子进程继续占 CPU/写 build 目录；clang 孙进程遗留 |
| IR2-10 | 并发同 out_dir 固定文件名交叉污染 | `wasm_build.py:155-164`：固定 `app.c`/`app.wasm` 名、无条件覆盖、无锁；失败路径遗留 `app.c`/`app.wasm.check` | 两个并行 app_compile/app_develop 指向同一 out_dir 时"双编译字节一致"检查可被 A 源×B 产物错配（误拒/误收） |
| IR2-11 | zenoh key 表达式注入 | `tools_net/keys.py:38-39` `f"tessera/{node}/{cube}/sys/{cmd}"` 无字符校验；`deploy.py:51-55` 直接拼 key | node/cube 含 `/`、`*`、`**` 可越出目标 cube 键空间；`deploy_status` 为 auto 类无审批面（对比 chunk_size 有校验 `deploy.py:127-129`） |

## 4. 低风险（择要登记）

- **linkmon 状态跨线程无锁**（`zenoh.c:161` 回调线程写 vs `init.c:33` net_wq 读；`linkmon.c:7` 注释的"无锁"假设与实际线程拓扑不符）——32 位平台 u64 撕裂/恢复判定抖动面，安全态本身有锁不受影响。
- **noinit 故障留痕弱桩未接**（`force.c:11-15` `__weak ts_store_noinit_record`，全库无强实现；noinit 机制本体已就绪 `store/noinit.c`）——复位后故障不可归因，IR2-01 若启用 WDT 后此缺口放大。
- **meta 序号回绕语义不安全 + CRC 不覆盖记录头**（`meta.c:96` 平凡比较 `s0>=s1`、`meta.c:15/41` 无 magic、CRC 仅 body）——2^32 次写才触发回绕（现实寿命不可达）故低；头部位翻可选旧副本。
- **输入面全桩**（`hal/api.c:78` gpio_read 恒 false、`hal/input.c:31`）——= G3 已登记缺口，此处确认"输入流不因保护中断"目前平凡成立。
- **estop 触发沿硬编码上升沿占位**（`driver_dispatch.c:225-230`，prov 接线 = M2a 遗留 TODO）——常闭开关场景极性反向风险，合同 5 单点。
- **mailbox 满时二次 put 返回值被忽略**（`runtime.c:357`）——并发生产者竞争时空位时新事件静默丢失且 `mb_dropped` 不计。
- **`ts_log_write` 无速率限制**（`natives.c:70-89`）——APP 可刷屏 printk 淹没观测面。
- **`mod_cache` 持调用方 wasm 缓冲指针**（`runtime.c:259-266/274` memcmp 复用）——隐含"缓冲进程级存活"契约，boot 静态缓冲满足，第三方调用方悬垂读隐患。
- **`ts_appmgr_app_evt` 无生产投递方**（全仓仅 tests 调用）——输入事件→APP 路由未接线（G3 同族）。
- **文档漂移**：`net.h:116-118` 称命令表容量 12（实际 `CMD_TABLE_MAX=16` 已注册 15）；`linkmon.c:42` `.t_ms=(uint32_t)now_ms` 64 位时钟低 32 位截断（~49 天回绕影响重放对拍口径）。
- **PC 侧小项**：审批 pending 无数量上限；TaskRegistry 终态任务仅 TTL 惰性清理（长跑内存缓增）；`app_chain.py:181` 重试分母误用 `OUTPUT_RETRIES`(3) 非 `CHAIN_RETRIES`(4)；`OUTPUT_MAX_TOKENS`(16384) 死常量；`with_suffix(".pub")` 对多点文件名推导错；clang 输出 locale 解码（Windows cp936 可抛未包装异常）；audit JSONL 无文件锁；RateLimiter 服务级单桶与"每客户端"注释不符；`deploy_discover` timeout 无边界校验；`FirmwareDeployer.router_locator` 死代码。
- **测试覆盖缺口**（与上关联）：`_run_clang` 超时分支、symlink 逃逸、`{"item":…}` 解包路径、编译失败→LLM 修复回路、CHAIN_RETRIES 耗尽断言、租约续期/释放失败路径、审批闸 E2E（现仅 tsap_keygen）等——详单见审查过程记录，随对应修复批补测试。

## 5. 处置建议（呈 owner；本次未动手）

按风险与依赖排序，供 owner 拍板排期（与既定 MD1.2d 呈递不冲突，可调整序）：

1. **看门狗接线批**（IR2-01，建议最优先）：合同 4 是硬约束且当前静默失效。内容 = 三子系统注册+喂狗接线、wdt_start 后注册窗口的启动顺序修复、真机硬件 WDT（task wdt）使能与 system_fail 复位闭环、APP 执行边界（WAMR 超时/fuel 或喂狗点设计）。含设计决策成分（启动序、APP 边界机制选型）——建议按门 ① 呈递方案再实施。
2. **Agent PC 读面加固批**（IR2-03/09/10/11，纯工程修复不需 Q）：读入路径纳入 roots 白名单、`-nostdinc`+显式 include 隔离、stderr 过滤后再回喂、`start_new_session`+killpg 对齐、out_dir 并发隔离（会话子目录或锁）、max_bytes 服务端钳制、node/cube 字符白名单。
3. **验签实装批**（IR2-02，含门 ③）：ed25519 真验签 + activate hash 对拍（TSAP 头摘要字段 = 文件格式变更须 Q）+ 生产 prov 烧录通道（板级十一候选天然同批）。
4. **小项打包批**：IR2-04（L5 正则一行）+ IR2-05（set_link/recover 补 irq_lock 复查范式平移）+ IR2-08（actor 透传）——可并入上述任一批。
5. **低项**：进观察项/待办清单随批清偿，不单开交付单元。

## 6. 已验证无风险面（正面清单）

- **meta P1 修复到位**（MD1.1b）：`meta.c:119-125` data0/data1 分缓冲，双副本皆损返回 `TS_E_IO` 交调用方 fail-safe。
- **写入路径唯一性成立**：`gpio_pin_set_dt`/裸 `pwm_set` 全库唯一于 `driver_dispatch.c:87/149`（boardbench 为 L5 显式白名单）；`ts_drivers[].write` 调用点全部在 safety 层；api/power 写全部收敛 `ts_safety_commit[_locked]`。（IR2-04 只是检查工具缺口）
- **PWM 落驱动校验链完整**：perm → 打包域 [100Hz, 6.5535MHz]/permille≤1000（`api.c:89-91`）→ ACTIVE/forced 检查 → 限幅 clamp → slew 拆分（`commit.c:106-119`）→ irq_lock 末段复查 forced（`commit.c:130-140`）→ 驱动层域兜底 + pwm_err 计数（`driver_dispatch.c:142-152`）。
- **断链 fail-safe 物理落值**（板级九修复在位）：`channel.c:107-114` linkloss 声明值直写驱动 + slew 基线重置；恢复不自动回写（DR-04）；判活单源 linkmon（hb-host publish，恢复滞回 2 次）。
- **DEC-40/41/42 全部已实现且 fail-closed**：信封 v2（`cmd.c:619-716` ver/kind/rid/src 必备、未知键拒绝、to>5000ms 拒绝）+ 幂等回放 LRU（`cmd.c:882-899` 跨 key/op 防御）+ 租约（`lease.c` 单租约/TTL 10s/lease_id 单调/写类门控 `cmd.c:900-911`/不联动安全态）+ 遥测信封（`pub.c` ver/kind + QoS 映射）。
- **权限运行时执行无绕过**：六 native 全经 user_data 注入 ctx（wasm 侧无法伪造身份，`natives.c:24-27`）+ `ts_perm_check` 位图裁决（未绑定 ctx 即拒绝 `perm.c:141`）；越权返回 TS_E_PERM + TS_EVT_PERM_DENIED 留痕 + QoS=SAFETY 外发。
- **半写 slot 无执行窗口**：先整槽抹除（`pkg.c:59-64`）+ verify 收满（`:105-106`）+ active_slot 仅经掉电安全 meta 双副本切换（擦→写→回读 memcmp）。
- **estop 直达路径纯净**：`force.c:18-33` 仅原子置位+逐通道直写，无队列/锁/分配/协议栈；L5 check_5 机械禁用符号。
- **PC 侧写出面纪律**：subprocess 全列表传参无 shell/eval；out_dir `..`/绝对/symlink 逃逸拦截（有测试）；strict/confirm 审批闸真实生效（超时自动 deny）；CHAIN_RETRIES 有界；config 不打印密钥；私钥 0600 不进日志/返回值；push 强制先验签后上传（双实现验签）；产物不执行。
- **密钥纪律复核（本审查）**：WiFi 凭证串与 API 密钥 JWT 前缀两项 `git grep` 模式在全库均 0 命中（模式串本身不入本文档，防验证信号污染）、`agent/config.toml` gitignore 生效（`.gitignore:33`）。
- **预算 TOCTOU 闭合**：`power/slots.c:86-113` 全程 write_lock + commit_locked，记账单源 safety readback；power 通道 linkloss/fault 恒关断不可放宽。

## 7. 未裁决项与实现债盘点（2026-10-06 现状）

**待裁 Q：无。** decisions.md 全文核验：Q-01…Q-26 已全部裁毕（最近 = Q-26 → DEC-46，2026-10-05）；Q-27 尚未提交（见下）。

**即将呈递的门项（未提交，不算待裁）**：
- **MD1.2d 设计**（下一单元既定）：zenoh 视频帧分片传输（帧 ~38KB vs 遥测 payload 128B）+ ts-fs/ts-av natives API 面 + ts_perm_v1 权限类扩展——权限模型变更 = 门 ③，将以 Q-27 呈递停门。
- **MD1.2c**：PDM 音频驱动扩展评估（i2s_esp32 无 PDM；hal_espressif i2s_pdm 组件可接）——评估后视方案定是否走门。
- **P4 适配**：硬前置 = Zephyr 升级 4.5+（技术栈变更 = 门 ⑤）；H7 已放弃（DEC 登记在案）。

**已裁未完成（实现债，非待裁）**：固件 ed25519 验签（IR2-02，M2b.2 TODO）；看门狗接线（IR2-01，合同 4 债）；estop 触发沿 prov 接线（M2a 遗留）；input monitor→APP mailbox 路由（G3）；单活跃 APP 语义（G4）；模拟深度（G5）；审计 actor 归因（IR2-08）。

**存量观察项**（登记在案未动）：外部静态 video_buffer DMA 报错根因未钉死（V1 已锁池路径）；deploybench watch 同槽重推不触发复位（五连部署序不受影响）；CI native-build 偶发面（诊断转储就位待复发）；ESP32-S3 SMP 上游（DEC-19 跟进机制内关注）。

## 8. 附记（2026-10-07 复检 · owner 指令"检查错误或忽略"）

新鲜回归全绿（CI 四 job @ce98bac；L5 6/6；agent pytest 74+2s；repo pytest 2；ruff；密钥双 grep 零）。本地 twister 14/15 的唯一 errored = framework.wamr 构建竞态（deps/wamr version.cmake 并行互踩——板级四已登记；单套件复跑 1/1 绿 + CI 同提交绿双证据排除代码回归）。新登记（低危，登记不动手——军规 9）：

- **ts_fs_write off 越过 EOF 间隙语义**：FAT 上越过 EOF 写入时间隙为未初始化旧簇数据（无句柄面无预填）——真实消费需连续写时由 APP 顺序写（off=累计长度）规避；如需语义收紧（E_RANGE 或零填）随真实需求再裁。
- **ts_fs_list 截断尾分隔符**：容量截断落在条目名中间的边界上可遗留尾 ';'（消费端解析按空段忽略即可）。
- **fs_paths 绑定无 stop 解绑**：app_stop 后 bound_app 保持——V1 单活跃 APP 且 natives 随实例销毁不可达，无越权面；多活跃 APP 语义（G4）落地时必须重设计绑定形态。
- **fs_paths 条目长度边缘**：agent 校验器允许 64 字符条目 vs 固件走查缓冲 pfx[64] 实收 ≤63——超长条目打包通过但 boot 拒载（fail-closed 方向安全；表现 = APP 静默不装载难排查）→ 修复落点 = 排期表单元 A（MD1.2g）对齐。

处置排期修订见 project-plan v1.30（IR2-07→单元 D；IR2-06→单元 F）。


---

## 原 `docs/impl-review-03.md`（2026-10-10）

# impl-review-03 · 板级移植 + 4.5 适配会话改动审查（2026-10-10）

> **性质**：owner 指令 review（「请 review 我们的改动，后续我们讨论下一步计划」）。
> **范围**：本会话 8 个提交（`24ecdc6..d9c4cca`，51 文件，+1456/−63）+ 两份 upstream issue（#121767/#121774）。
> **方法**：逐批对照验证证据（构建/真机判据/回归/CI）自查；风险与未验证项如实列出（本报告自查发现不构成已修复声明）。

## 1. 逐批审查

| # | 提交 | 批次 | 验证证据 | 自查结论 |
|---|------|------|----------|----------|
| 1 | `24ecdc6` | P4 适配批（p4bench 真机全链 PASS + 六 bench 兼容串 + persistbench v2 包） | 真机 PB/P4B 判据单迹 + twister 15/15（77）+ CI 绿 | ✅ 真机证据充分；存量缺陷修复（兼容串/v1 包）同批验证 |
| 2 | `b1f7bd5` | H7 构建级（h7bench + WAMR THUMBV7EM 映射） | 构建绿 + 回归绿 + CI 绿；**真机未做**（无 ST-LINK，DEC-51 已搁置） | ✅ 构建级达成自报口径（报告即标注 v0.1 待板） |
| 3 | `56fa073` | P4 PSRAM（p4psram 真机 PASS） | 真机 P4P 判据单迹 + 回归 + CI | ✅ |
| 4 | `77ff016` | P4 无线面（netbench P4 + 包含域提级 + 无 WAMR 桩） | 真机半程证据（RPC 通/数据面挂——定案上游）+ 回归 + CI | ✅ 自报缺陷诚实；桩经 twister 全量链接验证 |
| 5 | `b7a9c6b` | S3 复验批（persistbench @4.5 PASS + 栈 8192 批量防御 ×15） | 真机 PB PASS 单迹 + twister 15/15 + CI | ✅ 修复有实证；**批量防御部分仅 persistbench 有真机证据**（见风险 R2） |
| 6 | `695a396` | issue #121767 登记入库 | issue URL 可查 | ✅ |
| 7 | `4646d06` | D-AV @4.5 复测（avdemo 首构建 + 池 94208） | 真机复测单迹（stream started/零帧定论）+ CI | ✅ |
| 8 | `d9c4cca` | D-AV 采集执行 + 4.5 发送损坏定案（256B 绕行档） | 多轮真机采集 + PC 自环对照 + CI | ✅ 证据链完整；**256B 档未验证**（见风险 R3） |

**公共质量面**：每提交均过 pytest（编码/无 BOM）+ SOURCES.lock 同步 + 密钥零命中检查；twister native_sim 15/15（77 用例）在本会话跑过 6 轮全绿（WAMR 竞态一次复发当轮即识别修复——444 屏障恢复）。

## 2. 风险清单（自查，按优先级）

- **R1（中）S3 真机回归覆盖不全**：@4.5 下真机复验过的仅 persistbench 与 inputdemo（升级批）；**deploybench / otabench / netbench / avdemo / linkdemo 等未在 4.5 真机复跑**。其中 deploybench/otabench 内存面经两轮调整（池 151552 + 栈 8192），4.4 时代的真机结论不再直接适用。→ 建议批 A（见 §4）。
- **R2（低）栈 8192 批量防御为同型推断**：仅 persistbench 的挂死有实证；其余 14 个 bench 是同型防御（教训 31⑤/32 同源推理）。风险低（栈加大无副作用）但如实声明：非逐板实证。
- **R3（低）256B 绕行档残留**：avdemo conf 的 `TS_NET_PUBLISH_MAX_BYTES=256` 是未验证的实验档——若上游修复后忘回收，会静默降带宽。已在本报告与 conf 注释双登记；上游修复复测时回收。
- **R4（低）仓外资产依赖**：C6 固件链（D:/Software/project/esp_hosted 工作副本 + bat 脚本）、dav_recv/采集脚本均在 owner 机器 logs/deps——已文档化（教训 32），但无仓库备份。P4/H7 已搁置（DEC-51）故影响面有限。
- **R5（观察）WAMR version.h 只读屏障**：曾因某批操作被解除（644）引发并发竞争。当前已 444；**建议**：若再需重生成，操作后在同一命令内恢复 444（教训 21⑤ 纪律追加项）。
- **R6（信息）D-AV 双上游阻塞**：#121774（video 驱动首帧后停摆——当前主导）+ 4.5 zenoh-pico 1KB 发送损坏（未单独立 issue，已在 #121767 关联语境登记 decisions；如 owner 需可第三案起草）。

## 3. 与规划/合同的符合性

- 阶段白名单：全部产出在 impl 面（代码/测试/文档/登记），无越权。
- 军规 7（测试同批）/10（交付即验证）：每批 DoD 对照自报（含自报缺陷：P4 无线半程、H7 无真机、256B 未验证——无美化）。
- 合同 1-10：板级移植不触安全合同面（无 safety 代码变更）；唯一框架语义变更 = slot.c 无 WAMR 桩（TS_APPMGR 面，运行语义退化如注释所述，twister 覆盖）。
- 板卡集变更（DEC-51）经 owner 裁决登记。

## 4. 下一步计划候选（供讨论）

- **批 A（建议优先）：S3 全 bench @4.5 真机回归收口**——R1 的直接处置：deploybench（部署链+D8）/ otabench（SMP OTA）/ netbench（时延+断链）/ linkdemo / avdemo 逐个 4.5 真机复跑，恢复"S3-only 主力板"的完整真机基线。预计 2-3 个会话单元。
- **批 B：上游跟踪**——#121767/#121774 回复跟进；4.5.0 正式发布后平移 rc1 + 全量回归（可与批 A 合并做）。
- **批 C：产品化推进**——规划外新方向（如 agent 链完善 / 更多 demo APP / 硬件阶段二）——**需 owner 定方向与优先级**（呈递格式走门①/⑤）。
- **批 D：小收尾**——R3 绕行档回收（依赖上游）、R5 屏障纪律追加登记、dev-env 教训 33（直连/代理双模网络下 gh/curl 的环境变量纪律——本次已踩：代理关闭后显式 export 代理变量的调用全部失败）。

## 5. 结论

8 批改动全部有对应验证证据且缺陷如实自报；主要开放面集中在**上游依赖**（两 issue + 4.5 正式版）与 **R1 真机回归覆盖**。建议下一步从批 A 开始（S3 基线收口），批 B 时机成熟合并执行；批 C 方向请 owner 裁决。


---

## 原 `design/final-selfcheck-v0.8.0.md`（2026-10-15）

# 最终自检报告（V0.8.0 全量计划完成自检）· 2026-10-15

> **触发**：owner 指令（2026-10-15）「……完成我们原定的所有开发计划，并在完成后进行一次自检，检查文档是否完整，代码是否规范以及符合要求，测试十分充分。」
> **范围**：§11e 通用域解放三版本批收口后全库（重点 = V0.8.0 生态批 EC1-5 变更面 + 全库横向一致性）。
> **方法**：① 文档完整性（版本一致性机械扫描 / 登记册回填 / 术语与 README 时效）；② 代码规范（ruff / 军规 4 编码检查 / L5 机械检查 / SPDX 与出处纪律 / 残留扫描）；③ 测试充分性（全量回归定格 + 覆盖面清点 + 缺口如实登记）。
> **结论**：**15 项发现（SC-05…SC-19），全部当场处置；三项测试缺口如实登记（均有批次归属）；全量回归绿。**

## 一、发现与处置（SC 编号族延续 final-selfcheck.md 2026-09-21 批）

### A. 文档完整性（11 项）

| # | 严重度 | 发现 | 处置 |
|---|---|---|---|
| SC-05 | 高 | LLD-ts-net 修订记录缺 v0.4.1 行（EC2 批 python `.replace()` 模式含空行差异静默 no-op——状态行已更而修订行未落） | ✅ 补行；教训：文档批量编辑后须复扫断言（本报告扫描器即产物） |
| SC-06 | 中 | LLD-ts-appmgr 状态行 v0.7.1 ≠ 最新修订 v0.7.2（EC4 加修订未同步状态） | ✅ 同步 |
| SC-07 | 低 | 六份 LLD 标题行版本滞后于修订记录（appmgr/net/store/safety/A01/A02——标题行长期不随修订更新的历史惯例） | ✅ 全部归一至最新修订号 |
| SC-08 | 中 | LLD-ts-periph 版本序错误：v0.5（10-02）之后出现 v0.4.1（10-14 CG7）——CG7 应为 v0.5.1 | ✅ 更正为 v0.5.1 + 勘误注记 |
| SC-09 | 中 | LLD-ts-hal 状态行仍写「v0.1 草案，待 owner review」——实现已在库且修订至 v0.2.3 | ✅ 更正为现行态 |
| SC-10 | 低 | HLD-firmware-framework 状态行 v0.2 滞后（修订已至 v0.2.2；另其修订记录为旧→新序，与多数文件相反——保持原序不改格式） | ✅ 状态行更正 |
| SC-11 | 中 | README 滞后：用例计数（15 套件 77+/pytest 100+→实为 16/107/183） | ✅ 更正 |
| SC-12 | 中 | README 快速上手仍标 WSL2 环境（迁移批后主力 = 原生 x86 Linux） | ✅ 更正 + migration-x86 指引 |
| SC-13 | 低 | README 回归命令缺 TS_WAMR_DIR 注记（twister 实际需要） | ✅ 补注 |
| SC-14 | 中 | README demo 表滞后：D-AV 仍标 ◐（V0.2.0 已 DA PASS）；DP/DT/MA/NVD/AG7/CG7 七项缺失 | ✅ 更正补齐 |
| SC-15 | 中 | names.md 登记册大幅滞后：DEC/Q 索引止于 2026-09-22（DEC-39…60 / Q-20…43 全部未入册——跨多批历史漂移） | ✅ 区间行回填索引 + V0.8.0 批标识符全量登记（军规 6） |

**机械复核**：版本一致性扫描器（标题/状态/修订记录三方比对，排序无关算法）终态 = **design/ 25 份文档全部一致**。

### B. 代码规范（2 项发现，均合规）

| # | 项 | 结果 |
|---|---|---|
| SC-16 | 残留扫描 | ✅ 本批 51 变更文件无 TODO/FIXME/HACK；print() 命中均为合法工具输出（夹具生成器 CLI / L5 脚本本体） |
| SC-17 | 规范电池 | ✅ ruff 全绿（含 asyncio 阻塞检查）/ 军规 4 编码检查（repo pytest 2/2）/ L5 **7/7**（含新增 slot 收口检查）/ twister 16/16 全编译零警告（-Werror 基线）/ 新文件 SPDX 头齐 / 可调常量出处标注齐（L5 检查 4 把关） |

### C. 测试充分性（2 项登记）

| # | 项 | 状态 |
|---|---|---|
| SC-18 | 间歇失败观察 | **登记**：自检期一次 agent pytest 出现 1 failed（输出截断未捕获用例名），随后 **5 连跑全绿**（183+2s）。按 testing.md §5 flaky 纪律登记观察——复发时按隔离清单处置 |
| SC-19 | 覆盖缺口（既有，如实） | ① 覆盖率工具（gcov 门槛，testing.md §4）自「待套件生效裁决」以来未启用——历史遗留，非本批引入；② L5 工具自身无单测（检查 7 捕获力经负样本 ad-hoc 自证：注入越界 → FAILED → 还原绿）；③ 真机面三缺口已在 decisions.md 按批归属登记（信任链 E2E / net+SD 资源推送 E2E 随板级批；本地确认路随设备形态批） |

## 二、测试充分性清点（V0.8.0 批新增面）

| 层 | 新增用例 | 覆盖 |
|---|---|---|
| firmware.store | test_trust_table（RAM+flash 双变体） | schema 矩阵（ver=0 哨兵/9 键/重复/键序/尾余量）/roundtrip/乒乓切换/撕裂回退/双损哨兵 |
| firmware.app | test_13_trust_chain（11 断言组） | 未注册拒基线/租约门/陌生键拒/跳版拒/首次注册/**多根安装实证**/重放拒/互荐/全撤回复拒/工厂根全程可用 |
| firmware.net | 构建面裁剪断言 ×2 | 无 TS_STORE_TRUST 构建 = trust-* NOTFOUND（Agent 探测面） |
| agent | ×4（trust 全链 + 参数矩阵 + summary + brief） | TUF 全链（注册→互荐→陌生拒→全撤）/键参数矩阵/manifest_summary 全字段与坏包/brief 双形态 |
| L5 | 检查 7（+ 负样本自证） | slot 写路径收口机械保证（侧载纪律） |
| 回归定格 | twister 16/16（**107** 用例，本批 +3）/ agent **183+2s**（+4）/ L5 **7/7** / repo 2 / ruff / sync | 全绿（显式退出码） |

## 三、结论

原定开发计划（§11e 三版本批 25/25 单元）已全部完成并收口（V0.6.0/V0.7.0/V0.8.0 三 tag）；自检 15 项发现全部当场处置，三项测试缺口如实登记（各有批次归属，无悬空项）。库处于可交付 owner review 状态。

