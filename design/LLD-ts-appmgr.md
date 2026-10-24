# LLD · ts-appmgr v0.9.2（M2b.2 完成）

> **状态**：v0.9.2（2026-10-18 R5-V：**激活信息面带包身份**——stage_commit 增 staged manifest app_id/app_ver 提取（安装期 verify 已全 schema 走查，此处仅身份提取 + 未知键 skip 不复核；ts_app_info_t 与 [tsi] verdict 行随之带全身份——真机判据行保真，证据 r5v_verdicts_console.txt §5）；v0.9.1（2026-10-16 P1-3：**供电槽 native 面**——ts_power_set/get（power:set:slot 权限 + 预算联动 + readback——ts-power 层全链的 wasm 暴露；Agent 白名单/约定镜像））；v0.9（2026-10-16 P1-1 · **APP 间消息路由**——§5d：ts_appmgr_msg_send/recv （HLD §3.4——框架路由唯一互访通道；msg:send 名单授权；FIFO 满槽背压；TS_APP_EVT_MSG 取件通知；natives ts_msg_send/recv）；v0.8（2026-10-16 F3 · DEC-62①③ **安装闸本地确认**——§5c：prov v2 lconf/activate 过闸/confirm-reject 本地路 API/60s fail-closed/事件四态/-13 回执/install 同闸；timeout 路真机 af3_gate_console）；v0.7.2（2026-10-15 EC4 · 侧载纪律定稿 + L5 检查 7 引用）；v0.7.1（2026-10-15 EC2 · **多根验签与 trust-update 实现**——verify_slot NULL=有效集迭代〔显式键语义不变：TEST 固定测试根覆盖维持〕+ ts_appmgr_trust_effective + cose_ram_parse/check〔COSE_Sign1 RAM 解析〕+ ts_appmgr_trust_update 编排〔schema→严格 N+1→现有效集签名→乒乓持久化+事件〕；ts_appmgr_install NULL 根键放开；生产回滚 NULL 恒拒缺陷根治）；v0.7（2026-10-15 EC1 · Q-43/DEC-60：**验签链多根设计**——有效集 = 工厂根〔prov pk0+pk1，pk1 转正消费〕∪ 信任表.keys；verify_slot NULL = 有效集迭代〔含生产回滚 NULL 恒拒存量缺陷根治〕；trust-update 命令链编排 + 侧载纪律）；v0.6.3（2026-10-14 CG5-B：**资源白名单 registry**——needs.resources → res_csv〔scan 单一解析源〕→ activate 绑定 + boot 恢复；sys/fs-* 授权源）；v0.6.2（2026-10-14 CG5-A · Q-39④：**get-info caps 块实现**——{tiers, max_linear_memory_kb, slot_pool_kb} 设备自报 + Agent push_app 装前预检〔caps 缺失 = 旧固件跳过〕；CG5-B 资源推送随下单元）。上位：HLD §3.4 + HLD-contract-v2 §5；公共约定 `LLD-ts-common.md`。上位：HLD §3.4 + HLD-contract-v2 §5；公共约定 `LLD-ts-common.md`。
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
            mem:{stack_u16_kb, heap_u16_kb}, exports:{health_ping 必有, app_init/app_tick/app_evt 可选（§4 调用约定名——板级十对齐：早前 init/tick/evt 为笔误漂移，runtime.c lookup 即 app_*）} }
