/**
 * DRAIZER V2 - Price Cache Implementation
 */

#include "price_cache.h"
#include <stdlib.h>
#include <string.h>

PriceCache* price_cache_create(void) {
    PriceCache *cache = calloc(1, sizeof(PriceCache));
    return cache;
}

void price_cache_destroy(PriceCache *cache) {
    free(cache);
}

int price_cache_find(PriceCache *cache, const char *symbol, const char *exchange) {
    for (int i = 0; i < cache->num_entries; i++) {
        if (strcmp(cache->entries[i].symbol, symbol) == 0 &&
            strcmp(cache->entries[i].exchange, exchange) == 0) {
            return i;
        }
    }
    
    // Not found, add new entry
    if (cache->num_entries < MAX_SYMBOLS) {
        int idx = cache->num_entries++;
        strncpy(cache->entries[idx].symbol, symbol, 11);
        strncpy(cache->entries[idx].exchange, exchange, 19);
        cache->entries[idx].sequence = 0;
        return idx;
    }
    
    return -1;  // Cache full
}

void price_cache_update(PriceCache *cache, int idx, const Price *price) {
    if (idx < 0 || idx >= cache->num_entries) return;
    
    CachedPrice *entry = &cache->entries[idx];
    
    // Start write (increment sequence, make it odd)
    uint32_t seq = __atomic_load_n(&entry->sequence, __ATOMIC_RELAXED);
    __atomic_store_n(&entry->sequence, seq + 1, __ATOMIC_RELEASE);
    
    // Price object contains mid-price from orderbook (already bid+ask)/2
    // Reconstruct bid/ask with realistic 0.01% spread
    double mid = price->price;
    double spread_half = mid * 0.00005;  // 0.005% on each side = 0.01% total spread
    
    entry->bid = mid - spread_half;  // Best bid (slightly below mid)
    entry->ask = mid + spread_half;  // Best ask (slightly above mid)
    entry->timestamp_tsc = price->timestamp_tsc;
    
    // End write (increment again, make it even)
    __atomic_store_n(&entry->sequence, seq + 2, __ATOMIC_RELEASE);
}

int price_cache_read(PriceCache *cache, int idx, CachedPrice *out) {
    if (idx < 0 || idx >= cache->num_entries) return -1;
    
    CachedPrice *entry = &cache->entries[idx];
    uint32_t seq1, seq2;
    
    do {
        seq1 = __atomic_load_n(&entry->sequence, __ATOMIC_ACQUIRE);
        
        // If odd, write in progress
        if (seq1 & 1) continue;
        
        // Copy data
        out->bid = entry->bid;
        out->ask = entry->ask;
        out->timestamp_tsc = entry->timestamp_tsc;
        strncpy(out->symbol, entry->symbol, 12);
        strncpy(out->exchange, entry->exchange, 20);
        
        seq2 = __atomic_load_n(&entry->sequence, __ATOMIC_ACQUIRE);
    } while (seq1 != seq2);  // Retry if changed
    
    return 0;
}


