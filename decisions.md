# decisions.md · Tessera 决策登记册

> **生命周期**：`Q-xx`（待裁）→ owner 回复 → `DEC-xx`（已裁，附日期与原文）；编号不复用，REJECTED 留档。
> **呈递格式**（流程 §2.4 强制）：背景（现状 + 为何是问题）→ 选项 → 建议 → 影响。
> **默认值三问**（写任何常量前自答）：从哪来（Q/推导）？越界会怎样？改动破坏什么？
> 本文"§x.y"章节号指 `FOUNDING_PROMPT.md` 章节。

## 一、已裁定决策（DEC）

> DEC-01…16：**2026-09-18 owner 裁定**（K1 录入，原文见 `FOUNDING_PROMPT.md` §1）；DEC-17/18：**2026-09-19 owner 裁定**（原文见备注栏）。

| # | 裁定日期 | 决策（原文） | 备注（含遗留设计题） |
|---|---|---|---|
| DEC-01 | 2026-09-18 | 每个立方体 = 独立智能模块：自带 MCU、Zephyr 固件、网络接口、电源路径 | — |
| DEC-02 | 2026-09-18 | 立方体四面扩展接口**含数据链路**；并联后的多立方体对外构成**一个逻辑节点** | 遗留设计题（HLD 必答）：逻辑节点内部拓扑（主从/协商）、跨立方体资源编址、安全仲裁归属；硬约束见安全合同第 8 条 |
| DEC-03 | 2026-09-18 | 对外供电**受控**：软件开关、限流、功率预算上报 | 供电视同"输出"，纳入安全合同（§5.7） |
| DEC-04 | 2026-09-18 | APP 访问硬件 = 框架统一 HAL API + **声明式权限清单**（类安卓 Manifest）；APP 之间仅经框架消息通道通信，禁止直接互访 | 权限模型变更触发 review 门（§2.4-③） |
| DEC-05 | 2026-09-18 | APP 安装 = 网络分发 + 签名 + 版本化 + 失败自动回滚 | — |
| DEC-06 | 2026-09-18 | 数据面通信**只走物理网络**（以太网 / WiFi）；**BLE 不考虑** | — |
| DEC-07 | 2026-09-18 | UART 完全退出数据面：仅作调试终端（Zephyr shell，类 Linux console）+ MCUmgr/SMP 救砖与 OTA 底线通道 | — |
| DEC-08 | 2026-09-18 | 数据面应用层协议选型**重开**（旧项目的 Zenoh 结论不复用） | → Q-02 / R2 |
| DEC-09 | 2026-09-18 | APP 运行时（WASM 虚拟机 vs LLEXT 原生 ELF vs 其他）**待研究** | → Q-01 / R1；owner 已知观察：WASM 运行时（如 wasm3）非 Zephyr 官方维护、不在 west 默认 manifest；LLEXT 官方在树但标注实验性 |
| DEC-10 | 2026-09-18 | 物理安全基线继承 §5 安全合同（旧项目调研结论，与任何上层项目无关，属产品安全本身） | 合同全文：`AGENTS.md` §6 |
| DEC-11 | 2026-09-18 | AI Agent 产出范围 = 业务 APP **与** 硬件配置（外设分配 / 引脚映射 / 安全参数）——**两者，owner 强调** | — |
| DEC-12 | 2026-09-18 | Agent 形态 = MCP server，封装"模块 API + 模拟器 + 构建工具链"；LLM 由用户自选；Agent 运行于 PC 侧 | — |
| DEC-13 | 2026-09-18 | V1 模拟测试深度 = native_sim 固件仿真 + 外设桩模型（数字孪生-lite）；真机在环后续再议 | — |
| DEC-14 | 2026-09-18 | 目标板集：ESP32-S3 / ESP32-P4 / STM32H7 / RP2350 + native_sim（CI 平台） | 各板网络能力差异（S3 原生 WiFi；P4 无无线电需配 C6 或用以太网；H7 有 EMAC 需外挂 PHY；RP2350 需外挂网络模块）——R2/HLD 的输入 |
| DEC-15 | 2026-09-18 | V1 交付顺序：**固件框架（native_sim 上可运行）→ AI Agent + 模拟器 → 硬件立方体定型** | 理由：硬件结构/连接器周期最长且依赖软件形态验证 |
| DEC-16 | 2026-09-18 | 独立开源仓库；许可证 Apache-2.0 | — |
| DEC-17 | 2026-09-19 | APP 运行时 = **WASM 虚拟机**，实现采用 **WAMR**（WebAssembly Micro Runtime，Apache-2.0，有官方 Zephyr 移植） | owner 原文："R1：我们选择WAMR。"；依据 R1 初步笔记（草稿 v0.1，`docs/research/R1-app-runtime.md`）裁定。遗留设计题（HLD 必答）：① 执行模式（解释器 vs AOT vs 混合）与按板预编译策略；② HAL API 绑定层——权限清单（DEC-04）如何映射为 wasm 导入函数/能力句柄（安全合同 10 的强制点）；③ wasm APP 打包与签名格式（DEC-05）；④ 四板 + native_sim 的内存占用/性能实测（R1 待补项转入）；⑤ "LLEXT 作框架原生插件"的混合形态**未裁定**，如采用须另立 Q |
| DEC-18 | 2026-09-19 | 数据面应用层协议 = **zenoh**，Zephyr 侧采用嵌入式实现 **zenoh-pico**（Apache-2.0，官方 Zephyr 模块） | owner 原文："R2：选择zenoh-pico。"；DEC-08 重开后经 R2 初步笔记（草稿 v0.1，`docs/research/R2-protocol.md`）裁定。遗留设计题（HLD 必答）：① Zephyr 上传输层组合（UDP 单/组播已证实，TCP 及其他待核验）与 WiFi 组播可靠性；② 安全通道配置（zenoh 认证/TLS 选项）与密钥管理（合同 10：不经运行时自适应）；③ 断链判定参数——心跳/保活 → 失联检测时限（合同 3，须过默认值三问）；④ 逻辑节点寻址（DEC-02 遗留题：网关立方体终结 vs 协议多跳）；⑤ RP2350 外挂网络模块适配（DEC-14）；⑥ PC 侧 Agent 的 zenoh 客户端封装（DEC-12） |

