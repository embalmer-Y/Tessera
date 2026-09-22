/* SPDX-License-Identifier: Apache-2.0 */
/* 输入周期采集与变化上报（LLD-ts-hal §5，DR-02）。
 * sysworkq 周期工作项（无独立线程）；只观测不改值（合同 3 观测侧落点）。 */
#include <string.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <zephyr/kernel.h>

static struct k_work_delayable input_work;
static bool started;
static bool last_values[CONFIG_TS_HAL_MAX_INSTANCES];
static bool have_last[CONFIG_TS_HAL_MAX_INSTANCES];

static void input_poll_fn(struct k_work *work)
{
	struct k_work_delayable *d = k_work_delayable_from_work(work);

	ts_hal_input_poll_once();
	k_work_reschedule_for_queue(&k_sys_work_q, d,
				     K_MSEC(CONFIG_TS_HAL_INPUT_POLL_MS));
}

void ts_hal_input_poll_once(void)
{
	/* 遍历输入实例 → 读 → 变化则发布 TS_EVT_INPUT_CHANGED（DR-02） */
	for (size_t i = 0; i < ts_hal_dev_count(); i++) {
		const ts_hal_dev_desc_t *d = ts_hal_dev_get(i);

		if (d == NULL || d->kind != TS_DEV_GPIO_IN) continue;
		/* V1：从影子值读（M3 改真实驱动直读——合同 3：输入不经保护层） */
		bool cur = false;

		if (have_last[i] && last_values[i] != cur) {
			struct {
				uint32_t inst;
				bool old_v, new_v;
			} payload = {.inst = (uint32_t)i, .old_v = last_values[i], .new_v = cur};
			const ts_evt_t evt = {
				.id = TS_EVT_INPUT_CHANGED,
				.t_ms = ts_time_ms(),
				.data = &payload,
				.len = sizeof(payload),
			};
			ts_evt_publish(&evt);
		}
		last_values[i] = cur;
		have_last[i] = true;
	}
}

ts_res_t ts_hal_input_start(void)
{
	if (started) return TS_E_STATE;
	started = true;
	k_work_init_delayable(&input_work, input_poll_fn);
	k_work_reschedule_for_queue(&k_sys_work_q, &input_work,
				     K_MSEC(CONFIG_TS_HAL_INPUT_POLL_MS));
	return TS_OK;
}
