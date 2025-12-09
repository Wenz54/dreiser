/**
 * DRAIZER V2 - Memory Pool
 * Fast pre-allocated memory (15ns vs 200ns malloc)
 */

#ifndef MEMORY_POOL_H
#define MEMORY_POOL_H

#include <stddef.h>
#include <stdint.h>
#include <pthread.h>

typedef struct {
    void *pool;                // Pre-allocated memory
    size_t block_size;
    size_t block_count;
    uint32_t *free_bitmap;     // Bitmap of free blocks
    uint32_t next_free_hint;   // Hint for next free block
    pthread_mutex_t lock;      // Mutex (only for multi-threaded)
} MemoryPool;

MemoryPool* mempool_create(size_t block_size, size_t block_count);
void mempool_destroy(MemoryPool *mp);
void* mempool_alloc(MemoryPool *mp);
void mempool_free(MemoryPool *mp, void *ptr);

#endif // MEMORY_POOL_H


