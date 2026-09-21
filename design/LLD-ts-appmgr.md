# LLD · ts-appmgr v0.1 草案

> **状态**：v0.1 草案，随 LLD 批次待 owner review。上位：HLD §3.4；公共约定 `LLD-00-common.md`。
> **职责**：APP 包接收/验签/双 slot 存储/版本与回滚；WAMR 宿主（实例化 + 按能力装配导入面）；APP 线程与健康探针。
> **合同关联**：合同 10（权限硬边界 = 符号过滤装配）；DEC-04/05/17。
> **外部依赖**：WAMR（wasm_runtime_* 家族，具体签名以钉住版本为准，M0 核验）。

## 1. 内部结构

```text
src/appmgr/
  pkg.c        包解析与验签（DEC-21 格式）
  slot.c       双 slot + meta 区（掉电安全）
  host.c       WAMR 宿主：实例化/符号装配/线程
  health.c     健康探针与回滚决策
```

## 2. 包格式 TAPP v1（DEC-21 裁定）

```text
"TSAP" magic u32 | fmt_ver u16(=1) | manifest_len u32 | wasm_len u32
| manifest(CBOR) | wasm 模块 | COSE_Sign1(ed25519, 覆盖 manifest‖wasm)
manifest: { app_id(反域名串), app_ver(semver 串), min_fw_ver, capabilities[ts_perm_v1],
            mem:{stack_u16_kb, heap_u16_kb}, exports:{health_ping 必有, init/tick/evt 可选} }
```

- 验签：根公钥在安全参数分区（烧录期写入，运行时只读，合同 10）；失败 → TS_E_INVALID_SIG + 留痕，不入 slot。

## 3. slot 与 meta（slot.c，〔DEC-23〕；分区读写经 ts-store，DR-01）

```text
分区：app_slot_a | app_slot_b | meta(2 份冗余写, 序号防撕裂)
meta: { active_slot, app_id, app_ver, rollback_count, boot_gen }
```

- 升级写序（掉电安全）：写 inactive slot → 校验回读 → meta 新序号原子切换 → 下一加载周期生效。
- 回滚：健康失败 → active 切回上一 slot、rollback_count++；计数 >〔DEC-27： 3〕→ 该版本 QUARANTINED（拒载 + `TS_EVT_APP_QUARANTINED`），不循环。

## 4. APP 生命周期状态机（health.c + host.c）

```text
 RECEIVED →(验签)→ VERIFIED →(写slot/meta)→ STAGED
 STAGED →(加载周期)→ ACTIVE ⇄(健康失败)→ ROLLBACK → ACTIVE(旧版)
 任一态 →(rollback_count 超限)→ QUARANTINED（终态，需人工/显式命令解除）
```

- 加载发生在 boot 步骤 8；APP 级故障**不阻塞系统启动**（HLD §4.4-8）。
- 健康探针：周期〔DEC-27： 1000ms〕调用 wasm 导出 `app_health_ping`；连续超时〔DEC-27： 3〕次 → 触发回滚。

## 5. WAMR 宿主（host.c）

- 实例化参数：fast 解释器、WASI 关〔DEC-25〕；堆 = manifest.mem.heap（上限**每板动态配置**〔DEC-27，默认值见 HLD §4.6 每板表〕）、栈独立线程栈。
- **导入面装配（权限硬边界的落点）**：`ts_native_syms[]` 全集（= ts_api_v1 符号，LLD-ts-hal §3）逐项标注所需能力；实例化时**只注册** manifest 能力覆盖的子集——未授权符号在 wasm 模块内即不存在（链接期即拒，而非调用期判）。
- APP 线程：每 APP **恰好一个**框架创建的 Zephyr 线程（优先级/栈见 LLD-00 §4 与 manifest.mem.stack，上限〔DEC-27： 8KB〕）；同时加载上限〔DEC-27： 4〕个 APP。
- **APP 不可自建线程**〔Q-13 提案 A〕：WAMR 的 wasm pthread/共享内存特性**编译期不启用**，且 ts_api_v1 不提供任何线程创建导入——限制方式 = **能力不存在**（与符号装配硬边界同哲学），而非运行时配额。
  - APP 内并发 = 事件模型（app_evt/tick 串行回调）+ 语言内协作式并发（协程/async/状态机）；线程级真并行由 **APP 之间**提供（多核板 Zephyr SMP，S3/P4 双核）。
  - 长计算纪律：单次 tick/evt 回调工作量应有界（健康探针〔DEC-27 #8〕为最终防线）；重计算走 AOT（DEC-25）或下沉框架层原生实现。
  - 预留扩展：manifest schema v2 可增 `threads:{max,stack}` 能力字段（权限门控 + 计数 + 栈预算）后才启用 WAMR 线程特性——**V1 不实现**。
- 调用约定：框架按序调 `app_init` →（tick 若导出）周期〔DEC-27： 100ms〕驱动 → 事件到达时调 `app_evt`；wasm 陷出到 ts_* 导入即在本线程上下文执行（权限裁决无跨线程跳转）。
- **事件串行化（DR-14）**：tick 与 app_evt 均在 APP 线程内执行；外部事件入每 APP mailbox（深度〔DEC-27 #15： 8〕，满则丢最旧 + 计数），线程主循环顺序消费——单线程内无重入。
- **卸载/升级停止语义（DR-14）**：停止投递 → 排空 mailbox → join（超时〔DEC-27 #15： 2s〕强杀并回收）；强杀不影响框架喂狗（TS_WDT_APPMGR 独立喂狗源）。APP 业务状态 V1 不持久化（HLD §1 裁剪，DR-15）。

## 6. 测试要点

- L1：包解析/验签（坏签名/截断/字段缺失矩阵）；slot 切换掉电注入（meta 撕裂恢复）。
- L2：生命周期全迁移；健康探针超时→回滚→超限隔离。
- L4：安装→运行→升级→回滚全链重放（含 ts_evt 事件序）。
- L5：导入面装配过滤的静态断言（符号注册点唯一 = host.c）。

## 7. 未决依赖

- DEC-21（TSAP）、DEC-25（执行模式/WASI）、DEC-23（分区）、DEC-27（探针/回滚/APP 数等默认值与每板堆配置）已裁；待 **Q-13**（APP 线程模型，已按建议 A 预写）。

## 修订记录

- v0.1 · 2026-09-20：首版草案（"按能力过滤符号装配"为权限硬边界核心机制）。
- v0.2 · 2026-09-20：review-01——slot 经 ts-store（DR-01）、mailbox 串行化与卸载停止语义（DR-14）、APP 状态不持久化声明（DR-15）。
- v0.2.1 · 2026-09-21：裁决同步——DEC-27 每板堆配置；出处标注收敛（SC-02）。
- v0.2.2 · 2026-09-21：owner 问询线程模型——§5 增 APP 线程限制（禁自建线程/编译期禁用/三层限制机制），登记 Q-13。
