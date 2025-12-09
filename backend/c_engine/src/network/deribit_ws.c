/**
 * DRAIZER V2 - Deribit WebSocket Implementation
 * Parse orderbook snapshots/updates and funding rates
 * 
 * JSON-RPC 2.0 format:
 * Subscribe: {"jsonrpc":"2.0","id":1,"method":"public/subscribe","params":{"channels":["book.BTC-PERPETUAL.raw"]}}
 * Response: {"jsonrpc":"2.0","method":"subscription","params":{"channel":"book.BTC-PERPETUAL.raw","data":{...}}}
 */

#include "deribit_ws.h"
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

static double extract_json_double(const char *json, const char *key) {
    const char *pos = find_json_field(json, key);
    if (!pos) return 0.0;
    pos += strlen(key) + 2;  // Skip "key":
    while (*pos && (*pos == ' ' || *pos == '"')) pos++;
    return atof(pos);
}

DeribitWSClient* deribit_ws_create(const char *symbols[], int num_symbols, SPSCRingBuffer *output_feed) {
    DeribitWSClient *client = calloc(1, sizeof(DeribitWSClient));
    client->output_feed = output_feed;
    client->num_symbols = num_symbols < 10 ? num_symbols : 10;
    
    for (int i = 0; i < client->num_symbols; i++) {
        // Convert "BTCUSD" -> "BTC-PERPETUAL" (Deribit format)
        if (strstr(symbols[i], "-PERPETUAL")) {
            strncpy(client->symbols[i], symbols[i], sizeof(client->symbols[i]) - 1);
        } else {
            // Extract base currency (e.g., "BTCUSD" -> "BTC")
            char base[8] = {0};
            int j = 0;
            while (symbols[i][j] && symbols[i][j] != 'U' && j < 7) {
                base[j] = symbols[i][j];
                j++;
            }
            snprintf(client->symbols[i], sizeof(client->symbols[i]), "%s-PERPETUAL", base);
        }
        client->funding_rates[i] = 0.0;
        client->funding_timestamps[i] = 0;
    }
    
    return client;
}

int deribit_ws_connect(DeribitWSClient *client) {
    client->ws = ws_connect(DERIBIT_WS_URL);
    if (!client->ws) {
        fprintf(stderr, "❌ Deribit: WebSocket connection failed\n");
        return -1;
    }
    
    printf("✅ Deribit: Connected to %s\n", DERIBIT_WS_URL);
    
    // Subscribe to orderbook for each symbol
    // Format: book.{INSTRUMENT}.raw (raw = full orderbook updates)
    char subscribe_msg[2048];
    strcpy(subscribe_msg, "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"public/subscribe\",\"params\":{\"channels\":[");
    
    for (int i = 0; i < client->num_symbols; i++) {
        char channel[64];
        snprintf(channel, sizeof(channel), "%s\"book.%s.raw\"", i > 0 ? "," : "", client->symbols[i]);
        strcat(subscribe_msg, channel);
    }
    strcat(subscribe_msg, "]}}");
    
    if (ws_send(client->ws, subscribe_msg, strlen(subscribe_msg)) < 0) {
        fprintf(stderr, "⚠️  Deribit: Failed to subscribe\n");
        return -1;
    }
    
    printf("📡 Deribit: Subscribed to %d perpetual futures orderbooks\n", client->num_symbols);
    
    client->is_running = 1;
    return 0;
}

