# LLD · ts-hal v0.1 草案

> **状态**：v0.1 草案，随 LLD 批次待 owner review。上位：HLD §3.3；公共约定 `LLD-00-common.md`。
> **职责**：面向 APP 的板无关外设 API（gpio/pwm/adc/power）、**权限执行点**（manifest 能力 → 每调用裁决）、外设实例寻址。
> **合同关联**：合同 2（输出必经 ts-safety）、3（输入不受保护影响）、10（越权拒绝 + 留痕）。

## 1. 内部结构

```text
src/hal/
  api.c        ts_api_v1 导入面（WAMR native 符号表，ts-appmgr 按能力过滤装配）
  perm.c       能力文法解析 + 调用者裁决
  registry.c   实例注册（由 ts-periph 描述符喂入）
  input.c      输入周期采集与变化上报（input monitor，DR-02）
```

## 2. 能力文法 ts_perm_v1（manifest 声明，随 Q-05 裁决定稿）

```text
capability  = class ":" op ":" instances
class       = "gpio" | "pwm" | "adc" | "power" | "fs" | "av" | "msg" | "sys"
op          = "read" | "write" | "set" | "list" | "delete"
instances   = range | name          ; range = a["-"b] | a","… ; name = app_id（msg）
示例：gpio:write:0-3   adc:read:0,2   power:set:1   fs:read:0   av:read:0   msg:send:com.example.b   sys:read:time
```

- **fs/av 类（DEC-47⑤）**：fs 的 op ∈ {list, read, write, delete}（inst 占位 0）+ 路径授权走 manifest `fs_paths` 前缀白名单字段（双层裁决，见 §3）；av 的 op = read（inst 0 = 摄像头；采集与流发布同门）。

- 文法版本化（`ts_perm_v1`）；解析在**加载期**完成（非法 → 拒装，TS_E_PARAM），运行期只查位图/区间表。
- 能力→实例映射成 `ts_perm_table_t`（位图 + 名单），实例号在加载期冻结。

## 3. API 面（ts_api_v1，APP 可见的全部导入符号）

```c
/* 所有函数第一参数 ctx = 调用者上下文（ts-appmgr 注入），APP 代码不可伪造 */
ts_res_t ts_gpio_write(ts_ctx_t c, uint8_t inst, bool v);      /* → perm 裁决 → ts_safety_commit */
ts_res_t ts_gpio_read (ts_ctx_t c, uint8_t inst, bool *out);   /* 输入直读驱动（合同3） */
ts_res_t ts_pwm_set   (ts_ctx_t c, uint8_t inst, uint32_t hz, uint16_t permille);
ts_res_t ts_adc_read  (ts_ctx_t c, uint8_t inst, int32_t *mv);
ts_res_t ts_power_set (ts_ctx_t c, uint8_t slot, bool en);     /* 经 ts-power → ts-safety */
uint64_t ts_time_ms_api(ts_ctx_t c);                           /* 单调钟（合同9） */
ts_res_t ts_log_write (ts_ctx_t c, uint8_t lvl, const char *msg, uint32_t len);
ts_res_t ts_msg_send  (ts_ctx_t c, const char *to_app, const void *buf, uint32_t len); /* APP间唯一通道 */
/* ts-fs 能力面（DEC-47④⑤，MD1.2e）：无句柄四函数；路径授权 = manifest fs_paths
 * 前缀白名单（加载期 ts_fs_paths_bind 绑定；前缀边界 = 后须 '/' 或恰好等长；
 * 未绑定/不匹配 = TS_E_PERM fail-closed）。后端 = Zephyr fs（V1 挂载 FAT）。 */
ts_res_t ts_fs_list  (ts_ctx_t c, const char *dir, char *out, uint16_t cap, uint16_t *out_len);
ts_res_t ts_fs_read  (ts_ctx_t c, const char *path, uint32_t off, uint8_t *buf, uint16_t *len);
ts_res_t ts_fs_write (ts_ctx_t c, const char *path, uint32_t off, const uint8_t *data, uint16_t len);
ts_res_t ts_fs_delete(ts_ctx_t c, const char *path);
/* ts-av 能力面（DEC-47③⑥，MD1.2g）：读类（合同 3 输入面——不经安全提交层）。
 * 格式/分辨率经 manifest av_fmt/av_w/av_h 声明 → 加载期 ts_av_config_bind 绑定
 * （未声明 = TS_E_STATE fail-closed）；摄像头 = chosen zephyr,camera 官方池路径。 */
ts_res_t ts_av_capture(ts_ctx_t c, uint8_t *buf, uint32_t cap, uint32_t *len); /* 阻塞取一帧（帧 > cap = TS_E_RANGE） */
ts_res_t ts_av_publish(ts_ctx_t c, uint32_t fid, uint32_t cid, uint32_t n_chunks,
                       const uint8_t *data, uint32_t len); /* 分片发布 ≤1KB（DEC-47②）；打拍/重试在 ts-net avq（LLD-ts-net §5） */
```

