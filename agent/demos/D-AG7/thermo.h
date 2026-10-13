/*
 * include/thermo.h
 *
 * Thermo hysteresis control contract:
 *   - thermo_step(int mv, int* heat_out): single-step decision;
 *       when heat_on==0 and mv<2500  -> turn on  (heat_out=1, heat_on count +1);
 *       when heat_on==1 and mv>2800  -> turn off (heat_out=0);
 *       hysteresis band or unchanged  -> heat_out=current state (no flip;
 *                                       heat_on unchanged).
 *       Each call also increments cycles by 1.
 *
 *   - thermo_get_cycles() / thermo_get_heat_on(): read accumulated counters
 *       (only for logging / KV save).
 *
 *   - thermo_is_done(): returns 1 once cycles>=THERMO_TOTAL_CYCLES;
 *       main uses this to enter no-op mode (note: main also tracks a
 *       terminal-logged flag of its own to ensure exactly one DONE log).
 *
 * Design rules:
 *   - all state is file-scope static; no malloc, no global ctor.
 *   - decision and counters are encapsulated; main only orchestrates natives.
 */

#ifndef INCLUDE_THERMO_H
#define INCLUDE_THERMO_H

/* Hysteresis thresholds (millivolts), pinned by spec. */
#define THERMO_TURN_ON_MV   2500   /* below: turn heater on */
#define THERMO_TURN_OFF_MV  2800   /* above: turn heater off */
#define THERMO_TOTAL_CYCLES 200    /* terminal cycles threshold */
#define THERMO_KV_PERIOD    20     /* KV save every N ticks */

/* Single-step decision; returns 0 on success, heat_out written 0/1. */
int thermo_step(int mv, int* heat_out);

/* Counter getters. */
int thermo_get_cycles(void);
int thermo_get_heat_on(void);

/* Whether terminal state has been reached. */
int thermo_is_done(void);

#endif /* INCLUDE_THERMO_H */