/* SPDX-License-Identifier: Apache-2.0 */
/* 发布队列（LLD-ts-net §5）：遥测/事件尽力而为，不阻塞控制路径。
 * DOWN 期直接丢弃并计数（防上电风暴与不确定时序，不排队重放）；
 * 队满丢最旧并计数（DEC-27：缓冲 8）。 */
#include <string.h>
#include <ts/net.h>
#include "internal.h"

#define KEY_MAX     64
/* 溯源：DEC-42 信封最坏编码。原 64B = 信封头 + 单 extra 对（SAFE_STATE）；
 * impl-review-01 F-1 增补 periph（2 对）/预算（3 对）extra 后最坏 ≈ 96B
 * （t_ms/wall_ms 均 uint64 + 三键值对），扩至 128B。内存影响 +512B 静态
 * （8 深度 ×128B = 1KB），计入板级 RAM 预算复核（DEC-29）。 */
#define PAYLOAD_MAX 128
#define DEPTH       CONFIG_TS_NET_PUBQ_DEPTH

struct pubq_entry {
	char key[KEY_MAX];
	uint8_t payload[PAYLOAD_MAX];
	uint32_t len;
	ts_net_qos_t qos;
};

static struct pubq_entry q[DEPTH];
static uint32_t head, count, dropped;

ts_res_t ts_net_pubq_push(const char *key, const uint8_t *payload, uint32_t len)
{
	return ts_net_pubq_push_qos(key, payload, len, TS_NET_QOS_BESTEFFORT);
}

ts_res_t ts_net_pubq_push_qos(const char *key, const uint8_t *payload, uint32_t len,
			      ts_net_qos_t qos)
{
	if (key == NULL || payload == NULL || key[0] == '\0' || len == 0) {
		return TS_E_PARAM;
	}
	if (strlen(key) >= KEY_MAX || len > PAYLOAD_MAX) {
		return TS_E_PARAM;
	}
	if (ts_net_state() == TS_NET_DOWN) {
		dropped++; /* DOWN 期直接丢弃（LLD §5） */
		return TS_OK;
	}
	if (count == DEPTH) {
		head = (head + 1) % DEPTH; /* 满则丢最旧 */
		count--;
		dropped++;
	}
	struct pubq_entry *e = &q[(head + count) % DEPTH];

	strcpy(e->key, key);
	memcpy(e->payload, payload, len);
	e->len = len;
	e->qos = qos;
	count++;
	return TS_OK;
}

void ts_net_pubq_flush(void)
{
	if (ts_net_state() != TS_NET_CONNECTED || ts_net_transport == NULL) {
		return;
	}
	while (count > 0) {
		struct pubq_entry *e = &q[head];

		if (ts_net_transport->publish(e->key, e->payload, e->len, e->qos) != TS_OK) {
			dropped++; /* 发送失败丢弃（尽力而为语义） */
		}
		head = (head + 1) % DEPTH;
		count--;
	}
}

uint32_t ts_net_pubq_dropped(void)
{
	return dropped;
}

#ifdef CONFIG_TS_TEST
void ts_net_pubq_test_reset(void)
{
	head = count = dropped = 0;
	memset(q, 0, sizeof(q));
}
#endif
