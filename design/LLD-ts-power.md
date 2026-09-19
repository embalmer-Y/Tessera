# LLD · ts-power v0.1 草案

> **状态**：v0.1 草案，随 LLD 批次待 owner review。上位：HLD §3.6；公共约定 `LLD-00-common.md`。
> **职责**：受控供电——供电槽开关、限流、功率预算上报（DEC-03：供电视同输出，走同一安全合同）。
> **合同关联**：合同 7（纳入 1–6 同一合同）、1（供电通道三安全态必声明）、2（开关必经 ts-safety 唯一出口）。

## 1. 内部结构

```text
src/power/
  slots.c      供电槽注册（→ ts-safety 通道，kind=TS_CH_POWER）
  budget.c     功率预算记账与上报
```

## 2. 供电槽（slots.c）

```c
typedef struct {
    const char *uid;            /* 如 "pwr0"；进 ts-safety 注册为 TS_CH_POWER 通道 */
    uint32_t current_limit_ma;  /* 硬限流（注册期冻结，合同 10） */
    bool     poweron_on;        /* 上电态是否供电（三安全态之一的字段） */
} ts_pwr_slot_t;

ts_res_t ts_power_register_slot(const ts_pwr_slot_t *s);          /* ts-periph 描述符驱动 */
ts_res_t ts_power_request(ts_ctx_t c, uint8_t slot, bool on, uint32_t ma);  /* ts-hal → 此处 */
```

- `ts_power_request` 流程：预算检查（§3）→ 构造 `ts_out_value_t{.pwr={on, ma}}` → **`ts_safety_commit(uid, v)`**——开关的物理生效只有这一条路（合同 2/7）；限流由 ts-safety 的 `limits.current_limit_ma` 兜底。
- 三安全态：poweron/linkloss/fault 的取值在注册描述符中声明（如 fault = 关断），缺省拒绝注册。

## 3. 功率预算（budget.c）

- 预算总额来自烧录配置（板级 provisioning，运行时只读）；记账 = 活跃槽 Σ(ma) 与预算比较。
- 超预算：新请求 → `TS_E_RANGE`；既有槽不受影响（不在线降额，行为可预测）。
- 上报：预算/用量/峰值入遥测周期快照（LLD-ts-net §5）；超预算拒绝事件外发（`TS_EVT_POWER_BUDGET`）。

## 4. native_sim 桩

- 桩驱动（ts-safety driver_dispatch 的 POWER 项）记录开关/电流轨迹 → L4 重放比对；模拟"过流"注入用于限流路径测试。

## 5. Kconfig（节选）

| 项 | 默认〔Q-10〕 | 说明 |
|---|---|---|
| CONFIG_TS_POWER_MAX_SLOTS | 4 | 供电槽数量上限 |

## 6. 测试要点

- L1：预算记账数学（边界：恰好等于/超 1mA）；限流拒绝。
- L2：断链→供电槽进 linkloss 态（按声明值）；恢复。
- L4：开关轨迹 + 预算遥测序列 golden。

## 7. 未决依赖

- Q-09（slot/分区布局中供电参数区）、Q-10（槽容量）。

## 修订记录

- v0.1 · 2026-09-20：首版草案。
