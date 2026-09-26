# LLD · ts-power v0.2.1（M3b 已实现）

> **状态**：v0.2.1（2026-09-26 DEC-43：预算检查-提交原子化〔write_lock + commit_locked〕）。上位：HLD §3.6；公共约定 `LLD-00-common.md`。
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

- `ts_power_request` 流程：预算检查（§3）→ 构造 `ts_out_value_t{.pwr={on, ma}}` → **`ts_safety_commit(uid, v)`**——开关的物理生效只有这一条路（合同 2/7）；限流由 ts-safety 的 `limits.current_limit_ma` 兜底。**锁收口（DEC-43，v0.2.1）**：检查-提交原子化——全程持 `ts_safety_write_lock`，提交走 `ts_safety_commit_locked`（消除 TOCTOU：窗口实测 203ns〔Q-23 实验补充〕，真 SMP 板上可达）。
- 三安全态：poweron/linkloss/fault 的取值在注册描述符中声明（如 fault = 关断），缺省拒绝注册。

## 3. 功率预算（budget.c）

- 预算总额来自烧录配置（板级 provisioning，运行时只读）；记账 = 活跃槽 Σ(ma) 与预算比较。
- 超预算：新请求 → `TS_E_RANGE`；既有槽不受影响（不在线降额，行为可预测）。
- 上报：预算/用量/峰值入遥测周期快照（LLD-ts-net §5）；超预算拒绝事件外发（`TS_EVT_POWER_BUDGET`）。

## 4. native_sim 桩

- 桩驱动（ts-safety driver_dispatch 的 POWER 项）记录开关/电流轨迹 → L4 重放比对；模拟"过流"注入用于限流路径测试。

## 5. Kconfig（节选）

| 项 | 默认〔DEC-27〕 | 说明 |
|---|---|---|
| CONFIG_TS_POWER_MAX_SLOTS | 4 | 供电槽数量上限 |

## 6. 测试要点

- L1：预算记账数学（边界：恰好等于/超 1mA）；限流拒绝。
- L2：断链→供电槽进 linkloss 态（按声明值）；恢复。
- L4：开关轨迹 + 预算遥测序列 golden。

## 7. 未决依赖（M3b 后更新）

- **已实现（2026-09-25）**：slots.c + budget.c（src/power/）；预算总额 = prov `power_budget_ma` 只读（未加载/未配置 = 0 → 一切供电请求拒绝，缺省即安全侧）；记账 = 各槽 readback Σ（读回权威单源）；峰值跟踪；`TS_EVT_POWER_BUDGET` 超预算拒绝外发；`sys/get-budget` 实装；遥测 kind 97 预算快照（…/sys/power）。
- 实现细节定稿：组装通道描述符随槽记录静态存储（safety 注册表存指针）；`ts_power_request` 权限裁决 = TS_PERM_CLASS_POWER/SET；测试注入 `ts_power_test_set_budget`（prod 不可达）。

- DEC-23（分区布局）、DEC-27（槽容量）已裁；无未决。

## 修订记录

- v0.2.1 · 2026-09-26：DEC-43 锁收口——ts_power_request 检查-提交原子化（write_lock + commit_locked，TOCTOU 窗口 203ns 消除）；回归 framework.conc test_01 + 全量 13/13。
- v0.1 · 2026-09-20：首版草案。
- v0.1.1 · 2026-09-21：裁决同步——出处标注收敛（SC-02）。
- v0.2 · 2026-09-25：M3b 实现批次——§7 落地状态；prov 只读预算语义（缺省 0 = 安全侧）与静态存储细节定稿。
