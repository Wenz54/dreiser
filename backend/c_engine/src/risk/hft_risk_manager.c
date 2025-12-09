/**
 * DRAIZER V2 - HFT Risk Manager Implementation
 * Ultra-low latency risk management для high-frequency arbitrage
 */

#include "hft_risk_manager.h"
#include "../utils/timestamp.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#define NS_PER_SECOND 1000000000ULL
#define NS_PER_MINUTE (60ULL * NS_PER_SECOND)
#define NS_PER_DAY (24ULL * 60ULL * NS_PER_MINUTE)

// ==================== CREATION / DESTRUCTION ====================

HFTRiskManager* hft_risk_manager_create(double initial_balance, bool paper_mode) {
    HFTRiskManager *rm = calloc(1, sizeof(HFTRiskManager));
    if (!rm) return NULL;
    
    rm->balance_usd = initial_balance;
    rm->initial_balance_usd = initial_balance;
    rm->paper_mode = paper_mode;
    
    // ========== TIME-WEIGHTED LIMITS (REALISTIC FOR SOLO HFT) ==========
    rm->time_limits.burst_orders_limit = 20;           // 20 orders per micro-burst
    rm->time_limits.burst_window_ns = 50000000ULL;     // 50ms window
    rm->time_limits.orders_per_second_limit = 500;     // 500 orders/sec
    rm->time_limits.orders_per_minute_limit = 20000;   // 20K orders/min
    rm->time_limits.orders_per_day_limit = 1000000;    // 1M orders/day
    
    // ========== MARKET REGIME ==========
    rm->regime.current_regime = REGIME_NORMAL;
    rm->regime.regime_changed_at_ns = rdtsc();
    
    // ========== STRATEGY CONFIGS (MICRO POSITIONS: 1-2% BALANCE) ==========
    double micro_position = initial_balance * 0.015;  // 1.5% of balance
    
    // Strategy 0: Statistical Arbitrage
    rm->strategy_configs[0].enabled = true;
    rm->strategy_configs[0].priority = 1;
    rm->strategy_configs[0].max_position_usd = micro_position;
    rm->strategy_configs[0].min_profit_usd = 0.04;     // $0.04 minimum profit
    rm->strategy_configs[0].current_multiplier = 1.0;
    
    // Strategy 1: Cross-Exchange Arbitrage
    rm->strategy_configs[1].enabled = true;
    rm->strategy_configs[1].priority = 2;
    rm->strategy_configs[1].max_position_usd = micro_position * 1.3;  // Slightly larger
    rm->strategy_configs[1].min_profit_usd = 0.005;    // $0.005 for paper trading (0.5 cent)
    rm->strategy_configs[1].current_multiplier = 1.0;
    
    // Strategy 2: Triangular Arbitrage
    rm->strategy_configs[2].enabled = true;
    rm->strategy_configs[2].priority = 3;
    rm->strategy_configs[2].max_position_usd = micro_position * 1.5;
    rm->strategy_configs[2].min_profit_usd = 0.08;     // $0.08 minimum profit
    rm->strategy_configs[2].current_multiplier = 1.0;
    
    // ========== CIRCUIT BREAKER ==========
    rm->circuit_breaker_active = false;
    rm->circuit_breaker_overrides_left = 100;  // 100 overrides per day
    
    printf("✅ HFT Risk Manager initialized (balance: $%.2f, mode: %s)\n",
           initial_balance, paper_mode ? "PAPER" : "LIVE");
    
    return rm;
}

void hft_risk_manager_destroy(HFTRiskManager *rm) {
    free(rm);
}

// ==================== MARKET REGIME DETECTION ====================