可选键（DEC-47，MD1.2e/g）：fs_paths[绝对路径前缀]（fs 类路径白名单；有 fs: 能力时授权域）、
            av_fmt("jpeg"|"rgb565")/av_w/av_h（与 caps 含 av: 互为充要——加载期 ts_av_config_bind 绑定）
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
- APP 线程：每 APP **恰好一个**框架创建的 Zephyr 线程（优先级/栈见 LLD-ts-common §4 与 manifest.mem.stack，上限〔DEC-27： 8KB〕）；同时加载上限〔DEC-27： 4〕个 APP。
- **APP 不可自建线程**〔DEC-31〕：WAMR 的 wasm pthread/共享内存特性**编译期不启用**，且 ts_api_v1 不提供任何线程创建导入——限制方式 = **能力不存在**（与符号装配硬边界同哲学），而非运行时配额。
  - APP 内并发 = 事件模型（app_evt/tick 串行回调）+ 语言内协作式并发（协程/async/状态机）；线程级真并行由 **APP 之间**提供（多核板 Zephyr SMP，S3/P4 双核）。
  - 长计算纪律：单次 tick/evt 回调工作量应有界（健康探针〔DEC-27 #8〕为最终防线）；重计算走 AOT（DEC-25）或下沉框架层原生实现。
  - 预留扩展：manifest schema v2 可增 `threads:{max,stack}` 能力字段（权限门控 + 计数 + 栈预算）后才启用 WAMR 线程特性——**V1 不实现**。
- 调用约定：框架按序调 `app_init` →（tick 若导出）周期〔DEC-27： 100ms〕驱动 → 事件到达时调 `app_evt`；wasm 陷出到 ts_* 导入即在本线程上下文执行（权限裁决无跨线程跳转）。
- **事件串行化（DR-14）**：tick 与 app_evt 均在 APP 线程内执行；外部事件入每 APP mailbox（深度〔DEC-27 #15： 8〕，满则丢最旧 + 计数），线程主循环顺序消费——单线程内无重入。
- **卸载/升级停止语义（DR-14）**：停止投递 → 排空 mailbox → join（超时〔DEC-27 #15： 2s〕强杀并回收）；强杀不影响框架喂狗（TS_WDT_APPMGR 独立喂狗源）。APP 业务状态 V1 不持久化（HLD §1 裁剪，DR-15）。

## 5a. 资源档位与安装期匹配（CG1 · Q-39②④⑤——实现随 CG4，消费 AG7 实测数值）

