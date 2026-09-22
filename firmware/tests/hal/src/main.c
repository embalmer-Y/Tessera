/* SPDX-License-Identifier: Apache-2.0 */
/* ts-hal L1/L2 测试（LLD-ts-hal §7）：文法解析全分支 / 越权裁决 / API 面 /
 * 实例注册边界。 */
#include <string.h>
#include <zephyr/ztest.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/safety.h>

/* ---- 文法解析全分支（L1）------------------------------------------------ */

ZTEST(framework_hal, test_03_perm_parse_valid)
{
	ts_perm_table_t t;

	ts_perm_table_init(&t);
	zassert_equal(ts_perm_parse("gpio:write:0-3", &t), TS_OK);
	zassert_equal(ts_perm_parse("adc:read:0,2", &t), TS_OK);
	zassert_equal(ts_perm_parse("power:set:1", &t), TS_OK);
	zassert_equal(ts_perm_parse("sys:read:0", &t), TS_OK);
	zassert_equal(ts_perm_parse("gpio:read:5", &t), TS_OK);
	zassert_equal(ts_perm_parse("pwm:set:0-15", &t), TS_OK);

	/* 验证位图 */
	uint32_t gpio_write = t.bitmap[TS_PERM_CLASS_GPIO][TS_PERM_OP_WRITE];

	zassert_true(gpio_write & 0x0F, "gpio:write:0-3 → bits 0-3");
	zassert_false(gpio_write & 0x10, "bit 4 not set");
	uint32_t adc_read = t.bitmap[TS_PERM_CLASS_ADC][TS_PERM_OP_READ];

	zassert_true(adc_read & 0x05, "adc:read:0,2 → bits 0,2");
	zassert_false(adc_read & 0x02, "bit 1 not set");
}

ZTEST(framework_hal, test_04_perm_parse_invalid)
{
	ts_perm_table_t t;

	ts_perm_table_init(&t);
	/* 非法类/操作/实例格式 */
	zassert_equal(ts_perm_parse(NULL, &t), TS_E_PARAM);
	zassert_equal(ts_perm_parse("bad:write:0", &t), TS_E_PARAM);
	zassert_equal(ts_perm_parse("gpio:bad:0", &t), TS_E_PARAM);
	zassert_equal(ts_perm_parse("gpio:write", &t), TS_E_PARAM);
	zassert_equal(ts_perm_parse("gpio:write:xyz", &t), TS_E_PARAM);
	zassert_equal(ts_perm_parse("gpio:write:0-", &t), TS_E_PARAM);
	zassert_equal(ts_perm_parse("gpio:write:3-1", &t), TS_E_PARAM);
	zassert_equal(ts_perm_parse("gpio:write:99", &t), TS_E_PARAM); /* >31 */
}

/* ---- 越权裁决（L1，含边界实例号）---------------------------------------- */

ZTEST(framework_hal, test_02_perm_check_allowed_and_denied)
{
	ts_perm_table_t t;
	ts_ctx_t ctx;

	ts_perm_table_init(&t);
	zassert_equal(ts_perm_parse("gpio:write:0-3", &t), TS_OK);
	zassert_equal(ts_perm_parse("gpio:read:5", &t), TS_OK);

	zassert_equal(ts_hal_bind_context(&ctx, 1, &t), TS_OK);

	/* 授权范围 */
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_GPIO, TS_PERM_OP_WRITE, 0), TS_OK);
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_GPIO, TS_PERM_OP_WRITE, 3), TS_OK);
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_GPIO, TS_PERM_OP_READ, 5), TS_OK);

	/* 越权 */
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_GPIO, TS_PERM_OP_WRITE, 4), TS_E_PERM);
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_GPIO, TS_PERM_OP_READ, 0), TS_E_PERM);
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_ADC, TS_PERM_OP_READ, 0), TS_E_PERM);
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_PWM, TS_PERM_OP_SET, 0), TS_E_PERM);

	/* 边界实例号 */
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_GPIO, TS_PERM_OP_WRITE, 31), TS_E_PERM);

	/* 未绑定 ctx */
	ts_ctx_t rogue = {.app_id = 99};
	zassert_equal(ts_perm_check(rogue, TS_PERM_CLASS_GPIO, TS_PERM_OP_WRITE, 0), TS_E_PERM);

	ts_hal_unbind_context(&ctx);
	zassert_equal(ts_perm_check(ctx, TS_PERM_CLASS_GPIO, TS_PERM_OP_WRITE, 0), TS_E_PERM);
}

