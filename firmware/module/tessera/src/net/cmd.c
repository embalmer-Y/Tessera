/* SPDX-License-Identifier: Apache-2.0 */
/* 命令-回执分发（LLD-ts-net §4）。sys 命令面 host_only（DEC-30①/DR-03）——
 * 注册者 = 框架自身；APP 的 msg/net 能力文法不可达（M2b.2 msg 类前结构性
 * 隔离），host 侧通道授权由 prov 凭证保证。
 * 信封 v1/v2 共存（DEC-40，按首键判别："op" = v1 / "ver" = v2；v1 弃用期）：
 *   v1 请求 map{"op", "args"?}                → 回执 map{"status", "data"}
 *   v2 请求 map{"ver","kind","rid","src","op","args"?}（args 内 idem?/to?）
 *        → 回执 map{"ver","kind","rid"<回带>,"status","data"}
 * v2 语义：idem 命中 = 回放缓存回执不重执行（LRU，CONFIG_TS_NET_IDEM_CACHE）；
 * to > 5000ms = 拒绝（断链窗口 6000ms〔DEC-22〕− 余量）。未知键/超集/未知
 * kind = 显式拒绝回执（fail-closed，不留静默）。命令执行路径与 APP 一致
 * （无豁免：estop-clear 经 ts_safety_clear_fault，set-time 仅数据字段）。
 * 上下文：zenoh 回调线程或测试直调（分发串行），幂等缓存无锁。 */
#include <stdio.h>
#include <string.h>
#include <ts/appmgr.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/net.h>
#include <ts/power.h>
#include <ts/safety.h>
#include <ts/store.h>
#include <zephyr/kernel.h>
#include "internal.h"

#define CMD_TABLE_MAX  16 /* 7 基础 sys + 3 租约（DEC-41）+ 5 部署面（MA3.1）+ 余量 */
#define RESP_DATA_MAX  384 /* data 暂存上限（回执总预算 512 内扣除头） */
#define REQ_TO_MAX_MS  5000 /* 带内超时上界（DEC-40：断链窗口 6000 − 余量） */
#define RID_MAX        16
#define SRC_MAX        24
#define IDEM_KEY_MAX   16
#define IDEM_REPLY_MAX 512 /* = zenoh 回执预算（RESP_MAX），缓存回放原样字节 */
#define ARG_PAIRS_V1   3
#define ARG_PAIRS_V2   5

struct cmd_slot {
	const char *suffix; /* 如 "sys/get-info"（静态字面量，零拷贝） */
	ts_net_cmd_fn fn;
	bool gated; /* 写类（DEC-41）：仅 v2 信封 + 租约持有者 = src 可执行 */
	bool used;
};
static struct cmd_slot table[CMD_TABLE_MAX];

/* ---- sys 命令实现（§4 表）----------------------------------------------- */

