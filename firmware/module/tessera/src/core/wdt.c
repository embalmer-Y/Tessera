/* SPDX-License-Identifier: Apache-2.0 */
/*
 * 看门狗框架（LLD-ts-core §5）：喂狗注册表 + sysworkq 巡检。
 * 合同 4：每子系统独立喂狗（可定位卡死来源）；逾期 → WDT_WARN → system_fail。
 */
#include <ts/core.h>
#include <ts/safety.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>

struct wdt_src {
	uint32_t period_ms;
	atomic_t last_feed32; /* ts_time_ms 低 32 位；无符号差值对回绕安全 */
	bool registered;
};

static struct wdt_src srcs[TS_WDT_COUNT];
static bool started;

/* 硬 WDT 超时 = min(2×max(periods), 10000ms)（来源: DEC-22 / DEC-27） */
#define TS_HARD_WDT_CAP_MS 10000

static uint32_t elapsed_since(const struct wdt_src *s)
{
	uint32_t now32 = (uint32_t)ts_time_ms();
	uint32_t last = (uint32_t)atomic_get(&s->last_feed32);

	return now32 - last;
}

ts_res_t ts_wdt_register(ts_wdt_src_t src, uint32_t period_ms)
{
	if (src >= TS_WDT_COUNT || period_ms == 0 || started) {
		return TS_E_PARAM;
	}
	if (srcs[src].registered) {
		return TS_E_STATE;
	}
	srcs[src].registered = true;
	srcs[src].period_ms = period_ms;
	atomic_set(&srcs[src].last_feed32, (atomic_val_t)(uint32_t)ts_time_ms());
	return TS_OK;
}

void ts_wdt_feed(ts_wdt_src_t src)
{
	if (src < TS_WDT_COUNT) {
		atomic_set(&srcs[src].last_feed32, (atomic_val_t)(uint32_t)ts_time_ms());
	}
}

/* 巡检：返回首个逾期源；无则 TS_WDT_COUNT。 */
ts_wdt_src_t ts_wdt_patrol_once(void)
{
	for (int s = 0; s < TS_WDT_COUNT; s++) {
		if (!srcs[s].registered) {
			continue;
		}
		if (elapsed_since(&srcs[s]) > srcs[s].period_ms) {
			/* LLD §5：先 WDT_WARN（带 src 与最后 feed 时间）→ system_fail */
			struct {
				ts_wdt_src_t src;
				uint32_t last_feed;
			} payload = {
				.src = (ts_wdt_src_t)s,
				.last_feed = (uint32_t)atomic_get(&srcs[s].last_feed32),
			};
			const ts_evt_t evt = {
				.id = TS_EVT_WDT_WARN,
				.t_ms = ts_time_ms(),
				.data = &payload,
				.len = sizeof(payload),
			};

			ts_evt_publish(&evt);
			return (ts_wdt_src_t)s;
		}
	}
	return TS_WDT_COUNT;
}

static void patrol_work_cb(struct k_work *work)
{
	struct k_work_delayable *d = k_work_delayable_from_work(work);

	ts_safety_estop_deferred_publish(); /* estop 事后补发（合同 5，复用巡检节奏） */
	ts_wdt_src_t overdue = ts_wdt_patrol_once();

	if (overdue != TS_WDT_COUNT) {
		ts_safety_system_fail(TS_FAIL_WDT(overdue));
		/* 停止重排巡检（停喂语义由 system_fail 停机保证） */
		return;
	}
	uint32_t delay = ts_wdt_patrol_period_ms();

	k_work_reschedule_for_queue(&k_sys_work_q, d, K_MSEC(delay));
}

static struct k_work_delayable patrol_work;

uint32_t ts_wdt_patrol_period_ms(void)
{
	uint32_t min_p = UINT32_MAX;

	for (int s = 0; s < TS_WDT_COUNT; s++) {
		if (srcs[s].registered && srcs[s].period_ms < min_p) {
			min_p = srcs[s].period_ms;
		}
	}
	if (min_p == UINT32_MAX) {
		min_p = TS_HARD_WDT_CAP_MS; /* 无注册源：按硬 WDT 上限巡检 */
	}
	return min_p / 2 < 1 ? 1 : min_p / 2; /* 巡检周期 = min(periods)/2（LLD §5） */
}

ts_res_t ts_wdt_start(void)
{
	if (started) {
		return TS_E_STATE;
	}
	started = true;
	k_work_init_delayable(&patrol_work, patrol_work_cb);
	k_work_reschedule_for_queue(&k_sys_work_q, &patrol_work,
				    K_MSEC(ts_wdt_patrol_period_ms()));
	return TS_OK;
}
