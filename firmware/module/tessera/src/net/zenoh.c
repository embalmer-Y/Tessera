/* SPDX-License-Identifier: Apache-2.0 */
/* zenoh-pico 传输实现（CONFIG_TS_NET_ZENOH；钉版 1.10.1，DR-22 三方同 minor）。
 * 副作用边界：z_* 调用全部收敛于本文件（传输缝纪律，LLD-ts-net §1）。
 * locator 来自 prov.router_locators[0]（DEC-20 client 角色）；缺省回退
 * udp/127.0.0.1:7447（native_sim 基线，DEC-27）。 */
#include <string.h>
#include <zenoh-pico.h>
#include <ts/net.h>
#include <ts/store.h>
#include "internal.h"

static z_owned_session_t zs;
static bool opened;

static ts_res_t zenoh_open(void)
{
	if (opened) {
		return TS_OK;
	}
	const ts_prov_t *prov = ts_store_prov();
	/* prov 未加载/未烧录时取默认（集成联调 M3a.2 接 boot 编排后收紧） */
	const char *loc = (prov->router_locators[0][0] != '\0')
				  ? prov->router_locators[0]
				  : "udp/127.0.0.1:7447";

	z_owned_config_t cfg;

	if (z_config_default(&cfg) != Z_OK) {
		return TS_E_IO;
	}
	if (zp_config_insert(z_loan_mut(cfg), Z_CONFIG_CONNECT_KEY, loc) != Z_OK) {
		z_drop(z_move(cfg));
		return TS_E_IO;
	}
	if (z_open(&zs, z_move(cfg), NULL) != Z_OK) {
		z_drop(z_move(zs)); /* 归零 owned 句柄，允许重试 open */
		return TS_E_IO;
	}
	opened = true;
	return TS_OK;
}

static void zenoh_close(void)
{
	if (opened) {
		z_drop(z_move(zs));
		opened = false;
	}
}

static ts_res_t zenoh_publish(const char *key, const uint8_t *payload, uint32_t len)
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
	z_result_t r = z_put(z_loan(zs), z_loan(ke), z_move(pl), NULL);

	z_drop(z_move(ke));
	return (r == Z_OK) ? TS_OK : TS_E_IO;
}

static bool zenoh_is_up(void)
{
	/* V1：会话存活位（读写失败驱动的细粒度检测随 M3a.2 keepalive 接入） */
	return opened;
}

const ts_net_transport_t ts_net_zenoh_transport = {
	.open = zenoh_open,
	.close = zenoh_close,
	.publish = zenoh_publish,
	.is_up = zenoh_is_up,
};
