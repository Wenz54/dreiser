/**
 * DRAIZER V2 - Triangular Arbitrage Strategy
 * Profit from price discrepancies in currency triangles on a single exchange
 * Example: BTC/USDT → ETH/BTC → ETH/USDT → BTC/USDT
 */

#ifndef TRIANGULAR_H
#define TRIANGULAR_H

#include "../data/price_cache.h"
#include <stdint.h>
#include <stdbool.h>

// Triangular path (3 hops)
typedef struct {
    char pair1[12];  // e.g., "BTC/USDT"
    char pair2[12];  // e.g., "ETH/BTC"
    char pair3[12];  // e.g., "ETH/USDT"
    bool flip1;      // If true, use sell price for pair1
    bool flip2;
    bool flip3;
} TriangularPath;

// Triangular opportunity
typedef struct {
    char exchange[20];
    TriangularPath path;
    double start_amount;      // Starting amount (e.g., 100 USDT)
    double end_amount;        // Ending amount after 3 trades
    double profit_pct;        // Net profit %
    double profit_usd;        // Net profit USD
    double execution_rate;    // Expected rate after fees (bps)
    uint64_t detected_at_tsc;
    
    // Prices used
    double price1;
    double price2;
    double price3;
} TriangularOpportunity;

// Strategy configuration
typedef struct {
    double min_profit_pct;      // Minimum profit % (e.g., 0.3%)
    double max_position_usd;    // Max position size
    double fee_bps;             // Fee per trade (e.g., 10 bps)
    int enabled;
} TriangularConfig;

typedef struct {
    TriangularConfig config;
    PriceCache *price_cache;
    TriangularPath *paths;      // Array of pre-computed paths
    uint32_t num_paths;
    uint64_t opps_detected;
    uint64_t opps_executed;
} TriangularStrategy;

TriangularStrategy* triangular_create(PriceCache *price_cache);
void triangular_destroy(TriangularStrategy *strategy);
void triangular_update_config(TriangularStrategy *strategy, const TriangularConfig *config);

// Add a triangular path to scan
void triangular_add_path(
    TriangularStrategy *strategy,
    const char *pair1,
    const char *pair2,
    const char *pair3,
    bool flip1,
    bool flip2,
    bool flip3
);

// Detect opportunities across all paths
int triangular_scan(
    TriangularStrategy *strategy,
    const char *exchange,
    TriangularOpportunity *opp_out
);

// Detect for a specific path
int triangular_detect_path(
    TriangularStrategy *strategy,
    const char *exchange,
    const TriangularPath *path,
    TriangularOpportunity *opp_out
);

#endif // TRIANGULAR_H


