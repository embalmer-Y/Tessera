# HLD · Tessera 固件框架 v0.1（草案，待 owner 确认）

> **状态**：v0.2 草案（2026-09-20 经 design review-01 深化：新增 ts-store 模块、输入遥测、sys 命令面、断链恢复语义、关键场景时序、内存预算、V1 裁剪清单——DR-01…17 处置见 `design-review-01.md`）。依流程 §2.4 须 owner 确认后方可进入 impl；配套待裁批次 **Q-03…Q-11**（见 `decisions.md`），本文所有标注〔Q-xx〕处均为未裁默认值/选型，**不得先于裁决进入代码**（军规 2）。
> **输入**：DEC-01…18（`decisions.md`）、安全与确定性合同（`AGENTS.md` §6）、R1/R2 调研 v0.2（`docs/research/`）。
> **范围**：V1 固件框架（DEC-15 第一阶段；目标平台 native_sim，DEC-13/14）。Agent/模拟器（第二阶段）与硬件定型（第三阶段）不在本文；仅定义与 Agent 的接口契约。

## 1. 范围与目标

- **V1 交付物**：在 native_sim 上可运行、可测试的固件框架：安全层、HAL、APP 运行时（WAMR）、数据面（zenoh-pico）、受控供电（桩）、可插拔外设描述层（桩）。
- **V1 明确不做**（裁剪清单）：逻辑节点（多立方体并联）实现——仅命名空间与接口预留〔Q-07〕；真机四板移植（M3 后按 DEC-15 另列）；真机在环测试；**APP 业务状态持久化**（升级/回滚后状态丢弃，DR-15）；**审计留痕落盘**（V1 = 内存环形 + sys:get-audit 导出，掉电丢失，DR-07）；输入遥测为轮询变化上报（无硬件中断驱动，DR-02）。
- **验收基线**：DEC-13 模拟深度（native_sim + 外设桩全链路）+ 安全合同十条全部有对应机制与机械检查（`docs/std/testing.md`）。

## 2. 架构总览

```text
┌──────────────────────────────────────────────────────┐
│  APP 层：WASM 模块（WAMR 实例，沙箱内）                │  ← DEC-04/05/17
│    仅经 ts_* 导入函数访问框架；APP 间仅经框架消息通道    │
├──────────────────────────────────────────────────────┤
│  服务层                                               │
│  ts-appmgr  APP 生命周期：包接收/验签/版本/回滚 + WAMR 宿主│
│  ts-hal     统一外设 API（权限执行点）+ 外设描述         │
│  ts-net     zenoh-pico 封装：命名空间/命令-回执/心跳监视  │  ← DEC-18
│  ts-power   受控供电（软件开关/限流/功率预算，视同输出）  │  ← DEC-03
├──────────────────────────────────────────────────────┤
│  安全层 ts-safety（唯一写路径出口）                     │
│    输出保护（限幅/slew/限流）· 三安全态状态机 · estop ·  │  ← 合同 1/2/5/8
│    fail-safe 管线 · 看门狗框架                          │
├──────────────────────────────────────────────────────┤
│  框架核心 ts-core                                      │
│    初始化编排（固定顺序）· 事件总线 · 单调时间服务        │  ← 合同 6/9
├──────────────────────────────────────────────────────┤
│  Zephyr：设备驱动 / Devicetree / 网络 / 存储 / WDT      │
└──────────────────────────────────────────────────────┘
```

**数据流向铁律**（合同 2）：APP 的任何输出意图 → `ts-hal`（权限检查）→ `ts-safety`（保护校验）→ Zephyr 驱动。反向无此约束（输入流不因保护中断，合同 3）。ts-power 的供电输出走同一条 ts-safety 出口（合同 7）。

## 3. 模块分解（模块名已登记 `docs/names.md`，均为 HLD 提案态）

