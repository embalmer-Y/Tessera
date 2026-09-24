/* SPDX-License-Identifier: Apache-2.0 */
/*
 * ts-safety 公共 API（design/LLD-ts-safety.md）：输出保护层 / 三安全态 / estop / fail-safe。
 * 合同关联：合同 1（三安全态）、2（唯一写路径）、5（estop 不经队列）、7（供电同轨）、8（本地独立）。
 */
#ifndef TS_SAFETY_H__
#define TS_SAFETY_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <ts/core.h> /* safety→core 向下依赖（LLD-00 §1）：事件发布/时间源 */
#include <ts/err.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- 通道模型（LLD-ts-safety §2）---------------------------------------- */

typedef enum {
	TS_CH_GPIO,
	TS_CH_PWM,
	TS_CH_POWER,
	TS_CH_KIND_COUNT,
} ts_ch_kind_t;

typedef union {
	bool b;                            /* TS_CH_GPIO */
	uint32_t u;                        /* TS_CH_PWM */
	struct {
		bool en;
		uint32_t ma;
	} pwr;                             /* TS_CH_POWER（受控供电，DEC-03，合同7） */
} ts_out_value_t;

typedef struct {
	const char *uid;    /* 稳定逻辑名（ts-periph 分配，M3 交付） */
	ts_ch_kind_t kind;
	ts_out_value_t poweron; /* 三安全态：合同1，缺一拒绝注册 */
	ts_out_value_t linkloss;
	ts_out_value_t fault;
	struct {
		uint32_t min, max;         /* 限幅（TS_CH_GPIO 时忽略） */
		uint32_t slew_per_ms;      /* 变化率上界（0 = 不限） */
		uint32_t current_limit_ma; /* 供电限流（TS_CH_POWER） */
	} limits;
} ts_out_ch_t;

/* 三安全态状态机（LLD-ts-safety §3） */
typedef enum {
	TS_ST_SAFE_POWERON,
	TS_ST_ACTIVE,
	TS_ST_SAFE_LINKLOSS,
	TS_ST_SAFE_FAULT,
	TS_CH_STATE_COUNT,
} ts_ch_state_t;

/** [thread] init 期 + 外设注册期；三态缺一/越限/uid 撞名 → TS_E_PARAM（注册即失败，
 * 不留半注册）。容量 CONFIG_TS_SAFETY_MAX_CHANNELS（DEC-27: 32）。 */
ts_res_t ts_safety_register_channel(const ts_out_ch_t *ch);

/* ---- 唯一写路径（LLD-ts-safety §4）——合同 2 强制点 ----------------------- */

/** [thread] 一切输出必经的保护校验出口（限幅→slew→限流→末段临界区→审计）。
 * 非 ACTIVE 态 → TS_E_STATE；限流拒绝 → TS_E_RANGE；slew 拆分后返回实际落值。 */
ts_res_t ts_safety_commit(const char *uid, ts_out_value_t v);

/** [any] 影子值读回（不经驱动）。 */
ts_res_t ts_safety_readback(const char *uid, ts_out_value_t *out);

/** [any] 通道当前安全态（观测点：重放比对/遥测）。 */
ts_res_t ts_safety_channel_state(const char *uid, ts_ch_state_t *out);

/** ts_out_value_t 的规范单字编码（审计/遥测统一口径；b→0/1，
 * pwr→en<<31|ma&0x7FFFFFFF，其余取 .u）。 */
static inline uint32_t ts_value_encode(ts_ch_kind_t k, ts_out_value_t v)
{
	switch (k) {
	case TS_CH_GPIO:
		return v.b ? 1U : 0U;
	case TS_CH_POWER:
		return (v.pwr.en ? 1U << 31 : 0U) | (v.pwr.ma & 0x7FFFFFFFU);
	default:
		return v.u;
	}
}

/** 汇总观测（sys 命令 get-safety / 遥测，M3a.2）：按态计数 + 注册总数。 */
typedef struct {
	uint16_t by_state[TS_CH_STATE_COUNT];
	uint16_t channels;
} ts_safety_summary_t;

/** [thread] 汇总快照（注册表遍历，无锁读——观测面容忍微撕裂）。 */
ts_res_t ts_safety_summary(ts_safety_summary_t *out);

/* ---- estop 与 fail-safe 直达（LLD-ts-safety §5）——合同 5/8 --------------- */

/** [ISR] estop GPIO 回调直接调用：原子置 forced → 逐通道直写 fault 值。
 * 调用图内禁分配/队列/锁/协议栈（L5 机械检查目标）。 */
void ts_safety_force_all_fault(void);

/** [thread] WDT/BOOT/子系统故障：全通道进 SAFE_FAULT 并停机编排。 */
void ts_safety_system_fail(uint32_t reason);

