/**
 * DRAIZER V2 - Binance WebSocket Implementation
 * Parse JSON trade messages and push to price feed
 */

#include "binance_ws.h"
#include "../utils/timestamp.h"
#include "../main.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>

// Simple JSON parser (extract values)
static double json_get_double(const char *json, const char *key) {
    char search[64];
    snprintf(search, sizeof(search), "\"%s\":", key);
    
    const char *pos = strstr(json, search);
    if (!pos) return 0.0;
    
    pos += strlen(search);
    while (*pos && isspace(*pos)) pos++;
    if (*pos == '"') pos++;  // Skip quote if present
    
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

BinanceWSClient* binance_ws_create(
    const char **symbols,
    int num_symbols,
    SPSCRingBuffer *output_feed
) {
    BinanceWSClient *client = calloc(1, sizeof(BinanceWSClient));
    if (!client) return NULL;
    
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    
    for (int i = 0; i < client->num_symbols; i++) {
        strncpy(client->subscribe_symbols[i], symbols[i], 19);
        client->subscribe_symbols[i][19] = '\0';
    }
    
    return client;
}

int binance_ws_connect(BinanceWSClient *client) {
    if (!client) return -1;
    
    // Build combined stream URL (via nginx SSL termination)
    char url[1024];
    strcpy(url, BINANCE_WS_URL_SIMPLE);
    strcat(url, "/stream?streams=");
    
    for (int i = 0; i < client->num_symbols; i++) {
        if (i > 0) strcat(url, "/");
        
        // Convert to lowercase
        char symbol_lower[20];
        strncpy(symbol_lower, client->subscribe_symbols[i], 19);
        for (char *p = symbol_lower; *p; p++) *p = tolower(*p);
        
        strcat(url, symbol_lower);
        strcat(url, "@bookTicker");  // Best bid/ask prices (NOT trades!)
    }
    
    // printf("🔍🔍 FINAL URL: %s\n", url);  // DEBUG
    printf("🌐 Connecting to Binance: %s\n", url);
    
    client->ws = ws_create(url);
    if (!client->ws) {
        fprintf(stderr, "❌ Failed to create WebSocket\n");
        return -1;
    }
    
    return ws_connect(client->ws);
}

int binance_ws_subscribe(BinanceWSClient *client) {
    // For combined streams, subscription is done via URL
    // No need to send subscribe message
    return 0;
}

int binance_ws_process(BinanceWSClient *client) {
    if (!client || !client->ws) return -1;
    
    char buffer[16384];
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    
    if (len <= 0) return len;
    
    buffer[len] = '\0';
    
    // RAW DATA LOGGING - Show sample every 5000 messages for monitoring
    static int msg_count = 0;
    msg_count++;
    
    if (msg_count % 5000 == 1) {  // Show first message and then every 5000th
        printf("📊 BINANCE RAW #%d:\n%.300s...\n", msg_count, buffer);
    }
    
    // Parse Binance bookTicker message
    // Format: {"u":123456789,"s":"BTCUSDT","b":"50000.00","B":"100.00","a":"50001.00","A":"100.00"}
    // OR with stream wrapper: {"stream":"btcusdt@bookTicker","data":{...}}
    
    // Try to extract "data" object (combined stream) or parse directly
    const char *parse_pos = strstr(buffer, "\"data\":");
    if (parse_pos) {
        parse_pos += 7;  // Skip "data":
    } else {
        parse_pos = buffer;  // Direct format (single stream)
    }
    
    // Parse symbol
    char symbol[20];
    json_get_string(parse_pos, "s", symbol, sizeof(symbol));
    
    if (symbol[0] == '\0') {
        return 0;  // Invalid message
    }
    
    // Parse best bid and ask
    double bid = json_get_double(parse_pos, "b");
    double ask = json_get_double(parse_pos, "a");
    double bid_qty = json_get_double(parse_pos, "B");
    double ask_qty = json_get_double(parse_pos, "A");
    
    if (bid == 0.0 || ask == 0.0 || ask < bid) {
        return 0;  // Invalid prices
    }
    
    // Use mid-price for Price object, will be split into bid/ask in price_cache
    double mid_price = (bid + ask) / 2.0;
    
    // LATENCY TRACKING
    uint64_t received_tsc = rdtsc();
    
    // Get current system time for latency estimation
    struct timespec current_time;
    clock_gettime(CLOCK_REALTIME, &current_time);
    uint64_t received_ts_ms = (uint64_t)current_time.tv_sec * 1000 + current_time.tv_nsec / 1000000;
    
    // LATENCY MONITORING - Show sample every 2500 messages
    // Note: Binance bookTicker doesn't include exchange timestamp, so we can't calculate true latency
    // We measure inter-message arrival time instead
    static int latency_logs = 0;
    static uint64_t prev_ts_ms = 0;
    
    if (++latency_logs % 2500 == 1) {  // First message and every 2500th
        uint64_t delta_ms = prev_ts_ms ? (received_ts_ms - prev_ts_ms) : 0;
        printf("⏱️  BINANCE %s: bid=%.2f, ask=%.2f | Msg #%d | Inter-arrival: %lu ms\n",
               symbol, bid, ask, latency_logs, delta_ms);
    }
    prev_ts_ms = received_ts_ms;
    
    // Create Price object
    Price price_obj = {0};
    strncpy(price_obj.symbol, symbol, 11);
    strcpy(price_obj.exchange, "binance");
    price_obj.price = mid_price;  // Store mid-price
    price_obj.quantity = (bid_qty + ask_qty) / 2.0;  // Average quantity
    price_obj.timestamp_tsc = received_tsc;
    price_obj.is_valid = 1;
    
    // Push to feed
    if (!spsc_push(client->output_feed, &price_obj)) {
        // Buffer full (rare)
        fprintf(stderr, "⚠️  Price feed buffer full\n");
    } else {
        // Notify main loop about new data
        notify_new_data();
    }
    
    return 1;
}

void binance_ws_close(BinanceWSClient *client) {
    if (!client) return;
    if (client->ws) {
        ws_close(client->ws);
    }
}

void binance_ws_destroy(BinanceWSClient *client) {
    if (!client) return;
    if (client->ws) {
        ws_destroy(client->ws);
    }
    free(client);
}

