# DRAIZER V2.0 - TECHNICAL SPEC

**Version:** 2.0.0  
**Date:** 2025-10-28  
**Type:** Quantitative Arbitrage (Math-based, NO LLM)

---

## ARCHITECTURE

```
┌─────────────────────────────────────┐
│ Frontend (React) - existing         │
└─────────────────────────────────────┘
              ↓ HTTP/WS
┌─────────────────────────────────────┐
│ Python Backend (FastAPI)            │
│ ├─ Auth, API, DB (PostgreSQL)       │
│ ├─ Portfolio, Analytics             │
│ └─ IPC Bridge → C Engine            │
└─────────────────────────────────────┘
              ↓ Shared Memory + Socket
┌─────────────────────────────────────┐
│ C Trading Engine (CRITICAL PATH)    │
│ ├─ WebSocket (Binance, MEXC)        │
│ ├─ Arbitrage Detection (SIMD)       │
│ ├─ Risk Manager (inline)            │
│ └─ Order Execution (async)          │
└─────────────────────────────────────┘
```

**Latency target:** <50μs (P99 <100μs)  
**Throughput:** 100k+ price updates/sec

---

## C ENGINE STRUCTURE

```
backend/c_engine/
├── src/
│   ├── main.c                    # Entry, event loop
│   ├── network/
│   │   ├── iouring.c             # io_uring wrapper (async I/O)
│   │   ├── websocket.c           # Custom WS parser
│   │   └── connection.c          # Connection manager
│   ├── data/
│   │   ├── spsc_ring.c           # Lock-free SPSC buffer
│   │   ├── price_cache.c         # Lock-free cache (seqlock)
│   │   └── hash_table.c          # Cache-aligned
│   ├── strategies/
│   │   ├── cross_exchange.c      # Main strategy (SIMD)
│   │   ├── funding_rate.c        # Futures arb
│   │   └── triangular.c          # Single-exchange arb
│   ├── execution/
│   │   ├── executor.c            # Order placement
│   │   └── order_manager.c       # Order tracking
│   ├── risk/
│   │   ├── risk_manager.c        # Limits, circuit breaker
│   │   └── position_tracker.c    # Position state
│   ├── ipc/
│   │   ├── shm.c                 # Shared memory (mmap)
│   │   └── socket.c              # Unix socket (commands)
│   └── utils/
│       ├── timestamp.c           # RDTSC timestamp
│       ├── memory_pool.c         # Pre-allocated pools
│       ├── logger.c              # Binary log
│       └── simd_helpers.c        # AVX2 utils
├── config/
│   ├── engine.json               # Main config
│   └── strategies.json           # Strategy params
└── CMakeLists.txt
```

---

## CORE OPTIMIZATIONS

### 1. RDTSC Timestamp (6x faster)
```c
static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return ((uint64_t)hi << 32) | lo;
}
// Latency: 5ns vs 30ns (clock_gettime)
```

### 2. Lock-Free SPSC Ring Buffer (2.5x faster)
```c
typedef struct __attribute__((aligned(64))) {
    volatile uint64_t head __attribute__((aligned(64)));
    volatile uint64_t tail __attribute__((aligned(64)));
    uint64_t capacity;
    Price items[0];
} SPSCRingBuffer;

// Push: NO locks, NO CAS!
static inline int spsc_push(SPSCRingBuffer *buf, const Price *item) {
    uint64_t head = buf->head;
    uint64_t next_head = (head + 1) % buf->capacity;
    uint64_t tail = __atomic_load_n(&buf->tail, __ATOMIC_ACQUIRE);
    if (next_head == tail) return 0;
    buf->items[head] = *item;
    __atomic_store_n(&buf->head, next_head, __ATOMIC_RELEASE);
    return 1;
}
// Latency: 20ns vs 50ns (mutex)
```

