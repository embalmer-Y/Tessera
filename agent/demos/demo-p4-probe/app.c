/* demo.p4w.probe — P4-W2 部署链探针（V0.14.0）
 * log-only：物理域零申请（P4 画像引脚级事实未采期——HW-4 门语义自洽；
 * caps=[log:write:0] 不涉物理核对）。判据行：
 *   app_init → "P4W2 PROBE INIT"
 *   app_tick → "P4W2 PROBE ALIVE t=<秒>"
 * 合同内化：无 #include、手写十进制、禁随机/墙钟（时间经 ts_time_ms）。
 */
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);
extern unsigned long long ts_time_ms(int ctx);

static int g_n = 0;

static int put_str(const char* s) {
    int n = 0;
    while (s[n] != 0) n = n + 1;
    ts_log_write(0, 3, s, n);
    return n;
}

static int put_u32(unsigned int v, char* buf) {
    char tmp[12];
    int n = 0;
    int i;
    if (v == 0u) { buf[0] = '0'; return 1; }
    while (v != 0u) {
        tmp[n] = (char)('0' + (int)(v % 10u));
        n = n + 1;
        v = v / 10u;
    }
    for (i = 0; i < n; i = i + 1) {
        buf[i] = tmp[n - 1 - i];
    }
    return n;
}

int health_ping(void) { return 0; }

int app_init(int ctx) {
    g_n = 0;
    put_str("P4W2 PROBE INIT");
    return 0;
}

int app_tick(int ctx) {
    char buf[48];
    int n = 0;
    int i;
    unsigned int t;
    const char* p1 = "P4W2 PROBE ALIVE t=";
    const char* p2 = "s";

    g_n = g_n + 1;
    if (g_n != 1) { return 0; }  /* 首个 tick 打一行——判据面收敛 */
    t = (unsigned int)(ts_time_ms(0) / 1000u);
    for (i = 0; p1[i] != 0; i = i + 1) { buf[n] = p1[i]; n = n + 1; }
    n = n + put_u32(t, buf + n);
    for (i = 0; p2[i] != 0; i = i + 1) { buf[n] = p2[i]; n = n + 1; }
    ts_log_write(0, 3, buf, n);
    return 0;
}

int app_evt(int v) { (void)v; return 0; }
