# LLD · ts-net v0.3

> **状态**：v0.3 修订（2026-09-23，参考项目借鉴批次——owner 提供 NeuroLink/MatrixMechanic，指令"优化现有 design"触发；未裁决语义以〔Q-xx 提案〕标注）。上位：HLD §3.5；公共约定 `LLD-00-common.md`。
> **职责**：zenoh-pico 会话管理、命名空间构造、命令-回执分发、遥测/事件发布、心跳监视（断链判定）、控制租约〔Q-21 提案〕。
> **合同关联**：合同 3（断链 fail-safe 判定源）、8（本地独立生效——判定不依赖外部确认）、9（rx 串行化）、10（命令准入/留痕）。
> **外部依赖**：zenoh-pico 1.10.1（钉版，DR-22；上游零源码补丁，接线要点见 docs/dev-environment.md §7/§8）。

## 0. 演进原则（v0.3 新增——参考项目教训收敛）

- **方向不对称**：host→固件的**命令面严格 fail-closed**（未知键/未知 kind/超集 = 拒绝，M3a.2 语义不变）；固件→host 的**事件/遥测面前向兼容**（未知 kind 透传不解析——消费端升级先于/后于固件均可）。
- **演进走版本化信封**（ver + kind），**不采用"跳过未知键"**（MatrixMechanic TLV 思想的取舍：跳过语义利于传输层独占协议，但弱化确定性验证；版本边界显式且可机械断言）。
- **消息类型分级编号注册表**（NeuroLink 形态）：kind 区间 = 请求 1-15 / 回执 16-31 / 事件 32-95（32+TS_EVT_ID）/ 遥测 96-127；注册表唯一权威在本文件 §4.4，Agent 侧 `keys.py` 镜像（不自行发明）。
- **payload 键名 V1 维持字符串**（M3a.2 已实现面不折腾；整数键注册表的省流量收益在 128B 级回执上不显著，若 V2 切换走门③）。

## 1. 内部结构

```text
src/net/
  session.c    会话建立/重连（client 角色〔DEC-20〕；native_sim 默认 udp/localhost〔DEC-27〕）
  keyspace.c   key 构造与资源映射（tessera/<node>/<cube>/…）
  cmd.c        query 服务端：命令分发表 + 回执 + 信封 v2〔Q-20 提案〕
  lease.c      控制租约〔Q-21 提案〕：acquire/release/TTL 过期
  pub.c        遥测/事件/心跳发布（缓冲与合流 + 版本化信封〔Q-22 提案〕）
  linkmon.c    心跳监视 → ts_safety_set_link
  cbor_min.c   确定性子集 CBOR 编解码（M3a.2 已实现）
```

## 2. 会话（session.c）

- 角色 client〔DEC-20；宿主修订 DEC-32〕：locator 来自 prov（router 地址；宿主 = **Linux PC** 或 ARM64 Linux 工业/机器人主板，Windows 移出）；重连退避固定表〔DEC-27：250/500/1000/2000ms 循环〕（确定性，禁指数抖动随机）。
- TLS：`Z_FEATURE_LINK_TLS` 显式开启〔DEC-20〕；证书/密钥只读自安全参数分区（合同 10）。
- 会话状态：DOWN/CONNECTED；迁移发布 `TS_EVT_NET_LINK_UP/DOWN`（观测用；**安全语义以 linkmon 为准**，避免双源）。
- **传输健康定义（v0.3 定稿，M3a.2 已知短板的收口）**：`is_up` = zenoh-pico 会话任务活性自省 `zp_read_task_is_running() && zp_lease_task_is_running()`（探测"会话对象在而任务已死"的半死态；NeuroLink 实证手法）——替代 M3a.2 的 opened 标志位，实现随下一实现单元。

## 3. 命名空间构造（keyspace.c）

```c
int ts_net_key_cmd(char *buf, size_t n, const char *uid);     /* …/<class>/<inst>/cmd     */
int ts_net_key_tel(char *buf, size_t n, const char *uid);     /* …/<class>/<inst>/telemetry */
int ts_net_key_evt(char *buf, size_t n, const char *uid);     /* …/<class>/<inst>/event   */
int ts_net_key_hb  (char *buf, size_t n, bool host_dir);      /* …/sys/hb（cube→host）/ …/sys/hb-host（host→cube），DR-12 */
int ts_net_key_sys (char *buf, size_t n, const char *cmd);    /* …/sys/<cmd>（命令面见 §4，DR-03） */
/* 前缀 tessera/<node>/<cube> 由 node/cube id 配置拼装；node 段为 DEC-02 预留层（Q-07） */
```

