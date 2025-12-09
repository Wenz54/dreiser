/**
 * DRAIZER V2 - WebSocket Implementation with SSL support
 */

#include "websocket.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <fcntl.h>
#include <errno.h>

// WebSocket frame opcodes
#define WS_OPCODE_TEXT 0x01
#define WS_OPCODE_BINARY 0x02
#define WS_OPCODE_CLOSE 0x08
#define WS_OPCODE_PING 0x09
#define WS_OPCODE_PONG 0x0A

static bool ssl_initialized = false;

static void init_ssl() {
    if (!ssl_initialized) {
        SSL_library_init();
        SSL_load_error_strings();
        OpenSSL_add_all_algorithms();
        ssl_initialized = true;
    }
}

WebSocket* ws_create(const char *url) {
    // printf("🔍 ws_create() called with: %s\n", url);  // DEBUG
    
    WebSocket *ws = calloc(1, sizeof(WebSocket));
    if (!ws) return NULL;
    
    ws->state = WS_STATE_DISCONNECTED;
    ws->socket_fd = -1;
    ws->ssl_ctx = NULL;
    ws->ssl = NULL;
    
    // Parse URL
    // wss://stream.binance.com:9443/ws/btcusdt@trade
    if (strncmp(url, "wss://", 6) == 0) {
        // printf("🔍 Detected wss://, setting use_ssl=true\n");  // DEBUG
        ws->use_ssl = true;
        url += 6;
        // printf("🔍 URL after removing wss://: %s\n", url);  // DEBUG
    } else if (strncmp(url, "ws://", 5) == 0) {
        // printf("🔍 Detected ws://, setting use_ssl=false\n");  // DEBUG
        ws->use_ssl = false;
        url += 5;
        // printf("🔍 URL after removing ws://: %s\n", url);  // DEBUG
    } else {
        printf("❌ Invalid URL scheme\n");
        free(ws);
        return NULL;
    }
    
    // Extract host, port, path
    const char *colon = strchr(url, ':');
    const char *slash = strchr(url, '/');
    
    if (colon && slash) {
        // host:port/path
        size_t host_len = colon - url;
        strncpy(ws->host, url, host_len);
        ws->host[host_len] = '\0';
        
        ws->port = atoi(colon + 1);
        strcpy(ws->path, slash);
    } else if (slash) {
        // host/path (default port)
        size_t host_len = slash - url;
        strncpy(ws->host, url, host_len);
        ws->host[host_len] = '\0';
        
        ws->port = ws->use_ssl ? 443 : 80;
        strcpy(ws->path, slash);
    } else {
        free(ws);
        return NULL;
    }
    
    return ws;
}

