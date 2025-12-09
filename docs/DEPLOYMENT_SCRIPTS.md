# 📦 DEPLOYMENT SCRIPTS - TECHNICAL DOCUMENTATION

## 🎯 Обзор

Этот документ описывает архитектуру deployment scripts для Draizer V2.0.

---

## 📁 Структура файлов

```
draizer/
├── deploy.sh           # Ubuntu production deployment
├── deploy.ps1          # Windows Docker deployment
├── quick-start.sh      # Ubuntu quick start (after deploy)
├── quick-start.ps1     # Windows quick start (after deploy)
├── stop.sh             # Ubuntu service stop
└── QUICKSTART.md       # User-facing documentation
```

---

## 🐧 UBUNTU DEPLOYMENT (`deploy.sh`)

### **Что делает:**

1. **System Check:**
   - Проверяет OS (Ubuntu 22.04 рекомендуется)
   - Проверяет RT kernel (опционально, но рекомендуется)
   - Проверяет CPU cores (минимум 4, рекомендуется 8+)
   - Проверяет RAM (минимум 8GB)
   - Проверяет disk space (минимум 10GB)

2. **Dependency Installation:**
   - `build-essential` (gcc, make, etc.)
   - `cmake` (для сборки C-engine)
   - `libssl-dev` (SSL/TLS для WebSocket)
   - `postgresql` + `postgresql-contrib`
   - `redis-server`
   - `python3` + `python3-pip` + `python3-venv`
   - `nodejs` (18.x через nodesource)

3. **yyjson Installation:**
   - Клонирует https://github.com/ibireme/yyjson.git
   - Собирает из исходников (Release mode)
   - Устанавливает в `/usr/local/lib`
   - Обновляет `ldconfig`

4. **C-Engine Build:**
   - Чистит старый `build/` каталог
   - Запускает `cmake` (Release mode)
   - Компилирует с `make -j$(nproc)` (параллельная сборка)
   - Проверяет `draizer_engine` binary

5. **PostgreSQL Setup:**
   - Создает базу данных `draizer_db`
   - Создает пользователя `draizer_user` с случайным паролем
   - Генерирует `.env` файл с credentials
   - Генерирует `SECRET_KEY` и `ENCRYPTION_KEY`

6. **Python Backend Setup:**
   - Создает virtual environment (`venv/`)
   - Устанавливает dependencies из `requirements.txt`
   - Запускает Alembic migrations

7. **Frontend Setup:**
   - `npm install`
   - `npm run build` (production build)

8. **System Optimizations (optional):**
   - CPU Governor → `performance`
   - Turbo Boost → disabled (stable frequency)
   - Huge Pages → 2048 pages (4MB)
   - IRQ Balance → disabled (для CPU pinning)

9. **Systemd Services (optional):**
   - Создает `/etc/systemd/system/draizer-engine.service`
   - Создает `/etc/systemd/system/draizer-backend.service`
   - Включает `systemctl enable`

### **Использование:**

```bash
chmod +x deploy.sh
./deploy.sh
```

**Интерактивные prompts:**
- "Continue on non-Ubuntu OS?"
- "Apply CPU tuning?"
- "Create systemd services?"

**Время выполнения:** ~10-15 минут (первый раз)

---

## 🪟 WINDOWS DEPLOYMENT (`deploy.ps1`)

### **Что делает:**

1. **Docker Check:**
   - Проверяет `docker` command
   - Проверяет `docker-compose` command
   - Проверяет Docker daemon running
   - Проверяет disk space (минимум 10GB)

2. **Cleanup (optional):**
   - `docker-compose down`
   - `docker system prune -f`
   - `docker volume prune -f`

3. **Configuration:**
   - Создает `.env` файл если не существует
   - Генерирует случайные `SECRET_KEY`, `ENCRYPTION_KEY`
   - Предупреждает о необходимости добавить API keys

4. **Build:**
   - `docker-compose build --parallel`
   - Показывает прогресс сборки

5. **Start:**
   - `docker-compose up -d postgres redis`
   - `docker-compose exec backend alembic upgrade head`
   - `docker-compose up -d` (все сервисы)

6. **Verification:**
   - Ждет подключения C-Engine к биржам
   - Проверяет Backend availability (`http://localhost:8000/docs`)
   - Показывает статус контейнеров

### **Использование:**

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

**Интерактивные prompts:**
- "Run docker system prune?"
- "Open API docs in browser?"

**Время выполнения:** ~5-10 минут (первый раз)