| 模块 | 职责 | 关键合同关联 | 主测试面 |
|---|---|---|---|
| ts-core | 初始化编排、事件总线、单调时间、喂狗注册表 | 合同 6/9 | L1/L4 |
| ts-safety | 输出保护层、三安全态状态机、estop ISR、fail-safe、WDT 框架 | 合同 1/2/4/5/6/8 | L1/L4/L5 |
| ts-hal | 面向 APP 的外设 API、外设描述符（可插拔）、权限执行点 | 合同 2/10 | L1/L2/L5 |
| ts-appmgr | APP 包接收/验签/存储/版本/回滚、WAMR 宿主、manifest→导入面装配 | DEC-04/05/17；合同 10 | L2/L4/L5 |
| ts-net | zenoh-pico 会话、命名空间、命令-回执、心跳监视（断链判定） | DEC-06/18；合同 3 | L2/L3/L4 |
| ts-power | 受控供电开关/限流/功率预算上报（经 ts-safety 落驱动） | DEC-03；合同 7 | L1/L2 |
| ts-periph | 外设描述与插拔管理（V1 = native_sim 桩外设） | DEC-14；DEC-02 预留 | L1/L3 |
| ts-store | 存储抽象：分区布局 / 掉电安全 meta / 只读 provisioning / noinit 留痕（DR-01） | DEC-05/07；合同 10 | L1/L2 |

### 3.1 ts-core

- 初始化编排器：按 §4.4 顺序表逐步拉起；任一步失败 → 全系统 fail-safe 并停机（不回退半启动）。
- 事件总线：发布/订阅，静态注册表（禁动态注册，确定性）；estop 等事件**事后补发**于此（合同 5）。
- 单调时间服务：唯一时间源（`ts_time_ms()`，单调钟）；墙钟只作数据不作控制（合同 9）。
- 喂狗注册表：每子系统一个 feed 源（含 owner 与周期），WDT 超时报告携带最后 feed 时间 → 可定位卡死来源（合同 4）。

### 3.2 ts-safety（权限与安全的强制点）

- **通道注册**：每个输出通道注册时必须声明三安全态取值 `{poweron, linkloss, fault}`——无声明拒绝注册（运行时断言 + 静态扫描，合同 1）。
- **唯一写路径出口** `ts_safety_commit()`：限幅 → slew-rate → 限流（供电）逐级校验后落驱动；所有 Zephyr 输出驱动调用（gpio/pwm/…）**只允许出现在本模块**（CI 机械检查，`docs/std/testing.md` L5）。
- **estop**：专用 GPIO 中断 → ISR 内直接调用 `ts_safety_force_all(SAFE_FAULT)`——不排队、不分配、不经协议栈（合同 5）；ISR 返回后经事件总线补发 `TS_EVT_ESTOP`。
- **fail-safe 管线**：接收 ts-net 断链通知 / WDT 超时 / 任一子系统故障报告 → 按通道状态机转移（§4.2）。
- **不学习**：安全参数（限值/限流/slew/三态取值）只来自构建期配置与烧录期安全参数区，运行时只读（合同 10）。

### 3.3 ts-hal

- 外设类 API（V1）：`gpio`（读/写）、`pwm`、`adc`（输入）、`counter`、`power`（经 ts-power）。接口为板无关抽象（DEC-04：APP 不见具体硬件）。
- **权限执行点**：每个 ts-hal 调用携带调用者 APP 上下文；对照 manifest 能力裁决，越权 → 拒绝 + 留痕（合同 10）。
- 外设描述符（ts-periph 配合）：可插拔外设 = 描述符（类/实例/能力/安全参数）注册进框架；未注册外设不可寻址。
- **输入采集（input monitor，DR-02）**：sysworkq 周期轮询输入实例（gpio-in / adc），值变化 → 发 `TS_EVT_INPUT_CHANGED` 并经 ts-net 发布遥测（周期〔Q-10 #14〕；V1 无硬件中断驱动）。

### 3.4 ts-appmgr（DEC-05/17 落地）

