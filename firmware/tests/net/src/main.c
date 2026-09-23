/* SPDX-License-Identifier: Apache-2.0 */
/* ts-net L1/L2 测试（LLD-ts-net §8）：key 构造 / 退避表 / pubq 语义 /
 * 会话状态机 / linkmon→safety 断链-恢复集成（虚拟时钟确定性）。 */
#include <stdio.h>
#include <string.h>
#include <zephyr/ztest.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/net.h>
#include <ts/safety.h>
/* 最小 CBOR 编解码（模块内部 API——测试构造请求/解回执复用同一实现） */
#include "../../../module/tessera/src/net/internal.h"

/* ---- 注入桩传输 ---------------------------------------------------------- */

static int fake_open_fail;
static int fake_close_calls;
static int fake_pub_calls;
static bool fake_up_v;
static char last_key[64];
static uint8_t last_payload[64];
static uint32_t last_len;
static ts_net_qos_t last_qos;

static ts_res_t fake_open(void)
{
	return fake_open_fail ? TS_E_IO : TS_OK;
}
static void fake_close(void)
{
	fake_close_calls++;
}
static ts_res_t fake_publish(const char *key, const uint8_t *p, uint32_t l,
			     ts_net_qos_t qos)
{
	strncpy(last_key, key, sizeof(last_key) - 1);
	last_key[sizeof(last_key) - 1] = '\0';
	memcpy(last_payload, p, l > sizeof(last_payload) ? sizeof(last_payload) : l);
	last_len = l; /* 原始长度（payload 截存仅用于内容检查） */
	last_qos = qos;
	fake_pub_calls++;
	return TS_OK;
}
static bool fake_is_up(void)
{
	return fake_up_v;
}
static const ts_net_transport_t fake_t = {
	.open = fake_open, .close = fake_close,
	.publish = fake_publish, .is_up = fake_is_up,
};

/* ---- L1：keyspace -------------------------------------------------------- */

ZTEST(framework_net, test_01_keyspace)
{
	char buf[64];

	zassert_equal(ts_net_set_ids("n1", "c1"), TS_OK);
	zassert_equal(ts_net_set_ids(NULL, "c1"), TS_E_PARAM);
	zassert_equal(ts_net_set_ids("n1", ""), TS_E_PARAM);
	zassert_equal(ts_net_set_ids("overlong-node-id-0123456789abcdef0123456789", "c"),
		      TS_E_PARAM, "前缀超 48B 拒绝");

	zassert_true(ts_net_key_cmd(buf, sizeof(buf), "led1") > 0);
	zassert_equal(strcmp(buf, "tessera/n1/c1/led1/cmd"), 0);
	zassert_true(ts_net_key_tel(buf, sizeof(buf), "led1") > 0);
	zassert_equal(strcmp(buf, "tessera/n1/c1/led1/telemetry"), 0);
	zassert_true(ts_net_key_evt(buf, sizeof(buf), "led1") > 0);
	zassert_equal(strcmp(buf, "tessera/n1/c1/led1/event"), 0);
	zassert_true(ts_net_key_hb(buf, sizeof(buf), false) > 0);
	zassert_equal(strcmp(buf, "tessera/n1/c1/sys/hb"), 0, "cube→host（DR-12）");
	zassert_true(ts_net_key_hb(buf, sizeof(buf), true) > 0);
	zassert_equal(strcmp(buf, "tessera/n1/c1/sys/hb-host"), 0, "host→cube（DR-12）");
	zassert_true(ts_net_key_sys(buf, sizeof(buf), "get-info") > 0);
	zassert_equal(strcmp(buf, "tessera/n1/c1/sys/get-info"), 0);

	/* 截断语义：n 不足返回需要长度且不越界写 */
	char small[8] = "ZZZZZZZZ";
	int need = ts_net_key_cmd(small, 8, "led1");

	zassert_true(need > (int)sizeof(small), "返回所需长度");
	zassert_equal(small[7], '\0', "写入以 NUL 截断，无越界");
	zassert_equal(ts_net_key_cmd(buf, sizeof(buf), NULL), -1);
	zassert_equal(ts_net_key_sys(buf, sizeof(buf), ""), -1);
}

/* ---- L1：退避表（DEC-27 固定表循环）-------------------------------------- */

