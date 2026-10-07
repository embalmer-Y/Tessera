/*
 * D-AV demo: camera capture + chunked publish.
 * File-scope state, hand-rolled decimal conversion, zero #include.
 */

extern int ts_av_capture(int ctx, char* buf, int cap);
extern int ts_net_publish(int ctx, int frame_id, int chunk_id, int n_chunks, const char* buf, int len);
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* File-scope state (deterministic, no globals init, no rand/clock). */
static char frame_buf[38400];                 /* 160*120*2 = 38400 RGB565 max */
static int  state;                            /* 0=idle/capture, 1=publish, 2=done */
static int  frame_len;
static int  chunk_idx;
static int  n_chunks;
static int  frame_id;
static int  frames_sent;
static int  total_bytes;

/* Hand-rolled strlen (no <string.h>). */
static int slen(const char *s) {
    int n = 0;
    while (s[n] != 0) n++;
    return n;
}

/* Append decimal value of v (signed) into out[*p]; advances *p. No leading zeros. */
static void append_dec(char *out, int *p, int v) {
    char tmp[12];
    int  t = 0;
    int  neg = 0;
    unsigned int u;

    if (v < 0) {
        neg = 1;
        u = (unsigned int)(-(v + 1)) + 1u;   /* safe for INT_MIN */
    } else {
        u = (unsigned int)v;
        neg = 0;
    }

    if (u == 0u) {
        tmp[t++] = '0';
    } else {
        while (u > 0u) {
            tmp[t++] = (char)('0' + (int)(u % 10u));
            u = u / 10u;
        }
    }
    if (neg) tmp[t++] = '-';
    while (t > 0) out[(*p)++] = tmp[--t];
}

/* ---- log helpers (prefix-only or prefix+decimal, newline terminated) ---- */

static void log_init(void) {
    static const char M[] = "dav init";
    char line[16];
    int i, p = 0;
    for (i = 0; i < (int)(sizeof(M) - 1); i++) line[p++] = M[i];
    line[p++] = '\n';
    ts_log_write(0, 3, line, p);
}

static void log_cap_rc(int rc) {
    static const char P[] = "dav cap-rc=";
    char line[32];
    int i, p = 0;
    for (i = 0; i < (int)(sizeof(P) - 1); i++) line[p++] = P[i];
    append_dec(line, &p, rc);
    line[p++] = '\n';
    ts_log_write(0, 3, line, p);
}

static void log_pub_rc(int rc) {
    static const char P[] = "dav pub-rc=";
    char line[32];
    int i, p = 0;
    for (i = 0; i < (int)(sizeof(P) - 1); i++) line[p++] = P[i];
    append_dec(line, &p, rc);
    line[p++] = '\n';
    ts_log_write(0, 3, line, p);
}

static void log_frame(int fid, int flen, int nc) {
    static const char P[] = "dav frame ";
    static const char M1[] = " len ";
    static const char M2[] = " chunks ";
    char line[64];
    int i, p = 0;
    for (i = 0; i < (int)(sizeof(P) - 1); i++) line[p++] = P[i];
    append_dec(line, &p, fid);
    for (i = 0; i < (int)(sizeof(M1) - 1); i++) line[p++] = M1[i];
    append_dec(line, &p, flen);
    for (i = 0; i < (int)(sizeof(M2) - 1); i++) line[p++] = M2[i];
    append_dec(line, &p, nc);
    line[p++] = '\n';
    ts_log_write(0, 3, line, p);
}

static void log_done(int bytes) {
    static const char P[] = "DAV-DONE frames=10 bytes=";
    char line[64];
    int i, p = 0;
    for (i = 0; i < (int)(sizeof(P) - 1); i++) line[p++] = P[i];
    append_dec(line, &p, bytes);
    line[p++] = '\n';
    ts_log_write(0, 3, line, p);
}

/* ---- exports ---- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    (void)ctx;
    state       = 0;
    frame_len   = 0;
    chunk_idx   = 0;
    n_chunks    = 0;
    frame_id    = 0;
    frames_sent = 0;
    total_bytes = 0;
    log_init();
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    int len, rc, clen, off;

    if (state == 2) {
        /* Permanent idle after completion. */
        return 0;
    }

    if (state == 0) {
        len = ts_av_capture(0, frame_buf, (int)sizeof(frame_buf));
        if (len < 0) {
            log_cap_rc(len);
            return 0;                       /* stay in state 0 */
        }
        if (len == 0) {
            return 0;                       /* empty frame, stay in state 0 */
        }
        /* Begin a new frame. */
        frame_id = frame_id + 1;
        n_chunks  = (len + 1023) / 1024;
        chunk_idx = 0;
        frame_len = len;
        state     = 1;
        return 0;                           /* publish starts next tick */
    }

    /* state == 1: publish exactly one chunk per tick. */
    off  = chunk_idx * 1024;
    clen = 1024;
    if ((frame_len - off) < 1024) {
        clen = frame_len - off;
    }

    rc = ts_net_publish(0, frame_id, chunk_idx, n_chunks,
                        (const char *)(frame_buf + off), clen);

    if (rc == -5) {
        /* BUSY: host will retry same chunk next tick. */
        return 0;
    }
    if (rc < 0) {
        log_pub_rc(rc);
        /* Drop frame, return to capture. */
        state     = 0;
        chunk_idx = 0;
        n_chunks  = 0;
        frame_len = 0;
        return 0;
    }

    chunk_idx = chunk_idx + 1;
    if (chunk_idx == n_chunks) {
        /* Frame complete. */
        log_frame(frame_id, frame_len, n_chunks);
        total_bytes = total_bytes + frame_len;
        frames_sent = frames_sent + 1;

        /* Reset per-frame state. */
        chunk_idx = 0;
        n_chunks  = 0;
        frame_len = 0;

        if (frames_sent >= 10) {
            log_done(total_bytes);
            state = 2;                      /* permanent idle */
        } else {
            state = 0;                      /* next tick: capture again */
        }
    }
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void) {
    return 0;
}
