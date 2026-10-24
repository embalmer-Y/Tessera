/*
 * D-THR (DEC-55 / Q-37 A) —— 双线程计数演示
 *
 *   主线程  +  worker "count_worker"  共 threads=2。
 *   主经宿主 natives (ts_thread_start/ts_thread_join) 一次性汇合 worker。
 *
 *   约束（宿主零依赖）：
 *     - 禁 #include；标准库头一律不引（手写十进制 / 字面量）。
 *     - 跨线程可见 = 共享线性内存静态 int + __atomic_fetch_add。
 *     - 确定性：无随机 / 无墙钟分支。
 *
 *   静态状态：
 *     state ∈ {0,1,2,3}        —— 0=启动、1=join、2=校验、3=终态空转
 *     h    ：ts_thread_start 返回句柄（state=0 写入）
 *     r    ：ts_thread_join  返回值（state=1 写入）
 *     g_cnt：主 / worker 共享的原子计数器（file-scope，线性内存静态）
 */

/* ====== 宿主 import 区 (extern) ======
 * 仅声明 natives 与登记注册回调；本 APP 额外新增 ts_thread_start / ts_thread_join。
 * 签名精确，禁任何其它外部。
 */
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);
extern int ts_thread_start(int ctx, const char* name, int name_len, int arg);
extern int ts_thread_join(int ctx, int handle);

/* ====== 编译内建（标准库头不可用，但 wasm32/clang 内建可用） ======
 * __atomic_fetch_add 在 wasm32 由 clang 内置；-pthread 标志由宿主链注入，
 * 源码不写编译指令。
 */

/* ====== 共享静态 ====== */
static int g_cnt = 0;

/* ====== 主侧静态机 ====== */
static int state = 0;
static int h     = 0;
static int r     = 0;

/* ====== 手写工具：s_copy / s_copy_lit / put_uint / put_int ====== */

/* src[0..len) 拷到 dst[dst_off..)；返回新 off。 */
static int s_copy(char* dst, int dst_off, const char* src, int len) {
    int i;
    for (i = 0; i < len; ++i) {
        dst[dst_off + i] = src[i];
    }
    return dst_off + len;
}

/* 字面量（编译期已知长度）。 */
static int s_copy_lit(char* dst, int dst_off, const char* src, int len) {
    return s_copy(dst, dst_off, src, len);
}

/* 十进制无符号整数手写转换（基 10，仅 ASCII '0'..'9'）。 */
static int put_uint(char* dst, int off, unsigned int v) {
    char tmp[16];
    int  n = 0;
    int  i;
    if (v == 0u) {
        dst[off++] = '0';
        return off;
    }
    while (v > 0u && n < (int)sizeof(tmp)) {
        tmp[n++] = (char)('0' + (v % 10u));
        v /= 10u;
    }
    /* 翻转写入 dst。 */
    for (i = n - 1; i >= 0; --i) {
        dst[off++] = tmp[i];
    }
    return off;
}

/* 有符号整数（负值前置 '-'）。 */
static int put_int(char* dst, int off, int v) {
    if (v < 0) {
        unsigned int u;
        dst[off++] = '-';
        /* 手写绝对值：INT_MIN (-2147483648) 单独处理，避免 -INT_MIN 溢出。 */
        if (v == -2147483647 - 1) {
            u = 2147483648u;
        } else {
            u = (unsigned int)(-v);
        }
        return put_uint(dst, off, u);
    }
    return put_uint(dst, off, (unsigned int)v);
}

/* ====== 日志封装：ctx=-2 → 由宿主 TEST 语义自动注入真 ctx ====== */
static void do_log(int lvl, const char* buf, int len) {
    ts_log_write(-2, lvl, buf, len);
}