void hft_risk_update_regime(
    HFTRiskManager *rm,
    double current_volatility,
    double current_spread_bps
) {
    rm->regime.volatility_1m = current_volatility;
    rm->regime.avg_spread_bps = current_spread_bps;
    rm->regime.tick_count++;
    
    // Determine regime based on volatility
    MarketRegime old_regime = rm->regime.current_regime;
    
    if (current_volatility < 5.0 && current_spread_bps < 5.0) {
        rm->regime.current_regime = REGIME_LOW_VOL;
    } else if (current_volatility < 20.0 && current_spread_bps < 20.0) {
        rm->regime.current_regime = REGIME_NORMAL;
    } else if (current_volatility < 50.0 && current_spread_bps < 50.0) {
        rm->regime.current_regime = REGIME_HIGH_VOL;
    } else {
        rm->regime.current_regime = REGIME_EXTREME;
    }
    
    // Log regime changes
    if (old_regime != rm->regime.current_regime) {
        const char *regime_names[] = {"LOW_VOL", "NORMAL", "HIGH_VOL", "EXTREME"};
        printf("🔄 Market regime changed: %s → %s (vol=%.2f, spread=%.2f bps)\n",
               regime_names[old_regime], regime_names[rm->regime.current_regime],
               current_volatility, current_spread_bps);
        rm->regime.regime_changed_at_ns = rdtsc();
    }
}

// ==================== TIME-WEIGHTED LIMIT CHECKS ====================

static inline bool check_time_weighted_limits(HFTRiskManager *rm, uint64_t now_tsc) {
    uint64_t now_ns = tsc_to_ns(now_tsc);
    TimeWeightedLimits *tl = &rm->time_limits;
    
    // ========== MICRO-BURST CHECK (10-50ms window) ==========
    if (now_ns - tl->burst_started_at_ns > tl->burst_window_ns) {
        // New burst window
        tl->burst_started_at_ns = now_ns;
        tl->burst_orders_count = 0;
    }
    
    if (tl->burst_orders_count >= tl->burst_orders_limit) {
        // SOFT LIMIT - allow override for arbitrage
        static uint64_t burst_warns = 0;
        if (++burst_warns % 10000 == 0) {
            printf("⚠️  Micro-burst limit reached (%u orders in 50ms)\n", tl->burst_orders_count);
        }
        // Don't block - just warn
    }
    
    // ========== PER-SECOND CHECK ==========
    uint64_t current_second = now_ns / NS_PER_SECOND;
    if (current_second != tl->current_second_ns) {
        tl->current_second_ns = current_second;
        tl->orders_this_second = 0;
    }
    
    if (tl->orders_this_second >= tl->orders_per_second_limit) {
        return false;  // HARD LIMIT
    }
    
    // ========== PER-MINUTE CHECK ==========
    uint64_t current_minute = now_ns / NS_PER_MINUTE;
    if (current_minute != tl->current_minute_ns) {
        tl->current_minute_ns = current_minute;
        tl->orders_this_minute = 0;
    }
    
    if (tl->orders_this_minute >= tl->orders_per_minute_limit) {
        return false;  // HARD LIMIT
    }
    
    // ========== PER-DAY CHECK ==========
    uint64_t current_day = now_ns / NS_PER_DAY;
    if (current_day != tl->day_started_at_ns) {
        // New day - reset counters
        hft_risk_reset_daily(rm);
    }
    
    if (tl->orders_today >= tl->orders_per_day_limit) {
        return false;  // HARD LIMIT
    }
    
    return true;
}

static inline void increment_time_counters(HFTRiskManager *rm) {
    TimeWeightedLimits *tl = &rm->time_limits;
    tl->burst_orders_count++;
    tl->orders_this_second++;
    tl->orders_this_minute++;
    tl->orders_today++;
}

// ==================== NET EXPOSURE MANAGEMENT ====================

