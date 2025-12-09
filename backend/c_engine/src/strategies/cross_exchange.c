/**
 * DRAIZER V2 - Cross-Exchange Arbitrage Implementation
 */

#include "cross_exchange.h"
#include "../utils/timestamp.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef __AVX2__
#include <immintrin.h>
#endif

CrossExchangeStrategy* cross_exchange_create(PriceCache *price_cache) {
    CrossExchangeStrategy *strategy = calloc(1, sizeof(CrossExchangeStrategy));
    if (!strategy) return NULL;
    
    strategy->price_cache = price_cache;
    strategy->config.min_spread_bps = 4.0;   // 0.04% - ABSOLUTE_MIN_SPREAD
    strategy->config.max_position_usd = 50.0;  // Will be overridden by risk manager
    strategy->config.fee_bps = 10.0;  // 0.1% - realistic maker/taker average
    strategy->config.enabled = 1;
    strategy->opps_detected = 0;
    strategy->opps_executed = 0;
    
    return strategy;
}

void cross_exchange_destroy(CrossExchangeStrategy *strategy) {
    free(strategy);
}

void cross_exchange_update_config(CrossExchangeStrategy *strategy, const CrossExchangeConfig *config) {
    strategy->config = *config;
}

int cross_exchange_detect(
    CrossExchangeStrategy *strategy,
    const char *symbol,
    ArbitrageOpportunity *opp_out
) {
    if (!strategy->config.enabled) return 0;
    
    PriceCache *cache = strategy->price_cache;
    
    // TEMPORARY DEBUG
    static uint64_t detect_calls = 0;
    if (++detect_calls % 1000000 == 0) {
        printf("🔍 cross_exchange_detect: %lu calls for %s (cache entries: %d)\n", 
               detect_calls, symbol, cache->num_entries);
        // Print all cache entries once
        if (detect_calls == 1000000) {
            printf("📋 Cache contents:\n");
            for (int i = 0; i < cache->num_entries; i++) {
                CachedPrice entry;
                if (price_cache_read(cache, i, &entry) >= 0) {
                    printf("   [%d] %s @ %s | bid=%.2f, ask=%.2f\n",
                           i, entry.symbol, entry.exchange, entry.bid, entry.ask);
                }
            }
        }
    }
    
    // Find all prices for this symbol on different exchanges
    double best_bid = -1.0;
    double best_ask = 1e9;
    char best_bid_exchange[20] = {0};
    char best_ask_exchange[20] = {0};
    uint64_t now = rdtsc();
    
    for (int i = 0; i < cache->num_entries; i++) {
        CachedPrice entry;
        if (price_cache_read(cache, i, &entry) < 0) continue;
        
        if (strcmp(entry.symbol, symbol) != 0) continue;
        
        // TEMPORARY DEBUG - log prices for BTCUSDT
        static uint64_t price_logs = 0;
        if (strcmp(symbol, "BTCUSDT") == 0 && ++price_logs % 100000 == 0) {
            printf("💰 %s @ %s: bid=%.4f, ask=%.4f (age: %lu ns)\n", 
                   entry.symbol, entry.exchange, entry.bid, entry.ask,
                   (unsigned long)tsc_to_ns(now - entry.timestamp_tsc));
        }
        
        // ✅ BUG FIX: Check staleness (max 1 second old)
        uint64_t age_ns = tsc_to_ns(now - entry.timestamp_tsc);
        if (age_ns > 1000000000ULL) continue;  // 1 second
        
        // ✅ BUG FIX: Validate prices are positive and reasonable
        if (entry.bid <= 0 || entry.ask <= 0) continue;
        if (entry.ask < entry.bid) continue;  // Inverted book = bad data
        
        // Track best bid (highest price to sell at)
        if (entry.bid > best_bid) {
            best_bid = entry.bid;
            strncpy(best_bid_exchange, entry.exchange, 19);
            best_bid_exchange[19] = '\0';  // ✅ Null-terminate
        }
        
        // Track best ask (lowest price to buy at)
        if (entry.ask < best_ask) {
            best_ask = entry.ask;
            strncpy(best_ask_exchange, entry.exchange, 19);
            best_ask_exchange[19] = '\0';  // ✅ Null-terminate
        }
    }
    
    // No valid prices found
    if (best_bid <= 0 || best_ask >= 1e8) return 0;
    
    // ✅ BUG FIX: Check if best_bid > best_ask (required for arbitrage)
    // TEMPORARY DEBUG
    static uint64_t btc_logs = 0;
    if (strcmp(symbol, "BTCUSDT") == 0 && ++btc_logs % 1000000 == 0) {
        printf("🔍 %s before checks: bid=%.2f(%s), ask=%.2f(%s)\n",
               symbol, best_bid, best_bid_exchange, best_ask, best_ask_exchange);
    }
    
    if (best_bid <= best_ask) return 0;
    
    // Same exchange → no arbitrage
    if (strcmp(best_bid_exchange, best_ask_exchange) == 0) return 0;
    
    // Calculate spread
    double spread_bps = ((best_bid - best_ask) / best_ask) * 10000.0;
    double net_spread_bps = spread_bps - strategy->config.fee_bps - 5.0;  // -5bps slippage
    
    // TEMPORARY DEBUG
    static uint64_t spread_logs = 0;
    if (strcmp(symbol, "BTCUSDT") == 0 && ++spread_logs % 1000000 == 0) {
        printf("🔍 %s: bid=%.2f(%s), ask=%.2f(%s), gross=%.2f, net=%.2f, min=%.2f\n",
               symbol, best_bid, best_bid_exchange, best_ask, best_ask_exchange,
               spread_bps, net_spread_bps, strategy->config.min_spread_bps);
    }
    
    // ✅ BUG FIX: Check for reasonable spread (prevent overflow/underflow)
    if (net_spread_bps < 0 || net_spread_bps > 10000.0) return 0;  // Max 100% spread
    
    // Check if profitable
    if (net_spread_bps < strategy->config.min_spread_bps) return 0;
    
    // Calculate profit
    double position_size = fmin(strategy->config.max_position_usd, 500.0);
    double quantity = position_size / best_ask;
    
    // ✅ BUG FIX: More accurate profit calculation (fees on both sides)
    double buy_cost = position_size * (1.0 + strategy->config.fee_bps / 10000.0);
    double sell_proceeds = quantity * best_bid * (1.0 - strategy->config.fee_bps / 10000.0);
    double profit_usd = sell_proceeds - buy_cost;
    
    // ✅ BUG FIX: Sanity check profit
    if (profit_usd <= 0) return 0;
    
    // Fill opportunity
    strncpy(opp_out->symbol, symbol, 11);
    opp_out->symbol[11] = '\0';
    strncpy(opp_out->buy_exchange, best_ask_exchange, 19);
    opp_out->buy_exchange[19] = '\0';
    strncpy(opp_out->sell_exchange, best_bid_exchange, 19);
    opp_out->sell_exchange[19] = '\0';
    opp_out->buy_price = best_ask;
    opp_out->sell_price = best_bid;
    opp_out->spread_bps = net_spread_bps;
    opp_out->profit_usd = profit_usd;
    opp_out->detected_at_tsc = rdtsc();
    
    __atomic_fetch_add(&strategy->opps_detected, 1, __ATOMIC_RELAXED);
    
    return 1;  // Opportunity found!
}

