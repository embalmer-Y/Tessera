# R2 · 数据面应用层协议选型 —— 初步笔记（草稿 v0.1）

> **状态**：**已裁**——2026-09-19 owner 裁定 Q-02：数据面协议 = **zenoh**（Zephyr 侧采用 **zenoh-pico**）（DEC-18，原文："R2：选择zenoh-pico。"）。本文转为选型事实存档：§4 待补清单中选型类条目随裁决关闭，实测/核验类条目与 §3 耦合点移交 design 阶段（HLD 输入，另见 DEC-18 备注遗留设计题）。**v0.2（2026-09-19）**：增补 §6 二次核验（zenoh-pico 版本/传输/TLS/足迹），作为 HLD 与 Q 批次输入。
> **服务对象**：Q-02（DEC-08）→ 已裁 → DEC-18。
> **调研日期**：2026-09-19，web 检索转述，**采信前须回源核验**（来源见文末）。

## 0. 需求拆解（协议必须承载什么）

**现状**：数据面应用层协议从零选型（DEC-08 重开，旧 Zenoh 结论不复用）。**动因**：以下每一项都有上游裁定或安全合同条款背书，缺一项则上层设计无法闭合：

1. **发现**：Agent/宿主在局域网内发现立方体（含并联后的逻辑节点，DEC-02）；
2. **命名空间与编址**：逻辑节点 / 立方体 / 通道资源三级编址（DEC-02 遗留设计题之一）；
3. **命令-回执语义**：控制命令须有可靠回执与超时（Agent 编程模型的基础）；
4. **安全通道**：认证 + 加密（物理输出安全的传输侧配套，对应合同第 2/10 条）；
5. **断链判定（喂 fail-safe）**：心跳/保活 + **有界检测时间**——合同第 3 条要求失联即进安全态，检测时限是必须裁定的参数（默认值三问）；
6. **逻辑节点承载（DEC-02）**：多立方体并联对外一个端点：协议支持节点内路由，或由网关立方体终结；
7. **板覆盖（DEC-14）**：协议库必须在 Zephyr 主线栈上可用，避免每板私货（S3 原生 WiFi；P4 需 C6 或以太网；H7 需外挂 PHY；RP2350 需外挂网络模块）；
8. **确定性（合同第 9 条）**：协议栈行为可在 native_sim + 外设桩上重放测试（DEC-13）。

## 1. Zephyr in-tree 网络能力盘点（检索转述）

- Zephyr 网络栈提供：BSD-like sockets、TLS/DTLS（mbedTLS）、**CoAP**（含 observe/blockwise）、**LwM2M**、**MQTT**、**HTTP**、**WebSocket**（官方文档与示例确认，如官方 CoAP client sample）。
- 第三方聚合页另称支持 gRPC——**未获官方文档确认，暂不作为事实**（正式 R2 核验）。
- **mDNS/DNS-SD 是否在树支持未确认**——影响"发现"维度的选型，正式 R2 须核验。
- **zenoh-pico**（Apache-2.0，eclipse-zenoh）：**官方 Zephyr 模块**，支持 UDP 单播/组播传输；2025-07 的 peer-to-peer 改进在含 Zephyr 在内的全平台测试——维护活跃、Zephyr 为一级目标。注意 DEC-08 约束：旧项目 Zenoh **结论**不复用、**事实**可复用；本候选以同等地位重新进入对比，不预设立场。

## 2. 候选概览（完整对比留待正式 R2 实测）

