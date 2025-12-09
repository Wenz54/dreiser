    # 🔄 OpenRouter Setup Guide

## ✅ Что дает OpenRouter?

- 💰 **$5 free credits** при регистрации
- 🎯 Доступ к **100+ моделям** через один API
- 🔄 Легко переключаться между моделями
- 💳 Одна подписка для всех AI

---

## 📋 Быстрая настройка

### 1. Получи API ключ

```
https://openrouter.ai/
→ Sign Up (через Google/GitHub)
→ Keys → Create Key
→ Скопируй ключ (sk-or-v1-...)
```

### 2. Настрой .env

```env
# OpenRouter (заменяет DeepSeek + OpenAI)
DEEPSEEK_API_KEY=sk-or-v1-твой_ключ
DEEPSEEK_BASE_URL=https://openrouter.ai/api/v1
DEEPSEEK_MODEL=deepseek/deepseek-chat

OPENAI_API_KEY=sk-or-v1-твой_же_ключ
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=anthropic/claude-3.5-sonnet
```

### 3. Restart Docker

```bash
docker-compose restart backend celery_worker
```

---

## 🎯 Рекомендуемые модели

### Для Trading (DeepSeek заменитель):

```env
DEEPSEEK_MODEL=deepseek/deepseek-chat
```

**Альтернативы**:
- `anthropic/claude-3.5-sonnet` - Лучшая логика
- `meta-llama/llama-3.1-70b-instruct` - Дешевле
- `google/gemini-pro-1.5` - Быстрый

### Для Аналитики (GPT-4 заменитель):

```env
OPENAI_MODEL=anthropic/claude-3.5-sonnet
```

**Альтернативы**:
- `openai/gpt-4o` - Классический GPT-4
- `openai/gpt-4-turbo` - Дешевле GPT-4o
- `google/gemini-pro-1.5` - Бесплатнее

### Для News Analysis:

```env
# В telegram_monitor.py можно использовать:
# model = "anthropic/claude-3-haiku"  # Дешевый для простых задач
```

---

## 💰 Стоимость моделей

| Модель | Input | Output | Качество |
|--------|-------|--------|----------|
| `deepseek/deepseek-chat` | $0.14 | $0.28 | ⭐⭐⭐⭐⭐ |
| `anthropic/claude-3.5-sonnet` | $3.00 | $15.00 | ⭐⭐⭐⭐⭐ |
| `openai/gpt-4o` | $2.50 | $10.00 | ⭐⭐⭐⭐⭐ |
| `meta-llama/llama-3.1-70b` | $0.35 | $0.40 | ⭐⭐⭐⭐ |
| `google/gemini-pro-1.5` | $1.25 | $5.00 | ⭐⭐⭐⭐ |

**Примерная стоимость** при $5 credits:
- DeepSeek: ~15-20 дней
- Claude: ~3-5 дней
- Llama: ~10-15 дней

---

## 🔧 Дополнительные настройки

### Переключение моделей в runtime:

```python
# backend/app/services/ai_service.py

# Можно переключать модель динамически
if market_volatility > 0.05:
    self.model = "anthropic/claude-3.5-sonnet"  # Лучше для сложных ситуаций
else:
    self.model = "deepseek/deepseek-chat"  # Дешевле для обычных
```

### Fallback модели:

```python
# Если основная модель недоступна
try:
    response = await self._call_api(self.model)
except Exception:
    # Fallback на дешевую модель
    response = await self._call_api("meta-llama/llama-3.1-70b-instruct")
```

---

## 📊 Мониторинг расходов

### Через OpenRouter Dashboard:

```
https://openrouter.ai/activity
→ Смотри usage по моделям
→ Установи daily limit
```

### Alert когда осталось <$1:

В настройках OpenRouter:
- Settings → Billing → Set Alert

---

## 🎯 Best Practices

### 1. Используй дешевые модели где возможно:

```env
# News relevance scoring - простая задача
NEWS_ANALYSIS_MODEL=meta-llama/llama-3.1-8b-instruct

# Trading decisions - важная задача
TRADING_MODEL=deepseek/deepseek-chat

# Performance monitoring - критично
MONITOR_MODEL=anthropic/claude-3.5-sonnet
```

### 2. Кэшируй результаты:

```python
# Кэшируй анализ новостей (не менять каждую минуту)
@cache(ttl=1800)  # 30 минут
async def analyze_news(...):
    pass
```

### 3. Batch запросы:

```python
# Вместо 10 отдельных запросов:
for decision in decisions:
    await analyze(decision)

# Сделай 1 batch:
await analyze_batch(decisions)
```

---

## ✅ Проверка работы

```bash
# Test DeepSeek через OpenRouter
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-chat",
    "messages": [{"role": "user", "content": "Test"}]
  }'

# Проверь credits
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"
```

---

## 🆘 Troubleshooting

### Error: "Model not found"

```
✅ Проверь формат: "provider/model-name"
✅ Список моделей: https://openrouter.ai/models
```

### Error: "Insufficient credits"

```
✅ Проверь баланс: https://openrouter.ai/credits
✅ Пополни: Settings → Add Credits
```

### Slow responses

```
✅ Попробуй другую модель (например, llama вместо claude)
✅ Проверь OpenRouter status: https://status.openrouter.ai/
```

---

**Готово! OpenRouter настроен! 🚀**

Хватит ли $5? Для теста 5-10 дней точно хватит!

