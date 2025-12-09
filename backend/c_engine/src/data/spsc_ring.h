/**
 * DRAIZER V2 - SPSC Ring Buffer
 * Lock-free Single-Producer Single-Consumer queue
 * Latency: ~20ns per operation
 */

#ifndef SPSC_RING_H
#define SPSC_RING_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// Price data structure (64 bytes - 1 cache line)
typedef struct __attribute__((aligned(64))) {
    char symbol[12];              // "BTCUSDT"
    char exchange[8];             // "binance"
    double price;                 // 8 bytes
    double quantity;              // 8 bytes
    uint64_t timestamp_tsc;       // 8 bytes (RDTSC)
    uint32_t sequence;            // 4 bytes
    uint8_t is_valid;             // 1 byte
    uint8_t padding[11];          // 11 bytes padding
} Price;

// SPSC Ring Buffer (cache-line aligned)
typedef struct __attribute__((aligned(64))) {
    // Producer writes (own cache line)
    volatile uint64_t head __attribute__((aligned(64)));
    
    // Consumer writes (own cache line)
    volatile uint64_t tail __attribute__((aligned(64)));
    
    uint64_t capacity;
    Price items[0];  // Flexible array member
} SPSCRingBuffer;

/**
 * Create SPSC ring buffer
 * 
 * @param capacity Number of items (power of 2 recommended)
 * @return Buffer pointer or NULL on failure
 */
SPSCRingBuffer* spsc_create(size_t capacity);

/**
 * Destroy buffer
 */
void spsc_destroy(SPSCRingBuffer *buf);

/**
 * Push item (producer only!)
 * 
 * @return 1 on success, 0 if full
 */
static inline int spsc_push(SPSCRingBuffer *buf, const Price *item) {
    uint64_t head = buf->head;
    uint64_t next_head = (head + 1) % buf->capacity;
    
    // Check if full
    uint64_t tail = __atomic_load_n(&buf->tail, __ATOMIC_ACQUIRE);
    if (next_head == tail) {
        return 0;  // Full
    }
    
    // Copy item
    buf->items[head] = *item;
    
    // Commit (release fence)
    __atomic_store_n(&buf->head, next_head, __ATOMIC_RELEASE);
    
    return 1;
}

/**
 * Pop item (consumer only!)
 * 
 * @return 1 on success, 0 if empty
 */
static inline int spsc_pop(SPSCRingBuffer *buf, Price *item) {
    uint64_t tail = buf->tail;
    
    // Check if empty
    uint64_t head = __atomic_load_n(&buf->head, __ATOMIC_ACQUIRE);
    if (tail == head) {
        return 0;  // Empty
    }
    
    // Copy item
    *item = buf->items[tail];
    
    // Commit
    uint64_t next_tail = (tail + 1) % buf->capacity;
    __atomic_store_n(&buf->tail, next_tail, __ATOMIC_RELEASE);
    
    return 1;
}

/**
 * Check if empty
 */
static inline bool spsc_is_empty(const SPSCRingBuffer *buf) {
    uint64_t head = __atomic_load_n(&buf->head, __ATOMIC_ACQUIRE);
    uint64_t tail = __atomic_load_n(&buf->tail, __ATOMIC_ACQUIRE);
    return head == tail;
}

/**
 * Get count of items
 */
static inline uint64_t spsc_count(const SPSCRingBuffer *buf) {
    uint64_t head = __atomic_load_n(&buf->head, __ATOMIC_ACQUIRE);
    uint64_t tail = __atomic_load_n(&buf->tail, __ATOMIC_ACQUIRE);
    
    if (head >= tail) {
        return head - tail;
    } else {
        return buf->capacity - tail + head;
    }
}

#endif // SPSC_RING_H


