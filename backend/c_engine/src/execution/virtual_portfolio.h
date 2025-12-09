/**
 * DRAIZER V2 - Virtual Portfolio Manager
 * Paper trading: виртуальные балансы и позиции
 */

#ifndef VIRTUAL_PORTFOLIO_H
#define VIRTUAL_PORTFOLIO_H

#include <stdint.h>
#include <stdbool.h>

#define MAX_VIRTUAL_POSITIONS 50
#define MAX_VIRTUAL_BALANCES 20

// Виртуальная позиция
typedef struct {
    char symbol[12];           // e.g., "BTCUSDT"
    char exchange[20];         // e.g., "binance"
    double quantity;           // Количество
    double entry_price;        // Цена входа
    double current_price;      // Текущая цена (обновляется real-time)
    double unrealized_pnl;     // Нереализованная прибыль
    uint64_t opened_at_ns;     // Время открытия
    bool is_long;              // true = long, false = short
    char strategy[20];         // Какая стратегия открыла
} VirtualPosition;

// Виртуальный баланс (по валютам)
typedef struct {
    char currency[12];         // e.g., "USDT", "BTC", "ETH"
    double total;              // Общий баланс
    double available;          // Доступный (не в позициях)
    double locked;             // Заблокирован в позициях
} VirtualBalance;

// Виртуальная операция (для истории и отправки на фронт)
typedef struct {
    uint64_t id;               // Уникальный ID операции
    uint64_t timestamp_ns;     // Время операции
    char type[20];             // "BUY", "SELL", "CLOSE_LONG", "CLOSE_SHORT"
    char strategy[20];         // "cross_exchange", "funding_rate", "triangular"
    char symbol[12];
    char exchange_buy[20];     // Биржа покупки
    char exchange_sell[20];    // Биржа продажи
    double quantity;
    double entry_price;
    double exit_price;         // 0 если ещё не закрыта
    double pnl;                // Прибыль/убыток (0 если открыта)
    double pnl_percent;        // P&L в %
    double spread_bps;         // Спред в bps
    double fees_paid;          // Комиссии
    bool is_open;              // true = открыта, false = закрыта
} VirtualOperation;

// Виртуальный портфель
typedef struct {
    // Позиции
    VirtualPosition positions[MAX_VIRTUAL_POSITIONS];
    uint32_t num_positions;
    
    // Балансы
    VirtualBalance balances[MAX_VIRTUAL_BALANCES];
    uint32_t num_balances;
    
    // История операций (ring buffer)
    VirtualOperation operations[1000];  // Последние 1000 операций
    uint32_t operations_head;           // Куда писать следующую
    uint64_t total_operations;          // Всего операций
    
    // Статистика
    double initial_balance_usd;
    double current_balance_usd;
    double total_pnl_usd;
    double total_fees_paid;
    uint32_t wins;
    uint32_t losses;
    double win_rate;
    double avg_profit_per_trade;
    double max_drawdown_usd;
    
    // Последняя операция (для отправки на фронт)
    VirtualOperation last_operation;
    bool has_new_operation;             // Флаг для IPC
} VirtualPortfolio;

// Создание/уничтожение
VirtualPortfolio* virtual_portfolio_create(double initial_balance_usd);
void virtual_portfolio_destroy(VirtualPortfolio *vp);

// Инициализация балансов
void virtual_portfolio_init_balance(VirtualPortfolio *vp, const char *currency, double amount);

// Получение баланса
double virtual_portfolio_get_balance(VirtualPortfolio *vp, const char *currency);
double virtual_portfolio_get_available_balance(VirtualPortfolio *vp, const char *currency);

// Открытие позиции (эмуляция BUY/SHORT)
int virtual_portfolio_open_position(
    VirtualPortfolio *vp,
    const char *symbol,
    const char *exchange,
    double quantity,
    double price,
    bool is_long,
    const char *strategy,
    double fees
);

// Закрытие позиции (эмуляция SELL/CLOSE)
int virtual_portfolio_close_position(
    VirtualPortfolio *vp,
    const char *symbol,
    const char *exchange,
    double exit_price,
    double fees
);

// Обновление текущих цен позиций (для unrealized P&L)
void virtual_portfolio_update_prices(
    VirtualPortfolio *vp,
    const char *symbol,
    double current_price
);

// Получение позиции
VirtualPosition* virtual_portfolio_get_position(
    VirtualPortfolio *vp,
    const char *symbol,
    const char *exchange
);

// Расчёт текущего баланса в USD
double virtual_portfolio_calculate_total_value_usd(VirtualPortfolio *vp);

// Статистика
void virtual_portfolio_update_stats(VirtualPortfolio *vp);
void virtual_portfolio_print_summary(VirtualPortfolio *vp);

// Получение последней операции (для отправки на фронт)
VirtualOperation* virtual_portfolio_get_last_operation(VirtualPortfolio *vp);
void virtual_portfolio_clear_new_operation_flag(VirtualPortfolio *vp);

#endif // VIRTUAL_PORTFOLIO_H


