/**
 * DRAIZER V2 - Risk Manager Implementation
 * Enterprise-grade risk management with multiple safety layers
 */

#include "risk_manager.h"
#include "../utils/timestamp.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define NS_PER_SECOND 1000000000ULL
#define NS_PER_MINUTE (60ULL * NS_PER_SECOND)

RiskManager* risk_manager_create(double initial_balance) {
    RiskManager *rm = calloc(1, sizeof(RiskManager));
    if (!rm) return NULL;
    
    // Balance settings
    rm->balance_usd = initial_balance;
    rm->initial_balance_usd = initial_balance;
    rm->max_position_usd = initial_balance * 0.10;  // 10% max per trade (conservative!)
    rm->max_total_exposure_pct = 40.0;  // Max 40% total exposure
    rm->max_open_positions = 5;  // Max 5 concurrent positions
    
    // Daily limits
    rm->daily_loss_limit_usd = initial_balance * 0.05;  // 5% max daily loss
    rm->daily_profit_usd = 0.0;
    rm->daily_loss_usd = 0.0;
    rm->orders_placed_today = 0;
    rm->max_orders_per_day = 500;
    
    // Position tracking
    rm->num_open_positions = 0;
    rm->total_exposure_usd = 0.0;
    
    // Volatility tracking
    rm->num_symbols = 0;
    
    // Circuit breaker
    rm->circuit_breaker.is_triggered = false;
    rm->circuit_breaker.cooldown_ns = 15 * NS_PER_MINUTE;  // 15 min cooldown
    rm->circuit_breaker.trigger_loss_pct = 3.0;  // 3% quick loss triggers circuit breaker
    
    // Staleness check
    rm->max_price_age_ns = 2 * NS_PER_SECOND;  // Max 2 seconds old
    
    // Correlation
    rm->max_correlation = 0.8;  // Max 80% correlation
    
    return rm;
}

void risk_manager_destroy(RiskManager *rm) {
    free(rm);
}

// ==================== CIRCUIT BREAKER ====================

bool risk_manager_is_circuit_breaker_active(RiskManager *rm) {
    if (!rm->circuit_breaker.is_triggered) return false;
    
    // Check if cooldown expired
    uint64_t now = rdtsc();
    uint64_t elapsed = now - rm->circuit_breaker.triggered_at_ns;
    
    if (elapsed >= rm->circuit_breaker.cooldown_ns) {
        printf("✅ Circuit breaker cooldown expired, resetting\n");
        rm->circuit_breaker.is_triggered = false;
        return false;
    }
    
    return true;
}

void risk_manager_check_circuit_breaker(RiskManager *rm) {
    if (rm->circuit_breaker.is_triggered) return;
    
    // Check for rapid drawdown
    double drawdown_pct = (rm->daily_loss_usd / rm->initial_balance_usd) * 100.0;
    
    if (drawdown_pct >= rm->circuit_breaker.trigger_loss_pct) {
        rm->circuit_breaker.is_triggered = true;
        rm->circuit_breaker.triggered_at_ns = rdtsc();
        
        printf("🚨 CIRCUIT BREAKER TRIGGERED! Loss: %.2f%% (>= %.2f%%)\n", 
               drawdown_pct, rm->circuit_breaker.trigger_loss_pct);
        printf("   All trading STOPPED for 15 minutes\n");
    }
}

void risk_manager_reset_circuit_breaker(RiskManager *rm) {
    rm->circuit_breaker.is_triggered = false;
    printf("✅ Circuit breaker manually reset\n");
}

// ==================== VOLATILITY TRACKING ====================

void risk_manager_update_volatility(
    RiskManager *rm,
    const char *symbol,
    double price,
    uint64_t timestamp_ns
) {
    // Find or create volatility tracker
    VolatilityTracker *vt = NULL;
    for (uint32_t i = 0; i < rm->num_symbols; i++) {
        if (strcmp(rm->volatility[i].symbol, symbol) == 0) {
            vt = &rm->volatility[i];
            break;
        }
    }
    
    if (!vt && rm->num_symbols < MAX_SYMBOLS) {
        vt = &rm->volatility[rm->num_symbols++];
        strncpy(vt->symbol, symbol, 11);
        vt->volatility_1m = 0.0;
        vt->volatility_5m = 0.0;
        vt->last_update_ns = timestamp_ns;
    }
    
    if (vt) {
        // Simple volatility: percentage price change
        uint64_t elapsed_ns = timestamp_ns - vt->last_update_ns;
        if (elapsed_ns > NS_PER_MINUTE) {
            // Reset if too old
            vt->volatility_1m = 0.0;
            vt->volatility_5m = 0.0;
        }
        vt->last_update_ns = timestamp_ns;
    }
}

