/* SPDX-License-Identifier: Apache-2.0 */
/* 包接收/验签/写 slot（LLD-ts-appmgr §2/§3）。
 * 验签（DEC-49，Q-29④）= verify.c 全量管线：TSAP v2 头 + sha256 摘要对拍 +
 * COSE_Sign1 ed25519 真验签（tweetnacl；TEST 构建 = 固定测试根，生产 = prov
 * pk0）——IR2-02 结构桩时代结束；失败 → TS_E_INVALID_SIG + 留痕。
 * MA3.1：安装链分步化（stage_begin/chunk/verify/activate，LLD-A06 §3）——
 * ts_appmgr_install 与 sys/app-* 命令消费同一内部链（行为一致）。 */
#include <string.h>
#include <ts/appmgr.h>
#include <ts/core.h>
#include <ts/store.h>
#include <ts/tsap.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include "internal.h"

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
	/* v2 容器下限：头 16 + 摘要 32 + 最小 manifest/COSE + 签名域 */
	if (total_len < TSAP_CONTENT_OFF + 8 + 18 + 64 ||
	    total_len > CONFIG_TS_STORE_SLOT_SIZE) {
		return TS_E_PARAM;
	}
	ts_appmgr_meta_t meta;

	ts_res_t mr = ts_appmgr_meta_read(&meta);

	if (mr != TS_OK) {
		/* meta 不可读（空板首装 / 双副本皆损——store 层如实 E_IO）：
		 * 显式恢复安装（目标 slot 0），printk 可观测（IR2-07：不静默） */
		printk("[appmgr] meta unreadable (r=%d) — recovery install to slot 0\n",
		       (int)mr);
		memset(&meta, 0, sizeof(meta));
	}
	/* flash 后端：安装前抹除目标 slot（物理只可 1→0；RAM 后端 = 0xFF 复位）。
	 * begin 可重入重置 = 重装同槽亦经此处（重置语义保持）。 */
	uint8_t target = meta.active_slot ^ 1;
	ts_res_t er = ts_store_slot_erase(target);

	if (er != TS_OK) {
		memset(&stage, 0, sizeof(stage));
		return er; /* 槽抹除失败 = 拒绝开始安装（fail-closed） */
	}
	memset(&stage, 0, sizeof(stage));
	stage.active = true;
	stage.total = total_len;
	stage.slot = target;
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
	/* 1-3. 全量验签（verify.c：TSAP v2 头 → sha256 摘要对拍 → COSE ed25519；
	 * 读与校验全部以 slot 持久化面为准）。 */
	tsap_view_t v;
	ts_res_t r = ts_appmgr_verify_slot(stage.slot, root_pubkey, &v, NULL);

	if (r != TS_OK) {
		const ts_evt_t evt = {.id = TS_EVT_PERM_DENIED, .t_ms = ts_time_ms()};

		ts_evt_publish(&evt);
		return r;
	}
	if ((uint64_t)v.cose_off + 90 > stage.total) {
		return TS_E_PARAM; /* COSE 段不完整（< phdr+map0+payload 头+sig64） */
	}
	/* 4. manifest 边界（与 install 同标） */
	if (v.manifest_len < 8 || v.manifest_len > 512) {
		return TS_E_PARAM;
	}
	stage.verified = true;
	if (manifest_len != NULL) {
		*manifest_len = v.manifest_len;
	}
	if (wasm_len != NULL) {
		*wasm_len = v.wasm_len;
	}
	if (cose_off != NULL) {
		*cose_off = v.cose_off;
	}
	return TS_OK;
}

ts_res_t ts_appmgr_stage_activate(ts_app_info_t *out)
{
	if (!stage.active || !stage.verified) {
		return TS_E_STATE; /* 未验证不得激活（fail-closed） */
	}
	/* 5. 激活对拍（IR2-02 次账收口）：摘要重哈希 == 头摘要（verify 后
	 * 的持久化完整性复查）+ 摘要入 meta（boot 快校验对象）。 */
	tsap_view_t v;
	uint8_t digest[TSAP_DIGEST_SIZE];

	ts_res_t r = ts_appmgr_check_digest(stage.slot, &v);

	if (r != TS_OK) {
		return r;
	}
	if (ts_store_slot_read(stage.slot, TSAP_DIGEST_OFF, digest,
			       TSAP_DIGEST_SIZE) != TS_OK) {
		return TS_E_IO;
	}
	/* 6. meta 原子切换（active_slot = staging slot + 摘要随载） */
	ts_appmgr_meta_t meta;
	ts_res_t mr = ts_appmgr_meta_read(&meta);

	if (mr != TS_OK) {
		memset(&meta, 0, sizeof(meta)); /* 恢复安装路径（begin 已 printk） */
	}
	meta.active_slot = stage.slot;
	meta.rollback_count = 0; /* 新安装重置回滚计数 */
	memcpy(meta.content_digest, digest, TSAP_DIGEST_SIZE);
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
