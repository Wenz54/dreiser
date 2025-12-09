/**
 * DRAIZER V2 - Exchange Implementation
 */

#include "exchange.h"
#include "binance_ws.h"
#include "mexc_ws.h"
#include "bybit_ws.h"
#include "okx_ws.h"
#include "gateio_ws.h"
#include "kucoin_ws.h"
#include "huobi_ws.h"
#include "bitget_ws.h"
#include <stdlib.h>
#include <string.h>

// Binance adapter
static int binance_connect_adapter(Exchange *ex, const char **symbols, int num_symbols) {
    BinanceWSClient *client = (BinanceWSClient*)ex->impl;
    if (binance_ws_connect(client) < 0) return -1;
    return binance_ws_subscribe(client);
}

static int binance_process_adapter(Exchange *ex) {
    BinanceWSClient *client = (BinanceWSClient*)ex->impl;
    return binance_ws_process(client);
}

static void binance_close_adapter(Exchange *ex) {
    BinanceWSClient *client = (BinanceWSClient*)ex->impl;
    binance_ws_close(client);
}

static void binance_destroy_adapter(Exchange *ex) {
    BinanceWSClient *client = (BinanceWSClient*)ex->impl;
    binance_ws_destroy(client);
}

// MEXC adapter
static int mexc_connect_adapter(Exchange *ex, const char **symbols, int num_symbols) {
    MEXCWSClient *client = (MEXCWSClient*)ex->impl;
    if (mexc_ws_connect(client) < 0) return -1;
    return mexc_ws_subscribe(client);
}

static int mexc_process_adapter(Exchange *ex) {
    MEXCWSClient *client = (MEXCWSClient*)ex->impl;
    return mexc_ws_process(client);
}

static void mexc_close_adapter(Exchange *ex) {
    MEXCWSClient *client = (MEXCWSClient*)ex->impl;
    mexc_ws_close(client);
}

static void mexc_destroy_adapter(Exchange *ex) {
    MEXCWSClient *client = (MEXCWSClient*)ex->impl;
    mexc_ws_destroy(client);
}

// Bybit adapter
static int bybit_connect_adapter(Exchange *ex, const char **symbols, int num_symbols) {
    BybitWSClient *client = (BybitWSClient*)ex->impl;
    if (bybit_ws_connect(client) < 0) return -1;
    return bybit_ws_subscribe(client);
}

static int bybit_process_adapter(Exchange *ex) {
    BybitWSClient *client = (BybitWSClient*)ex->impl;
    return bybit_ws_process(client);
}

static void bybit_close_adapter(Exchange *ex) {
    BybitWSClient *client = (BybitWSClient*)ex->impl;
    bybit_ws_close(client);
}

static void bybit_destroy_adapter(Exchange *ex) {
    BybitWSClient *client = (BybitWSClient*)ex->impl;
    bybit_ws_destroy(client);
}

// OKX adapter
static int okx_connect_adapter(Exchange *ex, const char **symbols, int num_symbols) {
    OKXWSClient *client = (OKXWSClient*)ex->impl;
    if (okx_ws_connect(client) < 0) return -1;
    return okx_ws_subscribe(client);
}

static int okx_process_adapter(Exchange *ex) {
    OKXWSClient *client = (OKXWSClient*)ex->impl;
    return okx_ws_process(client);
}

static void okx_close_adapter(Exchange *ex) {
    OKXWSClient *client = (OKXWSClient*)ex->impl;
    okx_ws_close(client);
}

static void okx_destroy_adapter(Exchange *ex) {
    OKXWSClient *client = (OKXWSClient*)ex->impl;
    okx_ws_destroy(client);
}

// Gate.io adapter
static int gateio_connect_adapter(Exchange *ex, const char **symbols, int num_symbols) {
    GateIOWSClient *client = (GateIOWSClient*)ex->impl;
    if (gateio_ws_connect(client) < 0) return -1;
    return gateio_ws_subscribe(client);
}

static int gateio_process_adapter(Exchange *ex) {
    GateIOWSClient *client = (GateIOWSClient*)ex->impl;
    return gateio_ws_process(client);
}

static void gateio_close_adapter(Exchange *ex) {
    GateIOWSClient *client = (GateIOWSClient*)ex->impl;
    gateio_ws_close(client);
}

static void gateio_destroy_adapter(Exchange *ex) {
    GateIOWSClient *client = (GateIOWSClient*)ex->impl;
    gateio_ws_destroy(client);
}

// KuCoin adapter
static int kucoin_connect_adapter(Exchange *ex, const char **symbols, int num_symbols) {
    KuCoinWSClient *client = (KuCoinWSClient*)ex->impl;
    if (kucoin_ws_connect(client) < 0) return -1;
    return kucoin_ws_subscribe(client);
}

