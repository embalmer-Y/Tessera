/* com.example.cube.nvd — 立方体节拍巡检 APP
 * 周期来源 = 框架 app_tick 回调（典型 500ms，但本 APP 不依赖实测周期——仅用 tick 调用序列计数，确保确定性）。
 * 无硬件输出通道；仅使用 ts_log 输出。
 * 不使用随机数 / 墙钟 / WASI / stdio / 全局构造。
 * 自由固件零依赖：natives 仅 extern 声明，不 #include。
 */

/* ---------- 宿主 natives（extern 声明，签名精确） ---------- */
/* ts_log_write 签名：
 *   int ts_log_write(int ctx, int lvl, const char* msg, int len);
 * 返回 >=0 为已写入字节数；<0 为错误码。
 */
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* ---------- 静态状态（file-scope，确定性种子） ---------- */
static int g_ctx      = 0;
static int g_cnt      = 0;        /* 已打印周期数；达 10 触发 done 且停止打印 */
static int g_inited   = 0;        /* init 完成哨，避免重复打印 init 行 */
static int g_done     = 0;        /* 完成行已打印哨 */

/* ---------- 工具：两位补零打印 "nvd tick cnt=NN"（单次 log 输出完整行） ---------- */
static void emit_tick_line(int n) {
    /* 缓冲区："nvd tick cnt=NN" = 15 字节
     * 严格两位补零：n=0 → "00"；n=10 → "10"（但本函数仅在 n<10 时被调用）。
     */
    char buf[15];
    buf[0]  = 'n';
    buf[1]  = 'v';
    buf[2]  = 'd';
    buf[3]  = ' ';
    buf[4]  = 't';
    buf[5]  = 'i';
    buf[6]  = 'c';
    buf[7]  = 'k';
    buf[8]  = ' ';
    buf[9]  = 'c';
    buf[10] = 'n';
    buf[11] = 't';
    buf[12] = '=';
    buf[13] = '0' + ((n / 10) % 10);
    buf[14] = '0' + (n % 10);
    ts_log_write(g_ctx, 3 /* info */, buf, 15);
}

/* ---------- 导出：app_init ---------- */
__attribute__((export_name("app_init")))
int app_init(int ctx) {
    g_ctx    = ctx;
    g_cnt    = 0;
    g_inited = 0;
    g_done   = 0;

    /* 单次 log 输出完整 "nvd init" */
    {
        static const char kInit[] = "nvd init";
        ts_log_write(g_ctx, 3 /* info */, kInit, (int)(sizeof(kInit) - 1));
    }
    g_inited = 1;
    return 0;
}

/* ---------- 导出：app_tick ---------- */
__attribute__((export_name("app_tick")))
int app_tick(void) {
    /* 双保险：若宿主在 init 前调用 tick，先 ensure init 行已落盘 */
    if (!g_inited) {
        static const char kInit[] = "nvd init";
        ts_log_write(g_ctx, 3 /* info */, kInit, (int)(sizeof(kInit) - 1));
        g_inited = 1;
    }

    if (!g_done) {
        g_cnt += 1;                 /* 本周期计数（1..10） */
        if (g_cnt < 10) {
            emit_tick_line(g_cnt);  /* 打印 "nvd tick cnt=01".."nvd tick cnt=09" */
        } else {
            /* g_cnt == 10：完成行 + 锁定 */
            static const char kDone[] = "NVD DONE ticks=10";
            ts_log_write(g_ctx, 3 /* info */, kDone, (int)(sizeof(kDone) - 1));
            g_done = 1;
        }
    }
    /* g_done == 1 后仍继续 tick（APP 保持运行），但不再打印任何周期/完成行 */
    return 0;
}

/* ---------- 导出：health_ping（健康探针，必须导出） ---------- */
__attribute__((export_name("health_ping")))
int health_ping(void) {
    /* 纯状态探针：不打 log；返回 0 = healthy，1 = 已完成（终态） */
    return g_done ? 1 : 0;
}