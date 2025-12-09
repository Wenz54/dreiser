/**
 * DRAIZER V2 - Bitfinex WebSocket Implementation
 * Parse orderbook snapshots/updates and push to price feed
 * 
 * Format: {"event":"subscribe","channel":"book","symbol":"tBTCUSD"}
 * Response: [CHAN_ID, [[PRICE, COUNT, AMOUNT], ...]] (snapshot)
 *           [CHAN_ID, [PRICE, COUNT, AMOUNT]] (update)
 */

#include "bitfinex_ws.h"
#include "../utils/timestamp.h"
#include "../main.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>

// Simple JSON parser
static const char* find_json_field(const char *json, const char *key) {
    char search[64];
    snprintf(search, sizeof(search), "\"%s\":", key);
    return strstr(json, search);
}

static void extract_json_string(const char *json, const char *key, char *out, size_t out_size) {
    const char *pos = find_json_field(json, key);
    if (!pos) {
        out[0] = '\0';
        return;
    }
    pos += strlen(key) + 3;  // Skip "key":"
    while (*pos && (*pos == ' ' || *pos == '"')) pos++;
    
    size_t i = 0;
    while (*pos && *pos != '"' && *pos != ',' && *pos != '}' && i < out_size - 1) {
        out[i++] = *pos++;
    }
    out[i] = '\0';
}

BitfinexWSClient* bitfinex_ws_create(const char *symbols[], int num_symbols, SPSCRingBuffer *output_feed) {
    BitfinexWSClient *client = calloc(1, sizeof(BitfinexWSClient));
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    
    for (int i = 0; i < client->num_symbols; i++) {
        // Convert "BTCUSD" -> "tBTCUSD" (Bitfinex format)
        if (symbols[i][0] != 't') {
            snprintf(client->symbols[i], sizeof(client->symbols[i]), "t%s", symbols[i]);
        } else {
            strncpy(client->symbols[i], symbols[i], sizeof(client->symbols[i]) - 1);
        }
        client->channel_ids[i] = -1;  // Not subscribed yet
    }
    
    return client;
}

int bitfinex_ws_connect(BitfinexWSClient *client) {
    client->ws = ws_connect(BITFINEX_WS_URL);
    if (!client->ws) {
        fprintf(stderr, "❌ Bitfinex: WebSocket connection failed\n");
        return -1;
    }
    
    printf("✅ Bitfinex: Connected to %s\n", BITFINEX_WS_URL);
    
    // Subscribe to orderbook for each symbol
    for (int i = 0; i < client->num_symbols; i++) {
        char subscribe_msg[256];
        // prec="P0" = raw orderbooks, freq="F0" = realtime, len="25" = 25 price levels
        snprintf(subscribe_msg, sizeof(subscribe_msg),
                 "{\"event\":\"subscribe\",\"channel\":\"book\",\"symbol\":\"%s\",\"prec\":\"P0\",\"freq\":\"F0\",\"len\":\"25\"}",
                 client->symbols[i]);
        
        if (ws_send(client->ws, subscribe_msg, strlen(subscribe_msg)) < 0) {
            fprintf(stderr, "⚠️  Bitfinex: Failed to subscribe to %s\n", client->symbols[i]);
        } else {
            printf("📡 Bitfinex: Subscribed to %s orderbook\n", client->symbols[i]);
        }
    }
    
    client->is_running = 1;
    return 0;
}

