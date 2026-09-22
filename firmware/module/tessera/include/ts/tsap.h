/* SPDX-License-Identifier: Apache-2.0 */
/*
 * TSAP v1 容器格式（DEC-21；LLD-ts-appmgr §2）——**M2a 定稿**。
 * 头 16 字节，字段序 = LLD 原序 + 尾部 reserved u16：
 *   magic "TSAP"(4) | fmt_ver u16 | manifest_len u32 | wasm_len u32 | rsv u16
 * 之后：manifest(CBOR) ‖ wasm ‖ COSE_Sign1(ed25519，覆盖 manifest‖wasm)。
 * **多字节整数一律大端**（网络序，与 CBOR/COSE 生态一致；内部存储分区则为小端，
 * 两者互不相关——见 LLD-ts-store §2）。
 * 验签（COSE）与 slot 安装为 ts-appmgr M2b 职责；本头只做格式与边界自洽校验。
 */
#ifndef TS_TSAP_H__
#define TS_TSAP_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TSAP_MAGIC       0x54534150U /* 字节序：'T','S','A','P'（大端读取） */
#define TSAP_FMT_VER     1U
#define TSAP_HEADER_SIZE 16U

typedef struct {
	uint16_t fmt_ver;
	uint32_t manifest_len;
	uint32_t wasm_len;
	uint32_t manifest_off; /* = TSAP_HEADER_SIZE */
	uint32_t wasm_off;     /* = header + manifest_len */
	uint32_t cose_off;     /* = wasm_off + wasm_len */
} tsap_view_t;

static inline uint32_t tsap_be32(const uint8_t *p)
{
	return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | p[3];
}

static inline uint16_t tsap_be16(const uint8_t *p)
{
	return (uint16_t)((uint16_t)p[0] << 8 | p[1]);
}

/*
 * 解析并自洽校验容器头：magic/版本/长度不越界。
 * 返回 true 且填充 view；COSE_Sign1 至少占 1 字节（真实下限随 M2b 验签细化）。
 */
static inline bool tsap_header_parse(const uint8_t *buf, size_t len, tsap_view_t *v)
{
	if (buf == NULL || v == NULL || len < TSAP_HEADER_SIZE) {
		return false;
	}
	if (tsap_be32(buf) != TSAP_MAGIC) {
		return false;
	}
	uint16_t ver = tsap_be16(buf + 4);

	if (ver != TSAP_FMT_VER) {
		return false;
	}
	v->fmt_ver = ver;
	v->manifest_len = tsap_be32(buf + 6);
	v->wasm_len = tsap_be32(buf + 10);
	v->manifest_off = TSAP_HEADER_SIZE;
	v->wasm_off = TSAP_HEADER_SIZE + v->manifest_len;
	v->cose_off = v->wasm_off + v->wasm_len;
	/* 溢出与越界防御（长度和必须装进 u64 且留 COSE 空间）。
	 * cose_off+1 必须在 u64 域比较：u32 域在 cose_off==UINT32_MAX 时回绕为 0，
	 * 会使越界检查失效（impl-review IR-06）。 */
	uint64_t total = (uint64_t)TSAP_HEADER_SIZE + v->manifest_len + v->wasm_len;

	if (total > (uint64_t)UINT32_MAX || total + 1 > (uint64_t)len) {
		return false;
	}
	return true;
}

#ifdef __cplusplus
}
#endif

#endif /* TS_TSAP_H__ */
