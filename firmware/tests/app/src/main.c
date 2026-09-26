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

ZTEST_SUITE(framework_app, NULL, NULL, NULL, NULL, NULL);
