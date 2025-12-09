/**
 * DRAIZER V2 - Cross-Exchange Arbitrage Strategy
 * Detect price differences between exchanges
 */

#ifndef CROSS_EXCHANGE_H
#define CROSS_EXCHANGE_H

#include "../data/price_cache.h"
#include <stdint.h>

// Arbitrage opportunity
typedef struct {
    char symbol[12];
    char buy_exchange[20];
    char sell_exchange[20];
    double buy_price;
    double sell_price;
    double spread_bps;
    double profit_usd;
    uint64_t detected_at_tsc;
} ArbitrageOpportunity;

// Strategy configuration
typedef struct {
    double min_spread_bps;       // Minimum spread (e.g., 75 bps)
    double max_position_usd;     // Max position size
    double fee_bps;              // Total fees (buy + sell)
    int enabled;
} CrossExchangeConfig;

typedef struct {
    CrossExchangeConfig config;
    PriceCache *price_cache;
    uint64_t opps_detected;
    uint64_t opps_executed;
} CrossExchangeStrategy;

CrossExchangeStrategy* cross_exchange_create(PriceCache *price_cache);
void cross_exchange_destroy(CrossExchangeStrategy *strategy);
void cross_exchange_update_config(CrossExchangeStrategy *strategy, const CrossExchangeConfig *config);

int cross_exchange_detect(
    CrossExchangeStrategy *strategy,
    const char *symbol,
    ArbitrageOpportunity *opp_out
);

#endif // CROSS_EXCHANGE_H