static int kucoin_process_adapter(Exchange *ex) {
    KuCoinWSClient *client = (KuCoinWSClient*)ex->impl;
    return kucoin_ws_process(client);
}

static void kucoin_close_adapter(Exchange *ex) {
    KuCoinWSClient *client = (KuCoinWSClient*)ex->impl;
    kucoin_ws_close(client);
}

static void kucoin_destroy_adapter(Exchange *ex) {
    KuCoinWSClient *client = (KuCoinWSClient*)ex->impl;
    kucoin_ws_destroy(client);
}

// Huobi adapter
static int huobi_connect_adapter(Exchange *ex, const char **symbols, int num_symbols) {
    HuobiWSClient *client = (HuobiWSClient*)ex->impl;
    if (huobi_ws_connect(client) < 0) return -1;
    return huobi_ws_subscribe(client);
}

static int huobi_process_adapter(Exchange *ex) {
    HuobiWSClient *client = (HuobiWSClient*)ex->impl;
    return huobi_ws_process(client);
}

static void huobi_close_adapter(Exchange *ex) {
    HuobiWSClient *client = (HuobiWSClient*)ex->impl;
    huobi_ws_close(client);
}

static void huobi_destroy_adapter(Exchange *ex) {
    HuobiWSClient *client = (HuobiWSClient*)ex->impl;
    huobi_ws_destroy(client);
}

// Bitget adapter
static int bitget_connect_adapter(Exchange *ex, const char **symbols, int num_symbols) {
    BitgetWSClient *client = (BitgetWSClient*)ex->impl;
    if (bitget_ws_connect(client) < 0) return -1;
    return bitget_ws_subscribe(client);
}

static int bitget_process_adapter(Exchange *ex) {
    BitgetWSClient *client = (BitgetWSClient*)ex->impl;
    return bitget_ws_process(client);
}

static void bitget_close_adapter(Exchange *ex) {
    BitgetWSClient *client = (BitgetWSClient*)ex->impl;
    bitget_ws_close(client);
}

static void bitget_destroy_adapter(Exchange *ex) {
    BitgetWSClient *client = (BitgetWSClient*)ex->impl;
    bitget_ws_destroy(client);
}

Exchange* exchange_create(ExchangeType type, SPSCRingBuffer *output_feed) {
    Exchange *ex = calloc(1, sizeof(Exchange));
    if (!ex) return NULL;
    
    ex->type = type;
    ex->output_feed = output_feed;
    ex->enabled = true;
    ex->connected = false;
    
    switch (type) {
        case EXCHANGE_BINANCE:
            strcpy(ex->name, "Binance");
            ex->connect = binance_connect_adapter;
            ex->process = binance_process_adapter;
            ex->close = binance_close_adapter;
            ex->destroy = binance_destroy_adapter;
            break;
        
        case EXCHANGE_MEXC:
            strcpy(ex->name, "MEXC");
            ex->connect = mexc_connect_adapter;
            ex->process = mexc_process_adapter;
            ex->close = mexc_close_adapter;
            ex->destroy = mexc_destroy_adapter;
            break;
        
        case EXCHANGE_BYBIT:
            strcpy(ex->name, "Bybit");
            ex->connect = bybit_connect_adapter;
            ex->process = bybit_process_adapter;
            ex->close = bybit_close_adapter;
            ex->destroy = bybit_destroy_adapter;
            break;
        
        case EXCHANGE_OKX:
            strcpy(ex->name, "OKX");
            ex->connect = okx_connect_adapter;
            ex->process = okx_process_adapter;
            ex->close = okx_close_adapter;
            ex->destroy = okx_destroy_adapter;
            break;
        
        case EXCHANGE_GATEIO:
            strcpy(ex->name, "Gate.io");
            ex->connect = gateio_connect_adapter;
            ex->process = gateio_process_adapter;
            ex->close = gateio_close_adapter;
            ex->destroy = gateio_destroy_adapter;
            break;
        
        case EXCHANGE_KUCOIN:
            strcpy(ex->name, "KuCoin");
            ex->connect = kucoin_connect_adapter;
            ex->process = kucoin_process_adapter;
            ex->close = kucoin_close_adapter;
            ex->destroy = kucoin_destroy_adapter;
            break;
        
        case EXCHANGE_HUOBI:
            strcpy(ex->name, "Huobi");
            ex->connect = huobi_connect_adapter;
            ex->process = huobi_process_adapter;
            ex->close = huobi_close_adapter;
            ex->destroy = huobi_destroy_adapter;
            break;
        
        case EXCHANGE_BITGET:
            strcpy(ex->name, "Bitget");
            ex->connect = bitget_connect_adapter;
            ex->process = bitget_process_adapter;
            ex->close = bitget_close_adapter;
            ex->destroy = bitget_destroy_adapter;
            break;
        
        default:
            free(ex);
            return NULL;
    }
    
    return ex;
}

