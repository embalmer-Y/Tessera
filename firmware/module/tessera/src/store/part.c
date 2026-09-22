/* SPDX-License-Identifier: Apache-2.0 */
/*
 * 分区表与后端抽象（LLD-ts-store §2）。
 * 后端实现（M2a 收敛留痕）：
 *  - **RAM 后端**（本文件，native_sim/测试默认）：静态数组 + 0xFF 抹除语义，
 *    ts_store_test_reset() 模拟"掉电后全新镜像"；跨进程持久化非 M2a 测试所需
 *    （LLD 原文"宿主文件"形态的跨进程持久化留待真实掉电场景引入，届时一并
 *    接真机 flash 后端）。
 *  - 真机 flash 后端：板级移植阶段实现（slots 换 flash_map/flash 驱动页）。
 */
#include <string.h>
#include <zephyr/kernel.h>
#include <ts/store.h>
#include "internal.h"

/* 分区尺寸（来源: DEC-23 语义——尺寸按板可配；基线 = 结构性数值） */
#define PROV_SIZE   4096U
#define META_SIZE   1024U /* 双副本各 512B */
#define NOINIT_SIZE 256U

static uint8_t ram_prov[PROV_SIZE];
static uint8_t ram_meta[META_SIZE];
static uint8_t ram_slot_a[CONFIG_TS_STORE_SLOT_SIZE];
static uint8_t ram_slot_b[CONFIG_TS_STORE_SLOT_SIZE];
static uint8_t ram_noinit[NOINIT_SIZE];

static uint8_t *part_ram(ts_store_part_t part, uint32_t *size)
{
	switch (part) {
	case TS_PART_PROV:
		*size = PROV_SIZE;
		return ram_prov;
	case TS_PART_META:
		*size = META_SIZE;
		return ram_meta;
	case TS_PART_SLOT_A:
		*size = CONFIG_TS_STORE_SLOT_SIZE;
		return ram_slot_a;
	case TS_PART_SLOT_B:
		*size = CONFIG_TS_STORE_SLOT_SIZE;
		return ram_slot_b;
	case TS_PART_NOINIT:
		*size = NOINIT_SIZE;
		return ram_noinit;
	default:
		*size = 0;
		return NULL;
	}
}

static ts_res_t ram_read(ts_store_part_t part, uint32_t off, void *buf, uint32_t len)
{
	uint32_t size;
	uint8_t *base = part_ram(part, &size);

	/* 溢出安全边界（IR-07）：off+len 在 u32 域可能回绕 */
	if (base == NULL || off > size || len > size - off) {
		return TS_E_RANGE;
	}
	memcpy(buf, base + off, len);
	return TS_OK;
}

static ts_res_t ram_write(ts_store_part_t part, uint32_t off, const void *buf, uint32_t len)
{
	uint32_t size;
	uint8_t *base = part_ram(part, &size);

	if (base == NULL || off > size || len > size - off) {
		return TS_E_RANGE;
	}
	memcpy(base + off, buf, len);
	return TS_OK;
}

static ts_res_t ram_erase(ts_store_part_t part)
{
	uint32_t size;
	uint8_t *base = part_ram(part, &size);

	if (base == NULL) {
		return TS_E_PARAM;
	}
	memset(base, 0xFF, size);
	return TS_OK;
}

static uint32_t ram_size(ts_store_part_t part)
{
	uint32_t size;

	return part_ram(part, &size) == NULL ? 0 : size;
}

const ts_store_ops_t ts_store_backend = {
	.read = ram_read,
	.write = ram_write,
	.erase = ram_erase,
	.size = ram_size,
};

#ifdef CONFIG_TS_TEST
ts_res_t ts_store_test_reset(void)
{
	for (int p = 0; p < TS_PART_COUNT; p++) {
		ram_erase((ts_store_part_t)p);
	}
	return TS_OK;
}
#endif
