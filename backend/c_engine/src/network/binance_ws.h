/**
 * DRAIZER V2 - Binance WebSocket Handler
 * Parse Binance trade stream messages
 */

#ifndef BINANCE_WS_H
#define BINANCE_WS_H

#include "websocket.h"
#include "../data/spsc_ring.h"

#define BINANCE_WS_URL "wss://stream.binance.com:9443"
#define BINANCE_WS_URL_SIMPLE "wss://stream.binance.com:9443"  // Via nginx SSL termination (port 8080)

typedef struct {
    WebSocket *ws;
    char subscribe_symbols[10][20];  // Up to 10 symbols
    int num_symbols;
    SPSCRingBuffer *output_feed;
} BinanceWSClient;

/**
 * Create Binance WebSocket client
 * 
 * @param symbols Array of symbols (e.g., ["btcusdt", "ethusdt"])
 * @param num_symbols Number of symbols
 * @param output_feed SPSC buffer to push Price updates
 */
BinanceWSClient* binance_ws_create(
    const char **symbols,
    int num_symbols,
    SPSCRingBuffer *output_feed
);

/**
 * Connect to Binance stream
 */
int binance_ws_connect(BinanceWSClient *client);

/**
 * Subscribe to trade streams
 */
int binance_ws_subscribe(BinanceWSClient *client);

/**
 * Process incoming messages (call in loop)
 */
int binance_ws_process(BinanceWSClient *client);

/**
 * Close connection
 */
void binance_ws_close(BinanceWSClient *client);

/**
 * Destroy client
 */
void binance_ws_destroy(BinanceWSClient *client);

#endif // BINANCE_WS_H

