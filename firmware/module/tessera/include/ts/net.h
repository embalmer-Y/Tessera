/* SPDX-License-Identifier: Apache-2.0 */
/* ts-net 公共 API（design/LLD-ts-net.md）：zenoh-pico 会话 / 命名空间构造 /
 * 发布队列 / 心跳监视（断链判定源，合同 3）。
 * 传输缝纪律：zenoh 副作用全部收敛在 ts_net_transport_t 实现内（真实现 =
 * zenoh-pico〔CONFIG_TS_NET_ZENOH〕；测试/重放注入桩）——对齐 ts-store
 * backend 先例，保证 linkmon/pubq/session 逻辑确定性可测（合同 9）。 */
#ifndef TS_NET_H__
#define TS_NET_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <ts/err.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- 会话状态（LLD §2）--------------------------------------------------- */

typedef enum {
	TS_NET_DOWN,
	TS_NET_CONNECTED,
} ts_net_state_t;

/* ---- 传输缝 --------------------------------------------------------------- */

typedef struct ts_net_transport {
	ts_res_t (*open)(void); /* 建链（locator 自 prov 或测试注入） */
	void (*close)(void);
	/* 发布一行（DOWN 期不应被调用；失败由调用方按 pubq 语义丢弃计数） */
	ts_res_t (*publish)(const char *key, const uint8_t *payload, uint32_t len);
	bool (*is_up)(void);
} ts_net_transport_t;

/* ---- 命名空间构造（LLD §3；前缀 tessera/<node>/<cube>）-------------------- */

/* 前缀注入：session 初始化时取自 prov（V1 单立方体 node = cube，DEC-26）；
 * 测试可直接设置。id 为 NULL/空 → TS_E_PARAM；超长 → TS_E_PARAM。 */
ts_res_t ts_net_set_ids(const char *node_id, const char *cube_id);

/* 以下构造器返回 snprintf 语义（成功 = 写入字节数；n 不足 = 需要的字节数，
 * 不写越界；key 语法变更 = review 门 ③）。 */
int ts_net_key_cmd(char *buf, size_t n, const char *uid); /* …/<uid>/cmd      */
int ts_net_key_tel(char *buf, size_t n, const char *uid); /* …/<uid>/telemetry */
int ts_net_key_evt(char *buf, size_t n, const char *uid); /* …/<uid>/event    */
int ts_net_key_hb(char *buf, size_t n, bool host_dir);    /* …/sys/hb[-host]（DR-12） */
int ts_net_key_sys(char *buf, size_t n, const char *cmd); /* …/sys/<cmd>（DR-03） */

/* ---- 会话（LLD §2）------------------------------------------------------- */

ts_net_state_t ts_net_state(void);
void ts_net_set_transport(const ts_net_transport_t *t); /* NULL = 摘除 */
/* 退避表查值（DEC-27 固定表 250/500/1000/2000 循环；attempt 从 0 起，无随机） */
uint32_t ts_net_backoff_ms(uint32_t attempt);
/* 周期推进（sysworkq / 测试）：DOWN → 按退避表尝试 open；CONNECTED → 掉线
 * 检测 + 迁移；成功建链后冲刷 pubq。返回本 tick 后状态。 */
ts_net_state_t ts_net_session_poll(uint64_t now_ms);

/* ---- 发布队列（LLD §5：遥测尽力而为，不阻塞控制路径）---------------------- */

/* 入队（CONNECTED 时可直接发送）；DOWN 期 = 直接丢弃并计数（防上电风暴）；
 * 队满 = 丢最旧并计数。key/payload 超容量 → TS_E_PARAM。 */
ts_res_t ts_net_pubq_push(const char *key, const uint8_t *payload, uint32_t len);
uint32_t ts_net_pubq_dropped(void); /* 累计丢弃（含 DOWN 期丢与溢出丢） */
void ts_net_pubq_flush(void);       /* 经 transport 逐条发送（发送后清出） */

/* ---- 心跳监视（LLD §6，合同 3 判定源；合同 8 本地独立判定）---------------- */

/* 周期调用（sysworkq / 测试；now_ms 显式传入——虚拟时钟确定性）：
 * 发送 cube→host 心跳（transport 在位且 UP 时）+ host 心跳超时判定。 */
void ts_net_linkmon_tick(uint64_t now_ms);
/* host 心跳到达（订阅回调 / 测试注入）：更新时间戳与恢复连胜计数。 */
void ts_net_linkmon_hb_host(uint64_t now_ms);
bool ts_net_link_up(void); /* 当前判定（喂 ts_safety_set_link 的同一状态） */
uint32_t ts_net_linkmon_hb_seq(void); /* 已发心跳序号（payload 内容源） */

/* ---- 测试钩子（仅 CONFIG_TS_TEST）---------------------------------------- */
#ifdef CONFIG_TS_TEST
/* 全量复位（session/pubq/linkmon 状态 + 摘除传输注入）；不触碰 safety 注册表 */
void ts_net_test_reset(void);
#endif

#ifdef __cplusplus
}
#endif

#endif /* TS_NET_H__ */
