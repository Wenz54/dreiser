/**
 * DRAIZER V2 - Deribit WebSocket Client
 * Ultra-low latency orderbook subscription (perpetual futures)
 * 
 * Ping: 0.882ms | Maker: -0.025% (REBATE!) | Taker: 0.05%
 * Funding: Every 8 hours
 */

#ifndef DERIBIT_WS_H
#define DERIBIT_WS_H

#include "../data/price_feed.h"
#include "websocket.h"

// Deribit WebSocket V2 endpoints
#define DERIBIT_WS_URL "wss://www.deribit.com/ws/api/v2"
#define DERIBIT_WS_URL_SIMPLE "wss://www.deribit.com/ws/api/v2"

// Deribit uses instrument names like "BTC-PERPETUAL"
#define DERIBIT_PERPETUAL_SUFFIX "-PERPETUAL"

typedef struct {
    WebSocket *ws;
    SPSCRingBuffer *output_feed;  // Push Price objects here
    char symbols[10][24];         // e.g., "BTC-PERPETUAL", "ETH-PERPETUAL"
    int num_symbols;
    double funding_rates[10];     // Current funding rate for each symbol (bps)
    uint64_t funding_timestamps[10];  // Last funding rate update (ms)
    int is_running;
} DeribitWSClient;

// Create Deribit WebSocket client
DeribitWSClient* deribit_ws_create(const char *symbols[], int num_symbols, SPSCRingBuffer *output_feed);

// Connect and subscribe to orderbook (book channel)
int deribit_ws_connect(DeribitWSClient *client);

// Process incoming messages (call in loop)
int deribit_ws_process(DeribitWSClient *client);

// Get current funding rate for symbol (in bps)
double deribit_get_funding_rate(DeribitWSClient *client, const char *symbol);

// Cleanup
void deribit_ws_destroy(DeribitWSClient *client);

#endif  // DERIBIT_WS_H

