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

/* ---- boot 装载（M2b.2 收尾单元；HLD §4.4-8：APP 故障不阻塞启动）--------- */

#ifdef CONFIG_TS_APP_WAMR
#include "../net/internal.h" /* ts_cbor_* 读助手（tessera 模块内复用） */

static uint8_t boot_wasm_buf[CONFIG_TS_APP_LOAD_MAX];
static char boot_caps[160];

ts_res_t ts_appmgr_boot_start(void)
{
	ts_appmgr_meta_t meta;

	ts_appmgr_meta_read(&meta);
	uint8_t hdr[TSAP_HEADER_SIZE];

	if (ts_store_slot_read(meta.active_slot, 0, hdr, sizeof(hdr)) != TS_OK) {
		return TS_E_IO;
	}
	if (memcmp(hdr, "TSAP", 4) != 0) {
		return TS_E_NOTFOUND; /* 空/未写 slot = 无 APP（boot 不阻塞） */
	}
	uint32_t ml = ((uint32_t)hdr[6] << 24) | ((uint32_t)hdr[7] << 16) |
		      ((uint32_t)hdr[8] << 8) | hdr[9];
	uint32_t wl = ((uint32_t)hdr[10] << 24) | ((uint32_t)hdr[11] << 16) |
		      ((uint32_t)hdr[12] << 8) | hdr[13];

	if (ml == 0 || ml > 512 || wl == 0 || wl > sizeof(boot_wasm_buf)) {
		return TS_E_PARAM; /* 容器头越界（装载上限 = CONFIG_TS_APP_LOAD_MAX） */
	}
	static uint8_t man[512];

	if (ts_store_slot_read(meta.active_slot, TSAP_HEADER_SIZE, man, ml) != TS_OK) {
		return TS_E_IO;
	}
	/* manifest 走查（TsapManifest v1 canonical CBOR；按键名分发——
	 * fail-closed：未知键拒绝）。caps 组合为 ';' 分隔串（runtime 逐条 parse，
	 * ts_perm_parse 语义 = 位或合并）。stack_kb/heap_kb V1 消耗运行时常量
	 * （LLD §7 已知限制——manifest 读取但暂不生效，板级内存预算批兑现）。 */
	ts_cbor_rd_t r;
	uint32_t pairs;

	ts_cbor_rd_init(&r, man, ml);
	if (!ts_cbor_map_open(&r, &pairs)) {
		return TS_E_PARAM;
	}
	boot_caps[0] = '\0';
	size_t caps_len = 0;

	for (uint32_t i = 0; i < pairs; i++) {
		char key[16];

		if (!ts_cbor_tstr(&r, key, sizeof(key))) {
			return TS_E_PARAM;
		}
		if (strcmp(key, "caps") == 0) {
			uint32_t n;

			if (!ts_cbor_array_open(&r, &n)) {
				return TS_E_PARAM;
			}
			for (uint32_t j = 0; j < n; j++) {
				char cap[48];

				if (!ts_cbor_tstr(&r, cap, sizeof(cap))) {
					return TS_E_PARAM;
				}
				size_t cl = strlen(cap);

				if (caps_len + cl + 2 >= sizeof(boot_caps)) {
					return TS_E_PARAM;
				}
				if (caps_len > 0) {
					boot_caps[caps_len++] = ';';
				}
				memcpy(boot_caps + caps_len, cap, cl);
				caps_len += cl;
				boot_caps[caps_len] = '\0';
			}
		} else if (strcmp(key, "app_id") == 0 || strcmp(key, "app_ver") == 0) {
			char val[64];

			if (!ts_cbor_tstr(&r, val, sizeof(val))) {
				return TS_E_PARAM;
			}
			if (strcmp(key, "app_id") == 0) {
				strncpy(current_app.app_id, val,
					sizeof(current_app.app_id) - 1);
				current_app.app_id[sizeof(current_app.app_id) - 1] = '\0';
			} else {
				strncpy(current_app.app_ver, val,
					sizeof(current_app.app_ver) - 1);
				current_app.app_ver[sizeof(current_app.app_ver) - 1] = '\0';
			}
		} else if (strcmp(key, "min_fw_ver") == 0) {
			char val[32];

			if (!ts_cbor_tstr(&r, val, sizeof(val))) {
				return TS_E_PARAM;
			}
		} else if (strcmp(key, "stack_kb") == 0 || strcmp(key, "heap_kb") == 0) {
			uint64_t v;

			if (!ts_cbor_uint(&r, &v)) {
				return TS_E_PARAM;
			}
			/* V1 消耗运行时常量（见上注释） */
		} else if (strcmp(key, "exports") == 0) {
			uint32_t n;

			if (!ts_cbor_array_open(&r, &n)) {
				return TS_E_PARAM;
			}
			for (uint32_t j = 0; j < n; j++) {
				char ex[48];

				if (!ts_cbor_tstr(&r, ex, sizeof(ex))) {
					return TS_E_PARAM;
				}
			}
		} else {
			return TS_E_PARAM; /* 未知键 = schema v1 之外（fail-closed） */
		}
	}
	if (ts_store_slot_read(meta.active_slot, TSAP_HEADER_SIZE + ml,
			       boot_wasm_buf, wl) != TS_OK) {
		return TS_E_IO;
	}
	/* V1 运行时数值 app_id = 1（单活跃 APP；审计字符串归因在 current_app） */
	ts_res_t sr = ts_appmgr_app_start(1, boot_wasm_buf, wl, boot_caps);

	if (sr == TS_OK) {
		current_app.state = TS_APP_ACTIVE; /* STAGED →（加载周期）→ ACTIVE */
	}
	return sr;
}
#else
ts_res_t ts_appmgr_boot_start(void)
{
	return TS_E_STATE; /* WAMR 未编入（CONFIG_TS_APP_WAMR） */
}
#endif