int deribit_ws_process(DeribitWSClient *client) {
    char buffer[65536];  // Deribit can send large orderbook snapshots
    int len = ws_receive(client->ws, buffer, sizeof(buffer) - 1);
    if (len <= 0) return len;
    buffer[len] = '\0';
    
    // RAW DATA LOGGING - Show sample every 3000 messages for monitoring
    static int msg_count = 0;
    msg_count++;
    
    if (msg_count % 3000 == 1) {
        printf("📊 DERIBIT RAW #%d:\n%.300s...\n", msg_count, buffer);
    }
    
    // Parse JSON-RPC message
    const char *method_pos = find_json_field(buffer, "method");
    if (!method_pos) {
        // Response to subscribe request (has "result" field)
        return 0;
    }
    
    char method[64];
    extract_json_string(buffer, "method", method, sizeof(method));
    
    if (strcmp(method, "subscription") != 0) {
        return 0;  // Not a subscription update
    }
    
    // Extract channel name to identify symbol
    char channel[64];
    extract_json_string(buffer, "channel", channel, sizeof(channel));
    
    // Parse channel: "book.BTC-PERPETUAL.raw" -> "BTC-PERPETUAL"
    const char *instrument_start = strchr(channel, '.') + 1;
    if (!instrument_start) return 0;
    const char *instrument_end = strchr(instrument_start, '.');
    if (!instrument_end) return 0;
    
    char instrument[24];
    size_t len_instrument = instrument_end - instrument_start;
    if (len_instrument >= sizeof(instrument)) len_instrument = sizeof(instrument) - 1;
    strncpy(instrument, instrument_start, len_instrument);
    instrument[len_instrument] = '\0';
    
    // Find symbol index
    int symbol_idx = -1;
    for (int i = 0; i < client->num_symbols; i++) {
        if (strcmp(client->symbols[i], instrument) == 0) {
            symbol_idx = i;
            break;
        }
    }
    
    if (symbol_idx == -1) return 0;  // Unknown symbol
    
    // Extract bids and asks from data object
    const char *data_pos = find_json_field(buffer, "data");
    if (!data_pos) return 0;
    
    // Parse timestamp (optional)
    uint64_t exchange_ts_ms = (uint64_t)extract_json_double(buffer, "timestamp");
    
    // Parse bids: "bids":[[price,amount],...]
    const char *bids_pos = find_json_field(data_pos, "bids");
    double best_bid = 0.0;
    if (bids_pos) {
        bids_pos = strchr(bids_pos, '[');
        if (bids_pos) {
            bids_pos++;  // Skip '['
            if (*bids_pos == '[') {
                bids_pos++;  // Skip nested '['
                best_bid = atof(bids_pos);
            }
        }
    }
    
    // Parse asks: "asks":[[price,amount],...]
    const char *asks_pos = find_json_field(data_pos, "asks");
    double best_ask = 0.0;
    if (asks_pos) {
        asks_pos = strchr(asks_pos, '[');
        if (asks_pos) {
            asks_pos++;  // Skip '['
            if (*asks_pos == '[') {
                asks_pos++;  // Skip nested '['
                best_ask = atof(asks_pos);
            }
        }
    }
    
    if (best_bid == 0 || best_ask == 0 || best_ask < best_bid) {
        return 0;  // Invalid prices
    }
    
    // Update funding rate if present
    double funding_rate = extract_json_double(buffer, "current_funding");
    if (funding_rate != 0.0) {
        client->funding_rates[symbol_idx] = funding_rate * 10000.0;  // Convert to bps
        client->funding_timestamps[symbol_idx] = exchange_ts_ms;
    }
    
    // Use mid-price for Price object
    double mid_price = (best_bid + best_ask) / 2.0;
    
    // LATENCY MONITORING
    uint64_t received_tsc = rdtsc();
    
    static int latency_logs = 0;
    latency_logs++;
    
    if (exchange_ts_ms > 0 && latency_logs % 1500 == 1) {
        struct timespec current_time;
        clock_gettime(CLOCK_REALTIME, &current_time);
        uint64_t current_ts_ms = (uint64_t)current_time.tv_sec * 1000 + current_time.tv_nsec / 1000000;
        uint64_t latency_ms = current_ts_ms - exchange_ts_ms;
        
        printf("⏱️  DERIBIT %s: bid=%.2f, ask=%.2f | Msg #%d | LATENCY: %lu ms | Funding: %.4f%%\n",
               instrument, best_bid, best_ask, latency_logs, latency_ms, client->funding_rates[symbol_idx] / 100.0);
    }
    
    // Create Price object
    Price price_obj = {0};
    // Convert "BTC-PERPETUAL" -> "BTCUSD" for internal consistency
    const char *dash_pos = strchr(instrument, '-');
    if (dash_pos) {
        size_t base_len = dash_pos - instrument;
        if (base_len < sizeof(price_obj.symbol) - 3) {
            strncpy(price_obj.symbol, instrument, base_len);
            strcpy(price_obj.symbol + base_len, "USD");  // Append "USD"
        }
    }
    
    strcpy(price_obj.exchange, "deribit");
    price_obj.price = mid_price;
    price_obj.quantity = 100.0;  // Placeholder
    price_obj.timestamp_tsc = received_tsc;
    price_obj.is_valid = 1;
    
    // Push to feed
    if (!spsc_push(client->output_feed, &price_obj)) {
        fprintf(stderr, "⚠️  Deribit: Price feed buffer full\n");
    } else {
        notify_new_data();
    }
    
    return len;
}

double deribit_get_funding_rate(DeribitWSClient *client, const char *symbol) {
    for (int i = 0; i < client->num_symbols; i++) {
        if (strcmp(client->symbols[i], symbol) == 0) {
            return client->funding_rates[i];
        }
    }
    return 0.0;
}

void deribit_ws_destroy(DeribitWSClient *client) {
    if (!client) return;
    client->is_running = 0;
    if (client->ws) {
        ws_close(client->ws);
    }
    free(client);
}

