# 🚀 DRAIZER V2.0 - UBUNTU SERVER DEPLOYMENT GUIDE

## Bitfinex (SPOT) + Deribit (FUTURES) | Ping: 0.8ms

---

## 📋 СИСТЕМА

**Рекомендуемая ОС:** Ubuntu Server 22.04 LTS
**Тип:** Bare-metal (без Docker для минимальной latency)
**CPU:** Минимум 4 cores, рекомендуется 8+
**RAM:** Минимум 8GB
**Network:** Прямое подключение к интернету, без NAT (для минимального пинга)

---

## 🔧 УСТАНОВКА ЗАВИСИМОСТЕЙ

```bash
# 1. Обновление системы
sudo apt update && sudo apt upgrade -y

# 2. Real-Time Kernel (КРИТИЧНО ДЛЯ HFT!)
sudo apt install linux-image-rt-amd64 -y
sudo reboot

# После перезагрузки проверить:
uname -a  # Должно быть: "PREEMPT_RT"

# 3. Компиляторы и библиотеки
sudo apt install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    pkg-config \
    wget \
    procps \
    cpufrequtils \
    linux-tools-common \
    linux-tools-generic

# 4. yyjson (JSON parser)
cd /tmp
git clone https://github.com/ibireme/yyjson.git
cd yyjson
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig

# 5. PostgreSQL + Redis (для Python backend)
sudo apt install -y postgresql redis-server python3-pip python3-venv

# 6. Python зависимости
cd /path/to/draizer/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ⚡ ОПТИМИЗАЦИЯ СИСТЕМЫ ДЛЯ HFT

### 1. CPU Isolation (изолировать ядра 2-7 для trading)

```bash
sudo nano /etc/default/grub

# Добавить в GRUB_CMDLINE_LINUX:
GRUB_CMDLINE_LINUX="isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7"

sudo update-grub
sudo reboot
```

### 2. CPU Governor (максимальная производительность)

```bash
sudo cpupower frequency-set -g performance

# Проверить:
cpupower frequency-info
```

### 3. Disable Turbo Boost (стабильная частота)

```bash
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
```

### 4. Huge Pages (для price cache)

```bash
echo 2048 | sudo tee /proc/sys/vm/nr_hugepages

# Сделать постоянным:
echo "vm.nr_hugepages=2048" | sudo tee -a /etc/sysctl.conf
```

### 5. Network Tuning (минимальная latency)

```bash
# Disable interrupt coalescing
sudo ethtool -C eth0 rx-usecs 0 tx-usecs 0

# Increase ring buffer
sudo ethtool -G eth0 rx 4096 tx 4096

# Disable TCP timestamp
echo 0 | sudo tee /proc/sys/net/ipv4/tcp_timestamps
```

### 6. Disable IRQ Balance

```bash
sudo systemctl stop irqbalance
sudo systemctl disable irqbalance
```

---

## 🏗️ СБОРКА C-ENGINE

```bash
cd /path/to/draizer/backend/c_engine

# Clean build
rm -rf build
mkdir build && cd build

# Configure (Release build with all optimizations)
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build (parallel)
make -j$(nproc)

# Verify binary
ls -lh draizer_engine
file draizer_engine
```

---

## 🔐 API KEYS (ОПЦИОНАЛЬНО для публичных данных)

Для WebSocket orderbook streams **НЕ требуются** API ключи!
Bitfinex и Deribit предоставляют публичные WebSocket для orderbook.

Если захочешь добавить реальную торговлю (не paper trading):
1. Bitfinex: https://www.bitfinex.com/api
2. Deribit: https://www.deribit.com/account/BTC/settings/key_management

Добавь в `backend/c_engine/config/engine.json`:
```json
{
  "exchanges": {
    "bitfinex": {
      "api_key": "YOUR_KEY",
      "api_secret": "YOUR_SECRET"
    },
    "deribit": {
      "api_key": "YOUR_KEY",
      "api_secret": "YOUR_SECRET"
    }
  }
}
```

---

## 🚀 ЗАПУСК

### 1. Запуск C-Engine (с CPU pinning)

```bash
cd /path/to/draizer/backend/c_engine/build

# Pin to cores 2-7 (isolated cores)
sudo taskset -c 2-7 nice -n -20 ./draizer_engine --config ../config/engine.json
```

### 2. Запуск Python Backend (в другом терминале)

```bash
cd /path/to/draizer/backend
source venv/bin/activate

# Run migrations
alembic upgrade head

