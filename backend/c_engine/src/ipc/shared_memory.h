/**
 * DRAIZER V2 - Shared Memory IPC
 * Python can read stats + operations without blocking C engine
 */

#ifndef SHARED_MEMORY_H
#define SHARED_MEMORY_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define SHM_OPERATION_RING_SIZE 100

// Операция для передачи на фронт (Must match Python struct!)
typedef struct __attribute__((packed)) {
    uint64_t id;
    uint64_t timestamp_ns;
    char type[20];            // "LONG", "SHORT", "CLOSE"
    char strategy[20];        // "cross_exchange", etc.
    char symbol[12];
    char exchange_buy[20];
    char exchange_sell[20];
    double quantity;
    double entry_price;
    double exit_price;
    double pnl;
    double pnl_percent;
    double spread_bps;
    double fees_paid;
    bool is_open;
    uint8_t padding[7];
} ShmOperation;

// Must match Python struct!
typedef struct __attribute__((packed)) {
    // Status flags
    bool engine_running;
    bool strategy_enabled[3];  // cross_exchange, funding_rate, triangular
    uint8_t padding1[4];
    
    // Performance counters (atomic)
    uint64_t opps_detected;
    uint64_t opps_executed;
    uint64_t orders_placed;
    uint64_t orders_filled;
    
    // Financial metrics
    double total_profit_usd;
    double balance_usd;
    uint32_t wins;
    uint32_t losses;
    double win_rate;
    uint32_t open_positions;
    uint8_t padding2[4];
    
    // Latency metrics (microseconds)
    uint32_t avg_latency_us;
    uint32_t p99_latency_us;
    
    // Last update timestamp
    uint64_t last_update_ns;
    
    // Operations ring buffer
    ShmOperation operations[SHM_OPERATION_RING_SIZE];
    volatile uint32_t operations_head;  // Где писать следующую
    volatile uint32_t operations_tail;  // Откуда читать (Python)
    uint64_t total_operations;
} SharedMemory;

SharedMemory* shm_create(const char *name, size_t size);
void shm_destroy(SharedMemory *shm, const char *name, size_t size);
void shm_update_stats(SharedMemory *shm, uint64_t latency_us);

// Добавить операцию в ring buffer
void shm_push_operation(SharedMemory *shm, const ShmOperation *op);

// Python читает операции (возвращает количество прочитанных)
uint32_t shm_pop_operations(SharedMemory *shm, ShmOperation *out, uint32_t max_count);

#endif // SHARED_MEMORY_H

