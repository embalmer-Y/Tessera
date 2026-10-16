# LLD · ts-store v0.5.2

> **状态**：v0.5.2（2026-10-16 F3 · DEC-62①：**prov v2 第三尾键 lconf**〔12 对形态；0/1 域外 fail-closed；11 对缺省 0 = 存量零重刷〕——安装闸开关，消费方 LLD-ts-appmgr §5c）；v0.5.1（2026-10-15 EC2 · **信任表实现**——ts_trust.c 落地：trust_walk 确定性走查/乒乓写+回读校验/惰性装载/撕裂回退；分区 8KB〔2×4KB 擦除块对齐——sim-flash 实证 2KB 步距范围抹除被拒〕）；v0.5（2026-10-15 EC1 · Q-43/DEC-60：**信任根表分区**——ts_trust.c 8KB 双副本乒乓〔2×4KB 擦除块对齐〕+ TUF root 同型全量替换表 schema + TS_STORE_TRUST 可选分区〔默认 n = V0.7 等价〕）；v0.4.1（2026-10-14 CG2 · Q-42：**prov schema v2 实现**——v1/v2 双形态确定性解码〔9/11 对，键序 = v1 前缀 + 尾部追加〕+ v1 缺字段缺省〔orchestrated + estop 远程清除开放〕+ 域外值 fail-closed + 未装载兜底 enabled）。上位：HLD v0.2 §3（模块表）/§4.6；公共约定 `LLD-00-common.md`。
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

- 后端 ops：`{read, write, erase, erase_off, size}`；**RAM 后端**（默认，native_sim/CI：静态数组 + 0xFF 抹除语义）/ **flash 后端**（`CONFIG_TS_STORE_FLASH`：DT fixed-partitions〔ts_prov_part/ts_meta_part/ts_slot_a_part/ts_slot_b_part/ts_noinit_part〕+ flash_map；分区缺失/尺寸错配 = 构建期失败）双实现，**上层（appmgr 等）不感知后端**。
- flash 后端写对齐垫片（板级五）：逐 4B 字"读-比-写"——同值跳过（幂等重发）、位子集校验（越 erase 改写显式拦截，真机为静默 AND 损坏）、仅抹除态/可扩展字编程。块边界扩展写真机合法、sim-flash（EXPLICIT_ERASE 程序一次语义）拒绝——调用方约束为单次连续写或整槽 erase 后顺序写。

## 3. 掉电安全 meta（meta.c）

```c
typedef struct { uint32_t seq; uint16_t len; uint16_t crc16; uint8_t data[META_MAX]; } ts_meta_rec_t;
ts_res_t ts_store_meta_write(const void *buf, uint16_t len);   /* 写非活动副本→校验回读→切换活动指针（原子） */
ts_res_t ts_store_meta_read (void *buf, uint16_t *len);        /* 活动副本；双副本皆坏 → TS_E_IO + 系统按缺省安全态启动 */
```

- 撕裂恢复：活动指针 = 序号较大且 CRC 通过者；两副本皆损 → 启动进 fail-safe 并留痕（TS_FAIL_SRC_STORE）。**副本步距 = 分区尺寸/2**（RAM 512B / flash 4096B=擦除块对齐，板级五动态化）；flash 后端写前范围擦除目标副本（擦-写间撕裂 → 该副本损、另一副本完整）。
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
  /* —— schema v2（CG1 · DEC-56/57/Q-41）：部署模式与 estop 清除通道 —— */
  uint8_t  deploy_mode;                   /* 0=orchestrated（缺省）/1=standalone〔Q-41①〕 */
  uint8_t  estop_remote_clear;            /* 0=disabled/1=enabled；**v1 prov 缺字段 = enabled（现网兼容——无本地交互设备的唯一通道）**；有本地交互设备出厂 disabled〔Q-41③；LLD-ts-safety §5a〕 */
} ts_prov_t;                              /* 序列化 = CBOR，schema v1〔DEC-30⑤〕；v2 增字段（Q-42 呈递——门③） */
ts_res_t ts_store_prov_load(void);        /* 启动一次：CRC 校验失败 → fail-safe（合同 6） */
const ts_prov_t *ts_store_prov(void);     /* [any] 只读指针；无写接口（写通道仅烧录期/测试构建注入） */
```

- **运行时无写路径**（L5 检查：prov.c 不含写调用，DR-01 处置的强制面）；轮换 = 烧录期重写 + 双 root_pubkeys 支持交接。
- **v2 解码实现细节（CG2）**：`prov_walk` 收 9 对（v=1）/ 11 对（v=2）两形态，v 值与对数错配 = 结构损坏拒；v1 走查前置缺省（`deploy_mode=orchestrated`、`estop_remote_clear=1`——out 可能为脏 scratch）；`deploy_mode > 1` / `estop_remote_clear > 1` = TS_E_IO（未知值不静默归并，IR-10 同型）；未装载/装载失败的静态兜底 = 同 v1 缺省（estop_remote_clear enabled——测试构建常无 prov，装载失败生产板走 boot fail-safe）。烧录工具侧：agent/tools/flash_prov.py 产 v1/v2 双形态分区镜像（v2 字段显式给值才追加——旧固件兼容）。

## 4a. 信任根表（ts_trust.c）——V0.8.0 生态批（Q-43/DEC-60①③）

```c
#define TS_TRUST_KEYS_MAX   8   /* 开发者键上限（Q-43① 常量门值） */
typedef struct {
  uint32_t ver;                              /* 单调版本（严格 N+1 链——TUF root 同型） */
  uint8_t  n_keys;                           /* 0..TS_TRUST_KEYS_MAX（0 = 全撤回工厂根单源） */
  uint8_t  keys[TS_TRUST_KEYS_MAX][32];      /* ed25519 开发者公钥（全量替换语义） */
} ts_trust_table_t;
ts_res_t ts_store_trust_load(void);          /* 惰性装载：活动副本（seq 大且 CRC 过）→ RAM 表；
                                                无记录/分区未使能 = {ver=0, n_keys=0}（工厂根单源） */
