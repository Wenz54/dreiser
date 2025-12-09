/**
 * DRAIZER V2 - MEXC WebSocket Handler
 * Parse MEXC trade stream messages
 */

#ifndef MEXC_WS_H
#define MEXC_WS_H

#include "websocket.h"
#include "../data/spsc_ring.h"

// MEXC WebSocket URLs
#define MEXC_WS_URL "ws://nginx:8081/ws"
#define MEXC_WS_URL_SIMPLE "ws://nginx:8081/ws"  // Via nginx SSL termination (port 8081)

typedef struct {
    WebSocket *ws;
    char subscribe_symbols[10][20];
    int num_symbols;
    SPSCRingBuffer *output_feed;
} MEXCWSClient;

/**
 * Create MEXC WebSocket client
 */
MEXCWSClient* mexc_ws_create(
    const char **symbols,
    int num_symbols,
    SPSCRingBuffer *output_feed
);

/**
 * Connect to MEXC stream
 */
int mexc_ws_connect(MEXCWSClient *client);

/**
 * Subscribe to trade streams
 */
int mexc_ws_subscribe(MEXCWSClient *client);

/**
 * Process incoming messages
 */
int mexc_ws_process(MEXCWSClient *client);

/**
 * Close connection
 */
void mexc_ws_close(MEXCWSClient *client);

/**
 * Destroy client
 */
void mexc_ws_destroy(MEXCWSClient *client);

#endif // MEXC_WS_H