double risk_manager_get_volatility(RiskManager *rm, const char *symbol) {
    for (uint32_t i = 0; i < rm->num_symbols; i++) {
        if (strcmp(rm->volatility[i].symbol, symbol) == 0) {
            return rm->volatility[i].volatility_1m;
        }
    }
    return 0.0;
}

// ==================== POSITION MANAGEMENT ====================

uint32_t risk_manager_get_position_count(RiskManager *rm) {
    return rm->num_open_positions;
}

bool risk_manager_has_position(RiskManager *rm, const char *symbol, const char *exchange) {
    for (uint32_t i = 0; i < rm->num_open_positions; i++) {
        Position *pos = &rm->open_positions[i];
        if (strcmp(pos->symbol, symbol) == 0 && strcmp(pos->exchange, exchange) == 0) {
            return true;
        }
    }
    return false;
}

double risk_manager_get_position_exposure(RiskManager *rm, const char *symbol) {
    double exposure = 0.0;
    for (uint32_t i = 0; i < rm->num_open_positions; i++) {
        Position *pos = &rm->open_positions[i];
        if (strcmp(pos->symbol, symbol) == 0) {
            exposure += pos->quantity * pos->entry_price;
        }
    }
    return exposure;
}

int risk_manager_open_position(
    RiskManager *rm,
    const char *symbol,
    const char *exchange,
    double quantity,
    double entry_price,
    bool is_long
) {
    if (rm->num_open_positions >= rm->max_open_positions) {
        printf("❌ Risk: Max positions reached (%u)\n", rm->max_open_positions);
        return -1;
    }
    
    Position *pos = &rm->open_positions[rm->num_open_positions++];
    strncpy(pos->symbol, symbol, 11);
    strncpy(pos->exchange, exchange, 19);
    pos->quantity = quantity;
    pos->entry_price = entry_price;
    pos->opened_at_ns = rdtsc();
    pos->is_long = is_long;
    
    double position_value = quantity * entry_price;
    rm->total_exposure_usd += position_value;
    
    printf("✅ Position opened: %s @ %s (%.4f @ $%.2f) = $%.2f\n",
           symbol, exchange, quantity, entry_price, position_value);
    
    return 0;
}

void risk_manager_close_position(
    RiskManager *rm,
    const char *symbol,
    const char *exchange,
    double exit_price
) {
    for (uint32_t i = 0; i < rm->num_open_positions; i++) {
        Position *pos = &rm->open_positions[i];
        if (strcmp(pos->symbol, symbol) == 0 && strcmp(pos->exchange, exchange) == 0) {
            // Calculate P&L
            double pnl = pos->quantity * (exit_price - pos->entry_price);
            if (!pos->is_long) pnl = -pnl;  // Invert for shorts
            
            double position_value = pos->quantity * pos->entry_price;
            rm->total_exposure_usd -= position_value;
            
            risk_manager_update_balance(rm, pnl);
            
            printf("✅ Position closed: %s @ %s (P&L: $%.2f)\n", symbol, exchange, pnl);
            
            // Remove position (swap with last)
            rm->open_positions[i] = rm->open_positions[--rm->num_open_positions];
            return;
        }
    }
    
    printf("⚠️  Position not found: %s @ %s\n", symbol, exchange);
}

// ==================== ORDER VALIDATION ====================