### 3. SIMD Price Comparison (5x faster)
```c
#include <immintrin.h>

void detect_arbitrage_simd_batch(
    const double *prices_ex1,
    const double *prices_ex2,
    double min_spread,
    uint8_t *results)
{
    __m256d ex1 = _mm256_loadu_pd(prices_ex1);
    __m256d ex2 = _mm256_loadu_pd(prices_ex2);
    __m256d diff = _mm256_sub_pd(ex1, ex2);
    __m256d abs_diff = _mm256_andnot_pd(_mm256_set1_pd(-0.0), diff);
    __m256d avg = _mm256_mul_pd(_mm256_add_pd(ex1, ex2), _mm256_set1_pd(0.5));
    __m256d spread_pct = _mm256_div_pd(abs_diff, avg);
    __m256d threshold = _mm256_set1_pd(min_spread / 10000.0);
    __m256d mask = _mm256_cmp_pd(spread_pct, threshold, _CMP_GT_OQ);
    int result_mask = _mm256_movemask_pd(mask);
    results[0] = (result_mask & 1) ? 1 : 0;
    results[1] = (result_mask & 2) ? 1 : 0;
    results[2] = (result_mask & 4) ? 1 : 0;
    results[3] = (result_mask & 8) ? 1 : 0;
}
// Latency: 5ns for 4 comparisons vs 25ns (scalar)
```

### 4. Memory Pool (10x faster)
```c
typedef struct {
    void *pool;
    size_t block_size;
    size_t block_count;
    uint32_t *free_bitmap;
} MemoryPool;

static inline void* mempool_alloc(MemoryPool *mp) {
    // Bitmap-based fast allocation
    // Latency: 15ns vs 200ns (malloc)
}
```

### 5. io_uring (5x faster)
```c
#include <liburing.h>

typedef struct {
    struct io_uring ring;
    int socket_fd;
    char *recv_buffers[256];  // Pre-allocated
    size_t buffer_size;
} UringSocket;

// Setup with SQPOLL (kernel polling thread)
int uring_socket_init(UringSocket *us, int socket_fd) {
    us->socket_fd = socket_fd;
    us->buffer_size = 65536;
    
    for (uint32_t i = 0; i < 256; i++) {
        us->recv_buffers[i] = aligned_alloc(4096, us->buffer_size);
    }
    
    struct io_uring_params params = {0};
    params.flags = IORING_SETUP_SQPOLL;  // Kernel polling
    params.sq_thread_idle = 1000;
    
    int ret = io_uring_queue_init_params(256, &us->ring, &params);
    return ret;
}

// Submit recv (non-blocking)
void uring_socket_recv_async(UringSocket *us, uint32_t buffer_idx) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(&us->ring);
    io_uring_prep_recv(sqe, us->socket_fd,
                       us->recv_buffers[buffer_idx],
                       us->buffer_size, 0);
    io_uring_sqe_set_data(sqe, (void*)(uintptr_t)buffer_idx);
    io_uring_submit(&us->ring);
}

// Poll (NO syscall if nothing ready!)
int uring_socket_poll(UringSocket *us, char **data_out, size_t *len_out) {
    struct io_uring_cqe *cqe;
    int ret = io_uring_peek_cqe(&us->ring, &cqe);
    if (ret < 0) return 0;
    
    uint32_t buffer_idx = (uint32_t)(uintptr_t)io_uring_cqe_get_data(cqe);
    *data_out = us->recv_buffers[buffer_idx];
    *len_out = cqe->res;
    
    io_uring_cqe_seen(&us->ring, cqe);
    uring_socket_recv_async(us, buffer_idx);  // Re-submit
    return 1;
}
// Latency: 5μs vs 25μs (epoll)
```

---

## ADDITIONAL CORE COMPONENTS

