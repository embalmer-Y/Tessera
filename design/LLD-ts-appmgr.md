# LLD · ts-appmgr v0.4（M2b.2 完成）

> **状态**：v0.6.3（2026-10-14 CG5-B：**资源白名单 registry**——needs.resources → res_csv〔scan 单一解析源〕→ activate 绑定 + boot 恢复；sys/fs-* 授权源）；v0.6.2（2026-10-14 CG5-A · Q-39④：**get-info caps 块实现**——{tiers, max_linear_memory_kb, slot_pool_kb} 设备自报 + Agent push_app 装前预检〔caps 缺失 = 旧固件跳过〕；CG5-B 资源推送随下单元）。上位：HLD §3.4 + HLD-contract-v2 §5；公共约定 `LLD-00-common.md`。上位：HLD §3.4 + HLD-contract-v2 §5；公共约定 `LLD-00-common.md`。
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
- APP 线程：每 APP **恰好一个**框架创建的 Zephyr 线程（优先级/栈见 LLD-00 §4 与 manifest.mem.stack，上限〔DEC-27： 8KB〕）；同时加载上限〔DEC-27： 4〕个 APP。
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
- v0.6.3 · 2026-10-14：**CG5-B（Q-39③ 方案 A · 资源白名单 registry）**——scan res_csv + activate/boot 绑定 + res_allows 裁决；sys/fs-* 命令面授权源。
- v0.6.2 · 2026-10-14：**CG5-A（Q-39④ · 能力发现）**——get-info caps 块（WAMR 构建六键形态）+ Agent push_app 装前预检（TA_E_POLICY 结构化拒——设备档位不支持/线性内存超帽，零上传零租约）。
- v0.6.1 · 2026-10-14：**CG4（DEC-59/Q-39②⑤ · §5a 实现）**——scan_needs/needs_match/双门 Kconfig/槽池断言/Agent 镜像（见 §5a 实现注记）；get-info caps 随 CG5。
- v0.6 · 2026-10-14：CG1（Q-39 · HLD-contract-v2 §7）——§5a 资源档位与安装期匹配（manifest tier/needs + 尺寸门分档双门 + 匹配矩阵 + get-info caps——实现随 CG4 消费 AG7 数值；字段呈 Q-42 门③）。

- v0.5.2 · 2026-10-02：板级十第二修复——boot 装载成功路径补 initialized=true + active_slot=meta.active_slot（此前首次 get_info 惰性初始化盲写 state=STAGED 把 ACTIVE 打回〔装载结果被观测面抹掉〕，且 active_slot 不回填 = activate/get-app 槽位对拍必败；真机 DB6/get-app 对拍首证，docs/board-deploy-01.md）。

- v0.5.3 · 2026-10-07：MD1.2g（单元 A，DEC-47③⑥）——§2 manifest 增可选键 av_fmt/av_w/av_h（与 caps av: 互为充要）+ fs_paths 补记（MD1.2e）；natives 面 +ts_av_capture/ts_net_publish（V1 符号集 = gpio×2/pwm/adc/time/log + fs×4 + av×2）；boot 走查增 av_* 键 + ts_av_config_bind 随载绑定。回归 twister 15/15（68 用例）。
- v0.5.1 · 2026-10-02：板级十跨轨命名对齐——§2 manifest exports 名修正为 app_init/app_tick/app_evt（§4 调用约定/固件 runtime lookup/夹具 wasm 三方一致；Agent 侧 TsapManifest._EXPORTS_ALLOWED 同步修复——早前 init/tick/evt 漂移会拒绝一切真包，env 门控的 sim E2E 掩盖）。

- v0.5 · 2026-10-01：板级六（PSRAM 挂接，docs/board-psram-01.md）——WAMR 实例堆统一为显式池：wasm_runtime_full_init(Alloc_With_Pool) 注入堆缓冲（事实修正：WAMR-2.4.5 的 WASM_ENABLE_GLOBAL_HEAP_POOL 旗标无消费者，wasm_runtime_init() 实为系统分配器——"64KB 池基线"从未生效；池模式下 64KB 结构性不可行〔线性内存一页即 64KB〕，TS_APP_WAMR_HEAP 默认 65536→262144）；TS_APP_PSRAM_HEAP（esp32s3 = SMH_REG_ATTR_EXTERNAL 分配 = HLD §4.6 分层纪律落点；其余 = 内部静态池）。
- v0.4 · 2026-09-26：M2b.2 收尾——boot 步骤 8 slot 装载 + 默认 y + E2E 真夹具 wasm；M2b.2 全部完成（twister 14/14〔58 用例〕）。
- v0.3 · 2026-09-26：DEC-43 接线批——§5 运行时宿主与 natives 落地（framework.app 端到端）；§7 两项 V1 已知偏差（调用期裁决/模块进程级复用）+ 健康导出名对齐 health_ping + M2b.2 收尾余项登记。
- v0.1 · 2026-09-20：首版草案（"按能力过滤符号装配"为权限硬边界核心机制）。
- v0.2 · 2026-09-20：review-01——slot 经 ts-store（DR-01）、mailbox 串行化与卸载停止语义（DR-14）、APP 状态不持久化声明（DR-15）。
- v0.2.1 · 2026-09-21：裁决同步——DEC-27 每板堆配置；出处标注收敛（SC-02）。
- v0.2.2 · 2026-09-21：owner 问询线程模型——§5 增 APP 线程限制（禁自建线程/编译期禁用/三层限制机制），登记 Q-13。
- v0.2.3 · 2026-09-22：M2a 定稿——§2 TAPP/TSAP v1 容器头**16 字节**：magic(4)+fmt_ver u16+manifest_len u32+wasm_len u32+rsv u16（尾部预留）；**多字节整数一律大端**（网络序，与 CBOR/COSE 生态一致；内部分区小端互不相关）。头解析（含边界自洽）已落 include/ts/tsap.h（M2a），COSE 验签仍属 §2/M2b。