/** [thread] ts-net 专用链路判定（经 sysworkq 串行化迁移；带滞回，M3 细化）。 */
void ts_safety_set_link(bool up);

/* ---- 单通道故障/恢复（M3b，LLD-ts-periph §3 DETACH 语义的机制面）---------
 * 物理不在场 = 故障态：detach 强制单通道 fault（不置全局 estop 锁存）；
 * attach 恢复 = 上电态重放（全局 forced 锁存期拒绝恢复）。 */
ts_res_t ts_safety_force_channel_fault(const char *uid);
ts_res_t ts_safety_channel_recover(const char *uid);

#ifdef CONFIG_TS_TEST
/* 通道表/锁存/链路全清（测试隔离——模块级 test_reset 级联的显式起点；
 * 生产不可达）。 */
void ts_safety_test_reset(void);
#endif

/** [thread] 仅 sys:estop-clear 命令可达（host-only + 确认令牌，DEC-30①）。
 * M1：直调仅供测试；M3 起 net 命令面为唯一运行期入口。forced 标志不复位前拒绝。 */
ts_res_t ts_safety_clear_fault(void);

/** [thread] estop 事后补发（sysworkq 周期检测 forced 上升沿 → 发布 TS_EVT_ESTOP；
 * ISR 内不提交工作项——estop 调用图队列禁令的落点，LLD §5）。 */
void ts_safety_estop_deferred_publish(void);

/* ---- 审计环形（LLD-ts-safety §4-7，DR-07/DEC-30②④）---------------------- */

typedef struct {
	uint64_t t_ms;
	uint16_t ch_idx;   /* 注册表下标；0xFFFF = 全通道事件 */
	int32_t res;       /* commit 结果（TS_OK 或 TS_E_*） */
	uint16_t actor;    /* 调用者 app_id（M1 恒 0=system；M2 起 ts-hal 注入） */
	uint8_t kind;      /* ts_ch_kind_t（值语义按 kind 解释，原始 union 存 value） */
	uint8_t _rsv;
	uint32_t value_u;  /* ts_out_value_t 的规范单字表示（b→0/1；pwr→en<<31|ma 截低 31 位） */
} ts_audit_entry_t;

/** [thread] 拷贝审计快照（从最新往回 max 条），返回实际拷贝数；溢出丢弃计数另查。 */
size_t ts_safety_audit_copy(ts_audit_entry_t *out, size_t max);

/** [any] 审计溢出累计丢弃条数（观测，不清零）。 */
uint32_t ts_safety_audit_dropped(void);

/* ---- boot 步骤实现（LLD-ts-core §2 由本模块承接的两步）------------------- */

/** [thread] estop DT 绑定（DR-11）：chosen ts,estop-gpio → 配置 IRQ；
 * 无节点板（native_sim/测试）= 空操作返回 TS_OK（生产板必须提供，板级断言 M2+）。 */
ts_res_t ts_safety_estop_init(void);

/** [thread] 全通道置 SAFE_POWERON 初态（boot 步骤 2）。 */
ts_res_t ts_safety_poweron_init(void);

/* ---- 事件 payload（本模块发布的事件）------------------------------------- */

typedef struct {
	const char *uid;
	ts_ch_state_t new_state;
} ts_safe_state_evt_t; /* TS_EVT_SAFE_STATE_CHANGED（LLD §3：uid + 新态） */

typedef struct {
	uint32_t t_ms; /* estop 触发时刻（ISR 记录，补发时带上，合同 5） */
} ts_estop_evt_t; /* TS_EVT_ESTOP */

/* ---- 测试钩子（仅 CONFIG_TS_TEST）---------------------------------------- */
#ifdef CONFIG_TS_TEST
/** 最近一次 system_fail 的 reason（测试断言用；0 = 未发生）。 */
uint32_t ts_safety_test_fail_reason(void);
#endif

/* ---- 驱动分发（LLD-ts-safety §6）——全库唯一驱动调用点 -------------------- */

typedef struct {
	void (*write)(const ts_out_ch_t *ch, const ts_out_value_t *v);
	int (*read)(const ts_out_ch_t *ch, ts_out_value_t *out);
} ts_driver_ops_t;

extern const ts_driver_ops_t ts_drivers[TS_CH_KIND_COUNT];

/* native_sim 桩驱动的写序列记录（L4 重放 golden 数据源；真机驱动无记录）。 */
typedef struct {
	uint64_t t_ms;
	uint32_t value_u; /* 编码同 ts_audit_entry_t.value_u */
} ts_write_rec_t;

/** [thread] 拷贝指定通道的写序列快照（从旧到新），返回实际条数（环形容量 32/通道）。 */
size_t ts_driversim_writes(const char *uid, ts_write_rec_t *out, size_t max);

#ifdef __cplusplus
}
#endif

#endif /* TS_SAFETY_H__ */
