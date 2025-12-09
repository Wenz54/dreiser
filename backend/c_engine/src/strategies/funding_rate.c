/**
 * DRAIZER V2 - Funding Rate Arbitrage Implementation
 * Profit from funding payments in perpetual futures
 */

#include "funding_rate.h"
#include "../utils/timestamp.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

FundingRateStrategy* funding_rate_create(PriceCache *price_cache) {
    FundingRateStrategy *strategy = calloc(1, sizeof(FundingRateStrategy));
    if (!strategy) return NULL;
    
    strategy->price_cache = price_cache;
    strategy->config.min_funding_rate_pct = 0.03;  // 0.03% per 8h = 0.36% daily
    strategy->config.min_apr_pct = 10.0;           // 10% APR minimum
    strategy->config.max_position_usd = 500.0;
    strategy->config.hedge_ratio = 1.0;            // 1:1 hedge
    strategy->config.enabled = 1;
    strategy->opps_detected = 0;
    strategy->opps_executed = 0;
    
    return strategy;
}

void funding_rate_destroy(FundingRateStrategy *strategy) {
    free(strategy);
}

void funding_rate_update_config(FundingRateStrategy *strategy, const FundingRateConfig *config) {
    strategy->config = *config;
}

int funding_rate_detect(
    FundingRateStrategy *strategy,
    const char *symbol,
    double funding_rate_8h,
    uint64_t next_funding_time_ns,
    FundingOpportunity *opp_out
) {
    if (!strategy->config.enabled) return 0;
    
    PriceCache *cache = strategy->price_cache;
    
    // Find spot and futures prices
    double spot_price = -1.0;
    double futures_price = -1.0;
    char exchange[20] = {0};
    
    for (int i = 0; i < cache->num_entries; i++) {
        CachedPrice entry;
        if (price_cache_read(cache, i, &entry) < 0) continue;
        
        if (strcmp(entry.symbol, symbol) != 0) continue;
        
        // Check staleness (max 2 seconds old)
        uint64_t now = rdtsc();
        uint64_t age_ns = tsc_to_ns(now - entry.timestamp_tsc);
        if (age_ns > 2000000000ULL) continue;  // 2 seconds
        
        // Determine if spot or futures (futures usually have "PERP" or similar marker)
        // For now, use simple heuristic: first price = spot, second = futures
        if (spot_price < 0) {
            spot_price = entry.ask;
        } else if (futures_price < 0) {
            futures_price = entry.ask;
            strncpy(exchange, entry.exchange, 19);
        }
    }
    
    // Need both spot and futures prices
    if (spot_price < 0 || futures_price < 0) return 0;
    
    // Calculate annualized rate
    // 8-hour funding happens 3x per day = 1095x per year
    double annualized_rate_pct = funding_rate_8h * 365.0 * 3.0;
    
    // Check if profitable
    if (fabs(funding_rate_8h) < strategy->config.min_funding_rate_pct) return 0;
    if (fabs(annualized_rate_pct) < strategy->config.min_apr_pct) return 0;
    
    // Calculate basis (futures premium/discount to spot)
    double basis_bps = ((futures_price - spot_price) / spot_price) * 10000.0;
    
    // Calculate expected profit
    double position_size = fmin(strategy->config.max_position_usd, 500.0);
    double quantity = position_size / spot_price;
    
    // Profit = funding payment for 8 hours
    double funding_payment = quantity * futures_price * (funding_rate_8h / 100.0);
    double expected_profit = fabs(funding_payment) - (position_size * 0.001);  // -0.1% fees
    
    // Fill opportunity
    strncpy(opp_out->symbol, symbol, 11);
    strncpy(opp_out->exchange, exchange, 19);
    opp_out->funding_rate_pct = funding_rate_8h;
    opp_out->annualized_rate_pct = annualized_rate_pct;
    opp_out->spot_price = spot_price;
    opp_out->futures_price = futures_price;
    opp_out->basis_bps = basis_bps;
    opp_out->expected_profit_usd = expected_profit;
    opp_out->next_funding_time_ns = next_funding_time_ns;
    opp_out->is_positive_funding = (funding_rate_8h > 0);  // Positive = longs pay shorts
    opp_out->detected_at_tsc = rdtsc();
    
    __atomic_fetch_add(&strategy->opps_detected, 1, __ATOMIC_RELAXED);
    
    return 1;  // Opportunity found!
}