/* ---- ts_api_v1（L2：写 → 安全层传播）----------------------------------- */

ZTEST(framework_hal, test_01_gpio_write_via_safety)
{
	/* 注册输出通道（ts-safety）+ HAL 设备实例 */
	static const ts_out_ch_t led_ch = {
		.uid = "led1", .kind = TS_CH_GPIO,
		.poweron = {.b = false}, .linkloss = {.b = false}, .fault = {.b = false},
	};
	static const ts_hal_dev_desc_t led_dev = {
		.uid = "led1", .kind = TS_DEV_GPIO_OUT,
	};
	zassert_equal(ts_safety_register_channel(&led_ch), TS_OK);
	zassert_equal(ts_hal_register_dev(&led_dev), TS_OK);

	/* 绑定 ctx with gpio:write:0 */
	ts_perm_table_t t;
	ts_ctx_t ctx;

	ts_perm_table_init(&t);
	zassert_equal(ts_perm_parse("gpio:write:0", &t), TS_OK);
	zassert_equal(ts_hal_bind_context(&ctx, 2, &t), TS_OK);

	/* 链路未建立 → commit 被拒（安全层拦截传播） */
	zassert_equal(ts_gpio_write(ctx, 0, true), TS_E_STATE);

	/* 链路建立 → 写成功 */
	ts_safety_set_link(true);
	zassert_equal(ts_gpio_write(ctx, 0, true), TS_OK);
	ts_out_value_t rb;

	zassert_equal(ts_safety_readback("led1", &rb), TS_OK);
	zassert_true(rb.b, "gpio write propagated through safety");

	/* 越权实例 → TS_E_PERM */
	zassert_equal(ts_gpio_write(ctx, 1, true), TS_E_PERM);
	zassert_equal(ts_gpio_write(ctx, 0, true), TS_OK); /* 0 仍可用 */

	ts_hal_unbind_context(&ctx);
}

/* ---- 实例注册边界（L1）--------------------------------------------------- */

ZTEST(framework_hal, test_09_dev_registry_bounds)
{
	zassert_equal(ts_hal_register_dev(NULL), TS_E_PARAM);

	/* 动态填满（不论当前已注册多少） */
	static ts_hal_dev_desc_t fill[CONFIG_TS_HAL_MAX_INSTANCES];
	static char names[CONFIG_TS_HAL_MAX_INSTANCES][16];
	int filled = 0;

	while (ts_hal_dev_count() < CONFIG_TS_HAL_MAX_INSTANCES && filled < CONFIG_TS_HAL_MAX_INSTANCES) {
		snprintf(names[filled], sizeof(names[filled]), "pad%d", filled);
		fill[filled].uid = names[filled];
		fill[filled].kind = TS_DEV_GPIO_IN;
		if (ts_hal_register_dev(&fill[filled]) != TS_OK) break;
		filled++;
	}
	zassert_equal(ts_hal_dev_count(), CONFIG_TS_HAL_MAX_INSTANCES, "filled to max");
	static const ts_hal_dev_desc_t one_more = {.uid = "overflow", .kind = TS_DEV_ADC};
	zassert_equal(ts_hal_register_dev(&one_more), TS_E_NOMEM, "registry full");
}

ZTEST_SUITE(framework_hal, NULL, NULL, NULL, NULL, NULL);
