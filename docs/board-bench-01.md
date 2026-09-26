# 板级运行效率基准报告 board-bench-01 · 2026-09-26（板级二单元）

> **DoD 出处**：plan v1.10 六项（owner 指令"真板检查时多检查一下我们的架构运行效率如何"）。
> **载体**：xiao_esp32s3（ESP32-S3 @240MHz，**单核**——SMP 事实见 §4）+ `firmware/tests/boardbench/` 基准应用（wasm 夹具 `appw/bench.c` 669B + 宿主计时）。
> **方法学**：宿主侧 CCOUNT 计时（Xtensa `rsr.ccount`；`k_cycle_get_64` 本板冻结——§5 教训 B3）；完成检测 = 通道影子值翻转轮询；wasm 零测量逻辑（受控负载 + 标记回写）；mailbox 时延 = 投递→线程唤醒→wasm evt→native→安全层提交→影子可读全链路。
> **配置**：fast-interp（DEC-25）+ xtensa 官方汇编 invokeNative + WAMR 堆 64KB + APP 宿主栈 32KB；主线程 prio 15 / APP 线程 10 / 压测线程 15（时间片轮转）。

## 1. 六项数据（第一版）

| # | 指标 | 结果 | 对照 |
|---|---|---|---|
| ① | WAMR 解释器吞吐（busy 300k 迭代，volatile RMW） | **1043 ns/iter**（312.99ms/300k，~250 cycles/iter） | native_sim Q-23 基线 ~1.1ns/iter（host x86）→ 板级 ~950×慢，嵌入式解释器量级符合预期 |
| ② | wasm→native 往返（ts_time_ms ×20k） | **4524 ns/call**；减循环解释开销①（1043ns）≈ **净往返 ~3.5µs** | — |
| ③ | 写路径端到端（ts_gpio_write×5k：perm→唯一写路径→状态机→审计→驱动） | **9717 ns/call**；相对②增量 ≈ **安全层净成本 ~5.2µs** | 合同 2 唯一写路径含审计留痕的成本量化 |
| ④ | mailbox 时延分布（n=300，0 失败） | min 27 / **p50 28** / p95 28 / max 34 µs | 全链路（投递→唤醒→wasm→提交→可读）；tick 预算 100ms 占比 0.028% |
| ⑤ | 足迹 vs HLD §4.6 | bench 镜像：text 82KB@flash + rodata 14KB；静态 bss 92KB；libc 堆余 219KB。app 镜像（前一单元）：text 91KB / bss 113KB / 堆余 218KB | HLD §4.6 ESP32-S3 行预算：框架安全静态≈24KB ✓（ts_ch_table 17KB 等）；WAMR 实例堆 256KB 目标需 PSRAM（当前 64KB 内部过渡） |
| ⑥ | 并发（单核抢占降级模式） | 压测线程（同抢 write_lock 直写独立通道）期间：p50/p95 不变（28µs）、max 34→46µs；**estop 全局强制在并发中生效**（all_safe=1）+ 恢复后功能正常（echo 32µs） | DEC-43 锁收口设计验证：短临界区（write_lock）对中位无影响、尾部 +12µs |

补充：APP 冷启动（load+instantiate+natives 注册+app_init）≈ **4.8ms**。

## 2. 效率结论（V1 判断）

- **吞吐**：1µs/迭代级 → APP 每毫秒可执行 ~1000 迭代级操作；V1 输入输出业务（tick 100ms、断链 6s、WDT 10s 量级）预算充裕（>2 个数量级裕量）。
- **写路径**：~10µs/次经完整安全层——100Hz 输出更新率下占比 0.1%；限幅/审计/留痕成本可接受。
- **mailbox**：28µs p50 / 34µs max（空载）——mailbox 深度 8 + 丢最旧策略在突发场景下不会成为瓶颈。
- **判读注意**：①含每迭代 volatile RMW（比纯空转略重）；②③为单核独占测量，⑥给出锁竞争增量；数据为 fast-interp 解释器（DEC-25），AOT 为 Agent 构建期选项（升级留作后续）。

## 3. 板级二过程中的缺陷修复（同批交付）

| 项 | 内容 |
|---|---|
| B1 | `firmware/app/boards/xiao_esp32s3_esp32s3_procpu.conf`（bring-up 单元交付，内存过渡值 DEC-23/27） |
| B2 | WAMR xtensa 陷出改官方汇编 `invokeNative_xtensa.s` + `-Wa,--noexecstack`（汇编期补 GNU-stack 注记；GENERAL C 版注释自认部分 CPU 传参不可靠）——此前 native_sim 侧 GENERAL 保留 |
| B3 | runtime.c 失败可见性：app_init 异常路径补 WAMR 异常文本 printk（军规 7） |
| B4 | bench 教训：通道描述符须各自独立持久存储（注册存指针，栈上复用单对象 = 全表别名 → 全 NOTFOUND） |

## 4. 事实与限制（Q-24 呈递）

- **ESP32-S3 在 Zephyr v4.4.0 无 SMP**：kernel SMP 钩子 `arch_cpu_start` 无 esp32s3 实现（构建实证链接失败；v4.4.0 树内仅 esp32 经典款有）。espressif 双核路径 = AMP（`SOC_ENABLE_APPCPU`，双镜像 + IPM），与 framework.conc 单调度器语义不符。**⑥ 在本板降级为单核抢占并发**（数据见上）；双核终验载体 = Q-24 待 owner 裁决（建议：V1 以 native_sim 多核终验为准〔Q-23 批已具备，SMP=4 核〕，真机双核待 Zephyr ESP32-S3 SMP 落地〔DEC-19 跟进〕或换 ESP32 经典款板〔v4.4.0 已支持 SMP〕）。
- 驱动层为 native_sim 桩（driver_dispatch sim 记录）——③ 数据含桩成本、不含真 GPIO 外设访问（板级驱动 = 后续单元）。
- `k_cycle_get_64` 本板冻结（75ms 忙等 delta=0，uptime 正常）——基准改用 CCOUNT；根因未深究（登记 dev-env 教训 19，上游跟踪项）。

## 5. 环境教训（登记 dev-environment.md §5）

- **B3（教训 19）**：esp32s3 `k_cycle_get_64` 冻结 → 周期计时用 `rsr.ccount`（32 位 @240MHz，17.8s 回绕，差值即时计算）。
- **B2（教训 18）**：WAMR XTENSA 陷出实现必须用官方汇编（`-Wa,--noexecstack` 补注记）；GENERAL C 版跨板"一致"是假象。
- **B4**：`ts_safety_register_channel` 存描述符指针——描述符须 file-scope 持久对象（native_sim 测试惯例掩盖了该约束）。

## 6. 复跑方法

```bash
bash ~/project/logs/bflash.sh pristine   # 构建+烧录+45s console 抓取（BB* 行即数据）
# native_sim 流程回归（数字无意义，仅链路）：
west build -p always -b native_sim firmware/tests/boardbench -d <dir> -- -DZEPHYR_EXTRA_MODULES=... && <dir>/build/zephyr/zephyr.exe
```

原始记录：`~/project/logs/bench-console.log`（2026-09-26 两轮一致：BB1 1043/1043、BB2 4524/4524、BB3 9717/9717 ns）。
