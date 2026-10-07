/* SPDX-License-Identifier: Apache-2.0 */
/* ts-appmgr 内部共享（不对外）。 */
#ifndef TS_APPMGR_INTERNAL_H__
#define TS_APPMGR_INTERNAL_H__

#include <ts/appmgr.h>
#include <ts/tsap.h>
#include <stdbool.h>

/* 运行时 APP 状态（slot.c 定义，pkg.c 引用） */
extern ts_app_info_t current_app;
extern bool initialized;

/* verify.c（DEC-49）：全量验签（头 v2 → 摘要 → COSE ed25519）与 boot 快校验 */
ts_res_t ts_appmgr_verify_slot(uint8_t slot, const uint8_t root_pubkey[32],
			       tsap_view_t *v, uint8_t digest_out[32]);
ts_res_t ts_appmgr_check_digest(uint8_t slot, tsap_view_t *v);
const uint8_t *ts_appmgr_root_key(const uint8_t root_pubkey[32]);

#endif /* TS_APPMGR_INTERNAL_H__ */
