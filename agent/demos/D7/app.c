/*
 * demo.health.probe.rollback
 * 健康探针自动回滚演示 APP
 *
 * 行为契约（确定性，无随机/墙钟分支）：
 *   - app_init(ctx): 调用一次 ts_gpio_write(ctx, 0, 1) 拉高 GPIO 实例 0；
 *                    失败不重试（确定性失败 = 留痕由宿主记录）。
 *   - app_tick():   单调递增 tick 计数器，无 I/O，无副作用。
 *   - health_ping(): 当 tick 计数 > 20 时返回 1（模拟 APP 故障）；
 *                    否则返回 0。框架策略：1s 周期、连续 3 次失败
 *                    → 自动停止并回滚该 APP（宿主侧决策，本 APP 不感知）。
 *
 * 安全合同内化：
 *   - 仅声明并使用 caps=[gpio:write:0]，不导入未授权 native（合同 10 越权留痕）。
 *   - 静态 file-scope 状态，禁全局构造/墙钟/随机（合同 9 确定性）。
 *   - 写入路径唯一：GPIO 写入经宿主保护层限幅（合同 2）。
 *   - health_ping 必导出（tsap v1：缺 = 打包拒绝）。
 */

#include <stddef.h>

/* ---- 宿主 natives（精确签名；仅调用 caps 内已声明项） ---- */
extern int ts_gpio_write(int ctx, int inst, int v);
extern int ts_log_write(int ctx, int lvl, const char *msg, int len);

/* ---- file-scope 静态变量（禁全局构造） ---- */
static int s_ctx    = 0;  /* host 传入的运行时上下文 */
static int s_init   = 0;  /* app_init 完成标志 */
static int s_tick_n = 0;  /* app_tick 单调计数 */
static int s_fault  = 0;  /* GPIO 写入失败留痕 */

/* 故障阈值：第 20 次 tick 之后（即 s_tick_n > 20）health_ping 返回 1 */
#define FAULT_TICK_THRESHOLD 20

/* ---- 导出 ---- */

__attribute__((export_name("app_init")))
int app_init(int ctx) {
    s_ctx = ctx;
    /* 拉高 GPIO 实例 0：写入路径唯一，经宿主保护层（合同 2） */
    int rc = ts_gpio_write(ctx, 0, 1);
    if (rc != 0) {
        s_fault = 1;
        /* 留痕：合同 10——仅用已声明/宿主内建通道（log 无须 caps） */
        const char m[] = "demo.health.probe.rollback: gpio_write inst=0 rc!=0";
        ts_log_write(ctx, 3 /*warn*/, m, (int)(sizeof(m) - 1));
    }
    s_tick_n = 0;
    s_init = 1;
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void) {
    if (!s_init) return -1;
    /* 单调计数确定递增；溢出保护：达 INT_MAX-1 后钳制，禁未定义行为 */
    if (s_tick_n < 0x7FFFFFFE) {
        s_tick_n++;
    }
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void) {
    /* 故障语义：tick 越过阈值后持续返回 1（不退），
     * 框架 1s/次、连续 3 次失败 → 自动停止并回滚（宿主侧） */
    if (!s_init) return 1;        /* 未初始化即视为失败，触发回滚 */
    if (s_fault)  return 1;       /* init 阶段 GPIO 失败也直接故障 */
    return (s_tick_n > FAULT_TICK_THRESHOLD) ? 1 : 0;
}

/* ---- 事件通道（manifest 未列，但保留符号以便将来扩展） ---- */
__attribute__((export_name("app_evt")))
int app_evt(int v) {
    (void)v;
    return 0;
}