---

## ⚡ QUICK START SCRIPTS

### **Ubuntu (`quick-start.sh`):**

Запускает уже развернутую систему.

**Что делает:**
1. Проверяет существование `draizer_engine` binary
2. Запускает PostgreSQL + Redis (`systemctl start`)
3. Запускает C-Engine в background с CPU pinning:
   ```bash
   nohup sudo taskset -c 2-7 nice -n -20 ./draizer_engine > /tmp/draizer_engine.log 2>&1 &
   ```
4. Запускает Python Backend в background:
   ```bash
   nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 > /tmp/draizer_backend.log 2>&1 &
   ```
5. Сохраняет PID в `/tmp/draizer_*.pid`

**Использование:**
```bash
./quick-start.sh
```

---

### **Windows (`quick-start.ps1`):**

Запускает Docker контейнеры.

**Что делает:**
1. Проверяет Docker daemon
2. `docker-compose up -d`
3. Ждет инициализации (5 секунд)
4. Показывает статус контейнеров

**Использование:**
```powershell
.\quick-start.ps1
```

---

## 🛑 STOP SCRIPT (`stop.sh`)

Останавливает все сервисы на Ubuntu.

**Что делает:**
1. Читает PID из `/tmp/draizer_engine.pid`
2. Отправляет `SIGTERM` → ждет 2 секунды → `SIGKILL` (если нужно)
3. Аналогично для Backend
4. Удаляет shared memory `/dev/shm/draizer_v2`
5. Удаляет PID файлы

**Использование:**
```bash
./stop.sh
```

**Graceful shutdown:** SIGTERM → 2 sec wait → SIGKILL

---

## 📋 SYSTEMD SERVICES

### **draizer-engine.service:**

```ini
[Unit]
Description=Draizer V2.0 C Trading Engine
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/draizer/backend/c_engine/build
ExecStart=/home/ubuntu/draizer/backend/c_engine/build/draizer_engine --config ...
Restart=on-failure
RestartSec=10
CPUAffinity=2-7
Nice=-20

[Install]
WantedBy=multi-user.target
```

**Особенности:**
- `CPUAffinity=2-7` - закрепляет на CPU 2-7 (оставляет 0-1 для OS)
- `Nice=-20` - максимальный приоритет
- `Restart=on-failure` - автоматический перезапуск при падении

### **draizer-backend.service:**

```ini
[Unit]
Description=Draizer V2.0 Python Backend
After=network.target postgresql.service redis.service draizer-engine.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/draizer/backend
Environment="PATH=/home/ubuntu/draizer/backend/venv/bin:..."
ExecStart=/home/ubuntu/draizer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Особенности:**
- `After=draizer-engine.service` - ждет запуска C-Engine
- `Requires=postgresql.service redis.service` - зависимости
- `--workers 4` - 4 worker processes

**Управление:**
```bash
# Запуск
sudo systemctl start draizer-engine
sudo systemctl start draizer-backend

# Остановка
sudo systemctl stop draizer-engine
sudo systemctl stop draizer-backend

# Статус
sudo systemctl status draizer-engine

