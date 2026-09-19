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
