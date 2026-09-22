/* SPDX-License-Identifier: Apache-2.0 */
/* ts-appmgr 内部共享（不对外）。 */
#ifndef TS_APPMGR_INTERNAL_H__
#define TS_APPMGR_INTERNAL_H__

#include <ts/appmgr.h>
#include <stdbool.h>

/* 运行时 APP 状态（slot.c 定义，pkg.c 引用） */
extern ts_app_info_t current_app;
extern bool initialized;

#endif /* TS_APPMGR_INTERNAL_H__ */
