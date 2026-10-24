# LLD-agent-memory-planner · 通用内存规划程序（Memory Planner）· v0.1

> **本文件是什么**：通用内存规划程序低层设计——V0.13.0 MP 单元（DEC-70；owner「为各种各样的芯片设计一套通用的内存规划程序，确保不同的配置内存分配都可以合理并避免溢出的问题；同时记录这一套系统的最低要求下内存的需求是多少」）。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.1（2026-10-19 设计批；owner 泛指令「按照你规划的开发计划进行下一版本的规划和开发」= 按建议序开工——DEC-71，门③呈递随批）。

## 1. 定位与架构定性

**MP = 构建期确定性内存审计/规划工具**：输入一次真实构建的产物（linker map + `.config`），输出三层内存账本 + 规则判定报告。定性继承 BV1（LLD-agent-board-validation §1）——**非 LLM 创作任务**：解析机械、规则确定、报告结构化；LLM 不在关键路径。

**跨芯片通用性的来源（诚实声明）**：通用性不在「懂每种芯片」，而在**锚定两个芯片无关的稳定接口**——

1. **GNU ld/bfd map 格式**：xtensa（ESP32）/ aarch64 / riscv / x86_64（native_sim）全部经 GNU ld 链接，map 的 Memory Configuration 表 + output/input section 三行式条目 + 符号行形态一致（atk 真图与 native_sim 图同构解析已验证）；
2. **Kconfig `.config`**：Zephyr 全系生效值唯一事实源（`CONFIG_*` 键值行）。

芯片相关知识只存在于**规则目录**（§4）——每条规则挂教训/证据引用，目录版本化随教训增长；解析器与引擎零芯片假设。

**三个消费者**：

| 消费者 | 消费面 |
|---|---|
| MP 报告（配置合法定性） | 构建后跑一次——区域余量/栈堆池账/规则 findings；重平决策的输入（「谁占着 DRAM」具名到对象） |
| **最低内存基线**（DEC-70②） | `docs/memory-baseline.md` 按配置档的 DRAM/PSRAM/FLASH 最低需求——数据来源 = 本工具对三档载体的实测账 + 运行余量口径（§6） |
| BV1 画像（v2 缝） | 画像 `[memory]` 节（dram_kb/psram_kb/flash_kb 期望）× 本工具区域账对拍——v1 仅留 schema 缝不实现门（登记 v2） |

**与教训体系的关系**：历史上四次内存事故（FIX-1 rx 栈 1500 压穿 / R5-V③ shell+sysworkq 栈溢出 / P1-2 堆 -80 / R5-I wifi TX ENOMEM）全部是**事后人肉查 map/.config** 定案——MP 把这套排查法机械化，规则 = 事故的机械化拦截器，每条带出处。

## 2. 输入

```
tessera-agent memory-audit --map <zephyr.map> --config <.config>
                           [--prj-conf <prj.conf>]      # R0 覆盖对照（可选）
                           [--json] [--out <file>]
```

- `--map`：GNU ld map（Zephyr `zephyr/zephyr.map`；pre-build `zephyr_pre0.map` 同样可消费——链接失败态的溢出前账本也有价值，如实标注 `pre_build=true`）。
- `--config`：Kconfig 生效值（`.config`）。**只认生效值**——教训：atkbench prj.conf 声明 `HEAP_MEM_POOL_SIZE=196608` 被板级 conf 覆盖为 58368，声明≠生效（本设计批首日实录）。
- `--prj-conf`：可选对照——声明值 vs 生效值差异 = R0 finding（不假定谁对谁错，差异本身即风险信号）。

## 3. 三层账本（解析器）

### 3.1 region 层（精确）

map 头部 `Memory Configuration` 表（名称/起址/长度/属性）逐 region 求和 output section 占用：

- `used` = Σ output section size（按起址落入 region 判归属）；
- `slack` = length − used；
- **保留区识别**：ESP32-S3 `dram0.dummy`（0xf600 = IRAM 镜像窗）类零填充 output section 不计入可用余量——`reserved` 名单按形态判定（size>0 且无 input section 且无 load address）。诚实余量 = slack，不把保留窗当 free。

### 3.2 对象层（具名，best-effort）

input section 三种行式（GNU ld map 实测形态）逐一捕获：

1. 同长行：` .bss.wifi_cb  0xaddr  0xsize  objfile`；
2. 两行式：` .bss.ak_ui_tid` ⏎ `                0xaddr  0xsize  objfile`（objfile 可带 archive 括号尾）；
3. `*fill*` 行（对齐填充，单独累计不冒充对象）。

符号行（`0xaddr  symbol`）归并到**同址 input section**：`_k_thread_stack_*` → 线程栈、`kheap_*`/`*_heap` → 堆、`_k_mem_slab_buf_*` → slab 池。归并失败的如实落在「未具名静态」桶并报告归并率（不硬造归属——map 无符号名的对象无法机械定名）。

输出：对象账 = {线程栈明细（具名+尺寸）, 堆, slab 池, 池/缓冲（形态匹配）, 未具名静态}，按 region 分组。

### 3.3 config 层（意图与规则输入）

