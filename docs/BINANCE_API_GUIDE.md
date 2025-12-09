# 🔑 Binance API - Полное руководство

## 📋 ДВА ВАРИАНТА

### Вариант A: Testnet (РЕКОМЕНДУЮ ДЛЯ НАЧАЛА) ⭐

**Плюсы**:
- ✅ **Бесплатно**
- ✅ Без верификации (KYC)
- ✅ Реальные цены BTC/USDT
- ✅ Получить ключи за 30 секунд

**Минусы**:
- ⚠️ Тестовые данные (иногда могут быть задержки)

---

## 🚀 КАК ПОЛУЧИТЬ (Testnet - 30 секунд)

### Шаг 1: Открой

```
https://testnet.binance.vision/
```

### Шаг 2: Generate Key

Прямо на главной странице увидишь:

```
┌─────────────────────────────────────┐
│  Generate HMAC_SHA256 Key           │
│                                     │
│  [Generate Key Button]              │
└─────────────────────────────────────┘
```

Нажми **"Generate HMAC_SHA256 Key"**

### Шаг 3: Скопируй ключи

Получишь:

```
API Key: 
abc123def456ghi789jkl012mno345pqr678stu901vwx234yz

Secret Key:
XYZ789abc012def345ghi678jkl901mno234pqr567stu890vwx123yz
```

⚠️ **ВАЖНО**: Скопируй **ОБА** ключа сразу! Secret показывается один раз!

### Шаг 4: Заполни в .env

```env
BINANCE_API_KEY=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
BINANCE_API_SECRET=XYZ789abc012def345ghi678jkl901mno234pqr567stu890vwx123yz
BINANCE_USE_TESTNET=true
```

### Шаг 5: Готово! ✅

Testnet API работает сразу, никакой регистрации не нужно!

---

## 🏦 Вариант B: Real Binance (для Production)

**Когда нужен**:
- Полные данные
- Production environment
- 100% uptime

**Минусы**:
- Нужна регистрация
- KYC верификация (документы)
- Занимает 10-30 минут

---

## 📝 КАК ПОЛУЧИТЬ (Real Binance)

### Шаг 1: Регистрация

```
https://www.binance.com/en/register
```

- Email или телефон
- Придумай пароль
- Подтверди email/SMS

### Шаг 2: Верификация (KYC)

```
Profile → Identity Verification
```

Загрузи:
- Паспорт или ID
- Селфи
- Proof of address (опционально)

⏱️ Занимает: 10-30 минут (обычно быстро)

### Шаг 3: API Management

```
Profile → API Management
https://www.binance.com/en/my/settings/api-management
```

### Шаг 4: Create API Key

1. Нажми **"Create API"**
2. Label: `Draizer Trading Bot`
3. **API restrictions**:
   - ✅ **Enable Reading** ← ВКЛЮЧИ!
   - ❌ Enable Spot & Margin Trading ← НЕ ВКЛЮЧАЙ!
   - ❌ Enable Futures ← НЕ ВКЛЮЧАЙ!
   - ❌ Enable Withdrawals ← НИКОГДА!

⚠️ **БЕЗОПАСНОСТЬ**: Включи ТОЛЬКО "Enable Reading"!

### Шаг 5: 2FA Verification

Введи код из Google Authenticator или SMS

### Шаг 6: Скопируй ключи

```
API Key: abc123...
Secret Key: xyz789...
```

⚠️ Secret показывается только ОДИН раз!

### Шаг 7: IP Whitelist (опционально, но рекомендуется)

```
Edit API → IP Whitelist → Add your server IP
```

Узнать свой IP:
```bash
curl ifconfig.me
```

### Шаг 8: Заполни в .env

```env
BINANCE_API_KEY=твой_real_api_key
BINANCE_API_SECRET=твой_real_secret
BINANCE_USE_TESTNET=false  # ← FALSE для real API!
```

---

## 🔒 БЕЗОПАСНОСТЬ (КРИТИЧНО!)

### ✅ ПРАВИЛЬНО:

```
API Restrictions:
✅ Enable Reading        ← ТОЛЬКО ЭТО!
❌ Enable Trading        ← НЕТ!
❌ Enable Withdrawals    ← НИКОГДА!
✅ IP Whitelist          ← Рекомендуется
```

### ❌ НЕПРАВИЛЬНО:

```
❌ Enable Trading        ← НЕ ВКЛЮЧАЙ!
❌ Enable Withdrawals    ← ОПАСНО!
❌ No IP Whitelist       ← Небезопасно
```

**Мы НЕ торгуем реально** - нам нужны только данные!

---

## 🧪 ПРОВЕРКА РАБОТЫ

### Через curl (Testnet):

