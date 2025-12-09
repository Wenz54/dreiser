/**
 * DRAIZER V2 - KuCoin WebSocket Handler
 */

#ifndef KUCOIN_WS_H
#define KUCOIN_WS_H

#include "websocket.h"
#include "../data/spsc_ring.h"

#define KUCOIN_WS_URL "ws://nginx:8085/"
#define KUCOIN_WS_URL_SIMPLE "ws://nginx:8085/"  // Via nginx SSL termination

typedef struct {
    WebSocket *ws;
    char subscribe_symbols[10][20];
    int num_symbols;
    SPSCRingBuffer *output_feed;
} KuCoinWSClient;

KuCoinWSClient* kucoin_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed);
int kucoin_ws_connect(KuCoinWSClient *client);
int kucoin_ws_subscribe(KuCoinWSClient *client);
int kucoin_ws_process(KuCoinWSClient *client);
void kucoin_ws_close(KuCoinWSClient *client);
void kucoin_ws_destroy(KuCoinWSClient *client);

#endif // KUCOIN_WS_H

