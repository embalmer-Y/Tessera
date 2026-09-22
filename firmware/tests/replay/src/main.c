/* SPDX-License-Identifier: Apache-2.0 */
/*
 * L4 确定性重放雏形（LLD-ts-core §7 / testing.md §2；HLD M1 交付）。
 *
 * MA2 对接接口（LLD-A04 §2 约定，随 M1 定稿）：
 *   输入 = 虚拟时钟驱动的脚本序列（V1 编译期内嵌；后续演进为输入文件）；
 *   输出 = stdout JSONL 行（{"t_ms":..,"ch":..,"value_u":..}）+ 事件序列；
 *   判定 = ztest 断言（退出码表结果）。
 * 确定性（合同 9）：同一输入序列在两个相同通道上运行，写序列逐项一致，
 * 且与 golden 常量一致——"跑一遍拿输出当基准"是被禁止的（testing.md §2），
 * golden 的来源 = 规格推导（slew/限幅/状态机的数学预期）。
 */
#include <string.h>
#include <zephyr/ztest.h>
#include <ts/core.h>
#include <ts/safety.h>

static uint64_t virt_now;
static uint64_t virt_now_fn(void)
{
	return virt_now;
}
static const ts_time_source_t virt_src = {.now_ms = virt_now_fn};

/* 双通道同参数（slew 5/ms，min 0，max 1000，fault=7） */
#define REPLAY_CH(uid_literal)                                                     \
	{                                                                          \
		.uid = uid_literal, .kind = TS_CH_PWM, .poweron = {.u = 0},         \
		.linkloss = {.u = 0}, .fault = {.u = 7},                            \
		.limits = {.min = 0, .max = 1000, .slew_per_ms = 5},                \
	}

static const ts_out_ch_t ch_a = REPLAY_CH("rep_a");
static const ts_out_ch_t ch_b = REPLAY_CH("rep_b");

static int state_evt_seen;
static struct {
	uint64_t t_ms;
	const char *uid;
	ts_ch_state_t state;
} state_log[8];

static void state_cb(const ts_evt_t *e, void *u)
{
	ARG_UNUSED(u);
	const ts_safe_state_evt_t *p = e->data;

	if (state_evt_seen < 8) {
		state_log[state_evt_seen].t_ms = e->t_ms;
		state_log[state_evt_seen].uid = p->uid;
		state_log[state_evt_seen].state = p->new_state;
	}
	state_evt_seen++;
}

/* 对单通道执行同一脚本（虚拟时间在外层统一推进） */
static void run_script(const char *uid)
{
	ts_out_value_t v = {.u = 0};

	virt_now = 200;
	v.u = 100;
	ts_safety_commit(uid, v); /* 基线 100 */
	virt_now = 210;
	v.u = 300;
	ts_safety_commit(uid, v); /* Δt=10 → 界 55 → 155（slew 拆分） */
	virt_now = 220;
	v.u = 0;
	ts_safety_commit(uid, v); /* Δt=10 → 界 55 → 100 */
}

/* golden：规格推导（slew 5/ms × Δt+1）+ estop fault 值 7 */
static const ts_write_rec_t golden[] = {
	{.t_ms = 200, .value_u = 100},
	{.t_ms = 210, .value_u = 155},
	{.t_ms = 220, .value_u = 100},
	{.t_ms = 230, .value_u = 7},
};

ZTEST(framework_replay, test_deterministic_replay)
{
	ts_time_test_bind(&virt_src);
	virt_now = 0;
	zassert_equal(ts_safety_register_channel(&ch_a), TS_OK);
	zassert_equal(ts_safety_register_channel(&ch_b), TS_OK);
	zassert_equal(ts_evt_subscribe(TS_EVT_SAFE_STATE_CHANGED, state_cb, NULL), TS_OK);

	/* t=100 链路确立（两通道 POWERON→ACTIVE） */
	virt_now = 100;
	ts_safety_set_link(true);

	/* 同一脚本对两通道执行（同一输入序列） */
	run_script(ch_a.uid);
	run_script(ch_b.uid);

	/* t=230 estop 直达（两通道 → SAFE_FAULT，写 fault=7） */
	virt_now = 230;
	ts_safety_force_all_fault();

	/* 校验 1：两通道写序列逐项一致（确定性：同输入 → 同输出，合同 9） */
	ts_write_rec_t wa[8], wb[8];
	size_t na = ts_driversim_writes(ch_a.uid, wa, 8);
	size_t nb = ts_driversim_writes(ch_b.uid, wb, 8);

	zassert_equal(na, 4, "channel A write count");
	zassert_equal(na, nb, "identical sequences");
	for (size_t i = 0; i < na; i++) {
		zassert_equal(wa[i].t_ms, wb[i].t_ms, "time match at %u", (unsigned)i);
		zassert_equal(wa[i].value_u, wb[i].value_u, "value match at %u", (unsigned)i);
	}

	/* 校验 2：与规格推导的 golden 一致 */
	for (size_t i = 0; i < na; i++) {
		zassert_equal(wa[i].t_ms, golden[i].t_ms, "golden t at %u", (unsigned)i);
		zassert_equal(wa[i].value_u, golden[i].value_u, "golden v at %u", (unsigned)i);
	}

	/* 校验 3：estop 后写入锁死 */
	ts_out_value_t v = {.u = 500};

	zassert_equal(ts_safety_commit(ch_a.uid, v), TS_E_STATE);

	/* 校验 4：状态事件序列——estop/system_fail 路径不发布 SAFE_STATE_CHANGED
	 *（ISR 禁队列，合同 5），事后经 TS_EVT_ESTOP 补发；故此处仅 2 条（ACTIVE@100）。 */
	zassert_equal(state_evt_seen, 2, "link-up transitions only");
	for (int i = 0; i < 2; i++) {
		zassert_equal(state_log[i].t_ms, 100, "state evt time");
		zassert_equal(state_log[i].state, TS_ST_ACTIVE);
	}
	ts_ch_state_t st;
	zassert_equal(ts_safety_channel_state(ch_a.uid, &st), TS_OK);
	zassert_equal(st, TS_ST_SAFE_FAULT, "fault state visible (silent set)");

	/* 雏形接口：stdout JSONL（MA2 模拟器 harness 的采集格式） */
	for (size_t i = 0; i < na; i++) {
		printk("{\"t_ms\":%llu,\"ch\":\"%s\",\"value_u\":%u}\n",
		       (unsigned long long)wa[i].t_ms, ch_a.uid, wa[i].value_u);
	}
	ts_time_test_bind(NULL);
}

ZTEST_SUITE(framework_replay, NULL, NULL, NULL, NULL, NULL);