### 6. WebSocket Protocol
```c
typedef struct {
    int socket_fd;
    char url[256];
    bool is_connected;
    uint64_t last_ping_tsc;
    uint64_t reconnect_backoff_ms;
} WebSocketConnection;

// Custom minimal parser (no libwebsockets overhead for hot path)
typedef enum {
    WS_FRAME_TEXT = 0x1,
    WS_FRAME_BINARY = 0x2,
    WS_FRAME_PING = 0x9,
    WS_FRAME_PONG = 0xA
} WSFrameType;

typedef struct {
    WSFrameType type;
    uint64_t payload_len;
    char *payload;
} WSFrame;

// Parse WebSocket frame (zero-copy)
int ws_parse_frame(const char *data, size_t len, WSFrame *frame) {
    if (len < 2) return -1;
    
    uint8_t byte1 = data[0];
    uint8_t byte2 = data[1];
    
    frame->type = byte1 & 0x0F;
    bool masked = byte2 & 0x80;
    frame->payload_len = byte2 & 0x7F;
    
    size_t offset = 2;
    if (frame->payload_len == 126) {
        frame->payload_len = (data[2] << 8) | data[3];
        offset = 4;
    } else if (frame->payload_len == 127) {
        // 8-byte length (skip for simplicity)
        offset = 10;
    }
    
    if (masked) offset += 4;  // Skip mask
    frame->payload = (char*)(data + offset);
    
    return 0;
}

// Heartbeat (every 30s)
void ws_send_ping(WebSocketConnection *ws) {
    char frame[2] = {0x89, 0x00};  // PING frame, no payload
    send(ws->socket_fd, frame, 2, MSG_NOSIGNAL);
    ws->last_ping_tsc = rdtsc();
}

// Auto-reconnect with exponential backoff
void ws_reconnect(WebSocketConnection *ws) {
    close(ws->socket_fd);
    usleep(ws->reconnect_backoff_ms * 1000);
    
    // Reconnect logic...
    ws->socket_fd = socket(AF_INET, SOCK_STREAM, 0);
    // ...connect, handshake...
    
    ws->reconnect_backoff_ms = MIN(ws->reconnect_backoff_ms * 2, 60000);
    ws->is_connected = true;
}
```

### 7. Shared Memory IPC (Python ↔ C)
```c
// Shared memory layout (256MB)
typedef struct __attribute__((packed)) {
    // Control flags
    volatile bool engine_running;
    volatile bool strategy_enabled[3];  // cross_exchange, funding, triangular
    
    // Statistics (atomic updates)
    volatile uint64_t opportunities_detected;
    volatile uint64_t opportunities_executed;
    volatile uint64_t orders_placed;
    volatile uint64_t orders_filled;
    
    // Performance metrics
    volatile double total_profit_usd;
    volatile uint32_t avg_latency_us;
    volatile uint32_t p99_latency_us;
    
    // Latest opportunities (ring buffer)
    struct {
        char symbol[12];
        char exchange_buy[20];
        char exchange_sell[20];
        double spread_bps;
        double profit_usd;
        uint64_t detected_at_ns;
    } opportunities[1000];
    volatile uint32_t opportunities_head;
    
    // Latest prices (for monitoring)
    struct {
        char symbol[12];
        char exchange[20];
        double price;
        uint64_t timestamp_ns;
    } prices[100];
    volatile uint32_t prices_head;
    
} SharedMemory;

// C side: init
SharedMemory *shm_init_c(void) {
    int fd = shm_open("/draizer_v2", O_CREAT | O_RDWR, 0666);
    ftruncate(fd, sizeof(SharedMemory));
    SharedMemory *shm = mmap(NULL, sizeof(SharedMemory),
                             PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    memset(shm, 0, sizeof(SharedMemory));
    return shm;
}

// Python side: read
import mmap
import struct

def shm_init_python():
    fd = os.open("/dev/shm/draizer_v2", os.O_RDONLY)
    shm = mmap.mmap(fd, 256 * 1024 * 1024, access=mmap.ACCESS_READ)
    return shm

def read_stats(shm):
    # Parse struct (offset 0)
    engine_running = struct.unpack_from('?', shm, 0)[0]
    opps_detected = struct.unpack_from('Q', shm, 8)[0]
    opps_executed = struct.unpack_from('Q', shm, 16)[0]
    total_profit = struct.unpack_from('d', shm, 48)[0]
    # ...
    return {
        'engine_running': engine_running,
        'opportunities_detected': opps_detected,
        'opportunities_executed': opps_executed,
        'total_profit_usd': total_profit,
    }
```

