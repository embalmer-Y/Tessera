/* SPDX-License-Identifier: Apache-2.0 */
/* ts_api_v1 的 wasm 导入面（DEC-25 最小导入面 = 权限硬边界落点；
 * LLD-ts-hal §3 + LLD-ts-appmgr §5）。
 * 防伪造（LLD-00 §3.1）：调用者 ctx 由宿主经 exec_env user_data 注入
 * （runtime.c），wasm 传入的 ctx 位仅作不透明占位——natives 只信注入值。
 * 权限裁决：全部经 ts-hal（perm 表 + TS_EVT_PERM_DENIED 留痕 = 合同 10）。
 * 已知偏差（LLD-ts-appmgr 修订登记）：WAMR natives 为全局注册，
 * "未授权符号链接期不存在"的结构化装配留待 WAMR per-instance 支持；
 * 调用期拒绝不削弱合同 10（越权拒绝 + 留痕完整）。
 * V1 符号集 = ts-hal 已实现子集（gpio/pwm/adc/time/log）；msg/power_set
 * 随对应 hal API 实装后追加。
 * 读类返回约定：>= 0 = 值；< 0 = ts_res_t 错误码（err.h 负数）。 */
#include <inttypes.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <ts/hal.h>
#include <wasm_export.h>

struct ts_app_rt; /* runtime.c 内部类型（仅指针身份） */
extern ts_ctx_t ts_app_rt_ctx(struct ts_app_rt *rt);
extern uint16_t ts_app_rt_id(struct ts_app_rt *rt);

static ts_ctx_t ctx_of(wasm_exec_env_t env)
{
	return ts_app_rt_ctx((struct ts_app_rt *)wasm_runtime_get_user_data(env));
}

static int32_t native_gpio_write(wasm_exec_env_t env, uint32_t ctx_opaque,
				 uint32_t inst, uint32_t v)
{
	ARG_UNUSED(ctx_opaque);
	return (int32_t)ts_gpio_write(ctx_of(env), (uint8_t)inst, v != 0);
}

static int32_t native_gpio_read(wasm_exec_env_t env, uint32_t ctx_opaque,
				uint32_t inst)
{
	ARG_UNUSED(ctx_opaque);
	bool v = false;
	ts_res_t r = ts_gpio_read(ctx_of(env), (uint8_t)inst, &v);

	return (r == TS_OK) ? (v ? 1 : 0) : (int32_t)r;
}

static int32_t native_pwm_set(wasm_exec_env_t env, uint32_t ctx_opaque,
			      uint32_t inst, uint32_t hz, uint32_t permille)
{
	ARG_UNUSED(ctx_opaque);
	return (int32_t)ts_pwm_set(ctx_of(env), (uint8_t)inst, hz,
				   (uint16_t)permille);
}

static int32_t native_adc_read(wasm_exec_env_t env, uint32_t ctx_opaque,
			       uint32_t inst)
{
	ARG_UNUSED(ctx_opaque);
	int32_t mv = 0;
	ts_res_t r = ts_adc_read(ctx_of(env), (uint8_t)inst, &mv);

	return (r == TS_OK) ? mv : (int32_t)r;
}

static int64_t native_time_ms(wasm_exec_env_t env, uint32_t ctx_opaque)
{
	ARG_UNUSED(ctx_opaque);
	return (int64_t)ts_time_ms_api(ctx_of(env));
}

static int32_t native_log_write(wasm_exec_env_t env, uint32_t ctx_opaque,
				uint32_t lvl, uint32_t msg_off, uint32_t len)
{
	ARG_UNUSED(ctx_opaque);
	wasm_module_inst_t inst = wasm_runtime_get_module_inst(env);
	char buf[96];

	if (len == 0 || len >= sizeof(buf) ||
	    !wasm_runtime_validate_app_addr(inst, msg_off, len)) {
		return TS_E_PARAM;
	}
	const char *src = (const char *)wasm_runtime_addr_app_to_native(inst, msg_off);

	memcpy(buf, src, len);
	buf[len] = '\0';
	printk("[app%u/l%u] %s\n", (unsigned)ts_app_rt_id(
		       (struct ts_app_rt *)wasm_runtime_get_user_data(env)),
	       (unsigned)lvl, buf);
	return TS_OK;
}

/* wasm 导入符号表（namespace "env"；签名 = wasm 参数/返回类型） */
static NativeSymbol ts_native_syms[] = {
	{"ts_gpio_write", native_gpio_write, "(iii)i", NULL},
	{"ts_gpio_read", native_gpio_read, "(ii)i", NULL},
	{"ts_pwm_set", native_pwm_set, "(iiii)i", NULL},
	{"ts_adc_read", native_adc_read, "(ii)i", NULL},
	{"ts_time_ms", native_time_ms, "(i)I", NULL},
	{"ts_log_write", native_log_write, "(iiii)i", NULL},
};

bool ts_app_natives_register(void)
{
	static bool done;

	if (done) {
		return true;
	}
	done = wasm_runtime_register_natives(
		"env", ts_native_syms,
		sizeof(ts_native_syms) / sizeof(ts_native_syms[0]));
	return done;
}