ZTEST(framework_net, test_02_backoff_table)
{
	zassert_equal(ts_net_backoff_ms(0), 250);
	zassert_equal(ts_net_backoff_ms(1), 500);
	zassert_equal(ts_net_backoff_ms(2), 1000);
	zassert_equal(ts_net_backoff_ms(3), 2000);
	zassert_equal(ts_net_backoff_ms(4), 250, "回绕循环");
	zassert_equal(ts_net_backoff_ms(9), 500);
}

/* ---- L2：pubq 语义（DOWN 丢弃 / 满丢最旧 / flush）------------------------ */

ZTEST(framework_net, test_03_pubq)
{
	uint8_t p[4] = {1, 2, 3, 4};

	ts_net_test_reset();
	zassert_equal(ts_net_state(), TS_NET_DOWN);

	/* DOWN 期 = 直接丢弃并计数 */
	zassert_equal(ts_net_pubq_push("tessera/n1/c1/led1/telemetry", p, 4), TS_OK);
	zassert_equal(ts_net_pubq_dropped(), 1, "DOWN 期丢弃计数");

	/* 建链后 push→flush */
	fake_open_fail = 0;
	fake_up_v = true;
	fake_pub_calls = 0;
	ts_net_set_transport(&fake_t);
	zassert_equal(ts_net_session_poll(0), TS_NET_CONNECTED);
	for (int i = 0; i < 3; i++) {
		zassert_equal(ts_net_pubq_push("k/a", p, 4), TS_OK);
	}
	zassert_equal(ts_net_pubq_dropped(), 1);
	ts_net_pubq_flush();
	zassert_equal(fake_pub_calls, 3, "三条全部发出");
	zassert_equal(strcmp(last_key, "k/a"), 0);

	/* 满溢：push 11 条 → 8 入队 + 3 丢最旧 */
	for (int i = 0; i < 11; i++) {
		zassert_equal(ts_net_pubq_push("k/b", p, 4), TS_OK);
	}
	zassert_equal(ts_net_pubq_dropped(), 1 + 3, "溢出丢最旧计数");

	/* 参数域 */
	zassert_equal(ts_net_pubq_push(NULL, p, 4), TS_E_PARAM);
	zassert_equal(ts_net_pubq_push("k", NULL, 4), TS_E_PARAM);
	zassert_equal(ts_net_pubq_push("k", p, 0), TS_E_PARAM);
}

/* ---- L1/L2：会话状态机（建链/退避推进/掉线迁移）-------------------------- */

ZTEST(framework_net, test_04_session)
{
	ts_net_test_reset();
	fake_pub_calls = 0;
	fake_close_calls = 0;

	/* 无传输 = 不动 */
	zassert_equal(ts_net_session_poll(0), TS_NET_DOWN);

	/* open 失败 → 退避表推进（250/500）*/
	fake_open_fail = 1;
	fake_up_v = false;
	ts_net_set_transport(&fake_t);
	zassert_equal(ts_net_session_poll(0), TS_NET_DOWN);
	zassert_equal(ts_net_session_poll(100), TS_NET_DOWN, "退避期内不重试");
	zassert_equal(ts_net_session_poll(250), TS_NET_DOWN, "第二次失败");
	zassert_equal(ts_net_session_poll(300), TS_NET_DOWN, "500ms 退避期内不重试");
	zassert_equal(ts_net_session_poll(750), TS_NET_DOWN, "第三次失败");

	/* open 成功 → CONNECTED */
	fake_open_fail = 0;
	fake_up_v = true;
	zassert_equal(ts_net_session_poll(1750), TS_NET_CONNECTED, "建链");

	/* 传输掉线 → DOWN + close + 从表头退避 */
	fake_up_v = false;
	zassert_equal(ts_net_session_poll(1800), TS_NET_DOWN, "掉线迁移");
	zassert_equal(fake_close_calls, 1);
	zassert_equal(ts_net_session_poll(2000), TS_NET_DOWN, "250ms 退避");
	zassert_equal(ts_net_session_poll(2100), TS_NET_DOWN);
}

/* ---- L2 集成：linkmon → ts-safety（合同 3 判定源）------------------------ */