### 8. Unix Domain Socket (Commands)
```c
// C side: command listener
typedef enum {
    CMD_START_STRATEGY,
    CMD_STOP_STRATEGY,
    CMD_UPDATE_CONFIG,
    CMD_SHUTDOWN
} CommandType;

typedef struct {
    CommandType type;
    char data[256];
} Command;

void *command_listener_thread(void *arg) {
    int server_fd = socket(AF_UNIX, SOCK_STREAM, 0);
    struct sockaddr_un addr = {0};
    addr.sun_family = AF_UNIX;
    strcpy(addr.sun_path, "/tmp/draizer_v2.sock");
    
    bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(server_fd, 5);
    
    while (1) {
        int client_fd = accept(server_fd, NULL, NULL);
        Command cmd;
        recv(client_fd, &cmd, sizeof(cmd), 0);
        
        switch (cmd.type) {
            case CMD_START_STRATEGY:
                // Enable strategy...
                break;
            case CMD_SHUTDOWN:
                // Graceful shutdown...
                return NULL;
        }
        close(client_fd);
    }
}

// Python side: send command
import socket
import struct

def send_command(cmd_type, data=""):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect("/tmp/draizer_v2.sock")
    
    cmd = struct.pack('I256s', cmd_type, data.encode())
    sock.send(cmd)
    sock.close()
```

### 9. Price Cache (Lock-Free Seqlock)
```c
typedef struct __attribute__((aligned(64))) {
    volatile uint32_t sequence;  // Even=stable, Odd=writing
    char symbol[12];
    char exchange[20];
    double bid;
    double ask;
    uint64_t timestamp_tsc;
    uint32_t padding[6];  // Pad to 64 bytes
} CachedPrice;

typedef struct {
    CachedPrice entries[1000];
    // Hash: symbol -> index
} PriceCache;

// Write (lock-free)
void price_cache_update(PriceCache *cache, int idx, const CachedPrice *price) {
    CachedPrice *entry = &cache->entries[idx];
    
    // Start write
    uint32_t seq = __atomic_load_n(&entry->sequence, __ATOMIC_RELAXED);
    __atomic_store_n(&entry->sequence, seq + 1, __ATOMIC_RELEASE);
    
    // Copy data
    memcpy((void*)&entry->symbol, price, sizeof(CachedPrice) - sizeof(uint32_t));
    
    // End write
    __atomic_store_n(&entry->sequence, seq + 2, __ATOMIC_RELEASE);
}

// Read (lock-free)
int price_cache_read(PriceCache *cache, int idx, CachedPrice *out) {
    CachedPrice *entry = &cache->entries[idx];
    uint32_t seq1, seq2;
    
    do {
        seq1 = __atomic_load_n(&entry->sequence, __ATOMIC_ACQUIRE);
        if (seq1 & 1) continue;  // Writing in progress
        
        memcpy(out, (void*)&entry->symbol, sizeof(CachedPrice) - sizeof(uint32_t));
        
        seq2 = __atomic_load_n(&entry->sequence, __ATOMIC_ACQUIRE);
    } while (seq1 != seq2);  // Retry if changed
    
    return 0;
}
```

### 10. Exchange Authentication
```c
// HMAC-SHA256 signature (Binance/MEXC)
#include <openssl/hmac.h>

void sign_request(const char *query, const char *secret, char *signature_out) {
    unsigned char digest[32];
    unsigned int digest_len;
    
    HMAC(EVP_sha256(), secret, strlen(secret),
         (unsigned char*)query, strlen(query),
         digest, &digest_len);
    
    // Convert to hex
    for (int i = 0; i < 32; i++) {
        sprintf(&signature_out[i*2], "%02x", digest[i]);
    }
}

// Build authenticated WebSocket URL
void build_ws_auth_url(const char *api_key, const char *secret, char *url_out) {
    long timestamp = time(NULL) * 1000;
    char query[256];
    sprintf(query, "timestamp=%ld", timestamp);
    
    char signature[65];
    sign_request(query, secret, signature);
    
    sprintf(url_out, "wss://ws-api.binance.com/ws-api/v3?%s&signature=%s",
            query, signature);
}
```

