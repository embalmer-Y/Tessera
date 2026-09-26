/* SPDX-License-Identifier: Apache-2.0 */
/* framework.app（DEC-43 接线批）：APP 运行时宿主端到端——
 *   test_01 生命周期：start → app_init 经 natives 写 gpio → mailbox evt
 *           驱动 app_evt → gpio 随动 → stop 回收（重复停止拒绝）；
 *   test_02 权限拒绝：caps 不含 gpio → init 写被调用期裁决拒绝（-3）
 *           + TS_EVT_PERM_DENIED 留痕（合同 10）；
 *   test_03 健康失败自停：控制 evt 置 health=1 → 连续〔DEC-27：3〕探针
 *           失败 → health_fail（回滚入口）+ 线程自停。 */
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <ts/appmgr.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/safety.h>
#include <ts/store.h>
#include <ts/tsap.h>
#include "../../../module/tessera/src/net/internal.h"
#include "app_wasm.h"

static const ts_out_ch_t ag_ch = {
	.uid = "ag0", .kind = TS_CH_GPIO,
	.poweron = {.b = false}, .linkloss = {.b = false}, .fault = {.b = false},
};

static bool gpio_val(void)
{
	ts_out_value_t v;

	if (ts_safety_readback("ag0", &v) != TS_OK) {
		return false;
	}
	return v.b;
}

static bool wait_gpio(bool want)
{
	for (int i = 0; i < 300; i++) {
		if (gpio_val() == want) {
			return true;
		}
		k_msleep(10);
	}
	return false;
}

static const ts_hal_dev_desc_t ag_dev = {.uid = "ag0", .kind = TS_DEV_GPIO_OUT};
static bool hal_done;

static void suite_setup_channel(void)
{
	ts_safety_test_reset();
	ts_appmgr_app_test_reset();
	if (!hal_done) { /* hal 注册表进程级共享（无复位钩子）——一次即可 */
		zassert_equal(ts_hal_register_dev(&ag_dev), TS_OK);
		hal_done = true;
	}
	zassert_equal(ts_safety_register_channel(&ag_ch), TS_OK);
	ts_safety_set_link(true);
}

ZTEST(framework_app, test_01_lifecycle)
{
	suite_setup_channel();
	zassert_equal(ts_appmgr_app_start(9, app_wasm, app_wasm_len,
					  "gpio:write:0-3"), TS_OK);
	zassert_true(ts_appmgr_app_running(), "运行中");
	zassert_true(wait_gpio(true),
		     "app_init 经 natives→perm→唯一写路径 落 gpio=1");

	zassert_equal(ts_appmgr_app_evt(0), TS_OK);
	zassert_true(wait_gpio(false), "app_evt(0) → gpio=0");
	zassert_equal(ts_appmgr_app_evt(3), TS_OK);
	zassert_true(wait_gpio(true), "app_evt(3) → gpio=1");

	struct ts_app_rt_stats st;

	ts_appmgr_app_stats(&st);
	zassert_true(st.evt_seen >= 2, "mailbox 事件已消费（DR-14）");
	zassert_equal(st.init_res, 0, "app_init 返回 0");
	zassert_equal(st.health_fails, 0, "健康无失败");

	zassert_equal(ts_appmgr_app_stop(), TS_OK);
	zassert_false(ts_appmgr_app_running());
	zassert_equal(ts_appmgr_app_stop(), TS_E_STATE, "重复停止拒绝");
}

static int perm_seen;

static void on_perm(const ts_evt_t *e, void *u)
{
	ARG_UNUSED(e);
	ARG_UNUSED(u);
	perm_seen++;
}

ZTEST(framework_app, test_02_perm_denial)
{
	suite_setup_channel();
	perm_seen = 0;
	zassert_equal(ts_evt_subscribe(TS_EVT_PERM_DENIED, on_perm, NULL), TS_OK);

	zassert_equal(ts_appmgr_app_start(9, app_wasm, app_wasm_len,
					  "adc:read:0-3"), TS_OK,
		      "启动成功（无 gpio 能力——运行期拒绝）");
	for (int i = 0; i < 100 && perm_seen == 0; i++) {
		k_msleep(10);
	}
	zassert_false(gpio_val(), "写被拒——gpio 保持关");
	zassert_true(perm_seen > 0, "TS_EVT_PERM_DENIED 留痕（合同 10）");
	struct ts_app_rt_stats st;

	ts_appmgr_app_stats(&st);
	zassert_equal(st.init_res, (uint32_t)TS_E_PERM,
		      "app_init 收到 -3（调用期权限裁决）");
	zassert_equal(ts_appmgr_app_stop(), TS_OK);
}