- **manifest v2 增字段（Q-42 呈递——门③）**：`tier: "small" | "large"`（缺省 small——v1 包向后兼容）+ large 附 `needs: {linear_memory_kb, stack_kb, resources[]}`（linear_memory/stack 在编译期经 `-Wl,--initial-memory/--max-memory/-z stack-size` 链接钉死——三方一致纪律平移，Agent 侧 compile_project_c 消费）。
- **尺寸门分档（Q-39⑤：门不撤只分档）**：`TS_APP_SIZE_GATE_SMALL`（=16384 维持）与 `TS_APP_SIZE_GATE_LARGE`（建议 262144 = 256KB——AG7 数值：资源型 wasm = 资源 + 147B 线性 8-512KB 全谱；终值 CG4 呈 Q-42 裁）——装载校验按包 tier 取门。
- **安装期匹配矩阵（验签后、槽写入前新增步骤）**：tier 设备支持否 / linear_memory 预算 ≤ 设备档位上限否 / 资源清单 fs_paths 前缀可满足否——任一不满足 = 拒装（TS_E_RANGE + detail 指明缺口，回执结构化）——**安装期拒装替代运行期 OOM**（Android getMemoryClass 同型）。
- **装载缓冲与槽池**：`TS_APP_LOAD_MAX` 板级配置联动（large 档板 = 门值 ≥ gate_large）；槽池维持统一大槽 + 档位逻辑上限（不碎片化存储——LLD-ts-store §4 注）。
- **资源白名单 registry（CG5-B 已实现）**：ts_appmgr_res_bind/res_allows（per-entry 存储；scan_needs 增 res_csv 累积——安装期/boot/activate 三点同源解析）；无 needs 包 = 该 entry 白名单清空全拒（覆盖式）。消费 = sys/fs-* 命令面（LLD-ts-net §4）。已知限制：绑定随激活包覆盖，APP 停止不清白名单（部署通道租约门控下的可接受面——LLD-ts-safety §9a 同型登记）。
- **设备能力自报（CG5-A 已实现）**：`sys/get-info` 增 caps 块 `{tiers, max_linear_memory_kb, slot_pool_kb}`（异构设备生态基础）——tiers 派生（large ⇔ LOAD_MAX ≥ GATE_LARGE，与安装期矩阵同源）；max_linear = WAMR_HEAP/1024；slot_pool = SLOT_SIZE×COUNT/1024；非 WAMR 桩构建维持 v1 五键形态（无 APP 能力面）。消费 = Agent push_app 装前预检（tier/linear 双检，装前拒免整包上传；caps 缺失 = 旧固件 → 跳过〔新固件安装期矩阵兜底〕）。用例 framework.app test_11 + agent test_push_app_device_caps_precheck。peripherals 块（hal 注册表自报）随生态批。
- **实现注记（CG4）**：① 扫描单一解析源 = `ts_appmgr_scan_needs`（pkg.c——键分发 + `ts_cbor_skip`〔cbor_min 新增通用值跳过，深度 ≤4〕跳过非档位键；schema 纪律：tier ∈ {small,large}、needs 仅 large、resources 条目 fs_paths 同文法）——安装期 verify 与 boot 走查共用（walk 对 tier/needs 键跳过、walk 后调 scan 取档位门）。② 匹配矩阵 = `ts_appmgr_needs_match`（行序：线性内存 ≤ WAMR_HEAP 帽 → resources 须 TS_HAL_FS → tier=large 须 LOAD_MAX ≥ GATE_LARGE〔设备能力派生，无独立开关〕）；落点 = stage_verify 验签后（分步安装语义：包已入非激活槽、拒 = 不激活）。③ 尺寸门双门：Kconfig `TS_APP_SIZE_GATE_SMALL=16384`/`LARGE=262144`；boot 装载按包 tier 取门（装载缓冲上限门维持在前）；Agent 侧 `SIZE_GATE_LARGE` 同值镜像（调用方大值不可越档——IR2-03 钳制平移，缺省 max_bytes = 档位门）。④ 槽池装配断言：`BUILD_ASSERT(LOAD_MAX ≤ SLOT_SIZE)`（统一大槽 + 档位逻辑上限——不碎片化存储）。⑤ needs.stack_kb 记录不消费（V1 运行时常量已知限制维持）；非 WAMR 桩构建无安装匹配（不跑 APP 面）。用例 framework.app test_10（扫描矩阵/匹配行/安装拒/boot 直装走查〔差异化 wasm——模块缓存怪癖绕开〕）+ agent test_tsap_sim/test_wasm_build 档位族。夹具 = firmware/tests/app/gen_tier_pkgs.py（仓内机械生成 + 测试根签名 + pad 差异化）。

## 5b. 验签链多根与信任表更新（EC1 · Q-43/DEC-60②④⑤——实现随 EC2）