### 11. Binary Logger (High-Speed)
```c
typedef enum {
    LOG_PRICE_UPDATE,
    LOG_OPPORTUNITY_DETECTED,
    LOG_ORDER_PLACED,
    LOG_ORDER_FILLED,
    LOG_ERROR
} LogEventType;

typedef struct __attribute__((packed)) {
    uint64_t timestamp_ns;
    LogEventType type;
    uint32_t data_len;
    char data[0];  // Flexible
} LogEntry;

typedef struct {
    int fd;
    char *buffer;
    size_t buffer_size;
    size_t buffer_used;
    pthread_mutex_t lock;
} BinaryLogger;

// Async write (buffered)
void log_event(BinaryLogger *logger, LogEventType type, const void *data, size_t len) {
    pthread_mutex_lock(&logger->lock);
    
    if (logger->buffer_used + sizeof(LogEntry) + len > logger->buffer_size) {
        // Flush
        write(logger->fd, logger->buffer, logger->buffer_used);
        logger->buffer_used = 0;
    }
    
    LogEntry *entry = (LogEntry*)(logger->buffer + logger->buffer_used);
    entry->timestamp_ns = tsc_to_ns(rdtsc());
    entry->type = type;
    entry->data_len = len;
    memcpy(entry->data, data, len);
    
    logger->buffer_used += sizeof(LogEntry) + len;
    
    pthread_mutex_unlock(&logger->lock);
}

// Background flush thread
void *logger_flush_thread(void *arg) {
    BinaryLogger *logger = arg;
    while (1) {
        sleep(1);
        pthread_mutex_lock(&logger->lock);
        if (logger->buffer_used > 0) {
            write(logger->fd, logger->buffer, logger->buffer_used);
            logger->buffer_used = 0;
        }
        pthread_mutex_unlock(&logger->lock);
    }
}
```

---

### 12. JSON Parsing (Minimal Overhead)
```c
// Use yyjson (faster than jansson for hot path)
#include "yyjson.h"

// Parse price update (zero-copy where possible)
int parse_price_update(const char *json, size_t len, Price *price_out) {
    yyjson_doc *doc = yyjson_read(json, len, 0);
    if (!doc) return -1;
    
    yyjson_val *root = yyjson_doc_get_root(doc);
    yyjson_val *symbol = yyjson_obj_get(root, "s");
    yyjson_val *price = yyjson_obj_get(root, "p");
    yyjson_val *qty = yyjson_obj_get(root, "q");
    
    if (symbol && price && qty) {
        strncpy(price_out->symbol, yyjson_get_str(symbol), 11);
        price_out->price = yyjson_get_real(price);
        price_out->quantity = yyjson_get_real(qty);
        price_out->timestamp_tsc = rdtsc();
        
        yyjson_doc_free(doc);
        return 0;
    }
    
    yyjson_doc_free(doc);
    return -1;
}
// Latency: ~2μs (yyjson) vs ~8μs (jansson)

// Alternative: simdjson for even faster parsing (requires C++)
// Latency: ~0.5μs but adds C++ dependency
```

