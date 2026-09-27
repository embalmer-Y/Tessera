/* SPDX-License-Identifier: Apache-2.0 */
/* netbench（板级四单元）：WiFi + zenoh 命令往返时延——xiao_esp32s3 真机。
 * 流程：WiFi STA 连接（凭证经 cmake 变量注入，不入仓库）→ DHCP →
 * prov 烧入（TS_TEST 通道；定稿键序 CBOR，locator = NETBENCH_ROUTER）→
 * ts_core_boot()（含 net_init → zenoh-pico TCP 会话 + 心跳/命令面）。
 * 时延测量在 PC 侧客户端（netbench_client.py，L0/L1/L2 三层）。 */
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/net/dhcpv4.h>
#include <zephyr/net/net_event.h>
#include <zephyr/net/net_if.h>
#include <zephyr/net/net_mgmt.h>
#include <zephyr/net/wifi_mgmt.h>
#include <ts/core.h>
#include <ts/hal.h>
#include <ts/net.h>
#include <ts/safety.h>
#include <ts/store.h>

#ifndef NETBENCH_WIFI_SSID
#define NETBENCH_WIFI_SSID ""
#endif
#ifndef NETBENCH_WIFI_PASSWORD
#define NETBENCH_WIFI_PASSWORD ""
#endif
#ifndef NETBENCH_ROUTER
#define NETBENCH_ROUTER "tcp/192.168.2.90:7447"
#endif

static struct net_mgmt_event_callback ip_cb;
static struct net_mgmt_event_callback wifi_cb;
static struct k_sem ip_ready;

static void ip_handler(struct net_mgmt_event_callback *cb, uint64_t event,
		       struct net_if *iface)
{
	ARG_UNUSED(cb);
	if (event == NET_EVENT_IPV4_ADDR_ADD && net_if_is_up(iface)) {
		k_sem_give(&ip_ready);
	}
}

static void wifi_handler(struct net_mgmt_event_callback *cb, uint64_t event,
			 struct net_if *iface)
{
	ARG_UNUSED(cb);
	ARG_UNUSED(iface);
	if (event == NET_EVENT_WIFI_CONNECT_RESULT) {
		const struct wifi_status *st =
			(const struct wifi_status *)cb->info;

		printk("NBw connect_result status=%d\n", st ? (int)st->status : -1);
	} else if (event == NET_EVENT_WIFI_DISCONNECT_RESULT) {
		const struct wifi_status *st =
			(const struct wifi_status *)cb->info;

		printk("NBw disconnect reason=%d\n", st ? (int)st->status : -1);
	}
}

/* {"v":1,"node_id":"nbn","cube_id":"cbn","routers":[NETBENCH_ROUTER 字面]…
 * 定稿键序（prov.c 固定走查序；重生成脚本 ~/project/logs/gen_prov.py）。
 * 注：router 字面量为生成期固化的 tcp/192.168.2.90:7447——PC 侧 IP 变更
 * 时须重生成（含此注释如实登记）。 */
static const uint8_t prov_blob[] = {
	0xa9, 0x61, 0x76, 0x01, 0x67, 0x6e, 0x6f, 0x64, 0x65, 0x5f, 0x69, 0x64,
	0x63, 0x6e, 0x62, 0x6e, 0x67, 0x63, 0x75, 0x62, 0x65, 0x5f, 0x69, 0x64,
	0x63, 0x63, 0x62, 0x6e, 0x67, 0x72, 0x6f, 0x75, 0x74, 0x65, 0x72, 0x73,
	0x81, 0x75, 0x74, 0x63, 0x70, 0x2f, 0x31, 0x39, 0x32, 0x2e, 0x31, 0x36,
	0x38, 0x2e, 0x32, 0x2e, 0x39, 0x30, 0x3a, 0x39, 0x39, 0x35, 0x35, 0x63,
	0x70, 0x6b, 0x30, 0x58, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x63, 0x70, 0x6b, 0x31, 0x58, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x64, 0x63, 0x72, 0x65, 0x64, 0x60, 0x66, 0x70, 0x77,
	0x72, 0x5f, 0x6d, 0x61, 0x19, 0x01, 0xf4, 0x65, 0x65, 0x73, 0x74, 0x6f,
	0x70, 0x00,
};