- **有效信任集（单一事实源 = ts-appmgr 内部）**：`有效集 = 工厂根 ∪ ts_store_trust()->keys`。工厂根 = TEST 构建 `{test_root}`（Q-29④ 固定测试根维持）/ 生产 `{prov->root_pubkeys[0], [1]}`（**pk1 自本批消费**——schema v1 既存双钥轮换预留字段，此前死字段）。工厂根不受信任表管辖（吊销/轮换 = sys/prov-write 维护通道职权——owner 凭证层）；开发者键 = 信任表管辖（密码学层：现信任键签 COSE 即可推动 ver+1——安卓「平台根 + 开发者自签」同型分层）。有效集恒非空（工厂根常在）——无自锁死面。
- **verify_slot 根钥参数语义（Q-43⑤）**：显式传键 = 单键验签（ts_appmgr_install 本地装包/测试路径——签名与行为不变）；**NULL = 迭代有效集**（任一键过即过；≤1+2+8 键序贯尝试——ed25519 验签失败可重试〔sm 源缓冲不被 crypto_sign_open 改写〕）。TEST 构建 NULL 同样走迭代（{test_root} ∪ 表——测试可注册开发者键实证多根面）。**顺带根治存量生产缺陷**：rollback_n 此前 NULL 且生产 NULL = 拒 → IR2-07 以来生产回滚路径恒拒（TEST 不可见——测试根覆盖 NULL）；修复 = NULL 语义转有效集。
- **trust-update 命令链（ts-appmgr 侧编排，LLD-ts-net §4 命令面）**：① args.data（COSE_Sign1 与 TSAP 同构：tag18/phdr{1:-8}/uhdr∅/payload/sig64）RAM 解析（verify.c 增 `ts_appmgr_verify_cose_ram`——Sig_structure 前缀构造与 slot 路径同源）→ ② payload 表 schema 走查（ts_store_trust_validate）→ ③ `ver == 当前 ver + 1`（严格 N+1：重放/跳版均拒——TUF）→ ④ 签名对**当前有效集**任一键过 → ⑤ ts_store_trust_write（乒乓持久化 + 重载）+ `TS_EVT_TRUST_UPDATED{ver}` + printk 留痕。空表合法（全撤开发者键回工厂根单源）。
- **侧载纪律（EC4 定稿——同验签链无例外）**：TSAP 装入槽的**唯一写路径** = stage_begin/chunk（ts_store_slot_write 消费点唯一）；一切安装通道（zenoh 部署 / 回滚翻转 / 未来 SD/USB 侧载）必经 stage_verify/verify_slot 同一收口——本地物理通道（设备形态批）复用该链，无第二验签路径（OpenWrt 反面教训——R9 §6）。**EC4 落地 = L5 检查 7**（testing.md §3：slot write/erase 调用点白名单 = pkg.c——未来侧载实现的结构性约束，越界 = CI 失败）；SD/USB 侧载通道本体按设备形态按需（Q-40②——形态到位前无消费者，不预建）。

## 5c. 安装闸本地确认（F3 · Q-46①③/DEC-62——实现随设备形态批）

- **接入点 = 固件侧挂起态**：prov v2 第三尾键 `lconf`（0/1；缺省 0 = 无头板逐字节不变——11 对存量 prov 零重刷）。lconf=1 时 **activate（含 install 单发路）过闸不切 meta**：置 pending（仅内存——复位即失 = fail-closed，槽字节保留可重推）+ 60s 超时（`TS_APPMGR_PENDING_TIMEOUT_MS`，sysworkq k_work）+ 事件外发。**EC4 同收口纪律的闸面**：一切安装通道（stage 部署 / install 单发 / 未来侧载）同过此闸，无例外。
- **API（仅固件内本地路——无 zenoh 命令面 = 远程不可确认）**：`ts_appmgr_confirm_pending`（→ 走 stage_commit 提交体：digest 复查 + 停旧 APP + meta 原子切换）/ `ts_appmgr_reject_pending`（撤销 + 清台——重试须完整重推）/ `ts_appmgr_pending_active`（手势模态查询）/ `ts_appmgr_pending_summary`（呈现面单一事实源：ASCII 多行 manifest 摘要——EC3 本地路消费同一 manifest 数据面）。
- **事件四态**：`TS_EVT_PENDING_INSTALL/INSTALL_CONFIRMED/INSTALL_REJECTED/INSTALL_TIMEOUT`（payload `{slot, entry}`；订阅外发 …/sys/event——挂起 = 安全类 QoS；LLD-ts-net §5）。
- **net 回执**：activate 过闸 = status `-13 TS_E_PENDING` + data `{pending:1, slot}`（结构化中间态非失败——wrap_reply 语义原样转发）；Agent deploy 链按「待板上本地确认」收尾（pending_local_confirm=True + 租约照常归还）。
- **挂起面**：`ts_app_info_t.pending_slot`（加性，0xFF = 无）——get-app/activate 回执可见；单挂起窗（pending 期再 activate = BUSY；新 begin 终止挂起窗）。
- **手势模态（设备形态胶水——Q-46③）**：pending 期 BOOT 短按=确认 / 长按≥2s=拒绝（模态独占——与 F1 arb 切换互斥）；呈现 = 形态面（atkbench：LVGL + AKP1-4 判据行——DEC-62②）。
- 用例：framework.app test_14（过闸/单窗/summary/get-app 面/确认切 meta/拒绝不动/超时 fail-closed/begin 覆盖/lconf=0 零回归）+ framework.store prov v2 12 对矩阵 + agent test_push_app_install_gate_pending（-13 中间态收尾）。真机：af3_gate_console.txt（timeout 路径全链——deploy → AKP1 → 60s → AKP4 撤销）；确认/拒绝路径 = owner 按键判据（AKPC/AKP2、AKPR/AKP3）。