void hft_risk_update_net_exposure(
    HFTRiskManager *rm,
    const char *symbol,
    const char *exchange,
    double quantity,
    bool is_buy
) {
    // Find or create net exposure entry
    NetExposure *net = NULL;
    for (uint32_t i = 0; i < rm->num_net_positions; i++) {
        if (strcmp(rm->net_exposures[i].symbol, symbol) == 0) {
            net = &rm->net_exposures[i];
            break;
        }
    }
    
    if (!net && rm->num_net_positions < MAX_NET_POSITIONS) {
        net = &rm->net_exposures[rm->num_net_positions++];
        strncpy(net->symbol, symbol, 11);
        net->net_position = 0.0;
        net->long_exposure = 0.0;
        net->short_exposure = 0.0;
    }
    
    if (net) {
        if (is_buy) {
            net->long_exposure += quantity;
            net->net_position += quantity;
        } else {
            net->short_exposure += quantity;
            net->net_position -= quantity;
        }
        
        // Check if hedged (net close to zero)
        net->is_hedged = fabs(net->net_position) < 0.01 * fmax(net->long_exposure, net->short_exposure);
    }
}

// ==================== LIQUIDITY TRACKING ====================

void hft_risk_update_liquidity(
    HFTRiskManager *rm,
    const char *symbol,
    const char *exchange,
    double bid_volume,
    double ask_volume
) {
    // Find or create liquidity snapshot
    LiquiditySnapshot *liq = NULL;
    for (uint32_t i = 0; i < rm->num_liquidity_snapshots; i++) {
        if (strcmp(rm->liquidity[i].symbol, symbol) == 0 &&
            strcmp(rm->liquidity[i].exchange, exchange) == 0) {
            liq = &rm->liquidity[i];
            break;
        }
    }
    
    if (!liq && rm->num_liquidity_snapshots < MAX_LIQUIDITY_SNAPSHOTS) {
        liq = &rm->liquidity[rm->num_liquidity_snapshots++];
        strncpy(liq->symbol, symbol, 11);
        strncpy(liq->exchange, exchange, 19);
    }
    
    if (liq) {
        liq->bid_volume = bid_volume;
        liq->ask_volume = ask_volume;
        liq->max_safe_size_usd = fmin(bid_volume, ask_volume) * 0.1;  // 10% of min volume
        liq->updated_at_ns = tsc_to_ns(rdtsc());
    }
}

// ==================== MAIN ORDER VALIDATION (ULTRA FAST) ====================

