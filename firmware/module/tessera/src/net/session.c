/* SPDX-License-Identifier: Apache-2.0 */
/* 会话状态机 + 重连退避（LLD-ts-net §2）。client 角色〔DEC-20〕；退避 = 固定表
 * 〔DEC-27：250/500/1000/2000 循环〕——无随机抖动（确定性，合同 9）。
 * 观测事件 TS_EVT_NET_LINK_UP/DOWN 由本模块发布（安全语义以 linkmon 为准，
 * 避免双源——LLD §2 注）。 */
#include <stddef.h>
#include <ts/core.h>
#include <ts/net.h>
#include "internal.h"

const ts_net_transport_t *ts_net_transport;

static ts_net_state_t state = TS_NET_DOWN;
static uint32_t attempt;     /* 连续 open 失败次数（退避索引） */
static uint64_t next_try_ms;

ts_net_state_t ts_net_state(void)
{
	return state;
}

void ts_net_set_transport(const ts_net_transport_t *t)
{
	ts_net_transport = t;
}

uint32_t ts_net_backoff_ms(uint32_t a)
{
	/* DEC-27 固定退避表（LLD §7 CONFIG_TS_NET_RECONNECT_TABLE_MS 的编译期形态：
	 * 四值循环，attempt 无上限回绕） */
	static const uint32_t table[4] = {250, 500, 1000, 2000};

	return table[a % 4u];
}

ts_net_state_t ts_net_session_poll(uint64_t now_ms)
{
	if (ts_net_transport == NULL) {
		return state; /* 未注入传输 = 无网络面（native_sim 默认） */
	}
	if (state == TS_NET_DOWN) {
		if (now_ms < next_try_ms) {
			return state;
		}
		if (ts_net_transport->open() == TS_OK && ts_net_transport->is_up()) {
			state = TS_NET_CONNECTED;
			attempt = 0;
			const ts_evt_t evt = {
				.id = TS_EVT_NET_LINK_UP,
				.t_ms = (uint32_t)now_ms,
			};
			ts_evt_publish(&evt);
			ts_net_pubq_flush(); /* DOWN 期积压冲刷 */
		} else {
			next_try_ms = now_ms + ts_net_backoff_ms(attempt);
			attempt++;
		}
		return state;
	}
	/* CONNECTED：传输层掉线检测（is_up 由传输实现驱动：读写失败/keepalive） */
	if (!ts_net_transport->is_up()) {
		ts_net_transport->close();
		state = TS_NET_DOWN;
		attempt = 0; /* 掉线后从表头重试（250ms） */
		next_try_ms = now_ms + ts_net_backoff_ms(attempt);
		const ts_evt_t evt = {
			.id = TS_EVT_NET_LINK_DOWN,
			.t_ms = (uint32_t)now_ms,
		};
		ts_evt_publish(&evt);
	}
	return state;
}

#ifdef CONFIG_TS_TEST
void ts_net_test_reset(void)
{
	state = TS_NET_DOWN;
	attempt = 0;
	next_try_ms = 0;
	ts_net_transport = NULL;
	extern void ts_net_pubq_test_reset(void);
	extern void ts_net_linkmon_test_reset(void);
	ts_net_pubq_test_reset();
	ts_net_linkmon_test_reset();
}
#endif
