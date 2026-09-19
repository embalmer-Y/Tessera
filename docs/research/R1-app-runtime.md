# R1 · APP 运行时调研 —— 初步笔记（草稿 v0.1）

> **状态**：初步笔记，**非正式 R1 交付、非裁决**（军规 2：一切选型以 owner 对 Q-01 的裁定为准）。
> **服务对象**：Q-01（DEC-09：APP 运行时待研究）。正式 R1 将在此基础上补实测与设计映射，按呈递格式（背景→选项→建议→影响）呈报。
> **调研日期**：2026-09-19，web 检索；本文事实为检索摘要转述，**正式 R1 前须回源核验**（来源见文末）。

## 0. 问题定义与评估维度

**现状**：Tessera 固件框架需要一种 APP 运行时，承载 DEC-04 定义的业务 APP：可安装（DEC-05 网络分发 + 签名 + 失败回滚）、可跨板迁移（依赖框架 HAL 而非具体硬件）、声明式权限、APP 之间仅经框架消息通道通信。
**动因**：运行时选型决定——APP 分发格式与签名对象；权限清单到沙箱边界的映射方式（安全合同第 10 条"权限清单是硬边界"要求边界**可强制执行**）；AI Agent 产物格式与工具链（DEC-11/12）。
**评估维度**（由裁定与安全合同推导）：

1. **架构覆盖**：DEC-14 板集横跨 x86（native_sim）、ARM Cortex-M（STM32H7、RP2350）、RISC-V（ESP32-P4）、Xtensa（ESP32-S3）——运行时必须全覆盖或给出明确取舍；
2. **隔离/沙箱强度**：权限模型与"固件核心不学习"（合同第 10 条）的强制点；
3. **维护与治理**：官方支持度、west 接入成本（owner 在 DEC-09 已有观察：wasm3 非官方维护、LLEXT 实验性）；
4. **性能与内存**：解释执行 vs 原生；沙箱性能预算划分（框架层原生承载重实时，APP 只做业务编排）；
5. **确定性**（安全合同第 9 条：重放可验证）；
6. **工具链**：Agent（PC 侧）能否自动化"编译→打包→签名"（DEC-11/12/05）。

## 1. 候选事实清单（检索转述，待回源核验）

### 候选 A：WASM 虚拟机

**A1 · wasm3**

- 纯 C 的 WASM 解释器，面向嵌入式/IoT，以可移植性与小体积著称（MIT 许可）。
- **维护状态（本次检索最重要的新事实）**：仓库公告已进入**最低维护阶段（minimal maintenance phase）**——维护者承诺保持项目存活、继续 review/merge 社区 PR，重点放在可移植性与稳定性，不做大的新特性开发。
- 不在 Zephyr west 默认 manifest（owner 在 DEC-09 的既有观察；集成需走外部模块或源码引入）。

**A2 · WAMR（WebAssembly Micro Runtime，Intel 主导，Apache-2.0）**

- **已有官方 Zephyr 移植**，可作为 Zephyr 模块使用：Zephyr 项目 2024-10 公告提及 WAMR 可作为 Zephyr 模块获得；上游仍有把 WAMR 纳入 Zephyr 外部组件的 issue 在推进（zephyr#118425）。
- Zephyr 移植**仅依赖 Zephyr 自带子系统**（kernel、threading、timing、heap）；AOT 编译在宿主机（PC）完成——wasm 模块可预编译，MCU 上接近原生性能。
- 执行模式：解释器（classic/fast）与 AOT；Intel 博客论述过"WASM + Zephyr 两层隔离模型"用于嵌入式安全隔离。
- Espressif 组件库官方分发 WAMR——ESP32 生态有第一方接入物，对 ESP32-S3/P4 覆盖是正信号。
- 维护活跃（Golioth 2024-07 实战教程；社区内容持续到 2025+）。

**A 类共同特性（对齐本项目需求）**

- 语言无关：Agent 可用任意能编译到 wasm 的语言（Rust/C/…）生成 APP，工具链在 PC 侧（对齐 DEC-11/12）。
- 沙箱模型强：线性内存隔离、无裸指针——权限清单（DEC-04）可映射为"导入函数面 + 能力句柄"，与合同第 10 条"硬边界"语义契合。
- WASM 执行语义确定（基础特性子集无 GC），利于合同第 9 条重放验证；若启用带 GC/线程的语言特性需另行评估。
- 代价：解释执行有性能折损（AOT 可大幅缓解）；HAL API 进出沙箱需框架自建绑定层（设计工作量）。

### 候选 B：LLEXT（Zephyr 原生可加载 ELF）

- Zephyr **在树子系统**：运行时加载可重定位 ELF，提供类 dlopen/dlsym 接口；官方文档标注**实验性（experimental）**。
- **架构支持（当前官方文档口径）**：RISC-V、ARM、ARM64、ARC、x86、**Xtensa**——若核验属实，则**覆盖 DEC-14 全部板集**（含 ESP32-S3 的 Xtensa 与 native_sim 的 x86）。注意：这与 DEC-09 备注时点的通行认知（LLEXT 架构覆盖有限）相比是利好变化，**须回源核验**。
- **隔离性**：LLEXT 通过导出符号表控制扩展可调用的内核 API 面（符号级边界）；但**内存保护（MPU/MMU 对加载段的隔离）自 2023-10 起是 GitHub 追踪的增强项，尚未成为默认可用的成熟沙箱**——当前隔离强度是"符号可见性"，不是"内存不可越界"。
- 原生代码性能（无解释开销）；Antmicro 已用其做设备上 AI 模型/运行体更新（2024-12 报道）。
- **跨板迁移弱点**：ELF 与目标架构绑定——同一 APP 需按板分发多架构构建（或框架层定义"胖包/按板包"），削弱 DEC-04"APP 与板卡解耦"的单一分发型态。
- 签名/回滚（DEC-05）需框架自建（LLEXT 本身不管安全分发）。