- 包格式〔Q-05 提案〕：`wasm 模块 + manifest(CBOR) + COSE-Sign1(ed25519) 签名`单文件容器；manifest 含版本、最低框架版本、能力清单。
- 验签：根公钥在安全参数区（烧录期写入）；验签失败 → 拒装 + 留痕。
- 存储〔Q-09 提案〕：双 APP slot（a/b）+ meta 区（当前版本指针、回滚计数）；A/B 切换保证回滚原子性。
- 加载：WAMR 实例化时按 manifest 能力**子集注册** `ts_*` 导入函数（白名单式绑定 = 权限硬边界，DEC-04/合同 10）；WASI 全集默认关〔Q-06 提案〕。
- 健康探针：框架周期 ping APP 导出的 `app_health_ping`；超时 → 卸载 + 回滚 + 计数；计数超限 → 拒载该版本并留痕（防回滚循环）。
- APP 间通信：`ts_msg_send(recv_app, payload)` 经框架路由（key 前缀 `app/<appid>/**` 隔离）；禁止任何直接互访（DEC-04）。

### 3.5 ts-net（DEC-18 落地）

- 端点角色〔DEC-20〕：V1 = zenoh **client** 连宿主侧 zenohd router（Windows/Linux PC 或 ARM64 Linux 工业/机器人主板；UDP/TCP 单播 + TLS，`Z_FEATURE_LINK_TLS` 显式开启）。
- **命名空间草案**（随本文过门 ③）：

```text
tessera/<node>/<cube>/<class>/<instance>/<action>
  node   逻辑节点 ID（V1 单立方体 = cube ID；DEC-02 预留层）
  cube   立方体 ID（出厂烧录）
  class  gpio | pwm | adc | power | app | sys
  action telemetry | event | cmd | hb
命令：zenoh query 打到 .../cmd/**，响应 = 回执 {status, data}（超时/重试在 Agent 侧）
遥测/事件：put/pub 到 .../telemetry、.../event
心跳：cube 周期 pub .../hb；host 周期 pub .../sys/hb-host（双向）
```

- **心跳监视（断链判定）**〔DEC-22：参数**部署期可配（prov）**；出厂默认间隔 1000ms、阈值 6、检测上界 ≈6s（考虑超长物理链路），WDT 独立 10s；M3 长链路场景标定〕：逾期 → 通知 ts-safety → 全输出进断链态（本地决策，不发网络确认）；输入流继续。
- **断链恢复语义（DR-04）**：恢复仅解除写入封锁，输出不自动回写——防恢复瞬间意外动作（详见 §4.2）。
- **sys 命令面（v1，DR-03；授权模型〔Q-11①〕）**：`get-info / get-link / get-safety / get-budget / get-audit / set-time / estop-clear`——**host-only**（APP 能力文法不可达），estop-clear 需确认令牌；细见 LLD-ts-net §4。
- 密钥/证书：烧录期安全参数区；运行时不改（合同 10）。

### 3.6 ts-power / ts-periph

- ts-power：供电槽 = 特殊输出通道（三安全态必声明）；软件开关、限流（ts-safety 执行）、功率预算上报（遥测）。V1 在 native_sim 以桩实现语义。
- ts-periph：外设描述符管理 + 插拔事件（V1 桩）；为 DEC-02 跨立方体编址预留间接层（资源 ID ≠ 本地硬件地址）。

## 4. 安全架构（合同逐条映射）

### 4.1 合同 → 机制 → 检查对照表

| 合同 | 机制（本文） | 机械检查（testing.md L5） |
|---|---|---|
| 1 三安全态 | §4.2 状态机 + 注册强制声明 | 注册完备性扫描 |
| 2 写入路径唯一 | §2 铁律 + `ts_safety_commit` 唯一出口 | 驱动调用白名单扫描 |
| 3 断链 fail-safe | ts-net 心跳监视 → ts-safety；输入流独立 | L4 重放断链场景 |
| 4 看门狗 | ts-core 喂狗注册表 + WDT | feed 记录断言 |
| 5 estop | §3.2 ISR 直达 | estop 路径静态检查（禁队列/分配） |
| 6 初始化固定 | §4.4 顺序表 + 失败即停 | init 测试（注入逐步失败） |
| 7 受控供电 | ts-power 经同一出口 | 同 2 |
| 8 并联安全归属 | 本地决策（断链/estop 不依赖节点内通信） | 设计审查 + L4 |
| 9 确定性 | 单调钟、静态注册、禁未播种随机 | 禁用模式扫描 + L4 重放 |
| 10 固件不学习 | 安全参数只读 + manifest 硬边界 | 参数写入点扫描（仅烧录通道） |