## 二、问题登记（Q）

### 待裁批次（design 阶段呈递 · 2026-09-19 · 配套 HLD v0.1）

#### Q-03 · Zephyr 目标版本

- **背景**：DEC-01 定 Zephyr 但未定版本基线；west manifest、外部模块（WAMR/zenoh-pico）兼容面、native_sim/CI 行为随版本变化（当前最新为 4.4，2026-04 发布、配 Zephyr SDK 1.0；3.7 为 LTS 但已近维护尾期）。不定版本 M0 无法初始化工作区。
- **选项**：A. 4.4（最新 stable）；B. 3.7 LTS（旧，外部模块新特性可能不兼容）；C. 4.x 中间版（若确有 LTS 分支，待核验）。
- **建议**：A（4.4）：WAMR 与 zenoh-pico 均活跃跟踪主线，native_sim/CI 基线最新；V1 周期内若 4.x 出新 LTS 再评估迁移（显式提交+全量回归）。
- **影响**：west manifest 基线与 SDK 安装；依赖升级策略（`docs/std/versioning.md`）。

#### Q-04 · zenoh 部署拓扑与传输

- **背景**：DEC-18 定 zenoh/zenoh-pico 但未定端点角色与传输组合。zenoh 有 client（连 router）与 peer（对等）角色；Zephyr 上 UDP 单/组播、TCP 均可用（R2 v0.2 核验），TLS 经 mbedTLS（`Z_FEATURE_LINK_TLS` 默认 OFF，须显式开）。拓扑决定断链语义与 Agent 侧形态。
- **选项**：A. V1 立方体 = client，连 PC 侧 zenohd router（UDP/TCP 单播 + TLS）；peer/组播发现留逻辑节点阶段。B. V1 即 peer 对等（组播 scouting，无 router）。C. 混合。
- **建议**：A：断链判定单跳清晰、Agent 天然在 router 侧、实现面最小；WiFi 组播可靠性未实测前不押 B。
- **影响**：ts-net 实现面；Q-08 标定环境；Agent（DEC-12）封装对象；未来 peer 迁移成本（M3 评估）。

