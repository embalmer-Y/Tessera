/* SPDX-License-Identifier: Apache-2.0 */
/*
 * prov 烧录通道测试注入（仅 CONFIG_TS_TEST 编译）——prov.c 本体保持零写调用
 * （L5 机械检查目标，LLD-ts-store §4）。生产烧录 = 外部工具 / Agent
 * deploy_push_prov（MA3）。
 */
#include <ts/store.h>
#include "internal.h"

#ifdef CONFIG_TS_TEST
ts_res_t ts_store_prov_write_test(const uint8_t *cbor, uint32_t len)
{
	if (cbor == NULL || len == 0 || len + 6 > 4096) {
		return TS_E_PARAM;
	}
	uint8_t hdr[6];

	ts_put_le32(hdr, len);
	ts_put_le16(hdr + 4, ts_crc16(cbor, len));
	if (ts_store_backend.erase(TS_PART_PROV) != TS_OK) {
		return TS_E_IO;
	}
	if (ts_store_backend.write(TS_PART_PROV, 0, hdr, sizeof(hdr)) != TS_OK) {
		return TS_E_IO;
	}
	if (ts_store_backend.write(TS_PART_PROV, sizeof(hdr), cbor, len) != TS_OK) {
		return TS_E_IO;
	}
	return TS_OK;
}
#endif
