/**
 * DRAIZER V2 - OKX WebSocket Implementation
 */

#include "okx_ws.h"
#include "../utils/timestamp.h"
#include "../main.h"
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

OKXWSClient* okx_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed) {
    OKXWSClient *client = calloc(1, sizeof(OKXWSClient));
    if (!client) return NULL;
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    for (int i = 0; i < client->num_symbols; i++) {
        strncpy(client->subscribe_symbols[i], symbols[i], 19);
    }
    return client;
}

int okx_ws_connect(OKXWSClient *client) {
    if (!client) return -1;
    printf("🌐 Connecting to OKX: %s\n", OKX_WS_URL_SIMPLE);
    client->ws = ws_create(OKX_WS_URL_SIMPLE);
    if (!client->ws) return -1;
    return ws_connect(client->ws);
}

int okx_ws_subscribe(OKXWSClient *client) {
    if (!client || !client->ws) return -1;
    
    // OKX subscription: {"op":"subscribe","args":[{"channel":"trades","instId":"BTC-USDT"}]}
    char subscribe_msg[2048] = "{\"op\":\"subscribe\",\"args\":[";
    for (int i = 0; i < client->num_symbols; i++) {
        if (i > 0) strcat(subscribe_msg, ",");
        
        // Convert BTCUSDT → BTC-USDT
        char inst_id[20];
        strncpy(inst_id, client->subscribe_symbols[i], 19);
        for (size_t j = 0; j < strlen(inst_id); j++) {
            if (strncmp(&inst_id[j], "USDT", 4) == 0) {
                memmove(&inst_id[j+1], &inst_id[j], strlen(&inst_id[j])+1);
                inst_id[j] = '-';
                break;
            }
        }
        
        char stream[128];
        snprintf(stream, sizeof(stream), "{\"channel\":\"trades\",\"instId\":\"%s\"}", inst_id);
        strcat(subscribe_msg, stream);
    }
    strcat(subscribe_msg, "]}");
    printf("📤 Subscribing to OKX streams...\n");
    return ws_send_text(client->ws, subscribe_msg);
}

int okx_ws_process(OKXWSClient *client) {
    if (!client || !client->ws) return -1;
    char buffer[16384];
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    if (len <= 0) return len;
    buffer[len] = '\0';
    
    // OKX format: {"arg":{"channel":"trades","instId":"BTC-USDT"},"data":[{"px":"67000.50","sz":"0.1","ts":"1234567890"}]}
    char inst_id[20];
    json_get_string(buffer, "instId", inst_id, sizeof(inst_id));
    if (inst_id[0] == '\0') return 0;
    
    // Convert BTC-USDT → BTCUSDT
    char symbol[20];
    size_t j = 0;
    for (size_t i = 0; i < strlen(inst_id) && j < 19; i++) {
        if (inst_id[i] != '-') {
            symbol[j++] = inst_id[i];
        }
    }
    symbol[j] = '\0';
    
    double price = json_get_double(buffer, "px");
    double quantity = json_get_double(buffer, "sz");
    if (price == 0.0) return 0;
    
    Price price_obj = {0};
    strncpy(price_obj.symbol, symbol, 11);
    strcpy(price_obj.exchange, "okx");
    price_obj.price = price;
    price_obj.quantity = quantity;
    price_obj.timestamp_tsc = rdtsc();
    price_obj.is_valid = 1;
    
    if (!spsc_push(client->output_feed, &price_obj)) {
        fprintf(stderr, "⚠️  Price feed buffer full\n");
    } else {
        // Notify main loop about new data
        notify_new_data();
    }
    return 1;
}

void okx_ws_close(OKXWSClient *client) {
    if (!client || !client->ws) return;
    ws_close(client->ws);
}

void okx_ws_destroy(OKXWSClient *client) {
    if (!client) return;
    if (client->ws) ws_destroy(client->ws);
    free(client);
}