ZTEST(framework_app, test_03_health_fail_stops)
{
	suite_setup_channel();
	zassert_equal(ts_appmgr_app_start(9, app_wasm, app_wasm_len,
					  "gpio:write:0-3"), TS_OK);
	zassert_true(wait_gpio(true), "init 写生效");
	zassert_equal(ts_appmgr_app_evt(0x100), TS_OK, "控制通道：置健康失败");
	for (int i = 0; i < 600 && ts_appmgr_app_running(); i++) {
		k_msleep(10);
	}
	struct ts_app_rt_stats st;

	ts_appmgr_app_stats(&st);
	zassert_false(st.running, "连续 3 败后自停（DEC-27）");
	zassert_true(st.health_failed, "健康失败路径触发");
	zassert_true(st.health_fails >= 3);
	zassert_equal(ts_appmgr_app_stop(), TS_OK, "自停后 stop 清尾回收");
}

ZTEST(framework_app, test_04_boot_slot_load)
{
	suite_setup_channel();
	ts_store_test_reset();
	ts_appmgr_test_reset();

	/* 构造最小 TSAP 容器：manifest（canonical 七键）+ 夹具 wasm + COSE 结构尾 */
	static uint8_t pkg[1024];
	uint8_t man[256];
	size_t mp = 0;

	zassert_true(ts_cbor_put_map(man, sizeof(man), &mp, 7));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "app_id"));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "com.tessera.fixture"));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "app_ver"));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "0.1.0"));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "min_fw_ver"));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "0.0.1"));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "caps"));
	zassert_true(ts_cbor_put_array(man, sizeof(man), &mp, 1));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "gpio:write:0-3"));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "stack_kb"));
	zassert_true(ts_cbor_put_uint(man, sizeof(man), &mp, 4));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "heap_kb"));
	zassert_true(ts_cbor_put_uint(man, sizeof(man), &mp, 8));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "exports"));
	zassert_true(ts_cbor_put_array(man, sizeof(man), &mp, 1));
	zassert_true(ts_cbor_put_tstr(man, sizeof(man), &mp, "health_ping"));

	uint32_t ml = (uint32_t)mp;
	uint32_t wl = app_wasm_len;
	size_t total = TSAP_HEADER_SIZE + ml + wl + 18;

	zassert_true(total <= sizeof(pkg), "容器尺寸");
	memset(pkg, 0, total);
	pkg[0] = 'T'; pkg[1] = 'S'; pkg[2] = 'A'; pkg[3] = 'P';
	pkg[4] = 0; pkg[5] = 1;
	pkg[6] = (uint8_t)(ml >> 24); pkg[7] = (uint8_t)(ml >> 16);
	pkg[8] = (uint8_t)(ml >> 8); pkg[9] = (uint8_t)ml;
	pkg[10] = (uint8_t)(wl >> 24); pkg[11] = (uint8_t)(wl >> 16);
	pkg[12] = (uint8_t)(wl >> 8); pkg[13] = (uint8_t)wl;
	memcpy(pkg + TSAP_HEADER_SIZE, man, ml);
	memcpy(pkg + TSAP_HEADER_SIZE + ml, app_wasm, wl);
	pkg[TSAP_HEADER_SIZE + ml + wl] = 0xd2;
	pkg[TSAP_HEADER_SIZE + ml + wl + 1] = 0x84;

	/* 分步安装链（TEST 构建 = 结构级验签）→ meta 切换 */
	uint8_t slot = 0;
	uint32_t hw = 0;
	zassert_equal(ts_appmgr_stage_begin((uint32_t)total, &slot), TS_OK);
	zassert_equal(ts_appmgr_stage_chunk(0, pkg, (uint32_t)total, &hw), TS_OK);
	const uint8_t root_key[32] = {0}; /* TEST：prov 缺省（结构级验签） */

	zassert_equal(ts_appmgr_stage_verify(root_key, NULL, NULL, NULL), TS_OK);
	ts_app_info_t info;
	zassert_equal(ts_appmgr_stage_activate(&info), TS_OK);

	/* boot 装载（步骤 8 语义）：manifest 走查 + caps 组合 + wasm → 运行 */
	zassert_equal(ts_appmgr_boot_start(), TS_OK, "boot 装载");
	zassert_true(wait_gpio(true), "fixture init 写 gpio=1（经 slot 全链）");
	zassert_equal(ts_appmgr_app_evt(0), TS_OK);
	zassert_true(wait_gpio(false), "evt 驱动");
	ts_app_info_t after;
	zassert_equal(ts_appmgr_get_info(&after), TS_OK);
	zassert_equal(after.state, TS_APP_ACTIVE, "装载后 STAGED→ACTIVE");
	zassert_equal(strcmp(after.app_id, "com.tessera.fixture"), 0,
		      "manifest app_id 提取");
	zassert_equal(ts_appmgr_app_stop(), TS_OK);
}

ZTEST_SUITE(framework_app, NULL, NULL, NULL, NULL, NULL);
