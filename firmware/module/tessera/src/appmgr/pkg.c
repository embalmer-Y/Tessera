/* SPDX-License-Identifier: Apache-2.0 */
/* 包接收/验签/写 slot（LLD-ts-appmgr §2/§3）。
 * 验签使用 ed25519（根公钥来自 prov 或测试注入）；失败 → TS_E_INVALID_SIG + 留痕。
 * M2b：COSE 验签骨架 + TSAP 头解析 + slot 写入；WAMR 运行时 = M2b.2。 */
#include <string.h>
#include <ts/appmgr.h>
#include <ts/core.h>
#include <ts/store.h>
#include <ts/tsap.h>
#include <zephyr/kernel.h>
#include "internal.h"

/* V1：简化 ed25519 验签骨架（真实现随 WAMR/M2b.2 引入——当前仅结构校验。
 * WAMR 自带 COSE 验签能力；此处预留接口与哈希校验。 */
static ts_res_t verify_cose_minimal(const uint8_t *cose, uint32_t cose_len,
				     const uint8_t root_pubkey[32])
{
	if (cose == NULL || cose_len < 18 || root_pubkey == NULL) {
		return TS_E_INVALID_SIG;
	}
	/* V1 结构检查：CBOR tag 18 (0xd2) + array(4) 头 */
	if (cose[0] != 0xd2 || cose[1] != 0x84) {
		return TS_E_INVALID_SIG;
	}
	/* TODO M2b.2：接入 ed25519 验签（WAMR crypto 或 mbedtls） */
	return TS_OK;
}

ts_res_t ts_appmgr_install(const uint8_t *pkg_data, size_t pkg_len,
			    const uint8_t root_pubkey[32], ts_app_info_t *out)
{
	if (pkg_data == NULL || root_pubkey == NULL || out == NULL) {
		return TS_E_PARAM;
	}
	/* 1. TSAP 头解析（M2a 定稿：16B 头 / 大端） */
	tsap_view_t v;

	if (!tsap_header_parse(pkg_data, pkg_len, &v)) {
		return TS_E_INVALID_SIG;
	}
	/* 2. COSE 验签（V1：结构检查；M2b.2 接入真实验签） */
	ts_res_t r = verify_cose_minimal(pkg_data + v.cose_off,
					  (uint32_t)(pkg_len - v.cose_off), root_pubkey);

	if (r != TS_OK) {
		const ts_evt_t evt = {.id = TS_EVT_PERM_DENIED, .t_ms = ts_time_ms()};
		ts_evt_publish(&evt);
		return r;
	}
	/* 3. manifest 简单校验（V1：非零长度；完整 CBOR 解码随 M2b.2/WAMR） */
	if (v.manifest_len < 8 || v.manifest_len > 512) {
		return TS_E_PARAM;
	}
	/* 4. 写入 inactive slot（含 COSE，全包写入） */
	ts_appmgr_meta_t meta;

	ts_appmgr_meta_read(&meta);
	uint8_t inactive = meta.active_slot ^ 1;

	r = ts_store_slot_write(inactive, 0, pkg_data, (uint32_t)pkg_len);
	if (r != TS_OK) return r;
	/* 5. 整槽 hash 校验 */
	uint8_t sha[32];

	r = ts_store_slot_hash(inactive, sha);
	if (r != TS_OK) return r;
	/* 6. meta 原子切换（active_slot = inactive） */
	meta.active_slot = inactive;
	meta.rollback_count = 0; /* 新安装重置回滚计数 */
	r = ts_appmgr_meta_write(&meta);
	if (r != TS_OK) return r;
	/* 7. 更新运行时信息 */
	memset(&current_app, 0, sizeof(current_app));
	current_app.state = TS_APP_STAGED;
	current_app.active_slot = inactive;
	current_app.rollback_count = 0;
	*out = current_app;
	initialized = true;
	const ts_evt_t evt = {.id = TS_EVT_APP_LOADED, .t_ms = ts_time_ms()};
	ts_evt_publish(&evt);
	return TS_OK;
}
