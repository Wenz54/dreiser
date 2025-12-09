/**
 * DRAIZER V2 - Generic Exchange Interface
 * Abstract interface for multiple exchanges
 */

#ifndef EXCHANGE_H
#define EXCHANGE_H

#include "../data/spsc_ring.h"

typedef enum {
    EXCHANGE_BINANCE,
    EXCHANGE_MEXC,
    EXCHANGE_BYBIT,
    EXCHANGE_OKX,
    EXCHANGE_GATEIO,
    EXCHANGE_KUCOIN,
    EXCHANGE_HUOBI,
    EXCHANGE_BITGET,
    EXCHANGE_COUNT
} ExchangeType;

typedef struct Exchange Exchange;

// Exchange interface (virtual methods)
struct Exchange {
    ExchangeType type;
    char name[32];
    bool enabled;
    bool connected;
    
    SPSCRingBuffer *output_feed;
    void *impl;  // Implementation-specific data (e.g., BinanceWSClient*)
    
    // Virtual methods
    int (*connect)(Exchange *ex, const char **symbols, int num_symbols);
    int (*process)(Exchange *ex);
    void (*close)(Exchange *ex);
    void (*destroy)(Exchange *ex);
    
    // Stats
    uint64_t messages_received;
    uint64_t reconnect_count;
    uint64_t last_message_ts;
};

/**
 * Create exchange instance
 * 
 * @param type Exchange type
 * @param output_feed SPSC buffer for price updates
 * @return Exchange* or NULL
 */
Exchange* exchange_create(ExchangeType type, SPSCRingBuffer *output_feed);

/**
 * Connect to exchange
 * 
 * @param symbols Array of symbols (e.g., ["BTCUSDT", "ETHUSDT"])
 * @param num_symbols Number of symbols
 */
int exchange_connect(Exchange *ex, const char **symbols, int num_symbols);

/**
 * Process messages (call in loop)
 */
int exchange_process(Exchange *ex);

/**
 * Close connection
 */
void exchange_close(Exchange *ex);

/**
 * Destroy exchange
 */
void exchange_destroy(Exchange *ex);

/**
 * Get socket file descriptor for select()
 * @return socket FD or -1 if not available
 */
int exchange_get_fd(Exchange *ex);

/**
 * Get exchange name by type
 */
const char* exchange_get_name(ExchangeType type);

#endif // EXCHANGE_H

