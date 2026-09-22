/* SPDX-License-Identifier: Apache-2.0 */
/* ts-safety 内部共享（不对外）：通道槽表/forced/link 原子与编码辅助。 */
#ifndef TS_SAFETY_INTERNAL_H__
#define TS_SAFETY_INTERNAL_H__

#include <string.h>
#include <ts/safety.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>

/* 每通道写序列环形容量（native_sim 桩，L4 golden 数据源）。来源: 结构性数值 */
#define TS_SIM_REC_PER_CH 32

struct ts_ch_slot {
	const ts_out_ch_t *desc;
	ts_ch_state_t state;
	ts_out_value_t shadow;   /* 影子值：SAFE_* 态 = 安全值；ACTIVE = 最后落值 */
	bool have_last;          /* slew 基线是否已建立 */
	uint64_t last_t;         /* 上次 commit 时刻（slew Δt） */
	struct {
		uint32_t head, count;
		ts_write_rec_t ring[TS_SIM_REC_PER_CH];
	} sim_rec;               /* native_sim 桩驱动记录 */
};

extern struct ts_ch_slot ts_ch_table[CONFIG_TS_SAFETY_MAX_CHANNELS];
extern size_t ts_ch_count;

extern atomic_t ts_forced;      /* estop/fail 锁存标志（clear 前不复位，LLD §5） */
extern atomic_t ts_forced_at;   /* forced 置位时刻（低 32 位，estop 补发事件用） */
extern atomic_t ts_link_up;     /* 全局链路标志（LLD §3） */

/* ts_out_value_t 的规范单字编码（审计/记录统一用；b→0/1，pwr→en<<31|ma&0x7FFFFFFF） */
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

/* 查找槽下标；未注册返回 -1 */
static inline int ts_ch_find(const char *uid)
{
	if (uid == NULL) {
		return -1;
	}
	for (size_t i = 0; i < ts_ch_count; i++) {
		if (ts_ch_table[i].desc != NULL && ts_ch_table[i].desc->uid != NULL &&
		    strcmp(ts_ch_table[i].desc->uid, uid) == 0) {
			return (int)i;
		}
	}
	return -1;
}

#endif /* TS_SAFETY_INTERNAL_H__ */
