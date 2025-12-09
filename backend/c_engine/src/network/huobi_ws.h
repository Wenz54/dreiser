/**
 * DRAIZER V2 - Huobi (HTX) WebSocket Handler
 */

#ifndef HUOBI_WS_H
#define HUOBI_WS_H

#include "websocket.h"
#include "../data/spsc_ring.h"

#define HUOBI_WS_URL "ws://nginx:8086/ws"
#define HUOBI_WS_URL_SIMPLE "ws://nginx:8086/ws"  // Via nginx SSL termination

typedef struct {
    WebSocket *ws;
    char subscribe_symbols[10][20];
    int num_symbols;
    SPSCRingBuffer *output_feed;
} HuobiWSClient;

HuobiWSClient* huobi_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed);
int huobi_ws_connect(HuobiWSClient *client);
int huobi_ws_subscribe(HuobiWSClient *client);
int huobi_ws_process(HuobiWSClient *client);
void huobi_ws_close(HuobiWSClient *client);
void huobi_ws_destroy(HuobiWSClient *client);

#endif // HUOBI_WS_H

