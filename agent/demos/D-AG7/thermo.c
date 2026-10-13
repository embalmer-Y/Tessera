/*
 * thermo.c
 *
 * Thermo hysteresis state machine + counters (deterministic).
 * Only depends on #include "include/thermo.h"; calls no natives.
 *
 * Decision table (spec):
 *   state==0 (heater off) && mv < 2500  -> turn on  (heat_out=1, state=1, heat_count++)
 *   state==1 (heater on ) && mv > 2800  -> turn off (heat_out=0, state=0)
 *   otherwise                              -> hold    (heat_out=state, no flip)
 *
 * cycles increments on every call; no random / wall clock branches.
 */

#include "include/thermo.h"

/* file-scope state: external code cannot access these directly. */
static int s_state      = 0;   /* current heater switch 0/1 */
static int s_heat_count = 0;   /* accumulated heater-on count (off->on flips +1) */
static int s_cycles     = 0;   /* accumulated tick count */

int thermo_step(int mv, int* heat_out)
{
    int next = s_state;

    /* cycles always increments per tick (spec: "each tick cycles +1"). */
    s_cycles += 1;

    /* Decision (deterministic if-else; no random branches).
     * ADC error path (mv<0): skip decision -- hold current state. */
    if (mv >= 0) {
        if (s_state == 0) {
            if (mv < THERMO_TURN_ON_MV) {
                next = 1;        /* off -> on */
            }
        } else { /* s_state == 1 */
            if (mv > THERMO_TURN_OFF_MV) {
                next = 0;        /* on -> off */
            }
        }

        /* Flip point: only when next != s_state, update counters. */
        if (next != s_state) {
            s_state = next;
            if (next == 1) {
                s_heat_count += 1;   /* accumulated heater-on count +1 */
            }
        }
    }

    if (heat_out != 0) {
        *heat_out = s_state;
    }
    return 0;
}

int thermo_get_cycles(void)
{
    return s_cycles;
}

int thermo_get_heat_on(void)
{
    return s_heat_count;
}

int thermo_is_done(void)
{
    return (s_cycles >= THERMO_TOTAL_CYCLES) ? 1 : 0;
}