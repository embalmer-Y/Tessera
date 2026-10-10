/* SPDX-License-Identifier: Apache-2.0 */
/* 双 slot + meta 管理 + 生命周期状态机（LLD-ts-appmgr §3/§4）。
 * meta 经 ts-store 掉电安全 kv（LLD-ts-store §3）；回滚计数超限 → QUARANTINED。 */
#include <string.h>
#include <ts/appmgr.h>
#include <ts/core.h>
#include <ts/store.h>
#include <ts/tsap.h>
#include <zephyr/kernel.h>
#if !defined(CONFIG_TS_TEST) && defined(CONFIG_REBOOT)
#include <zephyr/sys/reboot.h> /* IR2-07：回滚后暖复位重载目标槽 */
#endif
#include "internal.h" /* ts_appmgr_verify_slot/check_digest（DEC-49） */
#if defined(CONFIG_TS_HAL_FS) || defined(CONFIG_TS_HAL_AV)
#include <ts/hal.h> /* ts_fs_paths_bind / ts_av_config_bind（DEC-47⑤③） */
#endif

ts_app_info_t current_app;
bool initialized;

#ifdef CONFIG_TS_TEST
void ts_appmgr_test_reset(void)
{
	initialized = false;
	memset(&current_app, 0, sizeof(current_app));
}
#endif

ts_res_t ts_appmgr_meta_read(ts_appmgr_meta_t *meta)
{
	if (meta == NULL) return TS_E_PARAM;
	uint16_t len = 0;

	if (ts_store_meta_read(meta, &len) != TS_OK || len != sizeof(*meta)) {
		memset(meta, 0, sizeof(*meta));
		meta->active_slot = 0;
		/* IR2-07：空板首装与双副本皆损在此同象（store 层不可分辨）——
		 * 如实上报 E_IO，不静默伪造成有效 meta；调用方按各自语义处置
		 * （boot = 不装载；install = 显式恢复安装〔begin printk 可观测〕） */
		return TS_E_IO;
	}
	return TS_OK;
}

ts_res_t ts_appmgr_meta_write(const ts_appmgr_meta_t *meta)
{
	return ts_store_meta_write(meta, (uint16_t)sizeof(*meta));
}

ts_res_t ts_appmgr_get_info(ts_app_info_t *out)
{
	if (out == NULL) return TS_E_PARAM;
	if (!initialized) {
		/* 首次调用：从 meta 恢复（掉电重启路径）；不可读（空板/双损）=
		 * 缺省可观测态（不静默写回——IR2-07） */
		ts_appmgr_meta_t meta;

		if (ts_appmgr_meta_read(&meta) == TS_OK) {
			current_app.active_slot = meta.active_slot;
			current_app.rollback_count = meta.rollback_count;
		}
		current_app.state = TS_APP_STAGED;
		initialized = true;
	}
	*out = current_app;
	return TS_OK;
}

