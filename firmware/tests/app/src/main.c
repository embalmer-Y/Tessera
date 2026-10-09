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
#include "boot_pkg.h"

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

	/* DEC-49④：boot E2E = 预签 v2 包（native_app.wasm 真 wasm + 测试根
	 * 签名，boot_pkg.h 机械生成）——真验签/真走查/真装载全链。 */
	uint32_t total = sizeof(boot_pkg);
	const uint8_t root_key[32] = {0}; /* TEST 构建：验签对象 = 固定测试根 */
	ts_app_info_t inst_info;

	zassert_equal(ts_appmgr_install(boot_pkg, total, root_key, &inst_info),
		      TS_OK, "install 预签包（真 ed25519）");

	/* B2 批：回滚计数随载恢复——装载前改写 meta.count=2，装载后 get-app
	 * 须如实报 2（旧缺陷 = 恒 0；flash 实测对拍拦下）。 */
	{
		ts_appmgr_meta_t m;

		zassert_equal(ts_appmgr_meta_read(&m), TS_OK);
		m.rollback_count = 2;
		zassert_equal(ts_appmgr_meta_write(&m), TS_OK);
	}

	/* boot 装载（步骤 8 语义）：摘要快校验 + manifest 走查 + caps 组合 +
	 * wasm → 运行 */
	zassert_equal(ts_appmgr_boot_start(), TS_OK, "boot 装载");
	zassert_true(wait_gpio(true), "fixture init 写 gpio=1（经 slot 全链）");
	zassert_equal(ts_appmgr_app_evt(0), TS_OK);
	zassert_true(wait_gpio(false), "evt 驱动");
	ts_app_info_t after;
	zassert_equal(ts_appmgr_get_info(&after), TS_OK);
	zassert_equal(after.state, TS_APP_ACTIVE, "装载后 STAGED→ACTIVE");
	zassert_equal(after.rollback_count, 2, "回滚计数随载恢复（B2）");
	zassert_equal(strcmp(after.app_id, "com.tessera.fixture"), 0,
		      "manifest app_id 提取");
	zassert_equal(ts_appmgr_app_stop(), TS_OK);
}

/* ---- ts-fs 能力面（DEC-47④⑤，MD1.2e）------------------------------------
 * 双层裁决 fail-closed：class/op 位图 + fs_paths 前缀白名单（边界语义：
 * 前缀后须 '/' 或恰好等长——防前缀绕过）；native_sim 无挂载盘 →
 * 授权路径走到后端报 TS_E_IO（IO 面），未授权路径在门内即拒 TS_E_PERM。 */
ZTEST(framework_app, test_05_fs_gates)
{
	ts_perm_table_t table;
	ts_ctx_t ctx;

	ts_perm_table_init(&table);
	zassert_equal(ts_perm_parse("fs:read:0", &table), TS_OK, "fs 类解析");
	zassert_equal(ts_perm_parse("fs:write:0", &table), TS_OK);
	zassert_equal(ts_perm_parse("fs:list:0", &table), TS_OK);
	zassert_equal(ts_perm_parse("fs:delete:0", &table), TS_OK);
	zassert_equal(ts_perm_parse("fs:append:0", &table), TS_E_PARAM,
		      "未知 op fail-closed");
	zassert_equal(ts_hal_bind_context(&ctx, 0x5a, &table), TS_OK);

	/* 未绑定 fs_paths：一切路径拒绝（参数合法 → 门内拒绝） */
	uint8_t b0[4];
	uint16_t n0 = sizeof(b0);

	zassert_equal(ts_fs_read(ctx, "/SD:/x", 0, b0, &n0), TS_E_PERM,
		      "未绑定白名单 = 拒绝");

	zassert_equal(ts_fs_paths_bind_ctx(ctx, "/SD:/apps;/SD:/tmp"), TS_OK);
	/* 前缀边界：等长 ✓ / 子路径 ✓ / 前缀绕过 ✗ */
	zassert_equal(ts_fs_path_allowed(ctx, "/SD:/apps"), TS_OK);
	zassert_equal(ts_fs_path_allowed(ctx, "/SD:/apps/a.txt"), TS_OK);
	zassert_equal(ts_fs_path_allowed(ctx, "/SD:/apps-secret"), TS_E_PERM,
		      "前缀绕过防护");
	zassert_equal(ts_fs_path_allowed(ctx, "/SD:/etc"), TS_E_PERM);
	zassert_equal(ts_fs_path_allowed(ctx, "SD:/apps"), TS_E_PARAM,
		      "非绝对路径");

	/* 授权路径 + 位图 op 通过 → 后端（native_sim 无挂载 → TS_E_IO） */
	uint8_t b[4];
	uint16_t n = sizeof(b);

	zassert_equal(ts_fs_read(ctx, "/SD:/apps/a.txt", 0, b, &n), TS_E_IO,
		      "授权读 → 后端 IO（无挂载，如实）");
	/* read 类 op 未授权路径：门内拒绝 */
	zassert_equal(ts_fs_read(ctx, "/SD:/etc/a", 0, b, &n), TS_E_PERM);

	/* class 位图缺 write op（新 ctx 只授 read）→ 门内拒绝 */
	ts_perm_table_init(&table);
	zassert_equal(ts_perm_parse("fs:read:0", &table), TS_OK);
	zassert_equal(ts_hal_bind_context(&ctx, 0x5b, &table), TS_OK);
	zassert_equal(ts_fs_paths_bind_ctx(ctx, "/SD:/apps"), TS_OK);
	zassert_equal(ts_fs_write(ctx, "/SD:/apps/a", 0, b, 0), TS_E_PERM,
		      "op 位图缺 write = 拒绝");
	ts_hal_unbind_context(&ctx);
}