const ts_trust_table_t *ts_store_trust(void);/* [any] 只读（装载由消费者首访触发——只读无写回面） */
ts_res_t ts_store_trust_validate(const uint8_t *cbor, uint32_t len, ts_trust_table_t *out);
                                             /* 确定性 schema 走查（与 load 同路径——单一事实源；
                                                prov.c rd_* 同型纪律） */
ts_res_t ts_store_trust_write(const uint8_t *cbor, uint32_t len);
                                             /* 校验→乒乓写（写非活动副本→回读校验→成为新活动）
                                                → RAM 表重载；**仅 trust-update 命令链调用**
                                                （签名/ver 门控在 ts-appmgr——本层只管持久化） */
```

- **表 CBOR schema（2 对定序键，无 revoked 列表）**：`map{"ver":uint32, "keys":[bstr(32)×0..8]}`——撤销 = 次版剔除（TUF root.json 全量替换；revoked 列表定长溢出 = 旧键复活面，全量替换根除——Q-43① 理由在册）。域外值/不定长/键内重复/超上限 = TS_E_IO fail-closed。
- **分区布局**：TS_PART_TRUST 8KB = 2×4KB 乒乓副本（flash 擦除块对齐——EC2 实施期 sim-flash 实证 2KB 步距范围抹除被拒）；记录 = `seq u32 | len u16 | crc16 u16 | CBOR`（§3 meta 同型 REC_HDR 8B + 撕裂安全：擦-写间掉电 → 旧副本完整）。表 CBOR ≤ CONFIG_TS_TRUST_TABLE_MAX（默认 512B；实际上限 270B 留余量）。Kconfig `TS_STORE_TRUST`（默认 n）+ flash 后端 DT `ts_trust_part`（BUILD_ASSERT 8192；缺节点 = 构建期失败——AUDIT/KV 同型）。**缺分区/未使能 = 工厂根单源 = V0.7 行为逐字节等价**（存量板零重刷）。
- **单调防回滚**：持久锚 = 活动副本 seq + 表内 ver（双记录；ver 严格 N+1 由 ts-appmgr trust-update 门控执行——重放/跳版均拒）。物理改写分区（脱机烧录）超威胁模型（同 MCUboot 无 TPM 假设——R9 §3）。

## 5. noinit（noinit.c）

```c
void ts_store_noinit_put(const void *rec, uint16_t len);   /* 复位前留痕（boot 失败原因/WDT 报告） */
ts_res_t ts_store_noinit_get(void *rec, uint16_t *len, bool *fresh);  /* 启动读取；fresh=false 表示上次异常复位 */
```

- 消费者：ts-core（boot/WDT 留痕，DR-17）；启动后首条遥测携带 `fresh` 标志（可观测）。**one-shot 读清**（板级五）：读到有效留痕后抹除分区——flash 持久介质上防陈旧留痕跨多次复位误报（RAM 后端同语义统一）。

## 6. APP slot 读写

```c
ts_res_t ts_store_slot_write(uint8_t slot, uint32_t off, const void *buf, uint32_t len); /* 逐块写+回读校验 */
ts_res_t ts_store_slot_read (uint8_t slot, uint32_t off, void *buf, uint32_t len);
ts_res_t ts_store_slot_hash (uint8_t slot, uint8_t sha[32]);   /* 供安装校验 */
ts_res_t ts_store_slot_erase(uint8_t slot);  /* 全槽抹除：安装序前置（板级五增补；
                                                flash 后端必须，RAM 后端语义一致；
                                                消费者 = ts-appmgr stage_begin） */