### 4.2 通道三安全态状态机

```text
上电 → SAFE_POWERON（所有通道，初始化前即达，estop GPIO 最先配置）
注册+链路确立 → ACTIVE
断链判定成立 → SAFE_LINKLOSS ；链路恢复 → ACTIVE（仅解除写封锁，**不自动回写断链前值**——须显式重设，DR-04）
estop / WDT / 故障 → SAFE_FAULT（estop 后须人工/显式命令复位）
```

### 4.3 看门狗拓扑

硬件 WDT 一只（超时初值〔Q-08 联动提案 5s〕）；软件喂狗注册表按子系统独立 feed；WDT 复位前的报告区写入最后 feed 时间戳（复位后留痕可查）。

### 4.4 初始化顺序（固定；任一步失败 → 全系统 fail-safe 停机）

1. estop GPIO 配置（最早的输出抑制路径就绪）
2. 全输出通道进 SAFE_POWERON（驱动直达）
3. WDT 启动
4. ts-core（时间/事件总线/喂狗表）
5. ts-periph / ts-hal（外设描述符注册）
6. 存储（APP slot/meta 读取）
7. ts-net（zenoh 会话建立、心跳监视启动；未连接 → 维持断链态）
8. ts-appmgr（按已装清单加载 APP；APP 故障 → 卸载回滚，**不阻塞系统启动**）
9. 系统进入运行态（输出仍按链路状态机管理）

### 4.5 关键场景端到端时序（设计基线；标"实测定"处为 M1/M3 验收项）

- **S1 estop**：GPIO 沿 → IRQ → `ts_safety_force_all_fault()`（置原子标志 + 逐通道直写 fault 值；上界目标 < 1ms，实测定）→ ISR 返回后 sysworkq 补发 `TS_EVT_ESTOP` → 事件外发（事后补发，合同 5）。
- **S2 断链 fail-safe**：host 心跳丢失计数达阈值（出厂默认 1000ms×6，DEC-22 prov 可配）→ `ts_safety_set_link(false)`（sysworkq 串行迁移）→ 全通道 SAFE_LINKLOSS（声明值落驱动）；输入/遥测继续。恢复：连续 2 周期〔Q-10 #12〕→ `set_link(true)` → 解除写封锁（不回写，DR-04）。
- **S3 APP 升级与回滚**：收包 → 验签（ed25519）→ 写 inactive slot + 回读校验 → meta 原子切换（ts-store）→ 下一加载周期卸旧载新 → 健康探针 3×1s 失败 → 回滚切回 + 计数；计数 > 3 → QUARANTINED。
- **S4 命令往返**：Agent query `…/cmd` → ts_net_thread 解析 CBOR → 命令分发表 →（host 命令走 sys 面）→ `ts_safety_commit`（限幅/slew/限流）→ driver_dispatch → 回执 `{status, data}`；命令超时上界 < 断链检测上界（Q-08）。

### 4.6 内存预算（提案〔Q-11⑥〕；实测后按行修订，不另开 Q）

约束板 = RP2350（SRAM 520KB，最小目标板）。RAM 分解：

| 区块 | 预算 | 依据 |
|---|---|---|
| Zephyr 内核 + 网络栈 + mbedTLS | 96KB | 栈与缓冲估算（Q-10 #2） |
| zenoh-pico | 32KB | R2 v0.2 量级，实测待 |
| ts 框架静态（通道表/审计环/事件表/perm 表） | 24KB | 容量 × 描述符尺寸（Q-10 #6/#7） |
| WAMR fast 解释器运行时 | 24KB | R1 v0.2 体积量级 |
| APP 实例 4 ×（堆 64KB + 栈 8KB） | 288KB | Q-10 #10 |
| 余量 | ≥56KB | — |