- key 语法随 HLD §3.5 草案；语义变更 = 门 ③（fw semver X 位）。

## 4. 命令-回执（cmd.c）

### 4.1 现行格式（M3a.2 已实现，v1）

- 请求：定体 map`{"op": tstr, "args"?: {"confirm"?: tstr, "time_ms"?: uint}}`；回执：map`{"status": int, "data": …}`；未知 op/key、op/key 不匹配、非法 CBOR = 显式拒绝回执（不留静默）。

### 4.2 命令信封 v2〔Q-20 提案——NeuroLink 请求信封借鉴〕

- 请求：`{"ver": 1, "kind": 1, "rid": tstr≤16, "src": tstr≤24, "op": tstr, "args": {…, "idem"?: tstr≤16, "to"?: uint}}`
- 回执：`{"ver": 1, "kind": 16, "rid": <原样回带>, "status": int, "data": …}`
- 语义：
  - **request_id（rid）**：回执回带——调用方关联/审计归因（合同 10 对外留痕的调用方标识）；
  - **幂等键（idem，可选）**：固件侧最近 4 项 idem→回执缓存（定容 LRU），同键重复请求**回放回执不重执行**——网络超时重发安全；
  - **带内超时（to，可选）**：命令执行上界；上界必须 < 断链判定上界〔DEC-22 联动，LLD 原文档级约束的机制化〕；
  - **source（src）**：调用方身份，进审计 payload。
- v1/v2 共存策略：固件按首键判别（"op" 首 = v1；"ver" 首 = v2）；v2 采纳则 v1 进入弃用期（fw semver 次+1 移除）。

### 4.3 sys 命令面（v1，DR-03；授权 DEC-30①）——注册者为框架自身，标记 `host_only`

| key（…/sys/ 下） | 语义 |
|---|---|
| get-info | 固件版本/板/构建（`git describe`，versioning.md §5） |
| get-link / get-safety | 链路与通道安全态汇总（读 ts-safety shadow） |
| get-budget | 功率预算/用量（ts-power，M3b 落地） |
| get-audit | 安全审计环形导出（含溢出丢弃计数，DR-07；V1 最新 6 条/次，分片游标随信封 v2） |
| set-time | 设置墙钟（**仅数据字段**，合同 9；DR-08） |
| estop-clear | 清除 SAFE_FAULT（参数须带确认令牌 `confirm="estop"`；调用 ts_safety_clear_fault） |
| lease-acquire / lease-release / lease-get | 控制租约面〔Q-21 提案，见 §4.5〕 |

### 4.4 kind 注册表（唯一权威；Agent 侧 keys.py 镜像）

| 区间 | 用途 | 已分配 |
|---|---|---|
| 1-15 | 请求 | 1 = sys 命令（op 分流） |
| 16-31 | 回执 | 16 = 命令回执 |
| 32-95 | 事件 | 32+TS_EVT_ID（与 core.h ts_evt_id_t 对齐；64-95 预留） |
| 96-127 | 遥测 | 96 = 输出实例快照 |

### 4.5 控制租约〔Q-21 提案——NeuroLink lease_manager 借鉴〕

- **问题**：多方（多个 Agent/工具/人工面板）并发命令同一 cube 时的输出控制权仲裁；当前无仲裁。
- **V1 形态（建议）**：单租约——`sys/lease-acquire {holder}` → `{lease_id, expires_at_ms}`；TTL 默认 10s〔Q-21 提案值：≈断链窗口 6s（DEC-22）×1.5+余量〕；持有者周期续期（re-acquire 幂等）；`lease-release` 主动归还；TTL 到期自动失效（控制方崩溃 = 天然失权）。
- **准入挂钩**：写类命令（未来 hal 写/app 命令，M2b.2 面）须持有有效租约；sys 面只读族与 estop-clear **豁免**（estop 安全路径不受租约约束——合同 5 优先）。挂钩实现随 M2b.2 命令面接入。
- **与安全态的关系（建议）**：租约**只管命令准入，不联动安全态**——输出安全态唯一判定源仍是 linkmon/estop（合同 3/5 单源纪律）；租约全部失效 ≠ 输出进安全态。
- 不做（V1）：多资源粒度、优先级抢占（NeuroLink 全形态）——单 cube 单控制方的现实负载下无需求，留 V2。

## 5. 发布（pub.c）

