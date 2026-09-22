/* SPDX-License-Identifier: Apache-2.0 */
/*
 * 驱动分发（LLD-ts-safety §6）——全库**唯一**出现 Zephyr 输出驱动调用的文件
 * （L5 机械检查白名单 = 本文件；testing.md §3.1）。
 * M1：三 kind 均为 native_sim 桩（写序列环形记录 = L4 golden 数据源）；
 * 真机 GPIO/PWM/PMIC 驱动随板级移植替换，写函数只依赖注册期冻结数据（可重入/无锁）。
 */
#include <string.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/util.h>
#include <ts/safety.h>
#include "internal.h"

static struct ts_ch_slot *slot_of(const ts_out_ch_t *ch)
{
	for (size_t i = 0; i < ts_ch_count; i++) {
		if (ts_ch_table[i].desc == ch) {
			return &ts_ch_table[i];
		}
	}
	return NULL;
}

static void sim_record(struct ts_ch_slot *s, const ts_out_value_t *v)
{
	if (s == NULL) {
		return;
	}
	s->sim_rec.ring[s->sim_rec.head] = (ts_write_rec_t){
		.t_ms = ts_time_ms(),
		.value_u = ts_value_encode(s->desc->kind, *v),
	};
	s->sim_rec.head = (s->sim_rec.head + 1) % TS_SIM_REC_PER_CH;
	if (s->sim_rec.count < TS_SIM_REC_PER_CH) {
		s->sim_rec.count++;
	}
}

static void sim_write(const ts_out_ch_t *ch, const ts_out_value_t *v)
{
	/* native_sim 桩：真机此处为 gpio_pin_set / pwm_set_* 等唯一合法调用点。 */
	sim_record(slot_of(ch), v);
}

static int sim_read(const ts_out_ch_t *ch, ts_out_value_t *out)
{
	struct ts_ch_slot *s = slot_of(ch);

	if (s == NULL) {
		return -1;
	}
	*out = s->shadow;
	return 0;
}

const ts_driver_ops_t ts_drivers[TS_CH_KIND_COUNT] = {
	[TS_CH_GPIO] = {sim_write, sim_read},
	[TS_CH_PWM] = {sim_write, sim_read},
	[TS_CH_POWER] = {sim_write, sim_read},
};

size_t ts_driversim_writes(const char *uid, ts_write_rec_t *out, size_t max)
{
	int i = ts_ch_find(uid);

	if (i < 0) {
		return 0;
	}
	struct ts_ch_slot *s = &ts_ch_table[i];
	size_t n = s->sim_rec.count < max ? s->sim_rec.count : max;

	for (size_t k = 0; k < n; k++) {
		size_t idx = (s->sim_rec.head + TS_SIM_REC_PER_CH - s->sim_rec.count + k) %
			     TS_SIM_REC_PER_CH;
		out[k] = s->sim_rec.ring[idx];
	}
	return n;
}

/* ---- estop DT 绑定（DR-11）与 ISR 粘合 ---------------------------------- */

#define ESTOP_GPIO_NODE DT_CHOSEN(ts_estop_gpio) /* chosen: ts,estop-gpio */

#if DT_NODE_EXISTS(ESTOP_GPIO_NODE)
static const struct gpio_dt_spec estop_spec = GPIO_DT_SPEC_GET(ESTOP_GPIO_NODE, gpios);
static struct gpio_callback estop_cb;

/* estop ISR：直达安全态，不经协议栈/调度排队（合同 5；L5 调用图审计目标）。 */
static void estop_isr(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
	ARG_UNUSED(dev);
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);
	ts_safety_force_all_fault();
}
#endif

ts_res_t ts_safety_estop_init(void)
{
#if DT_NODE_EXISTS(ESTOP_GPIO_NODE)
	if (!gpio_is_ready_dt(&estop_spec)) {
		return TS_E_IO;
	}
	/* 触发沿随 prov 配置（M2a 接线；当前占位上升沿）——来源: LLD DR-11 */
	gpio_init_callback(&estop_cb, estop_isr, BIT(estop_spec.pin));
	if (gpio_add_callback_dt(&estop_spec, &estop_cb) != 0) {
		return TS_E_IO;
	}
	if (gpio_pin_interrupt_configure_dt(&estop_spec, GPIO_INT_EDGE_RISING) != 0) {
		return TS_E_IO;
	}
#endif
	return TS_OK; /* 无节点板（native_sim/测试）空操作；生产板必须提供（M2+ 板级强化） */
}