/* ---- ts-av 能力面（DEC-47③⑥，MD1.2g）------------------------------------
 * 读类 fail-closed：av:read:0 位图 + av_fmt/av_w/av_h 配置绑定（manifest
 * 声明 → 随载绑定；未声明 = TS_E_STATE）。native_sim 无摄像头 chosen →
 * 权限+配置齐全时走到后端报 TS_E_IO（IO 面）；权限/配置缺口在门内即拒。
 * 发布面（TS_NET=y）：hal 权限/参数门 + avq 入队；发送/信封/重试语义在
 * framework.net test_12_avq 覆盖。 */
ZTEST(framework_app, test_06_av_gates)
{
	ts_perm_table_t table;
	ts_ctx_t ctx;

	/* av 类文法（op = read；DEC-47⑤） */
	ts_perm_table_init(&table);
	zassert_equal(ts_perm_parse("av:read:0", &table), TS_OK, "av 类解析");
	zassert_equal(ts_perm_parse("av:capture:0", &table), TS_E_PARAM,
		      "未知 op fail-closed（V1 av op = read）");
	zassert_equal(ts_hal_bind_context(&ctx, 0x5c, &table), TS_OK);

	/* 未绑定配置（manifest 未声明 av_*）：权限过、配置缺 → 拒绝 */
	uint8_t b[64];
	uint32_t n = 0;

	zassert_equal(ts_av_capture(ctx, b, sizeof(b), &n), TS_E_STATE,
		      "未声明格式 = 拒绝");

	/* 配置绑定 + 参数域（分辨率界 16..800 与 agent 校验器对齐） */
	zassert_equal(ts_av_config_bind_ctx(ctx, TS_AV_FMT_JPEG, 160, 120), TS_OK);
	zassert_equal(ts_av_config_bind(0x5c, TS_AV_FMT_JPEG, 8, 120), TS_E_PARAM,
		      "分辨率下界（<16）拒绝");
	zassert_equal(ts_av_config_bind(0x5c, (ts_av_fmt_t)9, 160, 120), TS_E_PARAM,
		      "未知格式拒绝");
	zassert_equal(ts_av_capture(ctx, NULL, sizeof(b), &n), TS_E_PARAM);

	/* 配置绑定域 = 声明它的 APP（其他 ctx → TS_E_STATE） */
	ts_ctx_t other;

	zassert_equal(ts_hal_bind_context(&other, 0x5d, &table), TS_OK);
	zassert_equal(ts_av_capture(other, b, sizeof(b), &n), TS_E_STATE,
		      "配置不属于本 APP");
	ts_hal_unbind_context(&other);

	/* 权限 + 配置齐全 → 后端（native_sim 无摄像头 chosen → TS_E_IO 如实） */
	zassert_equal(ts_av_capture(ctx, b, sizeof(b), &n), TS_E_IO,
		      "授权+配置 → 后端 IO（无摄像头，如实）");

	/* 发布面（TS_NET=y 构建）：权限/参数门 + 入队语义（本构建无传输注入，
	 * avq 只入队不发送——发送语义在 framework.net test_12 覆盖） */
	ts_net_avq_reset();
	zassert_equal(ts_av_publish(ctx, 1, 0, 2, b, 8), TS_OK, "授权分片入队");
	zassert_equal(ts_av_publish(ctx, 1, 0, 2, b, 0), TS_E_PARAM, "len=0 拒绝");
	zassert_equal(ts_av_publish(ctx, 1, 2, 2, b, 8), TS_E_PARAM, "cid>=n 拒绝");
	static uint8_t big[CONFIG_TS_NET_PUBLISH_MAX_BYTES + 1];

	memset(big, 1, sizeof(big));
	zassert_equal(ts_av_publish(ctx, 1, 0, 2, big, sizeof(big)), TS_E_PARAM,
		      "chunk > 1KB 拒绝（DEC-47②）");

	/* 无 av 权限的 ctx：门内拒绝（留痕） */
	ts_perm_table_init(&table);
	zassert_equal(ts_perm_parse("gpio:read:0", &table), TS_OK);
	zassert_equal(ts_hal_bind_context(&ctx, 0x5e, &table), TS_OK);
	zassert_equal(ts_av_config_bind_ctx(ctx, TS_AV_FMT_JPEG, 160, 120), TS_OK);
	zassert_equal(ts_av_capture(ctx, b, sizeof(b), &n), TS_E_PERM,
		      "无 av:read = 拒绝");
	zassert_equal(ts_av_publish(ctx, 1, 0, 2, b, 8), TS_E_PERM,
		      "发布同受 av:read 门（DEC-47⑥ 读类）");
	ts_hal_unbind_context(&ctx);
}