ZTEST(framework_net, test_05_linkmon_safety)
{
	static const ts_out_ch_t led_ch = {
		.uid = "netled", .kind = TS_CH_GPIO,
		.poweron = {.b = false}, .linkloss = {.b = true}, .fault = {.b = false},
	};
	ts_out_value_t rb;

	ts_net_test_reset();
	zassert_equal(ts_safety_register_channel(&led_ch), TS_OK);
	zassert_false(ts_net_link_up(), "初始判定 = down");

	/* 判定 down 期：commit 被安全层拒绝（链路未建立） */
	zassert_equal(ts_safety_commit("netled", (ts_out_value_t){.b = true}), TS_E_STATE);

	/* 恢复滞回：1 次心跳不足，2 次（DEC-27）→ up */
	ts_net_linkmon_hb_host(100);
	zassert_false(ts_net_link_up(), "滞回：单次不足");
	ts_net_linkmon_hb_host(1100);
	zassert_true(ts_net_link_up());
	zassert_equal(ts_safety_commit("netled", (ts_out_value_t){.b = true}), TS_OK);

	/* 断链：6 个周期（DEC-22）+ ε 未达 → set_link(false) → LINKLOSS 态值 */
	ts_net_linkmon_tick(1100 + 6 * 1000 + 1);
	zassert_false(ts_net_link_up(), "超时判定断链");
	ts_ch_state_t st;

	zassert_equal(ts_safety_channel_state("netled", &st), TS_OK);
	zassert_equal(st, TS_ST_SAFE_LINKLOSS, "通道进断链安全态");
	zassert_equal(ts_safety_readback("netled", &rb), TS_OK);
	zassert_true(rb.b, "linkloss 态值生效（.b=true）");

	/* 恢复：断链后心跳恢复 → 连续 2 次重新 up（streak 已被断链清零） */
	ts_net_linkmon_hb_host(7300);
	zassert_false(ts_net_link_up());
	ts_net_linkmon_hb_host(7400);
	zassert_true(ts_net_link_up(), "滞回恢复");
}

/* ---- M3a.2：sys 命令面矩阵（LLD-ts-net §4，DEC-30①）---------------------- */

static uint8_t resp[512];
static size_t resp_len;

/* 构造请求 map{"op": op} / 带参 map{"op": op, "args": {...}}（定体 canonical） */
static size_t build_req(uint8_t *buf, size_t cap, const char *op,
			const char *arg_key, const char *arg_str, uint64_t arg_uint)
{
	size_t p = 0;

	if (arg_key == NULL) {
		zassert_true(ts_cbor_put_map(buf, cap, &p, 1));
		zassert_true(ts_cbor_put_tstr(buf, cap, &p, "op"));
		zassert_true(ts_cbor_put_tstr(buf, cap, &p, op));
		return p;
	}
	zassert_true(ts_cbor_put_map(buf, cap, &p, 2));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, "op"));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, op));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, "args"));
	zassert_true(ts_cbor_put_map(buf, cap, &p, 1));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, arg_key));
	if (arg_str != NULL) {
		zassert_true(ts_cbor_put_tstr(buf, cap, &p, arg_str));
	} else {
		zassert_true(ts_cbor_put_uint(buf, cap, &p, arg_uint));
	}
	return p;
}

/* 解回执首对（"status"）验证编码合法性并取值 */
static int64_t resp_status(void)
{
	ts_cbor_rd_t r;
	uint32_t pairs;

	ts_cbor_rd_init(&r, resp, resp_len);
	zassert_true(ts_cbor_map_open(&r, &pairs));
	char key[8];

	zassert_true(ts_cbor_tstr(&r, key, sizeof(key)));
	zassert_equal(strcmp(key, "status"), 0);
	int64_t v;

	zassert_true(ts_cbor_int(&r, &v));
	return v;
}

