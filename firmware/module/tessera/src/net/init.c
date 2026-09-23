/* SPDX-License-Identifier: Apache-2.0 */
/* ts-net 初始化（boot 步骤接线，LLD-ts-net §2/§6）+ sysworkq 周期驱动。
 * 周期体 = session_poll → linkmon_tick → pub_telem（依赖序）；遥测周期
 * 〔DEC-27：200ms〕为驱动节拍（session/linkmon 内部按各自周期判定）。 */
#include <string.h>
#include <ts/core.h>
#include <ts/net.h>
#include <ts/store.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include "internal.h"

#ifdef CONFIG_TS_NET_ZENOH
extern const ts_net_transport_t ts_net_zenoh_transport;

static struct k_work_delayable net_work;
static bool started;

static void net_tick(struct k_work *work)
{
	struct k_work_delayable *d = k_work_delayable_from_work(work);
	uint64_t now = ts_time_ms();

	(void)ts_net_session_poll(now);
	ts_net_linkmon_tick(now);
	ts_net_pub_telem(now);
	ts_net_pubq_flush(); /* 周期冲刷（CONNECTED 持续期；DOWN 期 pubq 自弃） */
	k_work_reschedule_for_queue(&k_sys_work_q, d,
				     K_MSEC(CONFIG_TS_NET_TELEM_INTERVAL_MS));
}
#else
static bool started; /* 桩构建：ts_net_init 仅装配 ids/命令表/事件订阅 */
#endif

ts_res_t ts_net_init(void)
{
	if (started) {
		return TS_E_STATE;
	}
	started = true;

	/* ids ← prov（V1 单立方体 node = cube，DEC-26）。prov 缺失/损坏 → 开发
	 * 缺省（网络面保持 DOWN = 安全侧；生产板 boot 强校验随板级里程碑收紧）。 */
	const char *node = "n-dev";
	const char *cube = "c-dev";
	ts_res_t plr = ts_store_prov_load();
	const ts_prov_t *prov = ts_store_prov();

	if (plr == TS_OK && prov->cube_id[0] != '\0') {
		node = prov->node_id[0] != '\0' ? prov->node_id : prov->cube_id;
		cube = prov->cube_id;
	}
	printk("[ts-net] init prov_load=%d node=%s cube=%s\n", (int)plr, node, cube);
	(void)ts_net_set_ids(node, cube);

	/* sys 命令表注册（host_only；表满 = 装配错误，如实返回） */
	ts_net_cmd_sys_init();
	ts_res_t r = ts_net_pub_init();

	if (r != TS_OK) {
		return r;
	}
#ifdef CONFIG_TS_NET_ZENOH
	ts_net_set_transport(&ts_net_zenoh_transport);
	k_work_init_delayable(&net_work, net_tick);
	k_work_reschedule_for_queue(&k_sys_work_q, &net_work,
				     K_MSEC(CONFIG_TS_NET_TELEM_INTERVAL_MS));
#else
	/* 无传输（测试/桩构建）：不启动周期体——逻辑经测试直调驱动 */
#endif
	return TS_OK;
}