ZTEST_SUITE(framework_app, NULL, NULL, NULL, NULL, NULL);

/* ---- G3（单元 F）：INPUT_CHANGED → APP mailbox 路由 ----------------------- */
ZTEST(framework_app, test_07_input_routing)
{
	ts_appmgr_app_test_reset();
	zassert_equal(ts_appmgr_app_start(9, app_wasm, app_wasm_len,
					  "gpio:write:0-3"), TS_OK);
	k_sleep(K_MSEC(100)); /* APP 线程就位 */

	const struct ts_input_evt p = {.inst = 0, .old_mv = 100, .new_mv = 1234};
	const ts_evt_t evt = {
		.id = TS_EVT_INPUT_CHANGED,
		.t_ms = ts_time_ms(),
		.data = &p,
		.len = sizeof(p),
	};
	ts_evt_publish(&evt);
	k_sleep(K_MSEC(150));

	struct ts_app_rt_stats st;

	ts_appmgr_app_stats(&st);
	zassert_equal(st.evt_seen, 1, "input 事件路由进 mailbox（G3）");
	zassert_equal(ts_appmgr_app_stop(), TS_OK);
}

/* ---- G4（单元 H）：激活即停——单活跃语义收口 --------------------------------
 * 注：不经 boot_start 装载（直调 app_start）——进程内二次 boot_start 属
 * WAMR 池怪癖第三型（实例化后导出查找恒空；dev-env §5 登记，装载路径 V1
 * 经重启——与换包怪癖同族），本用例考察 activate 语义与装载来源无关；
 * boot 单次装载链在 test_04，重载链（暖复位）在 persistbench。 */
ZTEST(framework_app, test_08_activate_while_running)
{
	suite_setup_channel();
	ts_store_test_reset();
	ts_appmgr_test_reset();

	const uint8_t root_key[32] = {0};
	ts_app_info_t info;

	/* 首装（建 meta/双槽事实）+ 直调启动：APP 运行中（撕裂态起点） */
	zassert_equal(ts_appmgr_install(boot_pkg, sizeof(boot_pkg),
					root_key, &info), TS_OK);
	zassert_equal(ts_appmgr_app_start(9, app_wasm, app_wasm_len,
					  "gpio:write:0-3"), TS_OK);
	zassert_true(wait_gpio(true), "init 写 gpio=1");
	zassert_true(ts_appmgr_app_running());

	/* 二装（运行中安装 → 非活动槽）→ activate：旧缺陷 = 旧包继续运行 +
	 * 观测面报 STAGED/新槽；G4 收口 = 激活即停（DR-14 升级停止语义）。 */
	zassert_equal(ts_appmgr_install(boot_pkg, sizeof(boot_pkg),
					root_key, &info), TS_OK);
	zassert_false(ts_appmgr_app_running(), "激活即停（运行面收口）");
	zassert_equal(info.state, TS_APP_STAGED);
	zassert_equal(info.active_slot, 0, "meta 翻至 slot A（次装目标）");
	ts_appmgr_meta_t meta;

	zassert_equal(ts_appmgr_meta_read(&meta), TS_OK);
	zassert_equal(meta.active_slot, 0, "持久面同步翻转");
	zassert_equal(meta.rollback_count, 0, "新安装重置回滚计数");

	/* 激活停后 WAMR 运行面健全：同模块直调重启可用（装载周期在真机经
	 * 暖复位闭环——persistbench PB4/PB5 链）。 */
	zassert_equal(ts_appmgr_app_start(9, app_wasm, app_wasm_len,
					  "gpio:write:0-3"), TS_OK,
		      "stop 后运行面可重启");
	zassert_true(ts_appmgr_app_running());
	zassert_equal(ts_appmgr_app_stop(), TS_OK);
}
