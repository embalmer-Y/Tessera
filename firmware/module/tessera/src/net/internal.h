/* SPDX-License-Identifier: Apache-2.0 */
/* ts-net 内部共享（不对外）。 */
#ifndef TS_NET_INTERNAL_H__
#define TS_NET_INTERNAL_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <ts/net.h>

/* keyspace.c 定义，session.c/linkmon.c/pubq.c 共享 */
extern char ts_net_prefix[48]; /* "tessera/<node>/<cube>"，构造期一次成型 */

/* session.c 定义：当前传输（NULL = 未注入） */
extern const ts_net_transport_t *ts_net_transport;

/* cmd.c：sys 命令表注册（init 期一次；host_only——DEC-30①） */
void ts_net_cmd_sys_init(void);
#ifdef CONFIG_TS_TEST
void ts_net_cmd_test_reset(void); /* 表清空（测试隔离） */
#endif

/* ---- cbor_min：确定性子集编解码（cmd 请求/回执 + pub payload）-------------
 * 只支持 definite map/tstr/uint/negint/bool/array；任何超集 = 解码失败。
 * 编码为 canonical 序（由调用方按固定键序写入）。 */

typedef struct {
	const uint8_t *p;
	size_t rem;
} ts_cbor_rd_t;

void ts_cbor_rd_init(ts_cbor_rd_t *r, const uint8_t *buf, size_t len);
/* 逐项读取：失败返回 false（整个请求即非法，fail-closed） */
bool ts_cbor_map_open(ts_cbor_rd_t *r, uint32_t *pairs);
bool ts_cbor_array_open(ts_cbor_rd_t *r, uint32_t *items);
bool ts_cbor_tstr(ts_cbor_rd_t *r, char *out, size_t cap);
bool ts_cbor_uint(ts_cbor_rd_t *r, uint64_t *out);
bool ts_cbor_int(ts_cbor_rd_t *r, int64_t *out);
bool ts_cbor_bool(ts_cbor_rd_t *r, bool *out);

/* 编码器：buf 追加写（*pos 前进）；溢出由调用方检查（resp 定容） */
bool ts_cbor_put_map(uint8_t *buf, size_t cap, size_t *pos, uint32_t pairs);
bool ts_cbor_put_array(uint8_t *buf, size_t cap, size_t *pos, uint32_t items);
bool ts_cbor_put_tstr(uint8_t *buf, size_t cap, size_t *pos, const char *s);
bool ts_cbor_put_tstrn(uint8_t *buf, size_t cap, size_t *pos, const char *s, size_t n);
bool ts_cbor_put_uint(uint8_t *buf, size_t cap, size_t *pos, uint64_t v);
bool ts_cbor_put_int(uint8_t *buf, size_t cap, size_t *pos, int64_t v);
bool ts_cbor_put_bool(uint8_t *buf, size_t cap, size_t *pos, bool v);

#endif /* TS_NET_INTERNAL_H__ */
