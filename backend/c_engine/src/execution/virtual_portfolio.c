/**
 * DRAIZER V2 - Virtual Portfolio Manager Implementation
 * Paper trading: виртуальные балансы и позиции
 */

#include "virtual_portfolio.h"
#include "../utils/timestamp.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

static uint64_t next_operation_id = 1;

VirtualPortfolio* virtual_portfolio_create(double initial_balance_usd) {
    VirtualPortfolio *vp = calloc(1, sizeof(VirtualPortfolio));
    if (!vp) return NULL;
    
    vp->num_positions = 0;
    vp->num_balances = 0;
    vp->operations_head = 0;
    vp->total_operations = 0;
    
    vp->initial_balance_usd = initial_balance_usd;
    vp->current_balance_usd = initial_balance_usd;
    vp->total_pnl_usd = 0.0;
    vp->total_fees_paid = 0.0;
    vp->wins = 0;
    vp->losses = 0;
    vp->win_rate = 0.0;
    vp->avg_profit_per_trade = 0.0;
    vp->max_drawdown_usd = 0.0;
    vp->has_new_operation = false;
    
    // Инициализировать USDT баланс
    virtual_portfolio_init_balance(vp, "USDT", initial_balance_usd);
    
    return vp;
}

void virtual_portfolio_destroy(VirtualPortfolio *vp) {
    free(vp);
}

void virtual_portfolio_init_balance(VirtualPortfolio *vp, const char *currency, double amount) {
    if (vp->num_balances >= MAX_VIRTUAL_BALANCES) return;
    
    VirtualBalance *bal = &vp->balances[vp->num_balances++];
    strncpy(bal->currency, currency, 11);
    bal->currency[11] = '\0';
    bal->total = amount;
    bal->available = amount;
    bal->locked = 0.0;
}

double virtual_portfolio_get_balance(VirtualPortfolio *vp, const char *currency) {
    for (uint32_t i = 0; i < vp->num_balances; i++) {
        if (strcmp(vp->balances[i].currency, currency) == 0) {
            return vp->balances[i].total;
        }
    }
    return 0.0;
}

double virtual_portfolio_get_available_balance(VirtualPortfolio *vp, const char *currency) {
    for (uint32_t i = 0; i < vp->num_balances; i++) {
        if (strcmp(vp->balances[i].currency, currency) == 0) {
            return vp->balances[i].available;
        }
    }
    return 0.0;
}

int virtual_portfolio_open_position(
    VirtualPortfolio *vp,
    const char *symbol,
    const char *exchange,
    double quantity,
    double price,
    bool is_long,
    const char *strategy,
    double fees
) {
    if (vp->num_positions >= MAX_VIRTUAL_POSITIONS) {
        printf("❌ Virtual Portfolio: Max positions reached\n");
        return -1;
    }
    
    double position_value = quantity * price;
    double total_cost = position_value + fees;
    
    // Проверить доступный баланс USDT
    double available_usdt = virtual_portfolio_get_available_balance(vp, "USDT");
    if (total_cost > available_usdt) {
        printf("❌ Virtual Portfolio: Insufficient USDT balance (need $%.2f, have $%.2f)\n",
               total_cost, available_usdt);
        return -1;
    }
    
    // Списать USDT
    for (uint32_t i = 0; i < vp->num_balances; i++) {
        if (strcmp(vp->balances[i].currency, "USDT") == 0) {
            vp->balances[i].available -= total_cost;
            vp->balances[i].locked += position_value;
            break;
        }
    }
    
    // Создать позицию
    VirtualPosition *pos = &vp->positions[vp->num_positions++];
    strncpy(pos->symbol, symbol, 11);
    pos->symbol[11] = '\0';
    strncpy(pos->exchange, exchange, 19);
    pos->exchange[19] = '\0';
    strncpy(pos->strategy, strategy, 19);
    pos->strategy[19] = '\0';
    pos->quantity = quantity;
    pos->entry_price = price;
    pos->current_price = price;
    pos->unrealized_pnl = 0.0;
    pos->opened_at_ns = rdtsc();
    pos->is_long = is_long;
    
    // Создать операцию
    VirtualOperation *op = &vp->operations[vp->operations_head];
    vp->operations_head = (vp->operations_head + 1) % 1000;
    vp->total_operations++;
    
    op->id = next_operation_id++;
    op->timestamp_ns = rdtsc();
    strncpy(op->type, is_long ? "LONG" : "SHORT", 19);
    op->type[19] = '\0';
    strncpy(op->strategy, strategy, 19);
    op->strategy[19] = '\0';
    strncpy(op->symbol, symbol, 11);
    op->symbol[11] = '\0';
    strncpy(op->exchange_buy, exchange, 19);
    op->exchange_buy[19] = '\0';
    op->exchange_sell[0] = '\0';  // Пока не закрыта
    op->quantity = quantity;
    op->entry_price = price;
    op->exit_price = 0.0;
    op->pnl = 0.0;
    op->pnl_percent = 0.0;
    op->spread_bps = 0.0;
    op->fees_paid = fees;
    op->is_open = true;
    
    // Сохранить как последнюю операцию
    vp->last_operation = *op;
    vp->has_new_operation = true;
    
    vp->total_fees_paid += fees;
    
    printf("✅ VIRTUAL: Opened %s position: %s @ %s (%.4f @ $%.2f) = $%.2f\n",
           is_long ? "LONG" : "SHORT", symbol, exchange, quantity, price, position_value);
    
    return 0;
}

