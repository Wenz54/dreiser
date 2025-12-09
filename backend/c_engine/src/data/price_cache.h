/**
 * DRAIZER V2 - Price Cache
 * Lock-free price storage using seqlock
 */

#ifndef PRICE_CACHE_H
#define PRICE_CACHE_H

#include "spsc_ring.h"

#define MAX_SYMBOLS 1000

// Cached price entry (64 bytes aligned)
typedef struct __attribute__((aligned(64))) {
    volatile uint32_t sequence;  // Even=stable, Odd=writing
    char symbol[12];
    char exchange[20];
    double bid;
    double ask;
    uint64_t timestamp_tsc;
    uint32_t padding[6];  // Pad to 64 bytes
} CachedPrice;

typedef struct {
    CachedPrice entries[MAX_SYMBOLS];
    int num_entries;
} PriceCache;

PriceCache* price_cache_create(void);
void price_cache_destroy(PriceCache *cache);

int price_cache_find(PriceCache *cache, const char *symbol, const char *exchange);
void price_cache_update(PriceCache *cache, int idx, const Price *price);
int price_cache_read(PriceCache *cache, int idx, CachedPrice *out);

#endif // PRICE_CACHE_H


