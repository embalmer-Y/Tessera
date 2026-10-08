/* SPDX-License-Identifier: Apache-2.0 */
/* 输入周期采集与变化上报（LLD-ts-hal §5，DR-02；G3 路由 = 单元 F）。
 * sysworkq 周期工作项（无独立线程）；只观测不改值（合同 3 观测侧落点）。
 * V1 采集面 = ADC 实例（真后端经 ts_adc_sample_fw；未绑定 = 桩 0mV 连续）；
 * 变化语义 = **传输级**（与上次采样不同即发）——阈值/滞回语义归 APP 逻辑
 * （D4/D6 演示即此分工；框架不引入未裁默认值）。数字 GPIO_IN 直读留桩
 * （无板级绑定面；DR-11 后续）。
 * 消费：ts_evt 总线（TS_EVT_INPUT_CHANGED，ts-net pub 外发 + ts-appmgr
 * 订阅路由进 APP mailbox——runtime.c，G3）。 */
#include <string.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <zephyr/kernel.h>

static struct k_work_delayable input_work;
static bool started;
static int32_t last_mv[CONFIG_TS_HAL_MAX_INSTANCES];
static bool have_last[CONFIG_TS_HAL_MAX_INSTANCES];

#ifdef CONFIG_TS_TEST
/* 测试注入（G3 用例：无真后端时驱动变化序列） */
static bool inj_used[CONFIG_TS_HAL_MAX_INSTANCES];
static int32_t inj_mv[CONFIG_TS_HAL_MAX_INSTANCES];

void ts_hal_input_test_inject(uint32_t inst, int32_t mv)
{
	if (inst < CONFIG_TS_HAL_MAX_INSTANCES) {
		inj_used[inst] = true;
		inj_mv[inst] = mv;
	}
}
#endif

static void input_poll_fn(struct k_work *work)
{
	struct k_work_delayable *d = k_work_delayable_from_work(work);

	ts_hal_input_poll_once();
	k_work_reschedule_for_queue(&k_sys_work_q, d,
				     K_MSEC(CONFIG_TS_HAL_INPUT_POLL_MS));
}

void ts_hal_input_poll_once(void)
{
	for (size_t i = 0; i < ts_hal_dev_count(); i++) {
		const ts_hal_dev_desc_t *d = ts_hal_dev_get(i);

		if (d == NULL || d->kind != TS_DEV_ADC) {
			continue; /* V1 采集面 = ADC（见文件头） */
		}
		int32_t mv = 0;
#ifdef CONFIG_TS_TEST
		if (i < CONFIG_TS_HAL_MAX_INSTANCES && inj_used[i]) {
			mv = inj_mv[i]; /* 注入优先（测试确定性） */
		} else
#endif
		if (ts_adc_sample_fw((uint8_t)i, &mv) != TS_OK) {
			continue; /* 读失败如实跳过本拍（下拍重试） */
		}
		if (have_last[i] && last_mv[i] != mv) {
			const struct ts_input_evt payload = {
				.inst = (uint32_t)i,
				.old_mv = last_mv[i],
				.new_mv = mv,
			};
			const ts_evt_t evt = {
				.id = TS_EVT_INPUT_CHANGED,
				.t_ms = ts_time_ms(),
				.data = &payload,
				.len = sizeof(payload),
			};
			ts_evt_publish(&evt);
		}
		last_mv[i] = mv;
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
