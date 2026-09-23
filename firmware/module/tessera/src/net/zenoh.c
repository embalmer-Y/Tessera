/* SPDX-License-Identifier: Apache-2.0 */
/* zenoh-pico 传输实现（CONFIG_TS_NET_ZENOH；钉版 1.10.1，DR-22 三方同 minor）。
 * 副作用边界：z_* 调用全部收敛于本文件（传输缝纪律，LLD-ts-net §1）。
 * locator 来自 prov.router_locators[0]（DEC-20 client 角色）；缺省回退
 * tcp/127.0.0.1:7447（native_sim 基线，DEC-27；DEC-40 起缺省亦走 TCP）。
 * M3a.2：建链时接线 queryable（cube 前缀尾通配声明 + 回调内过滤 cmd 尾段
 * → ts_net_cmd_dispatch）与 hb-host 订阅（→ ts_net_linkmon_hb_host）。
 * DEC-40 批：locator 形态校验（命令面链路必须 TCP/TLS——UDP 拒绝）；is_up =
 * zp 任务活性自省（会话在而任务死 = 半死态，LLD §2）；publish 承接 QoS
 * 映射（DEC-42：安全事件 = BLOCK + REAL_TIME，缺省 = DROP + DATA）。 */
#include <stdio.h>
#include <string.h>
#include <zenoh-pico.h>
#include <ts/core.h>
#include <ts/net.h>
#include <ts/store.h>
#include "internal.h"

#define RESP_MAX 512 /* sys 命令回执预算（get-audit 最坏编码内） */

static z_owned_session_t zs;
static bool opened;
static z_owned_queryable_t zq;
static z_owned_subscriber_t zsub;

/* ---- 回调（zenoh 内部线程上下文；直落框架确定性分发）--------------------- */

static void drop_query(void *ctx)
{
	ARG_UNUSED(ctx);
}

static void on_query(const z_loaned_query_t *query, void *ctx)
{
	ARG_UNUSED(ctx);
	/* 两种命令面：…/<uid>/cmd（实例命令，M2b.2+）与 …/sys/<cmd>（sys 面，
	 * LLD-ts-net §3/§4）——按 key 形态剥前缀取分发后缀 */
	z_view_string_t vs;
	const z_loaned_keyexpr_t *qk = z_query_keyexpr(query);

	if (z_keyexpr_as_view_string(qk, &vs) != Z_OK) {
		return;
	}
	const char *k = z_string_data(z_loan(vs));
	size_t klen = z_string_len(z_loan(vs));
	size_t plen = strlen(ts_net_prefix);

	if (klen <= plen + 1 || strncmp(k, ts_net_prefix, plen) != 0) {
		return; /* 非 cube 命名空间：不回执（客户端侧超时可见） */
	}
	static char suffix[64];
	size_t slen;
	bool is_sys = (klen > plen + 5 && strncmp(k + plen, "/sys/", 5) == 0);

	if (is_sys) {
		slen = klen - (plen + 1); /* "sys/<cmd>" */
	} else if (klen > plen + 4 && strcmp(k + klen - 4, "/cmd") == 0) {
		slen = klen - 4 - (plen + 1); /* "<uid>" */
	} else {
		return;
	}
	if (slen == 0 || slen >= sizeof(suffix)) {
		return;
	}
	memcpy(suffix, k + plen + 1, slen);
	suffix[slen] = '\0';

	const z_loaned_bytes_t *pl = z_query_payload(query);
	z_bytes_reader_t rd = z_bytes_get_reader(pl);
	uint8_t req[128];
	size_t rlen = z_bytes_reader_read(&rd, req, sizeof(req));

	static uint8_t resp[RESP_MAX];
	size_t resp_len = 0;

	(void)ts_net_cmd_dispatch(suffix, req, (uint32_t)rlen, resp, sizeof(resp),
				  &resp_len);
	/* 回执（reply key = 查询 key 原样回显；编码失败 = 空回执可观测） */
	z_owned_bytes_t out;

	if (z_bytes_from_static_buf(&out, resp, resp_len) == Z_OK) {
		z_query_reply_options_t ro;

		z_query_reply_options_default(&ro);
		(void)z_query_reply(query, qk, z_move(out), &ro);
	}
}

static void on_sample(const z_loaned_sample_t *sample, void *ctx)
{
	ARG_UNUSED(ctx);
	/* 仅 hb-host 订阅在册；到达即视为 host 心跳（DR-12，合同 8 本地判定） */
	ts_net_linkmon_hb_host(ts_time_ms());
}

/* ---- 传输实现 ------------------------------------------------------------ */

/* 命令面链路约束（DEC-40）：TCP/TLS 前缀之外的 locator（如 udp/）拒绝建链
 * ——UDP 仅限 scouting/遥测可选路径；zenoh query 无重传，命令-回执链路的
 * 传输层可靠性由 TCP/TLS 承载。 */
static bool locator_cmd_face_ok(const char *loc)
{
	return strncmp(loc, "tcp/", 4) == 0 || strncmp(loc, "tls/", 4) == 0;
}

