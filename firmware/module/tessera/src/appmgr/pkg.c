/* SPDX-License-Identifier: Apache-2.0 */
/* 包接收/验签/写 slot（LLD-ts-appmgr §2/§3）。
 * 验签使用 ed25519（根公钥来自 prov 或测试注入）；失败 → TS_E_INVALID_SIG + 留痕。
 * M2b：COSE 验签骨架 + TSAP 头解析 + slot 写入；WAMR 运行时 = M2b.2。
 * MA3.1：安装链分步化（stage_begin/chunk/verify/activate，LLD-A06 §3）——
 * ts_appmgr_install 与 sys/app-* 命令消费同一内部链（行为一致）。 */
#include <string.h>
#include <ts/appmgr.h>
#include <ts/core.h>
#include <ts/store.h>
#include <ts/tsap.h>
#include <zephyr/kernel.h>
#include "internal.h"

/* V1：简化 ed25519 验签骨架（真实现随 WAMR/M2b.2 引入——当前仅结构校验。
 * WAMR 自带 COSE 验签能力；此处预留接口与哈希校验。
 * **fail-closed 纪律（impl-review IR-05）**：真实验签未接入前，非测试构建
 * 一律拒绝安装（TS_E_INVALID_SIG）——仅 CONFIG_TS_TEST 构建允许结构级
 * 通过以驱动 slot/meta 链路测试。 */
static ts_res_t verify_cose_minimal(const uint8_t *cose, uint32_t cose_len,
				     const uint8_t root_pubkey[32])
{
	if (cose == NULL || cose_len < 18 || root_pubkey == NULL) {
		return TS_E_INVALID_SIG;
	}
	/* V1 结构检查：CBOR tag 18 (0xd2) + array(4) 头 */
	if (cose[0] != 0xd2 || cose[1] != 0x84) {
		return TS_E_INVALID_SIG;
	}
#ifndef CONFIG_TS_TEST
	/* 生产构建：无真实验签 = 无安装（TODO M2b.2：ed25519 验签接入后移除） */
	return TS_E_INVALID_SIG;
#else
	return TS_OK;
#endif
}

/* ---- 分步安装 staging 状态（内存；begin 可重入重置）---------------------- */

static struct {
	bool active;
	bool verified;
	uint32_t total;
	uint32_t high_water; /* 已写最大 offset+len（断点续传进度） */
	uint8_t slot;        /* inactive slot */
} stage;

ts_res_t ts_appmgr_stage_begin(uint32_t total_len, uint8_t *slot_out)
{
	if (total_len < TSAP_HEADER_SIZE + 18 + 8 || /* 头 + 最小 COSE + 最小 manifest */
	    total_len > CONFIG_TS_STORE_SLOT_SIZE) {
		return TS_E_PARAM;
	}
	ts_appmgr_meta_t meta;

	ts_appmgr_meta_read(&meta);
	memset(&stage, 0, sizeof(stage));
	stage.active = true;
	stage.total = total_len;
	stage.slot = meta.active_slot ^ 1;
	if (slot_out != NULL) {
		*slot_out = stage.slot;
	}
	return TS_OK;
}

ts_res_t ts_appmgr_stage_chunk(uint32_t off, const uint8_t *data, uint32_t len,
			       uint32_t *high_water)
{
	if (!stage.active || data == NULL || len == 0) {
		return TS_E_STATE;
	}
	if ((uint64_t)off + len > stage.total) {
		return TS_E_PARAM; /* 越界 = 拒绝（不静默截断） */
	}
	/* 逐块写 + 回读校验语义由 ts_store_slot_write 内置（LLD-ts-store §6）；
	 * 同 offset 重写幂等（重发安全，DEC-40 idem 之外的传输层兜底）。 */
	ts_res_t r = ts_store_slot_write(stage.slot, off, data, len);

	if (r != TS_OK) {
		return r;
	}
	if (off + len > stage.high_water) {
		stage.high_water = off + len;
	}
	if (high_water != NULL) {
		*high_water = stage.high_water;
	}
	return TS_OK;
}