ts_res_t ts_appmgr_rollback(void)
{
	if (!initialized) return TS_E_STATE;
	if (current_app.state != TS_APP_ACTIVE && current_app.state != TS_APP_ROLLBACK) {
		return TS_E_STATE;
	}
	if (current_app.rollback_count >= TS_APPMGR_ROLLBACK_LIMIT) {
		/* DEC-27 #9：超限 → QUARANTINED（终态，不循环回滚） */
		current_app.state = TS_APP_QUARANTINED;
		/* G4（单元 H）：隔离持久化——meta.rollback_count = LIMIT+1 为拒载
		 * 标记（boot_start 判据；运行时计数仍如实 = LIMIT）。写失败留痕：
		 * 本 boot 已隔离，重启后重走一次装载判定（不静默伪造终态）。 */
		ts_appmgr_meta_t meta;

		if (ts_appmgr_meta_read(&meta) == TS_OK &&
		    meta.rollback_count <= TS_APPMGR_ROLLBACK_LIMIT) {
			meta.rollback_count = TS_APPMGR_ROLLBACK_LIMIT + 1;
			if (ts_appmgr_meta_write(&meta) != TS_OK) {
				printk("[appmgr] quarantine marker persist failed\n");
			}
		}
		const ts_evt_t evt = {.id = TS_EVT_APP_QUARANTINED, .t_ms = ts_time_ms()};
		ts_evt_publish(&evt);
		return TS_E_ROLLBACK_LIMIT;
	}
	/* IR2-07：回滚闭环——目标槽先全量验签（头 v2/摘要/ed25519），
	 * 空/坏槽 = 如实失败且不翻转 active_slot（旧缺陷：翻入空槽后系统
	 * 无限期无业务逻辑且无人知晓）。 */
	uint8_t target = current_app.active_slot ^ 1;
	tsap_view_t tv;
	ts_res_t vr = ts_appmgr_verify_slot(target, NULL, &tv, NULL);

	if (vr != TS_OK) {
		printk("[appmgr] rollback: target slot %u invalid (r=%d) — no flip\n",
		       target, (int)vr);
		return TS_E_IO;
	}
	ts_appmgr_meta_t meta;
	ts_res_t mr = ts_appmgr_meta_read(&meta);

	if (mr != TS_OK) {
		printk("[appmgr] rollback: meta unreadable (r=%d) — refused\n", (int)mr);
		return TS_E_IO;
	}
	/* 切换 slot + 递增计数 + 写 meta（原子；摘要随目标槽更新） */
	ts_app_state_t prev_state = current_app.state;

	current_app.active_slot = target;
	current_app.rollback_count++;
	current_app.state = TS_APP_ROLLBACK;
	meta.active_slot = current_app.active_slot;
	meta.rollback_count = current_app.rollback_count;
	if (ts_store_slot_read(target, TSAP_DIGEST_OFF, meta.content_digest,
			       TSAP_DIGEST_SIZE) != TS_OK) {
		return TS_E_IO;
	}
	ts_res_t r = ts_appmgr_meta_write(&meta);

	if (r != TS_OK) {
		/* meta 写失败：回退运行时状态并报错——运行态与持久态不得分叉
		 * （impl-review IR-09；重启后回到旧 meta = 安全侧） */
		current_app.active_slot ^= 1;
		current_app.rollback_count--;
		current_app.state = prev_state;
		return r;
	}
	const ts_evt_t evt = {.id = TS_EVT_APP_UNLOADED, .t_ms = ts_time_ms()};
	ts_evt_publish(&evt);
#if !defined(CONFIG_TS_TEST) && defined(CONFIG_REBOOT)
	/* IR2-07：回滚闭环——meta 翻转后暖复位装载目标槽（旧缺陷：翻转后无
	 * 重载/复位，系统无限期无业务逻辑）。TEST 构建不复位（用例断言状态机）；
	 * 无 REBOOT 的板配置 = 如实登记（printk 可观测）。 */
	printk("[appmgr] rollback: warm reboot to slot %u\n", current_app.active_slot);
	sys_reboot(SYS_REBOOT_WARM);
#elif !defined(CONFIG_TS_TEST)
	printk("[appmgr] rollback: slot flipped (no CONFIG_REBOOT — manual reload)\n");
#endif
	return TS_OK;
}

ts_res_t ts_appmgr_health_fail(void)
{
	return ts_appmgr_rollback();
}

/* ---- boot 装载（M2b.2 收尾单元；HLD §4.4-8：APP 故障不阻塞启动）--------- */

#ifdef CONFIG_TS_APP_WAMR
#include "../net/internal.h" /* ts_cbor_* 读助手（tessera 模块内复用） */

static uint8_t boot_wasm_buf[CONFIG_TS_APP_LOAD_MAX];
static char boot_caps[160];
#ifdef CONFIG_TS_HAL_FS
static char boot_fs_paths[CONFIG_TS_HAL_FS_PATHS_MAX]; /* DEC-47⑤ */
#endif
#ifdef CONFIG_TS_HAL_AV
static ts_av_fmt_t boot_av_fmt; /* DEC-47③（MD1.2g）：采集格式/分辨率随载绑定 */
static uint16_t boot_av_w, boot_av_h;
static uint8_t boot_av_set; /* 位掩码：1=fmt 2=w 4=h（全置 = 声明完整） */
#endif
#endif /* CONFIG_TS_APP_WAMR（boot 装载缓冲区——仅 WAMR 构建需要） */

