# 🔑 Полное руководство: Как получить все API ключи

## 📋 КРАТКИЙ ЧЕКЛИСТ

Тебе нужно получить API ключи для 4 сервисов:

1. ✅ **DeepSeek** - для AI трейдинга (ОБЯЗАТЕЛЬНО)
2. ✅ **OpenAI** - для GPT-4 аналитики (ОБЯЗАТЕЛЬНО)
3. ✅ **Binance** - для рыночных данных (ОБЯЗАТЕЛЬНО)
4. ⭐ **Telegram** - для новостей (ОПЦИОНАЛЬНО)

---

## 1️⃣ DeepSeek API

### Зачем нужен?
DeepSeek принимает решения о покупке/продаже BTC.

### Как получить:

**Шаг 1**: Открой https://platform.deepseek.com/

**Шаг 2**: Зарегистрируйся / Войди
- Можно через GitHub, Google или email

**Шаг 3**: Перейди в **API Keys**
- URL: https://platform.deepseek.com/api_keys

**Шаг 4**: Нажми **"Create API Key"**

**Шаг 5**: Скопируй ключ (начинается с `sk-`)
```
sk-1234567890abcdefghijklmnopqrstuvwxyz...
```

⚠️ **ВАЖНО**: Ключ показывается только ОДИН раз! Сохрани его сразу.

**Шаг 6**: Пополни баланс (минимум $1-5)
- Settings → Billing → Add credit

### Стоимость:
- ~$0.14 за 1M tokens (input)
- ~$0.28 за 1M tokens (output)
- **Примерно**: $0.50-2.00 в день для активной торговли

