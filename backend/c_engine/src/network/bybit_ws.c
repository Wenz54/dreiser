/**
 * DRAIZER V2 - Bybit WebSocket Implementation
 */

#include "bybit_ws.h"
#include "../utils/timestamp.h"
#include "../main.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>

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

BybitWSClient* bybit_ws_create(const char **symbols, int num_symbols, SPSCRingBuffer *output_feed) {
    BybitWSClient *client = calloc(1, sizeof(BybitWSClient));
    if (!client) return NULL;
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    for (int i = 0; i < client->num_symbols; i++) {
        strncpy(client->subscribe_symbols[i], symbols[i], 19);
    }
    return client;
}

int bybit_ws_connect(BybitWSClient *client) {
    if (!client) return -1;
    printf("🌐 Connecting to Bybit: %s\n", BYBIT_WS_URL_SIMPLE);
    client->ws = ws_create(BYBIT_WS_URL_SIMPLE);
    if (!client->ws) return -1;
    return ws_connect(client->ws);
}

int bybit_ws_subscribe(BybitWSClient *client) {
    if (!client || !client->ws) return -1;
    
    // Bybit orderbook subscription: {"op":"subscribe","args":["orderbook.1.BTCUSDT"]}
    // Using level 1 (best bid/ask only) for ultra-low latency
    char subscribe_msg[2048] = "{\"op\":\"subscribe\",\"args\":[";
    for (int i = 0; i < client->num_symbols; i++) {
        if (i > 0) strcat(subscribe_msg, ",");
        char stream[128];
        snprintf(stream, sizeof(stream), "\"orderbook.1.%s\"", client->subscribe_symbols[i]);
        strcat(subscribe_msg, stream);
    }
    strcat(subscribe_msg, "]}");
    printf("📤 Subscribing to Bybit orderbook streams: %s\n", subscribe_msg);
    return ws_send_text(client->ws, subscribe_msg);
}

int bybit_ws_process(BybitWSClient *client) {
    if (!client || !client->ws) return -1;
    char buffer[16384];
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    if (len <= 0) return len;
    buffer[len] = '\0';
    
    // RAW DATA LOGGING - Show sample every 3000 messages for monitoring
    static int msg_count = 0;
    static char seen_topics[20][32] = {{0}};
    static int num_topics = 0;
    msg_count++;
    
    if (msg_count % 3000 == 1) {  // Show first message and then every 3000th
        printf("📊 BYBIT RAW #%d:\n%.300s...\n", msg_count, buffer);
    }
    
    // Extract and track topic
    const char *topic_start = strstr(buffer, "\"topic\":\"");
    if (topic_start) {
        topic_start += 9;
        char topic[32];
        int i = 0;
        while (*topic_start && *topic_start != '"' && i < 31) {
            topic[i++] = *topic_start++;
        }
        topic[i] = '\0';
        
        // Check if new topic
        int found = 0;
        for (int j = 0; j < num_topics; j++) {
            if (strcmp(seen_topics[j], topic) == 0) {
                found = 1;
                break;
            }
        }
        if (!found && num_topics < 20) {
            strcpy(seen_topics[num_topics++], topic);
            printf("📊 NEW Bybit topic: %s (total: %d)\n", topic, num_topics);
        }
    }
    
    // Bybit orderbook format: {"topic":"orderbook.1.BTCUSDT","type":"snapshot","ts":1234567890000,"data":{"s":"BTCUSDT","b":[["50000.00","100.00"]],"a":[["50001.00","100.00"]]}}
    char symbol[20];
    const char *topic_pos = strstr(buffer, "\"topic\":\"orderbook.");
    if (!topic_pos) return 0;
    
    // Skip "orderbook.X." where X is depth level (1, 5, etc)
    topic_pos += 18;  // Skip "topic":"orderbook."
    while (*topic_pos && *topic_pos != '.') topic_pos++;  // Skip level number
    if (*topic_pos == '.') topic_pos++;  // Skip dot
    
    // Extract symbol
    size_t i = 0;
    while (*topic_pos && *topic_pos != '"' && i < 19) {
        symbol[i++] = *topic_pos++;
    }
    symbol[i] = '\0';
    
    if (strlen(symbol) == 0) return 0;
    
    // Find data object
    const char *data_pos = strstr(buffer, "\"data\":{");
    if (!data_pos) return 0;
    data_pos += 8;  // Skip to start of data object
    
    // Parse best bid: "b":[["price","qty"]] or "b":[[price,qty]] (without quotes)
    const char *bid_pos = strstr(data_pos, "\"b\":[[");
    if (!bid_pos) return 0;
    bid_pos += 6;  // Skip to [[
    // Skip any quotes or brackets
    while (*bid_pos && (*bid_pos == '[' || *bid_pos == '"')) bid_pos++;
    double bid = atof(bid_pos);
    
    // Parse best ask: "a":[["price","qty"]]  or "a":[[price,qty]]
    const char *ask_pos = strstr(data_pos, "\"a\":[[");
    if (!ask_pos) return 0;
    ask_pos += 6;  // Skip to [[
    // Skip any quotes or brackets
    while (*ask_pos && (*ask_pos == '[' || *ask_pos == '"')) ask_pos++;
    double ask = atof(ask_pos);
    
    if (bid == 0.0 || ask == 0.0 || ask < bid) return 0;
    
    // Use mid-price for Price object
    double mid_price = (bid + ask) / 2.0;
    
    // LATENCY TRACKING - get exchange timestamp
    uint64_t received_tsc = rdtsc();
    
    // Parse exchange timestamp "ts": milliseconds since epoch
    const char *ts_pos = strstr(buffer, "\"ts\":");
    uint64_t exchange_ts_ms = 0;
    if (ts_pos) {
        ts_pos += 5;  // Skip "ts":
        exchange_ts_ms = strtoull(ts_pos, NULL, 10);
    }
    
    // LATENCY MONITORING - Show sample every 1500 messages
    static int latency_logs = 0;
    latency_logs++;
    
    if (exchange_ts_ms > 0 && latency_logs % 1500 == 1) {  // First and every 1500th
        // Get current time in milliseconds
        struct timespec current_time;
        clock_gettime(CLOCK_REALTIME, &current_time);
        uint64_t current_ts_ms = (uint64_t)current_time.tv_sec * 1000 + current_time.tv_nsec / 1000000;
        
        uint64_t latency_ms = current_ts_ms - exchange_ts_ms;
        printf("⏱️  BYBIT %s: bid=%.2f, ask=%.2f | Msg #%d | LATENCY: %lu ms (Exchange→Us)\n",
               symbol, bid, ask, latency_logs, latency_ms);
    }
    
    Price price_obj = {0};
    strncpy(price_obj.symbol, symbol, 11);
    strcpy(price_obj.exchange, "bybit");
    price_obj.price = mid_price;
    price_obj.quantity = 100.0;  // Placeholder (actual quantity in orderbook)
    price_obj.timestamp_tsc = received_tsc;
    price_obj.is_valid = 1;
    
    if (!spsc_push(client->output_feed, &price_obj)) {
        fprintf(stderr, "⚠️  Price feed buffer full\n");
    } else {
        // Notify main loop about new data
        notify_new_data();
    }
    return 1;
}

void bybit_ws_close(BybitWSClient *client) {
    if (!client || !client->ws) return;
    ws_close(client->ws);
}

void bybit_ws_destroy(BybitWSClient *client) {
    if (!client) return;
    if (client->ws) ws_destroy(client->ws);
    free(client);
}