#### Q-05 · APP 包格式与签名方案

- **背景**：DEC-05 要求网络分发+签名+版本化+回滚；DEC-17 定 WASM 后包 = wasm + manifest + 签名，格式未定。Agent 产物（DEC-11）与固件 ts-appmgr 双向依赖该格式，属公共文件格式（门 ③）。
- **选项**：A. 单文件容器：wasm 模块 + manifest(CBOR) + COSE-Sign1(ed25519)；B. tar/zip 多文件 + 独立签名；C. 复用 OCI 等成熟 artifact（嵌入式生态不适配）。
- **建议**：A：CBOR+COSE 为 IETF 嵌入式标准栈；ed25519 验签快、密钥小；打包（Agent 侧）与验签（固件侧）均可自动化。
- **影响**：ts-appmgr 验签实现；Agent 打包工具；根公钥烧录体系（合同 10）；版本比较与回滚规则（联动 Q-09）。

#### Q-06 · WAMR 执行模式与 WASI 裁剪

- **背景**：DEC-17 定 WAMR；执行模式与 WASI 开关未定。核验数据（R1 v0.2）：classic ~56KB / fast ~59KB（≈2× 性能）/ AOT 运行时 ~29KB（文件更大、按架构预编译、需 wamrc）；WASI 是 CVE 集中面（2.4.x 修 poll_oneoff 堆溢出）且扩大攻击/权限面。
- **选项**：A. fast 解释器 + WASI 关（框架自建最小 `ts_*` 导入面）；B. AOT 优先；C. classic（省 ~3KB、性能减半）。
- **建议**：A 起步：单一 wasm 包保持跨板迁移（DEC-04）；AOT 留作 Agent 构建期优化选项；WASI 全集关，权限面最小。
- **影响**：内存预算（M2 实测四板余量）；Agent 工具链复杂度；WAMR 升级回归范围。

#### Q-07 · 逻辑节点 V1 范围

- **背景**：DEC-02 要求多立方体并联为逻辑节点（拓扑/编址/仲裁为遗留题）；V1 主战场 native_sim 单实例（DEC-13/15），连接器与硬件形态第三阶段才定型。
- **选项**：A. V1 仅命名空间与接口预留（key 首段 node 层、资源编址经 ts-periph 间接化），不实现并联；B. V1 即实现 native_sim 多实例并联模拟。
- **建议**：A：避免硬件形态未定时固化协议细节；预留成本已消化在 HLD。
- **影响**：DEC-02 遗留题推迟至硬件阶段前专项 HLD；选 B 则 M3 范围显著扩大。

#### Q-08 · 断链判定参数（默认值呈递）

- **背景**：合同 3 要求失联→输出进安全态且检测时限有界可测。zenoh 链路 keepalive 参数可配（默认值待回源核验）。值过短→抖动误触发；过长→失控窗口大。
- **选项（初值提案）**：心跳间隔 500ms / 连续丢失阈值 4 / 检测上界 ≈2s（含实现裕量）；WDT 周期独立设 5s（防喂狗伪造，与心跳解耦）。
- **建议**：采纳初值进 M3 实测标定（WiFi/以太网抖动分布），标定后按默认值三问复核再定稿。
- **影响**：ts-net↔ts-safety 联动阈值；Agent 命令超时上界；重放测试虚拟时钟注入。

#### Q-09 · 存储分区与 OTA 策略

- **背景**：DEC-05 要求 APP 版本化+回滚；DEC-07 定 UART MCUmgr/SMP 为救砖与 OTA 底线；固件自身 OTA 与分区表未裁，M2 依赖分区定义。
- **选项**：A. 双 APP slot(a/b) + meta 区（版本指针/回滚计数）+ 固件双 slot（MCUmgr img_mgmt，UART 底线、zenoh 通道后续可选）；B. 单 slot+备份区；C. APP 外置存储。
- **建议**：A：A/B 切换回滚最稳；native_sim 以文件系统模拟分区；meta 区仅验签成功后原子更新。
- **影响**：flash 预算（板间差异→slot 尺寸按板可配）；bootloader 信任链（M2 细化）；安全参数区烧录纪律（合同 10）。