static ts_res_t zenoh_open(void)
{
	if (opened) {
		return TS_OK;
	}
	const ts_prov_t *prov = ts_store_prov();
	/* prov 未加载/未烧录时取默认（缺省亦 TCP——DEC-40 命令面链路约束） */
	const char *loc = (prov->router_locators[0][0] != '\0')
				  ? prov->router_locators[0]
				  : "tcp/127.0.0.1:7447";

	if (!locator_cmd_face_ok(loc)) {
		printk("[ts-net] zenoh_open: locator %s rejected (DEC-40: tcp//tls/ only)\n",
		       loc);
		return TS_E_PARAM;
	}

	z_owned_config_t cfg;

	if (z_config_default(&cfg) != Z_OK) {
		printk("[ts-net] zenoh_open: config_default FAIL\n");
		return TS_E_IO;
	}
	if (zp_config_insert(z_loan_mut(cfg), Z_CONFIG_CONNECT_KEY, loc) != Z_OK) {
		printk("[ts-net] zenoh_open: insert loc=%s FAIL\n", loc);
		z_drop(z_move(cfg));
		return TS_E_IO;
	}
	z_result_t or = z_open(&zs, z_move(cfg), NULL);

	if (or != Z_OK) {
		printk("[ts-net] zenoh_open: z_open rc=%d loc=%s\n", (int)or, loc);
		z_drop(z_move(zs)); /* 归零 owned 句柄，允许重试 open */
		return TS_E_IO;
	}
	opened = true;
	printk("[ts-net] zenoh_open: CONNECTED loc=%s\n", loc);

	/* queryable：cube 前缀下 ** 通配（** 只能作尾段——回调内过滤 "/cmd"） */
	z_owned_keyexpr_t qk;
	char qkey[80];
	int qw = snprintf(qkey, sizeof(qkey), "%s/**", ts_net_prefix);

	if (qw < 0 || (size_t)qw >= sizeof(qkey) ||
	    z_keyexpr_from_str(&qk, qkey) != Z_OK) {
		goto fail;
	}
	z_owned_closure_query_t qclos;

	z_closure_query(&qclos, on_query, drop_query, NULL);
	if (z_declare_queryable(z_loan(zs), &zq, z_loan(qk), z_move(qclos), NULL) != Z_OK) {
		z_drop(z_move(qk));
		goto fail;
	}
	z_drop(z_move(qk));

	/* 订阅 host 心跳 …/sys/hb-host（DR-12） */
	z_owned_keyexpr_t hk;
	char hkey[80];
	int hw = snprintf(hkey, sizeof(hkey), "%s/sys/hb-host", ts_net_prefix);

	if (hw < 0 || (size_t)hw >= sizeof(hkey) ||
	    z_keyexpr_from_str(&hk, hkey) != Z_OK) {
		goto fail;
	}
	z_owned_closure_sample_t sclos;

	z_closure_sample(&sclos, on_sample, NULL, NULL);
	if (z_declare_subscriber(z_loan(zs), &zsub, z_loan(hk), z_move(sclos), NULL) != Z_OK) {
		z_drop(z_move(hk));
		goto fail;
	}
	z_drop(z_move(hk));
	return TS_OK;
fail:
	z_drop(z_move(zs));
	opened = false;
	return TS_E_IO;
}

static void zenoh_close(void)
{
	if (opened) {
		z_undeclare_subscriber(z_move(zsub));
		z_undeclare_queryable(z_move(zq));
		z_drop(z_move(zs));
		opened = false;
	}
}

static ts_res_t zenoh_publish(const char *key, const uint8_t *payload, uint32_t len,
			      ts_net_qos_t qos)
{
	if (!opened) {
		return TS_E_STATE;
	}
	z_owned_keyexpr_t ke;

	if (z_keyexpr_from_str(&ke, key) != Z_OK) {
		return TS_E_PARAM;
	}
	z_owned_bytes_t pl;

	if (z_bytes_from_static_buf(&pl, payload, (size_t)len) != Z_OK) {
		z_drop(z_move(ke));
		return TS_E_IO;
	}
	z_put_options_t opt;

	z_put_options_default(&opt);
	if (qos == TS_NET_QOS_SAFETY) {
		/* DEC-42 QoS 映射：安全事件阻塞式（不丢）+ 高优先级 lane */
		opt.congestion_control = Z_CONGESTION_CONTROL_BLOCK;
		opt.priority = Z_PRIORITY_REAL_TIME;
	}
	z_result_t r = z_put(z_loan(zs), z_loan(ke), z_move(pl), &opt);

	z_drop(z_move(ke));
	return (r == Z_OK) ? TS_OK : TS_E_IO;
}

static bool zenoh_is_up(void)
{
	if (!opened) {
		return false;
	}
#if defined(Z_FEATURE_MULTI_THREAD) && Z_FEATURE_MULTI_THREAD == 1
	/* 传输健康定义（LLD §2 定稿）：会话在而读写/租期任务已死 = 半死态 →
	 * 判 DOWN（session_poll 走 close+重连）。上游自省接口（标注 deprecated
	 * 仅指任务不再需手动启动，活性探测语义仍有效）。 */
	return zp_read_task_is_running(z_loan(zs)) && zp_lease_task_is_running(z_loan(zs));
#else
	return true; /* 单线程构建退化：opened 即活（无后台任务可自省） */
#endif
}

const ts_net_transport_t ts_net_zenoh_transport = {
	.open = zenoh_open,
	.close = zenoh_close,
	.publish = zenoh_publish,
	.is_up = zenoh_is_up,
};
