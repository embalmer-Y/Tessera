/* demo.pwm.breath — PWM breathing-light demo
 * Contract: caps = ["pwm:set:1"]; exports = health_ping, app_tick.
 * 100ms per tick; duty ramp +25 permille/tick, wrap at 1000.
 * >700 permille is clamped by the framework guard layer (expected demo).
 * Deterministic: state = tick counter only; no RNG/wall-clock.
 */
#include <stdint.h>

/* ---- host natives (precise signatures, no other imports allowed) ---- */
extern int ts_pwm_set(int ctx, int inst, int hz, int permille);

#define PWM_INST      1
#define PWM_HZ        1000
#define DUTY_STEP     25      /* permille per tick (100ms) */
#define DUTY_MAX      1000    /* wrap point, modulo */

static int g_ctx = 0;

/* ---- exports ---- */

int app_init(int ctx) __attribute__((export_name("app_init")));
int app_tick(void)    __attribute__((export_name("app_tick")));
int app_evt(int v)    __attribute__((export_name("app_evt")));
int health_ping(void) __attribute__((export_name("health_ping")));

/* ---- state ---- */
static int g_tick = 0;        /* monotonic tick count, deterministic */

int app_init(int ctx) {
    g_ctx = ctx;
    g_tick = 0;
    /* fail-safe: known-safe output on entry */
    (void)ts_pwm_set(g_ctx, PWM_INST, PWM_HZ, 0);
    return 0;
}

int health_ping(void) {
    return 0;
}

int app_evt(int v) {
    (void)v;
    /* no events subscribed; deterministic no-op */
    return 0;
}

int app_tick(void) {
    int duty = (g_tick * DUTY_STEP) % (DUTY_MAX + DUTY_STEP);
    /* fold the tail band [1000, 1025) into 0..0 to honor wrap-to-zero semantics */
    if (duty > DUTY_MAX) duty = 0;
    (void)ts_pwm_set(g_ctx, PWM_INST, PWM_HZ, duty);
    g_tick++;
    return 0;
}