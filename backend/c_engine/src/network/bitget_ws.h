/**
 * DRAIZER V2 - Bitget WebSocket Handler
 */

#ifndef BITGET_WS_H
#define BITGET_WS_H

#include "websocket.h"
#include "../data/spsc_ring.h"

#define BITGET_WS_URL "ws://nginx:8087/spot/v1/stream"
#define BITGET_WS_URL_SIMPLE "ws://nginx:8087/spot/v1/stream"  // Via nginx SSL termination

typedef struct {
    WebSocket *ws;
    char subscribe_symbols[10][20];
    int num_symbols;
    SPSCRingBuffer *output_feed;
} BitgetWSClient;

BitgetWSClient* bitget_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed);
int bitget_ws_connect(BitgetWSClient *client);
int bitget_ws_subscribe(BitgetWSClient *client);
int bitget_ws_process(BitgetWSClient *client);
void bitget_ws_close(BitgetWSClient *client);
void bitget_ws_destroy(BitgetWSClient *client);

#endif // BITGET_WS_H

