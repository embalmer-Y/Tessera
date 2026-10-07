/* SPDX-License-Identifier: Apache-2.0 */
/* ts-appmgr L1/L2 测试（LLD-ts-appmgr §6）：包安装链 / slot 切换 /
 * 回滚与隔离 / meta 掉电恢复。
 * DEC-49（Q-29④）：真验签语义——夹具 = 预签 v2 包（测试根签名，
 * fixture_pkg.h 机械生成）；篡改矩阵在副本上翻字节断言 INVALID_SIG。
 * IR2-07：回滚目标槽验证（坏/空槽不翻转）+ meta 双损如实 E_IO。 */
#include <string.h>
#include <zephyr/sys/printk.h>
#include <zephyr/ztest.h>
#include <ts/appmgr.h>
#include <ts/store.h>
#include <ts/tsap.h>

#include "fixture_pkg.h"

static void *appmgr_setup(void)
{
	ts_store_test_reset();
	ts_appmgr_test_reset();
	return NULL;
}

#define PKG_BUFFER_SIZE 1024

/* fixture 头字段（生成期事实，运行期自头读——与容器一致性对拍） */
static uint32_t fx_ml, fx_wl, fx_total;

static void fx_fields(void)
{
	fx_ml = ((uint32_t)fixture_pkg[6] << 24) | ((uint32_t)fixture_pkg[7] << 16) |
		((uint32_t)fixture_pkg[8] << 8) | fixture_pkg[9];
	fx_wl = ((uint32_t)fixture_pkg[10] << 24) | ((uint32_t)fixture_pkg[11] << 16) |
		((uint32_t)fixture_pkg[12] << 8) | fixture_pkg[13];
	fx_total = sizeof(fixture_pkg);
}

static const uint8_t root_key[32] = {0}; /* TEST 构建：验签对象 = 固定测试根 */

ZTEST(framework_appmgr, test_install_and_slot_switch)
{
	fx_fields();
	ts_app_info_t info;

	ts_res_t ir = ts_appmgr_install(fixture_pkg, fx_total, root_key, &info);

	zassert_equal(ir, TS_OK, "预签 v2 包安装（真 ed25519 验签）");
	zassert_equal(info.state, TS_APP_STAGED);
	zassert_equal(info.active_slot, 1, "first install → slot B（active=0^1）");

	uint8_t rb[4];

	zassert_equal(ts_store_slot_read(1, 0, rb, 4), TS_OK);
	zassert_equal(rb[0], 'T', "slot B starts with TSAP magic");

	/* 二次安装 → slot A */
	ts_appmgr_test_reset();
	zassert_equal(ts_appmgr_install(fixture_pkg, fx_total, root_key, &info), TS_OK);
	zassert_equal(info.active_slot, 0, "second install → slot A（active=1^1=0）");
}

ZTEST(framework_appmgr, test_install_tamper_matrix)
{
	fx_fields();
	static uint8_t pkg[PKG_BUFFER_SIZE];
	ts_app_info_t info;

	/* 坏 magic */
	memcpy(pkg, fixture_pkg, fx_total);
	pkg[0] = 'X';
	zassert_equal(ts_appmgr_install(pkg, fx_total, root_key, &info),
		      TS_E_INVALID_SIG);

	/* v1 头（fmt_ver=1）= fail-closed 拒收（DEC-49②：无兼容装载） */
	memcpy(pkg, fixture_pkg, fx_total);
	pkg[4] = 0; pkg[5] = 1; pkg[14] = 0; pkg[15] = 0;
	zassert_equal(ts_appmgr_install(pkg, fx_total, root_key, &info),
		      TS_E_INVALID_SIG, "v1 拒收");

	/* 未知 flags */
	memcpy(pkg, fixture_pkg, fx_total);
	pkg[15] = 0x02;
	zassert_equal(ts_appmgr_install(pkg, fx_total, root_key, &info),
		      TS_E_INVALID_SIG);

	/* 篡改摘要（位腐 → sha256 对拍失败） */
	memcpy(pkg, fixture_pkg, fx_total);
	pkg[16] ^= 0x01;
	zassert_equal(ts_appmgr_install(pkg, fx_total, root_key, &info),
		      TS_E_INVALID_SIG, "digest 篡改拒收");

	/* 篡改 manifest 内容字节（摘要与签名双双失败） */
	memcpy(pkg, fixture_pkg, fx_total);
	pkg[TSAP_CONTENT_OFF] ^= 0x01;
	zassert_equal(ts_appmgr_install(pkg, fx_total, root_key, &info),
		      TS_E_INVALID_SIG, "manifest 篡改拒收");

	/* 篡改 wasm 字节 */
	memcpy(pkg, fixture_pkg, fx_total);
	pkg[TSAP_CONTENT_OFF + fx_ml] ^= 0x01;
	zassert_equal(ts_appmgr_install(pkg, fx_total, root_key, &info),
		      TS_E_INVALID_SIG, "wasm 篡改拒收");

	/* 篡改签名（末 64B 翻一位 → ed25519 拒收） */
	memcpy(pkg, fixture_pkg, fx_total);
	pkg[fx_total - 1] ^= 0x01;
	zassert_equal(ts_appmgr_install(pkg, fx_total, root_key, &info),
		      TS_E_INVALID_SIG, "sig 篡改拒收");

	/* 非测试根签名的包 = 拒收：构造双字段错位（签名段首字节破坏） */
	memcpy(pkg, fixture_pkg, fx_total);
	pkg[fx_total - 70] ^= 0x01;
	zassert_equal(ts_appmgr_install(pkg, fx_total, root_key, &info),
		      TS_E_INVALID_SIG);

	/* 截断 */
	zassert_equal(ts_appmgr_install(fixture_pkg, 10, root_key, &info),
		      TS_E_INVALID_SIG);
}