# Логи
sudo journalctl -u draizer-engine -f
```

---

## 🔒 SECURITY CONSIDERATIONS

### **Generated Secrets:**

Deploy scripts генерируют случайные credentials:

1. **`SECRET_KEY`** (32 bytes hex):
   ```bash
   openssl rand -hex 32
   ```

2. **`ENCRYPTION_KEY`** (32 bytes base64):
   ```bash
   openssl rand -base64 32
   ```

3. **DB Password** (16 bytes hex):
   ```bash
   openssl rand -hex 8
   ```

### **Permissions:**

- `.env` файл содержит sensitive data → должен быть в `.gitignore`
- PID файлы (`/tmp/*.pid`) → `0644` permissions
- Log файлы (`/tmp/*.log`) → `0644` permissions
- Shared memory (`/dev/shm/draizer_v2`) → `0600` permissions (sudo)

---

## 🐛 TROUBLESHOOTING

### **"yyjson not found"**

**Причина:** Library не установлена или не в `ldconfig` cache.

**Решение:**
```bash
sudo ldconfig -v | grep yyjson
# Если не найдено:
cd /tmp
git clone https://github.com/ibireme/yyjson.git
cd yyjson && mkdir build && cd build
cmake .. && make && sudo make install
sudo ldconfig
```

### **"PostgreSQL connection failed"**

**Причина:** PostgreSQL не запущен.

**Решение:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### **"C-Engine не подключается к биржам"**

**Причина:** Firewall блокирует WSS connections.

**Решение:**
```bash
# Проверь ping
ping api.bitfinex.com
ping www.deribit.com

# Проверь WSS
openssl s_client -connect api.bitfinex.com:443

# Если firewall проблема:
sudo ufw allow out 443/tcp
```

### **"Frontend не подключается к Backend"**

**Причина:** CORS misconfiguration.

**Решение:**
```python
# backend/app/core/config.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

---

## 📊 PERFORMANCE TUNING

### **CPU Pinning (Ubuntu):**

```bash
# Проверь текущую affinity
taskset -cp $(pgrep draizer_engine)

# Установи affinity (CPU 2-7)
sudo taskset -c 2-7 -p $(pgrep draizer_engine)
```

### **CPU Governor:**

```bash
# Проверь текущий governor
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Установи performance
sudo cpupower frequency-set -g performance

# Автоматически при загрузке
echo 'GOVERNOR="performance"' | sudo tee -a /etc/default/cpufrequtils
sudo systemctl restart cpufrequtils
```

### **Huge Pages:**

```bash
# Проверь текущие
cat /proc/meminfo | grep HugePages

# Установи 2048 pages (4MB)
echo 2048 | sudo tee /proc/sys/vm/nr_hugepages

# Автоматически при загрузке
echo "vm.nr_hugepages = 2048" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### **Network Tuning:**

```bash
# Увеличь TCP buffers
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"

# Уменьши TCP latency
sudo sysctl -w net.ipv4.tcp_low_latency=1
sudo sysctl -w net.core.busy_poll=50

# Автоматически при загрузке
sudo tee -a /etc/sysctl.conf <<EOF
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_low_latency = 1
net.core.busy_poll = 50
EOF
sudo sysctl -p
```

---

## 📈 MONITORING

### **System Metrics:**

```bash
# CPU usage
top -p $(pgrep draizer_engine)

# Memory usage
ps aux | grep draizer

# Network connections
netstat -anp | grep draizer

# Disk I/O
iotop -p $(pgrep draizer_engine)
```

### **Application Metrics:**

```bash
# C-Engine logs (systemd)
sudo journalctl -u draizer-engine -f

# C-Engine logs (manual)
tail -f /tmp/draizer_engine.log

# Backend logs
tail -f /tmp/draizer_backend.log

# Latency monitoring
sudo journalctl -u draizer-engine -f | grep LATENCY

# Opportunities detected
sudo journalctl -u draizer-engine -f | grep OPPORTUNITY
```

### **API Monitoring:**

```bash
# Health check
curl http://localhost:8000/health

# Engine status
curl http://localhost:8000/api/v2/engine/status | jq

# Recent operations
curl http://localhost:8000/api/v2/operations/recent | jq
```

---

## 🎯 BEST PRACTICES

### **Production Deployment:**

1. ✅ **Используй RT kernel** для минимальной jitter
2. ✅ **CPU Pinning** на dedicated cores (не core 0!)
3. ✅ **Disable Turbo Boost** для stable frequency
4. ✅ **Huge Pages** для меньшей фрагментации памяти
5. ✅ **Network Tuning** для low latency
6. ✅ **Systemd Services** для автоматического restart
7. ✅ **Monitoring** с alerting (Prometheus + Grafana)

### **Development (Windows):**

1. ✅ **Docker Desktop** с WSL2 backend
2. ✅ **Windows Terminal** для лучшего UX
3. ✅ **VS Code** с Remote-Containers extension
4. ✅ **Git Bash** или PowerShell 7+

### **Security:**

1. ✅ **Никогда не commit `.env`** файлы
2. ✅ **Rotate API keys** регулярно
3. ✅ **Firewall rules** только для нужных портов
4. ✅ **SSH key authentication** вместо паролей
5. ✅ **Log rotation** для предотвращения disk overflow

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

- [QUICKSTART.md](../QUICKSTART.md) - User-facing guide
- [UBUNTU_DEPLOYMENT_V2.md](UBUNTU_DEPLOYMENT_V2.md) - Detailed Ubuntu setup
- [V2.0_MIGRATION_SUMMARY.md](V2.0_MIGRATION_SUMMARY.md) - Migration details
- [V2.0_READY_TO_BUILD.md](V2.0_READY_TO_BUILD.md) - Build troubleshooting

---

**Last Updated:** 2025-10-29  
**Version:** 2.0.00

