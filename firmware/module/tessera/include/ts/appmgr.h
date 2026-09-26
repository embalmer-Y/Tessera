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

/* ---- 分步安装（远程部署面，LLD-A06 §3；upload→verify→activate）-----------
 * 供 ts-net sys/app-* 命令消费：chunk 增量写 inactive slot（断点续传），
 * verify 只校验不动 meta，activate 才整槽 hash + meta 原子切换——与
 * ts_appmgr_install 同一内部链（行为一致）。staging 状态在内存，begin
 * 可重入（新 begin 重置进度）。 */
ts_res_t ts_appmgr_stage_begin(uint32_t total_len, uint8_t *slot_out);
ts_res_t ts_appmgr_stage_chunk(uint32_t off, const uint8_t *data, uint32_t len,
			       uint32_t *high_water);
/** verify：TSAP 头 + COSE 验签（fail-closed 同 install）+ manifest 边界。
 * 出参为容器事实（供调用方与本地包对拍——「版本回读一致」确认语义）。 */
ts_res_t ts_appmgr_stage_verify(const uint8_t root_pubkey[32],
				uint32_t *manifest_len, uint32_t *wasm_len,
				uint32_t *cose_off);
ts_res_t ts_appmgr_stage_activate(ts_app_info_t *out);

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

/* ---- APP 运行时宿主（runtime.c + natives.c；DEC-43 接线批，M2b.2a）---------
 * LLD-ts-appmgr §4/§5：每 APP 一个框架线程（V1 单活跃 APP）；事件串行化
 * （DR-14 mailbox）；停止 = 停投递→join 2s→强杀回收；健康探针连续失败
 * 〔DEC-27：3〕→ health_fail（回滚状态机）。wasm 导入面 = ts_api_v1
 * （natives.c，防伪造 ctx 注入 + 调用期权限裁决〔合同 10 留痕〕）。 */

struct ts_app_rt_stats {
	uint32_t evt_seen;
	uint32_t tick_count;
	uint32_t health_fails;
	uint32_t mb_dropped;
	uint32_t init_res; /* app_init 返回值（0 = 成功） */
	int32_t last_evt;
	bool running;
	bool health_failed;
};

/** 启动 APP（wasm 字节 + 能力文法串；V1 字节由调用方提供——boot 从
 * slot 装载随下一单元接线）。返回 TS_E_PARAM = caps 非法或缺 health_ping
 * 导出；TS_E_STATE = 已有 APP 在跑。 */
ts_res_t ts_appmgr_app_start(uint16_t app_id, const uint8_t *wasm,
			     uint32_t wasm_len, const char *caps);

/** 停止并回收（DR-14 停止语义）。 */
ts_res_t ts_appmgr_app_stop(void);

/** 外部事件入 APP mailbox（满丢最旧 + 计数，DR-14）。 */
ts_res_t ts_appmgr_app_evt(uint32_t payload);

bool ts_appmgr_app_running(void);
void ts_appmgr_app_stats(struct ts_app_rt_stats *out);

/* ---- 测试钩子（CONFIG_TS_TEST）------------------------------------------- */
#ifdef CONFIG_TS_TEST
void ts_appmgr_test_reset(void);
void ts_appmgr_app_test_reset(void);
#endif

#ifdef __cplusplus
}
#endif

#endif /* TS_APPMGR_H__ */
