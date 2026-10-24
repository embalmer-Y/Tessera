# LLD · ts-interact v0.2

> **本文件是什么**：ts-interact（本地交互终端）低层设计——V0.11.0 R5（DEC-65；需求源 = owner 2026-10-18「板卡最常见的是 UART……添加类似 linux 终端的交互 UART 终端」+ 同日扩意「日志/输出/终端同走 UART 一路」）。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.2（2026-10-18 R5-V 真机批：**单 UART 三合一真机点亮 + F3 终端确认/拒绝四判据 ALL PASS**——`uart:~$` 与日志行同 tty 复用〔1.9s prompt〕；deploy→PENDING→`ts confirm`→暖复位→`[tsi] confirm rc=0 app=… slot=…`→NVD DONE 全链 + `ts reject` 对称槽保留零复位（证据 r5v_verdicts_console.txt）。板级 DRAM 面定案：ZENOH_PICO_THREADS_NUM 4→2（pico 预分配 pthread 栈池 32KB→16KB——执行器单线程设计）+ SHELL_STACK 4096（2048 缺省装不下 confirm 链——EXCCAUSE 0 野跳真机定案）+ SYSTEM_WORKQUEUE_STACK_SIZE 4096（板缺省 1024 于 zenoh 建链窗溢出——SENTINEL 点名）+ STACK_SENTINEL=y。v0.1 设计批（DEC-65 按建议值）形态/信任级/命令集不变）。

## 1. 定位与形态

- **单 UART 承载三合一**：日志输出（log 子系统）+ 应用输出（printk 经 LOG_PRINTK 汇入）+ 交互终端（Zephyr shell ts 命令集）——Linux 串口终端同构形态（printk 与 getty 同 tty）；Zephyr 机制 = `SHELL` + `SHELL_BACKEND_SERIAL` + `SHELL_LOG_BACKEND`（日志行输出时保持输入行并重绘 prompt，编辑/历史内建——上游正牌路径，零补丁）。
- **载体**：uart0（CH343 三功能线——console/烧录/复位解耦纪律不变；esptool 烧录期终端让位，与现行 console 语义一致）。USJ 面保留为构建期备援（`zephyr,console` 可选回退，非默认）。
- **组件边界**：`src/interact/ts_interact.c` = **薄命令层**——命令处理 = 调既有框架入口（appmgr pending 族 / safety arb 族 / safety 本地清除），**零新安全面、零网络面**；核心逻辑函数（`ts_interact_*`）与 shell 运行时解耦（可 twister 直测），shell 命令表仅做打印。

## 2. 命令集（v1）

| 命令 | 框架挂点 | 语义（与既有本地路逐一对应） |
|---|---|---|
| `ts pending` | `ts_appmgr_pending_active/summary` | 挂起安装呈现（= LCD INSTALL PENDING 的文本态，EC3 单一事实源） |
| `ts confirm` | `ts_appmgr_confirm_pending()` | 安装确认（= BOOT 短按；meta 切换 + 暖复位随调用方约定） |
| `ts reject` | `ts_appmgr_reject_pending()` | 安装拒绝（= BOOT 长按 ≥2s；槽保留可重推） |
| `ts arb local/remote` | `ts_safety_set_arb()` | 席位切换（= BOOT 双短按；切换零输出语义不变） |
| `ts estop clear` | `ts_safety_clear_fault()` | 本地锁存释放（= F2 本地路；框架契约恒 TS_OK 幂等——无 fault = no-op 迁移） |
| `ts info` | prov/link/arb/pending/app 聚合只读 | 状态一览（模式/席位/链路/挂起/APP 态） |
| `ts log <off\|err\|wrn\|inf\|dbg>` | log filter | 日志详度调节 |

- 判据行纪律：命令回执统一 `[tsi] <cmd> rc=<n>` 前缀（机读可 grep；与 AK* 行族同约定）。
- 权限面：**无新增远程面**——shell 仅物理 UART 可达；信任级 = 物理在场代理（与 BOOT 键同源，DEC-65②）。confirm/reject 仅 pending 期有效（复用 appmgr 挂起态门，超时 fail-closed 不变）。

## 3. 日志/输出路由（atkbench 形态）

```
CONFIG_LOG=y + CONFIG_LOG_PRINTK=y   # printk（bench 判据行 + APP 日志）→ log 子系统
CONFIG_SHELL=y（SHELL_BACKEND_SERIAL 缺省 y）+ SHELL_LOG_BACKEND（随 LOG 默认 y）
CONFIG_CONSOLE=n                      # 关 console 子系统防双路重印（DT chosen 保留无副作用）
DT: zephyr,shell-uart = &uart0
```

- **判据行兼容**：bench 判据行（AK*/NVD/tsi）为日志行原样输出；驱动/watcher 按子串匹配不受 shell prompt 干扰（prompt 行不含判据子串）——`simreal_diff`/NVD/`nvd_acceptance --window` 口径零改动。
- **DRAM 预算**：shell 任务栈（CONFIG_SHELL_STACK_SIZE 调优）+ log MPSC 队列——atkbench 昨日余量 140B 基线上按实测增减重平（NET_MAX_CONTEXTS 富余可回收；build 溢出即调，纪律同前批）。

## 4. Kconfig

| 项 | 默认 | 说明 |
|---|---|---|
| TS_INTERACT | n | 基线构建零变化（无 shell 构建逐字节等价）；atkbench prj 显式 y |
| 依赖 | — | Kconfig `depends on TS_APPMGR && TS_SAFETY`（DEC-65 修订形态——SHELL/LOG 为 **C 内 `#if defined(CONFIG_SHELL)` 构建面**而非 Kconfig 依赖：核心逻辑可无 shell 直测〔framework.interact 同款〕；bench 侧全显式 `=y`，不 select Zephyr 面板） |

## 5. 测试要点（testing.md 映射）

- L1（framework.interact 新套件）：核心逻辑直测（shell 运行时外）——无 pending confirm/reject = E_STATE；pending confirm rc=0 + meta 切换；pending reject 槽保留；arb 双向切换 + 切换零输出；estop clear 无 fault 拒 / 有 fault 过；log 级别域外拒。
- L4：boot 步骤序不变（interact 不入 boot 关键路径——命令表为编译期注册）。
- 真机判据（R5-V）：lconf=1 prov + 部署 → `ts confirm` 经 CH343 → 安装确认 + 暖复位 + APP ACTIVE（= F3 确认路的无手势版本）；`ts reject` 对称。

## 6. 未决依赖

- DEC-65 已登记（泛指令按建议值，先例 DEC-64 同型）；上游 Zephyr shell 缺陷域未知（发现随 R5-V 真机批）。

## 修订记录

- v0.2 · 2026-10-18：R5-V 真机批收口——§1 形态真机实证 + §5 真机判据四条 ALL PASS（confirm 路含 NVD 复验）；板级配置定案（THREADS_NUM 2/SHELL_STACK 4096/SYSWORKQ 4096/SENTINEL）入 §4 注记。
- v0.1 · 2026-10-18：R5-U 设计批首版（DEC-65 按建议值）。
