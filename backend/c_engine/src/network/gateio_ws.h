/**
 * DRAIZER V2 - Gate.io WebSocket Handler
 */

#ifndef GATEIO_WS_H
#define GATEIO_WS_H

#include "websocket.h"
#include "../data/spsc_ring.h"

#define GATEIO_WS_URL "ws://nginx:8084/ws/v4/"
#define GATEIO_WS_URL_SIMPLE "ws://nginx:8084/ws/v4/"  // Via nginx SSL termination

typedef struct {
    WebSocket *ws;
    char subscribe_symbols[10][20];
    int num_symbols;
    SPSCRingBuffer *output_feed;
} GateIOWSClient;

GateIOWSClient* gateio_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed);
int gateio_ws_connect(GateIOWSClient *client);
int gateio_ws_subscribe(GateIOWSClient *client);
int gateio_ws_process(GateIOWSClient *client);
void gateio_ws_close(GateIOWSClient *client);
void gateio_ws_destroy(GateIOWSClient *client);

#endif // GATEIO_WS_H