### 13. Error Handling & Recovery
```c
typedef enum {
    ERR_OK = 0,
    ERR_NETWORK_TIMEOUT,
    ERR_PARSE_FAILED,
    ERR_INVALID_PRICE,
    ERR_RISK_REJECTED,
    ERR_EXCHANGE_ERROR,
    ERR_ORDER_FAILED
} ErrorCode;

typedef struct {
    ErrorCode code;
    char message[256];
    uint64_t timestamp_tsc;
} Error;

// Error handling with retry
int execute_with_retry(int (*func)(void*), void *arg, int max_retries) {
    int retries = 0;
    int result;
    
    while (retries < max_retries) {
        result = func(arg);
        if (result == 0) return 0;  // Success
        
        // Exponential backoff
        usleep((1 << retries) * 1000);  // 1ms, 2ms, 4ms, 8ms...
        retries++;
    }
    
    return -1;  // Failed after retries
}

// Circuit breaker pattern
typedef struct {
    int failure_count;
    int failure_threshold;
    uint64_t last_failure_tsc;
    uint64_t cooldown_duration_ns;
    bool is_open;
} CircuitBreaker;

int circuit_breaker_check(CircuitBreaker *cb) {
    if (cb->is_open) {
        uint64_t now = rdtsc();
        if (tsc_to_ns(now - cb->last_failure_tsc) > cb->cooldown_duration_ns) {
            // Try to close
            cb->is_open = false;
            cb->failure_count = 0;
            return 1;  // Allow attempt
        }
        return 0;  // Still open
    }
    return 1;  // Closed, allow
}

void circuit_breaker_record_failure(CircuitBreaker *cb) {
    cb->failure_count++;
    cb->last_failure_tsc = rdtsc();
    
    if (cb->failure_count >= cb->failure_threshold) {
        cb->is_open = true;
        printf("⚠️  Circuit breaker OPENED (failures: %d)\n", cb->failure_count);
    }
}

void circuit_breaker_record_success(CircuitBreaker *cb) {
    cb->failure_count = 0;
}
```

---

## LATENCY BREAKDOWN

```
Network (io_uring):         5μs
WebSocket parse:            0.2μs
JSON parse (yyjson):        2μs
Data pipeline (SPSC):       0.05μs
Detection (SIMD):           0.5μs
Risk checks (inline):       0.13μs
Order build/send:           1.5μs
Network RTT (exchange):     20μs
Fill processing:            1μs
───────────────────────────────
TOTAL:                      30μs (P50)
                            85μs (P99)
```

---

## STRATEGIES

### 1. Cross-Exchange Arbitrage (Primary)
**Concept:** Buy on Exchange A, sell on Exchange B when spread > fees

**Config:**
```json
{
  "min_spread_bps": 75,
  "min_profit_usd": 0.50,
  "max_position_usd": 500,
  "max_price_age_ms": 100
}
```

**Execution:**
```c
if (spread > 0.75% && profit > $0.50 && liquidity_ok) {
    place_order(exchange_a, BUY, quantity);
    place_order(exchange_b, SELL, quantity);
}
```

### 2. Funding Rate Arbitrage
**Concept:** Collect funding payments on futures by hedging with spot

**Config:**
```json
{
  "min_funding_rate": 0.03,
  "hedge_enabled": true,
  "capital_allocation": 0.3
}
```

### 3. Triangular Arbitrage
**Concept:** BTC→ETH→USDT→BTC cycle profit

**Config:**
```json
{
  "min_profit_bps": 15,
  "cycles": [
    ["BTC/USDT", "ETH/USDT", "ETH/BTC"]
  ]
}
```

---

## RISK MANAGEMENT

```c
typedef struct {
    double max_position_usd;        // 500
    double max_daily_loss_usd;      // 50
    double max_concurrent;          // 5
    double circuit_breaker_loss;    // 20 in 5min
    bool circuit_breaker_active;
} RiskManager;

// Inline checks (~130ns total)
if (position_usd > risk->max_position_usd) return REJECT;
if (daily_loss > risk->max_daily_loss_usd) return REJECT;
if (concurrent_pos >= risk->max_concurrent) return REJECT;
if (risk->circuit_breaker_active) return REJECT;
```

---

## REALISTIC PROJECTIONS

### Market Reality (2025)
- **BTC spread:** 0.05-0.15% (was 0.5-2% in 2021)
- **Fees total:** 0.65% per round-trip (buy 0.1% + sell 0.2% + withdrawal 0.3% + slippage 0.05%)
- **Min profitable spread:** 0.75%
- **Opportunities/day:** ~30 (spread >= 0.75%, top 30 pairs)
- **Success rate:** 50% (price moves, partial fills, API errors)

