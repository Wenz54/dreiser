# 🚀 DRAIZER V2 - BUILD & RUN GUIDE

## 📦 **PREREQUISITES**

```bash
# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# Required packages:
# - gcc (11+)
# - cmake (3.10+)
# - pthread
# - librt (for shared memory)
```

---

## 🔨 **BUILD**

### Method 1: CMake (Recommended)

```bash
cd backend/c_engine

# Create build directory
mkdir -p build
cd build

# Configure
cmake ..

# Compile
make -j$(nproc)

# Result: build/draizer_engine
```

### Method 2: Makefile

```bash
cd backend/c_engine

# Clean + build
make clean
make -j$(nproc)

# Result: build/draizer_engine
```

---

## ▶️ **RUN**

### Basic Usage

```bash
# From build directory:
./draizer_engine

# With options:
./draizer_engine -p 1 -c ../config/engine.json
```

### Options

```
-c <path>   Config file path (default: ../config/engine.json)
-p <0|1>    Paper mode: 1=paper, 0=live (default: 1)
-h          Help
```

### Example Output

```
╔══════════════════════════════════════════╗
║   DRAIZER V2.0 - TRADING ENGINE          ║
║   Ultra-Fast Quantitative Arbitrage      ║
╚══════════════════════════════════════════╝

📋 Configuration loaded (default)
   Mode: Paper
   Capital: $1000.00

⚙️  Initializing components...
✓ RDTSC calibrated: 2.800 cycles/ns (2.80 GHz)
   ✓ Price cache: Ready
   ✓ Price feed buffer: Ready (4096 slots)
   ✓ Cross-Exchange Strategy: Loaded
   ✓ Risk Manager: Active ($1000.00)
   ✓ IPC: Shared memory mapped (/draizer_v2)

🚀 Trading engine started!

📡 Price simulator started
💰 OPPORTUNITY: BTCUSDT | Buy @67012.34 (binance) → Sell @67045.67 (mexc) | 
   Spread: 49.70 bps | Profit: $2.34
   ✅ EXECUTED!

⏱️  Heartbeat #10 | Opps: 3 detected, 2 executed | 
   Balance: $1004.68 | Latency: 45 μs
```

---

## 🔍 **MONITORING**

### From Python

```python
from app.services.c_engine_bridge import CEngineBridge

bridge = CEngineBridge()
if bridge.connect():
    stats = bridge.get_stats()
    print(f"Opportunities detected: {stats['opportunities_detected']}")
    print(f"Profit: ${stats['total_profit_usd']:.2f}")
    print(f"Latency P99: {stats['p99_latency_us']}μs")
```

### Shared Memory Direct Access

```bash
# Check if running
ls -l /dev/shm/draizer_v2

# Size
du -h /dev/shm/draizer_v2
```

---

## 🐛 **TROUBLESHOOTING**

### Build Errors

**Error:** `fatal error: pthread.h: No such file or directory`
```bash
sudo apt-get install build-essential
```

**Error:** `undefined reference to 'shm_open'`
```bash
# Add -lrt to linker flags (already in CMakeLists.txt)
```

**Error:** `undefined reference to 'rdtsc'`
```bash
# RDTSC is x86-64 only. Make sure you're on Intel/AMD CPU.
uname -m  # Should show x86_64
```

### Runtime Errors

**Error:** `Failed to create shared memory`
```bash
# Check permissions
sudo chmod 666 /dev/shm

# Or run with sudo (not recommended)
sudo ./draizer_engine
```

**Error:** `RDTSC calibrated: 0.000 cycles/ns`
```bash
# CPU doesn't support RDTSC or running in VM
# Fallback: use clock_gettime() instead
```

### Performance Issues

**Low latency (<100μs expected):**
```bash
# Check CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Should be "performance", not "powersave"
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

**High latency (>1ms):**
- Disable hyperthreading
- Pin to dedicated CPU core
- Enable huge pages
- Check for other processes (top/htop)

---

## ⚡ **PERFORMANCE TUNING**

### CPU Pinning

```bash
# Run on CPU 0 only
taskset -c 0 ./draizer_engine
```

### Huge Pages

```bash
# Enable huge pages (2MB)
echo 512 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Verify
cat /proc/meminfo | grep Huge
```

### Real-Time Priority

```bash
# Run with RT priority (requires root)
sudo chrt -f 99 ./draizer_engine
```

### Complete Performance Command

```bash
# Ultimate performance setup
sudo sh -c "echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
sudo sh -c "echo 512 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages"
sudo taskset -c 0 chrt -f 99 ./draizer_engine
```

---

## 📊 **BENCHMARKING**

### Latency Test

```bash
# TODO: Add benchmark tool
./draizer_engine_benchmark --latency

# Expected results:
# - Timestamp: 5ns
# - SPSC push/pop: 20ns
# - Price cache update: 30ns
# - Arbitrage detection: 500ns (with SIMD)
# - Total loop: <30μs
```

### Throughput Test

```bash
./draizer_engine_benchmark --throughput

# Expected results:
# - Price updates: 500,000/sec
# - Opportunity checks: 100,000/sec
# - Order placements: 10,000/sec
```

---

## 🔄 **DEVELOPMENT WORKFLOW**

### Quick Rebuild

```bash
# From project root
cd backend/c_engine/build
make -j$(nproc) && ./draizer_engine
```

### Hot Reload Config

```python
# From Python
bridge.update_config({'min_spread_bps': 80})
```

### Clean Rebuild

```bash
cd backend/c_engine
make clean
make -j$(nproc)
```

---

## ✅ **CHECKLIST**

Before running in production:

- [ ] All unit tests pass
- [ ] Latency <100μs (P99)
- [ ] Memory leaks checked (valgrind)
- [ ] Config validated
- [ ] Exchange API keys set
- [ ] Risk limits configured
- [ ] Monitoring enabled
- [ ] Backup strategy in place

---

**Status:** ✅ Ready to build and test!  
**Last updated:** 2025-10-28


