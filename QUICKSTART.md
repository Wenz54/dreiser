# 🚀 DRAIZER V2.0 - QUICK START GUIDE

## Автоматическое развертывание за 5 минут!

---

## 📋 **ВЫБЕРИ СВОЮ ПЛАТФОРМУ:**

### **🐧 UBUNTU SERVER (Production)**

Рекомендуется для production развертывания с минимальной latency.

#### **Шаг 1: Скачать проект**
```bash
git clone https://github.com/your-repo/draizer.git
cd draizer
```

#### **Шаг 2: Запустить deploy скрипт**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Что делает скрипт:**
- ✅ Проверяет системные требования
- ✅ Устанавливает зависимости (PostgreSQL, Redis, Node.js)
- ✅ Собирает yyjson библиотеку
- ✅ Компилирует C-Engine (Release build)
- ✅ Настраивает PostgreSQL базу данных
- ✅ Устанавливает Python зависимости
- ✅ Собирает Frontend
- ✅ Применяет системные оптимизации (опционально)
- ✅ Создает systemd сервисы (опционально)

**Время выполнения:** ~10-15 минут (первый раз)

#### **Шаг 3: Добавить API ключи**
```bash
nano backend/.env
```

Добавь:
```env
DEEPSEEK_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
CRYPTOPANIC_API_TOKEN=your_token_here
```

#### **Шаг 4: Запустить систему**

**Вариант A: Systemd (рекомендуется)**
```bash
sudo systemctl start draizer-engine
sudo systemctl start draizer-backend
```

**Вариант B: Quick Start Script**
```bash
chmod +x quick-start.sh
./quick-start.sh
```

**Вариант C: Вручную**
```bash
# Terminal 1 - C-Engine
cd backend/c_engine/build
sudo taskset -c 2-7 nice -n -20 ./draizer_engine --config ../config/engine.json

# Terminal 2 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 3 - Frontend
cd frontend
npm run dev
```

#### **Шаг 5: Открыть Dashboard**
```
http://localhost:3000
```

---

### **🪟 WINDOWS (Development)**

Используется Docker для изоляции и упрощения.

#### **Предварительные требования:**
- ✅ Docker Desktop установлен и запущен
- ✅ WSL2 включен
- ✅ Минимум 10GB свободного места

#### **Шаг 1: Скачать проект**
```powershell
git clone https://github.com/your-repo/draizer.git
cd draizer
```

#### **Шаг 2: Запустить deploy скрипт**
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```

**Что делает скрипт:**
- ✅ Проверяет Docker
- ✅ Очищает старые контейнеры (опционально)
- ✅ Создает .env файл
- ✅ Собирает Docker images
- ✅ Запускает все сервисы
- ✅ Проверяет статус

**Время выполнения:** ~5-10 минут (первый раз)

#### **Шаг 3: Добавить API ключи**
Отредактируй `backend\.env`:
```env
DEEPSEEK_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
CRYPTOPANIC_API_TOKEN=your_token_here
```

Перезапусти:
```powershell
docker-compose restart
```

#### **Шаг 4: Запустить Frontend**
```powershell
cd frontend
npm install
npm run dev
```

#### **Шаг 5: Открыть Dashboard**
```
http://localhost:3000
```

---

## 🔧 **УПРАВЛЕНИЕ СЕРВИСАМИ:**

### **Ubuntu:**

#### Запуск:
```bash
# Быстрый старт (все сервисы)
./quick-start.sh

# ИЛИ через systemd
sudo systemctl start draizer-engine
sudo systemctl start draizer-backend
```

#### Остановка:
```bash
# Быстрая остановка (все сервисы)
./stop.sh

# ИЛИ через systemd
sudo systemctl stop draizer-engine
sudo systemctl stop draizer-backend
```

#### Логи:
```bash
# C-Engine
sudo journalctl -u draizer-engine -f

# Backend
sudo journalctl -u draizer-backend -f

# ИЛИ если запущено через quick-start
tail -f /tmp/draizer_engine.log
tail -f /tmp/draizer_backend.log
```

### **Windows:**

#### Запуск:
```powershell
# Быстрый старт
.\quick-start.ps1

# ИЛИ вручную
docker-compose up -d
```

#### Остановка:
```powershell
docker-compose down
```

#### Логи:
```powershell
# Все логи
docker-compose logs -f

# Только C-Engine
docker logs draizer_c_engine -f