```bash
curl "https://testnet.binance.vision/api/v3/ticker/price?symbol=BTCUSDT"
```

Ожидается:
```json
{"symbol":"BTCUSDT","price":"43521.50000000"}
```

### Через curl (Real):

```bash
curl "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
```

### Через Python тест:

```bash
# Установи переменные
export BINANCE_API_KEY=твой_ключ
export BINANCE_API_SECRET=твой_секрет

# Запусти тест
python test_api_access.py
```

---

## 📊 КАКИЕ ДАННЫЕ МЫ ПОЛУЧАЕМ

### 1. Ticker Price (текущая цена):

```python
# GET /api/v3/ticker/price?symbol=BTCUSDT
{
  "symbol": "BTCUSDT",
  "price": "43521.50"
}
```

### 2. 24h Ticker (статистика):

```python
# GET /api/v3/ticker/24hr?symbol=BTCUSDT
{
  "symbol": "BTCUSDT",
  "priceChange": "+1250.50",
  "priceChangePercent": "2.98",
  "highPrice": "44000.00",
  "lowPrice": "42000.00",
  "volume": "25431.50",
  ...
}
```

### 3. Klines (свечи):

```python
# GET /api/v3/klines?symbol=BTCUSDT&interval=15m&limit=100
[
  [
    1633024800000,    // Open time
    "43000.00",       // Open
    "43500.00",       // High
    "42800.00",       // Low
    "43200.00",       // Close
    "1250.50",        // Volume
    ...
  ],
  ...
]
```

### 4. Order Book (книга заявок):

```python
# GET /api/v3/depth?symbol=BTCUSDT&limit=10
{
  "bids": [
    ["43000.00", "1.50"],  // [price, quantity]
    ["42999.00", "2.30"],
    ...
  ],
  "asks": [
    ["43001.00", "1.20"],
    ["43002.00", "3.40"],
    ...
  ]
}
```

---

## 🔄 ПЕРЕКЛЮЧЕНИЕ Testnet ↔ Real

### В .env:

```env
# Testnet:
BINANCE_USE_TESTNET=true

# Real:
BINANCE_USE_TESTNET=false
```

### В коде (автоматически):

```python
# backend/app/services/binance_service.py

if settings.BINANCE_TESTNET:
    base_url = "https://testnet.binance.vision"
else:
    base_url = "https://api.binance.com"
```

---

## 🆘 TROUBLESHOOTING

### Error: "Invalid API key"

**Причины**:
1. Неправильно скопировал ключ
2. Лишние пробелы в начале/конце
3. Testnet ключ с Real API (или наоборот)

**Решение**:
```bash
# Проверь .env:
cat .env | grep BINANCE

# Убери пробелы:
BINANCE_API_KEY=abc123  # ← Без пробелов!
```

### Error: "Timestamp for this request is outside of the recvWindow"

**Причина**: Системное время неправильное

**Решение**:
```bash
# Windows:
w32tm /resync

# Linux:
sudo ntpdate pool.ntp.org
```

### Error: "IP address is not in whitelist"

**Причина**: Настроен IP whitelist, но твой IP не в нем

**Решение**:
1. Binance API Management → Edit API
2. IP Whitelist → Add current IP
3. Узнать IP: `curl ifconfig.me`

### Error: Connection timeout

**Причина**: Нет интернета или Binance down

**Решение**:
```bash
# Проверь доступность:
ping api.binance.com

# Или:
curl https://api.binance.com/api/v3/ping
```

---

## 💰 RATE LIMITS

### Testnet:
- 1200 requests/minute
- Достаточно для нашего проекта!

### Real Binance:
- 1200 requests/minute (weight-based)
- Более строгие лимиты для некоторых endpoints

**Наше использование**: ~4-10 requests/minute
✅ Полностью в пределах лимитов!

---

## 📚 ПОЛЕЗНЫЕ ССЫЛКИ

- **Testnet**: https://testnet.binance.vision/
- **Real API**: https://www.binance.com/
- **API Docs**: https://binance-docs.github.io/apidocs/spot/en/
- **Status**: https://www.binance.com/en/support/announcement

---

## ✅ CHECKLIST

Перед запуском проекта:

```
✅ Получил Binance API ключи (testnet или real)
✅ Заполнил BINANCE_API_KEY в .env
✅ Заполнил BINANCE_API_SECRET в .env
✅ Установил BINANCE_USE_TESTNET=true (для testnet)
✅ Включил ТОЛЬКО "Enable Reading" (для real)
✅ Протестировал через curl или test_api_access.py
```

---

**Готово! Binance API настроен! 🚀**

**Рекомендация**: Начни с **Testnet** (30 секунд), протестируй проект, потом переключись на Real если нужно.

