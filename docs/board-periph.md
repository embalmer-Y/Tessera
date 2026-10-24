# 板级九 · PWM/ADC 真驱动（ts-periph dispatch 板级后端）——单元报告

> **日期**：2026-10-02 · **载体**：`firmware/tests/periphbench/`（xiao_esp32s3 真机）· **状态**：PASS（真机全链 + 回归全绿）
> **上位**：AGENTS 二十七余项首项；HLD §4.5-S1/S2、合同 2/3；LLD-ts-periph v0.5 / LLD-ts-hal v0.2.2 / LLD-ts-safety v0.2.6。

## 1. 交付内容

1. **PWM 真后端**（`CONFIG_TS_DRV_PWM`，默认关；driver_dispatch.c = L5 白名单文件内）：DT 绑定 = zephyr,user（`pwm-uid` 逻辑名匹配 + `pwms` 三元胞规格；LEDC 引脚路由经 ledc0 pinctrl + channel 子节点——上游 `espressif,esp32-ledc` 绑定的既定模式）。写路径 = sim 记录（L4 golden 连续性）+ `pwm_set()`（ns 域；hz=打包高 16 ×100、permille=低 16）；写函数 void 返回 → 失败进 `ts_drv_pwm_err_count()` 观测计数（本批真机全程 0）。
2. **ADC 真后端**（`CONFIG_TS_DRV_ADC`，默认关；hal/api.c 输入面）：DT 绑定 = zephyr,user（`adc-uid` + `io-channels`——`ADC_DT_SPEC_GET_BY_NAME(DT_PATH(zephyr_user), …)` 即官方文档示例模式）。12bit / 内部基准 / 12dB 衰减（ADC_GAIN_1_4 最宽量程）；mV = Zephyr 通用换算（1100mV 基准口径，esp32 驱动已将 raw 预补偿：eFuse 曲线拟合校准 + 衰减反归一）；读失败如实 `TS_E_IO`。**输入直读不经保护层（合同 3）**；L5 唯一写路径检查只辖输出驱动面，adc_read 不在其列。
3. **安全层缺陷修复（本批被 bench 拦下的存量欠账）**：
   - **断链声明值落驱动**（channel.c set_link(false)）：HLD §4.5-S2 原文"全通道 SAFE_LINKLOSS（声明值落驱动）"，实现此前仅改 shadow = 物理输出滞留断链前值（合同 3 欠账；fault 路径 force.c 本就落驱动，故 estop 真机未暴露）。修复 = !up 迁移写 `desc->linkloss` 经 ts_drivers；DR-04 恢复不回写不变。已知余项：注册期 SAFE_POWERON 的 poweron 值落驱动（冷启物理态）未接线——V1 各板 poweron 值与硬件缺省态一致故未暴露，登记观察项（§5）。
   - **Kconfig 结构缺陷**：TS_POWER/TS_PERIPH 误嵌 `if TS_NET` 块（TS_NET=n 时不可见——estopbench 未用 periph 故未暴露，periphbench 构建即被拦）。修复 = endif 上移，两者回归 `depends on TS_HAL` 本位。
4. **api 域收紧**：`ts_pwm_set` hz 下界 100Hz（打包粒度 hz/100；V1 桩曾静默接受 hz<100，真后端按 hz 求周期后显式拒绝；既有测试零使用 <100）。

## 2. 真机判据与数据（PP*，xiao_esp32s3 @ procpu，2026-10-02）

引脚：PWM = LEDC_CH0→GPIO21（板载蓝色 LED，低有效——亮度与 duty 反相，仅肉眼观测注记）；ADC = ADC1_CH1 = GPIO2（D1；板 pinctrl 占用表核对：twai=3/4、spim2=7/8/9、i2c0=5/6，GPIO2 空闲）。注入/判据全部自动化（无人值守复跑 = §6）。