# Только Backend
docker logs draizer_backend -f
```

---

## 📊 **ПРОВЕРКА РАБОТЫ:**

### **1. C-Engine подключился к биржам?**

**Ubuntu:**
```bash
sudo journalctl -u draizer-engine -n 50 | grep "Connected"
```

**Windows:**
```powershell
docker logs draizer_c_engine --tail=50 | Select-String "Connected"
```

**Ожидаемый вывод:**
```
✅ Bitfinex (SPOT): Connected (ping 0.8ms)
✅ Deribit (FUTURES): Connected (ping 0.88ms)
```

### **2. Backend работает?**

**Проверить API:**
```bash
curl http://localhost:8000/api/v2/engine/status
```

**Открыть API Docs:**
```
http://localhost:8000/docs
```

### **3. Frontend показывает данные?**

Открой Dashboard:
```
http://localhost:3000
```

**Должен показывать:**
- ✅ Balance: $1000.00
- ✅ Profit: $0.00 (0%)
- ✅ Operations table (пустая если нет сделок)

### **4. Видны возможности арбитража?**

**Ubuntu:**
```bash
sudo journalctl -u draizer-engine -f | grep "OPPORTUNITY"
```

**Windows:**
```powershell
docker logs draizer_c_engine -f | Select-String "OPPORTUNITY"
```

**Ожидаемый вывод (если есть возможности):**
```
💰 SPOT-FUTURES TARGET: BTCUSD | 112735 → 112755 | Spread: 17.75 bps | Net: 5.0 bps
✅ EXECUTED! Profit: $0.05 (0.05%)
```

**Если 0 возможностей** - это НОРМАЛЬНО! Рынки очень эффективны.

---

## 🐛 **TROUBLESHOOTING:**

### **❌ "Docker not found"**

**Windows:**
1. Установи Docker Desktop: https://www.docker.com/products/docker-desktop
2. Включи WSL2
3. Перезагрузи компьютер

### **❌ "Failed to build C-engine"**

**Ubuntu:**
```bash
# Установи yyjson вручную
cd /tmp
git clone https://github.com/ibireme/yyjson.git
cd yyjson && mkdir build && cd build
cmake .. && make && sudo make install
sudo ldconfig

# Попробуй снова
cd ~/draizer
./deploy.sh
```

### **❌ "No data on Frontend"**

**Проверь:**
1. C-Engine запущен? → `docker ps` (Windows) или `systemctl status draizer-engine` (Ubuntu)
2. Backend получает данные? → `curl http://localhost:8000/api/v2/engine/status`
3. Shared memory существует? → `ls -lh /dev/shm/draizer_v2` (Ubuntu)

**Если SHM не существует:**
```bash
# Ubuntu - рестарт C-Engine
sudo systemctl restart draizer-engine

# Windows - рестарт контейнера
docker-compose restart c_engine
```

### **❌ "0 opportunities detected"**

Это **НОРМАЛЬНО**!

Причины:
- Спред между Bitfinex spot и Deribit futures < 10 bps
- Funding rate слишком высокий
- Рынок очень эффективен (BTC, ETH обычно tight spreads)

**Решения:**
1. Подожди волатильности (news events)
2. Добавь больше пар (SOL, MATIC имеют wider spreads)
3. Снизь `min_spread_bps` в `backend/c_engine/config/engine.json` (осторожно! будешь терять на fees)

---

## 📈 **МОНИТОРИНГ PERFORMANCE:**

### **Latency:**

**Проверить latency Bitfinex:**
```bash
# Ubuntu
sudo journalctl -u draizer-engine -f | grep "BITFINEX"

# Windows
docker logs draizer_c_engine -f | Select-String "BITFINEX"
```

**Ожидаемая latency:**
- Ubuntu bare-metal: **5-50ms**
- Windows + Docker: **100-300ms**

### **Real-time Stats:**

**API endpoint:**
```bash
watch -n 1 'curl -s http://localhost:8000/api/v2/engine/status | jq'
```

**WebSocket logs:**
```
ws://localhost:8000/api/v2/engine/logs/stream
```

---

## 🎉 **ВСЁ РАБОТАЕТ? ОТЛИЧНО!**

Теперь ты можешь:
1. ✅ Мониторить Dashboard в реальном времени
2. ✅ Смотреть историю операций
3. ✅ Анализировать performance
4. ✅ Настраивать стратегии в `engine.json`

---

## 🆘 **НУЖНА ПОМОЩЬ?**

1. **Логи:**
   - Ubuntu: `sudo journalctl -u draizer-engine -n 100`
   - Windows: `docker logs draizer_c_engine --tail=100`

2. **System Info:**
   - `uname -a`
   - `docker --version`
   - `free -h`

3. **Documentation:**
   - `docs/UBUNTU_DEPLOYMENT_V2.md` - Полный deployment guide
   - `docs/V2.0_MIGRATION_SUMMARY.md` - Детали изменений
   - `docs/V2.0_READY_TO_BUILD.md` - Troubleshooting

---

**Happy Trading! 🚀**