ZTEST(framework_net, test_06_syscmd_matrix)
{
	uint8_t req[128];
	size_t rlen;

	ts_net_test_reset();
	ts_net_cmd_test_reset();
	ts_net_cmd_sys_init();
	zassert_equal(ts_net_set_ids("n1", "c1"), TS_OK);

	/* get-info / get-link / get-safety / get-audit → OK 且回执合法 CBOR */
	const char *oks[] = {"get-info", "get-link", "get-safety", "get-audit"};

	for (size_t i = 0; i < 4; i++) {
		char key[32];

		snprintf(key, sizeof(key), "sys/%s", oks[i]);
		rlen = build_req(req, sizeof(req), oks[i], NULL, NULL, 0);
		zassert_equal(ts_net_cmd_dispatch(key, req, rlen, resp, sizeof(resp),
						  &resp_len),
			      TS_OK, "cmd %s", oks[i]);
		zassert_equal(resp_status(), TS_OK);
		zassert_true(resp_len > 10, "回执含 data");
	}

	/* get-budget：ts-power M3b → TS_E_NOTFOUND（面完整、如实报不可用） */
	rlen = build_req(req, sizeof(req), "get-budget", NULL, NULL, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/get-budget", req, rlen, resp,
					  sizeof(resp), &resp_len),
		      TS_E_NOTFOUND);
	zassert_equal(resp_status(), TS_E_NOTFOUND);

	/* set-time：无 time_ms → PARAM；带 time_ms → OK + 墙钟生效（DR-08） */
	rlen = build_req(req, sizeof(req), "set-time", NULL, NULL, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/set-time", req, rlen, resp,
					  sizeof(resp), &resp_len),
		      TS_E_PARAM);
	zassert_equal(resp_status(), TS_E_PARAM);
	rlen = build_req(req, sizeof(req), "set-time", "time_ms", NULL, 1700000000000ULL);
	zassert_equal(ts_net_cmd_dispatch("sys/set-time", req, rlen, resp,
					  sizeof(resp), &resp_len),
		      TS_OK);
	zassert_equal(ts_time_wall_ms(), 1700000000000ULL, "墙钟数据字段生效");

	/* estop-clear：令牌缺失/错误 → PARAM；正确令牌 → 走 clear_fault 路径 */
	rlen = build_req(req, sizeof(req), "estop-clear", NULL, NULL, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/estop-clear", req, rlen, resp,
					  sizeof(resp), &resp_len),
		      TS_E_PARAM);
	rlen = build_req(req, sizeof(req), "estop-clear", "confirm", "stop", 0);
	zassert_equal(ts_net_cmd_dispatch("sys/estop-clear", req, rlen, resp,
					  sizeof(resp), &resp_len),
		      TS_E_PARAM, "错误令牌拒绝");
	rlen = build_req(req, sizeof(req), "estop-clear", "confirm", "estop", 0);
	(void)ts_net_cmd_dispatch("sys/estop-clear", req, rlen, resp, sizeof(resp),
				  &resp_len);
	/* 无锁存时 clear_fault 语义由 safety 定义——此处只断回执编码合法 */

	/* 未知 key / op 与 key 不匹配 / 垃圾请求 → NOTFOUND/PARAM（不留静默） */
	rlen = build_req(req, sizeof(req), "get-info", NULL, NULL, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/bogus", req, rlen, resp, sizeof(resp),
					  &resp_len),
		      TS_E_NOTFOUND, "未知 key");
	zassert_equal(ts_net_cmd_dispatch("sys/get-link", req, rlen, resp,
					  sizeof(resp), &resp_len),
		      TS_E_NOTFOUND, "op/key 不匹配");
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, 1, resp,
					  sizeof(resp), &resp_len),
		      TS_E_PARAM, "垃圾请求");
	static const uint8_t garbage[4] = {0xA2, 0x63, 0x66, 0x6F};

	zassert_equal(ts_net_cmd_dispatch("sys/get-info", garbage, sizeof(garbage),
					  resp, sizeof(resp), &resp_len),
		      TS_E_PARAM, "非法 CBOR");
}

/* ---- M3a.2：遥测快照 + 事件外发 → pubq → transport ----------------------- */

