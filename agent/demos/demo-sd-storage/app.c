/* D-SD: deterministic SD read/write safety demo.
 * Zero #include, zero libc. All strlen / memcmp / substring done by hand.
 * Path/data buffers live in wasm linear memory (static or stack).
 * State machine advances one step per app_tick; stops on step 5.
 * Out-of-whitelist path is expected to return negative error and is logged as-is.
 */

static const char PATH_TARGET[]   = "/SD:/apps-data/dsd.txt";
static const char PATH_DENY[]    = "/SD:/etc/dsd-deny.txt";
static const char PATH_LISTDIR[] = "/SD:/apps-data";
static const char PATH_DONE[]    = "/SD:/apps-data/dsd-done.txt";

static char PAYLOAD[68];        /* "DSD-" + 64 digit chars = 68 bytes */
static char RBUF[68];           /* read-back buffer */
static char LBUF[256];          /* fs_list output buffer */

static int g_state = 0;         /* file-scope state machine */
static int g_ctx   = 0;         /* host context */

/* ---------- imported host natives ---------- */
extern int ts_fs_write(int ctx, const char* path, int path_len, int off,
                       const char* data, int len);
extern int ts_fs_read (int ctx, const char* path, int path_len, int off,
                       char* buf, int cap);
extern int ts_fs_list (int ctx, const char* dir, int dir_len, char* out, int cap);
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* ---------- tiny helpers (no libc) ---------- */
static int my_strlen(const char* s) {
    int n = 0;
    while (s[n] != 0) n++;
    return n;
}

/* Append exactly n bytes of s into buf starting at *pos; *pos advances.
 * No NUL terminator assumed; caller controls length. */
static void append_n(char* buf, int* pos, const char* s, int n) {
    int i;
    for (i = 0; i < n; i++) buf[(*pos)++] = s[i];
}

/* Append a non-negative decimal to its string (no libc). */
static void append_dec(char* buf, int* pos, int v) {
    char tmp[16];
    int  t = 0;
    int  started = 0;
    int  i;
    if (v == 0) {
        buf[(*pos)++] = '0';
        return;
    }
    if (v < 0) { buf[(*pos)++] = '-'; v = -v; }
    while (v > 0 && t < 16) { tmp[t++] = (char)('0' + (v % 10)); v /= 10; }
    started = t;
    for (i = t - 1; i >= 0; i--) buf[(*pos)++] = tmp[i];
    (void)started;
}

/* Hand-rolled substring search (no strstr). Returns1 if needle found in hay[0..hlen). */
static int contains_substr(const char* hay, int hlen, const char* needle) {
    int nlen = my_strlen(needle);
    int i;
    if (nlen == 0) return 1;
    if (nlen > hlen) return 0;
    for (i = 0; i <= hlen - nlen; i++) {
        int j;
        int ok = 1;
        for (j = 0; j < nlen; j++) {
            if (hay[i + j] != needle[j]) { ok = 0; break; }
        }
        if (ok) return 1;
    }
    return 0;
}

/* Build the deterministic 68-byte payload once. */
static void build_payload(void) {
    int i;
    /* "DSD-" */
    PAYLOAD[0] = 'D'; PAYLOAD[1] = 'S'; PAYLOAD[2] = 'D'; PAYLOAD[3] = '-';
    for (i = 0; i < 64; i++) {
        PAYLOAD[4 + i] = (char)('0' + (i % 10));
    }
}

/* ---------- required exports ---------- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    char msg[16];
    int  pos = 0;
    g_ctx = ctx;
    build_payload();
    g_state = 0;
    /* "dsd init" (8 bytes) */
    append_n(msg, &pos, "dsd init", 8);
    ts_log_write(g_ctx, 0 /*INFO*/, msg, pos);
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    /* If we've already finished, stay idle. */
    if (g_state >= 5) return 0;

    if (g_state == 0) {
        /* Step 1: write 68 bytes to whitelisted file. */
        int rc;
        char msg[40];
        int  pos = 0;
        int  p_len = my_strlen(PATH_TARGET);
        rc = ts_fs_write(g_ctx, PATH_TARGET, p_len, 0, PAYLOAD, 68);
        /* "dsd wr-rc=" + decimal */
        append_n(msg, &pos, "dsd wr-rc=", 10);
        append_dec(msg, &pos, rc);
        ts_log_write(g_ctx, 0, msg, pos);
        g_state = 1;
        return 0;
    }

    if (g_state == 1) {
        /* Step 2: read back 68, log match byte 0 = consistent. */
        int rc;
        int i;
        int match = 1;
        char msg[32];
        int  pos = 0;
        int  p_len = my_strlen(PATH_TARGET);
        rc = ts_fs_read(g_ctx, PATH_TARGET, p_len, 0, RBUF, 68);
        if (rc != 68) { match = 0; }
        for (i = 0; i < 68; i++) {
            if (RBUF[i] != PAYLOAD[i]) { match = 0; break; }
        }
        /* "dsd verify " + match */
        append_n(msg, &pos, "dsd verify ", 11);
        msg[pos++] = (char)('0' + (match ? 0 : 1));
        ts_log_write(g_ctx, 0, msg, pos);
        g_state = 2;
        return 0;
    }

    if (g_state == 2) {
        /* Step 3: write to /SD:/etc/dsd-deny.txt (NOT whitelisted).
         * Expected: negative error code, logged as-is (no retry). */
        int rc;
        char msg[40];
        int  pos = 0;
        int  p_len = my_strlen(PATH_DENY);
        rc = ts_fs_write(g_ctx, PATH_DENY, p_len, 0, "X", 1);
        /* "dsd deny-rc=" + signed decimal */
        append_n(msg, &pos, "dsd deny-rc=", 12);
        append_dec(msg, &pos, rc);
        ts_log_write(g_ctx, 0, msg, pos);
        g_state = 3;
        return 0;
    }

    if (g_state == 3) {
        /* Step 4: list /SD:/apps-data and check for "dsd.txt" via hand-rolled loop. */
        int rc;
        int hit;
        char msg[48];
        int  pos = 0;
        int  d_len = my_strlen(PATH_LISTDIR);
        rc = ts_fs_list(g_ctx, PATH_LISTDIR, d_len, LBUF, 256);
        hit = contains_substr(LBUF, (rc < 0 ? 0 : rc), "dsd.txt");
        /* "dsd list-rc=" + dec + " hit=" + dec */
        append_n(msg, &pos, "dsd list-rc=", 12);
        append_dec(msg, &pos, rc);
        append_n(msg, &pos, " hit=", 5);
        append_dec(msg, &pos, hit);
        ts_log_write(g_ctx, 0, msg, pos);
        g_state = 4;
        return 0;
    }

    if (g_state == 4) {
        /* Step 5: write "OK" to done file; afterwards all ticks are idle. */
        int rc;
        char msg[24];
        int  pos = 0;
        int  p_len = my_strlen(PATH_DONE);
        rc = ts_fs_write(g_ctx, PATH_DONE, p_len, 0, "OK", 2);
        (void)rc;
        append_n(msg, &pos, "dsd done", 8);
        ts_log_write(g_ctx, 0, msg, pos);
        g_state = 5;
        return 0;
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
