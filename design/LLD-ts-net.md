# LLD · ts-net v0.3.6

> **状态**：v0.3.6（2026-09-26 DEC-43：pubq 互斥——push/flush 并发安全〔锁内出队 + 锁外发送〕；锁序 write_lock → pubq 单向）。上位：HLD §3.5；公共约定 `LLD-00-common.md`。
> **职责**：zenoh-pico 会话管理、命名空间构造、命令-回执分发、遥测/事件发布、心跳监视（断链判定）、控制租约（DEC-41）。
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
  cmd.c        query 服务端：命令分发表 + 回执 + 信封 v2（DEC-40）
  lease.c      控制租约（DEC-41）：acquire/release/TTL 过期
  pub.c        遥测/事件/心跳发布（缓冲与合流 + 版本化信封（DEC-42））
  linkmon.c    心跳监视 → ts_safety_set_link
  cbor_min.c   确定性子集 CBOR 编解码（M3a.2 已实现）
```

## 2. 会话（session.c）

- 角色 client〔DEC-20；宿主修订 DEC-32〕：locator 来自 prov（router 地址；宿主 = **Linux PC** 或 ARM64 Linux 工业/机器人主板，Windows 移出）；重连退避固定表〔DEC-27：250/500/1000/2000ms 循环〕（确定性，禁指数抖动随机）。缺省回退 locator = `tcp/127.0.0.1:7447`（DEC-40 命令面链路约束后，原 native_sim udp 缺省收敛为 tcp——zenohd 缺省监听兼容）。
- TLS：`Z_FEATURE_LINK_TLS` 显式开启〔DEC-20〕；证书/密钥只读自安全参数分区（合同 10）。
- 会话状态：DOWN/CONNECTED；迁移发布 `TS_EVT_NET_LINK_UP/DOWN`（观测用；**安全语义以 linkmon 为准**，避免双源）。
- **传输健康定义（v0.3 定稿，已实现于 DEC-40 批）**：`is_up` = zenoh-pico 会话任务活性自省 `zp_read_task_is_running() && zp_lease_task_is_running()`（探测"会话对象在而任务已死"的半死态；NeuroLink 实证手法；上游接口标 deprecated 仅指任务无需手动启动，活性探测语义有效）。

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

### 4.2 命令信封 v2（DEC-40；NeuroLink 请求信封借鉴；**已实现**）

- 请求：`{"ver": 1, "kind": 1, "rid": tstr≤16, "src": tstr≤24, "op": tstr, "args": {…, "idem"?: tstr≤16, "to"?: uint}}`
- 回执：`{"ver": 1, "kind": 16, "rid": <原样回带>, "status": int, "data": …}`
- 语义：
  - **request_id（rid）**：回执回带——调用方关联/审计归因（合同 10 对外留痕的调用方标识）；
  - **幂等键（idem，可选）**：固件侧最近 4 项 idem→回执缓存（定容 LRU，`CONFIG_TS_NET_IDEM_CACHE`），同键重复请求**回放回执不重执行**——网络超时重发安全；**回放判定在 key/op 双匹配之后**（impl-review-01 F-4：回执只应在与其执行同 key 的查询上回放，跨 key 同 idem = op/key mismatch 拒绝；门控豁免回放是有意语义——回放无新副作用，缓存回执对应一次已通过门控的历史执行）；
  - **带内超时（to，可选）**：命令执行上界；**固件拒绝 to > 5000ms**（断链窗口 6000ms〔DEC-22〕− 余量；出处 DEC-40）；
  - **source（src）**：调用方身份，进审计 payload。
- v1/v2 共存策略：固件按首键判别（"op" 首 = v1；"ver" 首 = v2）；v1 进入弃用期（fw semver 次+1 移除）。
- 实现细节（v0.3.2 定稿）：idem 缓存键 = idem 字符串（≤16），命中且 **op 一致**才回放（op 不一致 = TS_E_PARAM "idem/op mismatch"——调用方键管理错误防御）；仅命令实际执行后的回执入缓存（malformed/mismatch 类分发级拒绝不缓存）；LRU 时钟 = 分发上下文单调计数（非墙钟，合同 9）。
- **zenoh 可靠性调研留档（DEC-40，2026-09-23 实查 zenoh-pico 1.10.1）**：① TCP/TLS 链路传输层可靠有序，UDP unicast 尽力而为且 zenoh 无重传；② QoS 旋钮（congestion_control/priority/reliability）均非投递保证（reliability 属 unstable 门控）；③ query 无重试无去重——"命令已执行、回执未达、调用方重发"的应用层重复由 idem 承载（端到端论证）。
- **命令面链路约束（DEC-40，已实现）**：命令/回执链路必须 TCP 或 TLS——prov `router_locators[0]` 形态校验 `tcp/`/`tls/` 前缀（UDP locator 拒绝建链，TS_E_PARAM）；UDP 仅限 scouting/遥测可选路径。

### 4.3 sys 命令面（v1，DR-03；授权 DEC-30①）——注册者为框架自身，标记 `host_only`

| key（…/sys/ 下） | 语义 |
|---|---|
| get-info | 固件版本/板/构建 + **node/cube 自报**（MA3.1：通配发现的身份以载荷为准） |
| get-link / get-safety | 链路与通道安全态汇总（读 ts-safety shadow） |
| get-budget | 功率预算/用量（ts-power，M3b 落地） |
| get-audit | 安全审计环形导出（含溢出丢弃计数，DR-07；V1 最新 6 条/次，分片游标随信封 v2） |
| set-time | 设置墙钟（**仅数据字段**，合同 9；DR-08） |
| estop-clear | 清除 SAFE_FAULT（参数须带确认令牌 `confirm="estop"`；调用 ts_safety_clear_fault） |
| lease-acquire / lease-release / lease-get | 控制租约面（DEC-41，见 §4.5） |
| app-begin / app-chunk / app-verify / app-activate | 远程部署面（MA3.1，LLD-A06 §3；**gated：仅 v2 信封 + 租约持有者 = src**——DEC-41 写类准入首个落点） |
| get-app | 当前 APP 信息快照（active_slot 回读确认，只读豁免） |

- **gated 装配（impl-review-01 F-3）**：`ts_net_cmd_sys_init`（返回 `ts_res_t`，表满/撞名上抛 → init fail-safe，合同 6）按 **suffix 回查**回填 gated 位——公共注册面占首个空位，若 sys 表非首个注册方则下标与表位错开，按名回填使门控恒指向本命令（按下标回填错位 = 写命令未门控，不可接受）。

### 4.4 kind 注册表（唯一权威；Agent 侧 keys.py 镜像）

| 区间 | 用途 | 已分配 |
|---|---|---|
| 1-15 | 请求 | 1 = sys 命令（op 分流） |
| 16-31 | 回执 | 16 = 命令回执 |
| 32-95 | 事件 | 32+TS_EVT_ID（与 core.h ts_evt_id_t 对齐；64-95 预留） |
| 96-127 | 遥测 | 96 = 输出实例快照；97 = 功率预算快照（M3b，…/sys/power） |

### 4.5 控制租约（DEC-41；NeuroLink lease_manager 借鉴；**已实现**）

- **问题**：多方（多个 Agent/工具/人工面板）并发命令同一 cube 时的输出控制权仲裁；当前无仲裁。
- **V1 形态（DEC-41）**：单租约——`sys/lease-acquire {holder≤24}` → `{lease_id, expires_at_ms}`；TTL 默认 10s〔DEC-41：≈断链窗口 6s（DEC-22）×1.5+余量〕；持有者周期续期（re-acquire 幂等，id 不变）；`lease-release {holder}` 主动归还（他人代还 = TS_E_STATE）；TTL 到期自动失效（**惰性过期**——访问时判定，无定时器；控制方崩溃 = 天然失权）。lease_id 从 1 起单调递增不复用（过期/归还后新授予必得新 id）。拒绝回执回填当前 {holder, lease_id, expires_at_ms} 供调用方归因（同信任域 host 面）。
- **准入挂钩**：写类命令（未来 hal 写/app 命令，M2b.2 面）须持有有效租约；sys 面只读族与 estop-clear **豁免**（estop 安全路径不受租约约束——合同 5 优先）。挂钩实现随 M2b.2 命令面接入。
- **与安全态的关系（DEC-41）**：租约**只管命令准入，不联动安全态**——输出安全态唯一判定源仍是 linkmon/estop（合同 3/5 单源纪律）；租约全部失效 ≠ 输出进安全态。
- 不做（V1）：多资源粒度、优先级抢占（NeuroLink 全形态）——单 cube 单控制方的现实负载下无需求，留 V2。

## 5. 发布（pub.c）

- 遥测：实例值变化（commit 审计缓冲消费）与周期快照〔DEC-27：200ms〕合流；缓冲深度〔DEC-27：8〕满则丢最旧并计数；**DOWN 期发布直接丢弃并计数**（不排队重放——防上电风暴与不确定时序）。pubq 单条 payload 上限 **128B**（impl-review-01 F-1 定容：DEC-42 信封头最坏 ~45B + 预算事件 3 对 extra ~51B——原 64B 系"单 extra 对"口径；内存影响 +512B 静态，计入 DEC-29 板级 RAM 预算复核）。
- 事件：TS_EVT_* 选择性外发，**订阅七类**——estop 后补发 / 安全态迁移 / 越权留痕 / 输入变化 / periph 插拔 / periph 附着 / 功率预算拒绝（后三类 = impl-review-01 F-1 兑现，其中插拔归因为 LLD-ts-periph §3"key 下线通告"承诺；早前"容量四类全占"系对订阅表分桶语义的误读——`subs[id][CONFIG_TS_CORE_MAX_SUBS]` 按事件类型各 4 位）。合同 5/10 对外可见面。
- **信封 v1（DEC-42，已实现）**：事件 payload = `{"ver":1, "kind":32+evt_id, "t_ms", "wall_ms", <extra 扁平键值对 0…3 个>}`——extra：安全态迁移 = `{"state"}`（按 uid 路由 `…/<uid>/event`）；periph 插拔 = `{"uid", "pkind"}`（按 uid 路由）；功率预算拒绝 = `{"requested_ma", "used_ma", "budget_ma"}`（路由 `…/sys/event`）；遥测 payload = `{"ver":1, "kind":96, "dev", "value_u", "wall_ms"}`（原 M3a.2 的设备种类键 `"kind"` 让位信封 kind，改名 `"dev"`——破坏性变更随本批与消费端同步切换）。消费端（host/Agent）对未知 kind **透传存储不解析**（§0 前向兼容落点）；固件产生端只产注册表内 kind。
- 优先级映射（DEC-42，已实现，经 `ts_net_qos_t` 穿透 pubq→transport）：安全事件（estop/安全态迁移/越权）= zenoh congestion **BLOCK** + priority **REAL_TIME**；遥测/心跳/**periph 插拔与预算事件**（DEC-42 安全类集合之外的观测类，类属缺省）= 缺省（DROP + DATA）——参考 MatrixMechanic priority 位思想，用 zenoh 原生 QoS 承接（不自造位域）。

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
| CONFIG_TS_NET_LEASE_TTL_MS | 10000 | 租约 TTL（DEC-41：≈断链窗口×1.5+余量） |
| CONFIG_TS_NET_IDEM_CACHE | 4 | 幂等回执缓存深度（DEC-40） |

## 8. 测试要点

- L1：key 构造；退避表推进；linkmon 计数判定（含滞回）；**信封编解码（v1/v2 判别、rid 回带、幂等缓存命中/驱逐/操作不匹配、to 边界 5000/5001）**；**租约获取/续期/过期/代还/豁免命令**。——已实现（framework.net test_08/09）。
- L2：命令分发（权限/未知 key/回执码）；遥测合流与丢弃计数；**同 idem 重放不重执行（副作用计数=1，墙钟不变）**；**事件/遥测信封 ver/kind 断言 + QoS 类穿透（SAFETY→阻塞高优先级）**。——已实现（test_06/07/08）。
- L4：断链→SAFE_LINKLOSS→恢复全时序重放（虚拟时钟 + hb 注入）；DOWN 期发布丢弃计数进入 golden。
- L3（已达成 2026-09-23；DEC-40/41/42 批扩展为五验证点）：对 PC 侧 router 端到端——发现（hb + 遥测信封 ver=1/kind=96）/ 命令（v1 共存 + v2 rid 回带 + estop 令牌硬点）/ 幂等（同 idem 回放原回执、to=6000 拒绝）/ 租约全生命周期（续期同 id、他人获取/代还 -4、本人归还）/ 心跳保持与断链判定——复跑方法 dev-environment.md §8。

## 9. 未决依赖

- DEC-40/41/42 **已实现**（2026-09-23 实现批次：cmd.c 信封 v2 + idem LRU + lease.c + pub.c 信封 + QoS 穿透 + is_up 自省；twister 35 用例 / L5 6/6 / L3 五验证点全绿）。
- 遗留挂钩：M2b.2 = 写命令面（`ts_net_lease_held_by` 准入挂钩时机；sys 面只读族与 estop-clear 豁免已定）。
- DEC-20/22/26/27/30/40/41/42 已裁；v1 请求弃用期随下一 fw semver 次+1 收敛。

## 修订记录

- v0.3.6 · 2026-09-26：DEC-43——§5 pubq 互斥（push/flush 并发安全；flush 锁内出队 + 锁外发送防传输阻塞反压；锁序 write_lock → pubq 单向无环）。回归 framework.conc test_03 + 全量 13/13（54 用例）。
- v0.3.5 · 2026-09-25：impl-review-01 修复批（F-1/F-3/F-4）——§5 订阅扩至七类（periph 插拔/附着 + 功率预算拒绝归因外发，extra 扁平对 0…3 个）+ pubq 定容 128B（溯源见 §5）；§4.2 idem 回放判定置于 key/op 匹配后（跨 key 同 idem 拒绝）；§4.3 gated 按 suffix 回查回填 + sys_init 错误上抛。回归：twister 10/10（46 用例）/ L5 6/6 / pytest 全绿。
- v0.1 · 2026-09-20：首版草案。
- v0.2 · 2026-09-20：review-01——keyspace 补 hb/sys 构造器（DR-12）；§4 补 sys 命令面（DR-03，深化批次）。
- v0.2.1 · 2026-09-21：裁决同步——DEC-20/22/30 出处收敛（SC-02）。
- v0.3 · 2026-09-23：参考项目借鉴批次（owner 提供 NeuroLink/MatrixMechanic）——新增 §0 演进原则（fail-closed 不变 + ver/kind 信封演进）；§2 传输健康定义（zp 任务自省，M3a.2 短板收口）；§4.2 命令信封 v2〔Q-20〕；§4.4 kind 注册表；§4.5 控制租约〔Q-21〕；§5 事件/遥测信封与 zenoh QoS 映射〔Q-22〕；§7 Kconfig 增补；M3a.1/M3a.2/L3 实现状态对齐（§8）。
- v0.3.1 · 2026-09-23：裁决同步（DEC-40/41/42）——§4.2 增 zenoh 可靠性调研留档 + 命令面链路 TCP/TLS 约束 + to>5000ms 拒绝；提案标记全部转 DEC 出处；§9 实现批次定为 MA3 前。
- v0.3.4 · 2026-09-25：M3b——§4.4 增 kind 97（功率预算快照，pub_telem 附带 …/sys/power 记录）；get-budget 实装（§4.3 表语义兑现）。
- v0.3.3 · 2026-09-25：MA3.1 部署面落地——§4.3 增 app-*（gated）/get-app 行与 get-info 身份自报；cbor_min 增 bstr 解码（ts_cbor_bstr_ref）；CMD_TABLE 容量 12→16；CONFIG_TS_NET_APP_CHUNK_MAX（§7 同步）。
- v0.3.2 · 2026-09-23：**DEC-40/41/42 实现批次落地**——§2 缺省 locator udp→tcp（DEC-40 收敛）+ is_up 自省已实现；§4.2 idem 缓存实现细节（op 一致性防御/分发级拒绝不缓存/LRU 单调时钟）；§4.5 惰性过期/lease_id 单调/拒绝回执归因细节；§5 遥测键 `kind`→`dev` 改名（信封 kind 让位）+ QoS 已实现；§8 测试要点逐条标记实现状态 + L3 扩展五验证点。回归：twister 8/8（35 用例）/ L5 6/6 / pytest / L3 PASS。