### 候选 C：脚本语言（MicroPython / Lua）

- **MicroPython**：有官方 Zephyr port（ports/zephyr），README 载明与 Zephyr 项目的相互维护承诺（最小二进制 < 128KB）；社区评价其为官方 port 中较不活跃的一档（2025-02 仍有实战文章）。
- Lua：体积小、易嵌入，但无官方 Zephyr 集成，需自行引入外部模块。
- **共同弱点**：GC/自动内存管理带来确定性挑战（合同第 9 条需设计规避，如禁自动 GC、预分配）；权限沙箱弱（需自建绑定层约束语言内建库/FFI）；解释性能低于原生。
- 优势：Agent 生成代码门槛最低（脚本语言的生成-试错循环短）、热更新天然。

## 2. 初步对比（工作假设，非裁决）

| 维度 | A. WASM（WAMR 为主） | B. LLEXT | C. 脚本类 |
|---|---|---|---|
| 架构覆盖（含 Xtensa） | 解释器架构无关；AOT 按架构预编译 | 文档称全覆盖（含 Xtensa，待核验） | 架构无关 |
| 隔离/权限硬边界 | 强（线性内存沙箱） | 弱-中（符号级；MPU 隔离在研） | 弱（需自建） |
| 维护/治理 | WAMR 活跃（外部模块）；wasm3 最低维护 | 官方在树但实验性 | port 存续、活跃度中低 |
| 性能 | 解释慢 / AOT 接近原生 | 原生 | 慢 |
| 确定性（合同第 9 条） | 好（注意语言特性选择） | 好 | 需规避 GC |
| Agent 工具链（DEC-11/12） | wasm 工具链成熟、语言无关 | 每板一套交叉编译 | 最轻 |
| 跨板单一分发型态 | 是（解释模式） | 否（按架构分发） | 是 |

**初步工作假设（仅为研究导向，不是建议、更不是裁决）**：WAMR（WASM，AOT 优先、解释兜底）在"权限硬边界 × 语言无关工具链 × 维护度"三个本项目最看重的轴上领先；LLEXT 可作为"框架层原生插件"（性能敏感的非业务组件）的补充形态——两者并不互斥：框架原生插件 vs 业务 APP 分层，恰与"重实时在框架层原生实现、业务编排在 APP"的既定划分（FOUNDING_PROMPT §6）吻合。正式 R1 需用实测数据检验此假设。

## 3. 正式 R1 待补清单（遗留项，不阻塞 K1 review）

1. 回源核验本文全部转述事实（官方文档/仓库原文，尤其是 LLEXT 含 Xtensa 的架构清单）；
2. 目标板实测：WAMR 解释/AOT 在四板 + native_sim 的内存占用与性能基准；
3. HAL API 绑定层设计映射：权限清单如何落到 wasm 导入函数/能力句柄（或 LLEXT 导出符号面）；
4. DEC-05 签名-版本-回滚链与运行时加载器的衔接设计；
5. wasm 工具链在 Agent（PC 侧）的自动化可行性验证（DEC-12：MCP 封装构建工具链）；
6. 若考虑混合形态：框架原生插件（LLEXT）与业务 APP（WASM）的边界定义。

## 4. 来源（检索于 2026-09-19）

- wasm3 仓库（最低维护阶段公告）：https://github.com/wasm3/wasm3
- Golioth《WebAssembly on Zephyr》（2024-07）：https://blog.golioth.io/webassembly-on-zephyr
- Zephyr issue #118425（WAMR 纳入外部组件讨论）：https://github.com/zephyrproject-rtos/zephyr/issues/118425
- Zephyr 项目公告（2024-10，含 WAMR 模块化可用）：https://www.zephyrproject.org/exploring-zephyr-secure-code-execution-board-support-openamp-and-documentation-improvements
- Intel《WebAssembly + Zephyr 两层隔离模型》：https://community.intel.com/t5/Blogs/Tech-Innovation/Client/WebAssembly-Zephyr-A-Two-Layer-Isolation-Model-for-Embedded/post/1754542
- Espressif 组件库 WAMR 页：https://components.espressif.com/components/espressif/wasm-micro-runtime
- Zephyr 官方文档 LLEXT 页（架构支持清单、experimental 标注）：https://docs.zephyrproject.org
- GitHub issue《llext: Better memory management and mmu/mpu support》（2023-10 起）：https://github.com/zephyrproject-rtos/zephyr
- Antmicro《Fast development of AI applications in Zephyr with LLEXT》（2024-12）：https://antmicro.com
- MicroPython Zephyr port 文档：https://docs.micropython.org ；port 起源 issue：https://github.com/micropython/micropython/issues/2481
