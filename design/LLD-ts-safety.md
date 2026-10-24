# LLD · ts-safety v0.3.4

> **状态**：v0.3.4（2026-10-16 K3 真机定案：**F1 审计下沉双修正**——① 异常审计 flash 下沉移出 write_lock〔pend 槽携带、解锁后同调用持久化〕② 持久化 1Hz 节流〔失败提交循环风暴防护——真机擦 APP 对照实证：断链后 APP 每 tick E_STATE 下沉风暴反噬 net_wq 喂狗 → NET WDT 循环复位 noinit 0x20000〕；DEC-52① 意图保留〔首条恒在盘〕+ 丢弃计数可观测）；v0.3.3（2026-10-14 CG6 收口：**§9a 已知限制节补齐**——estop 清除实质面 CG1/CG2 已交付，ISO 13850 偏离与本地通道/仲裁信号源 deferred 如实入节）。上位：HLD §3.2/§4 + HLD-contract-v2；公共约定 `LLD-ts-common.md`。上位：HLD §3.2/§4 + HLD-contract-v2；公共约定 `LLD-ts-common.md`。
> **职责**：输出保护层（限幅/slew/限流）、三安全态状态机、estop 直达路径、fail-safe 管线、**控制源仲裁状态（本版新增）**。
> **合同关联**：合同 1（三安全态）、2（唯一写路径）、3（断链 fail-safe——**部署模式化**，见 §3a）、5（estop 不经队列 + 清除按设备能力）、7（供电同轨）、8（本地独立生效）、**11（控制源仲裁——本版新增）**。

## 1. 内部结构

```text
src/safety/
  channel.c    通道注册表 + 三态状态机
  commit.c     唯一写路径出口（保护校验 + 驱动分发）
  force.c      estop/fail-safe 直达路径（ISR 安全，无锁）
  driver_dispatch.c  Zephyr 输出驱动调用的**唯一合法位置**（L5 白名单文件）
```

## 2. 通道模型与注册（channel.c）

```c
typedef enum { TS_CH_GPIO, TS_CH_PWM, TS_CH_POWER } ts_ch_kind_t;
typedef union { bool b; uint32_t u; struct { bool en; uint32_t ma; } pwr; } ts_out_value_t;

typedef struct {
    const char *uid;          /* 稳定逻辑名（ts-periph 分配，编址用） */
    ts_ch_kind_t kind;
    ts_out_value_t poweron, linkloss, fault;   /* 三安全态：合同1，缺一拒绝注册 */
    struct { uint32_t min, max;               /* 限幅 */
             uint32_t slew_per_ms;             /* 变化率上界 */
             uint32_t current_limit_ma; } limits; /* 供电限流（TS_CH_POWER） */
} ts_out_ch_t;

ts_res_t ts_safety_register_channel(const ts_out_ch_t *ch);  /* [thread] init 期 + 外设注册期 */
```

- 注册校验：uid 非空且不撞、三态值齐全且落在 limits 内（fault/poweron/linkloss 值本身必须合法——安全态值不得超限）；违例 → TS_E_PARAM（注册即失败，不留半注册）。
- 注册表：静态数组，容量〔DEC-27： 32〕；描述符指针来源 = 构建期配置 + ts-periph 描述符（安全参数**运行时只读**，合同 10）。

## 3. 三安全态状态机（channel.c）

```text
            注册完成
SAFE_POWERON ──── 链路确立(ts_safety_set_link(true))──→ ACTIVE
    ↑                                                  │
    │                              链路判定成立(↓false) │ estop / WDT / system_fail
    └── 链路恢复(带滞回) ←── SAFE_LINKLOSS ←────────────┴──→ SAFE_FAULT（清除通道见 §5a）
```