Flash（按板可配，联动 Q-09）：bootloader 64KB ｜ 固件 slot ×2 ｜ APP slot ×2 ｜ prov/meta/noinit 64KB；四板外置/内嵌 flash 量级均宽裕，尺寸表随 M2 板级配置定。

## 5. 可测试性设计（细则见 `docs/std/testing.md`）

- native_sim 主平台：全模块在仿真上可运行；WDT/estop/供电均有仿真桩。
- 外设桩：ts-periph 提供 fake 外设描述符（DEC-13 数字孪生-lite 的固件侧挂点；Agent 侧模拟器第二阶段对接）。
- 重放框架：输入序列文件 → 系统执行 → 输出序列逐位比对（合同 9；时间注入用虚拟时钟）。
- 机械检查五项（CI 强制）：唯一写路径、三态注册完备、禁用模式、常量出处、estop 路径。
- 审计/留痕导出：`sys:get-audit` 命令（合规观测点，DR-07）；输入变化进入遥测重放面（DR-02）。

## 6. 未决问题索引（全文见 `decisions.md`）

> 2026-09-20 裁决批次 1：Q-03/Q-04/Q-05/Q-08/Q-09/Q-12 已裁 → DEC-19…24（正文相关值已同步 DEC 语义）；仍待裁：Q-06/Q-07（已补通俗解释）、Q-10、Q-11。

| Q | 主题 | 本文建议 |
|---|---|---|
| Q-03 | Zephyr 目标版本 | 4.4（2026-04，最新 stable） |
| Q-04 | zenoh 拓扑与传输 | V1 client→PC router，UDP/TCP 单播+TLS |
| Q-05 | APP 包格式与签名 | wasm+CBOR manifest+COSE/ed25519 单文件 |
| Q-06 | WAMR 执行模式 | fast 解释器起步，WASI 关，AOT 预留 |
| Q-07 | 逻辑节点 V1 范围 | 仅命名空间/接口预留，不实现并联 |
| Q-08 | 断链判定参数 | 500ms×4 ≈2s 上界；WDT 5s（M3 实测校准） |
| Q-09 | 存储分区与 OTA | 双 APP slot+meta；MCUmgr/UART 底线 |
| Q-11 | review-01 语义批次：sys 命令面授权 / 共享写语义 / APP 状态不持久化 / 审计 V1 简化 / prov 模型 / 内存预算分配 | 全部按 review-01 提案 |

## 7. 里程碑分解（退出均须 owner review）

| 里程碑 | 内容 | 退出条件（DoD） |
|---|---|---|
| M0 | west 工作区 + native_sim 空模块 + CI 骨架（twister+pytest） | CI 绿；机械检查脚本骨架上线 |
| M1 | ts-core + ts-safety（状态机/estop 桩/WDT/唯一写路径） | L5 机械检查全过；L4 断链/estop 重放绿；覆盖率达门槛 |
| M2 | ts-hal + ts-appmgr + WAMR（样例 wasm APP 全生命周期） | 安装→运行→升级→回滚链路测试绿；越权访问拒绝并留痕 |
| M3 | ts-net + ts-power + ts-periph 桩 + 系统集成 | DEC-13 全链路演示：native_sim 上 Agent 命令→回执→遥测；断链 fail-safe 实测报告 |

## 8. 修订记录

- v0.1 · 2026-09-19：首版草案（design 阶段产出，待 owner 确认 + Q-03…Q-09 裁决）。
- v0.2 · 2026-09-20：design review-01 深化——新增 ts-store 模块行、§4.5 关键场景时序、§4.6 内存预算、sys 命令面、输入采集、断链恢复语义、V1 裁剪清单（DR-01…17 处置）。
