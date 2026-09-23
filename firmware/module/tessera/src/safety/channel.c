/* SPDX-License-Identifier: Apache-2.0 */
/*
 * 通道注册表 + 三安全态状态机（LLD-ts-safety §2/§3）。
 * 合同 1：无三安全态声明不予注册；合同 10：安全参数运行时只读。
 */
#include <string.h>
#include <ts/safety.h>
#include "internal.h"

struct ts_ch_slot ts_ch_table[CONFIG_TS_SAFETY_MAX_CHANNELS]; /* 容量 32（DEC-27） */
size_t ts_ch_count;

atomic_t ts_link_up = ATOMIC_INIT(0); /* 初值 down：boot 后链路未确立 */
atomic_t ts_forced = ATOMIC_INIT(0);
atomic_t ts_forced_at = ATOMIC_INIT(0);

static bool value_within_limits(const ts_out_ch_t *ch, ts_out_value_t v)
{
	switch (ch->kind) {
	case TS_CH_GPIO:
		return true;
	case TS_CH_PWM:
		return v.u >= ch->limits.min && v.u <= ch->limits.max;
	case TS_CH_POWER:
		if (!v.pwr.en) {
			return true;
		}
		return v.pwr.ma <= ch->limits.current_limit_ma;
	default:
		return false;
	}
}

ts_res_t ts_safety_register_channel(const ts_out_ch_t *ch)
{
	if (ch == NULL || ch->uid == NULL || ch->uid[0] == '\0' ||
	    ch->kind >= TS_CH_KIND_COUNT) {
		return TS_E_PARAM;
	}
	if (ts_ch_find(ch->uid) >= 0) {
		return TS_E_PARAM; /* uid 撞名 */
	}
	if (ts_ch_count >= CONFIG_TS_SAFETY_MAX_CHANNELS) {
		return TS_E_NOMEM;
	}
	/* 三安全态缺一拒绝；且安全态值本身必须落在 limits 内（LLD §2 注册校验） */
	if (!value_within_limits(ch, ch->poweron) ||
	    !value_within_limits(ch, ch->linkloss) ||
	    !value_within_limits(ch, ch->fault)) {
		return TS_E_PARAM;
	}

	struct ts_ch_slot *slot = &ts_ch_table[ts_ch_count++];

	slot->desc = ch;
	slot->state = TS_ST_SAFE_POWERON;
	slot->shadow = ch->poweron;
	slot->have_last = false;
	slot->last_t = 0;
	slot->sim_rec.head = 0;
	slot->sim_rec.count = 0;
	return TS_OK;
}

static void set_state(size_t i, ts_ch_state_t next)
{
	struct ts_ch_slot *s = &ts_ch_table[i];

	if (s->state == next) {
		return;
	}
	s->state = next;
	const ts_safe_state_evt_t payload = {
		.uid = s->desc->uid,
		.new_state = next,
	};
	const ts_evt_t evt = {
		.id = TS_EVT_SAFE_STATE_CHANGED,
		.t_ms = ts_time_ms(),
		.data = &payload,
		.len = sizeof(payload),
	};
	ts_evt_publish(&evt);
}

ts_res_t ts_safety_poweron_init(void)
{
	for (size_t i = 0; i < ts_ch_count; i++) {
		ts_ch_table[i].state = TS_ST_SAFE_POWERON;
	}
	return TS_OK;
}

void ts_safety_set_link(bool up)
{
	atomic_set(&ts_link_up, up ? 1 : 0);
	for (size_t i = 0; i < ts_ch_count; i++) {
		struct ts_ch_slot *s = &ts_ch_table[i];

		if (up && (s->state == TS_ST_SAFE_POWERON || s->state == TS_ST_SAFE_LINKLOSS)) {
			/* 链路确立：SAFE_POWERON/Safe_LINKLOSS → ACTIVE（LLD §3 图）。
			 * DR-04：LINKLOSS 恢复不自动回写断链前的值——须显式 commit。 */
			set_state(i, TS_ST_ACTIVE);
		} else if (!up && s->state == TS_ST_ACTIVE) {
			/* 断链：ACTIVE → SAFE_LINKLOSS（shadow 改写为安全值） */
			s->shadow = s->desc->linkloss;
			s->have_last = false;
			set_state(i, TS_ST_SAFE_LINKLOSS);
		}
	}
}

ts_res_t ts_safety_clear_fault(void)
{
	/* IR-01 修复（M1 自检）：clear_fault 是 estop 锁存的**唯一释放路径**
	 *（LLD §5"clear_fault 前 forced 标志不复位"= 复位只经此处发生）；
	 * 运行期可达性 = 仅 sys:estop-clear（host-only + 确认令牌，DEC-30①，
	 * M3 ts-net 接线；M1 直调仅供测试）。
	 * LLD §3 状态机图未明示复位目标态；实现取条件恢复
	 * （link up → ACTIVE，否则 SAFE_LINKLOSS），语义随 M3 net 联调复核。 */
	atomic_set(&ts_forced, 0);
	ts_safety_estop_announce_reset();
	for (size_t i = 0; i < ts_ch_count; i++) {
		if (ts_ch_table[i].state == TS_ST_SAFE_FAULT) {
			set_state(i, atomic_get(&ts_link_up) ? TS_ST_ACTIVE : TS_ST_SAFE_LINKLOSS);
			ts_ch_table[i].have_last = false;
		}
	}
	return TS_OK;
}

ts_res_t ts_safety_channel_state(const char *uid, ts_ch_state_t *out)
{
	if (out == NULL) {
		return TS_E_PARAM;
	}
	int i = ts_ch_find(uid);

	if (i < 0) {
		return TS_E_NOTFOUND;
	}
	*out = ts_ch_table[i].state;
	return TS_OK;
}

ts_res_t ts_safety_summary(ts_safety_summary_t *out)
{
	if (out == NULL) {
		return TS_E_PARAM;
	}
	memset(out, 0, sizeof(*out));
	for (size_t i = 0; i < ts_ch_count; i++) {
		if (ts_ch_table[i].state < TS_CH_STATE_COUNT) {
			out->by_state[ts_ch_table[i].state]++;
		}
	}
	out->channels = (uint16_t)ts_ch_count;
	return TS_OK;
}
