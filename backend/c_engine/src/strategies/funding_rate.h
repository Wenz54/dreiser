/**
 * DRAIZER V2 - Funding Rate Arbitrage Strategy
 * Profit from funding payments in perpetual futures by hedging spot+futures
 */

#ifndef FUNDING_RATE_H
#define FUNDING_RATE_H

#include "../data/price_cache.h"
#include <stdint.h>
#include <stdbool.h>

// Funding rate opportunity
typedef struct {
    char symbol[12];
    char exchange[20];
    double funding_rate_pct;      // 8-hour funding rate (%)
    double annualized_rate_pct;   // Annualized rate (%)
    double spot_price;
    double futures_price;
    double basis_bps;             // Futures - Spot (basis points)
    double expected_profit_usd;
    uint64_t next_funding_time_ns;
    bool is_positive_funding;     // true = longs pay shorts
    uint64_t detected_at_tsc;
} FundingOpportunity;

// Strategy configuration
typedef struct {
    double min_funding_rate_pct;  // Minimum 8h funding rate (e.g., 0.05%)
    double min_apr_pct;           // Minimum annualized rate (e.g., 15%)
    double max_position_usd;      // Max position size
    double hedge_ratio;           // Spot hedge ratio (typically 1.0)
    int enabled;
} FundingRateConfig;

typedef struct {
    FundingRateConfig config;
    PriceCache *price_cache;
    uint64_t opps_detected;
    uint64_t opps_executed;
} FundingRateStrategy;

FundingRateStrategy* funding_rate_create(PriceCache *price_cache);
void funding_rate_destroy(FundingRateStrategy *strategy);
void funding_rate_update_config(FundingRateStrategy *strategy, const FundingRateConfig *config);

int funding_rate_detect(
    FundingRateStrategy *strategy,
    const char *symbol,
    double funding_rate_8h,
    uint64_t next_funding_time_ns,
    FundingOpportunity *opp_out
);

#endif // FUNDING_RATE_H