### Заполни в .env:
```env
DEEPSEEK_API_KEY=sk-твой_ключ_сюда
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

---

## 2️⃣ OpenAI API (GPT-4)

### Зачем нужен?
Для аналитического чата, анализа новостей, performance monitoring.

### Как получить:

**Шаг 1**: Открой https://platform.openai.com/

**Шаг 2**: Зарегистрируйся / Войди

**Шаг 3**: Перейди в **API keys**
- URL: https://platform.openai.com/api-keys

**Шаг 4**: Нажми **"Create new secret key"**

**Шаг 5**: Дай имя (например: "Draizer Trading Bot")

**Шаг 6**: Скопируй ключ (начинается с `sk-`)
```
sk-proj-abcd1234...
```

⚠️ **ВАЖНО**: Ключ показывается только ОДИН раз!

**Шаг 7**: Добавь способ оплаты
- Settings → Billing → Add payment method
- Установи лимит (например: $10/месяц)

### Стоимость (GPT-4):
- Input: $2.50 за 1M tokens
- Output: $10.00 за 1M tokens
- **Примерно**: $2-5 в день для нашего приложения

### Альтернатива (дешевле):
Можно использовать **GPT-3.5-turbo** вместо GPT-4:
- В 10 раз дешевле ($0.50/$1.50 за 1M)
- Немного хуже качество

Для этого измени в `backend/app/services/gpt_service.py`:
```python
self.model = "gpt-3.5-turbo"  # Вместо "gpt-4"
```

### Заполни в .env:
```env
OPENAI_API_KEY=sk-proj-твой_ключ
OPENAI_BASE_URL=https://api.openai.com/v1
```

---

## 3️⃣ Binance API

### Зачем нужен?
Для получения реальных цен BTC/USDT и рыночных данных.

### ⚠️ ДВА ВАРИАНТА: Testnet vs Real

#### Вариант A: Testnet (РЕКОМЕНДУЮ ДЛЯ НАЧАЛА)

**Плюсы**:
- ✅ Бесплатно
- ✅ Не нужна верификация
- ✅ Реальные цены (но тестовые ключи)

**Минусы**:
- ❌ Иногда данные могут быть неполными

**Как получить**:

**Шаг 1**: Открой https://testnet.binance.vision/

**Шаг 2**: Нажми **"Generate HMAC_SHA256 Key"**

**Шаг 3**: Скопируй оба ключа:
```
API Key: abcdef123456...
Secret Key: xyz789...
```

**Шаг 4**: Заполни в .env:
```env
BINANCE_API_KEY=твой_api_key
BINANCE_API_SECRET=твой_secret_key
BINANCE_USE_TESTNET=true  # ← ВАЖНО!
```

#### Вариант B: Real Binance API

**Плюсы**:
- ✅ Полные данные
- ✅ Все функции

**Минусы**:
- ❌ Нужна регистрация + верификация (KYC)

**Как получить**:

**Шаг 1**: Зарегистрируйся на https://www.binance.com/

**Шаг 2**: Пройди верификацию (KYC)
- Identity Verification → Upload документы

**Шаг 3**: Перейди в **API Management**
- Profile → API Management
- URL: https://www.binance.com/en/my/settings/api-management

**Шаг 4**: Создай новый API Key
- Label: "Draizer Trading Bot"
- ⚠️ **ВАЖНО**: Выбери только **"Enable Reading"**
- НЕ включай "Enable Spot & Margin Trading" (нам не нужно!)

**Шаг 5**: Скопируй API Key и Secret

**Шаг 6**: Заполни в .env:
```env
BINANCE_API_KEY=твой_api_key
BINANCE_API_SECRET=твой_secret_key
BINANCE_USE_TESTNET=false  # ← Real API
```

### ⚠️ БЕЗОПАСНОСТЬ:
- ✅ Включи только **"Enable Reading"**
- ❌ НЕ включай trading permissions
- ✅ Установи IP whitelist (если возможно)
- ✅ Храни ключи в `.env` (НЕ коммить в git!)

---

## 4️⃣ Telegram API (ОПЦИОНАЛЬНО)

### Зачем нужен?
Для мониторинга новостных каналов (необязательно, но полезно).

### Как получить:

**Шаг 1**: Открой https://my.telegram.org/

**Шаг 2**: Войди через свой номер телефона
- Введи номер в международном формате: +7...
- Получишь код в Telegram app

**Шаг 3**: Перейди в **"API development tools"**
- URL: https://my.telegram.org/apps

**Шаг 4**: Создай приложение
- App title: "Draizer Trading Bot"
- Short name: "draizer"
- Platform: Other

**Шаг 5**: Получишь:
```
App api_id: 12345678
App api_hash: abcdef1234567890abcdef1234567890
```

**Шаг 6**: Заполни в .env:
```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=твой_api_hash
TELEGRAM_PHONE=+79991234567  # Твой номер телефона
TELEGRAM_NEWS_CHANNEL=@crypto_news  # Канал для мониторинга
```

### Первый запуск:
При первом запуске Telegram попросит код подтверждения:
```bash
docker-compose up celery_worker

# В логах:
# "Please enter the code you received: "
# Введи код из Telegram app (5 цифр)
```

После этого создастся файл `draizer_bot.session` → больше код не нужен.

---

## 🔐 БЕЗОПАСНОСТЬ: Генерация секретных ключей

### JWT Secret Key

**Способ 1** (Linux/Mac/WSL):
```bash
openssl rand -hex 32
```

**Способ 2** (Python):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Результат**:
```
a1b2c3d4e5f6...  # 64 символа
```

Заполни:
```env
JWT_SECRET_KEY=твой_сгенерированный_ключ
```

### Encryption Key (Fernet)

**Python**:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Результат**:
```
AbCdEf123456...==  # Base64 строка
```

Заполни:
```env
ENCRYPTION_KEY=твой_fernet_ключ
```

### Database Password

**Генератор**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Заполни:
```env
POSTGRES_PASSWORD=твой_надёжный_пароль
```

---

## 📝 ПОЛНЫЙ .env ФАЙЛ (пример)

```env
# DATABASE
POSTGRES_SERVER=postgres
POSTGRES_USER=draizer_user
POSTGRES_PASSWORD=super_secure_password_12345  # ← Сгенерируй!
POSTGRES_DB=draizer_db
POSTGRES_PORT=5432

# REDIS
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# ===== API KEYS - ЗАПОЛНИ СВОИ! =====