- 每次通道态迁移发布 `TS_EVT_SAFE_STATE_CHANGED`（uid + 旧/新态）——重放观测点。
- **断链落驱动（v0.2.6，板级九修复）**：ACTIVE → SAFE_LINKLOSS 迁移**声明值落驱动**（HLD §4.5-S2 原文；此前实现仅改 shadow = 物理输出滞留断链前值的合同 3 欠账，PWM 真后端接线时被板级九 bench 拦下）。fault 路径（force.c）本就落驱动；恢复语义不变（DR-04 不回写）。已知余项：注册期 SAFE_POWERON 的 poweron 值落驱动（冷启物理态）尚未接线——V1 各板 poweron 值与硬件缺省态一致故未暴露，登记板级九报告观察项。
- **断链恢复语义（DR-04）**：SAFE_LINKLOSS → ACTIVE 仅解除写入封锁，**不自动回写断链前的值**——shadow 即安全值，输出恢复必须经显式 commit（防恢复瞬间意外动作）。
- 并发：全局 `link_up` 原子标志 + 每通道 `state` 原子枚举；迁移操作在 sysworkq 上下文串行化（避免多源并发改态）。

### 3a. 部署模式守卫（Q-41① · 合同 3 模式化——本版新增）

- **模式语义**：`orchestrated`（缺省，现行行为一分不变）——linkmon 断链判定 → `ts_safety_set_link(false)` 全输出进 SAFE_LINKLOSS；`standalone` —— 编排通道失联为**留痕事件**（TS_EVT_NET_LINK_DOWN 既有观测面），**不调用 set_link 迁移**，本地逻辑照常（本地合同全量生效：三安全态/唯一写路径/限幅/看门狗四层/estop 至高——standalone ≠ 无安全，仅失联语义不同；ISO 17757「自治机器在任何通信失效下维持安全运行」背书）。
- **落点**：模式守卫在 linkmon 侧（LLD-ts-net §6）——`deploy_mode == TS_DEPLOY_ORCHESTRATED` 才触发迁移调用；prov schema v2 字段（LLD-ts-store §4），**fail-safe 侧缺省**（缺字段 = orchestrated）。
- 恢复对称：orchestrated 恢复 = 显式重写（DR-04 既有）；standalone 无迁移故无恢复动作。
- 运行时切换：V1 不做（prov 声明；重配 = 重新 provision——显式可审计）；混合形态（按通道组）机制余地留在 schema 数组形态，需求实证后另立 Q。
- **实现注记（CG2）**：守卫落点 = linkmon `link_migrates_safety()`（断链/恢复对称仅 orchestrated 迁移）；standalone 的 ACTIVE 驱动者 = ts_net_init boot 链路声明（LLD-ts-net §6——CG1 文本未覆盖的实现缺口，本批定案）。用例 framework.net test_14（零迁移断言）。

## 4. 唯一写路径出口（commit.c）——合同 2 的强制点

```c
ts_res_t ts_safety_commit(const char *uid, ts_out_value_t v);  /* [thread] */
ts_res_t ts_safety_readback(const char *uid, ts_out_value_t *out); /* [any] 影子值读回 */
```

内部流程（互斥锁 `commit_lock` 内）：

1. 查表 → 无则 TS_E_NOTFOUND；
2. 通道 state ≠ ACTIVE → **TS_E_STATE**（安全态下输出写入被拒，输入不受影响——合同 3）；
3. 限幅：clamp 到 [min,max]（越界原始值记录审计事件）；
4. slew：|Δv| ≤ slew_per_ms × Δt（Δt = ts_time_ms − last_t）；超率 → 拆分拒绝（本周期只允许到界值），返回实际落值；
5. 限流（TS_CH_POWER）：请求电流 > current_limit_ma → TS_E_RANGE；
6. 末段临界区：`irq_lock(); if (!atomic_forced) { driver_dispatch_write(ch, v); shadow=v; } irq_unlock();`
   ——防 estop ISR 与本线程竞争末笔（见 §5）；
