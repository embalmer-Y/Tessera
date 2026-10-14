/* SPDX-License-Identifier: Apache-2.0 */
/* ts-appmgr 内部共享（不对外）。 */
#ifndef TS_APPMGR_INTERNAL_H__
#define TS_APPMGR_INTERNAL_H__

#include <ts/appmgr.h>
#include <ts/tsap.h>
#include <stdbool.h>

/* 运行时 APP 状态（slot.c 定义，pkg.c 引用）——M6 起按 entry 索引
 * （current_apps[e]；legacy 单 APP 语义 = entry 0） */
extern ts_app_info_t current_apps[CONFIG_TS_APP_MAX_INSTANCES];
extern bool initialized;

/* verify.c（DEC-49）：全量验签（头 v2 → 摘要 → COSE ed25519）与 boot 快校验 */
ts_res_t ts_appmgr_verify_slot(uint8_t slot, const uint8_t root_pubkey[32],
			       tsap_view_t *v, uint8_t digest_out[32]);
ts_res_t ts_appmgr_check_digest(uint8_t slot, tsap_view_t *v);
const uint8_t *ts_appmgr_root_key(const uint8_t root_pubkey[32]);

/* ---- 资源档位（CG4 · Q-39②/Q-42 · LLD-ts-appmgr §5a）--------------------- */
#ifdef CONFIG_TS_APP_WAMR

/* manifest v2 tier/needs 扫描结果（ts_appmgr_scan_needs 填充） */
typedef struct {
	uint8_t tier;            /* 0=small（缺省）/1=large */
	bool has_needs;          /* needs 键出现（仅 large 合法） */
	uint32_t linear_memory_kb; /* 声明线性内存预算（0 = 未声明） */
	uint32_t stack_kb;         /* 声明栈预算（0 = 未声明；V1 记录不消费） */
	uint16_t resources;        /* 资源路径条数（fs 前缀需求面） */
} ts_app_needs_t;

/** manifest 键分发扫描：跳过非 tier/needs 键（ts_cbor_skip），仅提取档位
 * 声明。schema 纪律：tier ∈ {"small","large"}；needs 仅 large 可携
 *（small+needs = TS_E_PARAM）；needs 为 map{linear_memory_kb?, stack_kb?,
 * resources[]?}——resources 条目 = 绝对路径无 ".."（fs_paths 同文法）。
 * 任何结构/域值违例 = TS_E_PARAM（fail-closed，与 boot 走查同纪律）。 */
ts_res_t ts_appmgr_scan_needs(const uint8_t *man, uint32_t ml, ts_app_needs_t *out);

/** 安装期匹配矩阵（LLD §5a；stage_verify 验签后调用）：
 * ① needs.linear_memory_kb ≤ 设备线性内存帽（CONFIG_TS_APP_WAMR_HEAP 推导）
 * ② needs.resources>0 须 CONFIG_TS_HAL_FS
 * ③ tier=large 须设备支持（TS_APP_LOAD_MAX ≥ TS_APP_SIZE_GATE_LARGE）
 * 任一不满足 = TS_E_RANGE（安装期拒装替代运行期 OOM——Android
 * getMemoryClass 同型）。返回 TS_OK = 匹配通过。 */
ts_res_t ts_appmgr_needs_match(const ts_app_needs_t *n);

/** 档位取尺寸门（LLD §5a 双门；boot 装载与 Agent 编译链同值镜像） */
static inline uint32_t ts_app_tier_gate(uint8_t tier)
{
	return tier == 1 ? (uint32_t)CONFIG_TS_APP_SIZE_GATE_LARGE
			 : (uint32_t)CONFIG_TS_APP_SIZE_GATE_SMALL;
}

#endif /* CONFIG_TS_APP_WAMR */

#endif /* TS_APPMGR_INTERNAL_H__ */
