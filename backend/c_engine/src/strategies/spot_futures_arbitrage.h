/**
 * DRAIZER V2 - Spot-Futures Arbitrage Strategy (PRIORITY 1)
 * Ultra-low latency arbitrage between Bitfinex SPOT and Deribit FUTURES
 * 
 * Target latency: ~7 microseconds
 * 
 * Spreads (after fees):
 * - MIN:    10 bps (0.10%) - absolute minimum for profitability
 * - TARGET: 15 bps (0.15%) - comfortable zone
 * - FAT:    25 bps (0.25%) - premium opportunities
 * 
 * Fees:
 * - Bitfinex: 0.10% maker / 0.20% taker
 * - Deribit:  -0.025% maker (rebate!) / 0.05% taker
 * - Effective: ~0.1075% (mixed execution)
 * - Slippage: ~0.02%
 * - Total:    ~0.1275%
 * 
 * Funding Rate:
 * - Deribit charges/pays funding every 8 hours
 * - Must account for future funding payments over position lifetime
 * - Formula: effective_spread += funding_rate_bps * expected_periods
 */

#ifndef SPOT_FUTURES_ARBITRAGE_H
#define SPOT_FUTURES_ARBITRAGE_H

#include "../data/price_cache.h"
#include "../data/opportunity.h"

// Spread thresholds (in bps = 0.01%)
#define SPOT_FUTURES_MIN_BPS      10.0    // 0.10% minimum
#define SPOT_FUTURES_TARGET_BPS   15.0    // 0.15% target
#define SPOT_FUTURES_FAT_BPS      25.0    // 0.25% fat opportunity

// Fee structure
#define BITFINEX_MAKER_FEE_BPS    10.0    // 0.10%
#define BITFINEX_TAKER_FEE_BPS    20.0    // 0.20%
#define DERIBIT_MAKER_FEE_BPS    -2.5     // -0.025% (rebate!)
#define DERIBIT_TAKER_FEE_BPS     5.0     // 0.05%
#define EFFECTIVE_FEES_BPS        10.75   // Average: 0.1075%
#define SLIPPAGE_BPS              2.0     // Estimated slippage: 0.02%
#define TOTAL_COST_BPS            12.75   // Effective + slippage

// Funding rate handling
#define FUNDING_INTERVAL_HOURS    8       // Deribit funding every 8h
#define FUNDING_PERIODS_PER_DAY   3       // 24h / 8h = 3 periods
#define MAX_FUNDING_RATE_BPS      10.0    // 0.10% max funding per period (safety)

// Position holding time estimation (for funding calculation)
#define EXPECTED_HOLD_PERIODS     3       // Expect to hold ~24h (3x8h funding)

typedef struct {
    PriceCache *cache;
    double min_spread_bps;
    double target_spread_bps;
    double fat_spread_bps;
    double funding_rate_threshold_bps;  // Don't trade if funding > this
    int num_symbols;
    char symbols[10][12];
} SpotFuturesStrategy;

// Initialize strategy
SpotFuturesStrategy* spot_futures_create(PriceCache *cache, const char *symbols[], int num_symbols);

// Detect arbitrage opportunities
// Returns: number of opportunities found (pushes to opportunities array)
int spot_futures_detect(SpotFuturesStrategy *strategy, Opportunity *opportunities, int max_opps, double funding_rates[]);

// Calculate net spread after all costs
// spread_bps: raw spread between spot and futures
// funding_rate_bps: current funding rate (positive = longs pay shorts)
// returns: net spread in bps after fees and funding
static inline double calculate_net_spread(double spread_bps, double funding_rate_bps) {
    // Account for future funding payments over expected hold period
    double funding_cost_bps = funding_rate_bps * EXPECTED_HOLD_PERIODS;
    
    // Net spread = raw spread - total costs - funding
    return spread_bps - TOTAL_COST_BPS - funding_cost_bps;
}

// Destroy strategy
void spot_futures_destroy(SpotFuturesStrategy *strategy);

#endif  // SPOT_FUTURES_ARBITRAGE_H

