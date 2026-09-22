# LLD-A06 · 部署与数据面（deploy_*）· v0.1 草案

> **上游**：HLD-agent §2/A06；决策 DEC-18/20（zenoh，client→router 拓扑）、DEC-23（MCUmgr 底线）、DEC-30①（sys 命令面 host-only）；库基线 R5 §5（eclipse-zenoh 1.10.1）。

## 1. zenoh 客户端封装

- 包：`eclipse-zenoh==1.10.1`；**同步 API**（asyncio 已被上游移除）→ 封装 `ZenohService`：专属线程 + 队列桥（`asyncio.to_thread`/`run_coroutine_threadsafe` 反向），回调跨线程经 `janus` 队列〔Q-19 提案 1 是否引入 janus 或手搭——提案为手搭，避免加依赖〕。
- 配置：`[zenoh]` router locator（默认 tcp/127.0.0.1:7447）、TLS 节（自签场景**必须显式 root_ca_certificate**——R5 教训：默认信任 WebPKI）；Config.from_file 共享宿主 zenohd 配置。
- **三方同 minor 钉版（DR-22）**：zenohd router / eclipse-zenoh / zenoh-pico 固件侧 = 同一 1.x minor（1.10.1 基线）；sys_get_info 返回三方版本，集成测试断言一致；Zenoh 2.0（计划 2026 H2）= 联合升级风险项（HLD 登记，牵动 M3a）。

## 2. key 约定（与固件 LLD-ts-net 同源）

- 命名空间 `tessera/<node>/<cube>/<class>/<instance>/<action>`（固件侧权威）；Agent 侧消费/发布的 key 常量集中在 `keys.py`（镜像固件侧定义，**不自行发明**）。
- sys 命令消费（只读族）：get-info/get-link/get-safety/get-budget/get-audit（DEC-30①，host-only 面——Agent 天然属 host 侧）。

## 3. 工具规格

### deploy_discover（auto）
- 机制：router 侧查询在线 cube（经固件侧发现/liveness key——具体 key 随 M3a ts-net 定稿，镜像原则同上）；超时〔Q-19 提案 4：10s〕。
- 返回：[{cube_id, node_id, fw_version, endpoints}]。

### deploy_status（auto）
- 组合 sys_get-info + get-link + get-safety 快照；返回结构化状态（含三安全态当前值——部署前人工/上层核验依据）。

### deploy_push_app（strict，句柄）
- 前置强制：tsap_verify 复验（app_deploy 链外直调同样强制——工具内实现，不可跳过）。
- 传输：APP 包经 zenoh 通道分块传输至目标 cube（**通道语义未决**：固件侧 APP 安装入口（ts-appmgr 拉取/SMP）待 M2a/M3a 定稿——本工具的 wire 协议登记未决依赖，MA3 前与固件侧共同定稿；候选：zenoh put 分块 + 固件回执确认）。
- 完成语义：固件确认（版本回读一致）才置 completed；中间态如实（uploaded/confirmed）。

### deploy_push_prov（strict，句柄）
- prov CBOR（schema v1，DEC-30⑤）下发；**仅允许对处于维护模式的 cube**（固件侧烧录通道纪律，合同 10）；维护模式判定经 sys_get-info 状态位（固件侧语义，M3a 对齐）。
- 审批：strict（默认策略表）+ 审计记录完整 prov 摘要。

## 4. MCUmgr/SMP 通道说明

- DEC-23 定 UART SMP 为救砖底线——**不属 Agent V1 面**（物理串口操作留人工/后续工具）；本文仅登记：固件 OTA 经 MCUmgr 的触发若未来需 Agent 化，走工具面增补（review 门）。

## 5. 测试要点（L7）

- ZenohService 线程桥：并发 put/get/订阅回调有序性；断连重连（router 重启）恢复。
- deploy_discover/status：对 router + native_sim 仿真立方体（M3a 测试资产）集成。
- push_app：签名复验强制（无签名包必拒）；分块传输完整性（注入丢块）；确认回读语义。
- 三方版本断言（DR-22）。

## 6. 未决依赖

- 固件 M3a：发现/liveness key、sys 命令实现、APP 安装入口、维护模式语义（MA3 前共同定稿）；M2a：prov schema 最终字段；Q-19 提案 1/4。
