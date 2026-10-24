/*
 * main.c
 *
 * AG7 thermo hysteresis multi-file demo (D-AG7):
 *   - app_init     only ts_log("ag7 init")
 *   - app_tick     100ms period: read ADC, hysteresis decision,
 *                  write GPIO, count cycles, KV save every 20 ticks,
 *                  log terminal state at cycles>=200
 *   - app_evt      no-op
 *   - health_ping  returns 0 always (terminal state is expressed
 *                  via ts_log, NOT via health_ping return value)
 *
 * Natives used (aligned with manifest caps):
 *   ts_adc_read, ts_gpio_write, ts_kv_save, ts_log_write
 *
 * Explicitly forbidden symbols (spec safety statement):
 *   - no rand, time, clock, fopen, socket, av symbols
 *   - no ts_fs_*, ts_net_publish, ts_av_capture
 *   - no global ctor (no <stdio>/<stdlib>)
 *   - buffers all static, <=16B; manual decimal conversion
 */

#include "include/thermo.h"

/* ---- natives (signatures strictly match host ABI) ---- */
extern int ts_adc_read(int ctx, int inst);
extern int ts_gpio_write(int ctx, int inst, int v);
extern int ts_kv_save(int ctx, const char* buf, int len);
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* ---- internal utility: int -> ASCII (no sprintf; deterministic) ---- */
/* buf at least 12B; returns bytes written (no terminating NUL counted). */
static int fmt_int(char* buf, int cap, int v)
{
    int i = 0;
    int n = 0;
    int neg = 0;
    char local[12];

    if (buf == 0 || cap <= 0) {
        return 0;
    }

    if (v < 0) {
        neg = 1;
        v = -v;
    }

    if (v == 0) {
        local[i++] = '0';
    } else {
        while (v > 0 && i < (int)sizeof(local)) {
            local[i++] = (char)('0' + (v % 10));
            v /= 10;
        }
    }
    n = i;

    /* reverse into buf. */
    if (neg) {
        if (n + 1 >= cap) return 0;
        buf[0] = '-';
        i = 1;
    } else {
        i = 0;
    }
    while (i < n + neg && i + 1 < cap) {
        buf[i] = local[n - 1 - (i - neg)];
        i++;
    }
    buf[i] = '\0';
    return i;
}

/* ---- terminal flag (file-scope; set once) ---- */
static int s_done_logged = 0;

/* ---- export: app_init ---- */
int app_init(int ctx)
{
    /* only log "ag7 init", holds no business state (counters live in thermo.c). */
    static const char msg[] = "ag7 init";
    ts_log_write(ctx, 0, msg, (int)(sizeof(msg) - 1));
    s_done_logged = 0;
    return 0;
}

/* ---- export: app_tick (100ms period scheduled by host) ---- */
int app_tick(void)
{
    int mv;
    int heat_out = 0;
    int cycles;
    int heat_count;
    int i;

    /* after terminal state: no-op, no native calls (deterministic + no re-print). */
    if (s_done_logged != 0) {
        return 0;
    }

    /* 1) read ADC: ctx=0, inst=0. */
    mv = ts_adc_read(0, 0);

    /* 2) hysteresis decision + cycles increment (spec: decision and counting
     *    are owned by thermo_step).
     *    ADC error path (mv<0): cycles still +1, state held, GPIO not written. */
    thermo_step(mv, &heat_out);

    /* 3) write GPIO: ctx=0, inst=0, v=heat_out. Only when mv is valid. */
    if (mv >= 0) {
        ts_gpio_write(0, 0, heat_out);
    }

    /* 4) read accumulated counters (for KV save and terminal log). */
    cycles     = thermo_get_cycles();
    heat_count = thermo_get_heat_on();

    /* 5) every 20 ticks save KV. cycles>=20 and divisible by 20. */
    if (cycles > 0 && (cycles % THERMO_KV_PERIOD) == 0) {
        static char kv_buf[16];
        /* manual decimal conversion cycles -> ASCII (fmt_int, static buf <=16B). */
        i = fmt_int(kv_buf, (int)sizeof(kv_buf), cycles);
        if (i > 0) {
            ts_kv_save(0, kv_buf, i);
        }
    }

    /* 6) terminal state decision. */
    if (cycles >= THERMO_TOTAL_CYCLES) {
        /* manually assemble "AG7 DONE cycles=<n> heat=<n>".
         * Spec literal is "AG7 DONE cycles=200 heat=<n>"; we still use
         * fmt_int so the cycles value reflects the real counter. */
        static char done_buf[48];
        static const char prefix[]  = "AG7 DONE cycles=";
        static const char mid[]     = " heat=";
        int p = 0;
        int n;

        /* prefix */
        for (n = 0; prefix[n] != '\0' && p < (int)sizeof(done_buf) - 1; n++) {
            done_buf[p++] = prefix[n];
        }
        /* cycles -> decimal (use fmt_int, terminal value should be 200). */
        n = fmt_int(done_buf + p, (int)sizeof(done_buf) - p, cycles);
        p += n;
        /* mid */
        for (n = 0; mid[n] != '\0' && p < (int)sizeof(done_buf) - 1; n++) {
            done_buf[p++] = mid[n];
        }
        /* heat_count -> decimal (reuse fmt_int). */
        n = fmt_int(done_buf + p, (int)sizeof(done_buf) - p, heat_count);
        p += n;
        done_buf[p] = '\0';

        ts_log_write(0, 0, done_buf, p);
        s_done_logged = 1;
    }

    return 0;
}

/* ---- export: app_evt (unused; no-op) ---- */
int app_evt(int v)
{
    (void)v;
    return 0;
}

/* ---- export: health_ping (returns 0 always) ----
 * Business completion is expressed via ts_log line ("AG7 DONE ...");
 * health_ping return value carries no business information -- 0 = healthy.
 */
int health_ping(void)
{
    return 0;
}