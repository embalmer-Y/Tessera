/* SPDX-License-Identifier: Apache-2.0 */
/* 命令-回执分发（LLD-ts-net §4）。sys 命令面 host_only（DEC-30①/DR-03）——
 * 注册者 = 框架自身；APP 的 msg/net 能力文法不可达（M2b.2 msg 类前结构性
 * 隔离），host 侧通道授权由 prov 凭证保证。
 * 回执 = 定体 map{"status": int, "data": …}；未知 key/op = TS_E_NOTFOUND
 * 回执（不留静默）；req 非法 = TS_E_PARAM 回执。命令执行路径与 APP 一致
 * （无豁免：estop-clear 经 ts_safety_clear_fault，set-time 仅数据字段）。 */
#include <stdio.h>
#include <string.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/net.h>
#include <ts/safety.h>
#include <zephyr/kernel.h>
#include "internal.h"

#define CMD_TABLE_MAX  8
#define RESP_DATA_MAX  384 /* data 暂存上限（回执总预算 512 内扣除头） */

struct cmd_slot {
	const char *suffix; /* 如 "sys/get-info"（静态字面量，零拷贝） */
	ts_net_cmd_fn fn;
	bool used;
};
static struct cmd_slot table[CMD_TABLE_MAX];

/* ---- sys 命令实现（§4 表）----------------------------------------------- */

static ts_res_t cmd_get_info(const ts_net_cmd_args_t *a, uint8_t *r, size_t cap, size_t *n)
{
	ARG_UNUSED(a);
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 3) ||
	    !ts_cbor_put_tstr(r, cap, &p, "fw") ||
	    !ts_cbor_put_tstr(r, cap, &p, CONFIG_TS_FW_VERSION) ||
	    !ts_cbor_put_tstr(r, cap, &p, "board") ||
	    !ts_cbor_put_tstr(r, cap, &p, CONFIG_BOARD) ||
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
	/* ts-power = M3b；命令面先行注册（表完整），实现落地前如实报不可用 */
	ARG_UNUSED(a);
	size_t p = 0;

	if (!ts_cbor_put_map(r, cap, &p, 1) ||
	    !ts_cbor_put_tstr(r, cap, &p, "note") ||
	    !ts_cbor_put_tstr(r, cap, &p, "ts-power lands with M3b")) {
		return TS_E_IO;
	}
	*n = p;
	return TS_E_NOTFOUND;
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
			table[i].used = true;
			return TS_OK;
		}
	}
	return TS_E_NOMEM;
}

static ts_net_cmd_fn find_cmd(const char *suffix)
{
	for (int i = 0; i < CMD_TABLE_MAX; i++) {
		if (table[i].used && strcmp(table[i].suffix, suffix) == 0) {
			return table[i].fn;
		}
	}
	return NULL;
}

/* req 解码：map{ "op": tstr, "args"?: map{ "confirm"?: tstr, "time_ms"?: uint } } */
static ts_res_t parse_req(const uint8_t *req, uint32_t req_len, char *op, size_t op_cap,
			  ts_net_cmd_args_t *args)
{
	ts_cbor_rd_t r;
	uint32_t pairs;

	ts_cbor_rd_init(&r, req, req_len);
	memset(args, 0, sizeof(*args));
	if (!ts_cbor_map_open(&r, &pairs) || pairs == 0 || pairs > 2) {
		return TS_E_PARAM;
	}
	bool have_op = false;

	for (uint32_t i = 0; i < pairs; i++) {
		char key[12];

		if (!ts_cbor_tstr(&r, key, sizeof(key))) {
			return TS_E_PARAM;
		}
		if (strcmp(key, "op") == 0) {
			if (!ts_cbor_tstr(&r, op, op_cap)) {
				return TS_E_PARAM;
			}
			have_op = true;
		} else if (strcmp(key, "args") == 0) {
			uint32_t apairs;

			if (!ts_cbor_map_open(&r, &apairs) || apairs > 2) {
				return TS_E_PARAM;
			}
			for (uint32_t j = 0; j < apairs; j++) {
				char akey[12];

				if (!ts_cbor_tstr(&r, akey, sizeof(akey))) {
					return TS_E_PARAM;
				}
				if (strcmp(akey, "confirm") == 0) {
					if (!ts_cbor_tstr(&r, args->confirm,
							  sizeof(args->confirm))) {
						return TS_E_PARAM;
					}
				} else if (strcmp(akey, "time_ms") == 0) {
					uint64_t v;

					if (!ts_cbor_uint(&r, &v)) {
						return TS_E_PARAM;
					}
					args->time_ms = v;
					args->has_time_ms = true;
				} else {
					return TS_E_PARAM; /* 未知参数 = 拒绝 */
				}
			}
		} else {
			return TS_E_PARAM; /* 未知键 = 拒绝 */
		}
	}
	return have_op ? TS_OK : TS_E_PARAM;
}