static ts_res_t cmd_get_info(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	/* 身份自报（MA3.1：通配发现的回执 key 为查询通配形态，身份以载荷为准）：
	 * 自 ts_net_prefix 提取 node/cube 两段。 */
	char node[24] = "";
	char cube[24] = "";
	size_t plen = strlen(ts_net_prefix);

	if (plen > 8 && strncmp(ts_net_prefix, "tessera/", 8) == 0) {
		size_t c1 = 8, c1e = c1, c2, c2e;

		while (c1e < plen && ts_net_prefix[c1e] != '/') {
			c1e++;
		}
		c2 = c1e + 1;
		c2e = c2;
		while (c2e < plen && ts_net_prefix[c2e] != '/') {
			c2e++;
		}
		size_t nl = c1e - c1;
		size_t cl = (c2e > c2) ? (c2e - c2) : (plen - c2);

		if (nl < sizeof(node) && cl < sizeof(cube)) {
			memcpy(node, ts_net_prefix + c1, nl);
			memcpy(cube, ts_net_prefix + c2, cl);
		}
	}
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 5) ||
	    !ts_cbor_put_tstr(r, cap, &p, "fw") ||
	    !ts_cbor_put_tstr(r, cap, &p, CONFIG_TS_FW_VERSION) ||
	    !ts_cbor_put_tstr(r, cap, &p, "board") ||
	    !ts_cbor_put_tstr(r, cap, &p, CONFIG_BOARD) ||
	    !ts_cbor_put_tstr(r, cap, &p, "node") ||
	    !ts_cbor_put_tstr(r, cap, &p, node) ||
	    !ts_cbor_put_tstr(r, cap, &p, "cube") ||
	    !ts_cbor_put_tstr(r, cap, &p, cube) ||
	    !ts_cbor_put_tstr(r, cap, &p, "wall_ms") ||
	    !ts_cbor_put_uint(r, cap, &p, ts_time_wall_ms())) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_get_link(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 4) ||
	    !ts_cbor_put_tstr(r, cap, &p, "state") ||
	    !ts_cbor_put_uint(r, cap, &p, ts_net_state()) ||
	    !ts_cbor_put_tstr(r, cap, &p, "link_up") ||
	    !ts_cbor_put_bool(r, cap, &p, ts_net_link_up()) ||
	    !ts_cbor_put_tstr(r, cap, &p, "hb_seq") ||
	    !ts_cbor_put_uint(r, cap, &p, ts_net_linkmon_hb_seq()) ||
	    !ts_cbor_put_tstr(r, cap, &p, "pubq_dropped") ||
	    !ts_cbor_put_uint(r, cap, &p, ts_net_pubq_dropped())) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_get_safety(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	ts_safety_summary_t s;

	if (ts_safety_summary(&s) != TS_OK) {
		return TS_E_IO;
	}
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 5) ||
	    !ts_cbor_put_tstr(r, cap, &p, "channels") ||
	    !ts_cbor_put_uint(r, cap, &p, s.channels) ||
	    !ts_cbor_put_tstr(r, cap, &p, "poweron") ||
	    !ts_cbor_put_uint(r, cap, &p, s.by_state[TS_ST_SAFE_POWERON]) ||
	    !ts_cbor_put_tstr(r, cap, &p, "active") ||
	    !ts_cbor_put_uint(r, cap, &p, s.by_state[TS_ST_ACTIVE]) ||
	    !ts_cbor_put_tstr(r, cap, &p, "linkloss") ||
	    !ts_cbor_put_uint(r, cap, &p, s.by_state[TS_ST_SAFE_LINKLOSS]) ||
	    !ts_cbor_put_tstr(r, cap, &p, "fault") ||
	    !ts_cbor_put_uint(r, cap, &p, s.by_state[TS_ST_SAFE_FAULT])) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_get_budget(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	/* ts-power 预算快照（M3b 实装；LLD-ts-power §3——prov 只读总额） */
	ARG_UNUSED(a);
	size_t p = 0;
#ifdef CONFIG_TS_POWER
	ts_power_budget_t b;

	ts_power_budget_snapshot(&b);
	if (!ts_cbor_put_map(r, cap, &p, 4) ||
	    !ts_cbor_put_tstr(r, cap, &p, "budget_ma") ||
	    !ts_cbor_put_uint(r, cap, &p, b.budget_ma) ||
	    !ts_cbor_put_tstr(r, cap, &p, "used_ma") ||
	    !ts_cbor_put_uint(r, cap, &p, b.used_ma) ||
	    !ts_cbor_put_tstr(r, cap, &p, "peak_ma") ||
	    !ts_cbor_put_uint(r, cap, &p, b.peak_ma) ||
	    !ts_cbor_put_tstr(r, cap, &p, "slots") ||
	    !ts_cbor_put_uint(r, cap, &p, b.slots)) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
#else
	if (!ts_cbor_put_map(r, cap, &p, 1) ||
	    !ts_cbor_put_tstr(r, cap, &p, "note") ||
	    !ts_cbor_put_tstr(r, cap, &p, "ts-power disabled")) {
		return TS_E_IO;
	}
	*n = p;
	return TS_E_NOTFOUND;
#endif
}

#define AUDIT_EXPORT_MAX 6 /* DR-07：单次导出条数上限（回执定容内最坏编码预算） */