ZTEST(framework_appmgr, test_rollback_closed_loop)
{
	/* 套件级 setup 不逐用例复位——本用例自取确定基线 */
	ts_store_test_reset();
	ts_appmgr_test_reset();

	/* IR2-07：单槽已装 → 回滚目标槽为空 → 如实失败不翻转 */
	ts_app_info_t info;

	zassert_equal(ts_appmgr_install(fixture_pkg, sizeof(fixture_pkg),
					root_key, &info), TS_OK);
	zassert_equal(info.active_slot, 1, "净基线首装 slot B（slot A 空）");
	extern ts_app_info_t current_app;

	current_app.state = TS_APP_ACTIVE;
	uint8_t before = current_app.active_slot;

	zassert_equal(ts_appmgr_rollback(), TS_E_IO, "空目标槽 = 拒绝回滚");
	zassert_equal(current_app.active_slot, before, "不翻转");

	/* 双槽皆装（交替）→ 回滚验证通过 → 翻转 + 计数 */
	zassert_equal(ts_appmgr_install(fixture_pkg, sizeof(fixture_pkg),
					root_key, &info), TS_OK);
	zassert_equal(info.active_slot, 0, "次装 slot A（双有效槽）");
	current_app.state = TS_APP_ACTIVE;
	for (int i = 1; i <= TS_APPMGR_ROLLBACK_LIMIT; i++) {
		zassert_equal(ts_appmgr_rollback(), TS_OK, "rollback %d（双有效槽）", i);
		zassert_equal(current_app.rollback_count, i);
	}
	zassert_equal(ts_appmgr_rollback(), TS_E_ROLLBACK_LIMIT,
		      "rollback limit reached");
	ts_appmgr_get_info(&info);
	zassert_equal(info.state, TS_APP_QUARANTINED);
	zassert_equal(info.rollback_count, TS_APPMGR_ROLLBACK_LIMIT);
	zassert_equal(ts_appmgr_rollback(), TS_E_STATE, "quarantined: no further");
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

	/* meta 摘要随载（DEC-49②） */
	ts_app_info_t info;

	zassert_equal(ts_appmgr_install(fixture_pkg, sizeof(fixture_pkg),
					root_key, &info), TS_OK);
	ts_appmgr_meta_t m2;

	zassert_equal(ts_appmgr_meta_read(&m2), TS_OK);
	uint8_t hdr_digest[32];

	zassert_equal(ts_store_slot_read(info.active_slot, TSAP_DIGEST_OFF,
					 hdr_digest, 32), TS_OK);
	zassert_equal(memcmp(m2.content_digest, hdr_digest, 32), 0,
		      "meta 摘要 == 头摘要");
}

ZTEST(framework_appmgr, test_fresh_system_no_app)
{
	/* IR2-07：空板（无有效 meta）= meta_read 如实 E_IO（不静默伪造成
	 * 有效态）；观测面 get_info 仍给缺省可观测态 */
	ts_appmgr_test_reset();
	ts_appmgr_meta_t meta;

	zassert_equal(ts_appmgr_meta_read(&meta), TS_E_IO, "空板 = E_IO（如实）");
	ts_app_info_t info;

	zassert_equal(ts_appmgr_get_info(&info), TS_OK);
	zassert_equal(info.active_slot, 0, "缺省 slot 0（可观测）");
	zassert_equal(info.state, TS_APP_STAGED, "no app: staged default");
	/* boot：meta 不可读 → 不装载（IR2-07：不静默装 slot 0） */
	zassert_equal(ts_appmgr_boot_start(), TS_E_STATE, "boot 拒绝静默装载");
}

/* ---- MA3.1：分步安装链（stage_begin/chunk/verify/activate，LLD-A06 §3）-- */

