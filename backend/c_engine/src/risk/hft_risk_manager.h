/**
 * DRAIZER V2 - HFT Risk Manager
 * Ultra-low latency risk management для high-frequency arbitrage
 */

#ifndef HFT_RISK_MANAGER_H
#define HFT_RISK_MANAGER_H

#include <stdint.h>
#include <stdbool.h>

// ==================== SPREAD PARAMETERS ====================
// Updated for Bitfinex (spot) + Deribit (futures) arbitrage
// Fees: Bitfinex 0.10-0.20% + Deribit 0.05%/-0.025% = ~0.1075% effective
// Slippage: ~0.02%
// Total cost: ~0.1275%

// Absolute minimum spread thresholds (in basis points)
#define ABSOLUTE_MIN_SPREAD_BPS   10.0   // 0.10% - minimum profitable (covers fees + slippage)
#define TARGET_SPREAD_BPS         15.0   // 0.15% - comfortable target
#define SWEET_SPOT_BPS            20.0   // 0.20% - "жирные" возможности
#define IDEAL_ENTRY_BPS           17.0   // 0.17% - идеальная точка входа
#define FAT_OPPORTUNITY_BPS       25.0   // 0.25% - очень "жирные" возможности

// Strategy-specific spread ranges (in bps)
#define SPOT_FUTURES_MIN_BPS      10.0   // Spot-futures: учитываем funding rate
#define SPOT_FUTURES_TARGET_BPS   15.0
#define SPOT_FUTURES_FAT_BPS      25.0
#define STATISTICAL_MIN_BPS       5.0    // Statistical: внутрибиржевой, низкие fees
#define STATISTICAL_TARGET_BPS    8.0
#define TRIANGULAR_MIN_BPS        100.0  // Triangular: высокие требования (3 ноги)

// ==================== MARKET REGIME ====================

typedef enum {
    REGIME_LOW_VOL,        // Low volatility, tight spreads
    REGIME_NORMAL,         // Normal market conditions
    REGIME_HIGH_VOL,       // High volatility, wide spreads
    REGIME_EXTREME         // Extreme conditions, circuit breakers
} MarketRegime;

typedef struct {
    MarketRegime current_regime;
    uint64_t regime_changed_at_ns;
    double volatility_1m;
    double volatility_5m;
    double avg_spread_bps;
    uint32_t tick_count;
} MarketRegimeDetector;

// ==================== STRATEGY-SPECIFIC CONFIG ====================

typedef struct {
    bool enabled;
    uint8_t priority;  // 1=highest, 255=lowest
    
    // Position sizing
    double max_position_usd;
    double min_profit_usd;
    
    // Performance tracking
    uint32_t total_trades;
    uint32_t winning_trades;
    double cumulative_pnl;
    
    // Adaptive limits
    double current_multiplier;  // 0.5-2.0x based on performance
} StrategyRiskConfig;

// ==================== TIME-WEIGHTED LIMITS ====================

typedef struct {
    // Micro-burst windows (10-50ms)
    uint32_t burst_orders_limit;         // Max orders during burst
    uint64_t burst_window_ns;            // Burst window duration
    uint32_t burst_orders_count;
    uint64_t burst_started_at_ns;
    
    // Short-term (1s)
    uint32_t orders_per_second_limit;
    uint32_t orders_this_second;
    uint64_t current_second_ns;
    
    // Medium-term (1min)
    uint32_t orders_per_minute_limit;
    uint32_t orders_this_minute;
    uint64_t current_minute_ns;
    
    // Long-term (1day)
    uint32_t orders_per_day_limit;
    uint32_t orders_today;
    uint64_t day_started_at_ns;
} TimeWeightedLimits;

// ==================== CROSS-EXCHANGE NET EXPOSURE ====================

typedef struct {
    char symbol[12];
    double net_position;       // Net across all exchanges
    double long_exposure;      // Total long exposure
    double short_exposure;     // Total short exposure
    bool is_hedged;            // Is position hedged?
} NetExposure;

#define MAX_NET_POSITIONS 50

// ==================== LIQUIDITY TRACKING ====================

typedef struct {
    char symbol[12];
    char exchange[20];
    double bid_volume;
    double ask_volume;
    double max_safe_size_usd;  // Calculated from orderbook depth
    uint64_t updated_at_ns;
} LiquiditySnapshot;

#define MAX_LIQUIDITY_SNAPSHOTS 100

// ==================== CORRELATION MATRIX ====================

typedef struct {
    char symbol[12];
    double correlations[20];  // Correlation with other symbols
} CorrelationData;

// ==================== HFT RISK MANAGER ====================

typedef struct {
    // Core settings
    double balance_usd;
    double initial_balance_usd;
    bool paper_mode;
    
    // Market regime
    MarketRegimeDetector regime;
    
    // Strategy configs (indexed by strategy type)
    StrategyRiskConfig strategy_configs[10];
    
    // Time-weighted limits
    TimeWeightedLimits time_limits;
    
    // Cross-exchange net exposure
    NetExposure net_exposures[MAX_NET_POSITIONS];
    uint32_t num_net_positions;
    
    // Liquidity tracking
    LiquiditySnapshot liquidity[MAX_LIQUIDITY_SNAPSHOTS];
    uint32_t num_liquidity_snapshots;
    
    // Correlation matrix
    CorrelationData correlations[20];
    uint32_t num_correlations;
    
    // Circuit breaker
    bool circuit_breaker_active;
    uint32_t circuit_breaker_overrides_left;  // Limited overrides per day
    uint64_t circuit_breaker_triggered_at_ns;
    
    // Performance tracking
    double total_pnl_today;
    uint32_t win_streak;
    uint32_t loss_streak;
    
    // Latency tracking
    double avg_latency_us;
    uint32_t ultra_low_latency_trades;  // <10μs end-to-end
} HFTRiskManager;

// ==================== API ====================

// Creation/Destruction
HFTRiskManager* hft_risk_manager_create(double initial_balance, bool paper_mode);
void hft_risk_manager_destroy(HFTRiskManager *rm);

// Order validation (ULTRA FAST)
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
);

// Position management
void hft_risk_update_net_exposure(
    HFTRiskManager *rm,
    const char *symbol,
    const char *exchange,
    double quantity,
    bool is_buy
);

// Liquidity updates
void hft_risk_update_liquidity(
    HFTRiskManager *rm,
    const char *symbol,
    const char *exchange,
    double bid_volume,
    double ask_volume
);

// Market regime detection
void hft_risk_update_regime(
    HFTRiskManager *rm,
    double current_volatility,
    double current_spread_bps
);

// Performance tracking
void hft_risk_record_trade(
    HFTRiskManager *rm,
    uint8_t strategy_id,
    double pnl,
    uint64_t latency_us
);

// Circuit breaker
bool hft_risk_request_circuit_breaker_override(HFTRiskManager *rm);
void hft_risk_reset_circuit_breaker(HFTRiskManager *rm);

// Daily reset
void hft_risk_reset_daily(HFTRiskManager *rm);

#endif // HFT_RISK_MANAGER_H

