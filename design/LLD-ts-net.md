# LLD · ts-net v0.1 草案

> **状态**：v0.1 草案，随 LLD 批次待 owner review。上位：HLD §3.5；公共约定 `LLD-00-common.md`。
> **职责**：zenoh-pico 会话管理、命名空间构造、命令-回执分发、遥测/事件发布、心跳监视（断链判定）。
> **合同关联**：合同 3（断链 fail-safe 判定源）、8（本地独立生效——判定不依赖外部确认）、9（rx 串行化）。
> **外部依赖**：zenoh-pico（z_* 家族 API，具体签名以钉住版本为准，M0 核验）。

## 1. 内部结构

```text
src/net/
  session.c    会话建立/重连（client 角色〔DEC-20〕；native_sim 默认 udp/localhost〔DEC-27〕）
  keyspace.c   key 构造与资源映射（tessera/<node>/<cube>/…）
  cmd.c        query 服务端：命令分发表 + 回执
  pub.c        遥测/事件/心跳发布（缓冲与合流）
  linkmon.c    心跳监视 → ts_safety_set_link
```

## 2. 会话（session.c）

- 角色 client〔DEC-20；宿主修订 DEC-32〕：locator 来自 prov（router 地址；宿主 = **Linux PC** 或 ARM64 Linux 工业/机器人主板，Windows 移出）；重连退避固定表〔DEC-27：250/500/1000/2000ms 循环〕（确定性，禁指数抖动随机）。
- TLS：`Z_FEATURE_LINK_TLS` 显式开启〔DEC-20〕；证书/密钥只读自安全参数分区（合同 10）。
- 会话状态：DOWN/CONNECTED；迁移发布 `TS_EVT_NET_LINK_UP/DOWN`（观测用；**安全语义以 linkmon 为准**，避免双源）。

## 3. 命名空间构造（keyspace.c）

```c
int ts_net_key_cmd(char *buf, size_t n, const char *uid);     /* …/<class>/<inst>/cmd     */
int ts_net_key_tel(char *buf, size_t n, const char *uid);     /* …/<class>/<inst>/telemetry */
int ts_net_key_evt(char *buf, size_t n, const char *uid);     /* …/<class>/<inst>/event   */
int ts_net_key_hb  (char *buf, size_t n, bool host_dir);      /* …/sys/hb（cube→host）/ …/sys/hb-host（host→cube），DR-12 */
int ts_net_key_sys (char *buf, size_t n, const char *cmd);    /* …/sys/<cmd>（命令面见 §4，DR-03） */
/* 前缀 tessera/<node>/<cube> 由 node/cube id 配置拼装；node 段为 DEC-02 预留层（Q-07） */
```

- key 语法随 HLD §3.5 草案；语义变更 = 门 ③（fw semver X）。

## 4. 命令-回执（cmd.c）

- zenoh query 回调（ts_net_thread 上下文，串行）：`tessera/<node>/<cube>/**/cmd` → 解 CBOR `{op, args}` → 查**命令分发表**（各系统服务/ts-hal 实例注册，格式 `{key 后缀, fn, ctx}`）。
- 命令执行路径与 APP 一致（经 HAL/服务 → ts-safety）——**Agent 命令无豁免**（FOUNDING_PROMPT §6）。
- 回执：query response = `{status: ts_res_t, data: CBOR}`；框架不自动重试（重试属 Agent 侧语义），但命令超时上界须 < 断链检测上界〔DEC-22〕（文档级约束，写入 Agent 接口契约）。
- 未知 key → TS_E_NOTFOUND 回执（不留静默）。

**sys 命令面（v1，DR-03；授权 DEC-30①）**——注册者为框架自身，标记 `host_only`（APP 的 msg/net 能力文法不可达；host 侧命令通道授权由 prov 凭证保证）：

| key（…/sys/ 下） | 语义 |
|---|---|
| get-info | 固件版本/板/构建（`git describe`，versioning.md §5） |
| get-link / get-safety | 链路与通道安全态汇总（读 ts-safety shadow） |
| get-budget | 功率预算/用量（ts-power） |
| get-audit | 安全审计环形导出（含溢出丢弃计数，DR-07） |
| set-time | 设置墙钟（**仅数据字段**，合同 9；DR-08） |
| estop-clear | 清除 SAFE_FAULT（参数须带确认令牌 `confirm="estop"`；调用 ts_safety_clear_fault） |

## 5. 发布（pub.c）

- 遥测：实例值变化（commit 审计缓冲消费）与周期快照〔DEC-27： 200ms〕合流；缓冲深度〔DEC-27： 8〕满则丢最旧并计数（遥测尽力而为，不阻塞控制路径）。
- 事件：TS_EVT_* 选择性外发（estop 后补发、安全态迁移、越权留痕——合同 5/10 的对外可见面）。
- DOWN 状态下发布直接丢弃并计数（不排队重放——防上电风暴与不确定时序）。

## 6. 心跳监视（linkmon.c）——合同 3 判定源

- 发送：周期〔DEC-22：prov 可配，出厂默认 1000ms〕pub `…/sys/hb`；监视：host 侧 `…/sys/hb-host` 超过〔DEC-22：默认 6〕个周期未达 → `ts_safety_set_link(false)`（经 sysworkq 串行迁移）；恢复带滞回（连续〔DEC-27： 2〕个周期）才 `set_link(true)`。
- 判定完全本地（不依赖 router 确认自己的存在——合同 8）；输入/遥测方向不受 set_link 影响（合同 3）。
- 测试注入：`CONFIG_TS_TEST` 构建提供 hb 帧注入/抑制接口（L4 断链场景驱动）。

## 7. Kconfig（节选）

| 项 | 默认〔DEC-27〕 | 说明 |
|---|---|---|
| CONFIG_TS_NET_RECONNECT_TABLE_MS | "250,500,1000,2000" | 重连退避固定表 |
| CONFIG_TS_NET_TELEM_INTERVAL_MS | 200 | 周期快照 |
| CONFIG_TS_NET_TELEM_BUF | 8 | 发布缓冲 |

## 8. 测试要点

- L1：key 构造；退避表推进；linkmon 计数判定（含滞回）。
- L2：命令分发（权限/未知 key/回执码）；遥测合流与丢弃计数。
- L4：断链→SAFE_LINKLOSS→恢复全时序重放（虚拟时钟 + hb 注入）；DOWN 期发布丢弃计数进入 golden。
- L3（M3）：对 PC 侧 router 端到端（发现、命令、回执、心跳）。

## 9. 未决依赖

- DEC-20（拓扑/宿主）、DEC-22（心跳）、DEC-26（node 段预留，单立方体时 node = cube）、DEC-27（退避表/快照/缓冲）已裁；无未决。

## 修订记录

- v0.1 · 2026-09-20：首版草案。
- v0.2 · 2026-09-20：review-01——keyspace 补 hb/sys 构造器（DR-12）；§4 补 sys 命令面（DR-03，深化批次）。
- v0.2.1 · 2026-09-21：裁决同步——DEC-20/22/30 出处收敛（SC-02）。
