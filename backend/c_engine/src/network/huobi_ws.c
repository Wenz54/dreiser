/**
 * DRAIZER V2 - Huobi (HTX) WebSocket Implementation
 */

#include "huobi_ws.h"
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

HuobiWSClient* huobi_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed) {
    HuobiWSClient *client = calloc(1, sizeof(HuobiWSClient));
    if (!client) return NULL;
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    for (int i = 0; i < client->num_symbols; i++) {
        strncpy(client->subscribe_symbols[i], symbols[i], 19);
    }
    return client;
}

int huobi_ws_connect(HuobiWSClient *client) {
    if (!client) return -1;
    printf("🌐 Connecting to Huobi (HTX): %s\n", HUOBI_WS_URL_SIMPLE);
    client->ws = ws_create(HUOBI_WS_URL_SIMPLE);
    if (!client->ws) return -1;
    return ws_connect(client->ws);
}

int huobi_ws_subscribe(HuobiWSClient *client) {
    if (!client || !client->ws) return -1;
    
    // Huobi subscription: {"sub":"market.btcusdt.trade.detail","id":"123"}
    for (int i = 0; i < client->num_symbols; i++) {
        // Convert to lowercase
        char symbol_lower[20];
        strncpy(symbol_lower, client->subscribe_symbols[i], 19);
        for (char *p = symbol_lower; *p; p++) *p = tolower(*p);
        
        char subscribe_msg[256];
        snprintf(subscribe_msg, sizeof(subscribe_msg),
                 "{\"sub\":\"market.%s.trade.detail\",\"id\":\"%d\"}",
                 symbol_lower, i);
        ws_send_text(client->ws, subscribe_msg);
    }
    printf("📤 Subscribing to Huobi streams...\n");
    return 0;
}

int huobi_ws_process(HuobiWSClient *client) {
    if (!client || !client->ws) return -1;
    char buffer[16384];
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    if (len <= 0) return len;
    buffer[len] = '\0';
    
    // Huobi format: {"ch":"market.btcusdt.trade.detail","ts":123,"tick":{"data":[{"price":67000.50,"amount":0.1,"ts":123}]}}
    char channel[64];
    json_get_string(buffer, "ch", channel, sizeof(channel));
    if (channel[0] == '\0') return 0;
    
    // Extract symbol from channel: "market.btcusdt.trade.detail" → "btcusdt"
    char *start = strstr(channel, "market.");
    if (!start) return 0;
    start += 7;
    char *end = strstr(start, ".trade");
    if (!end) return 0;
    
    char symbol[20];
    size_t len_sym = end - start;
    if (len_sym >= 20) len_sym = 19;
    strncpy(symbol, start, len_sym);
    symbol[len_sym] = '\0';
    
    // Convert to uppercase
    for (char *p = symbol; *p; p++) *p = toupper(*p);
    
    double price = json_get_double(buffer, "price");
    double quantity = json_get_double(buffer, "amount");
    if (price == 0.0) return 0;
    
    Price price_obj = {0};
    strncpy(price_obj.symbol, symbol, 11);
    strcpy(price_obj.exchange, "huobi");
    price_obj.price = price;
    price_obj.quantity = quantity;
    price_obj.timestamp_tsc = rdtsc();
    price_obj.is_valid = 1;
    
    if (!spsc_push(client->output_feed, &price_obj)) {
        fprintf(stderr, "⚠️  Price feed buffer full\n");
    }
    return 1;
}

void huobi_ws_close(HuobiWSClient *client) {
    if (!client || !client->ws) return;
    ws_close(client->ws);
}

void huobi_ws_destroy(HuobiWSClient *client) {
    if (!client) return;
    if (client->ws) ws_destroy(client->ws);
    free(client);
}


