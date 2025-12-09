/**
 * DRAIZER V2 - Bitfinex WebSocket Client
 * Ultra-low latency orderbook subscription (spot trading)
 * 
 * Ping: 0.803ms | Maker: 0.10% | Taker: 0.20%
 */

#ifndef BITFINEX_WS_H
#define BITFINEX_WS_H

#include "../data/price_feed.h"
#include "websocket.h"

// Bitfinex WebSocket V2 endpoints
#define BITFINEX_WS_URL "wss://api-pub.bitfinex.com/ws/2"
#define BITFINEX_WS_URL_SIMPLE "wss://api-pub.bitfinex.com/ws/2"

// Bitfinex uses trading pairs like "tBTCUSD"
#define BITFINEX_SYMBOL_PREFIX "t"

typedef struct {
    WebSocket *ws;
    SPSCRingBuffer *output_feed;  // Push Price objects here
    char symbols[10][12];         // e.g., "tBTCUSD", "tETHUSD"
    int num_symbols;
    int channel_ids[10];          // Map channel_id -> symbol index
    int is_running;
} BitfinexWSClient;

// Create Bitfinex WebSocket client
BitfinexWSClient* bitfinex_ws_create(const char *symbols[], int num_symbols, SPSCRingBuffer *output_feed);

// Connect and subscribe to orderbook (books channel)
int bitfinex_ws_connect(BitfinexWSClient *client);

// Process incoming messages (call in loop)
int bitfinex_ws_process(BitfinexWSClient *client);

// Cleanup
void bitfinex_ws_destroy(BitfinexWSClient *client);

#endif  // BITFINEX_WS_H

