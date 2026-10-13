/* D-PDM: deterministic pcm16 capture & chunked publish demo.
 * Constraints: no #include, no stdlib; all decimal conv hand-rolled;
 * static file-scope state only; deterministic (no rand/wall-clock).
 * All manifest.exports symbols are explicitly attributed. */

/* ---------- file-scope state ---------- */
static int g_state = 0;            /* 0=need frame, 1=publishing chunks, 2=done */
static int g_frame_len = 0;        /* last ts_av_capture returned length */
static int g_chunk_idx = 0;        /* 0..n_chunks-1 */
static int g_n_chunks = 0;         /* 10 per frame */
static int g_frame_id = 0;         /* increments per frame */
static int g_frames_sent = 0;      /* total completed frames */
static int g_total_bytes = 0;      /* sum of frame bytes completed */

static char g_frame_buf[640];      /* 640B pcm16 frame, static in linear memory */

/* ---------- allowed host natives (exact signatures) ---------- */
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);
extern int ts_av_capture(int ctx, char* buf, int cap);
extern int ts_net_publish(int ctx, int frame_id, int chunk_id, int n_chunks,
                          const char* buf, int len);

/* ---------- helpers ---------- */
static int slen(const char* s) {
    int n = 0;
    while (s[n] != 0) n++;
    return n;
}

static void log_str(const char* s) {
    ts_log_write(0, 4, s, slen(s));
}

/* Append non-negative decimal into tmp[off..]; returns new off. */
static int append_u32(char* tmp, int off, unsigned int v) {
    char rev[12];
    int n = 0;
    if (v == 0u) {
        tmp[off++] = '0';
        return off;
    }
    while (v > 0u && n < 11) {
        rev[n++] = (char)('0' + (int)(v % 10u));
        v /= 10u;
    }
    while (n > 0) {
        tmp[off++] = rev[--n];
    }
    return off;
}

/* Append possibly-negative int decimal into tmp[off..]. */
static int append_i32(char* tmp, int off, int v) {
    unsigned int uv;
    if (v < 0) {
        tmp[off++] = '-';
        uv = (unsigned int)(-(v + 1)) + 1u;
    } else {
        uv = (unsigned int)v;
    }
    return append_u32(tmp, off, uv);
}

/* Copy a C string literal (NUL-terminated) into tmp at off; returns new off. */
static int copy_lit(char* tmp, int off, const char* lit) {
    while (*lit != 0) {
        tmp[off++] = *lit++;
    }
    return off;
}

/* ---------- exported entry points ---------- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    (void)ctx;
    g_state = 0;
    g_frame_len = 0;
    g_chunk_idx = 0;
    g_n_chunks = 0;
    g_frame_id = 0;
    g_frames_sent = 0;
    g_total_bytes = 0;
    log_str("dpm init");
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    char tmp[64];

    if (g_state == 2) {
        /* terminal: idle */
        return 0;
    }

    if (g_state == 0) {
        int rc = ts_av_capture(0, g_frame_buf, 640);
        if (rc < 0) {
            int off = 0;
            off = copy_lit(tmp, off, "dpm cap-rc=");
            off = append_i32(tmp, off, rc);
            ts_log_write(0, 3, tmp, off);
            return 0;
        }
        if (rc < 1) {
            return 0;
        }
        g_frame_len = rc;
        g_frame_id++;
        g_n_chunks = 10;
        g_chunk_idx = 0;
        g_state = 1;
        return 0;
    }

    /* state == 1: publish exactly one chunk per tick (64 bytes) */
    {
        int off = (int)(g_chunk_idx * 64);
        const char* chunk_ptr;
        int rc2;

        if (off < 0 || off > 640 - 64) {
            g_state = 0;
            return 0;
        }
        chunk_ptr = g_frame_buf + off;
        rc2 = ts_net_publish(0, g_frame_id, g_chunk_idx, g_n_chunks,
                             chunk_ptr, 64);

        if (rc2 == -5) {
            /* BUSY: retry same chunk next tick */
            return 0;
        }
        if (rc2 < 0) {
            int lo = 0;
            lo = copy_lit(tmp, lo, "dpm pub-rc=");
            lo = append_i32(tmp, lo, rc2);
            ts_log_write(0, 3, tmp, lo);
            g_state = 0;
            return 0;
        }

        g_chunk_idx++;
        if (g_chunk_idx == g_n_chunks) {
            int lo = 0;
            lo = copy_lit(tmp, lo, "dpm frame ");
            lo = append_u32(tmp, lo, (unsigned int)g_frame_id);
            lo = copy_lit(tmp, lo, " len 640 chunks 10");
            ts_log_write(0, 4, tmp, lo);

            g_total_bytes += 640;
            g_frames_sent++;
            if (g_frames_sent >= 10) {
                int lo2 = 0;
                lo2 = copy_lit(tmp, lo2, "DP DONE frames=10 bytes=");
                lo2 = append_u32(tmp, lo2, (unsigned int)g_total_bytes);
                ts_log_write(0, 4, tmp, lo2);
                g_state = 2;
            } else {
                g_state = 0;
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
