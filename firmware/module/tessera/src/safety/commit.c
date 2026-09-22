/* SPDX-License-Identifier: Apache-2.0 */
/*
 * 唯一写路径出口（LLD-ts-safety §4）——合同 2 的强制点。
 * 内部流程：查表 → ACTIVE 校验 → 限幅 → slew → 限流 → 末段临界区（irq_lock 复查
 * forced，防 estop ISR 与本线程竞争末笔）→ 审计。
 */
#include <string.h>
#include <ts/safety.h>
#include "internal.h"

static struct k_mutex commit_lock = Z_MUTEX_INITIALIZER(commit_lock);

/* 审计环形：深度 CONFIG_TS_SAFETY_AUDIT_DEPTH（DEC-27: 64）；溢出覆盖最旧并计数
 * （DR-07；V1 不落盘——DEC-30④）。消费者 = ts-net 遥测合流 + sys:get-audit（M3）。 */
static ts_audit_entry_t audit_ring[CONFIG_TS_SAFETY_AUDIT_DEPTH];
static uint32_t audit_head, audit_count, audit_dropped;

static void audit_append(int ch_idx, ts_ch_kind_t kind, ts_out_value_t v, ts_res_t res)
{
	uint32_t next = (audit_head + 1) % CONFIG_TS_SAFETY_AUDIT_DEPTH;

	if (audit_count == CONFIG_TS_SAFETY_AUDIT_DEPTH) {
		audit_dropped++; /* 覆盖最旧（DR-07） */
	} else {
		audit_count++;
	}
	audit_ring[audit_head] = (ts_audit_entry_t){
		.t_ms = ts_time_ms(),
		.ch_idx = (uint16_t)(ch_idx >= 0 ? ch_idx : 0xFFFF),
		.res = res,
		.actor = 0, /* M1 恒 system；M2 起 ts-hal 注入调用者 app_id（DEC-30②） */
		.kind = (uint8_t)kind,
		._rsv = 0,
		.value_u = ts_value_encode(kind, v),
	};
	audit_head = next;
}

ts_res_t ts_safety_commit(const char *uid, ts_out_value_t v)
{
	if (k_is_in_isr()) {
		return TS_E_PERM; /* [thread] API（ISR 禁入，LLD-00 §3） */
	}
	(void)k_mutex_lock(&commit_lock, K_FOREVER);

	int i = ts_ch_find(uid);
	if (i < 0) {
		(void)k_mutex_unlock(&commit_lock);
		return TS_E_NOTFOUND;
	}
	struct ts_ch_slot *s = &ts_ch_table[i];
	const ts_out_ch_t *ch = s->desc;

	if (s->state != TS_ST_ACTIVE) {
		audit_append(i, ch->kind, v, TS_E_STATE); /* 安全态下写入被拒（合同 3） */
		(void)k_mutex_unlock(&commit_lock);
		return TS_E_STATE;
	}
	if (atomic_get(&ts_forced) != 0) {
		audit_append(i, ch->kind, v, TS_E_STATE);
		(void)k_mutex_unlock(&commit_lock);
		return TS_E_STATE; /* fail-safe 锁存期 */
	}

	ts_res_t res = TS_OK;

	/* 1) 限幅：clamp 到 [min,max]（LLD §4-3）。被拦截 = TS_E_RANGE
	 *（err.h：限幅/slew/预算均属“输出被安全层拦截”），拦截事实经审计 res 留痕。 */
	if (ch->kind == TS_CH_PWM) {
		if (v.u < ch->limits.min) {
			v.u = ch->limits.min;
			res = TS_E_RANGE;
		} else if (v.u > ch->limits.max) {
			v.u = ch->limits.max;
			res = TS_E_RANGE;
		}
	}

	/* 2) slew：|Δv| ≤ slew_per_ms × Δt；超率拆分到界值并返回 TS_E_RANGE（LLD §4-4） */
	if (ch->limits.slew_per_ms > 0 && s->have_last) {
		uint64_t dt = ts_time_ms() - s->last_t;
		uint32_t last_u = ts_value_encode(ch->kind, s->shadow);
		uint32_t req_u = ts_value_encode(ch->kind, v);
		uint64_t bound = (uint64_t)ch->limits.slew_per_ms * (dt + 1);

		if (req_u > last_u && (uint64_t)(req_u - last_u) > bound) {
			v.u = last_u + (uint32_t)bound;
			res = TS_E_RANGE;
		} else if (req_u < last_u && (uint64_t)(last_u - req_u) > bound) {
			v.u = last_u - (uint32_t)bound;
			res = TS_E_RANGE;
		}
	}

	/* 3) 限流（TS_CH_POWER）：请求电流超限 → 整笔拒绝（LLD §4-5） */
	if (ch->kind == TS_CH_POWER && v.pwr.en && v.pwr.ma > ch->limits.current_limit_ma) {
		audit_append(i, ch->kind, v, TS_E_RANGE);
		(void)k_mutex_unlock(&commit_lock);
		return TS_E_RANGE;
	}

	/* 4) 末段临界区：防 estop ISR 与本线程竞争末笔（LLD §4-6） */
	unsigned int key = irq_lock();

	if (atomic_get(&ts_forced) == 0) {
		ts_drivers[ch->kind].write(ch, &v);
		s->shadow = v;
		s->last_t = ts_time_ms();
		s->have_last = true;
	}
	irq_unlock(key);

	audit_append(i, ch->kind, v, res);
	(void)k_mutex_unlock(&commit_lock);
	return res;
}

ts_res_t ts_safety_readback(const char *uid, ts_out_value_t *out)
{
	if (out == NULL) {
		return TS_E_PARAM;
	}
	int i = ts_ch_find(uid);

	if (i < 0) {
		return TS_E_NOTFOUND;
	}
	*out = ts_ch_table[i].shadow;
	return TS_OK;
}

size_t ts_safety_audit_copy(ts_audit_entry_t *out, size_t max)
{
	size_t n = 0;

	for (uint32_t k = 0; k < audit_count && n < max; k++) {
		uint32_t idx = (audit_head + CONFIG_TS_SAFETY_AUDIT_DEPTH - 1 - k) %
			       CONFIG_TS_SAFETY_AUDIT_DEPTH;
		out[n++] = audit_ring[idx];
	}
	return n;
}

uint32_t ts_safety_audit_dropped(void)
{
	return audit_dropped;
}
