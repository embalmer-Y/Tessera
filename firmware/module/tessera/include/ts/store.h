/* SPDX-License-Identifier: Apache-2.0 */
/*
 * ts-store 公共 API（design/LLD-ts-store.md）：分区抽象 / 掉电安全 meta /
 * 只读 provisioning / noinit 留痕 / APP slot 读写。
 * 合同关联：合同 10（prov 运行时只读）、DEC-05/23（slot 与 meta）。
 * 内部存储分区多字节整数 = **小端**（Zephyr 本机序；与 TSAP 容器的大端互不相关）。
 */
#ifndef TS_STORE_H__
#define TS_STORE_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <ts/err.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- 分区模型（LLD-ts-store §2；DEC-23）-------------------------------- */

typedef enum {
	TS_PART_PROV,
	TS_PART_META,
	TS_PART_SLOT_A,
	TS_PART_SLOT_B,
	TS_PART_NOINIT,
	TS_PART_AUDIT, /* DEC-52①：审计 flash 环（8KB 两页乒乓；无此分区的板
			* 降级——audit init 留痕失败、内存环保留） */
	TS_PART_COUNT,
} ts_store_part_t;

/* 初始化：后端就绪 + prov 加载（CRC 失败 → TS_E_IO，调用方进 fail-safe，合同 6）
 * + noinit 读取。boot 表接线随 M2b（periph/hal 步骤一次到位，保持数组纯追加）。 */
ts_res_t ts_store_init(void);

/* ---- 掉电安全 meta（§3）：双副本 + 序号 + CRC16-CCITT -------------------- */

ts_res_t ts_store_meta_write(const void *buf, uint16_t len);
ts_res_t ts_store_meta_read(void *buf, uint16_t *len);

/* ---- provisioning（§4）：CBOR schema v1（DEC-30⑤），运行时只读 ------------- */

typedef struct {
	char node_id[16];
	char cube_id[16];
	char router_locators[4][48];
	uint8_t root_pubkeys[2][32];
	char zenoh_cred[96];
	uint32_t power_budget_ma;
	uint8_t estop_trigger_flags;
} ts_prov_t;

ts_res_t ts_store_prov_load(void);      /* init 期一次；失败 = TS_E_IO */
const ts_prov_t *ts_store_prov(void);   /* [any] 只读指针；无运行时写接口（合同 10） */

/* ---- noinit 留痕（§5）：复位原因 / WDT 报告 ------------------------------ */

void ts_store_noinit_put(const void *rec, uint16_t len);
ts_res_t ts_store_noinit_get(void *rec, uint16_t *len, bool *fresh);

/* ---- APP slot 读写（§6；逐块写 + 回读校验）------------------------------- */

ts_res_t ts_store_slot_write(uint8_t slot, uint32_t off, const void *buf, uint32_t len);
ts_res_t ts_store_slot_read(uint8_t slot, uint32_t off, void *buf, uint32_t len);
ts_res_t ts_store_slot_hash(uint8_t slot, uint8_t sha[32]);
/* 全 slot 抹除：安装序前置（flash 后端必须——物理只可 1→0；RAM 后端 = 0xFF
 * 复位，语义一致）。消费者 = ts-appmgr stage_begin（板级五新增，LLD §6 增补）。 */
ts_res_t ts_store_slot_erase(uint8_t slot);

/* ---- 审计 flash 环（DEC-52①；掉电留存安全事件）--------------------------- */

#ifdef CONFIG_TS_STORE_AUDIT
#include <ts/safety.h>

/* flash 槽解码形态（64B 定长槽的小端字段视图；evt 扩展字段在 store 域） */
typedef struct {
	uint64_t t_ms;
	uint32_t seq;
	uint16_t ch_idx; /* 0xFFFF = 系统事件（estop 等） */
	uint16_t actor;
	uint8_t kind;
	int32_t res;   /* ts_res_t（负值错误码——u8 会截断，V2-2 实测拦下） */
	uint16_t evt; /* 0 = commit 审计；1 = estop 沿触发 */
	uint32_t value_u;
} ts_store_audit_entry_t;

ts_res_t ts_store_audit_init(void);   /* 扫描两页恢复游标；分区缺失 = 留痕降级 */
/* 安全事件落盘（commit 异常〔res != TS_OK〕+ estop 沿）；写满翻页（擦对页） */
ts_res_t ts_store_audit_append(const ts_audit_entry_t *e, uint16_t evt);
/* 按 seq 升序读最近 max 条（跨两页过渡态 ≤128）；返回条数 */
size_t ts_store_audit_read(ts_store_audit_entry_t *out, size_t max);
void ts_store_audit_boot_report(void); /* boot 打印最近 8 条（人读留痕） */
#endif

/* ---- 测试钩子（仅 CONFIG_TS_TEST）---------------------------------------- */
#ifdef CONFIG_TS_TEST
/* 抹除全部后端存储（测试隔离：每用例套件 setup 调用） */
ts_res_t ts_store_test_reset(void);
/* prov 烧录通道注入（生产烧录 = 外部工具/Agent deploy_push_prov，MA3；合同 10：
 * prov.c 本体零写调用——本函数在 prov_test.c，L5 检查目标即 prov.c）。 */
ts_res_t ts_store_prov_write_test(const uint8_t *cbor, uint32_t len);
/* 主动破坏一份 meta 副本（撕裂注入） */
ts_res_t ts_store_meta_corrupt_test(uint8_t copy_idx);
#endif

#ifdef __cplusplus
}
#endif

#endif /* TS_STORE_H__ */
