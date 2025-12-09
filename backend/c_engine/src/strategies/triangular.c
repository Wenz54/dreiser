/**
 * DRAIZER V2 - Triangular Arbitrage Implementation
 * Profit from price discrepancies in currency triangles
 */

#include "triangular.h"
#include "../utils/timestamp.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_TRIANGULAR_PATHS 50

TriangularStrategy* triangular_create(PriceCache *price_cache) {
    TriangularStrategy *strategy = calloc(1, sizeof(TriangularStrategy));
    if (!strategy) return NULL;
    
    strategy->price_cache = price_cache;
    strategy->config.min_profit_pct = 0.2;     // 0.2% minimum profit
    strategy->config.max_position_usd = 500.0;
    strategy->config.fee_bps = 10.0;           // 0.1% per trade (maker)
    strategy->config.enabled = 1;
    
    strategy->paths = calloc(MAX_TRIANGULAR_PATHS, sizeof(TriangularPath));
    strategy->num_paths = 0;
    strategy->opps_detected = 0;
    strategy->opps_executed = 0;
    
    return strategy;
}

void triangular_destroy(TriangularStrategy *strategy) {
    if (strategy->paths) free(strategy->paths);
    free(strategy);
}

void triangular_update_config(TriangularStrategy *strategy, const TriangularConfig *config) {
    strategy->config = *config;
}

void triangular_add_path(
    TriangularStrategy *strategy,
    const char *pair1,
    const char *pair2,
    const char *pair3,
    bool flip1,
    bool flip2,
    bool flip3
) {
    if (strategy->num_paths >= MAX_TRIANGULAR_PATHS) return;
    
    TriangularPath *path = &strategy->paths[strategy->num_paths++];
    strncpy(path->pair1, pair1, 11);
    strncpy(path->pair2, pair2, 11);
    strncpy(path->pair3, pair3, 11);
    path->flip1 = flip1;
    path->flip2 = flip2;
    path->flip3 = flip3;
}

// Helper: Get price from cache
static double get_price(PriceCache *cache, const char *exchange, const char *symbol, bool use_bid) {
    for (int i = 0; i < cache->num_entries; i++) {
        CachedPrice entry;
        if (price_cache_read(cache, i, &entry) < 0) continue;
        
        if (strcmp(entry.exchange, exchange) != 0) continue;
        if (strcmp(entry.symbol, symbol) != 0) continue;
        
        // Check staleness (max 1 second old)
        uint64_t now = rdtsc();
        uint64_t age_ns = tsc_to_ns(now - entry.timestamp_tsc);
        if (age_ns > 1000000000ULL) continue;
        
        return use_bid ? entry.bid : entry.ask;
    }
    
    return -1.0;
}

int triangular_detect_path(
    TriangularStrategy *strategy,
    const char *exchange,
    const TriangularPath *path,
    TriangularOpportunity *opp_out
) {
    if (!strategy->config.enabled) return 0;
    
    PriceCache *cache = strategy->price_cache;
    
    // Get prices for all 3 pairs
    double price1 = get_price(cache, exchange, path->pair1, path->flip1);
    double price2 = get_price(cache, exchange, path->pair2, path->flip2);
    double price3 = get_price(cache, exchange, path->pair3, path->flip3);
    
    if (price1 < 0 || price2 < 0 || price3 < 0) return 0;
    
    // Calculate triangular path
    // Start with $100 USDT equivalent
    double start_amount = fmin(strategy->config.max_position_usd, 100.0);
    double amount = start_amount;
    
    // Trade 1: USDT → BTC
    if (path->flip1) {
        amount = amount * price1;  // Sell
    } else {
        amount = amount / price1;  // Buy
    }
    amount *= (1.0 - strategy->config.fee_bps / 10000.0);  // Deduct fee
    
    // Trade 2: BTC → ETH
    if (path->flip2) {
        amount = amount * price2;
    } else {
        amount = amount / price2;
    }
    amount *= (1.0 - strategy->config.fee_bps / 10000.0);
    
    // Trade 3: ETH → USDT
    if (path->flip3) {
        amount = amount * price3;
    } else {
        amount = amount / price3;
    }
    amount *= (1.0 - strategy->config.fee_bps / 10000.0);
    
    double end_amount = amount;
    
    // Calculate profit
    double profit_usd = end_amount - start_amount;
    double profit_pct = (profit_usd / start_amount) * 100.0;
    
    // Check if profitable
    if (profit_pct < strategy->config.min_profit_pct) return 0;
    
    // Fill opportunity
    strncpy(opp_out->exchange, exchange, 19);
    opp_out->path = *path;
    opp_out->start_amount = start_amount;
    opp_out->end_amount = end_amount;
    opp_out->profit_pct = profit_pct;
    opp_out->profit_usd = profit_usd;
    opp_out->execution_rate = profit_pct * 100.0;  // Convert to bps
    opp_out->detected_at_tsc = rdtsc();
    opp_out->price1 = price1;
    opp_out->price2 = price2;
    opp_out->price3 = price3;
    
    __atomic_fetch_add(&strategy->opps_detected, 1, __ATOMIC_RELAXED);
    
    return 1;  // Opportunity found!
}

int triangular_scan(
    TriangularStrategy *strategy,
    const char *exchange,
    TriangularOpportunity *opp_out
) {
    if (!strategy->config.enabled) return 0;
    
    // Scan all configured paths
    for (uint32_t i = 0; i < strategy->num_paths; i++) {
        if (triangular_detect_path(strategy, exchange, &strategy->paths[i], opp_out)) {
            return 1;  // Found opportunity on this path
        }
    }
    
    return 0;  // No opportunities found
}