int hft_risk_check_order(
    HFTRiskManager *rm,
    uint8_t strategy_id,
    const char *symbol,
    const char *buy_exchange,
    const char *sell_exchange,
    double quantity,
    double buy_price,
    double sell_price,
    uint64_t detected_at_tsc,
    uint64_t latency_us
) {
    uint64_t now_tsc = rdtsc();
    double order_value = quantity * buy_price;
    
    // Performance tracking (minimal overhead)
    static uint64_t total_checks = 0;
    total_checks++;
    
    // ========== CHECK 1: Strategy Enabled ===========
    if (strategy_id >= 10 || !rm->strategy_configs[strategy_id].enabled) {
        return 0;
    }
    
    StrategyRiskConfig *strategy = &rm->strategy_configs[strategy_id];
    
    // ========== CHECK 2: Time-Weighted Limits ==========
    if (!check_time_weighted_limits(rm, now_tsc)) {
        return 0;
    }
    
    // ========== CHECK 3: Latency-Adjusted Position Size ==========
    double max_position = strategy->max_position_usd * strategy->current_multiplier;
    
    // LATENCY BONUS: Lower latency = higher position size allowed
    if (latency_us < 10) {
        max_position *= 1.5;  // 50% bonus for ultra-low latency (<10μs)
    } else if (latency_us < 50) {
        max_position *= 1.2;  // 20% bonus for very low latency (<50μs)
    }
    
    // MARKET REGIME ADJUSTMENT
    switch (rm->regime.current_regime) {
        case REGIME_LOW_VOL:
            max_position *= 1.3;  // Increase in stable markets
            break;
        case REGIME_HIGH_VOL:
            max_position *= 0.7;  // Decrease in volatile markets
            break;
        case REGIME_EXTREME:
            max_position *= 0.3;  // Aggressive decrease in extreme conditions
            break;
        default:
            break;  // REGIME_NORMAL - no adjustment
    }
    
    if (order_value > max_position) {
        return 0;
    }
    
    // ========== CHECK 4: Dynamic Spread Filtering ==========
    double spread_bps = ((sell_price - buy_price) / buy_price) * 10000.0;
    
    // Determine pair type and min spread
    double min_spread_bps = ABSOLUTE_MIN_SPREAD_BPS;
    bool is_btc_pair = strstr(symbol, "BTC") != NULL;
    bool is_cross_pair = strcmp(buy_exchange, sell_exchange) != 0;
    
    if (is_btc_pair) {
        min_spread_bps = BTC_MIN_SPREAD_BPS;  // 4 bps for BTC (high competition)
    } else if (is_cross_pair) {
        min_spread_bps = CROSS_MIN_SPREAD_BPS;  // 8 bps for cross-pairs (max profit)
    } else {
        min_spread_bps = ALT_MIN_SPREAD_BPS;  // 6 bps for ALTs
    }
    
    // DYNAMIC ADJUSTMENT based on liquidity
    // TODO: Get actual liquidity ratio from orderbook
    double liquidity_ratio = 0.5;  // Placeholder
    if (liquidity_ratio > 0.8) {
        min_spread_bps *= 0.75;  // Can go lower in high liquidity (3 bps for BTC)
    }
    
    // DYNAMIC ADJUSTMENT based on volatility
    if (rm->regime.current_regime == REGIME_HIGH_VOL) {
        min_spread_bps *= 1.3;  // Increase in volatile markets
    } else if (rm->regime.current_regime == REGIME_LOW_VOL) {
        min_spread_bps *= 0.9;  // Can be more aggressive in stable markets
    }
    
    // Calculate net profit after fees and slippage
    double commission_bps = 10.0;  // 0.1% per side
    double slippage_bps = 2.0;     // 0.02% estimated slippage
    double net_spread_bps = spread_bps - (commission_bps * 2) - slippage_bps;
    
    // Check if net profitable
    if (net_spread_bps < min_spread_bps) {
        return 0;
    }
    
    // PRIORITY SYSTEM based on spread size
    uint8_t priority = 3;  // Default: low priority
    if (spread_bps >= FAT_OPPORTUNITY_BPS) {
        priority = 0;  // IMMEDIATE: 0.12%+ spreads
    } else if (spread_bps >= SWEET_SPOT_BPS) {
        priority = 1;  // HIGH: 0.08-0.12% spreads
    } else if (spread_bps >= TARGET_SPREAD_BPS) {
        priority = 2;  // STANDARD: 0.06-0.08% spreads
    }
    // priority 3: Only execute in high liquidity conditions
    
    // For low priority, require high liquidity
    if (priority >= 3 && liquidity_ratio < 0.7) {
        return 0;
    }
    
    // Expected profit in USD
    double expected_profit = (net_spread_bps / 10000.0) * order_value;
    if (expected_profit < strategy->min_profit_usd) {
        return 0;
    }
    
    // ========== CHECK 5: Cross-Exchange Net Exposure ==========
    // For arbitrage, we BUY on one exchange and SELL on another = HEDGED
    // This is ALLOWED even if we have high gross exposure
    bool is_cross_exchange_arb = strcmp(buy_exchange, sell_exchange) != 0;
    
    if (is_cross_exchange_arb) {
        // Cross-exchange arbitrage is ALWAYS hedged - more lenient limits
        // NO NET EXPOSURE CHECK
    } else {
        // Same-exchange trade - check net exposure
        double current_net = 0.0;
        for (uint32_t i = 0; i < rm->num_net_positions; i++) {
            if (strcmp(rm->net_exposures[i].symbol, symbol) == 0) {
                current_net = rm->net_exposures[i].net_position;
                break;
            }
        }
        
        // Limit net exposure to 500% of balance (very aggressive)
        if (fabs(current_net + quantity) > rm->balance_usd * 5.0) {
            return 0;
        }
    }
    
    // ========== CHECK 6: Circuit Breaker Override ==========
    if (rm->circuit_breaker_active) {
        // For confirmed arbitrage opportunities, allow override
        if (is_cross_exchange_arb && expected_profit > strategy->min_profit_usd * 2.0) {
            if (!hft_risk_request_circuit_breaker_override(rm)) {
                return 0;  // No overrides left
            }
        } else {
            return 0;  // Circuit breaker active
        }
    }
    
    // ========== CHECK 7: Performance-Adaptive Limits ==========
    // If strategy is performing well, increase limits
    if (strategy->total_trades > 100) {
        double win_rate = (double)strategy->winning_trades / strategy->total_trades;
        
        if (win_rate > 0.75 && strategy->cumulative_pnl > 0) {
            // Excellent performance - increase multiplier
            strategy->current_multiplier = fmin(2.0, strategy->current_multiplier * 1.01);
        } else if (win_rate < 0.50 || strategy->cumulative_pnl < -100.0) {
            // Poor performance - decrease multiplier
            strategy->current_multiplier = fmax(0.5, strategy->current_multiplier * 0.99);
        }
    }
    
    // ========== ALL CHECKS PASSED ===========
    increment_time_counters(rm);
    return 1;
}

