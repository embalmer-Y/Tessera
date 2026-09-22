/* SPDX-License-Identifier: Apache-2.0 */
/*
 * ts-safety L1 测试（LLD-ts-safety §8）。
 * 说明：本套件为**有状态顺序场景**（注册表/forced 锁存为全局静态，estop 是终态），
 * ztest 用例执行顺序不保证 → 合并为单一顺序场景用例，断言链 = 规格链。
 */
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdio.h>
#include <ts/core.h>
#include <ts/safety.h>

static uint64_t virt_now;
static uint64_t virt_now_fn(void)
{
	return virt_now;
}
static const ts_time_source_t virt_src = {.now_ms = virt_now_fn};

static ts_res_t isr_commit_res;

static void isr_commit_fn(const void *arg)
{
	const char *uid = arg;
	ts_out_value_t v = {.u = 500};

	isr_commit_res = ts_safety_commit(uid, v);
}

ZTEST(framework_safety, test_safety_full_scenario)
{
	ts_out_value_t v = {.u = 0};
	ts_out_value_t rb = {0};
	ts_ch_state_t st;

	ts_time_test_bind(&virt_src);
	virt_now = 0;

	/* ---- 1. 注册校验（合同 1：三态缺一/值越限/uid 非法 → 拒绝，不留半注册） ---- */
	zassert_equal(ts_safety_register_channel(NULL), TS_E_PARAM);
	const ts_out_ch_t over_max = {
		.uid = "bad1", .kind = TS_CH_PWM,
		.poweron = {.u = 2000}, .linkloss = {.u = 0}, .fault = {.u = 0},
		.limits = {.min = 0, .max = 1000},
	};
	zassert_equal(ts_safety_register_channel(&over_max), TS_E_PARAM, "poweron 超 max 拒绝");

	static const ts_out_ch_t pwm_ch = { /* min=100 限幅用例 */
		.uid = "pwm1", .kind = TS_CH_PWM,
		.poweron = {.u = 100}, .linkloss = {.u = 100}, .fault = {.u = 100},
		.limits = {.min = 100, .max = 1000},
	};
	static const ts_out_ch_t slew_ch = { /* slew 用例：5/ms */
		.uid = "slew1", .kind = TS_CH_PWM,
		.poweron = {.u = 0}, .linkloss = {.u = 0}, .fault = {.u = 0},
		.limits = {.min = 0, .max = 1000, .slew_per_ms = 5},
	};
	static const ts_out_ch_t pwr_ch = { /* 受控供电（合同 7）：限流 500mA */
		.uid = "pwr1", .kind = TS_CH_POWER,
		.poweron = {.pwr = {.en = false, .ma = 0}},
		.linkloss = {.pwr = {.en = false, .ma = 0}},
		.fault = {.pwr = {.en = false, .ma = 0}},
		.limits = {.current_limit_ma = 500},
	};
	zassert_equal(ts_safety_register_channel(&pwm_ch), TS_OK);
	zassert_equal(ts_safety_register_channel(&slew_ch), TS_OK);
	zassert_equal(ts_safety_register_channel(&pwr_ch), TS_OK);
	zassert_equal(ts_safety_register_channel(&pwm_ch), TS_E_PARAM, "uid 撞名拒绝");

	/* ---- 2. 状态机与写路径保护 ---- */
	/* 非 ACTIVE（SAFE_POWERON）写入被拒（合同 3：输出拒写，输入不受影响） */
	v.u = 500;
	zassert_equal(ts_safety_commit("pwm1", v), TS_E_STATE, "commit before link");

	ts_safety_set_link(true); /* 链路确立 → ACTIVE */
	zassert_equal(ts_safety_channel_state("pwm1", &st), TS_OK);
	zassert_equal(st, TS_ST_ACTIVE, "POWERON -> ACTIVE");

	/* 限幅：commit 20 → clamp min=100，res=TS_E_RANGE（err.h：限幅=拦截） */
	v.u = 20;
	zassert_equal(ts_safety_commit("pwm1", v), TS_E_RANGE);
	zassert_equal(ts_safety_readback("pwm1", &rb), TS_OK);
	zassert_equal(rb.u, 100, "clamped to min");

	/* 断链 → SAFE_LINKLOSS：写入拒 + shadow=安全值；恢复不自动回写（DR-04） */
	ts_safety_set_link(false);
	zassert_equal(ts_safety_channel_state("pwm1", &st), TS_OK);
	zassert_equal(st, TS_ST_SAFE_LINKLOSS);
	v.u = 500;
	zassert_equal(ts_safety_commit("pwm1", v), TS_E_STATE, "commit in linkloss");
	zassert_equal(ts_safety_readback("pwm1", &rb), TS_OK);
	zassert_equal(rb.u, 100, "shadow = linkloss value");
	ts_safety_set_link(true);
	zassert_equal(ts_safety_readback("pwm1", &rb), TS_OK);
	zassert_equal(rb.u, 100, "DR-04: 恢复不回写断链前值");

	/* slew 数学（LLD §4-4）：slew1 5/ms */
	virt_now = 1000;
	v.u = 100;
	zassert_equal(ts_safety_commit("slew1", v), TS_OK);
	virt_now = 1010; /* Δt=10 → 界 = 5×11 = 55 */
	v.u = 155;
	zassert_equal(ts_safety_commit("slew1", v), TS_OK, "within slew bound");
	virt_now = 1011; /* Δt=1 → 界 = 5×2 = 10 */
	v.u = 300;
	zassert_equal(ts_safety_commit("slew1", v), TS_E_RANGE, "over slew → split");
	zassert_equal(ts_safety_readback("slew1", &rb), TS_OK);
	zassert_equal(rb.u, 165, "split to bound 155+10");

	/* ---- 3. 限流（TS_CH_POWER，LLD §4-5）：请求超限整笔拒绝 ---- */
	v.pwr.en = true;
	v.pwr.ma = 600;
	zassert_equal(ts_safety_commit("pwr1", v), TS_E_RANGE);
	zassert_equal(ts_safety_readback("pwr1", &rb), TS_OK);
	zassert_false(rb.pwr.en, "over-limit rejected entirely");
	v.pwr.ma = 400;
	zassert_equal(ts_safety_commit("pwr1", v), TS_OK);
	zassert_equal(ts_safety_readback("pwr1", &rb), TS_OK);
	zassert_true(rb.pwr.en);
	zassert_equal(rb.pwr.ma, 400);

	/* ---- 4. ISR 调 [thread] API 拒绝（LLD-00 §3） ---- */
	v.u = 500;
	zassert_equal(ts_safety_commit("pwm1", v), TS_OK, "前置：ACTIVE 可写");
	isr_commit_res = TS_OK;
	irq_offload(isr_commit_fn, "pwm1");
	zassert_equal(isr_commit_res, TS_E_PERM, "ISR 调 commit 必须被拒");

	/* ---- 5. 审计环形 64（DEC-27）：前段审计 9 次（ISR 拒绝发生在审计前，不计）
	 *        + 本段 70 次 = 79 → 保留 64，覆盖丢弃 15（DR-07） ---- */
	for (int i = 0; i < 70; i++) {
		ts_safety_commit("pwm1", v);
	}
	ts_audit_entry_t entries[64];
	size_t n = ts_safety_audit_copy(entries, 64);

	zassert_equal(n, 64, "ring keeps last 64");
	zassert_equal(ts_safety_audit_dropped(), 15, "9+70-64 overwritten");
	zassert_equal(entries[63].res, TS_OK, "newest is last commit");

	/* ---- 6. 容量 32（DEC-27）：填满后 NOMEM ---- */
	static ts_out_ch_t fill[29];
	static char names[29][16]; /* 静态存储：uid 必须指向持久内存 */

	for (int i = 0; i < 29; i++) {
		snprintf(names[i], sizeof(names[i]), "fill%02d", i);
		fill[i] = pwm_ch;
		fill[i].uid = names[i];
		zassert_equal(ts_safety_register_channel(&fill[i]), TS_OK, "fill %d", i);
	}
	static const ts_out_ch_t one_more = { /* 新 uid：撞满注册表 → NOMEM */
		.uid = "overflow1", .kind = TS_CH_GPIO,
		.poweron = {.b = false}, .linkloss = {.b = false}, .fault = {.b = false},
	};
	zassert_equal(ts_safety_register_channel(&one_more), TS_E_NOMEM, "registry full");

	/* ---- 7. estop 直达 + 锁存（合同 5/8；终态，置于场景末尾） ---- */
	ts_safety_force_all_fault();
	zassert_equal(ts_safety_channel_state("pwm1", &st), TS_OK);
	zassert_equal(st, TS_ST_SAFE_FAULT);
	zassert_equal(ts_safety_commit("pwm1", v), TS_E_STATE, "commit locked after estop");
	zassert_equal(ts_safety_clear_fault(), TS_E_STATE, "clear denied while forced latched");
	zassert_equal(ts_safety_readback("pwm1", &rb), TS_OK);
	zassert_equal(rb.u, 100, "fault value applied");

	ts_time_test_bind(NULL);
}

ZTEST_SUITE(framework_safety, NULL, NULL, NULL, NULL, NULL);
