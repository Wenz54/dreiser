/**
 * DRAIZER V2 - MEXC WebSocket Implementation
 * MEXC uses similar protocol to Binance
 */

#include "mexc_ws.h"
#include "../utils/timestamp.h"
#include "../main.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// Simple JSON parser (same as Binance)
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

MEXCWSClient* mexc_ws_create(
    const char **symbols,
    int num_symbols,
    SPSCRingBuffer *output_feed
) {
    MEXCWSClient *client = calloc(1, sizeof(MEXCWSClient));
    if (!client) return NULL;
    
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    
    for (int i = 0; i < client->num_symbols; i++) {
        strncpy(client->subscribe_symbols[i], symbols[i], 19);
        client->subscribe_symbols[i][19] = '\0';
    }
    
    return client;
}

int mexc_ws_connect(MEXCWSClient *client) {
    if (!client) return -1;
    
    // MEXC uses single WebSocket, subscribe via JSON message
    char url[512];
    snprintf(url, sizeof(url), "%s", MEXC_WS_URL_SIMPLE);
    
    printf("🌐 Connecting to MEXC: %s\n", url);
    
    client->ws = ws_create(url);
    if (!client->ws) {
        fprintf(stderr, "❌ Failed to create WebSocket\n");
        return -1;
    }
    
    return ws_connect(client->ws);
}

int mexc_ws_subscribe(MEXCWSClient *client) {
    if (!client || !client->ws) return -1;
    
    // MEXC subscription format:
    // {"method":"SUBSCRIPTION","params":["spot@public.deals.v3.api@BTCUSDT"]}
    
    char subscribe_msg[2048] = "{\"method\":\"SUBSCRIPTION\",\"params\":[";
    
    for (int i = 0; i < client->num_symbols; i++) {
        if (i > 0) strcat(subscribe_msg, ",");
        
        // Convert to uppercase (MEXC uses uppercase)
        char symbol_upper[20];
        strncpy(symbol_upper, client->subscribe_symbols[i], 19);
        for (char *p = symbol_upper; *p; p++) *p = toupper(*p);
        
        char stream[128];
        snprintf(stream, sizeof(stream), "\"spot@public.deals.v3.api@%s\"", symbol_upper);
        strcat(subscribe_msg, stream);
    }
    
    strcat(subscribe_msg, "]}");
    
    printf("📤 Subscribing to MEXC streams...\n");
    
    return ws_send_text(client->ws, subscribe_msg);
}

int mexc_ws_process(MEXCWSClient *client) {
    if (!client || !client->ws) return -1;
    
    char buffer[16384];
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    
    if (len <= 0) return len;
    
    buffer[len] = '\0';
    
    // Parse MEXC trade message
    // Format: {"c":"spot@public.deals.v3.api@BTCUSDT","d":{"deals":[{"p":"67000.50","v":"0.1","t":1234567890}],"e":"spot@public.deals.v3.api"},"s":"BTCUSDT"}
    
    char symbol[20];
    json_get_string(buffer, "s", symbol, sizeof(symbol));
    
    if (symbol[0] == '\0') {
        return 0;  // Invalid message or subscription confirmation
    }
    
    // Extract price from deals array
    // Simple approach: find first "p" after "deals"
    const char *deals_pos = strstr(buffer, "\"deals\"");
    if (!deals_pos) return 0;
    
    const char *price_pos = strstr(deals_pos, "\"p\":\"");
    if (!price_pos) return 0;
    
    price_pos += 5;  // Skip "p":"
    double price = atof(price_pos);
    
    const char *vol_pos = strstr(price_pos, "\"v\":\"");
    double quantity = 0.0;
    if (vol_pos) {
        vol_pos += 5;
        quantity = atof(vol_pos);
    }
    
    if (price == 0.0) {
        return 0;  // Invalid price
    }
    
    // Create Price object
    Price price_obj = {0};
    strncpy(price_obj.symbol, symbol, 11);
    strcpy(price_obj.exchange, "mexc");
    price_obj.price = price;
    price_obj.quantity = quantity;
    price_obj.timestamp_tsc = rdtsc();
    price_obj.is_valid = 1;
    
    // Push to feed
    if (!spsc_push(client->output_feed, &price_obj)) {
        fprintf(stderr, "⚠️  Price feed buffer full\n");
    } else {
        // Notify main loop about new data
        notify_new_data();
    }
    
    return 1;
}

void mexc_ws_close(MEXCWSClient *client) {
    if (!client) return;
    if (client->ws) {
        ws_close(client->ws);
    }
}

void mexc_ws_destroy(MEXCWSClient *client) {
    if (!client) return;
    if (client->ws) {
        ws_destroy(client->ws);
    }
    free(client);
}


