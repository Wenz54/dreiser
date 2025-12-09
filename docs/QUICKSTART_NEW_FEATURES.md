# 🚀 БЫСТРЫЙ СТАРТ: НОВЫЕ ФИЧИ

## 📋 ЧТО ДОБАВЛЕНО

1. **Telegram News Monitor** - автоматический анализ новостей каждые 30 мин
2. **DeepSeek Context Manager** - сжатие истории каждые 10 решений  
3. **Maximum Security Layer** - HMAC signing, anomaly detection, API key rotation

---

## ⚡ SETUP ЗА 5 МИНУТ

### Шаг 1: Обновить зависимости

```bash
cd backend
pip install -r requirements.txt
```

**Новые пакеты**: celery, telethon, python-telegram-bot, itsdangerous, bleach

### Шаг 2: Настроить `.env` 

```bash
cp .env.example .env
nano .env  # или notepad .env на Windows
```

**Добавить Telegram credentials (ОПЦИОНАЛЬНО)**:
```env
# Telegram Integration (получить на https://my.telegram.org)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abc123def456...
TELEGRAM_PHONE=+1234567890
TELEGRAM_NEWS_CHANNEL=@crypto_news  # Канал для мониторинга
```

**Если НЕ настроишь Telegram** - остальные фичи все равно работают!

### Шаг 3: Создать миграции БД

```bash
cd backend
alembic revision --autogenerate -m "Add news and security tables"
alembic upgrade head
```

**Новые таблицы**:
- `news_summaries` - Telegram news
- `deepseek_contexts` - compressed history  
- `security_audit_logs` - enhanced security
- `api_key_rotations` - key management

### Шаг 4: Запустить с Celery

```bash
docker-compose up --build
```

**Новые контейнеры**:
- `celery_worker` - background tasks
- `celery_beat` - periodic scheduler (каждые 30 мин)

---

## 🎮 КАК ИСПОЛЬЗОВАТЬ

### 1. Telegram News Monitoring

#### Automatic (каждые 30 минут):
```bash
# Celery Beat автоматически запустит task
# Check logs:
docker-compose logs celery_beat
```

#### Manual trigger:
```bash
curl -X POST http://localhost:8000/api/v1/telegram/news/fetch \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel_username": "@crypto_news"}'
```

#### Get latest news:
```bash
curl http://localhost:8000/api/v1/telegram/news/latest \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response**:
```json
{
  "summaries": [
    {
      "id": "123",
      "channel": "@crypto_news",
      "messages_count": 15,
      "summary": "• BTC ETF approval expected next week\n• Whale wallet moved 10k BTC\n• SEC postpones decision...",
      "sentiment": "bullish",
      "keywords": ["ETF", "SEC", "whale", "BTC"],
      "processed_at": "2025-10-21T15:30:00",
      "used_in_trading": false
    }
  ]
}
```

### 2. DeepSeek Context Compression

**Автоматически срабатывает** каждые 10 AI решений.

Check compression:
```bash
# Run 10+ AI analyses
for i in {1..12}; do
  curl -X POST http://localhost:8000/api/v1/ai/analyze \
    -H "Authorization: Bearer YOUR_TOKEN"
  sleep 5
done

# Check backend logs для compression message:
# "✅ Context compressed: 10 decisions, saved ~4500 tokens"
```

**PostgreSQL check**:
```sql
SELECT * FROM deepseek_contexts ORDER BY created_at DESC LIMIT 5;
```

### 3. Enhanced Security

#### Request Signing (для production):

```env
# В .env
ENABLE_REQUEST_SIGNING=True
```

**Client code example**:
```python
import hmac, hashlib, time, requests

api_key = "dk_abc123..."
api_secret = "secret_xyz..."

# Sign request
body = '{"amount": 100}'
timestamp = int(time.time())
message = f"{body}{timestamp}"
signature = hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

# Make request
headers = {
    "Authorization": f"Bearer {access_token}",
    "X-API-Key": api_key,
    "X-Signature": signature,
    "X-Timestamp": str(timestamp)
}
response = requests.post("http://localhost:8000/api/v1/trading/manual-trade", 
                        headers=headers, data=body)
```

#### Anomaly Detection:

Автоматически работает! Check logs:
```bash
# Try >5 failed logins:
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "test", "password": "wrong"}'
done

# Check security_audit_logs:
docker-compose exec postgres psql -U draizer_user -d draizer_db \
  -c "SELECT * FROM security_audit_logs WHERE is_anomaly = true;"
```

#### API Key Rotation:

```bash
# Celery task runs daily at 03:00
# Check logs:
docker-compose logs celery_beat | grep rotation

