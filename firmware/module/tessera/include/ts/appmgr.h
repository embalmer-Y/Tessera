/* SPDX-License-Identifier: Apache-2.0 */
/* ts-appmgr 公共 API（design/LLD-ts-appmgr.md）：包接收/验签/双 slot 存储/
 * 版本与回滚；WAMR 宿主（M2b.2 交付）；APP 生命周期状态机。 */
#ifndef TS_APPMGR_H__
#define TS_APPMGR_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <ts/err.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- APP 生命周期状态机（LLD-ts-appmgr §4）------------------------------ */

typedef enum {
	TS_APP_RECEIVED,    /* 包到达（尚未验签） */
	TS_APP_VERIFIED,    /* 验签通过（尚未写 slot） */
	TS_APP_STAGED,      /* 已写 slot + meta（待加载周期） */
	TS_APP_ACTIVE,      /* 运行中 */
	TS_APP_ROLLBACK,    /* 健康失败回退中 */
	TS_APP_QUARANTINED, /* 回滚计数超限（终态，需人工解除） */
} ts_app_state_t;

typedef struct {
	ts_app_state_t state;
	uint8_t active_slot;     /* 0=A, 1=B */
	uint8_t rollback_count;  /* 回滚计数（超限 → QUARANTINED） */
	char app_id[64];
	char app_ver[16];
} ts_app_info_t;

/** 安装一个 TSAP 包（验签 → 写 inactive slot → meta 原子切换）。
 * 验签使用根公钥（prov 或测试注入）。返回 app 信息。 */
ts_res_t ts_appmgr_install(const uint8_t *pkg_data, size_t pkg_len,
			    const uint8_t root_pubkey[32], ts_app_info_t *out);

/** 获取当前 active APP 信息。 */
ts_res_t ts_appmgr_get_info(ts_app_info_t *out);

/** 健康探针超时回调（health.c 周期检查发现超时时调用）→ 触发回滚或隔离。 */
ts_res_t ts_appmgr_health_fail(void);

/** 显式回滚（sys 命令或健康探针路径）。 */
ts_res_t ts_appmgr_rollback(void);

/* 回滚计数上限（DEC-27 #9：3；超限 → QUARANTINED） */
#define TS_APPMGR_ROLLBACK_LIMIT 3

/* ---- meta 记录（slot.c ↔ ts-store meta kv）------------------------------- */

typedef struct {
	uint8_t active_slot;
	uint8_t rollback_count;
	uint16_t boot_gen;
	uint32_t app_ver_u32; /* semver → u32 比较 */
} ts_appmgr_meta_t;

ts_res_t ts_appmgr_meta_read(ts_appmgr_meta_t *meta);
ts_res_t ts_appmgr_meta_write(const ts_appmgr_meta_t *meta);

/* ---- 测试钩子（CONFIG_TS_TEST）------------------------------------------- */
#ifdef CONFIG_TS_TEST
void ts_appmgr_test_reset(void);
#endif

#ifdef __cplusplus
}
#endif

#endif /* TS_APPMGR_H__ */