`.config` 逐行 `CONFIG_<KEY>=<val>` 解析为字典。**预期账**：凡 `*_STACK_SIZE` / `*_HEAP*` / `*POOL*` / `*BUF*` 键即内存意图清单——与对象层对拍（配置声明了但 map 里找不到对应对象 = 门控未开，如实注记；反之亦然）。

## 4. 规则目录 v1（RULES_VERSION = 1）

规则 = 纯函数 `f(config, ledger) -> Finding`；Finding = {rule_id, severity(fail/warn/info), message, evidence}。目录内置版本化；每条挂证据出处。

| ID | 判据 | 级 | 出处 |
|---|---|---|---|
| **R0** | `--prj-conf` 声明值 ≠ `.config` 生效值 | warn | 本设计批首日实录：atk/netbench/deploybench 三处 prj.conf 死值（196608 被板级 conf 覆盖） |
| **R1** | `WIFI=y && NET_RX_STACK_SIZE < 4096` | fail | FIX-1：缺省 1500 被部署突发压穿 FATAL（bv1_c6_crash_console.txt） |
| **R2** | zenoh 使能 && `SYSTEM_WORKQUEUE_STACK_SIZE < 4096` | fail | R5-V③：WiFi/DHCP 事件建链窗溢出（STACK_SENTINEL 点名） |
| **R3** | `SHELL=y && SHELL_STACK_SIZE < 4096` | fail | R5-V③：confirm 链 2048 装不下（EXCCAUSE 0 野跳实证） |
| **R4** | esp32 wifi && `ESP32_WIFI_DYNAMIC_TX_BUFFER_NUM × 1600 > 系统堆 × 50%` | warn | R5-I/FIX-1 残余：TX 突发 ENOMEM 噪声（atk 32×1.6K=52K > 58368/2） |
| **R5** | `TS_NET_TLS=y && 系统堆 < 65536` | warn | P1-2：TLS 建链期堆 -80 量级（50-56K 档实测循环） |
| **R6** | 任一 region `slack < 2048` | warn | 链接器擦边余量不可部署（对齐/填充漂移无缓冲） |
| **R7** | `ESP32_WIFI_STATIC_TX_BUFFER=y` | warn | 教训 41：STATIC TX 本机两轮实测均劣化（+SPIRAM heap = 关联活数据面死；单用 = 关联失败 rc=-134；4.5-rc1 驱动/hal 双层 TX buffer Kconfig 映射存疑——上游核实登记中，核实后更新判据） |

**总体判定**：任一 fail → `FAIL`；无 fail 有 warn → `WARN`；全过 → `PASS`。退出码三态 0/1/2。

## 5. 面

- **CLI**：`tessera-agent memory-audit`（§2 参数；文本报告人类可读 + `--json` 结构化）。
- **MCP**：`memory_audit` 工具（strict；本地只读文件——无 spawn 需求，直接函数调用）。
- **BV1 画像缝（不实现）**：`agent/boards/*.toml` v2 增加 `[memory]` 节的 schema 注记——本批不接入验证门。

## 6. 最低内存基线（DEC-70②——`docs/memory-baseline.md`）

**口径**：某配置档的最低需求 = `静态账（map 实测）+ 运行余量（系统堆实测峰值 × 裕度系数 1.3）`。DRAM 最低 = Σ(非堆静态) + 最低可行堆；PSRAM/FLASH 同理按 region。

**三档载体（本批实测）**：

| 档 | 载体 | 配置差 |
|---|---|---|
| 最小 net 档 | netbench @ xiao_esp32s3 | 无 WAMR/无 TLS/无 UI/无音频（TS_APP_WAMR=n） |
| 标准档 | deploybench @ xiao_esp32s3 | +WAMR（PSRAM 堆）+store，无 TLS/UI |
| 全外设档 | atkbench @ dnesp32s3b | +TLS mTLS+LVGL+音频+SD+interact shell |

每档报：DRAM 总量/静态账/系统堆定值/链接余量、PSRAM 账、FLASH 占用——**全部实测推导，推定项逐条标注**。消费方 = R12 板卡选型 + BV1 画像门（v2）。

## 7. 测试

- 合成 map/config 夹具矩阵：三行式解析 / 符号归并 / fill 不冒充 / 保留区识别 / 八条规则正负样本 / R0 对照 / overall 三态 / 退出码。
- **真图回放锚定**：atk FIX-1 真实 map 数字断言（dram0_0_seg 399108B；mbedtls 堆 31744；lvgl 池 16384；kheap__system_heap 58452≈58368+头）——解析器对真实 GNU ld 输出的回归锚。
- Live 分支：CLI 参数缺失/文件不存在 fail-closed。

## 8. v2 方向（登记不实施）

- **运行期水位闭环**：thread analyzer HWM / 堆峰值对拍静态账——「静态预算 × 运行水位」双面（atk UI 栈 91% 实测即运行水位数据）；
- BV1 画像 `[memory]` 门接入（新板 bring-up 时内存可行性机械判定）；
- 规则目录外部化（项目级规则文件）；
- PSRAM 账面细化（WAMR 池/装载缓冲/verify 缓冲具名归并）。
