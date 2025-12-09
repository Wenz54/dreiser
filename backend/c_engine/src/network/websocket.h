/**
 * DRAIZER V2 - WebSocket Client
 * Minimal WebSocket implementation for crypto exchanges
 */

#ifndef WEBSOCKET_H
#define WEBSOCKET_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

#define WS_MAX_FRAME_SIZE 65536
#define WS_RECONNECT_DELAY_MS 5000

typedef enum {
    WS_STATE_DISCONNECTED,
    WS_STATE_CONNECTING,
    WS_STATE_CONNECTED,
    WS_STATE_ERROR
} WSState;

typedef struct {
    int socket_fd;
    WSState state;
    char host[256];
    char path[512];
    int port;
    bool use_ssl;
    
    // SSL context (for wss://)
    SSL_CTX *ssl_ctx;
    SSL *ssl;
    
    // Buffers
    uint8_t recv_buffer[WS_MAX_FRAME_SIZE];
    size_t recv_len;
    
    // Stats
    uint64_t messages_received;
    uint64_t messages_sent;
    uint64_t reconnect_count;
    uint64_t last_pong_ts;
} WebSocket;

/**
 * Create WebSocket connection
 * 
 * @param url Full URL (e.g., "wss://stream.binance.com:9443/ws")
 * @return WebSocket* or NULL on failure
 */
WebSocket* ws_create(const char *url);

/**
 * Connect to server
 */
int ws_connect(WebSocket *ws);

/**
 * Send text message
 */
int ws_send_text(WebSocket *ws, const char *text);

/**
 * Send ping
 */
int ws_send_ping(WebSocket *ws);

/**
 * Receive message (non-blocking)
 * 
 * @param buffer Output buffer
 * @param max_len Buffer size
 * @return Number of bytes received, 0 if no data, -1 on error
 */
int ws_receive(WebSocket *ws, char *buffer, size_t max_len);

/**
 * Close connection
 */
void ws_close(WebSocket *ws);

/**
 * Destroy WebSocket
 */
void ws_destroy(WebSocket *ws);

/**
 * Check if connected
 */
bool ws_is_connected(WebSocket *ws);

/**
 * Get socket file descriptor for select()
 * @return socket FD or -1 if not connected
 */
int ws_get_fd(WebSocket *ws);

#endif // WEBSOCKET_H

