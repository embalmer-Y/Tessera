/* D4: ADC acquisition + change-report demo
 * - app_init: log "d4 init"
 * - app_evt(payload): payload hi16 = input instance, lo16 = new sample mV;
 *   log "d4 evt inst=<i> mv=<v>"
 * - app_tick (100ms): ts_adc_read(ctx=0, inst=0); |mv-last_reported|>=20
 *   or last_reported<0 triggers report; reports>=8 logs "D4-DONE reports=8" once
 * - health_ping returns 0
 * - caps = ["adc:read:0"]
 * Constraints: hand-written decimal conversion; deterministic; no #include.
 */

/* ---------- Host-provided natives (declared, not defined) ---------- */
extern int ts_adc_read(int ctx, int inst);
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* ---------- File-scope state (no globals with ctors) ---------- */
static int g_last_reported = -1;   /* -1 sentinel: first sample always reported */
static int g_reports       = 0;    /* count of reports emitted */
static int g_done_logged   = 0;    /* one-shot guard for D4-DONE */

/* ---------- Hand-written unsigned decimal to ASCII ---------- */
/* Writes digits into buf (no NUL). Returns number of chars written.
 * Handles v == 0 by writing single '0'. */
static int u32_to_dec(char* buf, unsigned int v) {
    char tmp[12]; /* enough for 32-bit unsigned (max 4294967295 = 10 digits) + spare */
    int n = 0;
    int i;
    int j;
    if (v == 0u) {
        buf[0] = '0';
        return 1;
    }
    while (v > 0u) {
        tmp[n] = (char)('0' + (int)(v % 10u));
        v = v / 10u;
        n++;
    }
    /* reverse */
    for (i = 0, j = n - 1; i < j; i++, j--) {
        char t = tmp[i];
        tmp[i] = tmp[j];
        tmp[j] = t;
    }
    for (i = 0; i < n; i++) buf[i] = tmp[i];
    return n;
}

/* ---------- Hand-written signed decimal to ASCII ---------- */
/* Writes ASCII digits (with leading '-' if negative) into buf. Returns length.
 * Handles INT_MIN by negation-safe path (cast through unsigned to avoid UB). */
static int i32_to_dec(char* buf, int v) {
    int len = 0;
    unsigned int uv;
    if (v < 0) {
        buf[len++] = '-';
        /* Negate via unsigned to avoid INT_MIN overflow */
        uv = (unsigned int)(0u - (unsigned int)v);
    } else {
        uv = (unsigned int)v;
    }
    len += u32_to_dec(buf + len, uv);
    return len;
}

/* ---------- Log helper ---------- */
/* Lvl: 0=info,1=warn,2=err (host convention; demo keeps it simple) */
static void log_str(int lvl, const char* s, int len) {
    (void)ts_log_write(0, lvl, s, len);
}

/* ---------- Exported entries ---------- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    const char m[] = {'d','4',' ','i','n','i','t'};
    (void)ctx;
    log_str(0, m, (int)(sizeof(m)));
    /* Deterministic reset of state (no ctors) */
    g_last_reported = -1;
    g_reports       = 0;
    g_done_logged   = 0;
    return 0;
}

__attribute__((export_name("app_evt")))
int app_evt(int payload) {
    /* payload: hi16 = input instance, lo16 = new sample mV (signed 16-bit) */
    int inst   = (payload >> 16) & 0xFFFF;
    int mv_raw = payload & 0xFFFF;
    /* Sign-extend low 16 bits to a signed int */
    if ((mv_raw & 0x8000) != 0) mv_raw = mv_raw - 0x10000;
    /* mv_raw now in [-32768, 32767] */
    {
        char b[80];
        int  n = 0;
        /* prefix "d4 evt inst=" */
        const char p1[] = {'d','4',' ','e','v','t',' ','i','n','s','t','='};
        int i;
        for (i = 0; i < (int)(sizeof(p1)); i++) b[n++] = p1[i];
        n += i32_to_dec(b + n, inst);
        b[n++] = ' ';
        /* "mv=" */
        b[n++] = 'm'; b[n++] = 'v'; b[n++] = '=';
        n += i32_to_dec(b + n, mv_raw);
        log_str(0, b, n);
    }
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    int rc;
    int mv;
    int delta;
    char b[96];
    int  n = 0;
    const char p_rep[]   = {'d','4',' ','r','e','p','o','r','t',' ','m','v','='};
    const char p_delta[] = {' ','d','e','l','t','a','='};
    const char p_done[]  = {'D','4','-','D','O','N','E',' ','r','e','p','o','r','t','s','=','8'};
    int i;

    rc = ts_adc_read(0, 0);
    if (rc < 0) {
        /* Error path: log mv=<rc> deterministically, skip this tick */
        const char p_err[] = {'d','4',' ','a','d','c',' ','e','r','r',' ','m','v','='};
        char eb[64];
        int  en = 0;
        for (i = 0; i < (int)(sizeof(p_err)); i++) eb[en++] = p_err[i];
        en += i32_to_dec(eb + en, rc);
        log_str(1, eb, en); /* warn */
        return 0;
    }
    mv = rc; /* mV, >=0 on success per contract */

    /* Compute |mv - last_reported| using safe unsigned diff. */
    {
        unsigned int a = (unsigned int)mv;
        unsigned int b0 = (unsigned int)g_last_reported;
        delta = (int)(a - b0); /* wraps mod 2^32, but inputs fit signed-16 range so OK */
        if (delta < 0) delta = -delta;
    }

    if (g_last_reported < 0 || delta >= 20) {
        /* Report path */
        for (i = 0; i < (int)(sizeof(p_rep)); i++) b[n++] = p_rep[i];
        n += i32_to_dec(b + n, mv);
        for (i = 0; i < (int)(sizeof(p_delta)); i++) b[n++] = p_delta[i];
        n += i32_to_dec(b + n, delta);
        log_str(0, b, n);

        g_last_reported = mv;
        g_reports += 1;

        if (g_reports >= 8 && g_done_logged == 0) {
            log_str(0, p_done, (int)(sizeof(p_done)));
            g_done_logged = 1;
        }
    }
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void) {
    return 0;
}
