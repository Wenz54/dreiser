# DRAIZER V2.0 - C Trading Engine

Ultra-low latency arbitrage trading engine written in pure C.

## Features

- ⚡ **Ultra-fast:** <30μs detection latency (P50), <85μs (P99)
- 🔒 **Lock-free:** SPSC ring buffers, seqlock price cache
- 🚀 **SIMD optimized:** AVX2 parallel price comparison
- 📡 **io_uring:** Zero-copy async networking (Linux 5.1+)
- 🎯 **Multiple strategies:** Cross-exchange, funding rate, triangular arbitrage
- 🛡️ **Risk management:** Position limits, circuit breakers, daily loss limits

## Architecture

```
Main Thread (Event Loop)
├─ WebSocket connections (Binance, MEXC)
├─ Price updates → SPSC buffer
└─ Strategy detection (SIMD)

Worker Threads
├─ Order execution (async)
├─ IPC server (commands from Python)
└─ Logger (binary + text)

Shared Memory
└─ Stats, opportunities, prices → Python backend
```

## Build

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    build-essential cmake \
    liburing-dev \
    libcurl4-openssl-dev \
    libssl-dev

# yyjson (fast JSON parser)
git clone https://github.com/ibireme/yyjson.git
cd yyjson && mkdir build && cd build
cmake .. && make && sudo make install
```

### Compile

```bash
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
```

### Run

```bash
# Paper trading (safe, no real money)
./draizer_engine --mode paper --capital 1000

# Live trading (real execution)
./draizer_engine --mode live --capital 10000 --config ../config/engine.json
```

## Configuration

Edit `config/engine.json`:
- `mode`: "paper" or "live"
- `capital_usd`: Trading capital
- `symbols`: Pairs to monitor
- `risk`: Position limits, circuit breaker

Edit `config/strategies.json`:
- Enable/disable strategies
- Adjust parameters (min spread, min profit, etc.)

## Testing

```bash
# Unit tests
make test

# Benchmarks
make benchmark
./benchmarks/bench_timestamp  # Should be <10ns
./benchmarks/bench_spsc       # Should be <50ns
./benchmarks/bench_simd       # Should be <10ns for 4 prices
```

## Performance Targets

- **Latency (P50):** <30μs
- **Latency (P99):** <85μs
- **Throughput:** 100k+ price updates/sec
- **Memory:** <256MB
- **CPU:** <30% (2 cores)

## Current Status

**Version:** 2.0.0-alpha  
**Status:** 🚧 Under construction

### Completed
- ✅ Project structure
- ✅ Build system (CMake)
- ✅ Main entry point
- ✅ Configuration files

### In Progress
- 🚧 Network layer (io_uring, WebSocket)
- 🚧 Data structures (SPSC, price cache)
- 🚧 Strategy detection (SIMD)

### Todo
- ⏳ Order execution
- ⏳ Risk management
- ⏳ IPC (Python bridge)
- ⏳ Logging
- ⏳ Tests & benchmarks

## Development Roadmap

- **Week 1-4:** Foundation (data structures, timestamp, memory pools)
- **Week 5-8:** Networking (io_uring, WebSocket, exchanges)
- **Week 9-11:** Detection (strategies, SIMD optimization)
- **Week 12-14:** Execution (order placement, tracking, recovery)
- **Week 15-16:** Integration (Python bridge, testing, deployment)

## License

Proprietary - Internal use only

## Author

Developed with AI assistance for ultra-low latency crypto arbitrage.


