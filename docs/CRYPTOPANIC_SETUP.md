# 🔥 CryptoPanic Integration - Замена Telegram

## 🎯 Преимущества

**CryptoPanic** vs Telegram:

| Фича | CryptoPanic | Telegram |
|------|-------------|----------|
| **Бесплатно** | ✅ 1000 req/день | ⚠️ Нужен API setup |
| **Готовность** | ✅ 30 секунд setup | ❌ Верификация кода |
| **Источники** | ✅ 500+ сайтов | ⚠️ 1 канал |
| **Sentiment** | ✅ Встроен | ❌ Нужен GPT |
| **Фильтры** | ✅ Hot/Important | ❌ Всё подряд |
| **Надёжность** | ✅ Высокая | ⚠️ Зависит от канала |

---

## 🚀 БЫСТРЫЙ СТАРТ (30 секунд)

### Шаг 1: Получи API Token

```
https://cryptopanic.com/developers/api/
```

1. Нажми **"Get your free API token"**
2. Заполни форму (email + project name)
3. Получи token (бесплатно!)

```
YOUR_TOKEN: abc123def456ghi789...
```

### Шаг 2: Добавь в .env

```env
# CryptoPanic API (вместо Telegram)
CRYPTOPANIC_API_TOKEN=abc123def456ghi789...
```

### Шаг 3: Готово! ✅

Новости работают сразу!

---

## 📋 ЧТО ПОЛУЧАЕМ

### Пример новости:

```json
{
  "id": "123456",
  "title": "Bitcoin ETF approval expected next week - SEC sources",
  "url": "https://coindesk.com/...",
  "source": "coindesk.com",
  "published_at": "2025-10-21T15:30:00Z",
  "votes": {
    "positive": 145,
    "negative": 12,
    "neutral": 5
  },
  "sentiment": "bullish",
  "currencies": ["BTC"]
}
```

### Пример summary для DeepSeek:

```
News Summary (last 30 min): 15 items

• [BULLISH] Bitcoin ETF approval expected next week (coindesk.com)
• [BULLISH] Major exchange reports record BTC inflows (cointelegraph.com)
• [NEUTRAL] Whale wallet moved 10k BTC to unknown address (bitcoinmagazine.com)
• [BEARISH] SEC postpones decision on XYZ proposal (decrypt.co)

Overall Sentiment: BULLISH (12 bullish, 1 bearish, 2 neutral)
```

---

## 🔄 ИНТЕГРАЦИЯ

### 1. Config (уже добавлено):

```python
# backend/app/core/config.py
CRYPTOPANIC_API_TOKEN: Optional[str] = None
```

### 2. Service (уже создан):

```python
# backend/app/services/cryptopanic_service.py
cryptopanic_service.get_news_summary()
```

### 3. Celery Task (замена telegram_monitor):

```python
# backend/app/tasks/news_tasks.py

@celery_app.task
def monitor_cryptopanic_news():
    """Каждые 30 минут - fetch hot news"""
    asyncio.run(_monitor_cryptopanic_async())

async def _monitor_cryptopanic_async():
    result = await cryptopanic_service.get_news_summary(
        currencies="BTC",
        filter_type="hot"
    )
    
    # Save to news_summaries table
    # ... (аналогично telegram)
```

### 4. Trading Service (использует новости):

```python
# backend/app/services/trading_service.py

async def _get_latest_news_context(self) -> str:
    # Получить last news_summary (теперь из CryptoPanic)
    # Работает так же!
```

---

## 🎨 ДОСТУПНЫЕ ФИЛЬТРЫ

### Filter Types:

```python
# Hot news (breaking, trending)
filter="hot"  # ⭐ Рекомендуется

# Important (major events only)
filter="important"

# Rising (gaining traction)
filter="rising"

# Bullish news only
filter="bullish"

# Bearish news only
filter="bearish"
```

### Currencies:

```python
# Только Bitcoin
currencies="BTC"

# Bitcoin + Ethereum
currencies="BTC,ETH"

# Все
currencies=""  # (не рекомендуется, слишком много)
```

---

## 📊 API LIMITS

**Free Tier**:
- ✅ 1000 requests/день
- ✅ All features
- ✅ No credit card

**Наше использование**:
- 48 requests/день (каждые 30 мин)
- ✅ **Полностью в лимитах!**

---

## 🔧 ДОПОЛНИТЕЛЬНЫЕ ФИЧИ

### 1. Metadata для каждой новости:

```python
news_item = {
    "title": "...",
    "votes": {"positive": 100, "negative": 10},
    "source": "coindesk.com",  # Проверенный источник
    "published_at": "...",
    "url": "..."  # Ссылка на оригинал
}
```

### 2. Автоматический sentiment:

```python
# Рассчитывается из votes
if positive_ratio >= 0.65: "bullish"
elif positive_ratio <= 0.35: "bearish"
else: "neutral"
```

### 3. Фильтрация по времени:

```python
# Только последние 30 минут
cutoff_time = datetime.utcnow() - timedelta(minutes=30)
```

---

## 🆚 СРАВНЕНИЕ С АЛЬТЕРНАТИВАМИ

| Источник | Бесплатно | Setup | Качество | Sentiment |
|----------|-----------|-------|----------|-----------|
| **CryptoPanic** | ✅ | 30 сек | ⭐⭐⭐⭐⭐ | ✅ Встроен |
| Telegram | ⚠️ | 5 мин | ⭐⭐⭐⭐ | ❌ Нужен GPT |
| RSS Feeds | ✅ | 1 мин | ⭐⭐⭐ | ❌ Нужен GPT |
| Reddit | ✅ | 2 мин | ⭐⭐⭐ | ⚠️ Шум |
| NewsAPI | ❌ | 1 мин | ⭐⭐⭐⭐ | ❌ Нужен GPT |

**Победитель**: CryptoPanic! 🏆

---

## 🧪 ТЕСТИРОВАНИЕ

### Через curl:

```bash
curl "https://cryptopanic.com/api/v1/posts/?auth_token=YOUR_TOKEN&currencies=BTC&filter=hot"
```

### Через Python:

```python
from app.services.cryptopanic_service import cryptopanic_service

result = await cryptopanic_service.get_news_summary(
    currencies="BTC",
    filter_type="hot"
)

print(f"News count: {result['news_count']}")
print(f"Sentiment: {result['overall_sentiment']}")
print(f"Summary:\n{result['summary_text']}")
```

---

## ✅ CHECKLIST

Перед запуском:

```
✅ Получил CryptoPanic API token
✅ Добавил в .env: CRYPTOPANIC_API_TOKEN=...
✅ Обновил tasks/news_tasks.py (замена telegram → cryptopanic)
✅ Restart Docker: docker-compose restart celery_worker celery_beat
✅ Проверил логи: docker-compose logs celery_worker
```

---

## 🎉 РЕЗУЛЬТАТ

**До** (Telegram):
- ⚠️ Нужна верификация кода
- ⚠️ Один канал
- ⚠️ Может быть spam
- ❌ Нужен GPT для sentiment

**После** (CryptoPanic):
- ✅ Работает сразу (30 сек setup)
- ✅ 500+ источников
- ✅ Только проверенные новости
- ✅ Sentiment встроен

---

**Готово! CryptoPanic намного лучше! 🚀**

