/* SPDX-License-Identifier: Apache-2.0 */
/* 发布面（LLD-ts-net §5）：遥测周期快照 + 事件选择性外发 → pubq（尽力而为，
 * 不阻塞控制路径）。DOWN 期丢弃/满丢最旧由 pubq 统一语义处理。
 * 事件外发 = 合同 5（estop 事后补发可见）/合同 10（越权留痕对外可见）的
 * 观测面；只观测不改值（不影响任何控制路径——合同 3）。 */
#include <string.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/net.h>
#include <ts/safety.h>
#include <zephyr/kernel.h>
#include "internal.h"

/* ---- 事件订阅 → pubq ------------------------------------------------------ */

static void push_evt_jsonlike(ts_evt_id_t id, uint64_t t_ms, const char *uid_key_suffix,
			      const uint8_t *extra, size_t extra_len)
{
	char key[64];
	int kw = ts_net_key_evt(key, sizeof(key), uid_key_suffix);

	if (kw <= 0 || (size_t)kw >= sizeof(key)) {
		kw = ts_net_key_sys(key, sizeof(key), "event");
		if (kw <= 0 || (size_t)kw >= sizeof(key)) {
			return;
		}
	}
	/* payload = map{id, t_ms, wall_ms, detail?} */
	uint8_t buf[48];
	size_t p = 0;
	bool ok = ts_cbor_put_map(buf, sizeof(buf), &p, extra ? 4 : 3) &&
		  ts_cbor_put_tstr(buf, sizeof(buf), &p, "id") &&
		  ts_cbor_put_uint(buf, sizeof(buf), &p, (uint64_t)id) &&
		  ts_cbor_put_tstr(buf, sizeof(buf), &p, "t_ms") &&
		  ts_cbor_put_uint(buf, sizeof(buf), &p, t_ms) &&
		  ts_cbor_put_tstr(buf, sizeof(buf), &p, "wall_ms") &&
		  ts_cbor_put_uint(buf, sizeof(buf), &p, ts_time_wall_ms());

	if (ok && extra != NULL && extra_len > 0 && extra_len <= sizeof(buf) - p &&
	    p + extra_len <= sizeof(buf)) {
		memcpy(buf + p, extra, extra_len);
		p += extra_len;
	}
	if (ok) {
		(void)ts_net_pubq_push(key, buf, (uint32_t)p);
	}
}

static void on_evt(const ts_evt_t *evt, void *user)
{
	ARG_UNUSED(user);
	switch (evt->id) {
	case TS_EVT_ESTOP: /* 事后补发观测（合同 5；estop 动作本身不经总线） */
		push_evt_jsonlike(evt->id, evt->t_ms, "sys", NULL, 0);
		break;
	case TS_EVT_SAFE_STATE_CHANGED: {
		/* payload: ts_safe_state_evt_t（safety.h——uid + 新态） */
		const ts_safe_state_evt_t *pl = evt->data;
		uint8_t extra[24];
		size_t p = 0;

		if (ts_cbor_put_tstr(extra, sizeof(extra), &p, "state") &&
		    ts_cbor_put_uint(extra, sizeof(extra), &p, (uint64_t)pl->new_state)) {
			push_evt_jsonlike(evt->id, evt->t_ms, pl->uid, extra, p);
		}
		break;
	}
	case TS_EVT_PERM_DENIED: /* 合同 10 留痕外发 */
	case TS_EVT_INPUT_CHANGED: /* DR-02 输入变化 */
	default:
		/* 通用：id + t_ms（detail 原始结构非稳定编码，不外发——防架构相关字节） */
		push_evt_jsonlike(evt->id, evt->t_ms, "sys", NULL, 0);
		break;
	}
}

ts_res_t ts_net_pub_init(void)
{
	static bool subscribed;
	ts_res_t r = TS_OK;

	if (subscribed) {
		return TS_OK;
	}
	/* 事件总线容量 CONFIG_TS_CORE_MAX_SUBS=4（DEC-27）——四类全占；
	 * 满员属装配错误（TS_E_NOMEM 如实上报） */
	const ts_evt_id_t ids[] = {
		TS_EVT_ESTOP, TS_EVT_SAFE_STATE_CHANGED,
		TS_EVT_PERM_DENIED, TS_EVT_INPUT_CHANGED,
	};

	for (size_t i = 0; i < sizeof(ids) / sizeof(ids[0]); i++) {
		r = ts_evt_subscribe(ids[i], on_evt, NULL);
		if (r != TS_OK) {
			return r;
		}
	}
	subscribed = true;
	return r;
}

/* ---- 遥测周期快照（§5：实例值 + 周期合流）-------------------------------- */

static ts_ch_kind_t ch_kind_of(ts_dev_kind_t k)
{
	switch (k) {
	case TS_DEV_GPIO_OUT:
		return TS_CH_GPIO;
	case TS_DEV_PWM:
		return TS_CH_PWM;
	case TS_DEV_POWER:
		return TS_CH_POWER;
	default:
		return TS_CH_KIND_COUNT;
	}
}

void ts_net_pub_telem(uint64_t now_ms)
{
	ARG_UNUSED(now_ms);
	for (size_t i = 0; i < ts_hal_dev_count(); i++) {
		const ts_hal_dev_desc_t *d = ts_hal_dev_get(i);
		ts_ch_kind_t ck = (d != NULL) ? ch_kind_of(d->kind) : TS_CH_KIND_COUNT;

		if (d == NULL || ck == TS_CH_KIND_COUNT) {
			continue; /* 输入实例走事件路径（DR-02），不进快照 */
		}
		ts_out_value_t v;

		if (ts_safety_readback(d->uid, &v) != TS_OK) {
			continue; /* hal 实例未必都有 safety 通道（如电源桩） */
		}
		uint8_t buf[40];
		size_t p = 0;

		if (!ts_cbor_put_map(buf, sizeof(buf), &p, 3) ||
		    !ts_cbor_put_tstr(buf, sizeof(buf), &p, "kind") ||
		    !ts_cbor_put_uint(buf, sizeof(buf), &p, (uint64_t)d->kind) ||
		    !ts_cbor_put_tstr(buf, sizeof(buf), &p, "value_u") ||
		    !ts_cbor_put_uint(buf, sizeof(buf), &p, ts_value_encode(ck, v)) ||
		    !ts_cbor_put_tstr(buf, sizeof(buf), &p, "wall_ms") ||
		    !ts_cbor_put_uint(buf, sizeof(buf), &p, ts_time_wall_ms())) {
			continue;
		}
		char key[64];
		int kw = ts_net_key_tel(key, sizeof(key), d->uid);

		if (kw > 0 && (size_t)kw < sizeof(key)) {
			(void)ts_net_pubq_push(key, buf, (uint32_t)p);
		}
	}
}