| 候选 | 拓扑 | 命令-回执 | 发现 | 安全 | 初步观察（非裁决） |
|---|---|---|---|---|---|
| A. MQTT(+TLS) | 需 broker（PC 侧或立方体侧） | 经 topic 双向；MQTT5 有请求/响应模式，非原生 | 需另行设计（topic 约定或 mDNS） | mTLS 生态成熟 | 生态最大；broker 是额外基础设施与单点；QoS 语义与"命令-回执"不直接对应 |
| B. CoAP(+DTLS/OSCORE) | 端到端（无 broker） | 原生（CON 确认 + 响应码） | CoRE Resource Directory 或 mDNS，需评估 | DTLS/OSCORE 标准化 | 与"受限设备控制面"语义最契合；Zephyr in-tree 成熟 |
| C. WebSocket(+TLS) | 端到端 | 自定义应用语义 | 需另行设计 | TLS | 适合 PC Agent 直连；协议语义全自建 |
| D. 裸 TCP/UDP + CBOR/Protobuf | 端到端 | 全自定义 | 全自定义 | TLS 或自建 | 控制力/确定性最大；设计成本最高，语义无标准化互认 |
| E. zenoh-pico | peer/router 混合 | query 原生 + pub/sub | 内建（组播 scouting） | TLS/认证选项 | 发现/命名/通信一体；引入整个 zenoh 语义体系；Zephyr 官方模块、维护活跃 |
| F. DDS | brokerless 发现 | RPC 标准 | 内建 | DDS-Security（重） | MCU 侧普遍偏重，初判不符资源画像（验证后可排除） |
| G. 组合 | — | — | — | — | 如"发现用 mDNS/DNS-SD + 数据用 B/D"；正式 R2 评估 |

## 3. 与本项目特殊需求的耦合点（正式 R2 必答）

1. **断链判定参数**：各候选保活机制（MQTT keepalive / CoAP 应用层心跳 / zenoh link keepalive）→ 合同第 3 条"失联→安全态"的检测时限与抖动，须给出可测上界与默认值呈递（默认值三问）。
2. **逻辑节点（DEC-02）**：a) 网关立方体终结协议、节点内自选内部总线；b) 协议层支持多跳寻址。与 HLD 拓扑遗留题（主从/协商）联动，安全合同第 8 条（estop 本地独立生效）是硬约束。
3. **Agent 侧（DEC-12）**：MCP server 封装协议客户端——PC 侧库成熟度（MQTT/CoAP/zenoh 的 Python 实现均成熟，但语义映射到 MCP 工具面的工作量不同）。
4. **板覆盖（DEC-14）**：WiFi（S3）与以太网（P4/H7/RP2350 外挂）下 UDP/TCP 行为差异；RP2350 外挂网络模块形态可能限制候选（硬件侧约束输入）。
5. **固件不学习（合同第 10 条）**：密钥/证书烧录与轮换流程不经运行时自适应——协议安全层的配置面在 HLD 定义。

## 4. 正式 R2 待补清单

1. 回源核验 in-tree 协议清单（含 mDNS/DNS-SD 有无、gRPC 争议项）；
2. 候选在 native_sim + 至少一块真机上的 PoC（发现时延、回执 RTT、断链检测时间实测）；
3. 心跳/保活参数与合同第 3 条的映射提案（含默认值三问呈递）；
4. 逻辑节点寻址两案对比（网关终结 vs 协议多跳）；
5. zenoh-pico 按 DEC-08"事实重采、结论重开"原则完整评估。

## 5. 来源（检索于 2026-09-19）

- zenoh-pico 仓库：https://github.com/eclipse-zenoh/zenoh-pico
- Zenoh 官方博客《Zenoh-Pico Peer to Peer Improvements》（2025-07）：https://zenoh.io
- Zephyr 官方文档（CoAP client 示例等网络协议文档）：https://docs.zephyrproject.org
- 第三方聚合页（gRPC 支持声明，**未核验**）：https://apis.io

## 6. 二次核验与增补（v0.2 · 2026-09-19，DEC-18 落地输入）

> **背景**：DEC-18 已裁定 zenoh/zenoh-pico；本节回源核验并补落地细节。事实为检索转述；RAM 足迹与 keepalive 默认值待实测/回源。

### 6.1 版本与 API 稳定性