# DeepSeek (ОБЯЗАТЕЛЬНО)
DEEPSEEK_API_KEY=sk-1234567890abcdef...  # ← platform.deepseek.com
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# OpenAI (ОБЯЗАТЕЛЬНО)
OPENAI_API_KEY=sk-proj-abcdef123...  # ← platform.openai.com
OPENAI_BASE_URL=https://api.openai.com/v1

# Binance (ОБЯЗАТЕЛЬНО)
BINANCE_API_KEY=abc123...  # ← testnet.binance.vision или binance.com
BINANCE_API_SECRET=xyz789...
BINANCE_USE_TESTNET=true  # true для testnet, false для real

# Telegram (ОПЦИОНАЛЬНО)
TELEGRAM_API_ID=12345678  # ← my.telegram.org
TELEGRAM_API_HASH=abcdef123456...
TELEGRAM_PHONE=+79991234567
TELEGRAM_NEWS_CHANNEL=@crypto_news

# ===== SECURITY =====

# Сгенерируй свои ключи!
JWT_SECRET_KEY=a1b2c3d4e5f6...  # ← openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

ENCRYPTION_KEY=AbCdEf123...==  # ← Fernet.generate_key()

# ===== APPLICATION =====

ENVIRONMENT=development
DEBUG=true
APP_NAME=Draizer
APP_VERSION=1.2.0
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ===== SECURITY SETTINGS =====

MFA_REQUIRED=true
PASSWORD_MIN_LENGTH=12
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
API_KEY_ROTATION_DAYS=90
AUDIT_LOG_RETENTION_DAYS=365
ENABLE_REQUEST_SIGNING=false  # true для production
ANOMALY_DETECTION_ENABLED=true

# ===== TRADING =====

INITIAL_BALANCE_USD=1000.00
DEFAULT_TRADING_SYMBOL=BTCUSDT
AI_DECISION_INTERVAL_MINUTES=15
DEEPSEEK_CONTEXT_COMPRESSION_THRESHOLD=10

# ===== FRONTEND =====

VITE_API_URL=http://localhost:8000

# ===== LOGGING =====

LOG_LEVEL=INFO
```

---

## ✅ ПРОВЕРКА НАСТРОЙКИ

После заполнения `.env`, проверь:

```bash
# 1. Запусти Docker
docker-compose up -d

# 2. Проверь логи
docker-compose logs backend | grep -i "error\|success"

# 3. Health check
curl http://localhost:8000/health

# Ожидается:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

---

## 🆘 TROUBLESHOOTING

### DeepSeek Error: "Invalid API key"
```
✅ Проверь: ключ начинается с "sk-"
✅ Проверь: нет лишних пробелов
✅ Проверь: баланс > $0 на platform.deepseek.com
```

### OpenAI Error: "Insufficient credits"
```
✅ Добавь способ оплаты: platform.openai.com/settings/billing
✅ Установи лимит: $10-20
```

### Binance Error: "Invalid API key"
```
✅ Если testnet: используй ключи с testnet.binance.vision
✅ Если real: проверь что включен "Enable Reading"
✅ Проверь BINANCE_USE_TESTNET=true/false соответствует ключам
```

### Telegram Error: "SessionPasswordNeeded"
```
✅ У тебя 2FA на Telegram
✅ Введи пароль в логах celery_worker
```

---

## 💰 СТОИМОСТЬ В ДЕНЬ

**Минимальная конфигурация** (testnet + minimal usage):
- DeepSeek: $0.50-1.00
- OpenAI (GPT-3.5): $0.30-0.80
- Binance: FREE (testnet)
- **ИТОГО**: ~$1-2 в день (~$30-60/месяц)

**Продакшн** (real data + GPT-4):
- DeepSeek: $1-3
- OpenAI (GPT-4): $2-5
- Binance: FREE (read-only)
- **ИТОГО**: ~$3-8 в день (~$90-240/месяц)

---

## 📚 ПОЛЕЗНЫЕ ССЫЛКИ

1. **DeepSeek**: https://platform.deepseek.com/
2. **OpenAI**: https://platform.openai.com/
3. **Binance Testnet**: https://testnet.binance.vision/
4. **Binance Real**: https://www.binance.com/
5. **Telegram**: https://my.telegram.org/

---

**Готово! Теперь у тебя есть все API ключи! 🚀**