## 5d. APP 间消息路由（P1-1 · HLD §3.4——DEC-04 禁直接互访的唯一例外通道）

- **API**：`ts_appmgr_msg_send(ctx, target_app_id, data, len)`（native `ts_msg_send`）→ 框架路由至目标运行实例（串身份 rt.app_id_str 匹配；多实例同 app_id = 首个命中）；`ts_appmgr_msg_recv(ctx, from, buf, cap, &len)`（native `ts_msg_recv`，接收被动无权限门）。evt 通知 = mailbox 投递 `TS_APP_EVT_MSG`（0x4D53475A "MSGZ"——app_evt 收此负载调 recv 取件）。
- **授权（合同 10）**：manifest caps `msg:send:<目标app_id>` 名单（≤4 目标/幂等/串文法 = zenoh key 段同源——LLD-ts-hal §2 v0.2.5）；**权限先于目标解析**（未授权探测不泄露运行面存在性）。目标未运行 = TS_E_NOTFOUND；未声明 = TS_E_PERM（留痕）。
- **FIFO 语义**：每实例 4 槽 × 96B（`TS_APPMGR_MSG_SLOTS/MSG_MAX`——DEC-62④ P1-1 出处）；**满槽 = 发送方 TS_E_BUSY 背压不丢弃**（与 mailbox 广播满丢最旧语义分立：点对点语义 vs 观测语义）；发送方身份随槽携带（审计/回信寻址）；接收缓冲不足 = TS_E_RANGE 不弹出。
- **Agent 镜像**：NATIVE_WHITELIST +2；约定块文法/签名/使用说明（msg:send 名单 + 0x4D53475A 取件协议）；面检查镜像测试。
- 用例：framework.hal test_16（名单文法矩阵 + 裁决）+ framework.app test_15（双实例路由/授权矩阵/FIFO 序/背压/取件）+ agent TestMsgNativesMirror。真机双 APP 互发 demo = 可复用 multiappbench（板侧固件含新 native 面——随下一板级轮）。

## 6. 测试要点

- L1：包解析/验签（坏签名/截断/字段缺失矩阵）；slot 切换掉电注入（meta 撕裂恢复）。
- L2：生命周期全迁移；健康探针超时→回滚→超限隔离。
- L4：安装→运行→升级→回滚全链重放（含 ts_evt 事件序）。
- L5：导入面装配过滤的静态断言（符号注册点唯一 = host.c）。

## 7. 未决依赖

- DEC-21/25/23/27 已裁；DEC-31（APP 线程模型：禁自建线程）已裁；DEC-43（宿主线程模型 A + 锁收口）已裁。
- **v0.2 实现批留痕（2026-09-26，framework.app 3 用例全绿）**：
  - 已落地：runtime.c（每 APP 一框架线程〔V1 单活跃〕/mailbox DR-14 满丢最旧/停止 join 2s 强杀/健康探针连续〔DEC-27：3〕败自停→health_fail 回滚入口）+ natives.c（ts_api_v1 V1 子集：gpio_write/gpio_read/pwm_set/adc_read/time_ms/log_write；ctx 由 exec_env user_data 注入防伪造——wasm 传参仅占位）。
  - **已知偏差 ①（结构化装配→调用期裁决）**：WAMR natives 为全局注册（namespace "env"），"未授权符号链接期不存在"需 per-instance natives 支持——留待 WAMR 升级/AOT 构建期裁剪；调用期经 ts_perm_check 拒绝 + TS_EVT_PERM_DENIED 留痕（合同 10 完整），测试 test_02 实证。
  - **已知偏差 ②（WAMR 平台怪癖规避）**：同进程 unload→reload 与 init→destroy→init 均实测失败（dev-env §5-12）——模块进程级复用（同字节流复用、stop 不卸载、换包需重启）；升级路径随板级/WAMR 修复版再议。
  - 健康导出名对齐 manifest v1 权威：`health_ping`（本文件 §4 早前笔误 app_health_ping 以 TsapManifest 为准）。
  - **收尾单元落地（v0.4）**：ts_appmgr_boot_start（active slot TSAP → manifest canonical 走查〔未知键 fail-closed；caps ';' 组合——ts_perm_parse 位图或合并；app_id/app_ver 提取；stack_kb/heap_kb 读取但 V1 消耗运行时常量〕→ wasm 装载〔CONFIG_TS_APP_LOAD_MAX 结构性上限〕→ app_start → STAGED→ACTIVE）；boot 步骤 8 app_load 尾部追加（APP 故障不阻塞启动 = 合同 6 显式例外〔HLD §4.4-8〕）；CONFIG_TS_APP_WAMR 默认 y；Agent E2E 使用固件同源夹具 wasm。

