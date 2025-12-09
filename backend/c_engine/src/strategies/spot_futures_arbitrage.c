/**
 * DRAIZER V2 - Spot-Futures Arbitrage Implementation
 * Target: <7μs latency for opportunity detection
 * 
 * Algorithm:
 * 1. Compare Bitfinex SPOT price with Deribit FUTURES price
 * 2. Calculate raw spread (basis): (futures - spot) / spot * 10000 bps
 * 3. Adjust for funding rate (futures long pay/receive funding)
 * 4. Subtract fees and slippage
 * 5. If net_spread >= min_threshold -> opportunity found
 */

#include "spot_futures_arbitrage.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

SpotFuturesStrategy* spot_futures_create(PriceCache *cache, const char *symbols[], int num_symbols) {
    SpotFuturesStrategy *strategy = malloc(sizeof(SpotFuturesStrategy));
    strategy->cache = cache;
    strategy->min_spread_bps = SPOT_FUTURES_MIN_BPS;
    strategy->target_spread_bps = SPOT_FUTURES_TARGET_BPS;
    strategy->fat_spread_bps = SPOT_FUTURES_FAT_BPS;
    strategy->funding_rate_threshold_bps = MAX_FUNDING_RATE_BPS;
    strategy->num_symbols = num_symbols < 10 ? num_symbols : 10;
    
    for (int i = 0; i < strategy->num_symbols; i++) {
        strncpy(strategy->symbols[i], symbols[i], sizeof(strategy->symbols[i]) - 1);
    }
    
    printf("✅ Spot-Futures Strategy initialized: %.1f/%.1f/%.1f bps thresholds\n",
           strategy->min_spread_bps, strategy->target_spread_bps, strategy->fat_spread_bps);
    
    return strategy;
}

int spot_futures_detect(SpotFuturesStrategy *strategy, Opportunity *opportunities, int max_opps, double funding_rates[]) {
    int num_opps = 0;
    
    // For each symbol, compare spot (Bitfinex) with futures (Deribit)
    for (int s = 0; s < strategy->num_symbols && num_opps < max_opps; s++) {
        const char *symbol = strategy->symbols[s];
        double funding_rate_bps = funding_rates ? funding_rates[s] : 0.0;
        
        // Check funding rate threshold (avoid excessive funding costs)
        if (fabs(funding_rate_bps) > strategy->funding_rate_threshold_bps) {
            continue;  // Skip if funding rate too high
        }
        
        // Get prices from cache
        PriceCacheEntry spot_entry, futures_entry;
        int has_spot = price_cache_get_bid_ask(strategy->cache, symbol, "bitfinex", &spot_entry);
        int has_futures = price_cache_get_bid_ask(strategy->cache, symbol, "deribit", &futures_entry);
        
        if (!has_spot || !has_futures) {
            continue;  // Missing data for this symbol
        }
        
        // Extract bid/ask prices
        double spot_bid = spot_entry.bid;
        double spot_ask = spot_entry.ask;
        double futures_bid = futures_entry.bid;
        double futures_ask = futures_entry.ask;
        
        // Validate prices
        if (spot_bid <= 0 || spot_ask <= 0 || futures_bid <= 0 || futures_ask <= 0) {
            continue;  // Invalid prices
        }
        if (spot_ask < spot_bid || futures_ask < futures_bid) {
            continue;  // Crossed book (invalid)
        }
        
        // Calculate mid prices for basis calculation
        double spot_mid = (spot_bid + spot_ask) * 0.5;
        double futures_mid = (futures_bid + futures_ask) * 0.5;
        
        // Calculate basis (futures premium/discount over spot)
        // basis_bps = (futures - spot) / spot * 10000
        double basis_bps = ((futures_mid - spot_mid) / spot_mid) * 10000.0;
        
        // TWO OPPORTUNITIES:
        // 1. CASH-AND-CARRY: futures > spot (positive basis)
        //    -> Buy spot, Sell futures (capture premium)
        // 2. REVERSE CASH-AND-CARRY: spot > futures (negative basis)
        //    -> Sell spot, Buy futures (capture discount)
        
        // === OPPORTUNITY 1: CASH-AND-CARRY (positive basis) ===
        if (basis_bps > 0) {
            // Execution: Buy spot @ ask, Sell futures @ bid
            double buy_spot_price = spot_ask;
            double sell_futures_price = futures_bid;
            
            // Recalculate actual spread with execution prices
            double actual_basis_bps = ((sell_futures_price - buy_spot_price) / buy_spot_price) * 10000.0;
            
            // Calculate net spread after costs
            double net_spread_bps = calculate_net_spread(actual_basis_bps, funding_rate_bps);
            
            if (net_spread_bps >= strategy->min_spread_bps) {
                // Opportunity found!
                Opportunity *opp = &opportunities[num_opps++];
                strncpy(opp->symbol, symbol, sizeof(opp->symbol) - 1);
                
                // Buy spot, sell futures
                opp->buy_exchange = 0;   // Bitfinex (index 0)
                opp->sell_exchange = 1;  // Deribit (index 1)
                opp->buy_price = buy_spot_price;
                opp->sell_price = sell_futures_price;
                opp->spread_bps = actual_basis_bps;
                opp->net_spread_bps = net_spread_bps;
                opp->timestamp_tsc = rdtsc();
                
                // Classify opportunity quality
                if (net_spread_bps >= strategy->fat_spread_bps) {
                    opp->type = 2;  // FAT opportunity
                } else if (net_spread_bps >= strategy->target_spread_bps) {
                    opp->type = 1;  // TARGET opportunity
                } else {
                    opp->type = 0;  // MIN opportunity
                }
            }
        }
        
        // === OPPORTUNITY 2: REVERSE CASH-AND-CARRY (negative basis) ===
        else if (basis_bps < 0) {
            // Execution: Sell spot @ bid, Buy futures @ ask
            double sell_spot_price = spot_bid;
            double buy_futures_price = futures_ask;
            
            // Recalculate actual spread with execution prices
            // In reverse, we profit from spot > futures
            double actual_basis_bps = ((sell_spot_price - buy_futures_price) / sell_spot_price) * 10000.0;
            
            // Calculate net spread after costs
            // Funding is reversed: if we're short futures, we receive funding
            double net_spread_bps = calculate_net_spread(actual_basis_bps, -funding_rate_bps);
            
            if (net_spread_bps >= strategy->min_spread_bps) {
                // Opportunity found!
                Opportunity *opp = &opportunities[num_opps++];
                strncpy(opp->symbol, symbol, sizeof(opp->symbol) - 1);
                
                // Sell spot, buy futures (reverse)
                opp->sell_exchange = 0;  // Bitfinex (sell spot)
                opp->buy_exchange = 1;   // Deribit (buy futures)
                opp->sell_price = sell_spot_price;
                opp->buy_price = buy_futures_price;
                opp->spread_bps = actual_basis_bps;
                opp->net_spread_bps = net_spread_bps;
                opp->timestamp_tsc = rdtsc();
                
                // Classify opportunity quality
                if (net_spread_bps >= strategy->fat_spread_bps) {
                    opp->type = 2;  // FAT opportunity
                } else if (net_spread_bps >= strategy->target_spread_bps) {
                    opp->type = 1;  // TARGET opportunity
                } else {
                    opp->type = 0;  // MIN opportunity
                }
            }
        }
    }
    
    return num_opps;
}

void spot_futures_destroy(SpotFuturesStrategy *strategy) {
    if (strategy) {
        free(strategy);
    }
}

