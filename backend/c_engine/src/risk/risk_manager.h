/**
 * DRAIZER V2 - Risk Manager
 * Enterprise-grade risk management with multiple safety layers
 */

#ifndef RISK_MANAGER_H
#define RISK_MANAGER_H

#include <stdint.h>
#include <stdbool.h>

#define MAX_OPEN_POSITIONS 10
#define MAX_SYMBOLS 50

// Position tracking
typedef struct {
    char symbol[12];
    char exchange[20];
    double quantity;
    double entry_price;
    uint64_t opened_at_ns;
    bool is_long;  // true = long, false = short
} Position;

// Volatility tracker
typedef struct {
    char symbol[12];
    double volatility_1m;   // 1-minute volatility
    double volatility_5m;   // 5-minute volatility
    uint64_t last_update_ns;
} VolatilityTracker;

// Circuit breaker
typedef struct {
    bool is_triggered;
    uint64_t triggered_at_ns;
    uint64_t cooldown_ns;   // Time to wait before resetting
    double trigger_loss_pct; // % loss to trigger
} CircuitBreaker;

typedef struct {
    // Balance & limits
    double balance_usd;
    double initial_balance_usd;
    double max_position_usd;
    double max_total_exposure_pct;
    uint32_t max_open_positions;
    
    // Daily limits
    double daily_loss_limit_usd;
    double daily_profit_usd;
    double daily_loss_usd;
    uint32_t orders_placed_today;
    uint32_t max_orders_per_day;
    
    // Position tracking
    Position open_positions[MAX_OPEN_POSITIONS];
    uint32_t num_open_positions;
    double total_exposure_usd;
    
    // Volatility tracking
    VolatilityTracker volatility[MAX_SYMBOLS];
    uint32_t num_symbols;
    
    // Circuit breaker
    CircuitBreaker circuit_breaker;
    
    // Staleness check
    uint64_t max_price_age_ns;  // Max age for price data
    
    // Correlation (anti-hedging)
    double max_correlation;  // Max correlation between positions
} RiskManager;

// Core functions
RiskManager* risk_manager_create(double initial_balance);
void risk_manager_destroy(RiskManager *rm);

// Order validation (COMPREHENSIVE)
int risk_manager_check_order(
    RiskManager *rm,
    const char *symbol,
    const char *exchange,
    double quantity,
    double price,
    uint64_t price_timestamp_ns
);

// Position management
int risk_manager_open_position(
    RiskManager *rm,
    const char *symbol,
    const char *exchange,
    double quantity,
    double entry_price,
    bool is_long
);

void risk_manager_close_position(
    RiskManager *rm,
    const char *symbol,
    const char *exchange,
    double exit_price
);

// Balance & P&L
void risk_manager_update_balance(RiskManager *rm, double pnl);
double risk_manager_get_available_balance(RiskManager *rm);
double risk_manager_get_total_exposure(RiskManager *rm);

// Circuit breaker
bool risk_manager_is_circuit_breaker_active(RiskManager *rm);
void risk_manager_check_circuit_breaker(RiskManager *rm);
void risk_manager_reset_circuit_breaker(RiskManager *rm);

// Volatility
void risk_manager_update_volatility(
    RiskManager *rm,
    const char *symbol,
    double price,
    uint64_t timestamp_ns
);

double risk_manager_get_volatility(RiskManager *rm, const char *symbol);

// Daily reset
void risk_manager_reset_daily(RiskManager *rm);

// Position checks
uint32_t risk_manager_get_position_count(RiskManager *rm);
double risk_manager_get_position_exposure(RiskManager *rm, const char *symbol);
bool risk_manager_has_position(RiskManager *rm, const char *symbol, const char *exchange);

#endif // RISK_MANAGER_H

