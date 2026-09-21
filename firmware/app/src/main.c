/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Tessera firmware application skeleton (M0).
 * 框架子系统自 M1 起按 design/LLD-* 落地；此处仅验证构建接线。
 */
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

int main(void)
{
	printk("Tessera firmware skeleton (M0)\n");
	return 0;
}
