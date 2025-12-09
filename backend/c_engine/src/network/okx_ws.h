/**
 * DRAIZER V2 - OKX WebSocket Handler
 */

#ifndef OKX_WS_H
#define OKX_WS_H

#include "websocket.h"
#include "../data/spsc_ring.h"

#define OKX_WS_URL "ws://nginx:8083/ws/v5/public"
#define OKX_WS_URL_SIMPLE "ws://nginx:8083/ws/v5/public"  // Via nginx SSL termination

typedef struct {
    WebSocket *ws;
    char subscribe_symbols[10][20];
    int num_symbols;
    SPSCRingBuffer *output_feed;
} OKXWSClient;

OKXWSClient* okx_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed);
int okx_ws_connect(OKXWSClient *client);
int okx_ws_subscribe(OKXWSClient *client);
int okx_ws_process(OKXWSClient *client);
void okx_ws_close(OKXWSClient *client);
void okx_ws_destroy(OKXWSClient *client);

#endif // OKX_WS_H