static const ts_out_ch_t nb_led = {
	.uid = "nbled", .kind = TS_CH_GPIO,
	.poweron = {.b = false}, .linkloss = {.b = false}, .fault = {.b = false},
};
static const ts_hal_dev_desc_t nb_dev = {
	.uid = "nbled", .kind = TS_DEV_GPIO_OUT,
};

int main(void)
{
	printk("NB0 netbench start（zenoh locator 来自 prov blob，见下方 NB2 后日志）\n");

	struct net_if *iface = net_if_get_default();

	k_sem_init(&ip_ready, 0, 1);
	net_mgmt_init_event_callback(&ip_cb, ip_handler, NET_EVENT_IPV4_ADDR_ADD);
	net_mgmt_add_event_callback(&ip_cb);
	net_mgmt_init_event_callback(&wifi_cb, wifi_handler,
				     NET_EVENT_WIFI_CONNECT_RESULT |
				     NET_EVENT_WIFI_DISCONNECT_RESULT);
	net_mgmt_add_event_callback(&wifi_cb);

	static const uint8_t ssid[] = NETBENCH_WIFI_SSID;
	static const uint8_t psk[] = NETBENCH_WIFI_PASSWORD;
	struct wifi_connect_req_params cnx = {
		.ssid = ssid,
		.ssid_length = sizeof(ssid) - 1,
		.psk = psk,
		.psk_length = sizeof(psk) - 1,
		.security = WIFI_SECURITY_TYPE_PSK,
		.channel = WIFI_CHANNEL_ANY,
		.band = WIFI_FREQ_BAND_2_4_GHZ,
		.mfp = WIFI_MFP_OPTIONAL,
	};

	int rc = net_mgmt(NET_REQUEST_WIFI_CONNECT, iface, &cnx, sizeof(cnx));

	printk("NB0 wifi_connect rc=%d ssid=%s\n", rc, NETBENCH_WIFI_SSID);
	/* 关 WiFi 省电：默认 modem-sleep 对齐信标 → 命令往返尾部 ~DTIM(≈100ms)
	 * 量级（板级四实证：开 PS 时 L1 p50≈66ms/max≈105ms）。 */
	struct wifi_ps_params ps = {
		.enabled = WIFI_PS_DISABLED,
	};

	int ps_rc = net_mgmt(NET_REQUEST_WIFI_PS, iface, &ps, sizeof(ps));

	printk("NB0 ps_disable rc=%d\n", ps_rc);
	if (k_sem_take(&ip_ready, K_SECONDS(40)) != 0) {
		printk("NB FAIL dhcp timeout\n");
		return 1;
	}
	char buf[NET_IPV4_ADDR_LEN];

	for (int i = 0; i < NET_IF_MAX_IPV4_ADDR; i++) {
		struct net_if_addr *a = &iface->config.ip.ipv4->unicast[i].ipv4;

		if (a->is_used) {
			net_addr_ntop(AF_INET, &a->address.in_addr, buf, sizeof(buf));
			printk("NB1 wifi up ip=%s\n", buf);
		}
	}

	/* prov：RAM 后端每次启动烧入（真板持久化 = 板级后续任务） */
	ts_res_t lr = ts_store_prov_load();
	ts_res_t wr = (lr == TS_OK)
		? TS_OK
		: ts_store_prov_write_test(prov_blob, sizeof(prov_blob));

	printk("NB2 prov load=%d burn=%d\n", (int)lr, (int)wr);
	if (wr != TS_OK) {
		printk("NB FAIL prov\n");
		return 1;
	}
	(void)ts_safety_register_channel(&nb_led);
	(void)ts_hal_register_dev(&nb_dev);
	ts_core_boot(); /* noreturn：表尾 net_init → zenoh + 周期驱动 */
	return 0;
}
