/* SPDX-License-Identifier: Apache-2.0 */
/*
 * provisioning 只读访问（LLD-ts-store §4，DEC-30⑤ CBOR schema v1）。
 * 合同 10 强制点：**本文件零写调用**（L5 机械检查目标）；写通道仅烧录期
 *（prov_test.c 测试注入 / 外部工具 / Agent deploy_push_prov，MA3）。
 *
 * PROV 分区布局（小端）：u32 cbor_len | u16 crc16(cbor) | cbor[]
 * CBOR schema v1（定稿 2026-09-22，键序固定）：
 *   map{"v":1, "node_id":tstr, "cube_id":tstr, "routers":[tstr×≤4],
 *        "pk0":bstr(32), "pk1":bstr(32), "cred":tstr,
 *        "pwr_ma":uint, "estop":uint}
 * 解码器为该固定 schema 的**确定性子集实现**（definite-length map/text/bytes/
 * uint；任何超集/不定长 = TS_E_IO）——不引入通用 CBOR 依赖（真机足迹纪律）。
 */
#include <string.h>
#include <ts/store.h>
#include "internal.h"

static ts_prov_t prov;

/* ---- 定长 schema 解码（buf 内指针推进） --------------------------------- */

typedef struct {
	const uint8_t *p;
	uint32_t rem;
} rd_t;

static bool rd_u8(rd_t *r, uint8_t *out)
{
	if (r->rem < 1) {
		return false;
	}
	*out = *r->p++;
	r->rem--;
	return true;
}

static bool rd_len(rd_t *r, uint8_t info, uint32_t *out)
{
	if (info < 0x18) {
		*out = info;
		return true;
	}
	uint32_t n = 0;
	int bytes = (info == 0x18) ? 1 : (info == 0x19) ? 2 : (info == 0x1A) ? 4 : -1;

	if (bytes < 0 || r->rem < (uint32_t)bytes) {
		return false;
	}
	for (int i = 0; i < bytes; i++) {
		n = (n << 8) | *r->p++;
	}
	r->rem -= bytes;
	*out = n;
	return true;
}

static bool rd_tstr(rd_t *r, char *out, size_t cap)
{
	uint8_t ib;

	if (!rd_u8(r, &ib) || (uint8_t)(ib & 0xE0) != 0x60) {
		return false;
	}
	uint32_t len;

	if (!rd_len(r, ib & 0x1F, &len) || len >= cap || r->rem < len) {
		return false;
	}
	memcpy(out, r->p, len);
	out[len] = '\0';
	r->p += len;
	r->rem -= len;
	return true;
}

static bool rd_bstr(rd_t *r, uint8_t *out, size_t cap)
{
	uint8_t ib;

	if (!rd_u8(r, &ib) || (uint8_t)(ib & 0xE0) != 0x40) {
		return false;
	}
	uint32_t len;

	if (!rd_len(r, ib & 0x1F, &len) || len != cap || r->rem < len) {
		return false;
	}
	memcpy(out, r->p, len);
	r->p += len;
	r->rem -= len;
	return true;
}

static bool rd_uint(rd_t *r, uint32_t *out)
{
	uint8_t ib;

	if (!rd_u8(r, &ib) || (ib & 0xE0) != 0x00) {
		return false;
	}
	uint32_t v;

	if (!rd_len(r, ib & 0x1F, &v)) {
		return false;
	}
	*out = v;
	return true;
}

/* ---- 分区读取 + 校验 ------------------------------------------------------ */

ts_res_t ts_store_prov_load(void)
{
	uint8_t hdr[6];

	if (ts_store_backend.read(TS_PART_PROV, 0, hdr, sizeof(hdr)) != TS_OK) {
		return TS_E_IO;
	}
	uint32_t cbor_len = ts_get_le32(hdr);
	uint16_t crc = ts_get_le16(hdr + 4);

	if (cbor_len == 0 || cbor_len > 3800) { /* PROV 分区 4KiB 内合理上限（结构性） */
		return TS_E_IO;
	}
	static uint8_t cbor[3800];

	if (ts_store_backend.read(TS_PART_PROV, sizeof(hdr), cbor, cbor_len) != TS_OK) {
		return TS_E_IO;
	}
	if (ts_crc16(cbor, cbor_len) != crc) {
		return TS_E_IO; /* CRC 失败 → 调用方 fail-safe（合同 6） */
	}

	rd_t r = {.p = cbor, .rem = cbor_len};
	uint8_t ib;

	if (!rd_u8(&r, &ib) || (uint8_t)(ib & 0xE0) != 0xA0) {
		return TS_E_IO;
	}
	uint32_t pairs;

	if (!rd_len(&r, ib & 0x1F, &pairs) || pairs != 9) {
		return TS_E_IO;
	}

	char key[16];
	uint32_t u;

	/* 键序固定（定稿 schema）；逐键消费 */
	static const char *const keys[9] = {
		"v", "node_id", "cube_id", "routers", "pk0", "pk1", "cred", "pwr_ma", "estop",
	};

	for (uint32_t k = 0; k < pairs; k++) {
		if (!rd_tstr(&r, key, sizeof(key)) || strcmp(key, keys[k]) != 0) {
			return TS_E_IO;
		}
		switch (k) {
		case 0: /* v */
			if (!rd_uint(&r, &u) || u != 1) {
				return TS_E_IO;
			}
			break;
		case 1:
			if (!rd_tstr(&r, prov.node_id, sizeof(prov.node_id))) {
				return TS_E_IO;
			}
			break;
		case 2:
			if (!rd_tstr(&r, prov.cube_id, sizeof(prov.cube_id))) {
				return TS_E_IO;
			}
			break;
		case 3: { /* routers: definite array of tstr ≤4 */
			uint8_t ab;

			if (!rd_u8(&r, &ab) || (uint8_t)(ab & 0xE0) != 0x80) {
				return TS_E_IO;
			}
			uint32_t n;

			if (!rd_len(&r, ab & 0x1F, &n) || n > 4) {
				return TS_E_IO;
			}
			for (uint32_t i = 0; i < n; i++) {
				if (!rd_tstr(&r, prov.router_locators[i],
					     sizeof(prov.router_locators[i]))) {
					return TS_E_IO;
				}
			}
			for (uint32_t i = n; i < 4; i++) {
				prov.router_locators[i][0] = '\0';
			}
			break;
		}
		case 4:
			if (!rd_bstr(&r, prov.root_pubkeys[0], 32)) {
				return TS_E_IO;
			}
			break;
		case 5:
			if (!rd_bstr(&r, prov.root_pubkeys[1], 32)) {
				return TS_E_IO;
			}
			break;
		case 6:
			if (!rd_tstr(&r, prov.zenoh_cred, sizeof(prov.zenoh_cred))) {
				return TS_E_IO;
			}
			break;
		case 7:
			if (!rd_uint(&r, &prov.power_budget_ma)) {
				return TS_E_IO;
			}
			break;
		default:
			if (!rd_uint(&r, &u) || u > 0xFFU) {
				return TS_E_IO; /* estop 标志域 u8（防静默截断，IR-10） */
			}
			prov.estop_trigger_flags = (uint8_t)u;
			break;
		}
	}
	return TS_OK;
}

const ts_prov_t *ts_store_prov(void)
{
	return &prov;
}
