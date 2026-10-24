/* demo.health.heartbeat — minimal health-heartbeat APP.
 * Deterministic, fail-safe, single-write contract:
 *   - app_init: drives GPIO inst 0 HIGH exactly once (guarded by file-scope flag).
 *   - app_tick / app_evt: no-op (return 0, no peripheral access).
 *   - health_ping: always returns 0 (healthy).
 * No WASI, no stdio, no globals-with-ctor, no RNG, no wall-clock.
 * Only the gpio:write:0 capability is declared; no other natives are imported.
 */

/* ---- Host imports (TSAP v1 natives; signatures fixed by host ABI) ---- */
extern int ts_gpio_write(int ctx, int inst, int v);

/* ---- App exports (manifest.exports must list each) ---- */
__attribute__((export_name("app_init")))
int app_init(int ctx)
{
    /* One-shot guard: re-entry of init must not re-drive the output.
     * File-scope static, zero-init at module load → first init writes,
     * later inits skip. Deterministic, no heap needed.
     */
    static int initialized = 0;
    if (initialized != 0) {
        return 0;
    }

    /* Drive GPIO instance 0 HIGH. Protection layer (host-side) performs
     * slew/limit; APP does not assume direct drive. A non-zero return
     * would indicate a host-side rejection (越权/限幅触发); per demo
     * contract we treat it as silent success and still mark initialized
     * so we do not busy-loop the write path.
     */
    (void)ts_gpio_write(ctx, 0, 1);

    initialized = 1;
    return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void)
{
    /* Contract: no peripheral writes from tick. */
    return 0;
}

__attribute__((export_name("app_evt")))
int app_evt(int v)
{
    /* Contract: no peripheral writes from event path. Parameter ignored. */
    (void)v;
    return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void)
{
    /* Constant healthy probe — host timeout watchdog reads this.
     * Returning 0 means "healthy"; any non-zero indicates the APP
     * is asking the host to enter fail-safe / rollback per AGENTS §6.
     */
    return 0;
}
