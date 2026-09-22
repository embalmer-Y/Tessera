/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Tessera firmware application（M1：ts-core + ts-safety 最小闭环）。
 * main 仅启动框架：固定顺序初始化（LLD-ts-core §2）→ 监督空转（LLD-00 §4）。
 */
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <ts/core.h>

int main(void)
{
	printk("Tessera firmware (M1: ts-core + ts-safety)\n");
	ts_core_boot(); /* noreturn */
	CODE_UNREACHABLE;
}