/* 回执兜底：data = map{"error": tstr}（status 已定） */
static ts_res_t encode_resp(uint8_t *resp, size_t cap, size_t *resp_len, ts_res_t status,
			    const char *note)
{
	size_t p = 0;

	if (!ts_cbor_put_map(resp, cap, &p, 2) ||
	    !ts_cbor_put_tstr(resp, cap, &p, "status") ||
	    !ts_cbor_put_int(resp, cap, &p, status) ||
	    !ts_cbor_put_tstr(resp, cap, &p, "data") ||
	    !ts_cbor_put_map(resp, cap, &p, 1) ||
	    !ts_cbor_put_tstr(resp, cap, &p, "error") ||
	    !ts_cbor_put_tstr(resp, cap, &p, note)) {
		return TS_E_IO;
	}
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
	ts_net_cmd_fn fn = find_cmd(key_suffix);

	if (fn == NULL) {
		return encode_resp(resp, cap, resp_len, TS_E_NOTFOUND, "unknown key");
	}
	char op[24];
	ts_net_cmd_args_t args;

	if (req == NULL || req_len == 0) {
		return encode_resp(resp, cap, resp_len, TS_E_PARAM, "empty request");
	}
	ts_res_t pr = parse_req(req, req_len, op, sizeof(op), &args);

	if (pr != TS_OK) {
		return encode_resp(resp, cap, resp_len, TS_E_PARAM, "malformed request");
	}
	/* key 后缀与 op 双重匹配（sys/get-info 处 op 必须为 get-info——防表项错位） */
	char expect[36];

	int w = snprintf(expect, sizeof(expect), "sys/%s", op);

	if (w < 0 || (size_t)w >= sizeof(expect) ||
	    strncmp(key_suffix, "sys/", 4) != 0 ||
	    strcmp(key_suffix, expect) != 0) {
		return encode_resp(resp, cap, resp_len, TS_E_NOTFOUND, "op/key mismatch");
	}
	/* 两段式：handler 先写 data 暂存，再回填 status 头（status 事后才知） */
	static uint8_t data_scratch[RESP_DATA_MAX]; /* 分发上下文串行（传输回调/测试） */
	size_t data_len = 0;
	ts_res_t status = fn(&args, data_scratch, sizeof(data_scratch), &data_len);

	if (status == TS_E_IO || data_len + 32 > cap) {
		return encode_resp(resp, cap, resp_len, TS_E_IO, "resp overflow");
	}
	size_t p = 0;

	if (!ts_cbor_put_map(resp, cap, &p, 2) ||
	    !ts_cbor_put_tstr(resp, cap, &p, "status") ||
	    !ts_cbor_put_int(resp, cap, &p, status) ||
	    !ts_cbor_put_tstr(resp, cap, &p, "data") ||
	    data_len > cap - p) {
		return TS_E_IO;
	}
	memcpy(resp + p, data_scratch, data_len);
	p += data_len;
	*resp_len = p;
	return status;
}

void ts_net_cmd_sys_init(void)
{
	/* sys 命令表（LLD §4；host_only——本函数仅框架 init 调用） */
	static const struct {
		const char *suffix;
		ts_net_cmd_fn fn;
	} sys_cmds[] = {
		{"sys/get-info", cmd_get_info},
		{"sys/get-link", cmd_get_link},
		{"sys/get-safety", cmd_get_safety},
		{"sys/get-budget", cmd_get_budget},
		{"sys/get-audit", cmd_get_audit},
		{"sys/set-time", cmd_set_time},
		{"sys/estop-clear", cmd_estop_clear},
	};
	for (size_t i = 0; i < sizeof(sys_cmds) / sizeof(sys_cmds[0]); i++) {
		(void)ts_net_cmd_register(sys_cmds[i].suffix, sys_cmds[i].fn);
	}
}

#ifdef CONFIG_TS_TEST
void ts_net_cmd_test_reset(void)
{
	memset(table, 0, sizeof(table));
}
#endif
