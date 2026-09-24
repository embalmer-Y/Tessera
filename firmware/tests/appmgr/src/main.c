/* SPDX-License-Identifier: Apache-2.0 */
/* ts-appmgr L1/L2 测试（LLD-ts-appmgr §6）：包安装链 / slot 切换 /
 * 回滚与隔离 / meta 掉电恢复。 */
#include <string.h>
#include <zephyr/ztest.h>
#include <ts/appmgr.h>
#include <ts/store.h>
#include <ts/tsap.h>

static void *appmgr_setup(void)
{
	ts_store_test_reset();
	ts_appmgr_test_reset();
	return NULL;
}

/* 构造一个最小 TSAP 包（V1：头 + 伪 manifest + 伪 wasm + 伪 COSE） */
#define PKG_BUFFER_SIZE 512

static size_t build_minimal_pkg(uint8_t *buf, size_t cap, uint8_t fmt_ver_override)
{
	uint32_t manifest_len = 32;
	uint32_t wasm_len = 64;
	size_t total = TSAP_HEADER_SIZE + manifest_len + wasm_len + 18;

	if (total > cap) return 0;
	memset(buf, 0xAA, total);
	buf[0] = 'T'; buf[1] = 'S'; buf[2] = 'A'; buf[3] = 'P';
	buf[4] = 0; buf[5] = fmt_ver_override;
	buf[6] = (uint8_t)(manifest_len >> 24); buf[7] = (uint8_t)(manifest_len >> 16);
	buf[8] = (uint8_t)(manifest_len >> 8); buf[9] = (uint8_t)manifest_len;
	buf[10] = (uint8_t)(wasm_len >> 24); buf[11] = (uint8_t)(wasm_len >> 16);
	buf[12] = (uint8_t)(wasm_len >> 8); buf[13] = (uint8_t)wasm_len;
	/* rsv = buf[14..15] = 0 */
	/* 伪 COSE：CBOR tag18 + array(4) 头（结构检查足够） */
	buf[TSAP_HEADER_SIZE + manifest_len + wasm_len] = 0xd2;
	buf[TSAP_HEADER_SIZE + manifest_len + wasm_len + 1] = 0x84;
	return total;
}

ZTEST(framework_appmgr, test_install_and_slot_switch)
{
	uint8_t pkg[PKG_BUFFER_SIZE];
	size_t len = build_minimal_pkg(pkg, sizeof(pkg), 1);
	uint8_t root_key[32] = {0};

	zassert_true(len > 0, "pkg built");
	ts_app_info_t info;

	zassert_equal(ts_appmgr_install(pkg, len, root_key, &info), TS_OK);
	zassert_equal(info.state, TS_APP_STAGED);
	zassert_equal(info.active_slot, 1, "first install → slot B（active=0^1）");

	/* slot B 有内容 */
	uint8_t rb[4];

	zassert_equal(ts_store_slot_read(1, 0, rb, 4), TS_OK);
	zassert_equal(rb[0], 'T', "slot B starts with TSAP magic");

	/* 二次安装 → slot A */
	ts_appmgr_test_reset();
	len = build_minimal_pkg(pkg, sizeof(pkg), 1);
	zassert_equal(ts_appmgr_install(pkg, len, root_key, &info), TS_OK);
	zassert_equal(info.active_slot, 0, "second install → slot A（active=1^1=0）");
}

ZTEST(framework_appmgr, test_install_bad_package)
{
	uint8_t pkg[PKG_BUFFER_SIZE];
	uint8_t root_key[32] = {0};
	ts_app_info_t info;

	/* 坏 magic */
	size_t len = build_minimal_pkg(pkg, sizeof(pkg), 1);

	pkg[0] = 'X';
	zassert_equal(ts_appmgr_install(pkg, len, root_key, &info), TS_E_INVALID_SIG);

	/* 坏版本 */
	len = build_minimal_pkg(pkg, sizeof(pkg), 99);
	zassert_equal(ts_appmgr_install(pkg, len, root_key, &info), TS_E_INVALID_SIG);

	/* 截断 */
	len = build_minimal_pkg(pkg, sizeof(pkg), 1);
	zassert_equal(ts_appmgr_install(pkg, 10, root_key, &info), TS_E_INVALID_SIG);

	/* manifest 过短 */
	len = build_minimal_pkg(pkg, sizeof(pkg), 1);
	pkg[9] = 2; /* manifest_len = 2 → COSE 偏移错位 → INVALID_SIG */
	zassert_equal(ts_appmgr_install(pkg, len, root_key, &info), TS_E_INVALID_SIG);
}

ZTEST(framework_appmgr, test_rollback_and_quarantine)
{
	uint8_t pkg[PKG_BUFFER_SIZE];
	size_t len = build_minimal_pkg(pkg, sizeof(pkg), 1);
	uint8_t root_key[32] = {0};
	ts_app_info_t info;

	zassert_equal(ts_appmgr_install(pkg, len, root_key, &info), TS_OK);

	/* 连续回滚 → 计数递增 + slot 切换（需先处于 ACTIVE——安装后为 STAGED，
	 * 这里直接操作内部状态模拟加载完成） */
	extern ts_app_info_t current_app;
	current_app.state = TS_APP_ACTIVE;
	for (int i = 1; i <= TS_APPMGR_ROLLBACK_LIMIT + 1; i++) {
		ts_res_t r = ts_appmgr_rollback();

		if (i <= TS_APPMGR_ROLLBACK_LIMIT) {
			zassert_equal(r, TS_OK, "rollback %d succeeded", i);
		} else {
			zassert_equal(r, TS_E_ROLLBACK_LIMIT, "rollback limit reached at %d", i);
		}
	}
	/* 终态后不可再回滚 */
	ts_appmgr_get_info(&info);
	zassert_equal(info.state, TS_APP_QUARANTINED);
	zassert_equal(info.rollback_count, TS_APPMGR_ROLLBACK_LIMIT);
	zassert_equal(ts_appmgr_rollback(), TS_E_STATE, "quarantined: no further rollback");
}

