/**
 * DRAIZER V2 - Bitget WebSocket Implementation
 */

#include "bitget_ws.h"
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

BitgetWSClient* bitget_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed) {
    BitgetWSClient *client = calloc(1, sizeof(BitgetWSClient));
    if (!client) return NULL;
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    for (int i = 0; i < client->num_symbols; i++) {
        strncpy(client->subscribe_symbols[i], symbols[i], 19);
    }
    return client;
}

int bitget_ws_connect(BitgetWSClient *client) {
    if (!client) return -1;
    printf("🌐 Connecting to Bitget: %s\n", BITGET_WS_URL_SIMPLE);
    client->ws = ws_create(BITGET_WS_URL_SIMPLE);
    if (!client->ws) return -1;
    return ws_connect(client->ws);
}

int bitget_ws_subscribe(BitgetWSClient *client) {
    if (!client || !client->ws) return -1;
    
    // Bitget subscription: {"op":"subscribe","args":[{"instType":"sp","channel":"trade","instId":"BTCUSDT"}]}
    char subscribe_msg[2048] = "{\"op\":\"subscribe\",\"args\":[";
    for (int i = 0; i < client->num_symbols; i++) {
        if (i > 0) strcat(subscribe_msg, ",");
        char stream[128];
        snprintf(stream, sizeof(stream),
                 "{\"instType\":\"sp\",\"channel\":\"trade\",\"instId\":\"%s\"}",
                 client->subscribe_symbols[i]);
        strcat(subscribe_msg, stream);
    }
    strcat(subscribe_msg, "]}");
    printf("📤 Subscribing to Bitget streams...\n");
    return ws_send_text(client->ws, subscribe_msg);
}

int bitget_ws_process(BitgetWSClient *client) {
    if (!client || !client->ws) return -1;
    char buffer[16384];
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    if (len <= 0) return len;
    buffer[len] = '\0';
    
    // Bitget format: {"action":"update","arg":{"instType":"sp","channel":"trade","instId":"BTCUSDT"},"data":[{"price":"67000.50","size":"0.1","ts":"1234567890"}]}
    char inst_id[20];
    json_get_string(buffer, "instId", inst_id, sizeof(inst_id));
    if (inst_id[0] == '\0') return 0;
    
    double price = json_get_double(buffer, "price");
    double quantity = json_get_double(buffer, "size");
    if (price == 0.0) return 0;
    
    Price price_obj = {0};
    strncpy(price_obj.symbol, inst_id, 11);
    strcpy(price_obj.exchange, "bitget");
    price_obj.price = price;
    price_obj.quantity = quantity;
    price_obj.timestamp_tsc = rdtsc();
    price_obj.is_valid = 1;
    
    if (!spsc_push(client->output_feed, &price_obj)) {
        fprintf(stderr, "⚠️  Price feed buffer full\n");
    }
    return 1;
}

void bitget_ws_close(BitgetWSClient *client) {
    if (!client || !client->ws) return;
    ws_close(client->ws);
}

void bitget_ws_destroy(BitgetWSClient *client) {
    if (!client) return;
    if (client->ws) ws_destroy(client->ws);
    free(client);
}