- `ts_ctx_t`（所有函数第一参数）定义与防伪造边界见 LLD-00 §3.1（原生侧映射表，wasm 侧仅整数 id）。
- **输出路径**：写类 API 全部收敛到 `ts_safety_commit`（本模块**零**直接驱动调用——L5 白名单外即违规；L5 检查的输出驱动面 = gpio_pin_set/pwm_set 族）。
- **权限裁决**（perm.c）：实例不在能力表 → `TS_E_PERM` + `TS_EVT_PERM_DENIED`（调用者 app_id/类/实例/时刻，合同 10 留痕）；裁决在 ts_app 线程上下文同步完成（无锁查只读表，确定性）。
- 版本策略：符号集变更 = `ts_api_v2` 并行注册，不原地改语义（门 ③ + fw semver X 位）。
- **PWM 打包域界限（v0.2.2，板级九）**：`ts_pwm_set` 的 hz 打包 = hz/100 → **合法域 [100, 6553500] Hz**（api 层显式拒绝；V1 桩曾静默接受 hz<100，真 PWM 后端按 hz 求周期后收紧）。
- **ADC 真后端（v0.2.2，板级九）**：`CONFIG_TS_DRV_ADC=y` + zephyr,user（adc-uid + io-channels）→ `ts_adc_read` 真读：12bit / 内部基准 / 12dB 衰减（ADC_GAIN_1_4 最宽量程）；mV = Zephyr 通用换算（1100mV 基准口径——esp32 驱动已将 raw 预补偿：eFuse 校准 + 衰减反归一）；读失败如实 `TS_E_IO`；uid 不匹配/未 init = 桩通道（0mV，L4/sim 连续性）。init = `ts_adc_drv_init()`（boot/bench 显式调用）。**输入直读不经保护层（合同 3）——adc 驱动调用属输入面，不在 L5 输出写路径辖内**。真机：GPIO2 轨到轨注入 0mV / 3122mV（3.3V 饱和，docs/board-periph-01.md PB6/7）。

## 4. 实例注册（registry.c）

```c
ts_res_t ts_hal_register_class(const ts_periph_desc_t *desc);  /* ts-periph 调用；分配实例号并绑定 uid */
```

- 实例号 = 某 class 内的稳定序号（由描述符顺序决定，构建期可复现）；uid→实例映射表供 ts-net 命名空间寻址（`tessera/<node>/<cube>/gpio/<inst>`）。

## 5. 输入采集 input monitor（DR-02，v0.2 新增）

- 执行体：sysworkq 周期工作项（无独立线程，LLD-00 §4 注）；周期 `CONFIG_TS_HAL_INPUT_POLL_MS`〔DEC-27 #14： 100ms〕。
- 流程：遍历输入实例（gpio-in/adc）→ 读驱动 → 与上次值比较 → 变化则：发布 `TS_EVT_INPUT_CHANGED`（uid + 旧/新值 + 时间戳）+ 通知 ts-net 发布该实例遥测。
- 语义：**只观测不改值**（不影响任何控制路径）；断链期间照常采集并进审计面（合同 3"输入流不因保护而中断"的观测侧落点）。
- 去抖：V1 无（数值抖动 = 遥测抖动，可接受；如需 M2 评审加阈值）。

## 6. Kconfig（节选）

| 项 | 默认〔DEC-27〕 | 说明 |
|---|---|---|
| CONFIG_TS_HAL_MAX_INSTANCES | 24 | 各类实例总容量 |
| CONFIG_TS_HAL_INPUT_POLL_MS | 100 | 输入轮询周期（DR-02） |

## 7. 测试要点

- L1：文法解析全分支；越权裁决（含边界实例号）。
- L2：gpio 写 → 安全层拦截（限幅态）传播；adc 读不受断链影响。
- L4：越权留痕事件进入重放 golden。
- L5：本模块驱动调用扫描（期望零命中）。
- L2：input monitor 变化上报（输入序列 → 遥测/事件序列）。

## 8. 未决依赖

- DEC-21（manifest/TSAP）、DEC-27（实例容量）已裁；无未决。

## 修订记录

- v0.2.3 · 2026-10-07：MD1.2g（单元 A）——§2 文法补 fs/av 类（DEC-47⑤，fs 补记 MD1.2e）；§3 增 ts-av 面（ts_av_capture/ts_av_publish，读类 + av:read:0 门 + manifest av_fmt/av_w/av_h 绑定）；fs 四函数补记（MD1.2e 已实现未入册）。回归：twister 15/15（68 用例）/L5 6/6。
- v0.1 · 2026-09-20：首版草案。
- v0.2 · 2026-09-20：review-01 深化——新增 §5 input monitor（DR-02）、ts_ctx_t 指针（DR-10）。
- v0.2.1 · 2026-09-21：裁决同步——出处标注收敛为 DEC 编号（SC-02）。
- v0.2.2 · 2026-10-02：板级九——§3 增补：ts_pwm_set hz 下界 100Hz（打包粒度）；ADC 真后端（CONFIG_TS_DRV_ADC + zephyr,user 绑定；真机轨到轨验证留档 docs/board-periph-01.md）。