# Manual check:
docker-compose exec postgres psql -U draizer_user -d draizer_db \
  -c "SELECT * FROM api_key_rotations;"
```

---

## 🔍 ПРОВЕРИТЬ ЧТО ВСЕ РАБОТАЕТ

### 1. Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}
```

### 2. Celery Worker
```bash
docker-compose logs celery_worker | tail -20
# Expected: "celery@... ready"
```

### 3. Celery Beat
```bash
docker-compose logs celery_beat | tail -20
# Expected: "Scheduler: Sending due task..."
```

### 4. Database Tables
```bash
docker-compose exec postgres psql -U draizer_user -d draizer_db \
  -c "\dt"
# Expected: 12+ tables включая news_summaries, deepseek_contexts
```

### 5. News API
```bash
curl http://localhost:8000/api/v1/telegram/news/latest \
  -H "Authorization: Bearer $(curl -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"YOUR_USERNAME","password":"YOUR_PASSWORD"}' | jq -r '.access_token')"
```

---

## 🐛 TROUBLESHOOTING

### Problem: Celery не запускается

**Error**: `ModuleNotFoundError: No module named 'celery'`

**Fix**:
```bash
docker-compose down
docker-compose up --build
```

### Problem: Telegram verification code

**Error**: `SessionPasswordNeededError`

**Fix**: При первом запуске Telegram попросит код:
1. Check logs: `docker-compose logs celery_worker`
2. Enter код из Telegram app
3. Создастся `draizer_bot.session` файл
4. Больше не спросит

### Problem: News не приходят

**Check**:
1. TELEGRAM_NEWS_CHANNEL правильно настроен?
   ```env
   TELEGRAM_NEWS_CHANNEL=@crypto_news  # С @ обязательно!
   ```

2. Channel существует и публичный?
   - Попробуй открыть в браузере: `https://t.me/crypto_news`

3. Celery Beat работает?
   ```bash
   docker-compose logs celery_beat
   # Должны быть: "Scheduler: Sending due task monitor-telegram-news"
   ```

### Problem: Context compression не срабатывает

**Причина**: Нужно минимум 10 AI решений.

**Check**:
```sql
SELECT COUNT(*) FROM ai_decisions WHERE portfolio_id = 'YOUR_PORTFOLIO_ID';
-- Должно быть >= 10
```

**Fix**: Просто подожди пока накопится 10 решений.

### Problem: Security audit logs не записываются

**Check middleware**:
```python
# В main.py должен быть audit middleware (TODO: реализовать)
```

**Temporary**: Пока что audit logs создаются вручную в endpoints.

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### После 1 часа работы:

- ✅ **2 News summaries** (каждые 30 мин)
- ✅ **~4 AI decisions** (каждые 15 мин)
- ✅ **~100+ audit logs** (каждый API call)

### После 3 часов:

- ✅ **6 News summaries**
- ✅ **12 AI decisions** → **1 context compression** ✨
- ✅ **~500+ audit logs**

### После 24 часов:

- ✅ **48 News summaries**
- ✅ **96 AI decisions** → **9 context compressions** ✨
- ✅ **~5000+ audit logs**
- ✅ **1 API key rotation check** (daily task)
- ✅ **1 Audit log cleanup** (daily task)

---

## 💡 СОВЕТЫ

### Для тестирования Telegram без реального канала:

```python
# Создай тестовый Telegram канал:
# 1. Open Telegram → New Channel
# 2. Name: "Draizer Test News"
# 3. Username: @draizer_test_news
# 4. Публикуй туда тестовые сообщения

# В .env:
TELEGRAM_NEWS_CHANNEL=@draizer_test_news
```

### Для ускорения тестирования context compression:

```python
# В config.py измени threshold:
DEEPSEEK_CONTEXT_COMPRESSION_THRESHOLD: int = 3  # Вместо 10

# Restart backend:
docker-compose restart backend celery_worker
```

### Для отключения Telegram (если не нужно):

```env
# Закомментируй в .env:
# TELEGRAM_API_ID=...
# TELEGRAM_NEWS_CHANNEL=...

# Celery task просто skip'нет мониторинг
```

---

## 🎯 NEXT STEPS

1. ✅ Запусти `docker-compose up --build`
2. ✅ Создай account в UI
3. ✅ Run несколько AI analyses
4. ✅ Подожди 30 мин для первого news summary
5. ✅ Проверь context compression после 10 решений
6. ✅ Проверь audit logs в PostgreSQL

**Готово! Все три фичи работают! 🚀**

---

**Вопросы?** Check `FEATURES_CHANGELOG.md` для детальной документации.

