# LLD · ts-core v0.1 草案

> **状态**：v0.1 草案，随 LLD 批次待 owner review。上位：HLD §3.1/§4.4；公共约定见 `LLD-00-common.md`（错误码/线程/上下文）。
> **职责**：初始化编排（固定顺序）、事件总线、单调时间服务、看门狗框架（喂狗注册表）。
> **合同关联**：合同 6（初始化顺序固定/失败即停）、合同 9（确定性时间源）、合同 4（看门狗可定位）。

## 1. 内部结构

```text
src/core/
  boot.c    初始化编排器（顺序表驱动）
  events.c  事件总线（静态注册表）
  time.c    单调时间 + 测试注入钩子
  wdt.c     喂狗注册表 + 巡检（sysworkq 周期项）
```

## 2. 初始化编排（boot.c）

```c
typedef ts_res_t (*ts_boot_step_fn)(void);
typedef struct { const char *name; ts_boot_step_fn fn; } ts_boot_step_t;
/* 顺序 = HLD §4.4：estop GPIO → 全通道 SAFE_POWERON → WDT 启动 → core →
   periph/hal → 存储 → net → appmgr → 运行态。顺序是规格，数组顺序不可调换。 */
extern const ts_boot_step_t ts_boot_steps[TS_BOOT_STEP_COUNT];
ts_noreturn void ts_core_boot(void);
```

- 任一步返回非 TS_OK → 调用 `ts_safety_system_fail(TS_FAIL_BOOT_<idx>)`（全输出进 SAFE_FAULT）后进入受控停机循环（喂狗停止 → 硬 WDT 兜底复位，复位原因留痕于 noinit 区——noinit 读写经 ts-store 接口，DR-01/17）。
- 每步执行前后发布 `TS_EVT_BOOT_STEP`（payload：idx/name/result）——重放测试的初始化观测点。

## 3. 单调时间（time.c）

```c
uint64_t ts_time_ms(void);                 /* [any] 唯一时间源（k_uptime_get 封装） */
void ts_time_test_bind(const ts_time_source_t *src);  /* 仅 CONFIG_TS_TEST 构建；L4 虚拟时钟注入 */
```

- 墙钟/RTC 读取在框架内**只允许**出现在 ts-net 的数据字段填充处，禁入控制路径（合同 9，L5 扫描）。

## 4. 事件总线（events.c）

```c
typedef enum {
    TS_EVT_BOOT_STEP, TS_EVT_BOOT_DONE,
    TS_EVT_ESTOP,                    /* 事后补发（合同5），estop 动作本身不经总线 */
    TS_EVT_NET_LINK_UP, TS_EVT_NET_LINK_DOWN,
    TS_EVT_SAFE_STATE_CHANGED,       /* payload: 通道 uid + 新态 */
    TS_EVT_APP_LOADED, TS_EVT_APP_UNLOADED, TS_EVT_APP_QUARANTINED,
    TS_EVT_PERIPH_ATTACH, TS_EVT_PERIPH_DETACH,
    TS_EVT_INPUT_CHANGED,            /* 输入值变化（ts-hal input monitor，DR-02） */
    TS_EVT_WDT_WARN, TS_EVT_POWER_BUDGET,
    TS_EVT_PERM_DENIED,              /* 合同10 越权留痕 */
} ts_evt_id_t;

typedef struct { ts_evt_id_t id; uint64_t t_ms; const void *data; size_t len; } ts_evt_t;

ts_res_t ts_evt_subscribe(ts_evt_id_t id, void (*fn)(const ts_evt_t *, void *), void *user); /* [thread] 仅 init 期 */
void ts_evt_publish(const ts_evt_t *e);   /* [thread] 同步分发；[ISR] 投递到深度〔Q-10 提案 16〕队列由 sysworkq 分发 */
```

- **确定性**：分发顺序 = 注册表静态顺序（禁运行期插队）；同一事件多次发布的间隔与内容进入重放记录。
- 订阅容量：每事件类型最大订阅数〔Q-10 提案 4〕；注册表满 → TS_E_NOMEM（启动期即暴露）。

## 5. 看门狗框架（wdt.c）

```c
typedef enum { TS_WDT_NET, TS_WDT_APPMGR, TS_WDT_SYWORK, TS_WDT_COUNT } ts_wdt_src_t;
ts_res_t ts_wdt_register(ts_wdt_src_t src, uint32_t period_ms);  /* init 期 */
void ts_wdt_feed(ts_wdt_src_t src);                              /* [any] 原子更新 last_feed */
```

- 硬件 WDT：单只，超时 = max(periods)×2 与〔DEC-22：10s〕取小〔Q-10 复核〕。
- 巡检：sysworkq 周期 = 最小 period/2；发现逾期 → 先 `TS_EVT_WDT_WARN`（带 src 与最后 feed 时间）→ `ts_safety_system_fail(TS_FAIL_WDT_<src>)` → 停喂硬 WDT（复位后 noinit 留痕可定位，合同 4）。
- native_sim：硬 WDT 用仿真桩（test 构建可注入逾期）。

## 6. Kconfig（节选）

| 项 | 默认〔Q-10〕 | 说明 |
|---|---|---|
| CONFIG_TS_CORE_EVT_QUEUE_DEPTH | 16 | ISR 投递队列深度 |
| CONFIG_TS_CORE_MAX_SUBS | 4 | 每事件类型订阅上限 |
| CONFIG_TS_TEST | n | 测试构建（时间注入/WDT 注入/RX 注入开） |

## 7. 测试要点（testing.md 映射）

- L1：boot 每步注错 → fail-safe 停机路径全覆盖；wdt 逾期判定数学。
- L4：init 序列重放（BOOT_STEP 事件序列 golden）；事件分发顺序稳定性。
- L5 挂点：`ts_time_ms` 唯一时间源（禁用模式扫描的白名单豁免点）。

## 8. 未决依赖

- DEC-22（WDT 周期）已裁；仍待 Q-10（队列深度/订阅数/优先级）。

## 修订记录

- v0.1 · 2026-09-20：首版草案。
- v0.2 · 2026-09-20：review-01——事件表补 TS_EVT_INPUT_CHANGED（DR-02）、noinit 依赖 ts-store（DR-17）。
