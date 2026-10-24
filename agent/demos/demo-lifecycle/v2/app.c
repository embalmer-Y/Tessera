/* demo.d8.lifecycle v2 — PWM ramp-down lifecycle demo
 * Deterministic, no #include, no itoa/printf. Manual decimal emit.
 */

static int  g_duty  = 700;
static int  g_tick  = 0;
static int  g_done  = 0;
static int  g_last  = -1;   /* last rc from idempotent re-assert, init to sentinel */

extern int  ts_pwm_set(int ctx, int inst, int hz, int permille);
extern int  ts_log_write(int ctx, int lvl, const char* msg, int len);

/* ---- manual decimal -> ASCII (handles 0 correctly via do/while) ---- */
static int emit_u32(char* out, unsigned int v) {
    char tmp[12];
    int  n = 0;
    int  i = 0;
    if (v == 0u) {
        out[0] = '0';
        return 1;
    }
    while (v > 0u) {
        unsigned int q = v / 10u;
        unsigned int r = v - q * 10u;
        tmp[i++] = (char)('0' + (int)r);
        v = q;
    }
    n = i;
    /* reverse */
    for (i = 0; i < n; ++i) out[i] = tmp[n - 1 - i];
    return n;
}

static int emit_i32(char* out, int v) {
    int n = 0;
    if (v < 0) { out[n++] = '-'; v = -v; }
    n += emit_u32(out + n, (unsigned int)v);
    return n;
}

/* ---- log helpers: build full line, write once ---- */
static void log_str(int ctx, int lvl, const char* s) {
    int n = 0;
    while (s[n] != '\0') ++n;
    ts_log_write(ctx, lvl, s, n);
}

static void log_init(int ctx) {
    char buf[64];
    int  n = 0;
    /* "d8 v2 init" */
    const char* p = "d8 v2 init";
    while (*p != '\0') buf[n++] = *p++;
    ts_log_write(ctx, 1, buf, n);
}

static void log_duty_rc(int ctx, int duty_v, int rc_v) {
    char buf[96];
    int  n = 0;
    /* prefix: "d8 out duty=" */
    const char* p1 = "d8 out duty=";
    while (*p1 != '\0') buf[n++] = *p1++;
    n += emit_i32(buf + n, duty_v);
    /* " rc=" */
    {
        const char* p2 = " rc=";
        while (*p2 != '\0') buf[n++] = *p2++;
    }
    n += emit_i32(buf + n, rc_v);
    ts_log_write(ctx, 1, buf, n);
}

static void log_done(int ctx) {
    char buf[64];
    int  n = 0;
    /* "D8-DONE v2 at0" */
    const char* p = "D8-DONE v2 at0";
    while (*p != '\0') buf[n++] = *p++;
    ts_log_write(ctx, 1, buf, n);
}

static void log_keep(int ctx, int duty_v, int rc_v) {
    char buf[96];
    int  n = 0;
    /* "d8 keep duty=" */
    const char* p1 = "d8 keep duty=";
    while (*p1 != '\0') buf[n++] = *p1++;
    n += emit_i32(buf + n, duty_v);
    /* " rc=" */
    {
        const char* p2 = " rc=";
        while (*p2 != '\0') buf[n++] = *p2++;
    }
    n += emit_i32(buf + n, rc_v);
    ts_log_write(ctx, 1, buf, n);
}

/* ---- exports ---- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    g_duty = 700;
    g_tick = 0;
    g_done = 0;
    g_last = -1;
    /* initial pump (return value intentionally ignored) */
    (void)ts_pwm_set(0, 1, 1000, 700);
    log_init(ctx);
    return 0;
}

__attribute__((export_name("app_evt")))
int app_evt(int v) {
    (void)v;
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void) {
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    g_tick = g_tick + 1;
    if (g_done == 0) {
        if ((g_tick % 10) == 0) {
            if (g_duty > 0) {
                g_duty = g_duty - 100;
                int r = ts_pwm_set(0, 1, 1000, g_duty);
                log_duty_rc(0, g_duty, r);
                if (g_duty == 0) {
                    g_done = 1;
                    log_done(0);
                }
            }
        }
    } else {
        if ((g_tick % 10) == 0) {
            int r = ts_pwm_set(0, 1, 1000, g_duty);
            if (r != g_last) {
                g_last = r;
                log_keep(0, g_duty, r);
            }
        }
    }
    return 0;
}
