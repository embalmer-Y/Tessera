/* SPDX-License-Identifier: Apache-2.0 */
/* 实例注册 + ts_api_v1 实现（LLD-ts-hal §3/§4）。
 * 输出路径：写类 API 全部收敛到 ts_safety_commit（零直接驱动调用——L5）。 */
#include <string.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/safety.h>
#include <zephyr/kernel.h>

/* ---- 实例注册（registry） ------------------------------------------------ */

#define MAX_DEVS CONFIG_TS_HAL_MAX_INSTANCES /* DEC-27 #7：24 */

static ts_hal_dev_desc_t devices[MAX_DEVS];
static size_t dev_count;

ts_res_t ts_hal_register_dev(const ts_hal_dev_desc_t *desc)
{
	if (desc == NULL || desc->uid == NULL || desc->uid[0] == '\0') {
		return TS_E_PARAM;
	}
	if (dev_count >= MAX_DEVS) return TS_E_NOMEM;
	devices[dev_count++] = *desc;
	return TS_OK;
}

size_t ts_hal_dev_count(void) { return dev_count; }
const ts_hal_dev_desc_t *ts_hal_dev_get(size_t idx)
{
	return idx < dev_count ? &devices[idx] : NULL;
}

/* 实例号 → uid 查找（写路径用） */
static const ts_hal_dev_desc_t *find_dev(uint8_t inst, ts_dev_kind_t kind)
{
	if (inst >= dev_count) return NULL;
	const ts_hal_dev_desc_t *d = &devices[inst];

	return d->kind == kind ? d : NULL;
}

/* ---- ts_api_v1（LLD-ts-hal §3）------------------------------------------- */

ts_res_t ts_gpio_write(ts_ctx_t c, uint8_t inst, bool v)
{
	ts_res_t r = ts_perm_check(c, TS_PERM_CLASS_GPIO, TS_PERM_OP_WRITE, inst);

	if (r != TS_OK) return r;
	const ts_hal_dev_desc_t *d = find_dev(inst, TS_DEV_GPIO_OUT);

	if (d == NULL) return TS_E_NOTFOUND;
	/* 唯一写路径：经 ts-safety 保护层（合同 2） */
	ts_out_value_t val = {.b = v};

	return ts_safety_commit(d->uid, val);
}

ts_res_t ts_gpio_read(ts_ctx_t c, uint8_t inst, bool *out)
{
	if (out == NULL) return TS_E_PARAM;
	ts_res_t r = ts_perm_check(c, TS_PERM_CLASS_GPIO, TS_PERM_OP_READ, inst);

	if (r != TS_OK) return r;
	/* 输入直读（合同 3：输入不受保护层影响）——V1 桩：从 ts-safety 影子值读 */
	const ts_hal_dev_desc_t *d = find_dev(inst, TS_DEV_GPIO_IN);

	if (d == NULL) return TS_E_NOTFOUND;
	ts_out_value_t v;

	/* GPIO_IN 无对应 out_ch——V1 用影子值近似（M3 接真驱动后改直读） */
	*out = false; /* 桩：M3 接真实 GPIO 输入驱动 */
	ARG_UNUSED(d);
	ARG_UNUSED(v);
	return TS_OK;
}

ts_res_t ts_pwm_set(ts_ctx_t c, uint8_t inst, uint32_t hz, uint16_t permille)
{
	ts_res_t r = ts_perm_check(c, TS_PERM_CLASS_PWM, TS_PERM_OP_SET, inst);

	if (r != TS_OK) return r;
	const ts_hal_dev_desc_t *d = find_dev(inst, TS_DEV_PWM);

	if (d == NULL) return TS_E_NOTFOUND;
	/* Hz 与 permille 打包进 u32（低 16 = permille，高 16 = Hz/100） */
	uint32_t u = ((uint32_t)(hz / 100) << 16) | (permille & 0xFFFFU);
	ts_out_value_t val = {.u = u};

	return ts_safety_commit(d->uid, val);
}

ts_res_t ts_adc_read(ts_ctx_t c, uint8_t inst, int32_t *mv)
{
	if (mv == NULL) return TS_E_PARAM;
	ts_res_t r = ts_perm_check(c, TS_PERM_CLASS_ADC, TS_PERM_OP_READ, inst);

	if (r != TS_OK) return r;
	/* V1 桩：M3 接真实 ADC 驱动 */
	*mv = 0;
	return TS_OK;
}

uint64_t ts_time_ms_api(ts_ctx_t c)
{
	ARG_UNUSED(c);
	return ts_time_ms(); /* 合同 9：唯一时间源（LLD-ts-hal §3） */
}

ts_res_t ts_log_write(ts_ctx_t c, uint8_t lvl, const char *msg, uint32_t len)
{
	ARG_UNUSED(c);
	ARG_UNUSED(lvl);
	ARG_UNUSED(msg);
	ARG_UNUSED(len);
	return TS_OK; /* V1：日志面走 printk / ts-net（M3 接入） */
}
