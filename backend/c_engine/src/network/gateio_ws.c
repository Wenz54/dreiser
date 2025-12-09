/**
 * DRAIZER V2 - Gate.io WebSocket Implementation
 */

#include "gateio_ws.h"
#include "../utils/timestamp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

static double json_get_double(const char *json, const char *key) {
    char search[64];
    snprintf(search, sizeof(search), "\"%s\":", key);
    const char *pos = strstr(json, search);
    if (!pos) return 0.0;
    pos += strlen(search);
    while (*pos && isspace(*pos)) pos++;
    if (*pos == '"') pos++;
    return atof(pos);
}

static void json_get_string(const char *json, const char *key, char *out, size_t out_len) {
    char search[64];
    snprintf(search, sizeof(search), "\"%s\":", key);
    const char *pos = strstr(json, search);
    if (!pos) {
        out[0] = '\0';
        return;
    }
    pos += strlen(search);
    while (*pos && (isspace(*pos) || *pos == '"')) pos++;
    size_t i = 0;
    while (*pos && *pos != '"' && *pos != ',' && i < out_len - 1) {
        out[i++] = *pos++;
    }
    out[i] = '\0';
}

GateIOWSClient* gateio_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed) {
    GateIOWSClient *client = calloc(1, sizeof(GateIOWSClient));
    if (!client) return NULL;
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    for (int i = 0; i < client->num_symbols; i++) {
        strncpy(client->subscribe_symbols[i], symbols[i], 19);
    }
    return client;
}

int gateio_ws_connect(GateIOWSClient *client) {
    if (!client) return -1;
    printf("🌐 Connecting to Gate.io: %s\n", GATEIO_WS_URL_SIMPLE);
    client->ws = ws_create(GATEIO_WS_URL_SIMPLE);
    if (!client->ws) return -1;
    return ws_connect(client->ws);
}

int gateio_ws_subscribe(GateIOWSClient *client) {
    if (!client || !client->ws) return -1;
    
    // Gate.io subscription: {"time":123,"channel":"spot.trades","event":"subscribe","payload":["BTC_USDT"]}
    for (int i = 0; i < client->num_symbols; i++) {
        // Convert BTCUSDT → BTC_USDT
        char currency_pair[20];
        strncpy(currency_pair, client->subscribe_symbols[i], 19);
        for (size_t j = 0; j < strlen(currency_pair); j++) {
            if (strncmp(&currency_pair[j], "USDT", 4) == 0) {
                memmove(&currency_pair[j+1], &currency_pair[j], strlen(&currency_pair[j])+1);
                currency_pair[j] = '_';
                break;
            }
        }
        
        char subscribe_msg[512];
        snprintf(subscribe_msg, sizeof(subscribe_msg),
                 "{\"time\":%ld,\"channel\":\"spot.trades\",\"event\":\"subscribe\",\"payload\":[\"%s\"]}",
                 time(NULL), currency_pair);
        ws_send_text(client->ws, subscribe_msg);
    }
    printf("📤 Subscribing to Gate.io streams...\n");
    return 0;
}

int gateio_ws_process(GateIOWSClient *client) {
    if (!client || !client->ws) return -1;
    char buffer[16384];
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    if (len <= 0) return len;
    buffer[len] = '\0';
    
    // Gate.io format: {"time":123,"channel":"spot.trades","event":"update","result":{"id":123,"create_time":123,"currency_pair":"BTC_USDT","price":"67000.50","amount":"0.1"}}
    char currency_pair[20];
    json_get_string(buffer, "currency_pair", currency_pair, sizeof(currency_pair));
    if (currency_pair[0] == '\0') return 0;
    
    // Convert BTC_USDT → BTCUSDT
    char symbol[20];
    size_t j = 0;
    for (size_t i = 0; i < strlen(currency_pair) && j < 19; i++) {
        if (currency_pair[i] != '_') {
            symbol[j++] = currency_pair[i];
        }
    }
    symbol[j] = '\0';
    
    double price = json_get_double(buffer, "price");
    double quantity = json_get_double(buffer, "amount");
    if (price == 0.0) return 0;
    
    Price price_obj = {0};
    strncpy(price_obj.symbol, symbol, 11);
    strcpy(price_obj.exchange, "gateio");
    price_obj.price = price;
    price_obj.quantity = quantity;
    price_obj.timestamp_tsc = rdtsc();
    price_obj.is_valid = 1;
    
    if (!spsc_push(client->output_feed, &price_obj)) {
        fprintf(stderr, "⚠️  Price feed buffer full\n");
    }
    return 1;
}

void gateio_ws_close(GateIOWSClient *client) {
    if (!client || !client->ws) return;
    ws_close(client->ws);
}

void gateio_ws_destroy(GateIOWSClient *client) {
    if (!client) return;
    if (client->ws) ws_destroy(client->ws);
    free(client);
}