/* ====== worker（一次性任务：累加 n 次后返回 n） ======
 *
 * 入口语义：arg = n；返回 n 表示任务完成（与主 join 期望 rc==2000 对拍）。
 * 跨线程可见：仅经 __atomic_fetch_add 写 g_cnt；主侧汇合后单方读 g_cnt 一次。
 *
 * 注：此函数符号名 "count_worker" 仅是 wasm 段内寻址名，由 ts_thread_start
 *     按 name 字符串寻址；它不属于宿主调用面的导出名，因此不列于 manifest.exports
 *     白名单（白名单只含 health_ping/app_init/app_tick/app_evt）。
 */
__attribute__((export_name("count_worker")))
int count_worker(int n) {
    int i;
    for (i = 0; i < n; ++i) {
        (void)__atomic_fetch_add(&g_cnt, 1, __ATOMIC_RELAXED);
    }
    return n;
}

/* ====== health_ping：恒 0（合同：非零=健康失败，编译门拦非零返回字面量） ====== */
__attribute__((export_name("health_ping")))
int health_ping(void) {
    return 0;
}

/* ====== app_init：log "dtr init"（十进制 / 字面量手写） ====== */
__attribute__((export_name("app_init")))
int app_init(int ctx) {
    char buf[16];
    int  off = 0;
    (void)ctx;

    off = s_copy_lit(buf, off, "dtr init", 8);

    do_log(0 /* INFO */, buf, off);
    return 0;
}

/* ====== app_tick：100ms 周期，按静态机推进 ======
 *   state=0：ts_thread_start  (name="count_worker", name_len=13, arg=2000)
 *            rc<0  → log "dtr spawn-rc=<h>" 且 state=3
 *            rc>=0 → state=1
 *   state=1：ts_thread_join(h)
 *            rc!=2000 → log "dtr join-rc=<r>" 且 state=3
 *            rc==2000 → state=2
 *   state=2：读 g_cnt；若 g_cnt==2000 且 r==2000
 *                → log "DT DONE cnt=2000 rc=2000" 且 state=3
 *              否则 → log "dtr mismatch cnt=<g_cnt>" 且 state=3
 *   state=3：终态空转（no-op）。
 *
 *  注：ctx 传 -2 ——宿主自动注入真值（与 ts_log_write 同模式）；线程 natives
 *    ts_thread_start / ts_thread_join 同约定。
 */
__attribute__((export_name("app_tick")))
int app_tick(void) {
    char buf[48];

    if (state == 0) {
        int rc;
        /* ts_thread_start(ctx=-2, name="count_worker", name_len=13, arg=2000) */
        rc = ts_thread_start(-2, "count_worker", 13, 2000);
        h = rc;
        if (rc < 0) {
            int off = 0;
            off = s_copy_lit(buf, off, "dtr spawn-rc=", 14);
            off = put_int(buf, off, rc);
            do_log(0, buf, off);
            state = 3;
        } else {
            state = 1;
        }
        return 0;
    }

    if (state == 1) {
        int rc;
        rc = ts_thread_join(-2, h);
        r = rc;
        if (rc != 2000) {
            int off = 0;
            off = s_copy_lit(buf, off, "dtr join-rc=", 12);
            off = put_int(buf, off, rc);
            do_log(0, buf, off);
            state = 3;
        } else {
            state = 2;
        }
        return 0;
    }

    if (state == 2) {
        /* 单读一次 g_cnt（join 已 barrier 在前 → 与 tear-down 序确定）。 */
        int cnt = __atomic_fetch_add(&g_cnt, 0, __ATOMIC_RELAXED);

        if (cnt == 2000 && r == 2000) {
            int off = 0;
            off = s_copy_lit(buf, off, "DT DONE cnt=2000 rc=2000", 25);
            do_log(0, buf, off);
        } else {
            int off = 0;
            off = s_copy_lit(buf, off, "dtr mismatch cnt=", 17);
            off = put_int(buf, off, cnt);
            do_log(0, buf, off);
        }
        state = 3;
        return 0;
    }

    /* state == 3: 空转。 */
    return 0;
}