## 修订记录
- v0.9.2 · 2026-10-18：R5-V——stage_commit 包身份提取（app_id/app_ver → current_apps + ts_app_info_t；F3 终端 verdict 行保真）。
- v0.9.1 · 2026-10-16：**P1-3（供电槽 natives）**——ts_power_set/get 暴露 + Agent 镜像。
- v0.9 · 2026-10-16：**P1-1（HLD §3.4 APP 间消息）**——新增 §5d 路由面 + natives + Agent 镜像；twister 111（+2）/agent 197（+1）。
- v0.8 · 2026-10-16：**F3（Q-46①③/DEC-62 安装闸本地确认）**——新增 §5c：固件侧挂起态（lconf prov 第三尾键，缺省 0 = 无头板不变）+ activate/install 同闸（EC4 无例外）+ confirm/reject 仅固件本地路 + 60s fail-closed + 事件四态 + -13 结构化回执 + pending_slot 加性面。用例 test_14 + store 12 对矩阵 + agent pending 测试；真机 timeout 路全链 PASS（AKP1→AKP4）。
- v0.7.2 · 2026-10-15：**EC4（侧载纪律定稿）**——§5b 增 L5 检查 7 引用（slot 收口白名单 = pkg.c）；SD/USB 侧载本体按设备形态按需（Q-40②）。
- v0.7.1 · 2026-10-15：**EC2（多根验签/trust-update 实现）**——§5b 落地：有效集构建（TEST={测试根}∪表——多根 sim 可测）/COSE RAM 验签/更新编排五步；install NULL 放开；rollback NULL 生产恒拒缺陷修复。用例 framework.app test_13_trust_chain（11 断言组：基线拒/租约门/陌生键拒/跳版拒/注册/多根安装/重放拒/互荐/全撤回复拒/工厂根全程可用）+ 夹具 gen_trust_fixtures.py 入仓（固定种子+测试根签名——教训 27）。
- v0.7 · 2026-10-15：**EC1（Q-43/DEC-60 · 验签链多根设计）**——新增 §5b：有效集分层（工厂根 ∪ 信任表）+ verify_slot NULL 语义 + trust-update 编排（COSE RAM 验签/严格 N+1/有效集签名门）+ 侧载纪律（EC4 设计面）；生产回滚 NULL 恒拒存量缺陷定案（EC2 修复 + 用例）。
- v0.6.3 · 2026-10-14：**CG5-B（Q-39③ 方案 A · 资源白名单 registry）**——scan res_csv + activate/boot 绑定 + res_allows 裁决；sys/fs-* 命令面授权源。
- v0.6.2 · 2026-10-14：**CG5-A（Q-39④ · 能力发现）**——get-info caps 块（WAMR 构建六键形态）+ Agent push_app 装前预检（TA_E_POLICY 结构化拒——设备档位不支持/线性内存超帽，零上传零租约）。
- v0.6.1 · 2026-10-14：**CG4（DEC-59/Q-39②⑤ · §5a 实现）**——scan_needs/needs_match/双门 Kconfig/槽池断言/Agent 镜像（见 §5a 实现注记）；get-info caps 随 CG5。
- v0.6 · 2026-10-14：CG1（Q-39 · HLD-contract-v2 §7）——§5a 资源档位与安装期匹配（manifest tier/needs + 尺寸门分档双门 + 匹配矩阵 + get-info caps——实现随 CG4 消费 AG7 数值；字段呈 Q-42 门③）。