ZTEST(framework_appmgr, test_meta_persistence)
{
	/* 清 store → 写 meta → 读取 → 掉电模拟（reset + re-read） */
	ts_store_test_reset();
	ts_appmgr_meta_t meta = {.active_slot = 1, .rollback_count = 2, .boot_gen = 7};
	zassert_equal(ts_appmgr_meta_write(&meta), TS_OK);

	ts_appmgr_meta_t rb;
	zassert_equal(ts_appmgr_meta_read(&rb), TS_OK);
	zassert_equal(rb.active_slot, 1);
	zassert_equal(rb.rollback_count, 2);
	zassert_equal(rb.boot_gen, 7);

	/* 重置 ts-appmgr（模拟重启）→ 从 meta 恢复 */
	ts_appmgr_test_reset();
	ts_app_info_t info;

	zassert_equal(ts_appmgr_get_info(&info), TS_OK);
	zassert_equal(info.active_slot, 1, "meta restored after reset");
	zassert_equal(info.rollback_count, 2);
}

ZTEST(framework_appmgr, test_fresh_system_no_app)
{
	ts_appmgr_test_reset();
	ts_appmgr_meta_t meta;

	ts_appmgr_meta_read(&meta);
	zassert_equal(meta.active_slot, 0, "default slot A");
	ts_app_info_t info;

	zassert_equal(ts_appmgr_get_info(&info), TS_OK);
	zassert_equal(info.state, TS_APP_STAGED, "no app: staged default");
}

/* ---- MA3.1：分步安装链（stage_begin/chunk/verify/activate，LLD-A06 §3）-- */

ZTEST(framework_appmgr, test_staged_install_chain)
{
	uint8_t pkg[PKG_BUFFER_SIZE];
	size_t len = build_minimal_pkg(pkg, sizeof(pkg), 1);
	uint8_t root_key[32] = {0};

	zassert_true(len > 0, "pkg built");

	/* 尺寸域：过小/过大拒绝 */
	zassert_equal(ts_appmgr_stage_begin(TSAP_HEADER_SIZE, NULL), TS_E_PARAM);
	zassert_equal(ts_appmgr_stage_begin(CONFIG_TS_STORE_SLOT_SIZE + 1, NULL),
		      TS_E_PARAM);

	/* 未 begin：chunk/verify/activate 全 STATE（fail-closed） */
	zassert_equal(ts_appmgr_stage_chunk(0, pkg, 8, NULL), TS_E_STATE);
	zassert_equal(ts_appmgr_stage_verify(root_key, NULL, NULL, NULL), TS_E_STATE);
	zassert_equal(ts_appmgr_stage_activate(NULL), TS_E_STATE);

	/* begin → slot B；分两半 chunk（断点续传语义） */
	uint8_t slot = 9;
	uint32_t hw = 0;

	zassert_equal(ts_appmgr_stage_begin((uint32_t)len, &slot), TS_OK);
	zassert_equal(slot, 1, "inactive = B（active=0^1）");

	/* 越界 chunk（off+len > total）拒绝 */
	zassert_equal(ts_appmgr_stage_chunk((uint32_t)len, pkg, 4, NULL), TS_E_PARAM);

	zassert_equal(ts_appmgr_stage_chunk(0, pkg, (uint32_t)len / 2, &hw), TS_OK);
	zassert_equal(hw, (uint32_t)len / 2);
	/* 未收满：verify 拒绝 */
	zassert_equal(ts_appmgr_stage_verify(root_key, NULL, NULL, NULL), TS_E_STATE);

	zassert_equal(ts_appmgr_stage_chunk((uint32_t)len / 2, pkg + len / 2,
					    (uint32_t)(len - len / 2), &hw), TS_OK);
	zassert_equal(hw, (uint32_t)len, "high_water = total");

	/* 未验证：activate 拒绝 */
	zassert_equal(ts_appmgr_stage_activate(NULL), TS_E_STATE);

	/* verify：容器事实对拍（manifest 32 / wasm 64 / cose_off = 16+96） */
	uint32_t ml = 0, wl = 0, co = 0;

	zassert_equal(ts_appmgr_stage_verify(root_key, &ml, &wl, &co), TS_OK);
	zassert_equal(ml, 32);
	zassert_equal(wl, 64);
	zassert_equal(co, TSAP_HEADER_SIZE + 32 + 64);

	/* activate：与 install 同效（STAGED + slot B） */
	ts_app_info_t info;

	zassert_equal(ts_appmgr_stage_activate(&info), TS_OK);
	zassert_equal(info.state, TS_APP_STAGED);
	zassert_equal(info.active_slot, 1);
	/* 终态清台：再 activate/chunk = STATE */
	zassert_equal(ts_appmgr_stage_activate(NULL), TS_E_STATE);
	zassert_equal(ts_appmgr_stage_chunk(0, pkg, 8, NULL), TS_E_STATE);

	/* slot 内容 = 包字节（回读对拍首 4B magic） */
	uint8_t rb[4];

	zassert_equal(ts_store_slot_read(1, 0, rb, 4), TS_OK);
	zassert_equal(rb[0], 'T');
}

ZTEST_SUITE(framework_appmgr, NULL, appmgr_setup, NULL, NULL, NULL);