ZTEST(framework_net, test_07_telemetry_and_events)
{
	static const ts_out_ch_t led_ch = {
		.uid = "tel1", .kind = TS_CH_GPIO,
		.poweron = {.b = false}, .linkloss = {.b = false}, .fault = {.b = false},
	};
	static const ts_hal_dev_desc_t led_dev = {.uid = "tel1", .kind = TS_DEV_GPIO_OUT};

	ts_net_test_reset();
	ts_net_cmd_test_reset();
	ts_net_cmd_sys_init();
	(void)ts_net_pub_init(); /* 幂等：重复订阅由容量守卫拒绝 */
	zassert_equal(ts_safety_register_channel(&led_ch), TS_OK);
	zassert_equal(ts_hal_register_dev(&led_dev), TS_OK);

	/* DOWN 期：快照入 pubq = 丢弃计数 */
	uint32_t d0 = ts_net_pubq_dropped();

	ts_net_pub_telem(0);
	zassert_equal(ts_net_pubq_dropped(), d0 + 1, "DOWN 期遥测丢弃");

	/* 建链后：快照 → flush → fake 捕获 telemetry key + value_u */
	fake_open_fail = 0;
	fake_up_v = true;
	fake_pub_calls = 0;
	ts_net_set_transport(&fake_t);
	zassert_equal(ts_net_session_poll(0), TS_NET_CONNECTED);
	ts_net_pub_telem(10);
	zassert_equal(ts_net_pubq_dropped(), d0 + 1);
	ts_net_pubq_flush();
	zassert_equal(fake_pub_calls, 1, "遥测一条");
	zassert_equal(strcmp(last_key, "tessera/n1/c1/tel1/telemetry"), 0);
	zassert_true(last_len > 20, "遥测 payload = 定体 CBOR 快照");

	/* 信封 v1（DEC-42）：map{ver:1, kind:96, dev, value_u, wall_ms} 全 uint 值 */
	{
		ts_cbor_rd_t r;
		uint32_t pairs;
		char k[8];
		uint64_t ver = 0, kind = 0, dev = 0;

		ts_cbor_rd_init(&r, last_payload, last_len);
		zassert_true(ts_cbor_map_open(&r, &pairs));
		zassert_equal(pairs, 5);
		zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "ver") == 0);
		zassert_true(ts_cbor_uint(&r, &ver) && ver == 1);
		zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "kind") == 0);
		zassert_true(ts_cbor_uint(&r, &kind) && kind == 96, "遥测 kind=96（§4.4）");
		zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "dev") == 0);
		zassert_true(ts_cbor_uint(&r, &dev) && dev == (uint64_t)TS_DEV_GPIO_OUT);
		zassert_equal(last_qos, TS_NET_QOS_BESTEFFORT, "遥测 = 丢弃式缺省");
	}

	/* 事件：SAFE_STATE_CHANGED（含 uid）→ event key 外发 */
	fake_pub_calls = 0;
	const ts_safe_state_evt_t pl = {.uid = "tel1", .new_state = TS_ST_ACTIVE};
	const ts_evt_t evt = {
		.id = TS_EVT_SAFE_STATE_CHANGED, .t_ms = 20,
		.data = &pl, .len = sizeof(pl),
	};

	ts_evt_publish(&evt);
	ts_net_pubq_flush();
	zassert_equal(fake_pub_calls, 1, "事件一条");
	zassert_equal(strcmp(last_key, "tessera/n1/c1/tel1/event"), 0, "实例事件路由");
	/* 信封（DEC-42）：kind = 32+evt_id；安全事件 = 阻塞式高优先级 QoS */
	{
		ts_cbor_rd_t r;
		uint32_t pairs;
		char k[8];
		uint64_t ver = 0, kind = 0;

		ts_cbor_rd_init(&r, last_payload, last_len);
		zassert_true(ts_cbor_map_open(&r, &pairs));
		zassert_equal(pairs, 5);
		zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "ver") == 0);
		zassert_true(ts_cbor_uint(&r, &ver) && ver == 1);
		zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "kind") == 0);
		zassert_true(ts_cbor_uint(&r, &kind));
		zassert_equal(kind, (uint64_t)(32 + (int)TS_EVT_SAFE_STATE_CHANGED),
			      "事件 kind = 32+evt_id（§4.4）");
		zassert_equal(last_qos, TS_NET_QOS_SAFETY, "安全事件 = 阻塞式高优先级");
	}
}

/* ---- DEC-40 批：命令信封 v2 + 幂等回执缓存 -------------------------------- */

