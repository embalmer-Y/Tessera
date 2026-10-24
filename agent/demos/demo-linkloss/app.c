/* demo.d9.linkloss — D9 断链 fail-safe 与自愈演示
 * ADC 输入 → 滞回逻辑 → PWM 输出
 * 合同内化：禁随机/墙钟（合同 9）、输出必经保护层（合同 2）、
 *           越权拒绝留痕（合同 10）、健康探针必导出（技能约束）。
 * 无 #include；手写十进制；无全局构造。
 */

static int g_state    = 0;     /* 0=低, 1=高 */
static int g_target   = 350;   /* 当前目标 permille */
static int g_last_rc  = 0;
static int g_armed    = 0;
static int g_recovered= 0;
static int g_done     = 0;

/* 宿主 natives：仅声明用到的；签名精确 */
extern int ts_pwm_set(int ctx, int inst, int hz, int permille);
extern int ts_adc_read(int ctx, int inst);
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* 手写十进制 int32 → 输出到 buf，返回长度；0 输出 "0"。 */
static int fmt_i32(int v, char* buf) {
    char tmp[12];
    int n = 0;
    int neg = 0;
    unsigned int u;
    int i;

    if (v == 0) {
        buf[0] = '0';
        return 1;
    }
    if (v < 0) {
        neg = 1;
        /* 对 -2147483648 特判：转成无符号后取反再加 1 的字符串形式；
         * 本 APP 输入域 mv<0 时直接返回，target 非负，所以不会到这里。
         * 仍做一般化处理：取反再加 1。 */
        u = (unsigned int)(-(v + 1));
        u = u + 1u;
    } else {
        u = (unsigned int)v;
    }

    /* do { 取余再除 }，确保 0 不进循环正确性 */
    do {
        tmp[n++] = (char)('0' + (int)(u % 10u));
        u = u / 10u;
    } while (u != 0u);

    if (neg) tmp[n++] = '-';

    /* 反序写回 buf */
    for (i = 0; i < n; i++) {
        buf[i] = tmp[n - 1 - i];
    }
    return n;
}

static void log_str(const char* s, int len) {
    ts_log_write(0, 0, s, len);
}

/* 拼一行带一个 int 的日志 */
static int log_line_int(const char* prefix, int prefix_len,
                        const char* mid, int mid_len,
                        int value,
                        const char* suffix, int suffix_len,
                        char* line) {
    int p = 0;
    int k;
    for (k = 0; k < prefix_len; k++) line[p++] = prefix[k];
    for (k = 0; k < mid_len; k++)   line[p++] = mid[k];
    p += fmt_i32(value, line + p);
    for (k = 0; k < suffix_len; k++) line[p++] = suffix[k];
    return p;
}

/* "d9 flip up mv=<mv>" */
static int line_flip_up(int mv, char* line) {
    static const char p[] = "d9 flip up mv=";
    int pl = (int)(sizeof(p) - 1);
    int p2 = log_line_int(p, pl, "", 0, mv, "", 0, line);
    return p2;
}

/* "d9 flip down mv=<mv>" */
static int line_flip_down(int mv, char* line) {
    static const char p[] = "d9 flip down mv=";
    int pl = (int)(sizeof(p) - 1);
    int p2 = log_line_int(p, pl, "", 0, mv, "", 0, line);
    return p2;
}

/* "d9 out duty=<target> rc=0" */
static int line_out(int target, char* line) {
    static const char p[] = "d9 out duty=";
    static const char s[] = " rc=0";
    int pl = (int)(sizeof(p) - 1);
    int sl = (int)(sizeof(s) - 1);
    return log_line_int(p, pl, "", 0, target, s, sl, line);
}

/* "d9 out duty=<target> rc=0 recovered=<n>" */
static int line_out_recovered(int target, int rec, char* line) {
    static const char p[] = "d9 out duty=";
    static const char mid[] = " rc=0 recovered=";
    int pl = (int)(sizeof(p) - 1);
    int ml = (int)(sizeof(mid) - 1);
    int p0 = log_line_int(p, pl, "", 0, target, "", 0, line);
    int i;
    for (i = 0; i < ml; i++) line[p0 + i] = mid[i];
    p0 += ml;
    p0 += fmt_i32(rec, line + p0);
    return p0;
}

/* "d9 block rc=<r>" */
static int line_block(int r, char* line) {
    static const char p[] = "d9 block rc=";
    int pl = (int)(sizeof(p) - 1);
    return log_line_int(p, pl, "", 0, r, "", 0, line);
}

/* ===== exports ===== */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    static const char m[] = "d9 init";
    log_str(m, (int)(sizeof(m) - 1));
    (void)ts_pwm_set(0, 1, 1000, 350);
    return 0;
}

__attribute__((export_name("app_evt")))
int app_evt(int payload) {
    char line[80];
    static const char p[] = "d9 evt mv=";
    int pl = (int)(sizeof(p) - 1);
    int mv = payload & 0xFFFF;
    int len = log_line_int(p, pl, "", 0, mv, "", 0, line);
    log_str(line, len);
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    char line[80];
    int mv = ts_adc_read(0, 0);
    if (mv < 0) return 0;

    /* 滞回：state 0→1 当 mv>82；state 1→0 当 mv<76；76..82 间不变 */
    if (mv > 82 && g_state == 0) {
        g_state  = 1;
        g_target = 700;
        {
            int n = line_flip_up(mv, line);
            log_str(line, n);
        }
    } else if (mv < 76 && g_state == 1) {
        g_state  = 0;
        g_target = 350;
        {
            int n = line_flip_down(mv, line);
            log_str(line, n);
        }
    }

    /* 每拍幂等重申目标 */
    int r = ts_pwm_set(0, 1, 1000, g_target);

    if (r == 0 && g_armed == 0) {
        g_armed = 1;
        {
            int n = line_out(g_target, line);
            log_str(line, n);
        }
    } else if (r < 0 && g_armed != 0 && g_last_rc >= 0) {
        int n = line_block(r, line);
        log_str(line, n);
    } else if (r == 0 && g_armed != 0 && g_last_rc < 0) {
        g_recovered = g_recovered + 1;
        {
            int n = line_out_recovered(g_target, g_recovered, line);
            log_str(line, n);
        }
    }

    g_last_rc = r;

    if (g_recovered >= 1 && g_done == 0) {
        g_done = 1;
        {
            static const char m[] = "D9-DONE recovered=1";
            log_str(m, (int)(sizeof(m) - 1));
        }
    }
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void) {
    return 0;
}