```

## 7. Kconfig（节选）

| 项 | 默认〔DEC-27〕 | 说明 |
|---|---|---|
| CONFIG_TS_STORE_META_MAX | 256B | meta 记录上限（appmgr 字段集） |
| CONFIG_TS_STORE_FLASH | n | flash 后端（板级五；依赖 FLASH_MAP + DT 五分区） |

## 8. 测试要点

- L1：meta 撕裂注入（半写/CRC 错）→ 恢复或 fail-safe；后端读写边界。
- L2：prov CRC 失败 → 系统 fail-safe（合同 6 联动）；slot 写坏 → 安装失败路径。
- L5：prov.c 写调用零命中（机械检查新增目标，testing.md §3 扩展位）。
- L4：升级时序（S3）中的 meta 原子切换进入重放 golden。

## 9. 未决依赖

- DEC-20（locator/宿主）、DEC-21（根公钥体系）、DEC-23（分区布局）、DEC-27（META_MAX）、DEC-30⑤（CBOR schema v1）已裁；无未决。

## 修订记录
- v0.5.2 · 2026-10-16：**F3（DEC-62①）**——prov v2 12 对形态：lconf 安装闸开关（缺省 0；域外 fail-closed）；store 用例矩阵扩展。
- v0.5.1 · 2026-10-15：**EC2（信任表实现）**——ts_trust.c + part.c 两后端 + TS_STORE_TRUST/TS_TRUST_TABLE_MAX Kconfig + prov.c rd_* 助手提炼 internal.h 共享（prov/trust 单一纪律）；用例 framework.store test_trust_table（schema 矩阵/roundtrip/乒乓/撕裂回退/双损哨兵——RAM+flash 双变体）。分区 4KB→8KB 实施修正（擦除块对齐——DEC-60 登记值随修）。
- v0.5 · 2026-10-15：**EC1（Q-43/DEC-60 · 信任根表设计）**——新增 §4a：ts_trust.c（表 CBOR 2 对定序键全量替换语义/8KB 双副本乒乓（2×4KB——EC2 实施期擦除块对齐定案）TS_STORE_TRUST 可选分区默认 n/单调 ver 防 TUF 同型）；用例面 = schema 矩阵 + 撕裂恢复（EC2 实施）。
- v0.4.1 · 2026-10-14：**CG2（Q-42 · prov schema v2 实现）**——§4 双形态解码 + 缺省/域外值/兜底语义（见 §4 实现细节条）；用例 framework.store test_prov_v2_fields（v2 字段/域外拒/v-pairs 错配拒）+ test_prov_ok 增 v1 缺省断言。
- v0.4 · 2026-10-14：CG1（Q-41/Q-39 · HLD-contract-v2 §7）——prov schema v2 增 `deploy_mode`（0=orchestrated 缺省/1=standalone——linkmon 模式守卫消费）与 `estop_remote_clear`（v1 缺字段 = enabled 现网兼容；有交互设备出厂 disabled）；槽池档位结构注（统一大槽 + 档位逻辑上限——实现随 CG4）。

- v0.1 · 2026-09-20：首版（design review-01 DR-01/17 处置新增）。
- v0.1.1 · 2026-09-21：裁决同步——DEC-20/21/23/27/30 出处收敛（SC-02）。
- v0.2 · 2026-09-22：M2a 实现收敛留痕——① §2 native_sim 后端实现为 **RAM 静态数组 + 0xFF 抹除语义**（`ts_store_test_reset()` 模拟掉电后全新镜像；"宿主文件"跨进程持久化非 M2a 测试所需，留真实掉电场景一并接真机 flash 后端）；② §4 prov CBOR 解码 = **固定 schema 确定性子集实现**（definite-length 专用，任何超集拒绝——不引入通用 CBOR 依赖），schema v1 键序定稿：v/node_id/cube_id/routers/pk0/pk1/cred/pwr_ma/estop；③ 内部分区多字节整数 = **小端**（与 TSAP 容器大端互不相关，见 LLD-ts-appmgr §2）；④ noinit fresh 语义实现 = 读到有效留痕即 fresh=false。
- v0.3 · 2026-09-28：板级五（flash 持久化，docs/board-persist-01.md）——① §2 flash 后端（CONFIG_TS_STORE_FLASH + DT 五分区 + flash_map + 写对齐垫片）与 ops 增 erase_off；② §3 副本步距 = 分区尺寸/2 + 写前范围擦除；③ §5 noinit one-shot 读清；④ §6 ts_store_slot_erase 公共 API 增补（消费者 stage_begin 安装前抹除）；⑤ prov 注入改一体单次连续写（程序一次纪律，prov.c 本体零写不变）；真机分区布局表见 board-persist-01 §1。