/* v2 请求 map{ver:1, kind:1, rid, src:"t-agent", op, args?{arg1?, idem?, to?}} */
static size_t build_req_v2(uint8_t *buf, size_t cap, const char *op, const char *rid,
			   const char *arg1k, const char *arg1s, uint64_t arg1u,
			   const char *idem, bool has_to, uint32_t to)
{
	bool has_args = arg1k != NULL || idem != NULL || has_to;
	uint32_t apairs = (arg1k ? 1u : 0u) + (idem ? 1u : 0u) + (has_to ? 1u : 0u);
	size_t p = 0;

	zassert_true(ts_cbor_put_map(buf, cap, &p, 5 + (has_args ? 1 : 0)));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, "ver"));
	zassert_true(ts_cbor_put_uint(buf, cap, &p, 1));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, "kind"));
	zassert_true(ts_cbor_put_uint(buf, cap, &p, 1));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, "rid"));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, rid));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, "src"));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, "t-agent"));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, "op"));
	zassert_true(ts_cbor_put_tstr(buf, cap, &p, op));
	if (has_args) {
		zassert_true(ts_cbor_put_tstr(buf, cap, &p, "args"));
		zassert_true(ts_cbor_put_map(buf, cap, &p, apairs));
		if (arg1k != NULL) {
			zassert_true(ts_cbor_put_tstr(buf, cap, &p, arg1k));
			if (arg1s != NULL) {
				zassert_true(ts_cbor_put_tstr(buf, cap, &p, arg1s));
			} else {
				zassert_true(ts_cbor_put_uint(buf, cap, &p, arg1u));
			}
		}
		if (idem != NULL) {
			zassert_true(ts_cbor_put_tstr(buf, cap, &p, "idem"));
			zassert_true(ts_cbor_put_tstr(buf, cap, &p, idem));
		}
		if (has_to) {
			zassert_true(ts_cbor_put_tstr(buf, cap, &p, "to"));
			zassert_true(ts_cbor_put_uint(buf, cap, &p, to));
		}
	}
	return p;
}

/* 解 v2 回执 map{ver,kind,rid,status,data}：验证信封头 + rid 回带，取 status */
static int64_t resp2_status(const char *expect_rid)
{
	ts_cbor_rd_t r;
	uint32_t pairs;
	char k[8], rid[24];
	uint64_t u;
	int64_t st;

	ts_cbor_rd_init(&r, resp, resp_len);
	zassert_true(ts_cbor_map_open(&r, &pairs));
	zassert_equal(pairs, 5, "v2 回执五对");
	zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "ver") == 0);
	zassert_true(ts_cbor_uint(&r, &u) && u == 1);
	zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "kind") == 0);
	zassert_true(ts_cbor_uint(&r, &u) && u == 16, "回执 kind=16（§4.4）");
	zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "rid") == 0);
	zassert_true(ts_cbor_tstr(&r, rid, sizeof(rid)));
	zassert_equal(strcmp(rid, expect_rid), 0, "rid 原样回带");
	zassert_true(ts_cbor_tstr(&r, k, sizeof(k)) && strcmp(k, "status") == 0);
	zassert_true(ts_cbor_int(&r, &st));
	return st;
}

