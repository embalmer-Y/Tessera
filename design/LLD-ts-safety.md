# LLD · ts-safety v0.1 草案

> **状态**：v0.1 草案，随 LLD 批次待 owner review。上位：HLD §3.2/§4；公共约定 `LLD-00-common.md`。
> **职责**：输出保护层（限幅/slew/限流）、三安全态状态机、estop 直达路径、fail-safe 管线。
> **合同关联**：合同 1（三安全态）、2（唯一写路径）、5（estop 不经队列）、7（供电同轨）、8（本地独立生效）。

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
- 注册表：静态数组，容量〔Q-10 提案 32〕；描述符指针来源 = 构建期配置 + ts-periph 描述符（安全参数**运行时只读**，合同 10）。

## 3. 三安全态状态机（channel.c）

```text
            注册完成                    
SAFE_POWERON ──── 链路确立(ts_safety_set_link(true))──→ ACTIVE
    ↑                                                  │
    │                              链路判定成立(↓false) │ estop / WDT / system_fail
    └── 链路恢复(带滞回) ←── SAFE_LINKLOSS ←────────────┴──→ SAFE_FAULT（须显式命令复位）
```

- 每次通道态迁移发布 `TS_EVT_SAFE_STATE_CHANGED`（uid + 旧/新态）——重放观测点。
- **断链恢复语义（DR-04）**：SAFE_LINKLOSS → ACTIVE 仅解除写入封锁，**不自动回写断链前的值**——shadow 即安全值，输出恢复必须经显式 commit（防恢复瞬间意外动作）。
- 并发：全局 `link_up` 原子标志 + 每通道 `state` 原子枚举；迁移操作在 sysworkq 上下文串行化（避免多源并发改态）。

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
7. 审计：commit 事件（uid/value/t/结果/**调用者 app_id**〔DEC-30②〕）入环形审计缓冲〔深度 Q-10 提案 64〕，供遥测与重放比对。

- **审计消费与溢出（DR-07）**：消费者 = ts-net 遥测合流 + `sys:get-audit` 导出命令（LLD-ts-net §4）；溢出覆盖最旧并累加丢弃计数；**V1 不落盘（掉电丢失）**——记入 HLD §1 裁剪清单〔DEC-30④〕。

## 5. estop 与 fail-safe 直达（force.c）——合同 5/8

```c
void ts_safety_force_all_fault(void);   /* [ISR] estop GPIO 回调直接调用：置原子 forced → 逐通道直写 fault 值 */
void ts_safety_system_fail(uint32_t reason);  /* [thread] WDT/BOOT/子系统故障：进 SAFE_FAULT 并停机编排 */
void ts_safety_set_link(bool up);       /* [thread] ts-net 专用（经 sysworkq 串行化迁移） */
ts_res_t ts_safety_clear_fault(void);   /* [thread] 仅 sys:estop-clear 命令可达（host-only + 确认令牌，LLD-ts-net §4；授权 DEC-30①） */
```

- **estop 路径纪律**（L5 机械检查目标）：`ts_safety_force_all_fault` 调用图内禁：分配、队列、锁、协议栈符号；仅原子置位 + driver_dispatch 直写（driver_dispatch 写函数须可重入/无锁——在 driver_dispatch.c 内以"写只依赖注册期冻结数据"实现）。
- **estop 引脚绑定（DR-11）**：devicetree `chosen` 节点 `ts,estop-gpio`（板级 overlay 提供）；boot 步骤 1 由本模块读取并配置 IRQ（触发沿来自 prov 配置，构建期/烧录期确定）。
- estop ISR 返回后：sysworkq 补发 `TS_EVT_ESTOP`（含触发时间戳，合同 5"事后补发事件"）。
- 与 commit 竞争的裁决：force 先置 `forced` 原子标志；commit 末段在 irq_lock 内复查（§4-6），保证 ISR 写入不被随后末笔覆盖；`clear_fault` 前 forced 标志不复位。

## 6. driver_dispatch.c（唯一驱动调用点）

```c
typedef struct { void (*write)(const ts_out_ch_t *, const ts_out_value_t *);
                 int (*read)(const ts_out_ch_t *, ts_out_value_t *); } ts_driver_ops_t;
extern const ts_driver_ops_t ts_drivers[3];   /* [GPIO]=native_sim 桩/gpio、[PWM]、[POWER] */
```

- 全库 **唯一** 出现 `gpio_pin_set`/`pwm_set_*` 等输出的文件（testing.md §3.1 白名单 = 本文件）。
- native_sim：桩驱动把写序列记入每通道环形记录（供 L4 重放 golden 比对）。

## 7. Kconfig（节选）

| 项 | 默认〔Q-10〕 | 说明 |
|---|---|---|
| CONFIG_TS_SAFETY_MAX_CHANNELS | 32 | 注册表容量 |
| CONFIG_TS_SAFETY_AUDIT_DEPTH | 64 | 审计环形缓冲深度 |

## 8. 测试要点

- L1：注册校验（缺三态/越界拒绝）；clamp/slew/限流数学（边界值表驱动）；状态机全迁移。
- L4：estop→commit 竞争注入（虚拟时钟下重复 10³ 次随机交错，末笔恒为 fault 态值）；断链→恢复滞回序列。
- L5：白名单扫描/estop 符号图审计的目标文件即本模块 §6。

## 9. 未决依赖

- DEC-22（断链时序参数）、DEC-23（分区）、DEC-27（容量/审计深度）、DEC-30②（共享写 = 后写胜出 + 审计含 app_id）已裁；无未决。

## 修订记录

- v0.1 · 2026-09-20：首版草案（estop 无锁直达 + commit 末段 irq_lock 复查为本版关键设计）。
- v0.2 · 2026-09-20：review-01——断链恢复不自动回写（DR-04）、审计消费/溢出策略（DR-07）、estop DT 绑定（DR-11）、clear_fault 授权收敛 sys:estop-clear（DR-03）。