int bitfinex_ws_process(BitfinexWSClient *client) {
    char buffer[65536];  // Bitfinex can send large orderbook snapshots
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    if (len <= 0) return len;
    buffer[len] = '\0';
    
    // RAW DATA LOGGING - Show sample every 3000 messages for monitoring
    static int msg_count = 0;
    msg_count++;
    
    if (msg_count % 3000 == 1) {
        printf("📊 BITFINEX RAW #%d:\n%.300s...\n", msg_count, buffer);
    }
    
    // Parse message type
    if (buffer[0] == '{') {
        // Event message (subscribe confirmation, info, etc.)
        const char *event_pos = find_json_field(buffer, "event");
        if (event_pos) {
            char event_type[32];
            extract_json_string(buffer, "event", event_type, sizeof(event_type));
            
            if (strcmp(event_type, "subscribed") == 0) {
                // Extract channel ID and symbol
                char symbol[16], channel_id_str[16];
                extract_json_string(buffer, "symbol", symbol, sizeof(symbol));
                extract_json_string(buffer, "chanId", channel_id_str, sizeof(channel_id_str));
                int channel_id = atoi(channel_id_str);
                
                // Map channel_id to symbol index
                for (int i = 0; i < client->num_symbols; i++) {
                    if (strcmp(client->symbols[i], symbol) == 0) {
                        client->channel_ids[i] = channel_id;
                        printf("✅ Bitfinex: %s mapped to channel %d\n", symbol, channel_id);
                        break;
                    }
                }
            }
        }
        return 0;  // Event messages don't contain price data
    }
    
    // Array message [CHAN_ID, ...] - orderbook snapshot or update
    if (buffer[0] == '[') {
        // Extract channel ID
        const char *pos = buffer + 1;
        while (*pos && *pos == ' ') pos++;
        int channel_id = atoi(pos);
        
        // Find symbol by channel_id
        int symbol_idx = -1;
        for (int i = 0; i < client->num_symbols; i++) {
            if (client->channel_ids[i] == channel_id) {
                symbol_idx = i;
                break;
            }
        }
        
        if (symbol_idx == -1) return 0;  // Unknown channel
        
        // Skip heartbeat messages [CHAN_ID, "hb"]
        if (strstr(buffer, "\"hb\"")) return 0;
        
        // Find first '[' after channel_id (start of data)
        pos = strchr(pos, ',');
        if (!pos) return 0;
        pos++;
        while (*pos && *pos == ' ') pos++;
        
        if (*pos != '[') return 0;  // Invalid format
        pos++;  // Skip opening '['
        
        // Parse orderbook data: [[PRICE, COUNT, AMOUNT], ...] or [PRICE, COUNT, AMOUNT]
        double best_bid = 0, best_ask = 0;
        int is_snapshot = (*pos == '[');  // Snapshot has nested arrays
        
        if (is_snapshot) {
            // Snapshot: [[PRICE1, COUNT1, AMOUNT1], [PRICE2, COUNT2, AMOUNT2], ...]
            // AMOUNT > 0 = bid, AMOUNT < 0 = ask
            while (*pos && *pos != ']') {
                if (*pos == '[') {
                    pos++;
                    double price = atof(pos);
                    while (*pos && *pos != ',') pos++;
                    if (*pos) pos++;  // Skip ','
                    while (*pos && *pos == ' ') pos++;
                    int count = atoi(pos);
                    while (*pos && *pos != ',') pos++;
                    if (*pos) pos++;
                    while (*pos && *pos == ' ') pos++;
                    double amount = atof(pos);
                    
                    if (count > 0) {  // Valid price level
                        if (amount > 0 && best_bid == 0) {
                            best_bid = price;  // First positive amount = best bid
                        } else if (amount < 0 && best_ask == 0) {
                            best_ask = price;  // First negative amount = best ask
                        }
                    }
                    
                    if (best_bid > 0 && best_ask > 0) break;  // Got both
                }
                pos++;
            }
        } else {
            // Update: [PRICE, COUNT, AMOUNT] - single level update
            // We need to maintain full orderbook state, but for now just use latest prices
            // TODO: implement full orderbook reconstruction
            return 0;  // Skip updates for now, rely on periodic snapshots
        }
        
        if (best_bid == 0 || best_ask == 0 || best_ask < best_bid) {
            return 0;  // Invalid prices
        }
        
        // Use mid-price for Price object
        double mid_price = (best_bid + best_ask) / 2.0;
        
        // LATENCY MONITORING
        uint64_t received_tsc = rdtsc();
        struct timespec current_time;
        clock_gettime(CLOCK_REALTIME, &current_time);
        uint64_t received_ts_ms = (uint64_t)current_time.tv_sec * 1000 + current_time.tv_nsec / 1000000;
        
        static int latency_logs = 0;
        static uint64_t prev_ts_ms = 0;
        
        if (++latency_logs % 1500 == 1) {
            uint64_t delta_ms = prev_ts_ms ? (received_ts_ms - prev_ts_ms) : 0;
            printf("⏱️  BITFINEX %s: bid=%.2f, ask=%.2f | Msg #%d | Inter-arrival: %lu ms\n",
                   client->symbols[symbol_idx], best_bid, best_ask, latency_logs, delta_ms);
        }
        prev_ts_ms = received_ts_ms;
        
        // Create Price object
        Price price_obj = {0};
        // Remove 't' prefix from symbol for internal use
        const char *sym = client->symbols[symbol_idx];
        strncpy(price_obj.symbol, sym + 1, sizeof(price_obj.symbol) - 1);  // Skip 't'
        strcpy(price_obj.exchange, "bitfinex");
        price_obj.price = mid_price;
        price_obj.quantity = 100.0;  // Placeholder
        price_obj.timestamp_tsc = received_tsc;
        price_obj.is_valid = 1;
        
        // Push to feed
        if (!spsc_push(client->output_feed, &price_obj)) {
            fprintf(stderr, "⚠️  Bitfinex: Price feed buffer full\n");
        } else {
            notify_new_data();
        }
    }
    
    return len;
}

void bitfinex_ws_destroy(BitfinexWSClient *client) {
    if (!client) return;
    client->is_running = 0;
    if (client->ws) {
        ws_close(client->ws);
    }
    free(client);
}

