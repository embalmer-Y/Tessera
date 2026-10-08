/* D6 hysteresis control loop demo
 * ADC mv (inst=0) -> hysteresis (low<76, high>82) -> PWM (inst=1) 1000Hz
 * Demonstrates protection-layer clamp: app_init requests 1000 permille but
 * channel ceiling is 700 permille; host returns negative error (-12) which
 * is logged as the clamp evidence.
 *
 * Constraints:
 *  - wasm32 freestanding, no #include, no WASI, no stdio, no rand/clock
 *  - Decimal ints emitted via hand-rolled loops
 *  - All state is file-scope static (deterministic replay)
 *  - heap_kb=1 satisfies manifest minimum; runtime uses no malloc/heap
 */

extern int ts_log_write(int ctx, int lvl, const char* msg, int len);
extern int ts_adc_read(int ctx, int inst);
extern int ts_pwm_set(int ctx, int inst, int hz, int permille);

static int g_ctx = 0;
static int g_state = 0;          /* 0 = low, 1 = high */
static int g_changes = 0;
static int g_done_logged = 0;    /* latch to keep D6-DONE exactly once */

/* ---- tiny helpers (no libc) -------------------------------------------- */

static int slen(const char *s) {
    int n = 0;
    while (s[n] != 0) n++;
    return n;
}

static void log_str(const char *s) {
    ts_log_write(g_ctx, 3 /*info*/, s, slen(s));
}

/* Append decimal representation of v (signed) to buf starting at *pos.
 * No leading zeros except a single '0' for v==0.
 * Negative numbers are prefixed with '-'. */
static void emit_dec(char *buf, int *pos, int v) {
    char tmp[12];
    int t = 0;
    int neg = 0;

    if (v < 0) {
        neg = 1;
        /* values stay tiny (rc, mv, counts); safe two-step negation */
        v = -v;
    }
    if (v == 0) {
        tmp[t++] = '0';
    } else {
        while (v > 0) {
            tmp[t++] = (char)('0' + (v % 10));
            v = v / 10;
        }
    }
    if (neg) tmp[t++] = '-';

    /* reverse into outbuf */
    while (t > 0) {
        buf[(*pos)++] = tmp[--t];
    }
}

/* ---- exported entry points -------------------------------------------- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    g_ctx = ctx;
    g_state = 0;
    g_changes = 0;
    g_done_logged = 0;

    log_str("d6 init");

    /* Clamp evidence: request 1000 permille, channel ceiling is 700.
     * Host is expected to return negative (-12). Log the evidence verbatim. */
    {
        int rc = ts_pwm_set(g_ctx, 1 /*inst*/, 1000 /*hz*/, 1000 /*permille*/);
        char line[64];
        int p = 0;
        const char *prefix = "d6 clamp rc=";
        for (int i = 0; prefix[i] != 0; i++) line[p++] = prefix[i];
        emit_dec(line, &p, rc);
        line[p] = 0;
        log_str(line);
    }

    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    int mv = ts_adc_read(g_ctx, 0);

    if (mv < 0) {
        /* honest logging: skip this tick on ADC error, do not advance state */
        char line[48];
        int p = 0;
        const char *prefix = "d6 adc err rc=";
        for (int i = 0; prefix[i] != 0; i++) line[p++] = prefix[i];
        emit_dec(line, &p, mv);
        line[p] = 0;
        log_str(line);
        return 0;
    }

    /* Hysteresis: only act on transitions, hold otherwise. */
    if (g_state == 0 && mv > 82) {
        g_state = 1;
        int rc = ts_pwm_set(g_ctx, 1, 1000, 700);

        char line[64];
        int p = 0;
        const char *pfx = "d6 out mv=";
        for (int i = 0; pfx[i] != 0; i++) line[p++] = pfx[i];
        emit_dec(line, &p, mv);
        const char *pfx2 = " duty=700 rc=";
        for (int i = 0; pfx2[i] != 0; i++) line[p++] = pfx2[i];
        emit_dec(line, &p, rc);
        line[p] = 0;
        log_str(line);

        g_changes++;
        if (!g_done_logged && g_changes >= 6) {
            log_str("D6-DONE changes=6");
            g_done_logged = 1;
        }
    } else if (g_state == 1 && mv < 76) {
        g_state = 0;
        int rc = ts_pwm_set(g_ctx, 1, 1000, 0);

        char line[64];
        int p = 0;
        const char *pfx = "d6 out mv=";
        for (int i = 0; pfx[i] != 0; i++) line[p++] = pfx[i];
        emit_dec(line, &p, mv);
        const char *pfx2 = " duty=0 rc=";
        for (int i = 0; pfx2[i] != 0; i++) line[p++] = pfx2[i];
        emit_dec(line, &p, rc);
        line[p] = 0;
        log_str(line);

        g_changes++;
        if (!g_done_logged && g_changes >= 6) {
            log_str("D6-DONE changes=6");
            g_done_logged = 1;
        }
    }
    /* else: dead-band 76..82 inclusive -> hold, no output, no log */

    return 0;
}

__attribute__((export_name("app_evt")))
int app_evt(int payload) {
    int mv16 = payload & 0xFFFF;
    char buf[32];
    int p = 0;
    const char *pfx = "d6 evt mv=";
    for (int i = 0; pfx[i] != 0; i++) buf[p++] = pfx[i];
    emit_dec(buf, &p, mv16);
    buf[p] = 0;
    log_str(buf);
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void) {
    return 0;
}