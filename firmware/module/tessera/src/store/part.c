/* SPDX-License-Identifier: Apache-2.0 */
/*
 * 分区表与后端抽象（LLD-ts-store §2）。
 * 后端实现：
 *  - **RAM 后端**（默认，native_sim/测试）：静态数组 + 0xFF 抹除语义，
 *    ts_store_test_reset() 模拟"掉电后全新镜像"；跨进程持久化非测试所需。
 *  - **flash 后端**（CONFIG_TS_STORE_FLASH，板级五）：DT fixed-partitions
 *    （ts_prov_part/ts_meta_part/ts_slot_a_part/ts_slot_b_part/ts_noinit_part）
 *    + flash_map 读写擦。写对齐按驱动 write_block_size 运行时适配
 *    （esp32s3 = 4B；非整字片段经读-改-写垫片——上层均为 erase-then-write
 *    或同值幂等重发，满足 flash 物理只可 1→0）。
 * 上层（appmgr 等）不感知后端。
 */
#include <string.h>
#include <zephyr/kernel.h>
#include <ts/store.h>
#include "internal.h"

#ifndef CONFIG_TS_STORE_FLASH

/* ---- RAM 后端 ----------------------------------------------------------- */

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

static ts_res_t ram_erase_off(ts_store_part_t part, uint32_t off, uint32_t len)
{
	uint32_t size;
	uint8_t *base = part_ram(part, &size);

	if (base == NULL || off > size || len > size - off) {
		return TS_E_RANGE;
	}
	memset(base + off, 0xFF, len);
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
	.erase_off = ram_erase_off,
	.size = ram_size,
};

#else /* CONFIG_TS_STORE_FLASH */

/* ---- flash 后端（板级五；DT 分区 + flash_map）--------------------------- */

#include <zephyr/storage/flash_map.h>

#define NODE_PROV    DT_NODELABEL(ts_prov_part)
#define NODE_META    DT_NODELABEL(ts_meta_part)
#define NODE_SLOT_A  DT_NODELABEL(ts_slot_a_part)
#define NODE_SLOT_B  DT_NODELABEL(ts_slot_b_part)
#define NODE_NOINIT  DT_NODELABEL(ts_noinit_part)

#if !DT_NODE_EXISTS(NODE_PROV) || !DT_NODE_EXISTS(NODE_META) || \
	!DT_NODE_EXISTS(NODE_SLOT_A) || !DT_NODE_EXISTS(NODE_SLOT_B) || \
	!DT_NODE_EXISTS(NODE_NOINIT)
#error "ts-store flash 后端：DT 缺少 ts_*_part 分区（板 overlay 须定义 ts_prov_part / ts_meta_part / ts_slot_a_part / ts_slot_b_part / ts_noinit_part，LLD-ts-store §2）"
#endif

/* 分区尺寸与 Kconfig 的硬耦合（fail-closed：错配 = 构建期失败而非运行期越界）。
 * PARTITION_* 为 v4.4 现行 API（FIXED_PARTITION_* 已弃用，twister -Werror 拦截）。 */
BUILD_ASSERT(PARTITION_SIZE(ts_slot_a_part) == CONFIG_TS_STORE_SLOT_SIZE,
	     "ts_slot_a_part size must equal CONFIG_TS_STORE_SLOT_SIZE");
BUILD_ASSERT(PARTITION_SIZE(ts_slot_b_part) == CONFIG_TS_STORE_SLOT_SIZE,
	     "ts_slot_b_part size must equal CONFIG_TS_STORE_SLOT_SIZE");
BUILD_ASSERT(PARTITION_SIZE(ts_meta_part) / 2 >= 8 + CONFIG_TS_STORE_META_MAX,
	     "ts_meta_part copy stride must fit REC_HDR + META_MAX");

static const struct flash_area *flash_fa(ts_store_part_t part)
{
	/* flash_area_open 为静态表查找——进程级缓存安全 */
	static const struct flash_area *cache[TS_PART_COUNT];
	const struct flash_area *fa = cache[part];
	uint8_t id;

	if (fa != NULL) {
		return fa;
	}
	switch (part) {
	case TS_PART_PROV:
		id = PARTITION_ID(ts_prov_part);
		break;
	case TS_PART_META:
		id = PARTITION_ID(ts_meta_part);
		break;
	case TS_PART_SLOT_A:
		id = PARTITION_ID(ts_slot_a_part);
		break;
	case TS_PART_SLOT_B:
		id = PARTITION_ID(ts_slot_b_part);
		break;
	default:
		id = PARTITION_ID(ts_noinit_part);
		break;
	}
	if (flash_area_open(id, &fa) != 0) {
		return NULL;
	}
	cache[part] = fa;
	return fa;
}