7. 审计：commit 事件（uid/value/t/结果/**调用者 app_id**〔DEC-30②〕）入环形审计缓冲〔深度 DEC-27： 64〕，供遥测与重放比对。

- **审计消费与溢出（DR-07）**：消费者 = ts-net 遥测合流 + `sys:get-audit` 导出命令（LLD-ts-net §4）；溢出覆盖最旧并累加丢弃计数；**V1 不落盘（掉电丢失）**——记入 HLD §1 裁剪清单〔DEC-30④〕。
- **锁收口（DEC-43，v0.2.4）**：`commit_lock` 经内部 `ts_safety_write_lock/unlock` 受控暴露——**安全态迁移路径（set_link / force_channel_fault / channel_recover / clear_fault）与供电预算检查-提交（ts_power_request，走 `ts_safety_commit_locked`）全部纳入同一互斥**（k_mutex 非递归，持锁方必须走 _locked 变体）。锁序 write_lock → pubq（事件发布路径），单向无环；线程上下文专用（ISR 禁入）；**estop ISR 路径（force_all_fault + 末段 irq_lock 复查）保持无锁直达不变（合同 5）**。读路径（readback/summary/遥测快照）维持无锁——影子字段均 ≤32bit 对齐读无撕裂，瞬时陈旧属观测面可接受（控制路径全部持锁）。回归 = framework.conc（对齐双冲 0 超限/迁移×提交不变量/pubq 完整性）+ 全量 13 套件。

## 5. estop 与 fail-safe 直达（force.c）——合同 5/8

```c
void ts_safety_force_all_fault(void);   /* [ISR] estop GPIO 回调直接调用：置原子 forced → 逐通道直写 fault 值 */
void ts_safety_system_fail(uint32_t reason);  /* [thread] WDT/BOOT/子系统故障：进 SAFE_FAULT 并停机编排 */
void ts_safety_set_link(bool up);       /* [thread] ts-net 专用（经 sysworkq 串行化迁移；**模式守卫见 §3a**） */
ts_res_t ts_safety_clear_fault(void);   /* [thread] 清除通道（按设备能力声明，§5a） */
```

- **clear_fault 复位语义（v0.2.3 定案，impl-review-01 F-8——v0.2.2 ③"随 M3 联调复核"闭环）**：释放 forced 锁存后逐 SAFE_FAULT 通道做**状态条件恢复**（link up → ACTIVE，否则 SAFE_LINKLOSS）+ **输出值不回写**——物理输出保持 fault 安全值直至下一次显式 commit（与 DR-04"断链恢复不自动回写"同则：任何恢复路径都不凭记忆回写历史值，调用方须重新提交目标值；消除了"clear 即跳回 estop 前值"的隐性风险）。

- **estop 路径纪律**（L5 机械检查目标）：`ts_safety_force_all_fault` 调用图内禁：分配、队列、锁、协议栈符号；仅原子置位 + driver_dispatch 直写（driver_dispatch 写函数须可重入/无锁——在 driver_dispatch.c 内以"写只依赖注册期冻结数据"实现）。
- **estop 引脚绑定（DR-11）**：devicetree `aliases` 节点 `ts-estop-gpio`（板级 overlay 提供）；boot 步骤 1 由本模块读取并配置 IRQ（触发沿来自 prov 配置，构建期/烧录期确定）。
- estop ISR 返回后：sysworkq 补发 `TS_EVT_ESTOP`（含触发时间戳，合同 5"事后补发事件"）。
- 与 commit 竞争的裁决：force 先置 `forced` 原子标志；commit 末段在 irq_lock 内复查（§4-6），保证 ISR 写入不被随后末笔覆盖；`clear_fault` 前 forced 标志不复位。

### 5a. estop 清除通道（Q-41③ · 合同 5 附注——按设备能力声明）

- **无本地交互能力的设备**（现全部板卡）：维持现状——远程 `sys:estop-clear`（confirm="estop" 硬令牌，LLD-ts-net §4）。**对 ISO 13850「复位仅限本地人为」的有据偏离**：无本地手段可用，令牌 + host-only 面 = 补偿控制；登记本文件已知限制节。
- **有本地交互能力的设备**（未来本地交互外设接入后）：本地清除为主（estop 器件物理脱开，ISO 13850 语义）；远程清除由 prov `estop_remote_clear` 配置（`enabled | disabled`，**缺省 disabled——保守侧**；enabled 时仍须令牌）。
- 触发面（硬件 ISR 至高）**两形态一字不差**；清除不解除锁存条件外任何状态、不引发输出（既有语义维持）。
- **实现注记（CG2）**：命令面守卫 = `sys:estop-clear` 入口按 prov `estop_remote_clear` 拒（TS_E_STATE + need=local-clear）；v1 prov 缺字段 = enabled（现网兼容——无本地交互设备的唯一清除通道）。用例 framework.net test_15。

## 5b. 控制源仲裁状态（Q-41② · 合同 11——本版新增）

```c
typedef enum { TS_ARB_REMOTE, TS_ARB_LOCAL } ts_arb_owner_t;
static atomic8_t arb_owner;   /* 远程编排 | 本地交互源 */
```

- **席位模型**：仲裁主体 = { zenoh 写命令（租约持有者）, 本地交互源（设备外设事实——有则占席，无则席位空缺 = 现行为零变化）}；estop = 席外至高（合同 5 不受本节影响）。
- **压制语义（EN 60204-1 §9.2.4 同型）**：本地交互源**激活期**，写路径按 `arb_owner == TS_ARB_LOCAL` 拒绝远程来源请求（TS_E_STATE，detail: local_active）——落点 = §4 commit 入口的**来源标记参数**（`ts_safety_commit` 增 `src: TS_SRC_ZENOH | TS_SRC_LOCAL`；门控只作用于 TS_SRC_ZENOTH〔zenoh〕路径，natives 写路径经 APP——APP 本身即编排意图的载体，V1 不经此闸，随本地交互外设实际形态复核）。
- **切换零输出**（EN 60204-1 §9.2.3 同型）：`ts_safety_set_arb(owner)` 仅改门控位 + 发 `TS_EVT_ARB_CHANGED`（owner/旧/新/t）——不产生任何通道写入；输出连续性由 APP 逻辑承载（Q-41④「交接=重声明」简化，bumpless 登记差距）。
- **租约联动**（LLD-ts-net §5 注）：本地激活 = 租约强制失效视图（远程 acquire 回执降级提示）；本地释放 = 远程可重新 acquire。
- **审计来源维度**：§4-7 审计事件增 `src` 字段（zenoh | local）——回溯「谁在什么时候压着谁写了什么」。
- 本地交互源的激活信号形态（按键/UI 会话打开）随本地交互外设实际接入定义——**本节先立席位与门控机制，信号源接线随后续设备形态批**。
- **实现注记（CG3）**：席位 = `ts_arb_owner` 原子（channel.c，缺省 REMOTE——席位空缺 = 现行为零变化）；`ts_safety_set_arb` 幂等（同席零事件零输出）+ TS_EVT_ARB_CHANGED（payload ts_arb_evt_t{owner,old}）；来源标记 = `ts_src_t {APP, ZENOH, LOCAL}`——`ts_safety_commit_src` 新入口（既有 commit/commit_a/commit_locked = TS_SRC_APP 不变），压制门控在 commit_impl 入口（持锁后、状态检查前——身份级拒绝优先，审计 res=TS_E_STATE + src 归因）；审计 src 维度 = ts_audit_entry_t 原 `_rsv` 字段转正（旧记录 0=APP 兼容）；get-audit 内存环条目末位加 src（加性——位置消费不受影响）；租约联动 = 视词语义（LLD-ts-net §4.5——不改在册状态，TTL 照常走完）。用例 framework.safety test_arb_seat_and_suppression + framework.net test_16_arb_lease_view。顺带修复：ts_safety_test_reset 此前不清审计环（full_scenario 丢弃算术用例序敏感——新用例先跑即暴露），增 ts_safety_audit_test_reset。

## 6. driver_dispatch.c（唯一驱动调用点）

```c
typedef struct { void (*write)(const ts_out_ch_t *, const ts_out_value_t *);
                 int (*read)(const ts_out_ch_t *, ts_out_value_t *); } ts_driver_ops_t;