static ts_res_t cmd_get_audit(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	static ts_audit_entry_t entries[AUDIT_EXPORT_MAX];
	size_t got = ts_safety_audit_copy(entries, AUDIT_EXPORT_MAX);

	/* 回执预算不足 = TS_E_IO（调用方可分片；V1 定容 512B × 16 条紧凑编码） */
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 2) ||
	    !ts_cbor_put_tstr(r, cap, &p, "dropped") ||
	    !ts_cbor_put_uint(r, cap, &p, ts_safety_audit_dropped()) ||
	    !ts_cbor_put_tstr(r, cap, &p, "entries") ||
	    !ts_cbor_put_array(r, cap, &p, (uint32_t)got)) {
		return TS_E_IO;
	}
	for (size_t i = 0; i < got; i++) {
		const ts_audit_entry_t *e = &entries[i];

		if (!ts_cbor_put_array(r, cap, &p, 6) ||
		    !ts_cbor_put_uint(r, cap, &p, e->t_ms) ||
		    !ts_cbor_put_int(r, cap, &p, e->res) ||
		    !ts_cbor_put_uint(r, cap, &p, e->ch_idx) ||
		    !ts_cbor_put_uint(r, cap, &p, e->kind) ||
		    !ts_cbor_put_uint(r, cap, &p, e->actor) ||
		    !ts_cbor_put_uint(r, cap, &p, e->value_u)) {
			return TS_E_IO;
		}
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_set_time(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	/* DR-08：仅数据字段（ts_time_wall_set）；控制路径不受影响（合同 9） */
	size_t p = 0;

	if (!a->has_time_ms) {
		if (ts_cbor_put_map(r, cap, &p, 1) && ts_cbor_put_tstr(r, cap, &p, "need") &&
		    ts_cbor_put_tstr(r, cap, &p, "time_ms")) {
			*n = p;
		}
		return TS_E_PARAM;
	}
	ts_time_wall_set(a->time_ms);
	if (!ts_cbor_put_map(r, cap, &p, 1) ||
	    !ts_cbor_put_tstr(r, cap, &p, "wall_ms") ||
	    !ts_cbor_put_uint(r, cap, &p, ts_time_wall_ms())) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_estop_clear(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	/* 确认令牌硬点（DEC-30①）：confirm != "estop" → 拒绝（防误触） */
	size_t p = 0;

	if (strcmp(a->confirm, "estop") != 0) {
		if (ts_cbor_put_map(r, cap, &p, 1) && ts_cbor_put_tstr(r, cap, &p, "need") &&
		    ts_cbor_put_tstr(r, cap, &p, "confirm=estop")) {
			*n = p;
		}
		return TS_E_PARAM;
	}
	ts_res_t res = ts_safety_clear_fault();

	if (!ts_cbor_put_map(r, cap, &p, 1) ||
	    !ts_cbor_put_tstr(r, cap, &p, "cleared") ||
	    !ts_cbor_put_bool(r, cap, &p, res == TS_OK)) {
		return TS_E_IO;
	}
	*n = p;
	return res;
}

/* ---- sys 命令实现：控制租约（DEC-41，LLD §4.5）-------------------------- */

static ts_res_t cmd_lease_acquire(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	size_t p = 0;

	if (!a->has_holder || a->holder[0] == '\0') {
		if (ts_cbor_put_map(r, cap, &p, 1) && ts_cbor_put_tstr(r, cap, &p, "need") &&
		    ts_cbor_put_tstr(r, cap, &p, "holder")) {
			*n = p;
		}
		return TS_E_PARAM;
	}
	uint64_t now = ts_time_ms();
	uint32_t id = 0;
	uint64_t exp = 0;
	ts_res_t res = ts_net_lease_acquire(a->holder, now, &id, &exp);

	if (res == TS_OK) {
		if (!ts_cbor_put_map(r, cap, &p, 2) ||
		    !ts_cbor_put_tstr(r, cap, &p, "lease_id") ||
		    !ts_cbor_put_uint(r, cap, &p, id) ||
		    !ts_cbor_put_tstr(r, cap, &p, "expires_at_ms") ||
		    !ts_cbor_put_uint(r, cap, &p, exp)) {
			return TS_E_IO;
		}
	} else if (res == TS_E_STATE) {
		/* 他人持有：回填当前租约供调用方归因（同信任域 host 面） */
		char cur[TS_NET_LEASE_HOLDER_MAX];
		uint32_t cid = 0;
		uint64_t cexp = 0;

		ts_net_lease_get(now, NULL, cur, sizeof(cur), &cid, &cexp);
		if (!ts_cbor_put_map(r, cap, &p, 3) ||
		    !ts_cbor_put_tstr(r, cap, &p, "holder") ||
		    !ts_cbor_put_tstr(r, cap, &p, cur) ||
		    !ts_cbor_put_tstr(r, cap, &p, "lease_id") ||
		    !ts_cbor_put_uint(r, cap, &p, cid) ||
		    !ts_cbor_put_tstr(r, cap, &p, "expires_at_ms") ||
		    !ts_cbor_put_uint(r, cap, &p, cexp)) {
			return TS_E_IO;
		}
	} else {
		return res;
	}
	*n = p;
	return res;
}

static ts_res_t cmd_lease_release(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	size_t p = 0;

	if (!a->has_holder || a->holder[0] == '\0') {
		if (ts_cbor_put_map(r, cap, &p, 1) && ts_cbor_put_tstr(r, cap, &p, "need") &&
		    ts_cbor_put_tstr(r, cap, &p, "holder")) {
			*n = p;
		}
		return TS_E_PARAM;
	}
	ts_res_t res = ts_net_lease_release(a->holder, ts_time_ms());

	if (res == TS_E_STATE) {
		char cur[TS_NET_LEASE_HOLDER_MAX];

		ts_net_lease_get(ts_time_ms(), NULL, cur, sizeof(cur), NULL, NULL);
		if (!ts_cbor_put_map(r, cap, &p, 2) ||
		    !ts_cbor_put_tstr(r, cap, &p, "released") ||
		    !ts_cbor_put_bool(r, cap, &p, false) ||
		    !ts_cbor_put_tstr(r, cap, &p, "holder") ||
		    !ts_cbor_put_tstr(r, cap, &p, cur)) {
			return TS_E_IO;
		}
	} else if (!ts_cbor_put_map(r, cap, &p, 1) ||
		   !ts_cbor_put_tstr(r, cap, &p, "released") ||
		   !ts_cbor_put_bool(r, cap, &p, res == TS_OK)) {
		return TS_E_IO;
	}
	*n = p;
	return res;
}

static ts_res_t cmd_lease_get(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	uint64_t now = ts_time_ms();
	bool valid = false;
	char holder[TS_NET_LEASE_HOLDER_MAX];
	uint32_t id = 0;
	uint64_t exp = 0;

	ts_net_lease_get(now, &valid, holder, sizeof(holder), &id, &exp);
	size_t p = 0;

	if (valid) {
		if (!ts_cbor_put_map(r, cap, &p, 4) ||
		    !ts_cbor_put_tstr(r, cap, &p, "valid") ||
		    !ts_cbor_put_bool(r, cap, &p, true) ||
		    !ts_cbor_put_tstr(r, cap, &p, "holder") ||
		    !ts_cbor_put_tstr(r, cap, &p, holder) ||
		    !ts_cbor_put_tstr(r, cap, &p, "lease_id") ||
		    !ts_cbor_put_uint(r, cap, &p, id) ||
		    !ts_cbor_put_tstr(r, cap, &p, "expires_at_ms") ||
		    !ts_cbor_put_uint(r, cap, &p, exp)) {
			return TS_E_IO;
		}
	} else if (!ts_cbor_put_map(r, cap, &p, 1) ||
		   !ts_cbor_put_tstr(r, cap, &p, "valid") ||
		   !ts_cbor_put_bool(r, cap, &p, false)) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

/* ---- sys 命令实现：远程部署面（MA3.1，LLD-A06 §3；gated = v2+租约）------ */

static ts_res_t cmd_app_begin(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	size_t p = 0;

	if (!a->has_total) {
		if (ts_cbor_put_map(r, cap, &p, 1) && ts_cbor_put_tstr(r, cap, &p, "need") &&
		    ts_cbor_put_tstr(r, cap, &p, "total")) {
			*n = p;
		}
		return TS_E_PARAM;
	}
	uint8_t slot = 0;
	ts_res_t res = ts_appmgr_stage_begin(a->total, &slot);

	if (res != TS_OK) {
		return res; /* 尺寸非法：PARAM（data 空，status 已达） */
	}
	if (!ts_cbor_put_map(r, cap, &p, 2) ||
	    !ts_cbor_put_tstr(r, cap, &p, "slot") ||
	    !ts_cbor_put_uint(r, cap, &p, slot) ||
	    !ts_cbor_put_tstr(r, cap, &p, "total") ||
	    !ts_cbor_put_uint(r, cap, &p, a->total)) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_app_chunk(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	size_t p = 0;

	if (!a->has_offset || a->chunk == NULL || a->chunk_len == 0) {
		if (ts_cbor_put_map(r, cap, &p, 1) && ts_cbor_put_tstr(r, cap, &p, "need") &&
		    ts_cbor_put_tstr(r, cap, &p, "offset+data")) {
			*n = p;
		}
		return TS_E_PARAM;
	}
	uint32_t hw = 0;
	ts_res_t res = ts_appmgr_stage_chunk(a->offset, a->chunk, a->chunk_len, &hw);

	if (res != TS_OK) {
		return res;
	}
	if (!ts_cbor_put_map(r, cap, &p, 2) ||
	    !ts_cbor_put_tstr(r, cap, &p, "written") ||
	    !ts_cbor_put_uint(r, cap, &p, a->chunk_len) ||
	    !ts_cbor_put_tstr(r, cap, &p, "high_water") ||
	    !ts_cbor_put_uint(r, cap, &p, hw)) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_app_verify(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	/* 根公钥自 prov（合同 10 只读面；pk0 = 首根钥） */
	const ts_prov_t *prov = ts_store_prov();
	uint32_t ml = 0, wl = 0, co = 0;
	ts_res_t res = ts_appmgr_stage_verify(prov->root_pubkeys[0], &ml, &wl, &co);

	if (res != TS_OK) {
		return res;
	}
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 3) ||
	    !ts_cbor_put_tstr(r, cap, &p, "manifest_len") ||
	    !ts_cbor_put_uint(r, cap, &p, ml) ||
	    !ts_cbor_put_tstr(r, cap, &p, "wasm_len") ||
	    !ts_cbor_put_uint(r, cap, &p, wl) ||
	    !ts_cbor_put_tstr(r, cap, &p, "cose_off") ||
	    !ts_cbor_put_uint(r, cap, &p, co)) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_app_activate(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	ts_app_info_t info;
	ts_res_t res = ts_appmgr_stage_activate(&info);

	if (res != TS_OK) {
		return res;
	}
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 3) ||
	    !ts_cbor_put_tstr(r, cap, &p, "state") ||
	    !ts_cbor_put_uint(r, cap, &p, (uint64_t)info.state) ||
	    !ts_cbor_put_tstr(r, cap, &p, "active_slot") ||
	    !ts_cbor_put_uint(r, cap, &p, info.active_slot) ||
	    !ts_cbor_put_tstr(r, cap, &p, "rollback_count") ||
	    !ts_cbor_put_uint(r, cap, &p, info.rollback_count)) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

static ts_res_t cmd_get_app(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	ts_app_info_t info;
	ts_res_t res = ts_appmgr_get_info(&info);

	if (res != TS_OK) {
		return res;
	}
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 4) ||
	    !ts_cbor_put_tstr(r, cap, &p, "state") ||
	    !ts_cbor_put_uint(r, cap, &p, (uint64_t)info.state) ||
	    !ts_cbor_put_tstr(r, cap, &p, "active_slot") ||
	    !ts_cbor_put_uint(r, cap, &p, info.active_slot) ||
	    !ts_cbor_put_tstr(r, cap, &p, "rollback_count") ||
	    !ts_cbor_put_uint(r, cap, &p, info.rollback_count) ||
	    !ts_cbor_put_tstr(r, cap, &p, "app_id") ||
	    !ts_cbor_put_tstr(r, cap, &p, info.app_id[0] != '\0' ? info.app_id : "")) {
		return TS_E_IO;
	}
	*n = p;
	return TS_OK;
}

/* ---- 注册与分发 ---------------------------------------------------------- */

ts_res_t ts_net_cmd_register(const char *suffix, ts_net_cmd_fn fn)
{
	if (suffix == NULL || suffix[0] == '\0' || fn == NULL) {
		return TS_E_PARAM;
	}
	for (int i = 0; i < CMD_TABLE_MAX; i++) {
		if (table[i].used && strcmp(table[i].suffix, suffix) == 0) {
			return TS_E_PARAM; /* 撞名 */
		}
	}
	for (int i = 0; i < CMD_TABLE_MAX; i++) {
		if (!table[i].used) {
			table[i].suffix = suffix;
			table[i].fn = fn;
			table[i].gated = false; /* 公共注册面 = 未门控（gated 属 sys 内部装配） */
			table[i].used = true;
			return TS_OK;
		}
	}
	return TS_E_NOMEM;
}

static struct cmd_slot *find_cmd(const char *suffix)
{
	for (int i = 0; i < CMD_TABLE_MAX; i++) {
		if (table[i].used && strcmp(table[i].suffix, suffix) == 0) {
			return &table[i];
		}
	}
	return NULL;
}

/* ---- 请求解析（v1/v2 统一体；fail-closed：未知键/超集/重复键 = 拒绝）----- */

struct req_env {
	bool v2;
	char rid[RID_MAX + 1];
	char src[SRC_MAX + 1]; /* 进审计 payload 的调用方身份（DEC-40） */
	char op[24];
	ts_net_cmd_args_t args;
	bool has_idem;
	char idem[IDEM_KEY_MAX + 1];
	bool has_to;
	uint32_t to_ms;
};

/* args 体公共键（confirm/time_ms/holder）；idem/to 仅 v2 信封（DEC-40） */
static bool parse_args_body(ts_cbor_rd_t *r, uint32_t pairs, struct req_env *e)
{
	for (uint32_t j = 0; j < pairs; j++) {
		char akey[12];

		if (!ts_cbor_tstr(r, akey, sizeof(akey))) {
			return false;
		}
		if (strcmp(akey, "confirm") == 0) {
			if (!ts_cbor_tstr(r, e->args.confirm, sizeof(e->args.confirm))) {
				return false;
			}
		} else if (strcmp(akey, "time_ms") == 0) {
			uint64_t v;

			if (!ts_cbor_uint(r, &v)) {
				return false;
			}
			e->args.time_ms = v;
			e->args.has_time_ms = true;
		} else if (strcmp(akey, "holder") == 0) {
			if (!ts_cbor_tstr(r, e->args.holder, sizeof(e->args.holder))) {
				return false;
			}
			e->args.has_holder = true;
		} else if (e->v2 && strcmp(akey, "total") == 0) {
			uint64_t v;

			if (!ts_cbor_uint(r, &v) || v > UINT32_MAX) {
				return false;
			}
			e->args.total = (uint32_t)v;
			e->args.has_total = true;
		} else if (e->v2 && strcmp(akey, "offset") == 0) {
			uint64_t v;

			if (!ts_cbor_uint(r, &v) || v > UINT32_MAX) {
				return false;
			}
			e->args.offset = (uint32_t)v;
			e->args.has_offset = true;
		} else if (e->v2 && strcmp(akey, "data") == 0) {
			/* bstr 零拷贝引用（生存期 = 分发调用域）；块长上限 =
			 * CONFIG_TS_NET_APP_CHUNK_MAX（LLD-A06 §3：默认 2048/上限 4096） */
			if (!ts_cbor_bstr_ref(r, &e->args.chunk, &e->args.chunk_len) ||
			    e->args.chunk_len > CONFIG_TS_NET_APP_CHUNK_MAX) {
				return false;
			}
		} else if (e->v2 && strcmp(akey, "idem") == 0) {
			if (!ts_cbor_tstr(r, e->idem, sizeof(e->idem))) {
				return false;
			}
			e->has_idem = true;
		} else if (e->v2 && strcmp(akey, "to") == 0) {
			uint64_t v;

			if (!ts_cbor_uint(r, &v) || v > UINT32_MAX) {
				return false;
			}
			e->to_ms = (uint32_t)v;
			e->has_to = true;
		} else {
			return false; /* 未知参数/v1 带 v2 键 = 拒绝 */
		}
	}
	return true;
}

/* 首键判别（DEC-40）："op" = v1 map{op, args?}；"ver" = v2 信封。
 * v2 必含 ver/kind/rid/src/op（args 可选）；kind 仅接受 1（sys 命令请求，
 * LLD §4.4 注册表）；ver 仅接受 1（未来版本 = fail-closed）。 */
static ts_res_t parse_req(const uint8_t *req, uint32_t req_len, struct req_env *e)
{
	ts_cbor_rd_t r;
	uint32_t pairs;

	ts_cbor_rd_init(&r, req, req_len);
	memset(e, 0, sizeof(*e));
	if (!ts_cbor_map_open(&r, &pairs) || pairs == 0) {
		return TS_E_PARAM;
	}
	char first[8];

	if (!ts_cbor_tstr(&r, first, sizeof(first))) {
		return TS_E_PARAM;
	}
	if (strcmp(first, "op") == 0) {
		e->v2 = false;
		if (pairs > 2) {
			return TS_E_PARAM;
		}
		if (!ts_cbor_tstr(&r, e->op, sizeof(e->op))) {
			return TS_E_PARAM;
		}
		if (pairs == 2) {
			char key[8];

			if (!ts_cbor_tstr(&r, key, sizeof(key)) || strcmp(key, "args") != 0 ||
			    !ts_cbor_map_open(&r, &pairs) || pairs > ARG_PAIRS_V1 ||
			    !parse_args_body(&r, pairs, e)) {
				return TS_E_PARAM;
			}
		}
		return TS_OK;
	}
	if (strcmp(first, "ver") != 0) {
		return TS_E_PARAM; /* 未知首键 = 非法形态 */
	}
	e->v2 = true;
	if (pairs > 6) {
		return TS_E_PARAM;
	}
	uint64_t ver = 0;

	if (!ts_cbor_uint(&r, &ver) || ver != 1) {
		return TS_E_PARAM;
	}
	bool have_kind = false, have_rid = false, have_src = false, have_op = false;
	bool have_args = false;

	for (uint32_t i = 1; i < pairs; i++) {
		char key[8];

		if (!ts_cbor_tstr(&r, key, sizeof(key))) {
			return TS_E_PARAM;
		}
		if (strcmp(key, "kind") == 0) {
			uint64_t v;

			if (have_kind || !ts_cbor_uint(&r, &v)) {
				return TS_E_PARAM;
			}
			have_kind = true;
			if (v != 1) {
				return TS_E_PARAM;
			}
		} else if (strcmp(key, "rid") == 0) {
			if (have_rid || !ts_cbor_tstr(&r, e->rid, sizeof(e->rid))) {
				return TS_E_PARAM;
			}
			have_rid = true;
		} else if (strcmp(key, "src") == 0) {
			if (have_src || !ts_cbor_tstr(&r, e->src, sizeof(e->src))) {
				return TS_E_PARAM;
			}
			have_src = true;
		} else if (strcmp(key, "op") == 0) {
			if (have_op || !ts_cbor_tstr(&r, e->op, sizeof(e->op))) {
				return TS_E_PARAM;
			}
			have_op = true;
		} else if (strcmp(key, "args") == 0) {
			if (have_args || !ts_cbor_map_open(&r, &pairs) ||
			    pairs > ARG_PAIRS_V2 || !parse_args_body(&r, pairs, e)) {
				return TS_E_PARAM;
			}
			have_args = true;
		} else {
			return TS_E_PARAM; /* 未知信封键 = 拒绝 */
		}
	}
	if (!have_kind || !have_rid || !have_src || !have_op) {
		return TS_E_PARAM;
	}
	return TS_OK;
}

/* ---- 幂等回执缓存（DEC-40：同 idem 重发 = 回放不重执行）------------------ */

struct idem_slot {
	bool used;
	uint64_t stamp; /* LRU 时钟（单调，非墙钟——合同 9） */
	char idem[IDEM_KEY_MAX + 1];
	char op[24];
	ts_res_t status;
	size_t rlen;
	uint8_t reply[IDEM_REPLY_MAX];
};
static struct idem_slot idem_cache[CONFIG_TS_NET_IDEM_CACHE];
static uint64_t idem_clock;

static struct idem_slot *idem_find(const char *idem_key)
{
	for (int i = 0; i < CONFIG_TS_NET_IDEM_CACHE; i++) {
		if (idem_cache[i].used && strcmp(idem_cache[i].idem, idem_key) == 0) {
			return &idem_cache[i];
		}
	}
	return NULL;
}

static void idem_insert(const struct req_env *e, const uint8_t *reply, size_t rlen,
			ts_res_t status)
{
	if (rlen > IDEM_REPLY_MAX) {
		return; /* 防御：回执预算即 512，不可达分支 */
	}
	struct idem_slot *s = NULL;

	for (int i = 0; i < CONFIG_TS_NET_IDEM_CACHE; i++) {
		if (!idem_cache[i].used) {
			s = &idem_cache[i];
			break;
		}
	}
	if (s == NULL) { /* 满则驱逐最旧（定容 LRU） */
		s = &idem_cache[0];
		for (int i = 1; i < CONFIG_TS_NET_IDEM_CACHE; i++) {
			if (idem_cache[i].stamp < s->stamp) {
				s = &idem_cache[i];
			}
		}
	}
	s->used = true;
	strcpy(s->idem, e->idem);
	strcpy(s->op, e->op);
	s->status = status;
	memcpy(s->reply, reply, rlen);
	s->rlen = rlen;
	s->stamp = ++idem_clock;
}

/* ---- 回执编码（v1 两对 / v2 五对信封，rid 回带）-------------------------- */

/* 兜底：data = map{"error": tstr}（status 已定）；v2 加信封头（rid 可能空） */
static ts_res_t encode_err(uint8_t *resp, size_t cap, size_t *resp_len, const struct req_env *e,
			   ts_res_t status, const char *note)
{
	size_t p = 0;
	bool ok;

	if (e->v2) {
		ok = ts_cbor_put_map(resp, cap, &p, 5) &&
		     ts_cbor_put_tstr(resp, cap, &p, "ver") &&
		     ts_cbor_put_uint(resp, cap, &p, 1) &&
		     ts_cbor_put_tstr(resp, cap, &p, "kind") &&
		     ts_cbor_put_uint(resp, cap, &p, 16) &&
		     ts_cbor_put_tstr(resp, cap, &p, "rid") &&
		     ts_cbor_put_tstr(resp, cap, &p, e->rid) &&
		     ts_cbor_put_tstr(resp, cap, &p, "status") &&
		     ts_cbor_put_int(resp, cap, &p, status);
	} else {
		ok = ts_cbor_put_map(resp, cap, &p, 2) &&
		     ts_cbor_put_tstr(resp, cap, &p, "status") &&
		     ts_cbor_put_int(resp, cap, &p, status);
	}
	if (!ok || !ts_cbor_put_tstr(resp, cap, &p, "data") ||
	    !ts_cbor_put_map(resp, cap, &p, 1) ||
	    !ts_cbor_put_tstr(resp, cap, &p, "error") ||
	    !ts_cbor_put_tstr(resp, cap, &p, note)) {
		return TS_E_IO;
	}
	*resp_len = p;
	return status;
}

/* 成功路径：handler 先写 data 暂存，再回填头（status 事后才知） */
static ts_res_t wrap_reply(uint8_t *resp, size_t cap, size_t *resp_len, const struct req_env *e,
			   ts_res_t status, const uint8_t *data, size_t data_len)
{
	size_t p = 0;
	bool ok;

	if (e->v2) {
		ok = ts_cbor_put_map(resp, cap, &p, 5) &&
		     ts_cbor_put_tstr(resp, cap, &p, "ver") &&
		     ts_cbor_put_uint(resp, cap, &p, 1) &&
		     ts_cbor_put_tstr(resp, cap, &p, "kind") &&
		     ts_cbor_put_uint(resp, cap, &p, 16) &&
		     ts_cbor_put_tstr(resp, cap, &p, "rid") &&
		     ts_cbor_put_tstr(resp, cap, &p, e->rid) &&
		     ts_cbor_put_tstr(resp, cap, &p, "status") &&
		     ts_cbor_put_int(resp, cap, &p, status);
	} else {
		ok = ts_cbor_put_map(resp, cap, &p, 2) &&
		     ts_cbor_put_tstr(resp, cap, &p, "status") &&
		     ts_cbor_put_int(resp, cap, &p, status);
	}
	if (!ok || !ts_cbor_put_tstr(resp, cap, &p, "data") ||
	    data_len > cap - p) {
		return TS_E_IO;
	}
	memcpy(resp + p, data, data_len);
	p += data_len;
	*resp_len = p;
	return status;
}

ts_res_t ts_net_cmd_dispatch(const char *key_suffix, const uint8_t *req, uint32_t req_len,
			     uint8_t *resp, size_t cap, size_t *resp_len)
{
	if (key_suffix == NULL || resp == NULL || resp_len == NULL) {
		return TS_E_PARAM;
	}
	*resp_len = 0;
	struct cmd_slot *slot = find_cmd(key_suffix);

	if (slot == NULL) {
		struct req_env e = {0};

		return encode_err(resp, cap, resp_len, &e, TS_E_NOTFOUND, "unknown key");
	}
	if (req == NULL || req_len == 0) {
		struct req_env e = {0};

		return encode_err(resp, cap, resp_len, &e, TS_E_PARAM, "empty request");
	}
	struct req_env e;

	if (parse_req(req, req_len, &e) != TS_OK) {
		return encode_err(resp, cap, resp_len, &e, TS_E_PARAM, "malformed request");
	}
	/* to 上界（DEC-40）：命令执行上界须留断链判定余量 */
	if (e.v2 && e.has_to && e.to_ms > REQ_TO_MAX_MS) {
		return encode_err(resp, cap, resp_len, &e, TS_E_PARAM, "to>5000ms rejected");
	}
	/* 幂等回放（DEC-40）：同 idem 命中 = 原样回执不重执行 */
	if (e.v2 && e.has_idem) {
		struct idem_slot *hit = idem_find(e.idem);

		if (hit != NULL) {
			if (strcmp(hit->op, e.op) != 0) {
				return encode_err(resp, cap, resp_len, &e, TS_E_PARAM,
						  "idem/op mismatch");
			}
			if (hit->rlen > cap) {
				return encode_err(resp, cap, resp_len, &e, TS_E_IO,
						  "resp overflow");
			}
			memcpy(resp, hit->reply, hit->rlen);
			*resp_len = hit->rlen;
			hit->stamp = ++idem_clock; /* LRU 触碰 */
			return hit->status;
		}
	}
	/* key 后缀与 op 双重匹配（sys/get-info 处 op 必须为 get-info——防表项错位） */
	char expect[36];

	int w = snprintf(expect, sizeof(expect), "sys/%s", e.op);

	if (w < 0 || (size_t)w >= sizeof(expect) ||
	    strncmp(key_suffix, "sys/", 4) != 0 ||
	    strcmp(key_suffix, expect) != 0) {
		return encode_err(resp, cap, resp_len, &e, TS_E_NOTFOUND, "op/key mismatch");
	}
	/* 写类命令门控（DEC-41 准入挂钩首个落点——部署面）：仅 v2 信封（v1 无
	 * src 身份）且当前租约持有者 = src。只读族与 estop-clear 豁免不变。 */
	if (slot->gated) {
		if (!e.v2) {
			return encode_err(resp, cap, resp_len, &e, TS_E_PARAM,
					  "v2 envelope required");
		}
		if (!ts_net_lease_held_by(e.src, ts_time_ms())) {
			return encode_err(resp, cap, resp_len, &e, TS_E_STATE,
					  "lease required");
		}
	}
	static uint8_t data_scratch[RESP_DATA_MAX]; /* 分发上下文串行（传输回调/测试） */
	size_t data_len = 0;
	ts_res_t status = slot->fn(&e.args, data_scratch, sizeof(data_scratch), &data_len);

	if (status == TS_E_IO || data_len + 64 > cap) {
		return encode_err(resp, cap, resp_len, &e, TS_E_IO, "resp overflow");
	}
	ts_res_t wr = wrap_reply(resp, cap, resp_len, &e, status, data_scratch, data_len);

	if (wr == TS_E_IO) {
		return encode_err(resp, cap, resp_len, &e, TS_E_IO, "resp overflow");
	}
	if (e.v2 && e.has_idem) {
		idem_insert(&e, resp, *resp_len, status);
	}
	return wr;
}

void ts_net_cmd_sys_init(void)
{
	/* sys 命令表（LLD §4；host_only——本函数仅框架 init 调用）。
	 * gated = 写类（v2 信封 + 租约持有者 = src 才执行，DEC-41）。 */
	static const struct {
		const char *suffix;
		ts_net_cmd_fn fn;
		bool gated;
	} sys_cmds[] = {
		{"sys/get-info", cmd_get_info, false},
		{"sys/get-link", cmd_get_link, false},
		{"sys/get-safety", cmd_get_safety, false},
		{"sys/get-budget", cmd_get_budget, false},
		{"sys/get-audit", cmd_get_audit, false},
		{"sys/set-time", cmd_set_time, false},
		{"sys/estop-clear", cmd_estop_clear, false},
		{"sys/lease-acquire", cmd_lease_acquire, false},
		{"sys/lease-release", cmd_lease_release, false},
		{"sys/lease-get", cmd_lease_get, false},
		{"sys/app-begin", cmd_app_begin, true},
		{"sys/app-chunk", cmd_app_chunk, true},
		{"sys/app-verify", cmd_app_verify, true},
		{"sys/app-activate", cmd_app_activate, true},
		{"sys/get-app", cmd_get_app, false},
	};
	for (size_t i = 0; i < sizeof(sys_cmds) / sizeof(sys_cmds[0]); i++) {
		(void)ts_net_cmd_register(sys_cmds[i].suffix, sys_cmds[i].fn);
		table[i].gated = sys_cmds[i].gated; /* 公共注册面之后补装配位 */
	}
}

#ifdef CONFIG_TS_TEST
void ts_net_cmd_test_reset(void)
{
	memset(table, 0, sizeof(table));
	memset(idem_cache, 0, sizeof(idem_cache));
	idem_clock = 0;
}
#endif