static uint32_t flash_size(ts_store_part_t part)
{
	switch (part) {
	case TS_PART_PROV:
		return PARTITION_SIZE(ts_prov_part);
	case TS_PART_META:
		return PARTITION_SIZE(ts_meta_part);
	case TS_PART_SLOT_A:
		return PARTITION_SIZE(ts_slot_a_part);
	case TS_PART_SLOT_B:
		return PARTITION_SIZE(ts_slot_b_part);
	default:
		return PARTITION_SIZE(ts_noinit_part);
	}
}

static ts_res_t flash_read(ts_store_part_t part, uint32_t off, void *buf, uint32_t len)
{
	uint32_t size = flash_size(part);

	if (off > size || len > size - off) { /* 溢出安全边界（IR-07） */
		return TS_E_RANGE;
	}
	const struct flash_area *fa = flash_fa(part);

	if (fa == NULL || flash_area_read(fa, off, buf, len) != 0) {
		return TS_E_IO;
	}
	return TS_OK;
}

/* 写对齐垫片：按 4B 字粒度（esp32s3 DT write-block-size=4；对 wbs∈{1,2,4}
 * 的后端均安全——4 对齐蕴含更小对齐。flash_get_write_block_size 为 syscall
 * 封装、非 userspace 构建链接不可用，故不运行时查询）。逐字"读-比-写"：
 *  - 同值字跳过（幂等重发零重编程）；
 *  - 位子集校验：目标字的 1-位须为现值所含（flash 物理只可 1→0）——
 *    越过 erase 的改写在真机为静默 AND 损坏，此处显式拦截；
 *  - 头/尾非整字片段经组字（片段外既有字节原样保留）。
 * 约束：任意偏移块写入在块边界字产生"部分编程字扩展写"——真机合法，
 * sim-flash EXPLICIT_ERASE（程序一次语义）拒绝；当前所有调用方均为
 * 单次连续写或整槽 erase 后顺序写，不受影响（LLD-ts-store §2 留痕）。 */
#define FLASH_WORD 4

static ts_res_t flash_write(ts_store_part_t part, uint32_t off, const void *buf, uint32_t len)
{
	uint32_t size = flash_size(part);

	if (off > size || len > size - off) {
		return TS_E_RANGE;
	}
	const struct flash_area *fa = flash_fa(part);

	if (fa == NULL) {
		return TS_E_IO;
	}
	const uint8_t *src = buf;
	uint32_t done = 0;
	uint8_t cur[FLASH_WORD] __aligned(4);
	uint8_t word[FLASH_WORD] __aligned(4);

	while (done < len) {
		uint32_t addr = off + done;
		uint32_t rem = len - done;
		uint32_t wa = addr - (addr % FLASH_WORD);
		uint32_t skip = addr - wa;
		uint32_t take = FLASH_WORD - skip;

		if (take > rem) {
			take = rem;
		}
		if (flash_area_read(fa, wa, cur, FLASH_WORD) != 0) {
			return TS_E_IO;
		}
		memcpy(word, cur, FLASH_WORD);
		memcpy(word + skip, src + done, take);
		if (memcmp(word, cur, FLASH_WORD) == 0) {
			done += take;
			continue; /* 同值幂等（重发安全） */
		}
		bool allowed = true;

		for (int i = 0; i < FLASH_WORD; i++) {
			if ((cur[i] & word[i]) != word[i]) {
				allowed = false; /* 需要 0→1 = 越 erase 改写 */
				break;
			}
		}
		if (!allowed) {
			return TS_E_IO;
		}
		if (flash_area_write(fa, wa, word, FLASH_WORD) != 0) {
			return TS_E_IO;
		}
		done += take;
	}
	return TS_OK;
}

static ts_res_t flash_erase_off(ts_store_part_t part, uint32_t off, uint32_t len)
{
	uint32_t size = flash_size(part);

	if (off > size || len > size - off) {
		return TS_E_RANGE;
	}
	const struct flash_area *fa = flash_fa(part);

	if (fa == NULL || flash_area_erase(fa, off, len) != 0) {
		return TS_E_IO;
	}
	return TS_OK;
}

static ts_res_t flash_erase_full(ts_store_part_t part)
{
	return flash_erase_off(part, 0, flash_size(part));
}

const ts_store_ops_t ts_store_backend = {
	.read = flash_read,
	.write = flash_write,
	.erase = flash_erase_full,
	.erase_off = flash_erase_off,
	.size = flash_size,
};

#endif /* CONFIG_TS_STORE_FLASH */

#ifdef CONFIG_TS_TEST
ts_res_t ts_store_test_reset(void)
{
	for (int p = 0; p < TS_PART_COUNT; p++) {
		ts_res_t r = ts_store_backend.erase((ts_store_part_t)p);

		if (r != TS_OK) {
			return r;
		}
	}
	return TS_OK;
}
#endif
