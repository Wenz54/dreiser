/**
 * DRAIZER V2 - KuCoin WebSocket Implementation
 */

#include "kucoin_ws.h"
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

KuCoinWSClient* kucoin_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed) {
    KuCoinWSClient *client = calloc(1, sizeof(KuCoinWSClient));
    if (!client) return NULL;
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    for (int i = 0; i < client->num_symbols; i++) {
        strncpy(client->subscribe_symbols[i], symbols[i], 19);
    }
    return client;
}

int kucoin_ws_connect(KuCoinWSClient *client) {
    if (!client) return -1;
    printf("🌐 Connecting to KuCoin: %s\n", KUCOIN_WS_URL_SIMPLE);
    client->ws = ws_create(KUCOIN_WS_URL_SIMPLE);
    if (!client->ws) return -1;
    return ws_connect(client->ws);
}

int kucoin_ws_subscribe(KuCoinWSClient *client) {
    if (!client || !client->ws) return -1;
    
    // KuCoin subscription: {"id":"123","type":"subscribe","topic":"/market/match:BTC-USDT","privateChannel":false,"response":true}
    for (int i = 0; i < client->num_symbols; i++) {
        // Convert BTCUSDT → BTC-USDT
        char symbol_dash[20];
        strncpy(symbol_dash, client->subscribe_symbols[i], 19);
        for (size_t j = 0; j < strlen(symbol_dash); j++) {
            if (strncmp(&symbol_dash[j], "USDT", 4) == 0) {
                memmove(&symbol_dash[j+1], &symbol_dash[j], strlen(&symbol_dash[j])+1);
                symbol_dash[j] = '-';
                break;
            }
        }
        
        char subscribe_msg[512];
        snprintf(subscribe_msg, sizeof(subscribe_msg),
                 "{\"id\":\"%d\",\"type\":\"subscribe\",\"topic\":\"/market/match:%s\",\"privateChannel\":false,\"response\":true}",
                 i, symbol_dash);
        ws_send_text(client->ws, subscribe_msg);
    }
    printf("📤 Subscribing to KuCoin streams...\n");
    return 0;
}

int kucoin_ws_process(KuCoinWSClient *client) {
    if (!client || !client->ws) return -1;
    char buffer[16384];
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    if (len <= 0) return len;
    buffer[len] = '\0';
    
    // KuCoin format: {"type":"message","topic":"/market/match:BTC-USDT","data":{"symbol":"BTC-USDT","price":"67000.50","size":"0.1","time":"1234567890"}}
    char symbol_dash[20];
    json_get_string(buffer, "symbol", symbol_dash, sizeof(symbol_dash));
    if (symbol_dash[0] == '\0') return 0;
    
    // Convert BTC-USDT → BTCUSDT
    char symbol[20];
    size_t j = 0;
    for (size_t i = 0; i < strlen(symbol_dash) && j < 19; i++) {
        if (symbol_dash[i] != '-') {
            symbol[j++] = symbol_dash[i];
        }
    }
    symbol[j] = '\0';
    
    double price = json_get_double(buffer, "price");
    double quantity = json_get_double(buffer, "size");
    if (price == 0.0) return 0;
    
    Price price_obj = {0};
    strncpy(price_obj.symbol, symbol, 11);
    strcpy(price_obj.exchange, "kucoin");
    price_obj.price = price;
    price_obj.quantity = quantity;
    price_obj.timestamp_tsc = rdtsc();
    price_obj.is_valid = 1;
    
    if (!spsc_push(client->output_feed, &price_obj)) {
        fprintf(stderr, "⚠️  Price feed buffer full\n");
    }
    return 1;
}

void kucoin_ws_close(KuCoinWSClient *client) {
    if (!client || !client->ws) return;
    ws_close(client->ws);
}

void kucoin_ws_destroy(KuCoinWSClient *client) {
    if (!client) return;
    if (client->ws) ws_destroy(client->ws);
    free(client);
}


