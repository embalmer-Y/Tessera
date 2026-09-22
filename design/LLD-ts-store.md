# LLD · ts-store v0.1 草案（DR-01 处置：新增模块）

> **状态**：v0.1 草案，随 design review-01 深化批次待 owner review。上位：HLD v0.2 §3（模块表）/§4.6；公共约定 `LLD-00-common.md`。
> **职责**：统一存储抽象——分区布局、掉电安全 meta（kv）、只读 provisioning（prov）、noinit 留痕区、APP slot 读写。此前散落各模块的"烧录配置/安全参数分区"引用全部收敛到本模块。
> **合同关联**：合同 10（安全参数不经运行时修改——prov 运行时只读是强制点）；DEC-05（slot/版本/回滚）、DEC-07（MCUmgr 底线）。

## 1. 内部结构

```text
src/store/
  part.c       分区表与后端抽象（native_sim 文件后端 / 真机 flash 后端）
  meta.c       掉电安全 kv（双副本 + 序号 + CRC）
  prov.c       provisioning 只读访问（schema v1，Q-11⑤）
  noinit.c     noinit 留痕（复位原因/WDT 报告）
```

## 2. 分区模型（布局随 Q-09 裁决定稿；本节为读写语义）〔DEC-23 已裁〕

```text
PROV（只读）｜ META_A/META_B（掉电安全 kv）｜ APP_SLOT_A/B ｜ NOINIT ｜ [AUDIT 预留，V1 不落盘 DR-07]
```

```c
typedef struct {
  uint32_t base, size;            /* 后端地址（native_sim = 文件内偏移） */
  enum { TS_PART_PROV, TS_PART_META, TS_PART_SLOT, TS_PART_NOINIT } kind;
} ts_store_part_t;
```

- 后端 ops：`{read, write, erase, is_erased}`；native_sim 实现为宿主文件（路径 `build/store/<part>.bin`，构建可重置）；真机为 flash 子系统。**上层（appmgr 等）不感知后端**。

## 3. 掉电安全 meta（meta.c）

```c
typedef struct { uint32_t seq; uint16_t len; uint16_t crc16; uint8_t data[META_MAX]; } ts_meta_rec_t;
ts_res_t ts_store_meta_write(const void *buf, uint16_t len);   /* 写非活动副本→校验回读→切换活动指针（原子） */
ts_res_t ts_store_meta_read (void *buf, uint16_t *len);        /* 活动副本；双副本皆坏 → TS_E_IO + 系统按缺省安全态启动 */
```

- 撕裂恢复：活动指针 = 序号较大且 CRC 通过者；两副本皆损 → 启动进 fail-safe 并留痕（TS_FAIL_SRC_STORE）。
- 消费者：ts-appmgr（active_slot/app_ver/rollback_count/boot_gen）。

## 4. provisioning（prov.c）——合同 10 的落点

```c
typedef struct {
  char     node_id[16], cube_id[16];      /* 命名空间前两段（DEC-02 预留 node 层） */
  char     router_locators[4][48];        /* zenoh locator 列表（Q-04） */
  uint8_t  root_pubkeys[2][32];           /* ed25519 根公钥（Q-05；双钥轮换预留） */
  char     zenoh_cred[96];                /* TLS/认证凭证（Q-04） */
  uint32_t power_budget_ma;               /* ts-power 预算 */
  uint8_t  estop_trigger_flags;           /* 触发沿等（DR-11） */
} ts_prov_t;                              /* 序列化 = CBOR，schema v1〔DEC-30⑤〕 */
ts_res_t ts_store_prov_load(void);        /* 启动一次：CRC 校验失败 → fail-safe（合同 6） */
const ts_prov_t *ts_store_prov(void);     /* [any] 只读指针；无写接口（写通道仅烧录期/测试构建注入） */
```

- **运行时无写路径**（L5 检查：prov.c 不含写调用，DR-01 处置的强制面）；轮换 = 烧录期重写 + 双 root_pubkeys 支持交接。

## 5. noinit（noinit.c）

```c
void ts_store_noinit_put(const void *rec, uint16_t len);   /* 复位前留痕（boot 失败原因/WDT 报告） */
ts_res_t ts_store_noinit_get(void *rec, uint16_t *len, bool *fresh);  /* 启动读取；fresh=false 表示上次异常复位 */
```

- 消费者：ts-core（boot/WDT 留痕，DR-17）；启动后首条遥测携带 `fresh` 标志（可观测）。

## 6. APP slot 读写

```c
ts_res_t ts_store_slot_write(uint8_t slot, uint32_t off, const void *buf, uint32_t len); /* 逐块写+回读校验 */
ts_res_t ts_store_slot_read (uint8_t slot, uint32_t off, void *buf, uint32_t len);
ts_res_t ts_store_slot_hash (uint8_t slot, uint8_t sha[32]);   /* 供安装校验 */
```

## 7. Kconfig（节选）

| 项 | 默认〔DEC-27〕 | 说明 |
|---|---|---|
| CONFIG_TS_STORE_META_MAX | 256B | meta 记录上限（appmgr 字段集） |

## 8. 测试要点

- L1：meta 撕裂注入（半写/CRC 错）→ 恢复或 fail-safe；后端读写边界。
- L2：prov CRC 失败 → 系统 fail-safe（合同 6 联动）；slot 写坏 → 安装失败路径。
- L5：prov.c 写调用零命中（机械检查新增目标，testing.md §3 扩展位）。
- L4：升级时序（S3）中的 meta 原子切换进入重放 golden。

## 9. 未决依赖

- DEC-20（locator/宿主）、DEC-21（根公钥体系）、DEC-23（分区布局）、DEC-27（META_MAX）、DEC-30⑤（CBOR schema v1）已裁；无未决。

## 修订记录

- v0.1 · 2026-09-20：首版（design review-01 DR-01/17 处置新增）。
- v0.1.1 · 2026-09-21：裁决同步——DEC-20/21/23/27/30 出处收敛（SC-02）。
- v0.2 · 2026-09-22：M2a 实现收敛留痕——① §2 native_sim 后端实现为 **RAM 静态数组 + 0xFF 抹除语义**（`ts_store_test_reset()` 模拟掉电后全新镜像；"宿主文件"跨进程持久化非 M2a 测试所需，留真实掉电场景一并接真机 flash 后端）；② §4 prov CBOR 解码 = **固定 schema 确定性子集实现**（definite-length 专用，任何超集拒绝——不引入通用 CBOR 依赖），schema v1 键序定稿：v/node_id/cube_id/routers/pk0/pk1/cred/pwr_ma/estop；③ 内部分区多字节整数 = **小端**（与 TSAP 容器大端互不相关，见 LLD-ts-appmgr §2）；④ noinit fresh 语义实现 = 读到有效留痕即 fresh=false。
