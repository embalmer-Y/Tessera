/*
 * demo.tessera.security.overreach — 越权拦截安全演示
 *
 * 设计意图：
 *   - manifest caps 仅声明 gpio:write:0，故意不含任何 pwm:* 能力。
 *   - app_init 中先调用 ts_pwm_set(ctx, 1, 1000, 500)（越权访问），
 *     框架权限层将拦截并返回负值错误码（合同 10：越权拒绝并留痕）。
 *   - 越权调用的返回值被显式丢弃——APP 不依赖其结果，纯演示性质。
 *   - 随后正常写 GPIO 实例 0 = 1（写入路径必经保护层，合同 2）。
 *   - app_tick 空操作（不参与控制环）；health_ping 返回 0 表示存活。
 *
 * 确定性：
 *   - 无随机、无墙钟、无 WASI/stdio、无全局构造。
 *   - 静态文件域变量在加载时隐式零初始化，确定性。
 *   - 同输入序列（init 一次）→ 同输出序列（GPIO 单次写入 + pwm 越权拒绝留痕）。
 *
 * 编译目标：wasm32 自由固件（wasm-ld 链接宿主 natives）。
 */

#include <stddef.h>

/* ---------- 宿主 natives（按规则精确签名 extern 声明） ---------- */
extern int ts_gpio_write(int ctx, int inst, int v);
extern int ts_gpio_read(int ctx, int inst);
extern int ts_pwm_set(int ctx, int inst, int hz, int permille);
extern int ts_adc_read(int ctx, int inst);
extern unsigned long long ts_time_ms(int ctx);
extern int ts_log_write(int ctx, int lvl, const char* msg, int len);

/* ---------- 文件域静态状态（确定性零初始化） ---------- */
/* 当前 APP 上下文（app_init 时由宿主传入并固化）。 */
static int g_ctx = 0;
/* 已完成初始化标记（一次性，避免 tick 重复行为；仅用于演示，无副作用）。 */
static int g_inited = 0;

/* ---------- 导出：app_init ---------- */
/*
 * 入参 ctx：宿主上下文句柄，由宿主在装载后、首次 tick 前传入。
 * 返回：0 = 成功；负值 = 初始化失败（宿主将按合同 6 进入 fail-safe）。
 *
 * 副作用次序固定：
 *   1) 保存 ctx；
 *   2) 越权调用 ts_pwm_set（实例 1）——预期被权限层拒绝并留痕；
 *   3) 正常写 GPIO 实例 0 = 1。
 */
__attribute__((export_name("app_init")))
int app_init(int ctx) {
    /* (1) 保存上下文 */
    g_ctx = ctx;
    g_inited = 1;

    /* (2) 越权演示：caps 不含 pwm:*，框架应拒绝此调用并留痕（合同 10）。
     *     返回值被显式丢弃——本 APP 不假设其可用，仅作触发器。 */
    (void)ts_pwm_set(ctx, /*inst=*/1, /*hz=*/1000, /*permille=*/500);

    /* (3) 正常路径：在授权范围内写 GPIO 实例 0 = 1。
     *     写入仍受固件保护层限幅/校验（合同 2），此处仅表达意图。 */
    (void)ts_gpio_write(ctx, /*inst=*/0, /*v=*/1);

    return 0;
}

/* ---------- 导出：app_tick ---------- */
/*
 * 空操作：本演示 APP 不参与周期性控制环。
 * 返回：0 = 正常。
 */
__attribute__((export_name("app_tick")))
int app_tick(void) {
    /* 故意为空——无定时行为、无状态变更。 */
    return 0;
}

/* ---------- 导出：app_evt ---------- */
/*
 * 可选导出：宿主事件回调入口。本 APP 不订阅事件，但为完整 API 表面导出。
 * 当前 caps 未涉及任何事件源，亦无事件处理逻辑。
 */
__attribute__((export_name("app_evt")))
int app_evt(int v) {
    (void)v;
    return 0;
}

/* ---------- 导出：health_ping（必出，合同：超时回滚/隔离） ---------- */
/*
 * 存活探针：返回 0 表示健康。
 * 本演示不引入 watchdog 喂狗动作——health_ping 由宿主按周期调用，
 * 返回非零可触发宿主侧的隔离流程（合同 4 / LLD-ts-appmgr §2）。
 */
__attribute__((export_name("health_ping")))
int health_ping(void) {
    return 0;
}
