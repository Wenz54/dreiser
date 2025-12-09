# 🔑 КАК ПОЛУЧИТЬ И ВСТАВИТЬ API КЛЮЧИ

## 📋 **ЧТО НУЖНО:**

Для работы бота нужны API ключи от 4 бирж. **Для начала** используй **TESTNET** (тестовые ключи - без реальных денег)!

---

## 🎯 **ГДЕ ВСТАВЛЯТЬ:**

Открой файл: **`backend/c_engine/config/engine.json`**

Найди строки с `═══ ВСТАВЬ СЮДА ═══` и замени их на свои ключи!

---

## 🏦 **1. BINANCE**

### Testnet (РЕКОМЕНДУЕТСЯ ДЛЯ НАЧАЛА)
1. Открой: https://testnet.binance.vision/
2. Нажми **"Log in with GitHub"**
3. Перейди в **"API Keys"** → **"Generate HMAC_SHA256 Key"**
4. Скопируй:
   - **API Key** → вставь в `binance.testnet.api_key`
   - **Secret Key** → вставь в `binance.testnet.api_secret`

### Real Trading (ТОЛЬКО ДЛЯ ОПЫТНЫХ)
1. Открой: https://www.binance.com/en/my/settings/api-management
2. Создай новый API ключ
3. **ВАЖНО:** Включи только **"Enable Spot & Margin Trading"**
4. **WHITELIST:** Добавь IP адрес своего сервера
5. Скопируй ключи в `binance.api_key` и `binance.api_secret`

---

## 🏦 **2. MEXC**

### Real Trading
1. Открой: https://www.mexc.com/user/openapi
2. Нажми **"Create API"**
3. Включи **"Spot Trading"**
4. Скопируй:
   - **API Key** → вставь в `mexc.api_key`
   - **Secret Key** → вставь в `mexc.api_secret`

**Note:** MEXC не имеет testnet, но можно создать аккаунт с минимальным балансом ($10-20) для тестов.

---

## 🏦 **3. BYBIT**

### Testnet (РЕКОМЕНДУЕТСЯ)
1. Открой: https://testnet.bybit.com/
2. Зарегистрируйся через email
3. Получи тестовые 100 BTC, 100 ETH, 100 USDT на баланс
4. Перейди: **API Keys** → **Create New Key**
5. Включи **"Unified Trading Account"**
6. Скопируй ключи в `bybit.testnet.api_key` и `bybit.testnet.api_secret`

### Real Trading
1. Открой: https://www.bybit.com/app/user/api-management
2. Создай новый API ключ
3. Включи **"Spot"**
4. Whitelist IP
5. Скопируй ключи

---

## 🏦 **4. OKX**

### Testnet (Demo Trading)
1. Открой: https://www.okx.com/account/my-api
2. Включи **"Demo Trading"** mode
3. Создай API ключ
4. **ВАЖНО:** OKX требует **API Passphrase** (придумай сам, 8-32 символа)
5. Скопируй:
   - **API Key** → `okx.testnet.api_key`
   - **Secret Key** → `okx.testnet.api_secret`
   - **Passphrase** → `okx.testnet.api_passphrase`

### Real Trading
1. Открой: https://www.okx.com/account/my-api
2. Создай новый API ключ
3. Включи **"Trade"**
4. Установи Passphrase
5. Whitelist IP
6. Скопируй ключи

---

## 📝 **ПРИМЕР ЗАПОЛНЕНИЯ:**

### До:
```json
{
  "exchanges": {
    "binance": {
      "testnet": {
        "api_key": "═══ TESTNET KEY ЗДЕСЬ ═══",
        "api_secret": "═══ TESTNET SECRET ЗДЕСЬ ═══"
      }
    }
  }
}
```

### После:
```json
{
  "exchanges": {
    "binance": {
      "testnet": {
        "api_key": "abc123def456ghi789jklmnopqrstuvwxyz",
        "api_secret": "xyz987wvu654tsr321qponmlkjihgfedcba"
      }
    }
  }
}
```

---

## ⚠️ **ВАЖНЫЕ ПРАВИЛА:**

### 1. Никогда не коммить ключи в Git!
```bash
# Проверь перед коммитом:
git diff backend/c_engine/config/engine.json

# Если там реальные ключи - НЕ КОММИТЬ!
```

### 2. Ограничь права API ключей
- ✅ Включи только **Spot Trading**
- ❌ НЕ включай **Withdrawals** (снятие средств)
- ✅ Whitelist IP (если возможно)
- ✅ Установи лимиты (daily limits)

### 3. Используй Testnet для разработки
- Testnet = виртуальные деньги
- Real = настоящие деньги
- **ВСЕГДА** тестируй на testnet сначала!

### 4. Храни ключи безопасно
```bash
# Скопируй конфиг в безопасное место:
cp backend/c_engine/config/engine.json ~/my_secure_keys.json

# И добавь в .gitignore:
echo "backend/c_engine/config/engine.json" >> .gitignore
```

---

## 🚀 **БЫСТРЫЙ СТАРТ (TESTNET):**

1. **Binance Testnet:**
   - https://testnet.binance.vision/ → Log in → API Keys → Generate

2. **Bybit Testnet:**
   - https://testnet.bybit.com/ → Register → API Keys → Create

3. **MEXC Real (минимальный баланс):**
   - https://www.mexc.com/user/openapi → Create API → Spot Trading

4. **OKX Demo:**
   - https://www.okx.com/account/my-api → Demo Trading → Create

5. **Вставь все ключи в `engine.json`**

6. **Запусти бота:**
```bash
cd backend/c_engine/build
./draizer_engine
```

---

## ✅ **CHECKLIST:**

- [ ] Binance testnet ключи получены
- [ ] Bybit testnet ключи получены  
- [ ] MEXC ключи получены
- [ ] OKX demo ключи получены
- [ ] Все ключи вставлены в `engine.json`
- [ ] Права ограничены (только Spot Trading)
- [ ] IP whitelist настроен (если возможно)
- [ ] `engine.json` добавлен в `.gitignore`
- [ ] Бот успешно запустился

---

## 📞 **ПРОБЛЕМЫ?**

### "API key invalid"
- Проверь: копировал без пробелов?
- Проверь: не истёк срок действия?
- Проверь: включен Spot Trading?

### "IP not whitelisted"
- Узнай свой IP: `curl ifconfig.me`
- Добавь в whitelist на бирже

### "Insufficient permissions"
- Включи Spot Trading в настройках API ключа

---

**ГОТОВО!** Теперь у тебя есть все 4 ключа для тестов! 🚀


