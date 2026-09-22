/* SPDX-License-Identifier: Apache-2.0 */
/* 双 slot + meta 管理 + 生命周期状态机（LLD-ts-appmgr §3/§4）。
 * meta 经 ts-store 掉电安全 kv（LLD-ts-store §3）；回滚计数超限 → QUARANTINED。 */
#include <string.h>
#include <ts/appmgr.h>
#include <ts/core.h>
#include <ts/store.h>
#include <ts/tsap.h>
#include <zephyr/kernel.h>

ts_app_info_t current_app;
bool initialized;

#ifdef CONFIG_TS_TEST
void ts_appmgr_test_reset(void)
{
	initialized = false;
	memset(&current_app, 0, sizeof(current_app));
}
#endif

ts_res_t ts_appmgr_meta_read(ts_appmgr_meta_t *meta)
{
	if (meta == NULL) return TS_E_PARAM;
	uint16_t len = 0;

	if (ts_store_meta_read(meta, &len) != TS_OK || len != sizeof(*meta)) {
		memset(meta, 0, sizeof(*meta));
		meta->active_slot = 0;
	}
	return TS_OK;
}

ts_res_t ts_appmgr_meta_write(const ts_appmgr_meta_t *meta)
{
	return ts_store_meta_write(meta, (uint16_t)sizeof(*meta));
}

ts_res_t ts_appmgr_get_info(ts_app_info_t *out)
{
	if (out == NULL) return TS_E_PARAM;
	if (!initialized) {
		/* 首次调用：从 meta 恢复（掉电重启路径） */
		ts_appmgr_meta_t meta;

		ts_appmgr_meta_read(&meta);
		current_app.state = TS_APP_STAGED;
		current_app.active_slot = meta.active_slot;
		current_app.rollback_count = meta.rollback_count;
		initialized = true;
	}
	*out = current_app;
	return TS_OK;
}

ts_res_t ts_appmgr_rollback(void)
{
	if (!initialized) return TS_E_STATE;
	if (current_app.state != TS_APP_ACTIVE && current_app.state != TS_APP_ROLLBACK) {
		return TS_E_STATE;
	}
	if (current_app.rollback_count >= TS_APPMGR_ROLLBACK_LIMIT) {
		/* DEC-27 #9：超限 → QUARANTINED（终态，不循环回滚） */
		current_app.state = TS_APP_QUARANTINED;
		const ts_evt_t evt = {.id = TS_EVT_APP_QUARANTINED, .t_ms = ts_time_ms()};
		ts_evt_publish(&evt);
		return TS_E_ROLLBACK_LIMIT;
	}
	/* 切换 slot + 递增计数 + 写 meta（原子） */
	ts_app_state_t prev_state = current_app.state;

	current_app.active_slot ^= 1;
	current_app.rollback_count++;
	current_app.state = TS_APP_ROLLBACK;
	ts_appmgr_meta_t meta = {
		.active_slot = current_app.active_slot,
		.rollback_count = current_app.rollback_count,
		.boot_gen = 0,
		.app_ver_u32 = 0,
	};
	ts_res_t r = ts_appmgr_meta_write(&meta);

	if (r != TS_OK) {
		/* meta 写失败：回退运行时状态并报错——运行态与持久态不得分叉
		 * （impl-review IR-09；重启后回到旧 meta = 安全侧） */
		current_app.active_slot ^= 1;
		current_app.rollback_count--;
		current_app.state = prev_state;
		return r;
	}
	const ts_evt_t evt = {.id = TS_EVT_APP_UNLOADED, .t_ms = ts_time_ms()};
	ts_evt_publish(&evt);
	return TS_OK;
}

ts_res_t ts_appmgr_health_fail(void)
{
	return ts_appmgr_rollback();
}