- v0.5.2 · 2026-10-02：板级十第二修复——boot 装载成功路径补 initialized=true + active_slot=meta.active_slot（此前首次 get_info 惰性初始化盲写 state=STAGED 把 ACTIVE 打回〔装载结果被观测面抹掉〕，且 active_slot 不回填 = activate/get-app 槽位对拍必败；真机 DB6/get-app 对拍首证，docs/board-deploy.md）。

- v0.5.3 · 2026-10-07：MD1.2g（单元 A，DEC-47③⑥）——§2 manifest 增可选键 av_fmt/av_w/av_h（与 caps av: 互为充要）+ fs_paths 补记（MD1.2e）；natives 面 +ts_av_capture/ts_net_publish（V1 符号集 = gpio×2/pwm/adc/time/log + fs×4 + av×2）；boot 走查增 av_* 键 + ts_av_config_bind 随载绑定。回归 twister 15/15（68 用例）。
- v0.5.1 · 2026-10-02：板级十跨轨命名对齐——§2 manifest exports 名修正为 app_init/app_tick/app_evt（§4 调用约定/固件 runtime lookup/夹具 wasm 三方一致；Agent 侧 TsapManifest._EXPORTS_ALLOWED 同步修复——早前 init/tick/evt 漂移会拒绝一切真包，env 门控的 sim E2E 掩盖）。

- v0.5 · 2026-10-01：板级六（PSRAM 挂接，docs/board-psram.md）——WAMR 实例堆统一为显式池：wasm_runtime_full_init(Alloc_With_Pool) 注入堆缓冲（事实修正：WAMR-2.4.5 的 WASM_ENABLE_GLOBAL_HEAP_POOL 旗标无消费者，wasm_runtime_init() 实为系统分配器——"64KB 池基线"从未生效；池模式下 64KB 结构性不可行〔线性内存一页即 64KB〕，TS_APP_WAMR_HEAP 默认 65536→262144）；TS_APP_PSRAM_HEAP（esp32s3 = SMH_REG_ATTR_EXTERNAL 分配 = HLD §4.6 分层纪律落点；其余 = 内部静态池）。
- v0.4 · 2026-09-26：M2b.2 收尾——boot 步骤 8 slot 装载 + 默认 y + E2E 真夹具 wasm；M2b.2 全部完成（twister 14/14〔58 用例〕）。
- v0.3 · 2026-09-26：DEC-43 接线批——§5 运行时宿主与 natives 落地（framework.app 端到端）；§7 两项 V1 已知偏差（调用期裁决/模块进程级复用）+ 健康导出名对齐 health_ping + M2b.2 收尾余项登记。
- v0.1 · 2026-09-20：首版草案（"按能力过滤符号装配"为权限硬边界核心机制）。
- v0.2 · 2026-09-20：review-01——slot 经 ts-store（DR-01）、mailbox 串行化与卸载停止语义（DR-14）、APP 状态不持久化声明（DR-15）。
- v0.2.1 · 2026-09-21：裁决同步——DEC-27 每板堆配置；出处标注收敛（SC-02）。
- v0.2.2 · 2026-09-21：owner 问询线程模型——§5 增 APP 线程限制（禁自建线程/编译期禁用/三层限制机制），登记 Q-13。
- v0.2.3 · 2026-09-22：M2a 定稿——§2 TAPP/TSAP v1 容器头**16 字节**：magic(4)+fmt_ver u16+manifest_len u32+wasm_len u32+rsv u16（尾部预留）；**多字节整数一律大端**（网络序，与 CBOR/COSE 生态一致；内部分区小端互不相关）。头解析（含边界自洽）已落 include/ts/tsap.h（M2a），COSE 验签仍属 §2/M2b。
