/**
 * DRAIZER V2 - Ultra-Fast Timestamp
 * RDTSC-based nanosecond timing (5ns latency)
 */

#ifndef TIMESTAMP_H
#define TIMESTAMP_H

#include <stdint.h>
#include <time.h>

// RDTSC calibration
extern double g_tsc_to_ns_multiplier;

/**
 * Initialize timestamp system (calibrate RDTSC)
 * Call once at startup
 */
void timestamp_init(void);

/**
 * Read CPU timestamp counter (TSC)
 * Latency: ~5ns
 */
static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return ((uint64_t)hi << 32) | lo;
}

/**
 * Convert TSC to nanoseconds
 */
static inline uint64_t tsc_to_ns(uint64_t tsc) {
    return (uint64_t)((double)tsc * g_tsc_to_ns_multiplier);
}

/**
 * Convert milliseconds to TSC
 */
static inline uint64_t ms_to_tsc(uint64_t ms) {
    return (uint64_t)((double)ms * 1000000.0 / g_tsc_to_ns_multiplier);
}

/**
 * Get current time in nanoseconds
 */
static inline uint64_t get_time_ns(void) {
    return tsc_to_ns(rdtsc());
}

#endif // TIMESTAMP_H


