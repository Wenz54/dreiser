/**
 * DRAIZER V2 - SPSC Ring Buffer Implementation
 */

#include "spsc_ring.h"
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

SPSCRingBuffer* spsc_create(size_t capacity) {
    size_t size = sizeof(SPSCRingBuffer) + capacity * sizeof(Price);
    
    // Try huge pages first (2MB pages → faster TLB)
    void *ptr = mmap(NULL, size, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
    
    if (ptr == MAP_FAILED) {
        // Fallback to normal pages
        ptr = mmap(NULL, size, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    }
    
    if (ptr == MAP_FAILED) {
        return NULL;
    }
    
    SPSCRingBuffer *buf = (SPSCRingBuffer*)ptr;
    buf->head = 0;
    buf->tail = 0;
    buf->capacity = capacity;
    
    // Zero out items
    memset(buf->items, 0, capacity * sizeof(Price));
    
    return buf;
}

void spsc_destroy(SPSCRingBuffer *buf) {
    if (buf) {
        size_t size = sizeof(SPSCRingBuffer) + buf->capacity * sizeof(Price);
        munmap(buf, size);
    }
}


