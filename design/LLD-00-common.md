# LLD-00 · 公共约定（跨模块）v0.1 草案

> **状态**：v0.1 草案，随 LLD 批次待 owner review。上位文档：`design/HLD-firmware-framework.md`（下称 HLD）。
> **用途**：所有 ts-* 模块 LLD 共享的错误码/时间/上下文/线程/命名/Kconfig 约定；本文是唯一出处，各模块 LLD 只引用不复写。
> **未决承载**：标注〔Q-xx〕处为待裁值；本文新增默认值统一入 **Q-10**（LLD 批次默认值清单，`decisions.md`）。

## 1. 目录与文件布局（west 工作区外的仓库内源，M0 经 manifest 挂载）

```text
firmware/
  app/                    板级应用（选择启用的 ts 模块、板配置）
  module/tessera/         框架 Zephyr 模块
    module.yml  Kconfig  CMakeLists.txt
    include/ts/           公共 API 头（core.h safety.h hal.h appmgr.h net.h power.h periph.h err.h）
    src/{core,safety,hal,appmgr,net,power,periph}/
  tests/                  系统级与重放测试（twister 用例）
```

- 依赖方向（coding.md §2）：app→tessera 公共头；模块间只经公共头；反向引用 = CI 失败。

## 2. 错误码（include/ts/err.h）

```c
typedef int32_t ts_res_t;                 /* TS_OK=0；负数为错误 */
#define TS_OK                0
#define TS_E_PARAM          -1   /* 非法参数/描述符缺字段 */
#define TS_E_NOMEM          -2
#define TS_E_PERM           -3   /* 权限拒绝（合同10：留痕） */
#define TS_E_STATE          -4   /* 状态机/生命周期拒绝 */
#define TS_E_BUSY           -5
#define TS_E_TIMEOUT        -6
#define TS_E_NOTFOUND       -7   /* 通道/外设/APP 不存在 */
#define TS_E_IO             -8   /* 驱动/存储失败 */
#define TS_E_INVALID_SIG    -9   /* 包验签失败 */
#define TS_E_ROLLBACK_LIMIT -10  /* 回滚计数超限 */
#define TS_E_UNINIT        -11
#define TS_E_RANGE         -12   /* 限幅/slew/预算拒绝（输出被安全层拦截） */
```

- 只增不复用；模块不得私造错误码（新增走本文修订 + review 门 ③）。

### 2.1 故障原因码 TS_FAIL_*（DR-09 补）

```c
/* u32 reason：高 16 位 = 来源（TS_FAIL_SRC_*），低 16 位 = 细因（来源模块自定义） */
#define TS_FAIL_SRC_BOOT   0x0001U   /* 细因 = 失败的 boot 步骤 idx */
#define TS_FAIL_SRC_WDT    0x0002U   /* 细因 = ts_wdt_src_t */
#define TS_FAIL_SRC_SAFETY 0x0003U   /* 细因 = ts-safety 自定义 */
#define TS_FAIL_SRC_STORE  0x0004U   /* 细因 = ts-store 错误细分 */
```

- 用于 `ts_safety_system_fail(reason)`、noinit 留痕与复位后诊断；不得挪用为通用 API 返回值。

## 3. 时间与上下文

- 唯一时间源：`uint64_t ts_time_ms(void)`（[any]，单调；ts-core LLD §3）。
- 每个 API 注明**允许上下文**：`[thread]`（线程）/ `[ISR]`（中断）/ `[any]`；`[thread]` API 禁在中断调用（断言拦截）。
- ISR 路径禁分配/禁队列/禁锁（estop 机械检查，testing.md §3.5）。

### 3.1 调用者上下文 ts_ctx_t（DR-10 补）

```c
typedef struct ts_ctx_opaque ts_ctx_t;   /* 不透明句柄；由 ts-appmgr 每 APP 实例化并注入 */
```

- ts-hal/ts-power 全部 API 以其为第一参数；实现侧经它反查权限表与 app_id。**防伪造边界**：wasm 侧只能见到整数 id（导入函数签名），id→上下文映射表在原生侧且不可被 APP 寻址。

## 4. 线程模型（全系统线程清单——唯一出处）

| 线程 | 优先级（Zephyr 抢占式，小=高）〔Q-10 提案〕 | 栈〔Q-10〕 | 职责 |
|---|---|---|---|
| （无线程）estop | GPIO IRQ 直达 | — | ts-safety force（合同5） |
| sysworkq（Zephyr 系统工作队列） | 3 | 2048B | ts-core 周期服务（WDT 巡检/事件分发） |
| ts_net_thread | 5 | 4096B | zenoh 会话/收发/心跳监视 |
| ts_app_*（每 APP 一线程） | 8 | manifest 声明（上限 Q-10） | WAMR 执行 |
| main（init 后转监督） | 10 | 板级配置 | 初始化编排、空转监督 |

- 抢占式优先级均为 Q-10 提案值；禁止协作式长占（确定性 + 响应上界）。
- 输入采集（ts-hal）与存储服务（ts-store）**无独立线程**——sysworkq 周期工作项（DR-01/02）。

## 5. 命名与 Kconfig

- 公共符号 `ts_<模块>_<动作>`；错误码 `TS_E_*`；事件 `TS_EVT_*`；Kconfig 前缀 `CONFIG_TS_*`。
- 新跨文件符号先查/登记 `docs/names.md`（军规 6）。

## 6. 常量出处标注法（coding.md §4 的 LLD 形态）

- LLD 中每个默认值标注 `〔Q-xx 提案 n〕` 或 `〔DEC-xx〕`；无标注的数值 = 纯结构性（如数组维度由逻辑决定）。
- 实现落地时转为 C 注释 `/* 来源: Q-xx */`（L5 机械检查）。

## 修订记录

- v0.1 · 2026-09-20：首版（错误码/线程模型/布局/命名约定；Q-10 登记项随 LLD 批次）。
- v0.2 · 2026-09-20：review-01 修复——§2.1 TS_FAIL_* 原因码（DR-09）、§3.1 ts_ctx_t（DR-10）、线程表补注（DR-01/02）。