### Income Projections

**Capital: $1,000 (testing)**
- Opportunities: 30/day × 50% success = 15 trades
- Profit per trade: $1,000 × 0.20% = $2
- Daily: $30
- Monthly: $900 (15% monthly ROI)
- **Use case:** Proof of concept

**Capital: $10,000 (realistic)**
- Opportunities: 30/day × 50% success = 15 trades
- Profit per trade: $10,000 × 0.20% = $20
- Daily: $300 × 50% uptime = $150/day
- Monthly: $4,500 - $200 (costs) = **$4,300**
- **Annual:** ~$50,000 (500% APY)

**Risk factors:**
- Market efficiency increases (more bots)
- Exchange API changes/limits
- Regulatory changes
- Capital at risk (bugs, hacks)

---

## COSTS

### Development (5 months)
- AI subscription: $100
- VPS: $50
- **Total:** $150

### Production (monthly)
- VPS: $30-40
- Monitoring: $5
- Taxes (ИП/самозанятый): $100-200
- **Total:** $135-245/month

### Capital (one-time)
- Testing: $1,000 (returnable)
- Production: $10,000 (returnable)

**Break-even:** 1-2 months after launch

---

## IMPLEMENTATION ROADMAP

### Phase 1: Foundation (4 weeks)
- [ ] Project structure, build system
- [ ] RDTSC timestamp
- [ ] Memory pool allocator
- [ ] SPSC ring buffer
- [ ] Unit tests

### Phase 2: Networking (4 weeks)
- [ ] io_uring wrapper
- [ ] WebSocket manager
- [ ] Binance/MEXC connections
- [ ] Price cache
- [ ] End-to-end price flow

### Phase 3: Detection (3 weeks)
- [ ] Cross-exchange detection (scalar)
- [ ] SIMD optimization (AVX2)
- [ ] Risk manager
- [ ] Opportunity queue
- [ ] Detection benchmarks

### Phase 4: Execution (3 weeks)
- [ ] Order placement (WebSocket)
- [ ] Order tracking
- [ ] Fill monitoring
- [ ] Failure recovery
- [ ] Full cycle test

### Phase 5: Integration (2 weeks)
- [ ] Shared memory IPC
- [ ] Python bridge
- [ ] FastAPI endpoints
- [ ] Frontend updates
- [ ] Production deployment

**Total:** 16 weeks (~4 months)

---

## DEPENDENCIES

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    build-essential cmake \
    liburing-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libyyjson-dev

# Or compile yyjson from source (faster)
git clone https://github.com/ibireme/yyjson.git
cd yyjson && mkdir build && cd build
cmake .. && make && sudo make install
```

---

## COMPILER FLAGS

```makefile
CC = gcc
CFLAGS = -O3 -march=native -mtune=native \
         -flto -ffast-math -funroll-loops \
         -mavx2 -mfma \
         -fprofile-use -fprofile-correction \
         -DNDEBUG