int risk_manager_check_order(
    RiskManager *rm,
    const char *symbol,
    const char *exchange,
    double quantity,
    double price,
    uint64_t price_timestamp_ns
) {
    double order_value = quantity * price;
    
    // TEMPORARY DEBUG
    static uint64_t check_calls = 0;
    if (++check_calls % 100 == 0) {
        printf("🔍 risk_manager_check_order: call #%lu, symbol=%s, order_value=$%.2f\n",
               check_calls, symbol, order_value);
        fflush(stdout);
    }
    
    // ✅ CHECK 1: Circuit breaker
    if (risk_manager_is_circuit_breaker_active(rm)) {
        printf("🚨 BLOCKED: Circuit breaker active\n");
        fflush(stdout);
        return 0;
    }
    
    // ✅ CHECK 2: Price staleness
    uint64_t now = rdtsc();
    uint64_t price_age_ns = tsc_to_ns(now - price_timestamp_ns);  // Convert TSC to NS!
    if (price_age_ns > rm->max_price_age_ns) {
        printf("❌ Risk: Stale price (age: %.2f seconds)\n", 
               price_age_ns / (double)NS_PER_SECOND);
        return 0;
    }
    
    // ✅ CHECK 3: Position size limit
    if (order_value > rm->max_position_usd) {
        static uint64_t check3_fails = 0;
        if (++check3_fails % 1000 == 0) {
            printf("❌ CHECK 3 FAIL #%lu: Order $%.2f > max $%.2f\n", 
                   check3_fails, order_value, rm->max_position_usd);
        }
        return 0;
    }
    
    // ✅ CHECK 4: Max positions
    if (rm->num_open_positions >= rm->max_open_positions) {
        static uint64_t check4_fails = 0;
        if (++check4_fails % 1000 == 0) {
            printf("❌ CHECK 4 FAIL #%lu: Positions %u/%u\n", 
                   check4_fails, rm->num_open_positions, rm->max_open_positions);
        }
        return 0;
    }
    
    // ✅ CHECK 5: Total exposure limit
    double new_exposure = rm->total_exposure_usd + order_value;
    double exposure_pct = (new_exposure / rm->balance_usd) * 100.0;
    if (exposure_pct > rm->max_total_exposure_pct) {
        static uint64_t check5_fails = 0;
        if (++check5_fails % 1000 == 0) {
            printf("❌ CHECK 5 FAIL #%lu: Exposure %.1f%% > %.1f%%\n", 
                   check5_fails, exposure_pct, rm->max_total_exposure_pct);
        }
        return 0;
    }
    
    // ✅ CHECK 6: Daily loss limit
    if (rm->daily_loss_usd >= rm->daily_loss_limit_usd) {
        printf("❌ Risk: Daily loss limit reached ($%.2f >= $%.2f)\n", 
               rm->daily_loss_usd, rm->daily_loss_limit_usd);
        return 0;
    }
    
    // ✅ CHECK 7: Order count limit
    if (rm->orders_placed_today >= rm->max_orders_per_day) {
        printf("❌ Risk: Max orders/day reached (%u)\n", rm->max_orders_per_day);
        return 0;
    }
    
    // ✅ CHECK 8: Balance check (keep 15% reserve)
    double available = rm->balance_usd - rm->total_exposure_usd;
    if (order_value > available * 0.85) {
        printf("❌ Risk: Insufficient available balance ($%.2f available)\n", available);
        return 0;
    }
    
    // ✅ CHECK 9: Duplicate position check
    if (risk_manager_has_position(rm, symbol, exchange)) {
        printf("❌ Risk: Already have position in %s @ %s\n", symbol, exchange);
        return 0;
    }
    
    // ✅ CHECK 10: Symbol exposure limit (max 20% per symbol)
    double symbol_exposure = risk_manager_get_position_exposure(rm, symbol);
    double symbol_exposure_pct = ((symbol_exposure + order_value) / rm->balance_usd) * 100.0;
    if (symbol_exposure_pct > 20.0) {
        printf("❌ Risk: Symbol exposure %.1f%% > 20%%\n", symbol_exposure_pct);
        return 0;
    }
    
    // ✅ ALL CHECKS PASSED!
    rm->orders_placed_today++;
    return 1;
}

// ==================== BALANCE MANAGEMENT ====================

void risk_manager_update_balance(RiskManager *rm, double pnl) {
    rm->balance_usd += pnl;
    
    if (pnl > 0) {
        rm->daily_profit_usd += pnl;
    } else {
        rm->daily_loss_usd += -pnl;
        
        // Check circuit breaker after each loss
        risk_manager_check_circuit_breaker(rm);
    }
}

double risk_manager_get_available_balance(RiskManager *rm) {
    return rm->balance_usd - rm->total_exposure_usd;
}

double risk_manager_get_total_exposure(RiskManager *rm) {
    return rm->total_exposure_usd;
}

// ==================== DAILY RESET ====================

void risk_manager_reset_daily(RiskManager *rm) {
    printf("🔄 Daily reset: Profit: $%.2f, Loss: $%.2f, Orders: %u\n",
           rm->daily_profit_usd, rm->daily_loss_usd, rm->orders_placed_today);
    
    rm->daily_profit_usd = 0.0;
    rm->daily_loss_usd = 0.0;
    rm->orders_placed_today = 0;
    
    // Reset circuit breaker if it was triggered
    if (rm->circuit_breaker.is_triggered) {
        risk_manager_reset_circuit_breaker(rm);
    }
}
