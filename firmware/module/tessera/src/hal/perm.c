/* SPDX-License-Identifier: Apache-2.0 */
/* 能力文法解析 + 调用者裁决（LLD-ts-hal §2/§3）。
 * 合同 10：越权访问一律拒绝并留痕（TS_EVT_PERM_DENIED）。 */
#include <ctype.h>
#include <string.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/safety.h>
#include <zephyr/kernel.h>

/* ctx → perm 表绑定（一对一；原生侧映射，APP 不可寻址） */
#define MAX_BOUND_CTX 4 /* = 同时加载 APP 上限（DEC-27 #10） */

struct bound_ctx {
	uint16_t app_id;
	ts_perm_table_t table;
	bool used;
};
static struct bound_ctx contexts[MAX_BOUND_CTX];

void ts_perm_table_init(ts_perm_table_t *table)
{
	memset(table, 0, sizeof(*table));
}

static int parse_class(const char *s, size_t len)
{
	if (len == 4 && strncmp(s, "gpio", 4) == 0) return TS_PERM_CLASS_GPIO;
	if (len == 3 && strncmp(s, "pwm", 3) == 0) return TS_PERM_CLASS_PWM;
	if (len == 3 && strncmp(s, "adc", 3) == 0) return TS_PERM_CLASS_ADC;
	if (len == 5 && strncmp(s, "power", 5) == 0) return TS_PERM_CLASS_POWER;
	if (len == 3 && strncmp(s, "msg", 3) == 0) return TS_PERM_CLASS_MSG;
	if (len == 3 && strncmp(s, "sys", 3) == 0) return TS_PERM_CLASS_SYS;
	return -1;
}

static int parse_op(const char *s, size_t len)
{
	if (len == 4 && strncmp(s, "read", 4) == 0) return TS_PERM_OP_READ;
	if (len == 5 && strncmp(s, "write", 5) == 0) return TS_PERM_OP_WRITE;
	if (len == 3 && strncmp(s, "set", 3) == 0) return TS_PERM_OP_SET;
	return -1;
}

/* 解析实例段："0-3" / "0,2" / "5" / "*"（msg 类用 name——V1 按 0 处理） */
static ts_res_t parse_instances(const char *s, size_t len, uint32_t *bitmap)
{
	size_t i = 0;

	while (i < len) {
		/* 跳过逗号 */
		if (s[i] == ',') {
			i++;
			continue;
		}
		if (!isdigit((int)s[i])) {
			return TS_E_PARAM;
		}
		uint32_t start = 0, end = 0;

		while (i < len && isdigit((int)s[i])) {
			start = start * 10 + (uint32_t)(s[i] - '0');
			if (start > 31) return TS_E_PARAM;
			i++;
		}
		end = start;
		if (i < len && s[i] == '-') {
			i++;
			if (i >= len || !isdigit((int)s[i])) return TS_E_PARAM;
			end = 0; /* 范围尾段独立解析（不从 start 累积） */
			while (i < len && isdigit((int)s[i])) {
				end = end * 10 + (uint32_t)(s[i] - '0');
				if (end > 31) return TS_E_PARAM;
				i++;
			}
		}
		if (end < start) return TS_E_PARAM;
		for (uint32_t b = start; b <= end; b++) {
			*bitmap |= (1U << b);
		}
	}
	return TS_OK;
}

ts_res_t ts_perm_parse(const char *cap, ts_perm_table_t *table)
{
	if (cap == NULL || table == NULL) {
		return TS_E_PARAM;
	}
	/* 格式：class:op:instances */
	const char *c1 = strchr(cap, ':');

	if (c1 == NULL) return TS_E_PARAM;
	const char *c2 = strchr(c1 + 1, ':');

	if (c2 == NULL) return TS_E_PARAM;

	int cls = parse_class(cap, (size_t)(c1 - cap));

	if (cls < 0) return TS_E_PARAM;
	int op = parse_op(c1 + 1, (size_t)(c2 - c1 - 1));

	if (op < 0) return TS_E_PARAM;

	uint32_t bitmap = 0;
	ts_res_t r = parse_instances(c2 + 1, strlen(c2 + 1), &bitmap);

	if (r != TS_OK) return r;
	table->bitmap[cls][op] |= bitmap;
	return TS_OK;
}

ts_res_t ts_perm_check(ts_ctx_t ctx, ts_perm_class_t cls, ts_perm_op_t op, uint8_t inst)
{
	/* 查绑定表 */
	for (int i = 0; i < MAX_BOUND_CTX; i++) {
		if (contexts[i].used && contexts[i].app_id == ctx.app_id) {
			if (cls < TS_PERM_CLASS_COUNT && op < TS_PERM_OP_COUNT && inst < 32) {
				if (contexts[i].table.bitmap[cls][op] & (1U << inst)) {
					return TS_OK;
				}
			}
			/* 合同 10：越权拒绝并留痕 */
			struct {
				uint16_t app_id;
				uint8_t cls, op, inst;
			} payload = {.app_id = ctx.app_id, .cls = (uint8_t)cls,
				     .op = (uint8_t)op, .inst = inst};
			const ts_evt_t evt = {
				.id = TS_EVT_PERM_DENIED,
				.t_ms = ts_time_ms(),
				.data = &payload,
				.len = sizeof(payload),
			};
			ts_evt_publish(&evt);
			return TS_E_PERM;
		}
	}
	return TS_E_PERM; /* 未绑定上下文 = 拒绝 */
}

ts_res_t ts_hal_bind_context(ts_ctx_t *ctx, uint16_t app_id, const ts_perm_table_t *table)
{
	if (ctx == NULL || table == NULL) return TS_E_PARAM;
	for (int i = 0; i < MAX_BOUND_CTX; i++) {
		if (!contexts[i].used) {
			contexts[i].used = true;
			contexts[i].app_id = app_id;
			contexts[i].table = *table;
			ctx->app_id = app_id;
			ctx->_rsv = 0;
			return TS_OK;
		}
	}
	return TS_E_NOMEM; /* 同时加载上限（DEC-27 #10：4） */
}

void ts_hal_unbind_context(ts_ctx_t *ctx)
{
	if (ctx == NULL) return;
	for (int i = 0; i < MAX_BOUND_CTX; i++) {
		if (contexts[i].used && contexts[i].app_id == ctx->app_id) {
			contexts[i].used = false;
			return;
		}
	}
}
