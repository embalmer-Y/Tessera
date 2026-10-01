# board-estop-01 · 板级八：estop chosen 绑定真机验证（xiao_esp32s3）

> **状态**：v1.0 · 2026-10-01 · 板级八交付单元报告（owner 指令"依次解决剩余问题"第三项）。
> **DoD**：estop 硬件链路（引脚沿 → 中断 → ISR 直达 → fault 态落通道 → 锁存 → 恢复）真机验证；绑定机制板级落地。**判定：达成。**
> 关联：合同 5（estop 不经协议栈/调度排队）、DR-11（estop DT 绑定）、DEC-30①（estop-clear host-only）、LLD-ts-safety v0.2.5。

## 1. 绑定机制修订（上游事实，本批钉死）

- **v4.4 的 EDT 管道不发射非 `zephyr,` 前缀 chosen 属性的宏**：dtlib 层属性在（zephyr.dts 有 `ts-estop-gpio = < &estop_key >`）、edtlib 层被弃（edt.pickle 的 chosen_nodes 无此键 → devicetree_generated.h 无 `DT_CHOSEN_ts_estop_gpio`）。诊断路径留痕：dtlib 直读 dts ✓ / EDT pickle ✗ / 生成头 ✗。
- **修复（零上游补丁）**：绑定改走 **aliases**——`aliases { ts-estop-gpio = &estop_key; }`（注意语法为直接引用，非尖括号 phandle）；模块 `driver_dispatch.c` 同步 `DT_CHOSEN(...)` → `DT_ALIAS(ts_estop_gpio)`。DR-11 语义不变（板级声明式 estop 引脚绑定），机制事实登记 LLD/dev-env。

## 2. 触发注入方法（无人工按键的自动化）

无人按键条件下走**完整硬件路径**（非软件直调）：io_mux 输入+输出双使能 + 翻转 GPIO 输出寄存器（esp32s3 GPIO0 bank @0x60004000：ENABLE_W1TS/W1TC + OUT_W1TS/W1TC）→ 引脚电平真实变化 → 输入采样器 + GPIO 外设中断 → estop_isr。bench 专用测试注入（与 boardbench 裸基线同类豁免；产品路径唯一写经保护层不变）。

## 3. 真机验证（estopbench，EB* console 行）

```text
EB1 estop bound (GPIO9) 通道基线 fault-free
EB3 #1 硬件沿→fault 落通道≤20ms     ← 沿→ISR→force_all_fault→fault 值直写（轮询粒度上界 20ms）
EB3 #1 恢复 fault-free               ← clear_fault + 显式 commit 回写（DR-04：恢复不自动回写）
（×3 轮重复，全部 ≤20ms + 恢复成功）
EB PASS estop 硬件链路 ×3（沿触发/ISR 直达/锁存/补发/恢复）
```

- **通道观测设计**：eb0 通道三态 poweron=false / linkloss=false / **fault=true**——readback 由 false→true 的唯一置位来源即 estop 链路 fault 直写（判据无歧义）。
- **恢复语义**：`ts_safety_clear_fault()`（estop 锁存双检）→ DR-04 不自动回写 → 显式 `ts_safety_commit(false)` 回写 → fault-free 基线恢复。
- **如实记录**：`TS_EVT_ESTOP 事后补发 = 0`——deferred publish 由周期驱动调用（`ts_safety_estop_deferred_publish`），本 bench 直启面（无 core_boot 周期驱动）未接线，与设计一致；补发语义由 framework.safety 测试覆盖（native_sim）。ISR 直达路径（合同 5）本批真机证实。
- 沿配置 = 上升沿占位（松开触发；DR-11 沿配置 prov 化为既有 M2+ 待办，不变）。

## 4. 回归

twister **15/15（65 用例）** / L5 6/6（含 estop 调用图检查——绑定宏切换后仍零违规）/ pytest 2/2 全绿。

## 5. 复跑入口

`west build -p always -b xiao_esp32s3/esp32s3/procpu firmware/tests/estopbench -d <build> -- -DZEPHYR_EXTRA_MODULES=<module>` → `west flash` → `console_smoke.py /dev/ttyACM0 14`（关注 EB PASS 行）。人工按键（BOOT 键按下-松开）同样触发——上行沿语义见 §3。