- 遥测：实例值变化（commit 审计缓冲消费）与周期快照〔DEC-27：200ms〕合流；缓冲深度〔DEC-27：8〕满则丢最旧并计数；**DOWN 期发布直接丢弃并计数**（不排队重放——防上电风暴与不确定时序）。
- 事件：TS_EVT_* 选择性外发（estop 后补发、安全态迁移、越权留痕——合同 5/10 对外可见面）。
- **信封 v1〔Q-22 提案〕**：事件 payload = `{"ver":1, "kind":32+evt_id, "t_ms", "wall_ms", …}`；遥测 payload = `{"ver":1, "kind":96, "value_u", "wall_ms", …}`。消费端（host/Agent）对未知 kind **透传存储不解析**（§0 前向兼容落点）；固件产生端只产注册表内 kind。
- 优先级映射（v0.3 登记，实现随 zenoh publish options）：安全事件（estop/安全态迁移/越权）= zenoh congestion block + 高优先级；遥测 = drop——参考 MatrixMechanic priority 位思想，用 zenoh 原生 QoS 承接（不自造位域）。

## 6. 心跳监视（linkmon.c）——合同 3 判定源

- 发送：周期〔DEC-22：prov 可配，出厂默认 1000ms〕pub `…/sys/hb`；监视：host 侧 `…/sys/hb-host` 超过〔DEC-22：默认 6〕个周期未达 → `ts_safety_set_link(false)`（经 sysworkq 串行迁移）；恢复带滞回（连续〔DEC-27：2〕个周期）才 `set_link(true)`。
- 判定完全本地（不依赖 router 确认自己的存在——合同 8）；输入/遥测方向不受 set_link 影响（合同 3）。
- 测试注入：`CONFIG_TS_TEST` 构建提供 hb 帧注入/抑制接口（L4 断链场景驱动）。

## 7. Kconfig（节选）

| 项 | 默认〔DEC-27〕 | 说明 |
|---|---|---|
| CONFIG_TS_NET_HB_PERIOD_MS | 1000 | 心跳周期（DEC-22 prov 可配） |
| CONFIG_TS_NET_HB_MISS_LIMIT | 6 | 断链判定窗口 |
| CONFIG_TS_NET_HB_RECOVER | 2 | 恢复滞回 |
| CONFIG_TS_NET_TELEM_INTERVAL_MS | 200 | 周期快照 |
| CONFIG_TS_NET_PUBQ_DEPTH | 8 | 发布缓冲 |
| CONFIG_TS_NET_LEASE_TTL_MS〔Q-21〕 | 10000 | 租约 TTL（≈断链窗口×1.5+余量） |
| CONFIG_TS_NET_IDEM_CACHE | 4 | 幂等回执缓存深度〔Q-20〕 |

## 8. 测试要点

- L1：key 构造；退避表推进；linkmon 计数判定（含滞回）；**信封编解码（v1/v2 判别、rid 回带、幂等缓存命中/驱逐）**；**租约获取/续期/过期/豁免命令**。
- L2：命令分发（权限/未知 key/回执码）；遥测合流与丢弃计数；**同 idem 重放不重执行（副作用计数=1）**。
- L4：断链→SAFE_LINKLOSS→恢复全时序重放（虚拟时钟 + hb 注入）；DOWN 期发布丢弃计数进入 golden。
- L3（已达成 2026-09-23）：对 PC 侧 router 端到端（发现、命令、回执、心跳）——复跑方法 dev-environment.md §8；信封 v2/租约用例随实现批次扩展。

## 9. 未决依赖

- **Q-20 命令信封 v2 / Q-21 控制租约 / Q-22 事件遥测信封**（本批呈递）——裁定后进实现（建议批次：随 MA3 deploy 链）。
- is_up 任务自省（§2）为已定稿实现项（无需裁决）。
- DEC-20/22/26/27/30 已裁；M2b.2 = 写命令面（租约准入挂钩时机）。

## 修订记录

- v0.1 · 2026-09-20：首版草案。
- v0.2 · 2026-09-20：review-01——keyspace 补 hb/sys 构造器（DR-12）；§4 补 sys 命令面（DR-03，深化批次）。
- v0.2.1 · 2026-09-21：裁决同步——DEC-20/22/30 出处收敛（SC-02）。
- v0.3 · 2026-09-23：参考项目借鉴批次（owner 提供 NeuroLink/MatrixMechanic）——新增 §0 演进原则（fail-closed 不变 + ver/kind 信封演进）；§2 传输健康定义（zp 任务自省，M3a.2 短板收口）；§4.2 命令信封 v2〔Q-20〕；§4.4 kind 注册表；§4.5 控制租约〔Q-21〕；§5 事件/遥测信封与 zenoh QoS 映射〔Q-22〕；§7 Kconfig 增补；M3a.1/M3a.2/L3 实现状态对齐（§8）。
