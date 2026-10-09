/* demo.d8.lifecycle v1.0.0 — D8 first-stage lifecycle demo: PWM ramp-up.
 * Deterministic, no #include, no stdio, no globals ctors, no rand/clock.
 * Hand-rolled decimal formatter (handles 0 as single '0').
 * Every log line emitted via a single ts_log_write with full length.
 * All PWM ctx args follow the spec shorthand: literal 0.
 */

extern int ts_pwm_set(int ctx, int inst, int hz, int permille);
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* File-scope static state (DEC-9 deterministic). */
static int g_duty;
static int g_tick_cnt;
static int g_done;
static int g_last_keep_rc;

/* Append decimal of v (>=0) into buf at *pos, advance *pos.
 * Handles v==0 as a single '0'. Uses do-while so 0 is covered.
 */
static void append_int(char *buf, int *pos, int v) {
    unsigned int u;
    char tmp[16];
    int n = 0;
    int i;
    int j;
    if (v < 0) {
        buf[(*pos)++] = '-';
        u = (unsigned int)(-(long long)v);
    } else {
        u = (unsigned int)v;
    }
    do {
        tmp[n++] = (char)('0' + (int)(u % 10u));
        u /= 10u;
    } while (u != 0u);
    for (i = 0, j = n - 1; i < n; ++i, --j) {
        buf[(*pos)++] = tmp[j];
    }
}

/* Append a C string into buf at *pos, advance *pos. */
static void append_str(char *buf, int *pos, const char *s) {
    while (*s != 0) {
        buf[(*pos)++] = *s++;
    }
}

/* ---------- logs (single ts_log_write per line) ---------- */

static void log_init(void) {
    const char *m = "d8 v1 init";
    int len = 0;
    while (m[len] != 0) {
        ++len;
    }
    ts_log_write(0, 3, m, len);
}

static void log_out_step(int duty, int rc) {
    char buf[64];
    int p = 0;
    append_str(buf, &p, "d8 out duty=");
    append_int(buf, &p, duty);
    append_str(buf, &p, " rc=");
    append_int(buf, &p, rc);
    ts_log_write(0, 3, buf, p);
}

static void log_done_at700(void) {
    const char *m = "D8-DONE v1 at700";
    int len = 0;
    while (m[len] != 0) {
        ++len;
    }
    ts_log_write(0, 3, m, len);
}

static void log_keep(int duty, int rc) {
    char buf[64];
    int p = 0;
    append_str(buf, &p, "d8 keep duty=");
    append_int(buf, &p, duty);
    append_str(buf, &p, " rc=");
    append_int(buf, &p, rc);
    ts_log_write(0, 3, buf, p);
}

/* ---------- exports ---------- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    (void)ctx;
    g_duty = 0;
    g_tick_cnt = 0;
    g_done = 0;
    g_last_keep_rc = -1;
    log_init();
    (void)ts_pwm_set(0, 1, 1000, 0);
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    g_tick_cnt = g_tick_cnt + 1;

    if ((g_tick_cnt % 10) == 0) {
        if (g_duty < 700) {
            int r;
            g_duty = g_duty + 100;
            r = ts_pwm_set(0, 1, 1000, g_duty);
            log_out_step(g_duty, r);
            if (g_duty == 700 && g_done == 0) {
                g_done = 1;
                log_done_at700();
            }
        } else if (g_done != 0) {
            int r2 = ts_pwm_set(0, 1, 1000, g_duty);
            if (r2 != g_last_keep_rc) {
                g_last_keep_rc = r2;
                log_keep(g_duty, r2);
            }
        }
    }

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