int exchange_connect(Exchange *ex, const char **symbols, int num_symbols) {
    if (!ex || !ex->connect) return -1;
    
    // Create implementation-specific client
    switch (ex->type) {
        case EXCHANGE_BINANCE:
            ex->impl = binance_ws_create(symbols, num_symbols, ex->output_feed);
            break;
        
        case EXCHANGE_MEXC:
            ex->impl = mexc_ws_create(symbols, num_symbols, ex->output_feed);
            break;
        
        case EXCHANGE_BYBIT:
            ex->impl = bybit_ws_create(symbols, num_symbols, ex->output_feed);
            break;
        
        case EXCHANGE_OKX:
            ex->impl = okx_ws_create(symbols, num_symbols, ex->output_feed);
            break;
        
        case EXCHANGE_GATEIO:
            ex->impl = gateio_ws_create(symbols, num_symbols, ex->output_feed);
            break;
        
        case EXCHANGE_KUCOIN:
            ex->impl = kucoin_ws_create(symbols, num_symbols, ex->output_feed);
            break;
        
        case EXCHANGE_HUOBI:
            ex->impl = huobi_ws_create(symbols, num_symbols, ex->output_feed);
            break;
        
        case EXCHANGE_BITGET:
            ex->impl = bitget_ws_create(symbols, num_symbols, ex->output_feed);
            break;
        
        default:
            return -1;
    }
    
    if (!ex->impl) return -1;
    
    int result = ex->connect(ex, symbols, num_symbols);
    if (result >= 0) {  // ws_send_text returns bytes sent (>0), not 0!
        ex->connected = true;
    }
    
    return result;
}

int exchange_process(Exchange *ex) {
    if (!ex || !ex->process || !ex->connected) return -1;
    return ex->process(ex);
}

void exchange_close(Exchange *ex) {
    if (!ex || !ex->close) return;
    ex->close(ex);
    ex->connected = false;
}

void exchange_destroy(Exchange *ex) {
    if (!ex) return;
    
    if (ex->destroy && ex->impl) {
        ex->destroy(ex);
    }
    
    free(ex);
}

int exchange_get_fd(Exchange *ex) {
    if (!ex || !ex->impl) return -1;
    
    // Get FD from exchange-specific WebSocket client
    switch (ex->type) {
        case EXCHANGE_BINANCE: {
            BinanceWSClient *client = (BinanceWSClient*)ex->impl;
            return client->ws ? ws_get_fd(client->ws) : -1;
        }
        case EXCHANGE_MEXC: {
            MEXCWSClient *client = (MEXCWSClient*)ex->impl;
            return client->ws ? ws_get_fd(client->ws) : -1;
        }
        case EXCHANGE_BYBIT: {
            BybitWSClient *client = (BybitWSClient*)ex->impl;
            return client->ws ? ws_get_fd(client->ws) : -1;
        }
        case EXCHANGE_OKX: {
            OKXWSClient *client = (OKXWSClient*)ex->impl;
            return client->ws ? ws_get_fd(client->ws) : -1;
        }
        case EXCHANGE_GATEIO: {
            GateIOWSClient *client = (GateIOWSClient*)ex->impl;
            return client->ws ? ws_get_fd(client->ws) : -1;
        }
        case EXCHANGE_KUCOIN: {
            KuCoinWSClient *client = (KuCoinWSClient*)ex->impl;
            return client->ws ? ws_get_fd(client->ws) : -1;
        }
        case EXCHANGE_HUOBI: {
            HuobiWSClient *client = (HuobiWSClient*)ex->impl;
            return client->ws ? ws_get_fd(client->ws) : -1;
        }
        case EXCHANGE_BITGET: {
            BitgetWSClient *client = (BitgetWSClient*)ex->impl;
            return client->ws ? ws_get_fd(client->ws) : -1;
        }
        default:
            return -1;
    }
}

const char* exchange_get_name(ExchangeType type) {
    switch (type) {
        case EXCHANGE_BINANCE: return "Binance";
        case EXCHANGE_MEXC: return "MEXC";
        case EXCHANGE_BYBIT: return "Bybit";
        case EXCHANGE_OKX: return "OKX";
        case EXCHANGE_GATEIO: return "Gate.io";
        case EXCHANGE_KUCOIN: return "KuCoin";
        case EXCHANGE_HUOBI: return "Huobi";
        case EXCHANGE_BITGET: return "Bitget";
        default: return "Unknown";
    }
}