ts_res_t ts_appmgr_stage_verify(const uint8_t root_pubkey[32],
				uint32_t *manifest_len, uint32_t *wasm_len,
				uint32_t *cose_off)
{
	if (!stage.active || stage.high_water < stage.total) {
		return TS_E_STATE; /* 未收满不得验（fail-closed） */
	}
	/* 1. TSAP 头（自 slot 回读——传输内容以持久化面为准）。字段级解析：
	 * tsap_header_parse 的边界自洽以传入缓冲长度为界，staging 场景只回读
	 * 头部，故以 stage.total 为权威长度做同等校验（magic/ver/段布局不越界）。 */
	uint8_t hdr[TSAP_HEADER_SIZE];
	ts_res_t r = ts_store_slot_read(stage.slot, 0, hdr, sizeof(hdr));

	if (r != TS_OK) {
		return r;
	}
	if (tsap_be32(hdr) != TSAP_MAGIC || tsap_be16(hdr + 4) != TSAP_FMT_VER) {
		return TS_E_INVALID_SIG;
	}
	uint32_t ml = tsap_be32(hdr + 6);
	uint32_t wl = tsap_be32(hdr + 10);
	uint64_t co = (uint64_t)TSAP_HEADER_SIZE + ml + wl;

	/* 2. 容器自洽：total 与头声明的段布局一致（COSE 起点之后至少 18B） */
	if (co + 18 > stage.total) {
		return TS_E_PARAM;
	}
	/* 3. COSE 验签（V1 结构级；读 COSE 段首部，结构检查只需头部字节）。
	 * 检查序与旧 install 链一致（COSE 结构先于 manifest 边界——manifest
	 * 错位时 COSE 落点即错，报 INVALID_SIG 而非 PARAM）。 */
	uint32_t clen = (uint32_t)(stage.total - co);
	uint32_t read_len = clen < 64 ? clen : 64;
	uint8_t cose_buf[64];

	r = ts_store_slot_read(stage.slot, (uint32_t)co, cose_buf, read_len);
	if (r != TS_OK) {
		return r;
	}
	r = verify_cose_minimal(cose_buf, clen, root_pubkey);
	if (r != TS_OK) {
		const ts_evt_t evt = {.id = TS_EVT_PERM_DENIED, .t_ms = ts_time_ms()};
		ts_evt_publish(&evt);
		return r;
	}
	/* 4. manifest 边界（V1：8..512，与 install 同标） */
	if (ml < 8 || ml > 512) {
		return TS_E_PARAM;
	}
	stage.verified = true;
	if (manifest_len != NULL) {
		*manifest_len = ml;
	}
	if (wasm_len != NULL) {
		*wasm_len = wl;
	}
	if (cose_off != NULL) {
		*cose_off = (uint32_t)co;
	}
	return TS_OK;
}

ts_res_t ts_appmgr_stage_activate(ts_app_info_t *out)
{
	if (!stage.active || !stage.verified) {
		return TS_E_STATE; /* 未验证不得激活（fail-closed） */
	}
	/* 5. 整槽 hash 校验（与 install 同标：覆盖全槽，非仅 pkg 长度） */
	uint8_t sha[32];

	ts_res_t r = ts_store_slot_hash(stage.slot, sha);

	if (r != TS_OK) {
		return r;
	}
	/* 6. meta 原子切换（active_slot = staging slot） */
	ts_appmgr_meta_t meta;

	ts_appmgr_meta_read(&meta);
	meta.active_slot = stage.slot;
	meta.rollback_count = 0; /* 新安装重置回滚计数 */
	r = ts_appmgr_meta_write(&meta);
	if (r != TS_OK) {
		return r;
	}
	/* 7. 更新运行时信息（与 install 一致） */
	memset(&current_app, 0, sizeof(current_app));
	current_app.state = TS_APP_STAGED;
	current_app.active_slot = stage.slot;
	current_app.rollback_count = 0;
	if (out != NULL) {
		*out = current_app;
	}
	initialized = true;
	const ts_evt_t evt = {.id = TS_EVT_APP_LOADED, .t_ms = ts_time_ms()};
	ts_evt_publish(&evt);
	memset(&stage, 0, sizeof(stage)); /* 终态清台（下轮 begin 重置） */
	return TS_OK;
}

/* ---- 整包一次式安装（本地路径；= 分步链的组合，行为与 M2b.1 一致）-------- */

ts_res_t ts_appmgr_install(const uint8_t *pkg_data, size_t pkg_len,
			    const uint8_t root_pubkey[32], ts_app_info_t *out)
{
	if (pkg_data == NULL || root_pubkey == NULL || out == NULL) {
		return TS_E_PARAM;
	}
	if (ts_appmgr_stage_begin((uint32_t)pkg_len, NULL) != TS_OK) {
		return TS_E_INVALID_SIG; /* 尺寸非法 = 容器非法（与旧语义一致） */
	}
	ts_res_t r = ts_appmgr_stage_chunk(0, pkg_data, (uint32_t)pkg_len, NULL);

	if (r != TS_OK) {
		memset(&stage, 0, sizeof(stage));
		return r;
	}
	uint32_t ml = 0, wl = 0, co = 0;

	r = ts_appmgr_stage_verify(root_pubkey, &ml, &wl, &co);
	if (r != TS_OK) {
		memset(&stage, 0, sizeof(stage));
		return r;
	}
	return ts_appmgr_stage_activate(out);
}