extern const ts_driver_ops_t ts_drivers[3];   /* [GPIO]=native_sim 桩/gpio、[PWM]、[POWER] */
```

- 全库 **唯一** 出现 `gpio_pin_set`/`pwm_set_*` 等输出的文件（testing.md §3.1 白名单 = 本文件）。
- native_sim：桩驱动把写序列记入每通道环形记录（供 L4 重放 golden 比对）。
- **真机后端（板级三 GPIO / 板级九 PWM，均默认关）**：`CONFIG_TS_DRV_GPIO`（zephyr,user：uid + io-gpios）与 `CONFIG_TS_DRV_PWM`（zephyr,user：pwm-uid + pwms 三元胞；引脚路由经 PWM 控制器 pinctrl）。写路径 = sim 记录（L4 连续性）+ 真驱动写；uid 匹配通道才落寄存器（V1 单通道绑定，多通道随板声明扩展）。PWM 值域 = 打包 u 低 16 permille [0,1000] / 高 16 hz/100（api 层保证 hz≥100）；写函数 void 返回 → 失败进 `ts_drv_pwm_err_count()` 观测计数。真机验证：LEDC duty 寄存器六点 ±1‰ + 限幅截断 + 端点停止态 + 断链 fail-safe（docs/board-periph.md）。

## 7. Kconfig（节选）

| 项 | 默认〔DEC-27〕 | 说明 |
|---|---|---|
| CONFIG_TS_SAFETY_MAX_CHANNELS | 32 | 注册表容量 |
| CONFIG_TS_SAFETY_AUDIT_DEPTH | 64 | 审计环形缓冲深度 |

## 8. 测试要点

- L1：注册校验（缺三态/越界拒绝）；clamp/slew/限流数学（边界值表驱动）；状态机全迁移。
- L4：estop→commit 竞争注入（虚拟时钟下重复 10³ 次随机交错，末笔恒为 fault 态值）；断链→恢复滞回序列。
- L5：白名单扫描/estop 符号图审计的目标文件即本模块 §6。

## 9. 未决依赖

- DEC-22（断链时序参数）、DEC-23（分区）、DEC-27（容量/审计深度）、DEC-30②（共享写 = 后写胜出 + 审计含 app_id）已裁；无未决。

## 9a. 已知限制（CG6 收口节 · 如实登记）

- **ISO 13850「复位仅限本地人为」的有据偏离（§5a · Q-41③）**：现网全部板卡无本地交互能力——远程 `sys:estop-clear`（confirm="estop" 硬令牌 + host-only 面 + lease 外豁免）= 唯一清除通道；补偿控制 = 令牌确认 + 命令面留痕 + prov `estop_remote_clear` 可禁（v2 起有本地交互设备的出厂配置 = disabled〔保守侧〕）。**本地清除通道（estop 器件物理脱开 → 本地复位）随本地交互外设实际形态批接入**——届时本偏离撤销，prov 缺省翻 disabled（Q-42 现网兼容语义维持：v1 prov 缺字段 = enabled 不切断既有唯一通道）。
- **控制源仲裁本地席位信号源（§5b · Q-41②）**：席位/门控/租约联动/审计 src 机制已全量落地（CG3），本地交互源**激活信号形态**（按键/UI 会话）随本地交互外设批定义接线——席位空缺期（现全部板卡）零行为变化。
- **needs.stack_kb 记录不消费（§5a · CG4）**：V1 运行时消耗常量（既有已知限制维持）；消费面随板级内存预算批。

## 修订记录

- v0.3.3 · 2026-10-14：**CG6 收口（estop 清除通道）**——实质面已随 CG1（§5a 措辞 + prov 字段）/CG2（命令面守卫 + 用例）交付；本版补 **§9a 已知限制节**（ISO 13850 有据偏离/本地清除通道随硬件批/仲裁信号源接线 deferred/stack_kb 不消费——CG1 注记声称的「已知限制节」此前缺正式节点，本版补齐）。
- v0.3.2 · 2026-10-14：**CG3（Q-41② · §5b 仲裁机制实现）**——席位/set_arb/来源标记/压制门控/审计 src/事件外发（见 §5b 实现注记）；本地交互源信号源接线随后续设备形态批。顺带：ts_safety_test_reset 补审计环归零（用例序敏感缺陷）。
- v0.3.1 · 2026-10-14：**CG2（Q-41①③ · §3a/§5a 实现）**——linkmon 模式守卫 + standalone boot 链路声明注记（net/init 侧）+ estop-clear prov 守卫注记；§5b 仲裁（arb_owner/来源标记/租约联动/审计 src）仍随 CG3。
- v0.3 · 2026-10-14：**CG1（DEC-56/57/Q-41 A，措辞 DEC-58 已批）**——§3a 部署模式守卫（orchestrated 现行为不变 / standalone 断链仅留痕不迁移）；§5a estop 清除按设备能力声明（无交互设备维持远程令牌 = 有据偏离登记；有交互设备本地为主 + prov estop_remote_clear 缺省 disabled）；§5b 控制源仲裁状态（arb_owner 席位/激活压制远程/切换零输出 TS_EVT_ARB_CHANGED/审计 src 维度/租约联动注）；合同 3/5/11 措辞同步 AGENTS.md §6。实现随 CG2/CG3。
- v0.2.6 · 2026-10-02：板级九（PWM/ADC 真后端，docs/board-periph.md）——① §3 断链迁移补"声明值落驱动"（HLD §4.5-S2 欠账修复：此前仅改 shadow，物理输出滞留断链前值；真机 PB5 首证 linkloss 0% 落 LEDC）；② §6 增 CONFIG_TS_DRV_PWM 真机后端（zephyr,user 绑定 + err 计数；LEDC duty 六点 ±1‰ 真机验证）。回归：twister 15/15（65 用例）/L5 6/6 全绿。
- v0.2.5 · 2026-10-01：板级八（estop 真机，docs/board-estop.md）——① §5 estop DT 绑定机制修订：**aliases**（`DT_ALIAS(ts_estop_gpio)` ← 板 overlay `aliases { ts-estop-gpio = &node; }`）替代 chosen——v4.4 EDT 管道不发射非 zephyr 前缀 chosen 宏（dtlib 属性在、edtlib 弃，实证留痕）；DR-11 语义不变；② 真机实证：引脚沿→ISR 直达→fault 落通道 ≤20ms（轮询粒度上界）→锁存→clear+显式 commit 恢复，×3 轮；合同 5 链路真机首证。
- v0.2.4 · 2026-09-26：DEC-43 锁收口——§4 增 write_lock 语义（迁移路径/预算检查-提交纳入同一互斥；estop ISR 无锁直达不变；读路径无锁标注）；回归 framework.conc 3 用例 + twister 13/13（54 用例）全绿。
- v0.2.3 · 2026-09-25：impl-review-01 修复批（F-8）——§5 clear_fault 复位语义定案（v0.2.2 ③ 复核闭环）：状态条件恢复 + 输出值不回写（保持 fault 安全值直至显式 commit，与 DR-04 同则）。代码注释同步（channel.c），无行为变更。
- v0.1 · 2026-09-20：首版草案（estop 无锁直达 + commit 末段 irq_lock 复查为本版关键设计）。
- v0.2 · 2026-09-20：review-01——断链恢复不自动回写（DR-04）、审计消费/溢出策略（DR-07）、estop DT 绑定（DR-11）、clear_fault 授权收敛 sys:estop-clear（DR-03）。
- v0.2.1 · 2026-09-21：裁决同步——DEC-30② 审计含 app_id；出处标注收敛（SC-02）。
- v0.2.2 · 2026-09-22：M1 实现收敛留痕——① §4-3 限幅被拦截时返回 **TS_E_RANGE**（err.h：限幅/slew/预算均属"输出被安全层拦截"），落值仍为 clamp 后值；② §3 状态机图的 estop/system_fail 路径**不发布** SAFE_STATE_CHANGED（ISR 禁队列），观测走 TS_EVT_ESTOP 补发与状态查询；③ clear_fault 复位目标态取**条件恢复**（link up→ACTIVE，否则 SAFE_LINKLOSS；图未明示，随 M3 net 联调复核）。