// ==================== PERFORMANCE TRACKING ====================

void hft_risk_record_trade(
    HFTRiskManager *rm,
    uint8_t strategy_id,
    double pnl,
    uint64_t latency_us
) {
    if (strategy_id >= 10) return;
    
    StrategyRiskConfig *strategy = &rm->strategy_configs[strategy_id];
    
    strategy->total_trades++;
    strategy->cumulative_pnl += pnl;
    
    if (pnl > 0) {
        strategy->winning_trades++;
        rm->win_streak++;
        rm->loss_streak = 0;
    } else {
        rm->win_streak = 0;
        rm->loss_streak++;
    }
    
    rm->total_pnl_today += pnl;
    rm->balance_usd += pnl;
    
    // Track ultra-low latency trades
    if (latency_us < 10) {
        rm->ultra_low_latency_trades++;
    }
    
    // Update average latency (exponential moving average)
    rm->avg_latency_us = rm->avg_latency_us * 0.95 + latency_us * 0.05;
    
    // Log performance milestones
    if (strategy->total_trades % 1000 == 0) {
        double win_rate = (double)strategy->winning_trades / strategy->total_trades * 100.0;
        printf("📊 Strategy %u: %u trades, %.1f%% win rate, $%.2f PnL, %.1fx multiplier\n",
               strategy_id, strategy->total_trades, win_rate, strategy->cumulative_pnl,
               strategy->current_multiplier);
    }
}

// ==================== CIRCUIT BREAKER ====================

bool hft_risk_request_circuit_breaker_override(HFTRiskManager *rm) {
    if (rm->circuit_breaker_overrides_left > 0) {
        rm->circuit_breaker_overrides_left--;
        return true;
    }
    return false;
}

void hft_risk_reset_circuit_breaker(HFTRiskManager *rm) {
    rm->circuit_breaker_active = false;
    rm->circuit_breaker_triggered_at_ns = 0;
    printf("✅ Circuit breaker reset\n");
}

// ==================== DAILY RESET ====================

void hft_risk_reset_daily(HFTRiskManager *rm) {
    uint64_t now_ns = tsc_to_ns(rdtsc());
    
    printf("🔄 Daily reset: PnL: $%.2f, Orders: %u, Win streak: %u\n",
           rm->total_pnl_today, rm->time_limits.orders_today, rm->win_streak);
    
    rm->time_limits.orders_today = 0;
    rm->time_limits.day_started_at_ns = now_ns / NS_PER_DAY;
    rm->total_pnl_today = 0.0;
    rm->circuit_breaker_overrides_left = 100;  // Reset overrides
    
    // Reset strategy multipliers to 1.0
    for (int i = 0; i < 10; i++) {
        rm->strategy_configs[i].current_multiplier = 1.0;
    }
}

