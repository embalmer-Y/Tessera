/* led.blink.demo v1.0.0
 * 最小权限 LED 闪烁：app_tick (100ms 周期) 每 10 次翻转 GPIO 实例 0。
 * 写路径唯一：所有 GPIO 输出经 ts_gpio_write，由固件保护层限幅/限流。
 * 确定性：纯计数器分支，无随机/墙钟/容器迭代序依赖。
 * 越权保护：本 APP 仅导入 ts_gpio_write；caps 仅声明 gpio:write:0。
 */
#include <stddef.h>

/* ---- 宿主 natives（签名精确；manifest.caps 仅声明 gpio:write:0） ---- */
extern int ts_gpio_write(int ctx, int inst, int v);

/* ---- file-scope 静态状态（确定性，重放可重现） ---- */
static int s_ctx = 0;            /* 宿主上下文，app_init 时写入 */
static int s_tick_counter = 0;   /* tick 计数器（0..9 循环） */
static int s_led_state = 0;      /* 当前 LED 输出态：0=灭, 1=亮 */

/* ---- 导出：与 manifest.exports 完全一致 ---- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    s_ctx = ctx;
    s_tick_counter = 0;
    s_led_state = 0;
    /* 上电态：输出 0（LED 灭）；所有写经保护层（合同 2） */
    (void)ts_gpio_write(s_ctx, 0, 0);
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    /* 100ms 一次；10 次 = 1.0s 翻转一次；on/off 各 1s = 周期 2s */
    s_tick_counter++;
    if (s_tick_counter >= 10) {
        s_tick_counter = 0;
        s_led_state = s_led_state ? 0 : 1;  /* 0/1 交替，分支确定性 */
        (void)ts_gpio_write(s_ctx, 0, s_led_state);
    }
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void) {
    return 0;
}