- zenoh-pico 当前文档线 **1.9.0**（readthedocs）；与 Rust zenoh 1.x 协议兼容、原生 C API。
- 1.x 线 API 相对 0.x 稳定，minor 间仍有破坏性变更记录 → **west 钉 revision**（与 WAMR 同策略，见 `docs/std/versioning.md`）。

### 6.2 传输、安全与平台（核验通过，且优于初判）

- 传输：**TCP、UDP 单播/组播**、串口、蓝牙（蓝牙依 DEC-06 排除）；**TLS 基于 mbedTLS**，编译期开关 `Z_FEATURE_LINK_TLS`（**默认 OFF**——启用须显式决定，纳入 Q-04 呈递）。
- Zephyr：在 Zephyr 官方外部模块清单内（`develop/manifest/external/zenoh-pico`）；文档口径支持 UDP（单/组播）与 TCP over IPv4/IPv6。
- 足迹：核心最小配置 ~**15KB flash**（2022 官方博客，裁剪极限）；RP2040 全功能基线 ~**80KB flash**（2025-01 官方博客）。RAM 权威数字未见——**待实测**。
- 对 DEC-18 影响：无翻转；"Zephyr 上仅 UDP"的保守假设被推翻（TCP 亦支持），拓扑选项扩大（Q-04）。

### 6.3 发现与命名（落地要点）

- 发现：组播 scouting + gossip；端点角色 client（连 router）与 peer（对等）两种——**V1 拓扑选择 → Q-04**。
- 命名：zenoh key expression 层级命名空间（如 `tessera/**`）可承载"逻辑节点 / 立方体 / 资源"三级编址（语法细节回源 zenoh 1.x 文档核验，HLD 给草案）。

### 6.4 断链语义与安全（HLD 必答项来源）

- 保活：zenoh 链路层 keepalive（参数可配，默认值待回源核验）→ 映射安全合同第 3 条失联检测时限（**Q-08**，须实测校准）。
- 安全：TLS（mbedTLS）+ zenoh 认证（口令 / x509 家族；pico 侧支持矩阵待核验）；密钥烧录与轮换属 HLD 安全配置面（合同 10：不经运行时自适应）。

### 6.5 对 HLD 的直接输入

1. 拓扑建议基础：V1 立方体 = **zenoh client** 连 PC 侧 zenohd router（UDP/TCP 单播 + TLS）；peer 模式与组播发现留逻辑节点（DEC-02）阶段。
2. 命名空间 key 语法草案在 HLD §数据面（随 HLD 一并过门 ③ 公共协议确认）。
3. keepalive → fail-safe 参数 → Q-08（默认值三问）。

### 6.6 新增来源（v0.2，检索于 2026-09-19）

- zenoh-pico 仓库：https://github.com/eclipse-zenoh/zenoh-pico
- zenoh-pico 1.9.0 文档（Z_FEATURE_LINK_TLS 等）：https://zenoh-pico.readthedocs.io
- Zephyr 外部模块清单 zenoh-pico 页：https://docs.zephyrproject.org/latest/develop/manifest/external/zenoh-pico.html
- RP2040 支持博客（2025-01，~80KB flash 基线）：https://zenoh.io/blog/2025-01-08-introducing-raspberry-pi-pico-support-in-zenoh-pico
- 核心裁剪极限（2022-06，~15KB）：https://zenoh.io/blog/2022-06-09-zenoh-pico-above-and-beyond
- P2P unicast 改进（2025-07）：https://zenoh.io/blog/2025-07-11-zenoh-pico-peer-to-peer-unicast

## 修订记录

- v0.1 · 2026-09-19：初步笔记（草稿）；同日 owner 裁定 → DEC-18。
- v0.2 · 2026-09-19：二次核验增补 §6（版本/传输/TLS/足迹/发现命名），输入 HLD 与 Q-04/Q-08。
