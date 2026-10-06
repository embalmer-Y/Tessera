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

/* ---- ts-fs natives（DEC-47④，MD1.2e）--------------------------------
 * wasm 指针参数一律 validate_app_addr 后经 addr_app_to_native 落主机指针
 * （native_log_write 同纪律）。读类返回：>= 0 = 字节数；< 0 = ts_res_t。 */
#ifdef CONFIG_TS_HAL_FS
static char fs_path_buf[96];

static const char *fs_path_in(wasm_module_inst_t inst, uint32_t off, uint32_t len)
{
	if (len == 0 || len >= sizeof(fs_path_buf) ||
	    !wasm_runtime_validate_app_addr(inst, off, len)) {
		return NULL;
	}
	const char *src = (const char *)wasm_runtime_addr_app_to_native(inst, off);

	memcpy(fs_path_buf, src, len);
	fs_path_buf[len] = '\0';
	if (memchr(fs_path_buf, '\0', len) != NULL) {
		return NULL; /* 内嵌 NUL = 非法路径 */
	}
	return fs_path_buf;
}

static int32_t native_fs_read(wasm_exec_env_t env, uint32_t ctx_opaque,
			      uint32_t path_off, uint32_t path_len,
			      uint32_t off, uint32_t buf_off, uint32_t cap)
{
	ARG_UNUSED(ctx_opaque);
	wasm_module_inst_t inst = wasm_runtime_get_module_inst(env);
	const char *path = fs_path_in(inst, path_off, path_len);
	uint8_t *host;

	if (path == NULL || cap == 0 || cap > 0xFFFF ||
	    !wasm_runtime_validate_app_addr(inst, buf_off, cap)) {
		return TS_E_PARAM;
	}
	host = (uint8_t *)wasm_runtime_addr_app_to_native(inst, buf_off);
	uint16_t n = (uint16_t)cap;
	ts_res_t r = ts_fs_read(ctx_of(env), path, off, host, &n);

	return (r == TS_OK) ? (int32_t)n : (int32_t)r;
}

static int32_t native_fs_write(wasm_exec_env_t env, uint32_t ctx_opaque,
			       uint32_t path_off, uint32_t path_len,
			       uint32_t off, uint32_t data_off, uint32_t len)
{
	ARG_UNUSED(ctx_opaque);
	wasm_module_inst_t inst = wasm_runtime_get_module_inst(env);
	const char *path = fs_path_in(inst, path_off, path_len);
	const uint8_t *host;

	if (path == NULL || len > 0xFFFF ||
	    (len > 0 && !wasm_runtime_validate_app_addr(inst, data_off, len))) {
		return TS_E_PARAM;
	}
	host = (const uint8_t *)wasm_runtime_addr_app_to_native(inst, data_off);
	return (int32_t)ts_fs_write(ctx_of(env), path, off, host, (uint16_t)len);
}

static int32_t native_fs_list(wasm_exec_env_t env, uint32_t ctx_opaque,
			      uint32_t dir_off, uint32_t dir_len,
			      uint32_t out_off, uint32_t cap)
{
	ARG_UNUSED(ctx_opaque);
	wasm_module_inst_t inst = wasm_runtime_get_module_inst(env);
	const char *dir = fs_path_in(inst, dir_off, dir_len);
	char *host;

	if (dir == NULL || cap < 2 || cap > 0xFFFF ||
	    !wasm_runtime_validate_app_addr(inst, out_off, cap)) {
		return TS_E_PARAM;
	}
	host = (char *)wasm_runtime_addr_app_to_native(inst, out_off);
	uint16_t n = (uint16_t)cap;
	ts_res_t r = ts_fs_list(ctx_of(env), dir, host, n, &n);

	return (r == TS_OK) ? (int32_t)n : (int32_t)r;
}

static int32_t native_fs_delete(wasm_exec_env_t env, uint32_t ctx_opaque,
				uint32_t path_off, uint32_t path_len)
{
	ARG_UNUSED(ctx_opaque);
	wasm_module_inst_t inst = wasm_runtime_get_module_inst(env);
	const char *path = fs_path_in(inst, path_off, path_len);

	if (path == NULL) {
		return TS_E_PARAM;
	}
	return (int32_t)ts_fs_delete(ctx_of(env), path);
}
#endif /* CONFIG_TS_HAL_FS */

/* wasm 导入符号表（namespace "env"；签名 = wasm 参数/返回类型） */

static NativeSymbol ts_native_syms[] = {
	{"ts_gpio_write", native_gpio_write, "(iii)i", NULL},
	{"ts_gpio_read", native_gpio_read, "(ii)i", NULL},
	{"ts_pwm_set", native_pwm_set, "(iiii)i", NULL},
	{"ts_adc_read", native_adc_read, "(ii)i", NULL},
	{"ts_time_ms", native_time_ms, "(i)I", NULL},
	{"ts_log_write", native_log_write, "(iiii)i", NULL},
#ifdef CONFIG_TS_HAL_FS
	{"ts_fs_read", native_fs_read, "(iiiiii)i", NULL},
	{"ts_fs_write", native_fs_write, "(iiiiii)i", NULL},
	{"ts_fs_list", native_fs_list, "(iiiii)i", NULL},
	{"ts_fs_delete", native_fs_delete, "(iiii)i", NULL},
#endif
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