int virtual_portfolio_close_position(
    VirtualPortfolio *vp,
    const char *symbol,
    const char *exchange,
    double exit_price,
    double fees
) {
    // Найти позицию
    int pos_idx = -1;
    for (uint32_t i = 0; i < vp->num_positions; i++) {
        VirtualPosition *pos = &vp->positions[i];
        if (strcmp(pos->symbol, symbol) == 0 && strcmp(pos->exchange, exchange) == 0) {
            pos_idx = i;
            break;
        }
    }
    
    if (pos_idx < 0) {
        printf("⚠️  VIRTUAL: Position not found: %s @ %s\n", symbol, exchange);
        return -1;
    }
    
    VirtualPosition *pos = &vp->positions[pos_idx];
    
    // Рассчитать P&L
    double pnl = pos->quantity * (exit_price - pos->entry_price);
    if (!pos->is_long) pnl = -pnl;  // Инвертировать для SHORT
    pnl -= fees;  // Вычесть комиссии
    
    double pnl_percent = (pnl / (pos->quantity * pos->entry_price)) * 100.0;
    double position_value = pos->quantity * pos->entry_price;
    
    // Вернуть USDT
    for (uint32_t i = 0; i < vp->num_balances; i++) {
        if (strcmp(vp->balances[i].currency, "USDT") == 0) {
            vp->balances[i].locked -= position_value;
            vp->balances[i].available += position_value + pnl;
            vp->balances[i].total += pnl;
            break;
        }
    }
    
    // Обновить статистику
    vp->total_pnl_usd += pnl;
    vp->total_fees_paid += fees;
    vp->current_balance_usd += pnl;
    
    if (pnl > 0) {
        vp->wins++;
    } else {
        vp->losses++;
    }
    
    // Обновить операцию
    for (int i = vp->operations_head - 1; i >= 0; i--) {
        VirtualOperation *op = &vp->operations[i];
        if (strcmp(op->symbol, symbol) == 0 && op->is_open) {
            op->exit_price = exit_price;
            op->pnl = pnl;
            op->pnl_percent = pnl_percent;
            op->is_open = false;
            strncpy(op->exchange_sell, exchange, 19);
            op->exchange_sell[19] = '\0';
            op->fees_paid += fees;
            
            // Сохранить как последнюю операцию
            vp->last_operation = *op;
            vp->has_new_operation = true;
            break;
        }
    }
    
    printf("✅ VIRTUAL: Closed position: %s @ %s (P&L: $%.2f / %.2f%%)\n",
           symbol, exchange, pnl, pnl_percent);
    
    // Удалить позицию (swap with last)
    vp->positions[pos_idx] = vp->positions[--vp->num_positions];
    
    virtual_portfolio_update_stats(vp);
    
    return 0;
}