| 段 | 判据 | 结果 |
|---|---|---|
| PP2 duty 扫描 6 点 | ts_pwm_set（权限+限幅+审计全链）→ LEDC 寄存器 DUTY_R/DUTY_RES 比值 = permille ±3‰ | **99/250/500/699/500/399** vs 请求 100/250/500/700/500/400（±1‰，含跨 hz 1000↔5000 重配 duty_res 14↔13）全过 |
| PP3 保护层限幅 | 900‰ 请求（max=700‰）→ 落硬件 700‰ + 返回 TS_E_RANGE(-12) | **hw=700, r=-12** ✓（合同 2 真机证据：拦截值仍落驱动） |
| PP4 端点 0%/100% | 驱动停止态：CONF0.SIG_OUT_EN=0 + IDLE_LV=0/1 对应 | ✓（上游驱动 0%/100% 走 stop+idle-level 语义） |
| PP5 断链 fail-safe | 600‰ 运行中 set_link(false) → linkloss 声明值（0%）落硬件（SIG_OUT_EN=0）+ 断链写拒 TS_E_STATE + 恢复显式重写 400‰ 落硬件 | **hw=399, r=0** ✓（HLD §4.5-S2 修复真机首证） |
| PP6 ADC 低轨 | io_mux 输出使能注入 0V → mv < 150 | **mv=0** ✓ |
| PP7 ADC 高轨 | 注入 3.3V → mv > 2000 | **mv=3122**（12dB 衰减满量程饱和读数，eFuse 校准口径）✓ |
| PP8 悬空观测 | 撤输出使能 → 无判据 | mv=3122（悬空脚保持残压，SAR 高阻采样——观测记录） |
| PWM 静默失败计数 | err_count == 0 | ✓ |

判定口径：LEDC duty 寄存器字段 = **duty ticks << 4**（hal `ledc_ll_set_duty_int_part`：`hw->duty = duty_val << 4`，有效位 [18:4]——reg 头部位域注释 [18:0] 有误导）；permille_hw = DUTY_R×1000 / (2^duty_res×16)。

## 3. 过程留痕（如实）

1. 首轮 PP 读数恰为 16×：bench 回读公式漏 ÷16（源码核对 hal ledc_ll 后修正公式，PWM 写链本身从未错——六点数据在两轮完全一致）。
2. 修复后首烧未生效：pb_flash.sh `--skip-rebuild` 跳过重编，烧的仍是旧镜像（流程脚注：改码后必须重建再烧）。
3. 板卡 USB 中途脱落 → `usbipd attach --wsl --busid 7-4` 复挂（既有现象）。

## 4. 回归

twister **15/15（65 用例）** 全绿（断链落驱动修复零破坏——safety/power/net/periph/conc/replay 全过）；L5 **6/6**（TS_ADC_* 常量出处标注补齐后）；Agent pytest **58 passed, 2 skipped**；真机 PP PASS（本文 §2）。

## 5. 观察项（登记不动手，军规 9）

- **注册期 poweron 值落驱动未接线**（冷启物理态靠硬件缺省巧合）：建议随下一板级批或 Agent→真机部署批兑现（影响：poweron 声明 ≠ 硬件缺省的通道在首次 set_link 前物理态不等于声明值）。
- ADC 悬空读数保持残压（高阻采样特性）：真部署需外部分压/上拉网络，Agent 侧建模时注意。
- input monitor（DR-02 周期采集面）仍为影子桩（ts_gpio_read/ts_hal_input_poll_once 的真输入驱动未接，板级三已登记）——与本次 ADC 按需读（api 面）是两条线。
- LEDC 单 timer 共享约束：同 timer 多通道必须同频（上游驱动语义）——多 PWM 通道板级声明时注意分配 timer。

## 6. 复跑

```bash
# WSL 内：
bash ~/project/logs/pb_build.sh        # 构建（west build -p always -b xiao_esp32s3/esp32s3/procpu）
bash ~/project/logs/pb_flash.sh        # 烧录 + 15s console 捕获 → ~/project/logs/pb_console.log
# 判据 = 输出含 "PP PASS"
```
