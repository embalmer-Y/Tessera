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

/* V0.4.0 M6（Q-32②/DEC-53）：meta v2 = 每 entry（APP 实例位）一条记录。
 * entry e 的槽对 = {2e, 2e+1}（绝对槽号，^1 翻转 = 对内乒乓）；count ≤
 * TS_APP_MAX_INSTANCES。**v1 兼容**：旧 40B 单条布局（无 ver 字段）读侧
 * 自动迁移为 entries[0]（长度判别——v2 尺寸恒 > 40）。 */
#define TS_APPMGR_META_VER 2 /* 结构性版本号（Q-32②/DEC-53：meta v2 = entries 数组） */

typedef struct {
	uint8_t active_slot;      /* 绝对槽号（pair 基 = entry*2） */
	uint8_t rollback_count;   /* 超限 → QUARANTINED（per entry） */
	uint16_t boot_gen;
	uint32_t app_ver_u32;     /* semver → u32 比较 */
	uint8_t content_digest[32]; /* TSAP v2 头摘要（DEC-49②：boot 快校验对象） */
} ts_appmgr_entry_t;

typedef struct {
	uint8_t ver;              /* = TS_APPMGR_META_VER */
	uint8_t count;            /* 有效 entry 数 */
	ts_appmgr_entry_t entries[CONFIG_TS_APP_MAX_INSTANCES];
} ts_appmgr_meta_t;

ts_res_t ts_appmgr_meta_read(ts_appmgr_meta_t *meta);
ts_res_t ts_appmgr_meta_write(const ts_appmgr_meta_t *meta);
/** 缺省 meta（ver=2/count=1/entry0 槽 0）——恢复安装路径起点（slot.c）。 */
void ts_appmgr_meta_default(ts_appmgr_meta_t *meta);

/* ---- 多 entry 面（V0.4.0 M6，Q-32；legacy 单 API = entry 0 别名）---------- */

ts_res_t ts_appmgr_stage_begin_n(uint32_t total_len, uint8_t entry, uint8_t *slot_out);
ts_res_t ts_appmgr_stage_activate_n(uint8_t entry, ts_app_info_t *out);
ts_res_t ts_appmgr_get_info_n(uint8_t entry, ts_app_info_t *out);
ts_res_t ts_appmgr_rollback_n(uint8_t entry);

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
 * 导出；TS_E_STATE = 已有 APP 在跑。
 * V0.4.0 M7（Q-32③）：app_id = entry+1（1..N）——rt[app_id-1] 槽位。 */
ts_res_t ts_appmgr_app_start(uint16_t app_id, const uint8_t *wasm,
			     uint32_t wasm_len, const char *caps);

/** 停止并回收（DR-14 停止语义）——legacy = app_id 1。 */
ts_res_t ts_appmgr_app_stop(void);

/** 外部事件入 APP mailbox（满丢最旧 + 计数，DR-14）——legacy = app_id 1。 */
ts_res_t ts_appmgr_app_evt(uint32_t payload);

/** M7：按 id 停止/事件/运行态/统计（分账面）+ 事件广播（input monitor）。 */
ts_res_t ts_appmgr_app_stop_id(uint16_t app_id);
ts_res_t ts_appmgr_app_evt_id(uint16_t app_id, uint32_t payload);
void ts_appmgr_app_evt_bcast(uint32_t payload);
bool ts_appmgr_app_running_id(uint16_t app_id);
void ts_appmgr_app_stats_id(uint16_t app_id, struct ts_app_rt_stats *out);

/** M9（DR-15）：注入 manifest 串身份（boot 装载期；kv 哈希源）。 */
void ts_appmgr_app_set_idstr(uint16_t app_id, const char *idstr);

#ifdef CONFIG_TS_APP_THREADS
/** M19a（DEC-55/Q-37 A）：注入 manifest threads（boot 装载期；总并发含
 * 主，1-4）。threads<2 = spawn 拒绝（DEC-31 单线程语义收口）。 */
void ts_appmgr_app_set_threads(uint16_t app_id, uint8_t threads);
#endif

/** M7：健康失败按实例分账（rt 健康探针 → 对应 entry 回滚链）。 */
ts_res_t ts_appmgr_health_fail_id(uint16_t app_id);

bool ts_appmgr_app_running(void);
void ts_appmgr_app_stats(struct ts_app_rt_stats *out);

/** boot 装载（HLD §4.4-8；M2b.2 收尾单元）：读 active slot TSAP 容器 →
 * manifest 走查（caps 组合/app_id 提取；未知键 fail-closed）→ wasm 字节
 * → app_start。空 slot = TS_E_NOTFOUND；**APP 故障不阻塞启动**（boot
 * 步骤内部留痕吞掉非致命错误——合同 6 显式例外）。加载缓冲上限 =
 * CONFIG_TS_APP_LOAD_MAX；stack_kb/heap_kb V1 消耗运行时常量（已知限制）。 */
ts_res_t ts_appmgr_boot_start(void);

/* ---- 测试钩子（CONFIG_TS_TEST）------------------------------------------- */
#ifdef CONFIG_TS_TEST
void ts_appmgr_test_reset(void);
void ts_appmgr_app_test_reset(void);
#endif

#ifdef __cplusplus
}
#endif

#endif /* TS_APPMGR_H__ */