void virtual_portfolio_update_prices(
    VirtualPortfolio *vp,
    const char *symbol,
    double current_price
) {
    for (uint32_t i = 0; i < vp->num_positions; i++) {
        VirtualPosition *pos = &vp->positions[i];
        if (strcmp(pos->symbol, symbol) == 0) {
            pos->current_price = current_price;
            
            // Рассчитать unrealized P&L
            double pnl = pos->quantity * (current_price - pos->entry_price);
            if (!pos->is_long) pnl = -pnl;
            pos->unrealized_pnl = pnl;
        }
    }
}

VirtualPosition* virtual_portfolio_get_position(
    VirtualPortfolio *vp,
    const char *symbol,
    const char *exchange
) {
    for (uint32_t i = 0; i < vp->num_positions; i++) {
        VirtualPosition *pos = &vp->positions[i];
        if (strcmp(pos->symbol, symbol) == 0 && strcmp(pos->exchange, exchange) == 0) {
            return pos;
        }
    }
    return NULL;
}

double virtual_portfolio_calculate_total_value_usd(VirtualPortfolio *vp) {
    double total = 0.0;
    
    // Available USDT
    total += virtual_portfolio_get_available_balance(vp, "USDT");
    
    // Locked USDT + unrealized P&L
    for (uint32_t i = 0; i < vp->num_positions; i++) {
        VirtualPosition *pos = &vp->positions[i];
        double position_value = pos->quantity * pos->entry_price;
        total += position_value + pos->unrealized_pnl;
    }
    
    return total;
}

void virtual_portfolio_update_stats(VirtualPortfolio *vp) {
    uint32_t total_trades = vp->wins + vp->losses;
    if (total_trades > 0) {
        vp->win_rate = ((double)vp->wins / total_trades) * 100.0;
        vp->avg_profit_per_trade = vp->total_pnl_usd / total_trades;
    }
    
    // Max drawdown
    double drawdown = vp->initial_balance_usd - vp->current_balance_usd;
    if (drawdown > vp->max_drawdown_usd) {
        vp->max_drawdown_usd = drawdown;
    }
}

void virtual_portfolio_print_summary(VirtualPortfolio *vp) {
    printf("\n╔════════════════════════════════════════════════════╗\n");
    printf("║        VIRTUAL PORTFOLIO SUMMARY                  ║\n");
    printf("╠════════════════════════════════════════════════════╣\n");
    printf("║ Initial Balance:  $%.2f                       ║\n", vp->initial_balance_usd);
    printf("║ Current Balance:  $%.2f                       ║\n", vp->current_balance_usd);
    printf("║ Total P&L:        $%.2f (%.2f%%)               ║\n", 
           vp->total_pnl_usd, 
           (vp->total_pnl_usd / vp->initial_balance_usd) * 100.0);
    printf("║ Total Fees:       $%.2f                       ║\n", vp->total_fees_paid);
    printf("║ Open Positions:   %u                              ║\n", vp->num_positions);
    printf("║ Total Operations: %lu                             ║\n", vp->total_operations);
    printf("║ Wins/Losses:      %u / %u                        ║\n", vp->wins, vp->losses);
    printf("║ Win Rate:         %.2f%%                         ║\n", vp->win_rate);
    printf("║ Avg Profit/Trade: $%.2f                       ║\n", vp->avg_profit_per_trade);
    printf("║ Max Drawdown:     $%.2f                       ║\n", vp->max_drawdown_usd);
    printf("╚════════════════════════════════════════════════════╝\n\n");
}

VirtualOperation* virtual_portfolio_get_last_operation(VirtualPortfolio *vp) {
    if (!vp->has_new_operation) return NULL;
    return &vp->last_operation;
}

void virtual_portfolio_clear_new_operation_flag(VirtualPortfolio *vp) {
    vp->has_new_operation = false;
}


