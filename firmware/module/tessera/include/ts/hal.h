/* SPDX-License-Identifier: Apache-2.0 */
/*
 * ts-hal 公共 API（design/LLD-ts-hal.md）：面向 APP 的板无关外设 API +
 * **权限执行点**（manifest 能力 → 每调用裁决，合同 10）。
 * 输出路径：写类 API 全部收敛到 ts_safety_commit（本模块零直接驱动调用——L5）。
 */
#ifndef TS_HAL_H__
#define TS_HAL_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <ts/err.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- ts_ctx_t（LLD-00 §3.1，DR-10）：调用者不透明上下文 ------------------ */
struct ts_ctx_opaque {
	uint16_t app_id;    /* 分配序号（ts-appmgr 管理） */
	uint16_t _rsv;
};
struct ts_ctx_opaque;
typedef struct ts_ctx_opaque ts_ctx_t;

/* ---- 能力文法 ts_perm_v1（LLD-ts-hal §2）-------------------------------- */

typedef enum {
	TS_PERM_CLASS_GPIO,
	TS_PERM_CLASS_PWM,
	TS_PERM_CLASS_ADC,
	TS_PERM_CLASS_POWER,
	TS_PERM_CLASS_MSG,
	TS_PERM_CLASS_SYS,
	TS_PERM_CLASS_COUNT,
} ts_perm_class_t;

typedef enum {
	TS_PERM_OP_READ,
	TS_PERM_OP_WRITE,
	TS_PERM_OP_SET,
	TS_PERM_OP_COUNT,
} ts_perm_op_t;

/* 实例位图：每 class 最多 32 实例（CONFIG_TS_HAL_MAX_INSTANCES=24 → 够用） */
typedef struct {
	uint32_t bitmap[TS_PERM_CLASS_COUNT][TS_PERM_OP_COUNT];
} ts_perm_table_t;

/** 解析一条能力串（"class:op:instances"）→ 更新表。返回 TS_OK 或 TS_E_PARAM。 */
ts_res_t ts_perm_parse(const char *cap, ts_perm_table_t *table);

/** 裁决：class+op+inst 是否在表内。返回 TS_OK 或 TS_E_PERM（+ 事件发布）。 */
ts_res_t ts_perm_check(ts_ctx_t ctx, ts_perm_class_t cls, ts_perm_op_t op, uint8_t inst);

/** 清零表（加载期用）。 */
void ts_perm_table_init(ts_perm_table_t *table);

/** 绑定 ctx → perm 表（ts-appmgr 加载 APP 时调用；一对一绑定）。 */
ts_res_t ts_hal_bind_context(ts_ctx_t *ctx, uint16_t app_id, const ts_perm_table_t *table);
void ts_hal_unbind_context(ts_ctx_t *ctx);

/* ---- ts_api_v1（APP 可见的全部导入符号，LLD-ts-hal §3）------------------ */

ts_res_t ts_gpio_write(ts_ctx_t c, uint8_t inst, bool v);
ts_res_t ts_gpio_read(ts_ctx_t c, uint8_t inst, bool *out);
ts_res_t ts_pwm_set(ts_ctx_t c, uint8_t inst, uint32_t hz, uint16_t permille);
ts_res_t ts_adc_read(ts_ctx_t c, uint8_t inst, int32_t *mv);
uint64_t ts_time_ms_api(ts_ctx_t c);
ts_res_t ts_log_write(ts_ctx_t c, uint8_t lvl, const char *msg, uint32_t len);

/* ---- 实例注册（registry.c，ts-periph 调用）------------------------------ */

typedef enum {
	TS_DEV_GPIO_OUT,
	TS_DEV_GPIO_IN,
	TS_DEV_PWM,
	TS_DEV_ADC,
	TS_DEV_POWER,
} ts_dev_kind_t;

typedef struct {
	const char *uid;       /* 稳定逻辑名（命名空间寻址用） */
	ts_dev_kind_t kind;
	uint8_t ts_out_ch_idx; /* TS_DEV_GPIO_OUT/PWM/POWER → ts-safety 通道 uid 哈希映射 */
} ts_hal_dev_desc_t;

ts_res_t ts_hal_register_dev(const ts_hal_dev_desc_t *desc);
size_t ts_hal_dev_count(void);
const ts_hal_dev_desc_t *ts_hal_dev_get(size_t idx);

/* ---- 输入采集 input monitor（DR-02）-------------------------------------- */

/** 启动输入轮询周期项（sysworkq，无独立线程）。 */
ts_res_t ts_hal_input_start(void);

/** 单次采集（input_poll_fn 内部调用 + 测试钩子）。 */
void ts_hal_input_poll_once(void);

#ifdef __cplusplus
}
#endif

#endif /* TS_HAL_H__ */
