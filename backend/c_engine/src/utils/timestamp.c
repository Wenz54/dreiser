/**
 * DRAIZER V2 - Timestamp Implementation
 */

#include "timestamp.h"
#include <stdio.h>
#include <unistd.h>

double g_tsc_to_ns_multiplier = 1.0;

void timestamp_init(void) {
    struct timespec start, end;
    uint64_t tsc_start, tsc_end;
    
    // Warm up
    for (int i = 0; i < 10; i++) {
        rdtsc();
    }
    
    // Calibrate
    clock_gettime(CLOCK_MONOTONIC, &start);
    tsc_start = rdtsc();
    
    usleep(100000);  // Sleep 100ms
    
    tsc_end = rdtsc();
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    uint64_t tsc_elapsed = tsc_end - tsc_start;
    uint64_t ns_elapsed = (end.tv_sec - start.tv_sec) * 1000000000ULL +
                          (end.tv_nsec - start.tv_nsec);
    
    g_tsc_to_ns_multiplier = (double)ns_elapsed / (double)tsc_elapsed;
    
    double cycles_per_ns = 1.0 / g_tsc_to_ns_multiplier;
    printf("✓ RDTSC calibrated: %.3f cycles/ns (%.2f GHz)\n", 
           cycles_per_ns, cycles_per_ns);
}