ts_res_t ts_appmgr_boot_start(void)
{
	ts_appmgr_meta_t meta;

	if (ts_appmgr_meta_read(&meta) != TS_OK) {
		/* IR2-07：meta 不可读（空板/双损）= 不静默装载 slot 0 */
		printk("[appmgr] boot: meta unreadable — no app loaded\n");
		return TS_E_STATE;
	}
	/* G4（单元 H）：隔离拒载（LLD §2「QUARANTINED 拒载」的 boot 面）——
	 * meta.rollback_count = LIMIT+1 为隔离持久化标记（rollback 拒绝第 4 次
	 * 时写入）；跨重启不再装载已知坏链（旧缺陷：每次上电重载坏包 → 健康
	 * 失败 → 再隔离，一次/boot 循环）。解除 = 新安装（activate 重置计数）。
	 * 计数 == LIMIT（第 3 次回滚落地态）不拒——其目标版本仍可装载（与
	 * runtime 语义一致：允许恰好 3 次回滚）。观测面如实报 QUARANTINED。 */
	if (meta.rollback_count > TS_APPMGR_ROLLBACK_LIMIT) {
		printk("[appmgr] boot: rollback_count=%u quarantined — no app loaded\n",
		       meta.rollback_count);
		current_app.active_slot = meta.active_slot;
		current_app.rollback_count = TS_APPMGR_ROLLBACK_LIMIT;
		current_app.state = TS_APP_QUARANTINED;
		initialized = true;
		return TS_E_ROLLBACK_LIMIT;
	}
#ifdef CONFIG_TS_APP_WAMR
	uint8_t hdr[TSAP_HEADER_SIZE];

	if (ts_store_slot_read(meta.active_slot, 0, hdr, sizeof(hdr)) != TS_OK) {
		return TS_E_IO;
	}
	if (memcmp(hdr, "TSAP", 4) != 0) {
		return TS_E_NOTFOUND; /* 空/未写 slot = 无 APP（boot 不阻塞） */
	}
	/* v2 快校验（DEC-49②）：sha256(manifest‖wasm) == 头摘要（毫秒级——
	 * 全量 ed25519 验签在安装/激活期完成；boot 只防持久化位腐）。 */
	tsap_view_t v;

	if (ts_appmgr_check_digest(meta.active_slot, &v) != TS_OK) {
		printk("[appmgr] boot: digest mismatch (slot %u) — no app loaded\n",
		       meta.active_slot);
		return TS_E_INVALID_SIG;
	}
	uint32_t ml = v.manifest_len;
	uint32_t wl = v.wasm_len;

	if (ml == 0 || ml > 512 || wl == 0 || wl > sizeof(boot_wasm_buf)) {
		return TS_E_PARAM; /* 容器头越界（装载上限 = CONFIG_TS_APP_LOAD_MAX） */
	}
	static uint8_t man[512];

	if (ts_store_slot_read(meta.active_slot, TSAP_CONTENT_OFF, man, ml) != TS_OK) {
		return TS_E_IO;
	}
	/* manifest 走查（TsapManifest v1 canonical CBOR；按键名分发——
	 * fail-closed：未知键拒绝）。caps 组合为 ';' 分隔串（runtime 逐条 parse，
	 * ts_perm_parse 语义 = 位或合并）。stack_kb/heap_kb V1 消耗运行时常量
	 * （LLD §7 已知限制——manifest 读取但暂不生效，板级内存预算批兑现）。 */
	ts_cbor_rd_t r;
	uint32_t pairs;

	ts_cbor_rd_init(&r, man, ml);
	if (!ts_cbor_map_open(&r, &pairs)) {
		return TS_E_PARAM;
	}
	boot_caps[0] = '\0';
	size_t caps_len = 0;

	for (uint32_t i = 0; i < pairs; i++) {
		char key[16];

		if (!ts_cbor_tstr(&r, key, sizeof(key))) {
			return TS_E_PARAM;
		}
		if (strcmp(key, "caps") == 0) {
			uint32_t n;

			if (!ts_cbor_array_open(&r, &n)) {
				return TS_E_PARAM;
			}
			for (uint32_t j = 0; j < n; j++) {
				char cap[48];

				if (!ts_cbor_tstr(&r, cap, sizeof(cap))) {
					return TS_E_PARAM;
				}
				size_t cl = strlen(cap);

				if (caps_len + cl + 2 >= sizeof(boot_caps)) {
					return TS_E_PARAM;
				}
				if (caps_len > 0) {
					boot_caps[caps_len++] = ';';
				}
				memcpy(boot_caps + caps_len, cap, cl);
				caps_len += cl;
				boot_caps[caps_len] = '\0';
			}
		} else if (strcmp(key, "app_id") == 0 || strcmp(key, "app_ver") == 0) {
			char val[64];

			if (!ts_cbor_tstr(&r, val, sizeof(val))) {
				return TS_E_PARAM;
			}
			if (strcmp(key, "app_id") == 0) {
				strncpy(current_app.app_id, val,
					sizeof(current_app.app_id) - 1);
				current_app.app_id[sizeof(current_app.app_id) - 1] = '\0';
			} else {
				strncpy(current_app.app_ver, val,
					sizeof(current_app.app_ver) - 1);
				current_app.app_ver[sizeof(current_app.app_ver) - 1] = '\0';
			}
		} else if (strcmp(key, "min_fw_ver") == 0) {
			char val[32];

			if (!ts_cbor_tstr(&r, val, sizeof(val))) {
				return TS_E_PARAM;
			}
		} else if (strcmp(key, "stack_kb") == 0 || strcmp(key, "heap_kb") == 0) {
			uint64_t v;

			if (!ts_cbor_uint(&r, &v)) {
				return TS_E_PARAM;
			}
			/* V1 消耗运行时常量（见上注释） */
#ifdef CONFIG_TS_HAL_FS
		} else if (strcmp(key, "fs_paths") == 0) {
			/* DEC-47⑤（MD1.2e）：路径前缀白名单（数组 → ';' CSV；
			 * fail-closed：越界/非绝对路径条目拒绝装载） */
			uint32_t n;

			if (!ts_cbor_array_open(&r, &n)) {
				return TS_E_PARAM;
			}
			boot_fs_paths[0] = '\0';
			size_t plen = 0;

			for (uint32_t j = 0; j < n; j++) {
				char pfx[68]; /* agent 校验器条目上限 64+NUL；68 对齐（复检发现②） */

				if (!ts_cbor_tstr(&r, pfx, sizeof(pfx)) ||
				    pfx[0] != '/' ||
				    strstr(pfx, "..") != NULL) {
					return TS_E_PARAM;
				}
				size_t l = strlen(pfx);

				if (plen + l + 2 >= sizeof(boot_fs_paths)) {
					return TS_E_PARAM;
				}
				if (plen > 0) {
					boot_fs_paths[plen++] = ';';
				}
				memcpy(boot_fs_paths + plen, pfx, l);
				plen += l;
				boot_fs_paths[plen] = '\0';
			}
#endif /* CONFIG_TS_HAL_FS */
#ifdef CONFIG_TS_HAL_AV
		} else if (strcmp(key, "av_fmt") == 0) {
			/* DEC-47③（MD1.2g）：采集格式（jpeg/rgb565——DEC-47② JPEG 优先） */
			char f[8];

			if (!ts_cbor_tstr(&r, f, sizeof(f))) {
				return TS_E_PARAM;
			}
			if (strcmp(f, "jpeg") == 0) {
				boot_av_fmt = TS_AV_FMT_JPEG;
			} else if (strcmp(f, "rgb565") == 0) {
				boot_av_fmt = TS_AV_FMT_RGB565;
			} else {
				return TS_E_PARAM;
			}
			boot_av_set |= 1U;
		} else if (strcmp(key, "av_w") == 0 || strcmp(key, "av_h") == 0) {
			uint64_t v;

			if (!ts_cbor_uint(&r, &v) || v < 16 || v > 800) {
				return TS_E_PARAM;
			}
			if (key[3] == 'w') {
				boot_av_w = (uint16_t)v;
				boot_av_set |= 2U;
			} else {
				boot_av_h = (uint16_t)v;
				boot_av_set |= 4U;
			}
#endif /* CONFIG_TS_HAL_AV */
		} else if (strcmp(key, "exports") == 0) {
			uint32_t n;

			if (!ts_cbor_array_open(&r, &n)) {
				return TS_E_PARAM;
			}
			for (uint32_t j = 0; j < n; j++) {
				char ex[48];

				if (!ts_cbor_tstr(&r, ex, sizeof(ex))) {
					return TS_E_PARAM;
				}
			}
		} else {
			return TS_E_PARAM; /* 未知键 = schema v1 之外（fail-closed） */
		}
	}
	if (ts_store_slot_read(meta.active_slot, TSAP_CONTENT_OFF + ml,
			       boot_wasm_buf, wl) != TS_OK) {
		return TS_E_IO;
	}
	/* V1 运行时数值 app_id = 1（单活跃 APP；审计字符串归因在 current_app） */
	ts_res_t sr = ts_appmgr_app_start(1, boot_wasm_buf, wl, boot_caps);

#ifdef CONFIG_TS_HAL_FS
	if (sr == TS_OK && boot_fs_paths[0] != '\0') {
		(void)ts_fs_paths_bind(1, boot_fs_paths); /* DEC-47⑤：路径白名单随载绑定 */
	}
#endif
#ifdef CONFIG_TS_HAL_AV
	if (sr == TS_OK && boot_av_set == 0x7) {
		(void)ts_av_config_bind(1, boot_av_fmt, boot_av_w, boot_av_h); /* DEC-47③ */
	}
#endif
	if (sr == TS_OK) {
		current_app.state = TS_APP_ACTIVE; /* STAGED →（加载周期）→ ACTIVE */
		current_app.active_slot = meta.active_slot;
		/* B2 批修正：回滚计数随载恢复（旧缺：仅恢复 state/slot——count
		 * 停留 BSS 0，跨重启后 get-app 永远报 0；flash 实测 meta=1 而
		 * 运行时报 0 即本缺陷。隔离拒载路径（上文）与 get_info 懒恢复
		 * 均已各自恢复计数，唯本装载路径漏）。 */
		current_app.rollback_count = meta.rollback_count;
		/* 板级十修复：装载成功即占有 current_app——不置 initialized 时首次
		 * get_info（观测线程/sys get-app）的惰性初始化会把 ACTIVE 打回
		 * STAGED（懒路径盲写 state = 装载结果被观测面抹掉）；active_slot
		 * 同步自 meta（部署确认语义 = activate/get-app 槽位对拍）。 */
		initialized = true;
	}
	return sr;
#else
	return TS_E_STATE; /* WAMR 未编入（CONFIG_TS_APP_WAMR） */
#endif
}

#ifndef CONFIG_TS_APP_WAMR
/* 无 WAMR 构建面（netbench 等：TS_APPMGR=y 供 sys/app 命令链，但无运行
 * 时）。G4（单元 H）起 pkg.c 的 activate 路径引用本组符号——无 WAMR 面
 * 无构建覆盖，P4 无线批（netbench @ esp32p4）链接实证修复。语义退化：
 * 无运行时 = 恒无 APP 在跑；stop 无对象 = OK（无可停者）。 */
bool ts_appmgr_app_running(void)
{
	return false;
}

ts_res_t ts_appmgr_app_stop(void)
{
	return TS_OK;
}
#endif
