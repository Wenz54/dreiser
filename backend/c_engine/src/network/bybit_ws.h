/**
 * DRAIZER V2 - Bybit WebSocket Handler
 */

#ifndef BYBIT_WS_H
#define BYBIT_WS_H

#include "websocket.h"
#include "../data/spsc_ring.h"

#define BYBIT_WS_URL "wss://stream.bybit.com/v5/public/spot"
#define BYBIT_WS_URL_SIMPLE "wss://stream.bybit.com/v5/public/spot"

typedef struct {
    WebSocket *ws;
    char subscribe_symbols[10][20];
    int num_symbols;
    SPSCRingBuffer *output_feed;
} BybitWSClient;

BybitWSClient* bybit_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed);
int bybit_ws_connect(BybitWSClient *client);
int bybit_ws_subscribe(BybitWSClient *client);
int bybit_ws_process(BybitWSClient *client);
void bybit_ws_close(BybitWSClient *client);
void bybit_ws_destroy(BybitWSClient *client);

#endif // BYBIT_WS_H

