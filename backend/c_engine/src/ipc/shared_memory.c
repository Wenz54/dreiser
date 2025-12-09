/**
 * DRAIZER V2 - Shared Memory Implementation
 */

#include "shared_memory.h"
#include "../utils/timestamp.h"
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>

SharedMemory* shm_create(const char *name, size_t size) {
    // Create shared memory
    int fd = shm_open(name, O_CREAT | O_RDWR, 0666);
    if (fd < 0) {
        perror("shm_open");
        return NULL;
    }
    
    // Set size
    if (ftruncate(fd, size) < 0) {
        perror("ftruncate");
        close(fd);
        return NULL;
    }
    
    // Map into memory
    void *ptr = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    
    if (ptr == MAP_FAILED) {
        perror("mmap");
        return NULL;
    }
    
    // Zero out
    memset(ptr, 0, size);
    
    return (SharedMemory*)ptr;
}

void shm_destroy(SharedMemory *shm, const char *name, size_t size) {
    if (shm) {
        munmap(shm, size);
    }
    shm_unlink(name);
}

void shm_update_stats(SharedMemory *shm, uint64_t latency_us) {
    // Update latency (simple moving average)
    uint32_t avg = __atomic_load_n(&shm->avg_latency_us, __ATOMIC_RELAXED);
    uint32_t new_avg = (avg * 9 + latency_us) / 10;  // EMA
    __atomic_store_n(&shm->avg_latency_us, new_avg, __ATOMIC_RELAXED);
    
    // Update P99 (simple approach: track max of last 100)
    if (latency_us > shm->p99_latency_us) {
        __atomic_store_n(&shm->p99_latency_us, (uint32_t)latency_us, __ATOMIC_RELAXED);
    }
    
    // Update timestamp
    __atomic_store_n(&shm->last_update_ns, get_time_ns(), __ATOMIC_RELEASE);
}

void shm_push_operation(SharedMemory *shm, const ShmOperation *op) {
    // Get current head
    uint32_t head = __atomic_load_n(&shm->operations_head, __ATOMIC_ACQUIRE);
    uint32_t next_head = (head + 1) % SHM_OPERATION_RING_SIZE;
    
    // Check if ring is full
    uint32_t tail = __atomic_load_n(&shm->operations_tail, __ATOMIC_ACQUIRE);
    if (next_head == tail) {
        // Ring full, advance tail (drop oldest)
        uint32_t new_tail = (tail + 1) % SHM_OPERATION_RING_SIZE;
        __atomic_store_n(&shm->operations_tail, new_tail, __ATOMIC_RELEASE);
    }
    
    // Write operation
    memcpy(&shm->operations[head], op, sizeof(ShmOperation));
    
    // Advance head
    __atomic_store_n(&shm->operations_head, next_head, __ATOMIC_RELEASE);
    
    // Increment counter
    __atomic_fetch_add(&shm->total_operations, 1, __ATOMIC_RELAXED);
}

uint32_t shm_pop_operations(SharedMemory *shm, ShmOperation *out, uint32_t max_count) {
    uint32_t count = 0;
    
    while (count < max_count) {
        uint32_t tail = __atomic_load_n(&shm->operations_tail, __ATOMIC_ACQUIRE);
        uint32_t head = __atomic_load_n(&shm->operations_head, __ATOMIC_ACQUIRE);
        
        // Check if empty
        if (tail == head) break;
        
        // Read operation
        memcpy(&out[count], &shm->operations[tail], sizeof(ShmOperation));
        count++;
        
        // Advance tail
        uint32_t next_tail = (tail + 1) % SHM_OPERATION_RING_SIZE;
        __atomic_store_n(&shm->operations_tail, next_tail, __ATOMIC_RELEASE);
    }
    
    return count;
}