### 已裁（留档）

#### Q-01 · APP 运行时选型（→ R1）

- **状态**：**已裁 → DEC-17**（2026-09-19：APP 运行时 = WASM，实现采用 WAMR）。
- **背景**：DEC-04 要求 APP 与板卡解耦、声明式权限、APP 间仅经框架消息通道隔离；DEC-09 裁定运行时待研究。现状：候选（WASM 解释器 / LLEXT 原生 ELF / 脚本类等）在维护度、沙箱强度、性能、架构覆盖（DEC-14 板集横跨 x86 仿真、Cortex-M、RISC-V、Xtensa）、west 接入成本上差异显著，尚未系统对比。该选型是 APP 打包格式、权限边界落点、Agent 产物形态的前置条件。
- **选项**：A. WASM 解释器（wasm3 / WAMR / wasmi 等）；B. LLEXT 原生 ELF；C. 脚本语言（MicroPython / Lua 等）；D. 混合或自研加载器。
- **建议**：（留档）未及正式呈报——owner 于初步笔记阶段直接裁定，见 DEC-17。
- **影响**：APP 分发与签名对象（DEC-05）；权限清单到沙箱边界的映射（安全合同第 10 条）；实时/性能预算划分；Agent 生成物格式与工具链（DEC-11/12）；目标板覆盖（DEC-14）。

### Q-02 · 数据面应用层协议选型（→ R2）

- **状态**：**已裁 → DEC-18**（2026-09-19：数据面协议 = zenoh，Zephyr 侧用 zenoh-pico）。
- **背景**：DEC-08 裁定重开（旧项目 Zenoh 结论不复用，事实可复用）；DEC-06 限定数据面只走以太网/WiFi；DEC-07 UART 退出数据面。协议须承载：设备发现、命名空间与编址、命令-回执语义、安全通道、断链判定（喂安全合同第 3 条 fail-safe）、多立方体逻辑节点（DEC-02）。现状：候选（MQTT / CoAP / WebSocket / 裸 TCP+序列化 / Zenoh-pico / DDS 等）未在"Zephyr in-tree 支持度 × 安全 × 确定性 × 逻辑节点承载 × 板覆盖"维度上系统对比。
- **选项**：A. MQTT(+TLS)；B. CoAP(+OSCORE/DTLS)；C. WebSocket(+TLS)；D. 裸 TCP/UDP + CBOR/Protobuf 自定义语义；E. Zenoh（zenoh-pico）；F. DDS；G. 组合（如发现层 + 数据层分离）。
- **建议**：（留档）未及正式呈报——owner 于初步笔记阶段直接裁定，见 DEC-18。
- **影响**：Agent 与模块间 API（DEC-12）；断链心跳与检测时限（安全合同第 3/5 条的参数来源）；多立方体编址（DEC-02 遗留题）；证书/密钥管理与分发；Zephyr 网络栈裁剪与内存占用。

## 三、修订记录

- 2026-09-19 · K1 录入：DEC-01…16（2026-09-18 owner 裁定）+ 待裁 Q-01/Q-02（依 `FOUNDING_PROMPT.md` §9-2）。
- 2026-09-19 · owner 裁定 Q-01/Q-02 → **DEC-17**（APP 运行时 = WASM / WAMR）、**DEC-18**（数据面协议 = zenoh / zenoh-pico）；R1/R2 初步笔记转为选型事实存档，其实测/核验类待补项与两项 DEC 的遗留设计题移交 design 阶段。
- 2026-09-19 · design 阶段呈递：HLD 固件框架 v0.1（`design/HLD-firmware-framework.md`）+ 待裁批次 **Q-03…Q-09**（Zephyr 版本 / zenoh 拓扑 / APP 包格式 / WAMR 模式 / 逻辑节点范围 / 断链参数 / 存储与 OTA）。