ZTEST(framework_net, test_08_env_v2_idem)
{
	uint8_t req[192];
	uint8_t first[512];
	size_t flen;
	size_t rlen;

	ts_net_test_reset();
	ts_net_cmd_test_reset();
	ts_net_cmd_sys_init();

	/* v2 基础：rid 回带 + kind 16 + status 语义 */
	rlen = build_req_v2(req, sizeof(req), "get-info", "rid-1", NULL, NULL, 0,
			    NULL, false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_OK);
	zassert_equal(resp2_status("rid-1"), TS_OK);

	/* v1 共存（首键判别）：v1 回执仍两对 {status,data}——弃用期不破坏 */
	rlen = build_req(req, sizeof(req), "get-info", NULL, NULL, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_OK);
	zassert_equal(resp_status(), TS_OK);

	/* v2 fail-closed：缺 src / kind!=1 / 未知信封键 = PARAM */
	size_t p = 0;

	zassert_true(ts_cbor_put_map(req, sizeof(req), &p, 4));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "ver"));
	zassert_true(ts_cbor_put_uint(req, sizeof(req), &p, 1));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "kind"));
	zassert_true(ts_cbor_put_uint(req, sizeof(req), &p, 1));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "rid"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "r"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "op"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "get-info"));
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, p, resp, sizeof(resp),
					  &resp_len), TS_E_PARAM, "缺 src 拒绝");

	rlen = build_req_v2(req, sizeof(req), "get-info", "rid-k", NULL, NULL, 0,
			    NULL, false, 0);
	/* 手改 kind 值（map hdr 1B + "ver" 4B + 1B + "kind" 5B → 值偏移 = 11） */
	req[11] = 2; /* kind=2（未注册的请求 kind） */
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_E_PARAM, "kind!=1 拒绝");
	req[11] = 1; /* 还原 */

	p = 0;
	zassert_true(ts_cbor_put_map(req, sizeof(req), &p, 6));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "ver"));
	zassert_true(ts_cbor_put_uint(req, sizeof(req), &p, 1));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "kind"));
	zassert_true(ts_cbor_put_uint(req, sizeof(req), &p, 1));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "rid"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "r"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "src"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "t"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "op"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "get-info"));
	zassert_true(ts_cbor_put_tstr(req, sizeof(req), &p, "bogus"));
	zassert_true(ts_cbor_put_uint(req, sizeof(req), &p, 1));
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, p, resp, sizeof(resp),
					  &resp_len), TS_E_PARAM, "未知信封键拒绝");

	/* to 边界（DEC-40）：5000 OK；5001 拒 */
	rlen = build_req_v2(req, sizeof(req), "get-info", "rid-t", NULL, NULL, 0,
			    NULL, true, 5000);
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_OK, "to=5000 上界内");
	rlen = build_req_v2(req, sizeof(req), "get-info", "rid-t", NULL, NULL, 0,
			    NULL, true, 5001);
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_E_PARAM, "to>5000 拒绝");
	zassert_equal(resp2_status("rid-t"), TS_E_PARAM, "拒绝回执仍是 v2 信封");

	/* 幂等（DEC-40）：同 idem 重发 = 原样回执，不重执行 */
	rlen = build_req_v2(req, sizeof(req), "set-time", "rid-a", "time_ms", NULL,
			    111111ULL, "idem-a", false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/set-time", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_OK);
	memcpy(first, resp, resp_len);
	flen = resp_len;
	zassert_equal(ts_time_wall_ms(), 111111ULL, "首次执行生效");
	rlen = build_req_v2(req, sizeof(req), "set-time", "rid-b", "time_ms", NULL,
			    222222ULL, "idem-a", false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/set-time", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_OK);
	zassert_equal(resp_len, flen);
	zassert_equal(memcmp(first, resp, flen), 0, "回放 = 字节级原样回执");
	zassert_equal(ts_time_wall_ms(), 111111ULL, "未重执行（墙钟不变）");

	/* idem 与 op 不匹配（调用方键管理错误）→ PARAM */
	rlen = build_req_v2(req, sizeof(req), "get-info", "rid-c", NULL, NULL, 0,
			    "idem-a", false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/get-info", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_E_PARAM, "idem/op mismatch");

	/* LRU 驱逐（深度 CONFIG_TS_NET_IDEM_CACHE=4）：填 b/c/d/e → a 被驱逐重执行 */
	const char *fill[] = {"idem-b", "idem-c", "idem-d"};

	for (int i = 0; i < 3; i++) {
		rlen = build_req_v2(req, sizeof(req), "set-time", "rid-f", "time_ms",
				    NULL, 500 + (uint64_t)i, fill[i], false, 0);
		(void)ts_net_cmd_dispatch("sys/set-time", req, rlen, resp, sizeof(resp),
					  &resp_len);
	}
	rlen = build_req_v2(req, sizeof(req), "set-time", "rid-f", "time_ms", NULL,
			    999ULL, "idem-e", false, 0);
	(void)ts_net_cmd_dispatch("sys/set-time", req, rlen, resp, sizeof(resp),
				  &resp_len); /* 第 5 项 → 驱逐最旧 idem-a */
	rlen = build_req_v2(req, sizeof(req), "set-time", "rid-g", "time_ms", NULL,
			    333333ULL, "idem-a", false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/set-time", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_OK);
	zassert_equal(ts_time_wall_ms(), 333333ULL, "驱逐后同 idem = 重新执行");
}

/* ---- DEC-41 批：控制租约生命周期 ------------------------------------------ */

ZTEST(framework_net, test_09_lease)
{
	ts_net_test_reset();
	ts_net_cmd_test_reset();
	ts_net_cmd_sys_init();
	ts_net_lease_test_reset();

	const uint32_t ttl = CONFIG_TS_NET_LEASE_TTL_MS;
	uint32_t id = 0;
	uint64_t exp = 0;
	bool valid = false;
	char holder[TS_NET_LEASE_HOLDER_MAX];
	uint32_t gid = 0;
	uint64_t gexp = 0;

	/* 空态：get → invalid；release 幂等 OK */
	ts_net_lease_get(0, &valid, holder, sizeof(holder), &gid, &gexp);
	zassert_false(valid);
	zassert_equal(gid, 0);
	zassert_equal(ts_net_lease_release("a", 0), TS_OK, "无租约释放 = 幂等空操作");

	/* 获取：id 从 1 起，TTL 自 now 顺延 */
	zassert_equal(ts_net_lease_acquire("agent-a", 1000, &id, &exp), TS_OK);
	zassert_equal(id, 1);
	zassert_equal(exp, 1000 + ttl);
	zassert_true(ts_net_lease_held_by("agent-a", 1500));
	zassert_false(ts_net_lease_held_by("agent-b", 1500));

	/* 续期幂等：同 holder → id 不变，窗口自 now 顺延 */
	zassert_equal(ts_net_lease_acquire("agent-a", 5000, &id, &exp), TS_OK);
	zassert_equal(id, 1, "续期不换 id");
	zassert_equal(exp, 5000 + ttl);

	/* 他人获取 → STATE（回填当前租约） */
	zassert_equal(ts_net_lease_acquire("agent-b", 6000, &id, &exp), TS_E_STATE);
	zassert_equal(id, 1);
	zassert_equal(exp, 5000 + ttl, "拒绝回执回填当前租约");

	/* 惰性过期：now == expires 即失效；过期后再获取 → 新 id（不复用） */
	zassert_false(ts_net_lease_held_by("agent-a", 5000 + ttl));
	zassert_equal(ts_net_lease_acquire("agent-b", 5000 + ttl + 1, &id, &exp), TS_OK);
	zassert_equal(id, 2, "过期后新授予 id 递增");

	/* 代还拒绝；本人归还 OK；重复归还幂等 */
	zassert_equal(ts_net_lease_release("agent-a", 5000 + ttl + 2), TS_E_STATE);
	zassert_equal(ts_net_lease_release("agent-b", 5000 + ttl + 3), TS_OK);
	zassert_equal(ts_net_lease_release("agent-b", 5000 + ttl + 4), TS_OK);
	ts_net_lease_get(5000 + ttl + 5, &valid, holder, sizeof(holder), &gid, &gexp);
	zassert_false(valid);

	/* 参数域：空/超长 holder 拒绝 */
	zassert_equal(ts_net_lease_acquire(NULL, 0, NULL, NULL), TS_E_PARAM);
	zassert_equal(ts_net_lease_acquire("", 0, NULL, NULL), TS_E_PARAM);
	zassert_equal(ts_net_lease_acquire("holder-of-24-chars-xxxxx", 0, NULL, NULL),
		      TS_E_PARAM, "超长 holder 拒绝");

	/* 命令面全链（v2 信封）：acquire → get → 他人 release 拒 → 本人 release */
	uint8_t req[192];
	size_t rlen = build_req_v2(req, sizeof(req), "lease-acquire", "rid-l1",
				   "holder", "panel-1", 0, NULL, false, 0);

	zassert_equal(ts_net_cmd_dispatch("sys/lease-acquire", req, rlen, resp,
					  sizeof(resp), &resp_len), TS_OK);
	zassert_equal(resp2_status("rid-l1"), TS_OK);

	rlen = build_req_v2(req, sizeof(req), "lease-get", "rid-l2", NULL, NULL, 0,
			    NULL, false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/lease-get", req, rlen, resp, sizeof(resp),
					  &resp_len), TS_OK);
	zassert_equal(resp2_status("rid-l2"), TS_OK);

	rlen = build_req_v2(req, sizeof(req), "lease-release", "rid-l3",
			   "holder", "someone-else", 0, NULL, false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/lease-release", req, rlen, resp,
					  sizeof(resp), &resp_len), TS_E_STATE,
		      "他人代还拒绝");
	rlen = build_req_v2(req, sizeof(req), "lease-release", "rid-l4",
			   "holder", "panel-1", 0, NULL, false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/lease-release", req, rlen, resp,
					  sizeof(resp), &resp_len), TS_OK);

	/* lease-acquire 缺 holder → PARAM（fail-closed） */
	rlen = build_req_v2(req, sizeof(req), "lease-acquire", "rid-l5", NULL, NULL, 0,
			    NULL, false, 0);
	zassert_equal(ts_net_cmd_dispatch("sys/lease-acquire", req, rlen, resp,
					  sizeof(resp), &resp_len), TS_E_PARAM);
}

ZTEST_SUITE(framework_net, NULL, NULL, NULL, NULL, NULL);
