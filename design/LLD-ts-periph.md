# LLD · ts-periph v0.4（M3b 已实现）

> **状态**：v0.4（2026-09-25 impl-review-01 修复批：F-2 注册源静态表化 + F-1 插拔事件外发兑现 + F-5 已知限制登记；twister framework.periph 4 用例全绿）。上位：HLD §3.6；公共约定 `LLD-00-common.md`。
> **职责**：外设描述符管理与插拔事件、逻辑名→硬件资源绑定（可插拔外设的框架侧落点；DEC-02 跨立方体编址的间接层）。
> **合同关联**：合同 1/10（描述符携带三安全态与安全参数，注册期冻结）；DEC-14（板差异隔离于此层）。

## 1. 内部结构

```text
src/periph/
  desc.c       描述符表（构建期生成 + 运行期注册接口）
  hotplug.c    插拔事件（V1：仅事件与预留接口，native_sim 桩触发）
```

## 2. 描述符（desc.c）

```c
typedef struct {
    const char      *uid;      /* 逻辑名："gpio0"、"pwm1"、"pwr0"…（编址用，跨板稳定） */
    ts_periph_kind_t  kind;     /* TS_PK_GPIO / TS_PK_PWM / TS_PK_POWER / TS_PK_ADC（DR-13） */
    const void      *dt_spec;  /* Zephyr devicetree spec（板相关，构建期绑定） */
    ts_out_ch_t      safe;     /* 三安全态值 + limits（随描述符冻结，合同 10） */
} ts_periph_desc_t;

typedef enum { TS_PK_GPIO, TS_PK_PWM, TS_PK_POWER, TS_PK_ADC } ts_periph_kind_t;
/* DR-13：与 ts_ch_kind_t（仅输出通道）分离；TS_PK_ADC 只注册 ts-hal 输入侧，不进 ts-safety */

ts_res_t ts_periph_register(const ts_periph_desc_t *d);  /* init 步骤 5 批量执行 */
```

- **双名解耦**：uid（逻辑，进命名空间/权限/审计）与 dt_spec（物理，板相关）分离——换板只改 dt 绑定，uid 与 APP 权限不变（DEC-04 跨板迁移的落点）。
- 注册职责链：ts-periph（描述）→ ts-safety（输出通道）/ts-hal（实例寻址）→ ts-net（key 映射）。
- **生命周期契约（impl-review-01 F-2 定稿）**：`ts_periph_register` 将描述符**结构体拷入模块静态表**后再经表内存储注册下游（safety 通道注册表持指针——注册源必须是静态存储；此前直接注册调用方 `&d->safe`，栈上组装即悬垂，与 ts-power slots M3b 自检修复同类）——调用方**允许栈上组装结构体本身**；其**字符串字段**（uid/dt_spec/safe.uid 指向内容）须指向静态存储。回归测试 framework.periph test_04。
- **已知限制（impl-review-01 F-5 登记）**：注册链失败**无回滚**——末段 ts_hal_register_dev 失败时，已注册的 safety 通道/power 槽残留（无注销 API），同 uid 重试将永远撞名（需重启）。板级初始化为编译期静态声明 + 失败即全系统 fail-safe（合同 6），运行期无重试路径，实际影响低；引入动态注册（真机热插拔）时再议注销面（走门 ③）。
- 描述符来源：板级 overlay + 配置生成（构建期固化为主）；运行期注册接口保留给热插拔（V1 仅测试用）。

## 3. 插拔（hotplug.c，V1 范围裁剪）

- 事件：`TS_EVT_PERIPH_ATTACH/DETACH`（payload：uid/kind）——native_sim 测试可注入；真机检测（连接器感知）第三阶段硬件定型后补。
- DETACH 语义：通道进 SAFE_FAULT（物理不在场 = 故障态，输出拒绝）+ key 下线通告（事件外发——**ts-net pub.c 订阅兑现〔impl-review-01 F-1〕**：extra = `{"uid", "pkind"}`，按 uid 路由 `…/<uid>/event`，QoS = 尽力而为〔DEC-42 安全类集合之外的观测类〕）。
- DEC-02 预留：资源 ID 已是逻辑名，跨立方体编址在此层之上扩展（`<cube>:<uid>` 形态留待逻辑节点 HLD，Q-07）。

## 4. native_sim 外设桩（DEC-13 固件侧挂点）

```text
桩驱动（绑定到 dt_spec）：gpio/pwm/adc/power 四类 fake 设备
  - 写轨迹环形记录（供 L4 golden 比对）
  - 读值由测试脚本驱动（输入序列注入）
  - 与 Agent 侧模拟器（第二阶段）的对接面 = 本桩的注入/记录接口（test 构建）
```

## 5. Kconfig（节选）

| 项 | 默认〔DEC-27〕 | 说明 |
|---|---|---|
| CONFIG_TS_PERIPH_MAX_DESCS | 24 | 描述符容量（与 ts-hal 实例容量一致） |

## 6. 测试要点

- L1：注册职责链（缺三态/撞 uid 拒绝）；DETACH→SAFE_FAULT。
- L3：桩外设全类读写 + key 映射一致性（uid ↔ `tessera/.../<class>/<inst>`）。
- L4：插拔事件序列进 golden。

## 7. 未决依赖（M3b 后更新）

- **已实现（2026-09-25）**：desc.c（注册职责链：GPIO/PWM → safety 通道；POWER → ts-power 槽；ADC → 仅 ts-hal 输入侧〔DR-13〕）+ hotplug.c（ATTACH/DETACH 事件 payload = ts_periph_evt_t{uid,kind}；DETACH → 单通道 SAFE_FAULT，ATTACH → 上电态重放——机制面 = ts_safety_force_channel_fault/ts_safety_channel_recover 新公共 API）。
- Q-07（跨立方体编址预留）：uid 已是逻辑名，`<cube>:<uid>` 扩展留逻辑节点 HLD。

- Q-07（跨立方体编址预留边界）、Q-10（描述符容量）。

## 修订记录

- v0.4 · 2026-09-25：impl-review-01 修复批（F-1/F-2/F-5）——§2 注册源静态表化生命周期契约 + 已知限制（无回滚）登记；§3 插拔事件外发兑现说明（ts-net pub.c 订阅）。回归：framework.periph 4 用例（+test_04 栈描述符回归）全绿。
- v0.1 · 2026-09-20：首版草案。
- v0.2 · 2026-09-20：review-01——kind 枚举独立为 ts_periph_kind_t（含 ADC，DR-13）。
- v0.2.1 · 2026-09-21：裁决同步——出处标注收敛为 DEC 编号（SC-02）。
- v0.3 · 2026-09-25：M3b 实现批次——§7 落地状态；DETACH 机制面（safety 单通道 fault/recover API）与 safe.uid 单源校验定稿。