ZTEST(framework_appmgr, test_staged_install_chain)
{
	fx_fields();
	static uint8_t pkg[PKG_BUFFER_SIZE];

	memcpy(pkg, fixture_pkg, fx_total);
	ts_store_test_reset();

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

	zassert_equal(ts_appmgr_stage_begin(fx_total, &slot), TS_OK);
	zassert_equal(slot, 1, "inactive = B（active=0^1）");

	zassert_equal(ts_appmgr_stage_chunk(fx_total, pkg, 4, NULL), TS_E_PARAM,
		      "越界 chunk 拒绝");

	zassert_equal(ts_appmgr_stage_chunk(0, pkg, fx_total / 2, &hw), TS_OK);
	zassert_equal(hw, fx_total / 2);
	zassert_equal(ts_appmgr_stage_verify(root_key, NULL, NULL, NULL), TS_E_STATE,
		      "未收满：verify 拒绝");

	zassert_equal(ts_appmgr_stage_chunk(fx_total / 2, pkg + fx_total / 2,
					    fx_total - fx_total / 2, &hw), TS_OK);
	zassert_equal(hw, fx_total, "high_water = total");

	zassert_equal(ts_appmgr_stage_activate(NULL), TS_E_STATE,
		      "未验证：activate 拒绝");

	/* verify：容器事实对拍（ml/wl 与生成期头一致；cose_off = 48+ml+wl） */
	uint32_t ml = 0, wl = 0, co = 0;

	zassert_equal(ts_appmgr_stage_verify(root_key, &ml, &wl, &co), TS_OK,
		      "真验签通过（测试根）");
	zassert_equal(ml, fx_ml);
	zassert_equal(wl, fx_wl);
	zassert_equal(co, TSAP_CONTENT_OFF + fx_ml + fx_wl);

	ts_app_info_t info;

	zassert_equal(ts_appmgr_stage_activate(&info), TS_OK);
	zassert_equal(info.state, TS_APP_STAGED);
	zassert_equal(info.active_slot, 1);
	zassert_equal(ts_appmgr_stage_activate(NULL), TS_E_STATE, "终态清台");
	zassert_equal(ts_appmgr_stage_chunk(0, pkg, 8, NULL), TS_E_STATE);

	uint8_t rb[4];

	zassert_equal(ts_store_slot_read(1, 0, rb, 4), TS_OK);
	zassert_equal(rb[0], 'T');
}

/* ---- 密码件基线：sha256 NIST 向量（store/sha256.c 实现护栏；DEC-49 复用）-- */
#include "../../../module/tessera/src/store/internal.h"

ZTEST(framework_appmgr, test_sha256_vectors)
{
	/* FIPS 180-4 标准向量 */
	static const uint8_t vec_abc[32] = {
		0xba, 0x78, 0x16, 0xbf, 0x8f, 0x01, 0xcf, 0xea, 0x41, 0x41, 0x40,
		0xde, 0x5d, 0xae, 0x22, 0x23, 0xb0, 0x03, 0x61, 0xa3, 0x96, 0x17,
		0x7a, 0x9c, 0xb4, 0x10, 0xff, 0x61, 0xf2, 0x00, 0x15, 0xad,
	};
	static const uint8_t vec_empty[32] = {
		0xe3, 0xb0, 0xc4, 0x42, 0x98, 0xfc, 0x1c, 0x14, 0x9a, 0xfb, 0xf4,
		0xc8, 0x99, 0x6f, 0xb9, 0x24, 0x27, 0xae, 0x41, 0xe4, 0x64, 0x9b,
		0x93, 0x4c, 0xa4, 0x95, 0x99, 0x1b, 0x78, 0x52, 0xb8, 0x55,
	};
	uint8_t out[32];
	ts_sha256_ctx_t c;

	ts_sha256_init(&c);
	ts_sha256_update(&c, (const uint8_t *)"abc", 3);
	ts_sha256_final(&c, out);
	zassert_equal(memcmp(out, vec_abc, 32), 0, "sha256(abc)");

	ts_sha256_init(&c);
	ts_sha256_final(&c, out);
	zassert_equal(memcmp(out, vec_empty, 32), 0, "sha256(empty)");

	/* 流式 = 一次等价（21B 分三段 7B 喂入，跨块边界语义） */
	static const uint8_t msg21[21] = "abcabcabcabcabcabcabc";

	ts_sha256_init(&c);
	for (int i = 0; i < 3; i++) {
		ts_sha256_update(&c, msg21 + i * 7, 7);
	}
	ts_sha256_final(&c, out);
	uint8_t ref[32];
	ts_sha256_ctx_t c2;

	ts_sha256_init(&c2);
	ts_sha256_update(&c2, msg21, sizeof(msg21));
	ts_sha256_final(&c2, ref);
	zassert_equal(memcmp(out, ref, 32), 0, "流式一致性");
}

/* ---- 密码件基线：tweetnacl 内建自测（已知向量 sm/pub → crypto_sign_open）
 * ——模块构建下的库护栏（调试期别名缺陷即由本面拦截路径演化而来）-------- */
ZTEST(framework_appmgr, test_tnacl_selftest)
{
	extern int ts_tnacl_selftest(void);

	zassert_equal(ts_tnacl_selftest(), 0, "tweetnacl 已知向量验签");
}

ZTEST_SUITE(framework_appmgr, NULL, appmgr_setup, NULL, NULL, NULL);
