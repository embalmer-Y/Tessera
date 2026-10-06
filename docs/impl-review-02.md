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