# Start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Запуск Frontend (в третьем терминале)

```bash
cd /path/to/draizer/frontend
npm install
npm run dev
```

---

## 📊 МОНИТОРИНГ PERFORMANCE

### CPU Affinity

```bash
# Проверить на каких ядрах работает C-engine
ps -eLo pid,tid,psr,comm | grep draizer
```

### Latency

```bash
# Смотреть логи C-engine в реальном времени
tail -f /path/to/draizer/backend/c_engine/engine.log | grep "LATENCY"
```

### Network Latency

```bash
# Проверить пинг к биржам
ping api-pub.bitfinex.com
ping www.deribit.com

# Ожидаемый результат: <5ms если сервер в Европе/США
```

---

## 🔥 ОЖИДАЕМАЯ ПРОИЗВОДИТЕЛЬНОСТЬ

| Метрика | Windows + Docker | Ubuntu Native | Ubuntu + RT Kernel + Tuning |
|---------|------------------|--------------|----------------------------|
| **Latency (Exchange→Us)** | 500-800 ms | 100-300 ms | **5-50 ms** |
| **Jitter** | ±200 ms | ±50 ms | **±2 ms** |
| **Detection time** | ~50 μs | ~20 μs | **~7 μs** |
| **Orders/sec capacity** | ~100 | ~1,000 | **~10,000+** |

---

## ✅ ПРОВЕРКА РАБОТЫ

### 1. C-Engine логи

Должны видеть:
```
✅ Bitfinex: Connected to wss://api-pub.bitfinex.com/ws/2
✅ Deribit: Connected to wss://www.deribit.com/ws/api/v2
📡 Bitfinex: Subscribed to 9 orderbooks
📡 Deribit: Subscribed to 9 perpetual futures orderbooks
⏱️  BITFINEX BTCUSD: bid=112735.84, ask=112735.85 | Inter-arrival: 25 ms
⏱️  DERIBIT BTC-PERPETUAL: bid=112738.00, ask=112738.10 | LATENCY: 8 ms | Funding: 0.0125%
🎯 SPOT-FUTURES OPPORTUNITY: BTCUSD | Spread: 22.5 bps | Net: 9.75 bps | Type: TARGET
```

### 2. Frontend Dashboard

Откройте http://YOUR_SERVER_IP:3000

Должны видеть:
- **Live Prices**: Bitfinex (spot) и Deribit (futures)
- **Opportunities Detected**: > 0
- **Spread Quality**: MIN/TARGET/FAT распределение
- **Latency Graph**: < 50ms average

---

## 🐛 TROUBLESHOOTING

### Problem: "No data from exchanges"

```bash
# Проверить firewall
sudo ufw status
sudo ufw allow 8000/tcp  # FastAPI
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 443/tcp   # WSS

# Проверить DNS
nslookup api-pub.bitfinex.com
nslookup www.deribit.com
```

### Problem: "High latency (>100ms)"

```bash
# Проверить что RT kernel активен
uname -a | grep PREEMPT_RT

# Проверить CPU governor
cpupower frequency-info | grep "current policy"
# Должно быть: "performance"

# Проверить CPU affinity
ps -eLo pid,psr,comm | grep draizer
# Должно показывать cores 2-7
```

### Problem: "No opportunities detected"

Это НОРМАЛЬНО если:
1. Спред между Bitfinex spot и Deribit futures < 10 bps
2. Funding rate слишком высокий (>0.10%)
3. Рынок очень эффективен (BTC, ETH обычно tight spreads)

Попробуй:
- Снизить `min_spread_bps` в `engine.json` (но будешь терять на fees!)
- Добавить больше пар (SOL, MATIC, DOT имеют wider spreads)
- Дождаться волатильности (funding rate spike, news events)

---

## 📈 NEXT STEPS

1. ✅ Deploy на Ubuntu Server с RT kernel
2. ✅ Запустить C-engine + Python backend
3. ✅ Мониторить latency (target: <50ms)
4. 🔄 Собирать orderbook data для backtesting
5. 🔄 Implement полноценный statistical arbitrage (приоритет 2)
6. 🔄 Добавить real trading (сейчас paper trading)

---

## 🆘 SUPPORT

Если что-то не работает - присылай логи:
```bash
# C-engine logs
cat /path/to/draizer/backend/c_engine/engine.log

# Python backend logs
journalctl -u draizer-backend -n 100

# System info
uname -a
cpupower frequency-info
ethtool eth0
```

Удачи! 🚀

