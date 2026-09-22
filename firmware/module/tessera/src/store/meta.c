/* SPDX-License-Identifier: Apache-2.0 */
/*
 * 掉电安全 meta kv（LLD-ts-store §3）：双副本 + 序号 + CRC16。
 * 撕裂恢复：活动 = 序号较大且 CRC 通过者；两副本皆损 → TS_E_IO（调用方按缺省
 * 安全态启动 / fail-safe）。写序：写非活动副本 → 校验回读 → 完成即成为新活动
 *（seq 单调递增，无独立指针——撕裂时旧副本仍完整可读）。
 */
#include <string.h>
#include <ts/store.h>
#include "internal.h"

/* META 分区布局：copy0 @0x000，copy1 @0x200（各 512B） */
#define COPY_STRIDE 0x200
#define REC_HDR     8 /* seq u32 | len u16 | crc16 u16（小端） */

static ts_res_t read_rec(uint8_t copy, uint32_t *seq, uint16_t *len, uint8_t *data)
{
	uint8_t hdr[REC_HDR];

	if (ts_store_backend.read(TS_PART_META, copy * COPY_STRIDE, hdr, REC_HDR) != TS_OK) {
		return TS_E_IO;
	}
	*seq = ts_get_le32(hdr);
	*len = ts_get_le16(hdr + 4);
	uint16_t crc = ts_get_le16(hdr + 6);

	if (*len == 0 || *len > CONFIG_TS_STORE_META_MAX) {
		return TS_E_IO;
	}
	if (ts_store_backend.read(TS_PART_META, copy * COPY_STRIDE + REC_HDR, data, *len) != TS_OK) {
		return TS_E_IO;
	}
	if (ts_crc16(data, *len) != crc) {
		return TS_E_IO;
	}
	return TS_OK;
}

static ts_res_t write_rec(uint8_t copy, uint32_t seq, const void *buf, uint16_t len)
{
	uint8_t rec[REC_HDR + CONFIG_TS_STORE_META_MAX];

	ts_put_le32(rec, seq);
	ts_put_le16(rec + 4, len);
	ts_put_le16(rec + 6, ts_crc16(buf, len));
	memcpy(rec + REC_HDR, buf, len);
	uint32_t total = REC_HDR + len;

	if (ts_store_backend.write(TS_PART_META, copy * COPY_STRIDE, rec, total) != TS_OK) {
		return TS_E_IO;
	}
	/* 校验回读 */
	uint8_t back[REC_HDR + CONFIG_TS_STORE_META_MAX];

	if (ts_store_backend.read(TS_PART_META, copy * COPY_STRIDE, back, total) != TS_OK ||
	    memcmp(rec, back, total) != 0) {
		return TS_E_IO;
	}
	return TS_OK;
}

ts_res_t ts_store_meta_write(const void *buf, uint16_t len)
{
	if (buf == NULL || len == 0 || len > CONFIG_TS_STORE_META_MAX) {
		return TS_E_PARAM;
	}
	uint8_t data[CONFIG_TS_STORE_META_MAX];
	uint32_t s0, s1;
	uint16_t l0, l1;

	bool ok0 = read_rec(0, &s0, &l0, data) == TS_OK;
	bool ok1 = read_rec(1, &s1, &l1, data) == TS_OK;

	uint32_t cur_seq = 0;
	uint8_t inactive = 0;

	if (ok0 && ok1) {
		cur_seq = (s0 >= s1) ? s0 : s1;
		inactive = (s0 >= s1) ? 1 : 0;
	} else if (ok0) {
		cur_seq = s0;
		inactive = 1;
	} else if (ok1) {
		cur_seq = s1;
		inactive = 0;
	}
	return write_rec(inactive, cur_seq + 1, buf, len);
}

ts_res_t ts_store_meta_read(void *buf, uint16_t *len)
{
	if (buf == NULL || len == NULL) {
		return TS_E_PARAM;
	}
	uint8_t data[CONFIG_TS_STORE_META_MAX];
	uint32_t s0, s1;
	uint16_t l0, l1;

	bool ok0 = read_rec(0, &s0, &l0, data) == TS_OK;
	bool ok1 = read_rec(1, &s1, &l1, data) == TS_OK;

	if (!ok0 && !ok1) {
		return TS_E_IO; /* 双副本皆损：调用方进 fail-safe/缺省安全态（LLD §3） */
	}
	if (ok0 && (!ok1 || s0 >= s1)) {
		memcpy(buf, data, l0);
		*len = l0;
	} else {
		memcpy(buf, data, l1);
		*len = l1;
	}
	return TS_OK;
}

#ifdef CONFIG_TS_TEST
ts_res_t ts_store_meta_corrupt_test(uint8_t copy_idx)
{
	if (copy_idx > 1) {
		return TS_E_PARAM;
	}
	uint8_t garbage[REC_HDR] = {0xDE, 0xAD, 0xBE, 0xEF, 0, 0, 0, 0};

	return ts_store_backend.write(TS_PART_META, copy_idx * COPY_STRIDE, garbage, REC_HDR);
}
#endif
