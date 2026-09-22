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

#endif /* TS_NET_INTERNAL_H__ */