int ws_connect(WebSocket *ws) {
    if (!ws) return -1;
    
    ws->state = WS_STATE_CONNECTING;
    
    // Initialize SSL if needed
    if (ws->use_ssl) {
        init_ssl();
        
        // Create SSL context
        ws->ssl_ctx = SSL_CTX_new(TLS_client_method());
        if (!ws->ssl_ctx) {
            fprintf(stderr, "❌ Failed to create SSL context\n");
            ERR_print_errors_fp(stderr);
            ws->state = WS_STATE_ERROR;
            return -1;
        }
        
        // Don't verify certificates (for now - production should verify!)
        SSL_CTX_set_verify(ws->ssl_ctx, SSL_VERIFY_NONE, NULL);
    }
    
    // Resolve hostname
    struct hostent *he = gethostbyname(ws->host);
    if (!he) {
        fprintf(stderr, "❌ Failed to resolve host: %s\n", ws->host);
        ws->state = WS_STATE_ERROR;
        return -1;
    }
    
    // Create socket
    ws->socket_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (ws->socket_fd < 0) {
        perror("socket");
        ws->state = WS_STATE_ERROR;
        return -1;
    }
    
    // Set TCP_NODELAY (disable Nagle's algorithm)
    int flag = 1;
    setsockopt(ws->socket_fd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));
    
    // Connect (blocking for now)
    struct sockaddr_in server;
    server.sin_family = AF_INET;
    server.sin_port = htons(ws->port);
    memcpy(&server.sin_addr, he->h_addr_list[0], he->h_length);
    
    if (connect(ws->socket_fd, (struct sockaddr*)&server, sizeof(server)) < 0) {
        perror("connect");
        close(ws->socket_fd);
        ws->socket_fd = -1;
        ws->state = WS_STATE_ERROR;
        return -1;
    }
    
    // SSL handshake if needed
    if (ws->use_ssl) {
        ws->ssl = SSL_new(ws->ssl_ctx);
        if (!ws->ssl) {
            fprintf(stderr, "❌ Failed to create SSL\n");
            close(ws->socket_fd);
            ws->socket_fd = -1;
            ws->state = WS_STATE_ERROR;
            return -1;
        }
        
        SSL_set_fd(ws->ssl, ws->socket_fd);
        
        // Set SNI (Server Name Indication) - REQUIRED for modern SSL servers
        SSL_set_tlsext_host_name(ws->ssl, ws->host);
        
        if (SSL_connect(ws->ssl) <= 0) {
            fprintf(stderr, "❌ SSL handshake failed\n");
            ERR_print_errors_fp(stderr);
            SSL_free(ws->ssl);
            ws->ssl = NULL;
            close(ws->socket_fd);
            ws->socket_fd = -1;
            ws->state = WS_STATE_ERROR;
            return -1;
        }
    }
    
    // Set non-blocking after connection
    fcntl(ws->socket_fd, F_SETFL, O_NONBLOCK);
    
    // Send WebSocket handshake
    char handshake[1024];
    snprintf(handshake, sizeof(handshake),
        "GET %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n",
        ws->path, ws->host);
    
    int sent;
    if (ws->use_ssl) {
        sent = SSL_write(ws->ssl, handshake, strlen(handshake));
    } else {
        sent = send(ws->socket_fd, handshake, strlen(handshake), 0);
    }
    
    if (sent < 0) {
        perror("send handshake");
        ws_close(ws);
        return -1;
    }
    
    // Wait for response (simplified - should parse HTTP response)
    char response[4096];
    int received;
    
    // Set temporary blocking for handshake response
    int flags = fcntl(ws->socket_fd, F_GETFL, 0);
    fcntl(ws->socket_fd, F_SETFL, flags & ~O_NONBLOCK);
    
    if (ws->use_ssl) {
        received = SSL_read(ws->ssl, response, sizeof(response) - 1);
    } else {
        received = recv(ws->socket_fd, response, sizeof(response) - 1, 0);
    }
    
    // Restore non-blocking
    fcntl(ws->socket_fd, F_SETFL, flags);
    
    if (received > 0) {
        response[received] = '\0';
        // printf("🔍 Handshake response (%d bytes):\n%s\n", received, response);  // DEBUG
        if (strstr(response, "101") && strstr(response, "Switching Protocols")) {
            ws->state = WS_STATE_CONNECTED;
            return 0;
        } else {
            fprintf(stderr, "❌ Response doesn't contain '101 Switching Protocols'\n");
        }
    } else {
        fprintf(stderr, "❌ No handshake response received (received=%d, errno=%d)\n", received, errno);
    }
    
    fprintf(stderr, "❌ WebSocket handshake failed\n");
    ws_close(ws);
    return -1;
}

int ws_send_text(WebSocket *ws, const char *text) {
    if (!ws || ws->state != WS_STATE_CONNECTED) return -1;
    
    size_t text_len = strlen(text);
    uint8_t frame[WS_MAX_FRAME_SIZE];
    size_t frame_len = 0;
    
    // FIN + TEXT opcode
    frame[frame_len++] = 0x80 | WS_OPCODE_TEXT;
    
    // Mask bit + payload length
    if (text_len < 126) {
        frame[frame_len++] = 0x80 | text_len;
    } else if (text_len < 65536) {
        frame[frame_len++] = 0x80 | 126;
        frame[frame_len++] = (text_len >> 8) & 0xFF;
        frame[frame_len++] = text_len & 0xFF;
    } else {
        frame[frame_len++] = 0x80 | 127;
        for (int i = 7; i >= 0; i--) {
            frame[frame_len++] = (text_len >> (i * 8)) & 0xFF;
        }
    }
    
    // Masking key (simple random)
    uint8_t mask[4] = {0x12, 0x34, 0x56, 0x78};
    memcpy(frame + frame_len, mask, 4);
    frame_len += 4;
    
    // Masked payload
    for (size_t i = 0; i < text_len; i++) {
        frame[frame_len++] = text[i] ^ mask[i % 4];
    }
    
    int sent;
    if (ws->use_ssl) {
        sent = SSL_write(ws->ssl, frame, frame_len);
    } else {
        sent = send(ws->socket_fd, frame, frame_len, 0);
    }
    
    if (sent > 0) {
        ws->messages_sent++;
        return sent;
    }
    
    return -1;
}

