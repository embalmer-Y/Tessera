/* SPDX-License-Identifier: Apache-2.0 */
/* 单调时间服务（LLD-ts-core §3）：合同 9 唯一时间源；测试构建可注入虚拟时钟。 */
#include <ts/core.h>
#include <zephyr/kernel.h>

static uint64_t now_default(void)
{
	return (uint64_t)k_uptime_get();
}

#ifdef CONFIG_TS_TEST
static const ts_time_source_t *bound_src;

void ts_time_test_bind(const ts_time_source_t *src)
{
	bound_src = src;
}

uint64_t ts_time_ms(void)
{
	if (bound_src != NULL) {
		return bound_src->now_ms();
	}
	return now_default();
}
#else
uint64_t ts_time_ms(void)
{
	return now_default();
}
#endif
