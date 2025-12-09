/**
 * DRAIZER V2 - Memory Pool Implementation
 */

#include "memory_pool.h"
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

MemoryPool* mempool_create(size_t block_size, size_t block_count) {
    MemoryPool *mp = malloc(sizeof(MemoryPool));
    if (!mp) return NULL;
    
    size_t pool_size = block_size * block_count;
    
    // Try huge pages
    mp->pool = mmap(NULL, pool_size, PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
    
    if (mp->pool == MAP_FAILED) {
        mp->pool = malloc(pool_size);  // Fallback
        if (!mp->pool) {
            free(mp);
            return NULL;
        }
    }
    
    mp->block_size = block_size;
    mp->block_count = block_count;
    
    // Bitmap (1 bit per block)
    size_t bitmap_size = (block_count + 31) / 32;
    mp->free_bitmap = calloc(bitmap_size, sizeof(uint32_t));
    if (!mp->free_bitmap) {
        free(mp->pool);
        free(mp);
        return NULL;
    }
    
    // All blocks free initially
    memset(mp->free_bitmap, 0xFF, bitmap_size * sizeof(uint32_t));
    
    mp->next_free_hint = 0;
    pthread_mutex_init(&mp->lock, NULL);
    
    return mp;
}

void mempool_destroy(MemoryPool *mp) {
    if (!mp) return;
    
    pthread_mutex_destroy(&mp->lock);
    free(mp->free_bitmap);
    free(mp->pool);  // or munmap if mmap'd
    free(mp);
}

void* mempool_alloc(MemoryPool *mp) {
    if (!mp) return NULL;
    
    pthread_mutex_lock(&mp->lock);
    
    uint32_t start_idx = mp->next_free_hint;
    
    // Fast path: check hint first
    uint32_t bitmap_idx = start_idx / 32;
    uint32_t bit_idx = start_idx % 32;
    
    if (mp->free_bitmap[bitmap_idx] & (1u << bit_idx)) {
        // Clear bit (mark as used)
        mp->free_bitmap[bitmap_idx] &= ~(1u << bit_idx);
        mp->next_free_hint = (start_idx + 1) % mp->block_count;
        
        pthread_mutex_unlock(&mp->lock);
        return (char*)mp->pool + (start_idx * mp->block_size);
    }
    
    // Slow path: linear scan
    for (uint32_t i = 0; i < mp->block_count; i++) {
        bitmap_idx = i / 32;
        bit_idx = i % 32;
        
        if (mp->free_bitmap[bitmap_idx] & (1u << bit_idx)) {
            mp->free_bitmap[bitmap_idx] &= ~(1u << bit_idx);
            mp->next_free_hint = (i + 1) % mp->block_count;
            
            pthread_mutex_unlock(&mp->lock);
            return (char*)mp->pool + (i * mp->block_size);
        }
    }
    
    pthread_mutex_unlock(&mp->lock);
    return NULL;  // Pool exhausted
}

void mempool_free(MemoryPool *mp, void *ptr) {
    if (!mp || !ptr) return;
    
    size_t offset = (char*)ptr - (char*)mp->pool;
    uint32_t idx = offset / mp->block_size;
    
    if (idx >= mp->block_count) return;  // Invalid pointer
    
    pthread_mutex_lock(&mp->lock);
    
    uint32_t bitmap_idx = idx / 32;
    uint32_t bit_idx = idx % 32;
    
    // Mark as free
    mp->free_bitmap[bitmap_idx] |= (1u << bit_idx);
    
    pthread_mutex_unlock(&mp->lock);
}


