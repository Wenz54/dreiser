# 🔄 Миграция: Telegram → CryptoPanic

## ✅ ЗАВЕРШЕНО

Система **полностью переписана** с Telegram на CryptoPanic!

---

## 📦 ЧТО ИЗМЕНИЛОСЬ

### Файлы обновлены (7):

1. **`backend/app/tasks/news_tasks.py`** - полностью переписан
   - `monitor_telegram_news()` → `monitor_crypto_news()`
   - `telegram_monitor` → `cryptopanic_service`
   - Убран GPT анализ (CryptoPanic уже дает sentiment)

2. **`backend/app/tasks/celery_app.py`** - обновлен schedule
   - `"monitor-telegram-news"` → `"monitor-crypto-news"`

3. **`backend/app/api/v1/endpoints/telegram.py`** - переименованы endpoints
   - `/telegram/news/*` → `/news/*`
   - Tags: "Telegram News" → "Crypto News"
   - Параметры: `channel_username` → `currencies`, `filter_type`

4. **`backend/app/api/v1/api.py`** - обновлены imports
   - `telegram.router` → `news.router`

5. **`backend/app/core/config.py`** - добавлен
   - `CRYPTOPANIC_API_TOKEN: Optional[str]`

6. **`.env.example`** - полностью переписан
   - Убраны Telegram переменные из основной секции
   - Добавлен `CRYPTOPANIC_API_TOKEN`

7. **`test_cryptopanic.py`** - создан новый тест

---

## 🆕 НОВЫЕ ENDPOINTS

| Старый (Telegram) | Новый (CryptoPanic) |
|-------------------|---------------------|
| `GET /api/v1/telegram/news/latest` | `GET /api/v1/news/latest` |
| `POST /api/v1/telegram/news/fetch` | `POST /api/v1/news/fetch` |
| `GET /api/v1/telegram/news/{id}` | `GET /api/v1/news/{id}` |

### Новые параметры:

```python
# Старый (Telegram)
POST /api/v1/telegram/news/fetch?channel_username=@crypto_news

# Новый (CryptoPanic)
POST /api/v1/news/fetch?currencies=BTC&filter_type=hot
```

---

## 📊 ПРЕИМУЩЕСТВА

| Фича | Telegram | CryptoPanic |
|------|----------|-------------|
| **Setup** | 5-10 мин (verification) | 30 секунд |
| **Источники** | 1 канал | 500+ сайтов |
| **Sentiment** | Нужен GPT | Встроен |
| **API calls** | 2 (Telegram + GPT) | 1 |
| **Стоимость** | GPT analysis ~$0.02/запрос | Бесплатно |
| **Надёжность** | Зависит от канала | Агрегатор |
| **Фильтры** | Нет | Hot/Important/Trending |

---

## 🚀 КАК ИСПОЛЬЗОВАТЬ

### 1. Получи CryptoPanic Token

```
https://cryptopanic.com/developers/api/
→ "Get your free API token"
→ Заполни форму (30 секунд)
→ Получи token
```

### 2. Добавь в .env

```env
CRYPTOPANIC_API_TOKEN=твой_token_здесь
```

### 3. Тест

```bash
python test_cryptopanic.py
```

Ожидается:
```
🔥 ТЕСТ: CryptoPanic API
✅ Успешно!
   Получено новостей: 25
   Latency: 345ms

📰 Первые 3 новости:
1. 📈 BULLISH
   Bitcoin ETF approval expected next week...
   Source: coindesk.com | Votes: +145 -12
```

### 4. Запуск

```bash
docker-compose up --build
```

---

## 🔄 ЧТО ОСТАЛОСЬ БЕЗ ИЗМЕНЕНИЙ

✅ **Database schema** - `news_summaries` table работает как раньше
✅ **Trading service** - `_get_latest_news_context()` без изменений
✅ **DeepSeek prompt** - получает новости как раньше
✅ **GPT Relevance Scorer** - работает (опционально)

---

## ⚠️ BREAKING CHANGES

Если у тебя уже были старые endpoints в use:

### Frontend:

```javascript
// Старое
fetch('/api/v1/telegram/news/latest')

// Новое
fetch('/api/v1/news/latest')
```

### Manual trigger:

```python
# Старое
requests.post('/api/v1/telegram/news/fetch', 
              json={"channel_username": "@crypto_news"})

# Новое  
requests.post('/api/v1/news/fetch?currencies=BTC&filter_type=hot')
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Через curl:

```bash
# Latest news
curl http://localhost:8000/api/v1/news/latest \
  -H "Authorization: Bearer YOUR_TOKEN"

# Manual fetch
curl -X POST "http://localhost:8000/api/v1/news/fetch?currencies=BTC&filter_type=hot" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Через Python:

```python
from app.services.cryptopanic_service import cryptopanic_service

result = await cryptopanic_service.get_news_summary("BTC", "hot")
print(f"News: {result['news_count']}, Sentiment: {result['overall_sentiment']}")
```

---

## 📝 МИГРАЦИЯ ДАННЫХ

**Старые news_summaries** (из Telegram) остаются в БД и работают.

**Новые news_summaries** (из CryptoPanic) будут иметь:
- `channel_id = "cryptopanic"`
- `channel_name = "CryptoPanic Aggregator"`
- `overall_relevance = 100` (уже отфильтрованы)

---

## ✅ CHECKLIST

Перед запуском:

```
✅ Получил CryptoPanic API token
✅ Добавил в .env: CRYPTOPANIC_API_TOKEN=...
✅ Протестировал: python test_cryptopanic.py
✅ Обновил frontend endpoints (если были)
✅ Restart Docker: docker-compose up --build
✅ Проверил логи: docker-compose logs celery_worker
```

---

## 🎉 РЕЗУЛЬТАТ

**ДО**:
- Telegram verification → 5-10 минут
- Один канал → ограниченный охват
- GPT анализ → дополнительные расходы
- Sentiment нужно вычислять

**ПОСЛЕ**:
- CryptoPanic token → 30 секунд ✅
- 500+ источников → полный охват ✅
- Без GPT анализа → бесплатно ✅
- Sentiment встроен ✅

---

**Готово! CryptoPanic работает! 🚀**

