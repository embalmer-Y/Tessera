# LLD-A06 · 部署与数据面（deploy_*）· v0.2 修订

> **上游**：HLD-agent §2/A06；决策 DEC-18/20（zenoh，client→router 拓扑）、DEC-23（MCUmgr 底线）、DEC-30①（sys 命令面 host-only）；库基线 R5 §5（eclipse-zenoh 1.10.1）。v0.2 = 参考项目借鉴批次（NeuroLink 分块传输/分步升级实证档位）。

## 1. zenoh 客户端封装

- 包：`eclipse-zenoh==1.10.1`；**同步 API**（asyncio 已被上游移除）→ 封装 `ZenohService`：专属线程 + 队列桥（`asyncio.to_thread`/`run_coroutine_threadsafe` 反向），回调跨线程经 `janus` 队列〔Q-19 提案 1 是否引入 janus 或手搭——提案为手搭，避免加依赖〕。
- 配置：`[zenoh]` router locator（默认 tcp/127.0.0.1:7447）、TLS 节（自签场景**必须显式 root_ca_certificate**——R5 教训：默认信任 WebPKI）；Config.from_file 共享宿主 zenohd 配置。
- **三方同 minor 钉版（DR-22）**：zenohd router / eclipse-zenoh / zenoh-pico 固件侧 = 同一 1.x minor（1.10.1 基线）；sys_get_info 返回三方版本，集成测试断言一致；Zenoh 2.0（计划 2026 H2）= 联合升级风险项（HLD 登记，牵动 M3a）。

## 2. key 约定与命令镜像（与固件 LLD-ts-net 同源）

- 命名空间 `tessera/<node>/<cube>/<class>/<instance>/<action>`（固件侧权威）；Agent 侧消费/发布的 key 常量与 **kind 注册表**（LLD-ts-net §4.4）集中在 `keys.py`（镜像固件侧定义，**不自行发明**）。
- sys 命令消费：get-info/get-link/get-safety/get-budget/get-audit（DEC-30①，host-only 面——Agent 天然属 host 侧）；**控制租约三命令**（lease-acquire/release/get，〔Q-21 提案〕——deploy_push_* 写操作前 acquire、周期续期、完成/失败 release）。
- 命令请求构造随〔Q-20 信封 v2〕：deploy 工具一律带 rid + idem（重试安全）+ src（审计归因）。

## 3. 工具规格

### deploy_discover（auto）
- 机制：router 侧查询在线 cube（经固件侧发现/liveness key——具体 key 随 M3a ts-net 定稿，镜像原则同上）；超时〔Q-19 提案 4：10s〕。
- 返回：[{cube_id, node_id, fw_version, endpoints}]。

### deploy_status（auto）
- 组合 sys_get-info + get-link + get-safety 快照；返回结构化状态（含三安全态当前值——部署前人工/上层核验依据）。

### deploy_push_app（strict，句柄）
- 前置强制：tsap_verify 复验（app_deploy 链外直调同样强制——工具内实现，不可跳过）；**租约 acquire**〔Q-21〕。
- 传输（v0.2 定稿方向，NeuroLink 实证档位借鉴）：zenoh query 分块拉送——`sys/app-chunk {offset, chunk_size}` → `{data: bstr}`；块默认 2048B / 上限 4096B（1-4KB 实测稳定区间）；每块回执确认（丢块重拉，idem 幂等重试安全〔Q-20〕）。固件侧消费 = 增量写 inactive slot（复用 ts_store_slot_write 逐块回读校验语义）。
- **分步安装协议（v0.2）**：upload（分块写 slot）→ verify（整槽 hash + TSAP 验签链）→ activate（meta 原子切换）——对齐固件 ts-appmgr 既有安装链（pkg.c 三步），协议即链的远程化；各步独立回执，失败留于当前步（重试从失败步续传——offset 断点语义）。
- 完成语义：固件确认（版本回读一致）才置 completed；中间态如实（uploading/verifying/activating/confirmed）；结束（成功或失败）**release 租约**。

### deploy_push_prov（strict，句柄）
- prov CBOR（schema v1，DEC-30⑤，**固件定稿键序**——生成侧按 LLD-ts-store §4 键序手工构造，非 cbor2 canonical 排序；M3a-L3 实证）下发，分块同上；**仅允许对处于维护模式的 cube**（固件侧烧录通道纪律，合同 10）；维护模式判定经 sys_get-info 状态位。
- 审批：strict（默认策略表）+ 审计记录完整 prov 摘要。

## 4. MCUmgr/SMP 通道说明

- DEC-23 定 UART SMP 为救砖底线——**不属 Agent V1 面**（物理串口操作留人工/后续工具）；本文仅登记：固件 OTA 经 MCUmgr 的触发若未来需 Agent 化，走工具面增补（review 门）。

## 5. 测试要点（L7）

- ZenohService 线程桥：并发 put/get/订阅回调有序性；断连重连（router 重启）恢复。
- deploy_discover/status：对 router + native_sim 仿真立方体（M3a 测试资产；L3 复跑方法 dev-environment.md §8）集成。
- push_app：签名复验强制（无签名包必拒）；分块传输完整性（注入丢块重拉）；断点续传（中断后 offset 续）；分步状态机（upload/verify/activate 各失败注入）；确认回读语义。
- push_prov：维护模式门外拒绝；固件键序 CBOR 构造对拍（固件 prov 解析器）。
- 租约闭环：push 全程持有 → 崩溃模拟 → TTL 过期后他方可 acquire。
- 三方版本断言（DR-22）。

## 6. 未决依赖

- 固件侧：〔Q-21〕租约三命令 + 〔Q-20〕信封 v2 + sys/app-chunk 与分步安装命令（随裁定进实现，MA3 前共同定稿）；维护模式语义（M2b.2/板级）。
- Q-19 提案 1/4（janus 手搭 / discover 超时）。

## 修订记录

- v0.1 · 2026-09-22：首版草案（Agent design 批次）。
- v0.2 · 2026-09-23：参考项目借鉴批次（NeuroLink 分块/分步升级实证）——§3 push_app 传输定稿方向（query 分块 2-4KB + upload/verify/activate 分步对齐固件安装链 + 断点续传）；push_prov 补固件定稿键序生成纪律；§2 增租约/信封镜像；§5 测试面扩充。
