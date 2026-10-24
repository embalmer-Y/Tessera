/* demo.d8.lifecycle v2.1.0 — D8 rollback trigger (bad version) */

static int g_ctx = 0;

/* ---------- extern host natives (whitelist) ---------- */
extern int ts_pwm_set(int ctx, int inst, int hz, int permille);
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* ---------- required exports (manifest.exports) ---------- */
__attribute__((export_name("app_init")))
int app_init(int ctx) {
    g_ctx = ctx;
    ts_log_write(ctx, 3, "d8bad init", 10);
    /* one-shot PWM silence on inst 1 (return ignored per spec) */
    ts_pwm_set(ctx, 1, 1000, 0);
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    static unsigned int cnt = 0;
    static unsigned int mod10 = 0;

    mod10++;
    if (mod10 >= 10) {
        mod10 = 0;
        cnt++;

        /* build "d8bad alive cnt=<n>\n" into stack buffer, single write */
        const char prefix[] = "d8bad alive cnt=";
        char line[40];
        int i = 0;

        /* prefix copy */
        for (int k = 0; prefix[k] != 0; k++) {
            line[i++] = prefix[k];
        }

        /* decimal n: do-while remainder/div, handles 0 correctly (first '0') */
        {
            unsigned int x = cnt;
            char tmp[12];
            int t = 0;
            do {
                tmp[t++] = (char)('0' + (x % 10));
                x /= 10;
            } while (x != 0);
            /* reverse into line */
            while (t > 0) {
                line[i++] = tmp[--t];
            }
        }

        line[i++] = '\n';

        ts_log_write(g_ctx, 3, line, i);
    }
    return 0;
}

__attribute__((export_name("app_evt")))
int app_evt(int v) {
    /* no-op per spec */
    (void)v;
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void) {
    /* deliberately sick — host fails 3x -> D8 health rollback */
    return 1;
}