int ws_receive(WebSocket *ws, char *buffer, size_t max_len) {
    if (!ws || ws->state != WS_STATE_CONNECTED) return -1;
    
    uint8_t frame_header[14];
    int header_len;
    
    if (ws->use_ssl) {
        header_len = SSL_read(ws->ssl, frame_header, 2);
    } else {
        header_len = recv(ws->socket_fd, frame_header, 2, MSG_DONTWAIT);
    }
    
    if (header_len <= 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) return 0;
        return -1;
    }
    
    uint8_t fin = frame_header[0] & 0x80;
    uint8_t opcode = frame_header[0] & 0x0F;
    uint8_t masked = frame_header[1] & 0x80;
    uint64_t payload_len = frame_header[1] & 0x7F;
    
    // Read extended payload length
    if (payload_len == 126) {
        uint8_t ext[2];
        int read_bytes = ws->use_ssl ? SSL_read(ws->ssl, ext, 2) : recv(ws->socket_fd, ext, 2, 0);
        if (read_bytes != 2) return -1;
        payload_len = (ext[0] << 8) | ext[1];
    } else if (payload_len == 127) {
        uint8_t ext[8];
        int read_bytes = ws->use_ssl ? SSL_read(ws->ssl, ext, 8) : recv(ws->socket_fd, ext, 8, 0);
        if (read_bytes != 8) return -1;
        payload_len = 0;
        for (int i = 0; i < 8; i++) {
            payload_len = (payload_len << 8) | ext[i];
        }
    }
    
    if (payload_len > max_len) return -1;
    
    // Read payload
    size_t total_read = 0;
    while (total_read < payload_len) {
        int chunk = ws->use_ssl ? 
            SSL_read(ws->ssl, buffer + total_read, payload_len - total_read) :
            recv(ws->socket_fd, buffer + total_read, payload_len - total_read, 0);
        
        if (chunk <= 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) continue;
            return -1;
        }
        total_read += chunk;
    }
    
    buffer[total_read] = '\0';
    ws->messages_received++;
    
    return total_read;
}

int ws_send_ping(WebSocket *ws) {
    if (!ws || ws->state != WS_STATE_CONNECTED) return -1;
    
    uint8_t frame[6] = {0x80 | WS_OPCODE_PING, 0x80, 0, 0, 0, 0};
    
    int sent = ws->use_ssl ? SSL_write(ws->ssl, frame, 6) : send(ws->socket_fd, frame, 6, 0);
    return sent > 0 ? 0 : -1;
}

void ws_close(WebSocket *ws) {
    if (!ws) return;
    
    if (ws->state == WS_STATE_CONNECTED) {
        // Send close frame
        uint8_t frame[6] = {0x80 | WS_OPCODE_CLOSE, 0x80, 0, 0, 0, 0};
        if (ws->use_ssl && ws->ssl) {
            SSL_write(ws->ssl, frame, 6);
        } else if (ws->socket_fd >= 0) {
            send(ws->socket_fd, frame, 6, 0);
        }
    }
    
    if (ws->ssl) {
        SSL_shutdown(ws->ssl);
        SSL_free(ws->ssl);
        ws->ssl = NULL;
    }
    
    if (ws->ssl_ctx) {
        SSL_CTX_free(ws->ssl_ctx);
        ws->ssl_ctx = NULL;
    }
    
    if (ws->socket_fd >= 0) {
        close(ws->socket_fd);
        ws->socket_fd = -1;
    }
    
    ws->state = WS_STATE_DISCONNECTED;
}

void ws_destroy(WebSocket *ws) {
    if (!ws) return;
    ws_close(ws);
    free(ws);
}

bool ws_is_connected(WebSocket *ws) {
    return ws && ws->state == WS_STATE_CONNECTED;
}

int ws_get_fd(WebSocket *ws) {
    if (!ws || ws->socket_fd < 0) return -1;
    return ws->socket_fd;
}