LDFLAGS = -flto -Wl,-O3 -Wl,--strip-all
LIBS = -luring -lcurl -lyyjson -lssl -lcrypto -lpthread -lm
```

---

## CONFIGURATION FILES

### config/engine.json
```json
{
  "version": "2.0.0",
  "mode": "live",
  "capital_usd": 10000,
  "exchanges": [
    {
      "name": "binance",
      "ws_url": "wss://stream.binance.com:9443/ws",
      "api_url": "https://api.binance.com",
      "api_key": "${BINANCE_API_KEY}",
      "api_secret": "${BINANCE_API_SECRET}"
    },
    {
      "name": "mexc",
      "ws_url": "wss://wbs.mexc.com/ws",
      "api_url": "https://api.mexc.com",
      "api_key": "${MEXC_API_KEY}",
      "api_secret": "${MEXC_API_SECRET}"
    }
  ],
  "symbols": [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
    "ADAUSDT", "DOGEUSDT", "XRPUSDT", "DOTUSDT"
  ],
  "risk": {
    "max_position_usd": 500,
    "max_daily_loss_usd": 50,
    "max_concurrent_positions": 5,
    "circuit_breaker_loss_usd": 20,
    "circuit_breaker_window_sec": 300
  },
  "performance": {
    "cpu_affinity": [0, 1],
    "rt_priority": 99,
    "use_huge_pages": true
  },
  "logging": {
    "level": "info",
    "binary_log_path": "/var/log/draizer/engine.bin",
    "text_log_path": "/var/log/draizer/engine.log",
    "flush_interval_sec": 1
  }
}
```

### config/strategies.json
```json
{
  "strategies": [
    {
      "name": "cross_exchange",
      "enabled": true,
      "params": {
        "min_spread_bps": 75,
        "min_profit_usd": 0.50,
        "max_position_usd": 500,
        "max_price_age_ms": 100,
        "capital_allocation": 0.50
      }
    },
    {
      "name": "funding_rate",
      "enabled": true,
      "params": {
        "min_funding_rate": 0.03,
        "hedge_enabled": true,
        "capital_allocation": 0.30,
        "check_interval_sec": 60
      }
    },
    {
      "name": "triangular",
      "enabled": false,
      "params": {
        "min_profit_bps": 15,
        "cycles": [
          ["BTCUSDT", "ETHUSDT", "ETHBTC"],
          ["BTCUSDT", "BNBUSDT", "BNBBTC"]
        ],
        "capital_allocation": 0.20
      }
    }
  ]
}
```

---

## SYSTEM TUNING

```bash
# Network
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.ipv4.tcp_nodelay=1

# CPU
sudo cpupower frequency-set -g performance

# Huge pages
echo 1024 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# RT priority (optional)
sudo sysctl -w kernel.sched_rt_runtime_us=-1
```

---

## TESTING

### Unit Tests
```bash
make test
./tests/test_spsc_ring
./tests/test_timestamp
./tests/test_simd
```

### Benchmarks
```bash
make benchmark
./benchmarks/bench_timestamp  # Expect: <10ns
./benchmarks/bench_spsc       # Expect: <50ns
./benchmarks/bench_simd       # Expect: <10ns/4prices
```

### Integration
```bash
# Paper trading (1 week)
./c_engine --mode paper --capital 1000

# Live trading (small)
./c_engine --mode live --capital 1000

# Scale up
./c_engine --mode live --capital 10000
```

---

## MONITORING

```python
# backend/app/services/c_engine_bridge.py
class CEngineBridge:
    def get_stats(self):
        # Read from shared memory
        return {
            'opportunities_detected': int,
            'opportunities_executed': int,
            'total_profit_usd': float,
            'avg_latency_us': float,
            'p99_latency_us': float,
        }
```

---

## DECISION MATRIX

**Start with $1k if:**
- ✅ Want proof of concept first
- ✅ Can wait 2-3 months for scale
- ⚠️ Income: $900/month

**Start with $10k if:**
- ✅ Have capital available
- ✅ Want realistic income immediately
- ✅ Income: $4,000-5,000/month

**Don't build if:**
- ❌ No capital available
- ❌ Need income <4 months
- ❌ Risk-averse (capital at risk)
- ❌ Have better alternatives

---

## NEXT STEPS

1. **Validate with existing V1 infrastructure:**
   - Use current Docker setup
   - Keep PostgreSQL, Redis
   - Reuse auth, frontend
   - Add C engine alongside

2. **Start minimal:**
   - Single strategy (cross-exchange)
   - 2 exchanges (Binance, MEXC)
   - $1k capital (testing)
   - Hetzner CX21 ($6.50/month)

3. **Scale incrementally:**
   - Week 1-4: Foundation works
   - Week 5-8: Network + detection
   - Week 9-12: Execution + testing
   - Week 13-16: Production + monitoring
   - Week 17+: Scale capital if profitable

**Ready to start?** → Begin with Phase 1 (Foundation)

---

**End of Technical Spec**

