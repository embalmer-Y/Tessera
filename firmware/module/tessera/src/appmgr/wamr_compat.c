/* SPDX-License-Identifier: Apache-2.0 */
/* WAMR × Zephyr 4.4 兼容垫片（M2b.2a，零上游补丁纪律）。
 * WAMR-2.4.5 的 zephyr 平台层（core/shared/platform/zephyr/zephyr_platform.c）
 * 调用 Zephyr ≥3.x 已移除的 __stdout_hook_install（旧 printf 钩子机制）；
 * Zephyr 4.4 下 printk 原生可用，钩子无需安装——本垫片仅满足链接符号。
 * picolibc 的 Zephyr 集成自带同名符号（lib/libc/picolibc/stdio.c），垫片仅对
 * 无该实现的 libc（minimal-libc，native_sim 基线）编译（xiao_esp32s3 实证 2026-09-26）。
 * 升级 WAMR 后若平台层不再引用，可移除（撤垫片须重建复测，DR-22 纪律）。 */
#include <zephyr/kernel.h>

#if !defined(CONFIG_PICOLIBC)
void __stdout_hook_install(int (*hook)(int));

void __stdout_hook_install(int (*hook)(int))
{
	ARG_UNUSED(hook);
}
#endif
