# Техническое задание: AI Trading Platform (Draizer)

## 1. Описание проекта

**Draizer** - революционная платформа AI-торговли на криптовалютной бирже с виртуальным тестированием стратегий.

### Цель MVP
Создать **ИМИТАЦИОННУЮ** систему для проверки работоспособности AI-трейдинга с виртуальным балансом.

⚠️ **ВАЖНО: ЭТО ПОЛНОСТЬЮ ВИРТУАЛЬНАЯ СИМУЛЯЦИЯ**
- НЕТ реальных денег
- НЕТ реальных сделок на бирже
- Используются РЕАЛЬНЫЕ цены с Binance, но сделки ИМИТИРУЮТСЯ
- Цель: тестирование AI стратегий без финансового риска

### Основной функционал (имитация)
- AI (DeepSeek) анализирует РЕАЛЬНЫЕ рыночные данные Binance
- Принимает решения о ВИРТУАЛЬНЫХ покупках/продажах
- Система ИМИТИРУЕТ исполнение сделок по текущим ценам
- Рассчитывает виртуальную прибыль/убыток
- Отображает статистику через веб-интерфейс
- Экспорт статистики в .md формате

## 2. Технический стек

### Backend
- **Язык**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **БД**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Миграции**: Alembic
- **Асинхронность**: asyncio, asyncpg
- **Кэширование**: Redis 7+
- **Валидация**: Pydantic v2

### Frontend
- **Framework**: React 18+
- **Язык**: TypeScript 5+
- **UI**: Material-UI (MUI) v5
- **State**: Redux Toolkit + RTK Query
- **Charts**: Recharts / TradingView Lightweight Charts
- **Build**: Vite

### Infrastructure
- **Контейнеризация**: Docker + Docker Compose
- **Proxy**: Nginx (reverse proxy, SSL termination)
- **Secrets**: Environment variables (dev), HashiCorp Vault (prod)

### External APIs
- **Binance API**: WebSocket + REST (testnet для разработки)
- **DeepSeek API**: LLM для самостоятельного анализа и принятия торговых решений
- **OpenAI API**: GPT-4 для аналитического чата и объяснения результатов

## 3. Требования безопасности (банковский уровень)

### 3.1 Аутентификация и авторизация
- JWT токены (access + refresh)
- Access token TTL: 15 минут
- Refresh token TTL: 7 дней, хранится в httpOnly cookie
- Обязательная 2FA/MFA (TOTP)
- Device fingerprinting
- IP whitelist для критичных операций
- Автоматический logout при бездействии

### 3.2 Шифрование
- **In Transit**: TLS 1.3 (только), HTTPS принудительно
- **At Rest**: 
  - Пароли: Argon2id (память 64MB, iterations 3, parallelism 4)
  - API ключи: AES-256-GCM с индивидуальными ключами
  - Персональные данные: AES-256-GCM
  - Database: PostgreSQL шифрование на уровне таблиц

### 3.3 Защита API
- Rate limiting: 100 req/min общий, 10 req/min для auth
- Request signing (HMAC-SHA256)
- API versioning (/api/v1/)
- Strict CORS policy
- Request size limits (10MB max)
- Timeout protection (30s max)

### 3.4 База данных
- PostgreSQL Row-Level Security (RLS)
- Prepared statements (100% покрытие)
- Connection pooling с ограничениями
- Отдельные пользователи БД для сервисов (read-only где возможно)
- Encrypted backups
- Audit logging всех изменений

### 3.5 Мониторинг и аудит
- Полное логирование всех действий пользователей
- Детекция аномалий:
  - Необычные паттерны входа
  - Подозрительная торговая активность
  - Резкие изменения баланса
- Failed login tracking (блокировка после 5 попыток)
- Real-time alerts на критичные события
- Хранение логов: 1 год минимум

### 3.6 Frontend Security
- Content Security Policy (CSP) headers
- XSS protection (sanitization всех inputs)
- CSRF tokens
- Secure token storage (не в localStorage!)
- Subresource Integrity (SRI)
- No sensitive data in Redux state

### 3.7 OWASP Top 10 Protection
- ✅ Broken Access Control: RBAC + RLS
- ✅ Cryptographic Failures: AES-256, Argon2id
- ✅ Injection: ORM + validation
- ✅ Insecure Design: Security by design
- ✅ Security Misconfiguration: Automated checks
- ✅ Vulnerable Components: Dependency scanning
- ✅ Authentication Failures: MFA + strong policies
- ✅ Software Integrity Failures: Signed releases
- ✅ Logging Failures: Comprehensive audit logs
- ✅ SSRF: Input validation + network isolation

## 4. Архитектура системы

### 4.1 Компоненты

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTPS
┌──────▼──────┐
│    Nginx    │ ← SSL/TLS, Rate Limiting, WAF
└──────┬──────┘
       │
┌──────▼──────────┐
│  React Frontend │ ← SPA, TypeScript
└──────┬──────────┘
       │ REST API + WebSocket
┌──────▼──────────┐
│  FastAPI Backend│ ← Python, JWT Auth
└─┬─┬─┬─┬────────┘
  │ │ │ │
  │ │ │ └──────────┐
  │ │ │            │
  │ │ └────┐   ┌───▼────────┐
  │ │      │   │   Redis    │ ← Rate Limit, Cache, Sessions
  │ │  ┌───▼───▼────────────┐
  │ │  │   PostgreSQL       │ ← Data Storage, RLS
  │ │  └────────────────────┘
  │ │
  │ └───► Binance API (WebSocket + REST)
  │
  └─────► DeepSeek API (LLM)
```

### 4.2 Микросервисная готовность
Монолит на старте, но с четким разделением:
- **Auth Service**: Аутентификация, MFA
- **Trading Service**: Логика торговли
- **AI Service**: Интеграция с DeepSeek
- **Market Service**: Binance интеграция
- **Portfolio Service**: Управление балансами
- **Notification Service**: Alerts, emails

## 5. Модель данных

### 5.1 Таблицы PostgreSQL

#### users
```sql
- id: UUID PRIMARY KEY
- email: VARCHAR(255) UNIQUE NOT NULL (encrypted)
- username: VARCHAR(50) UNIQUE NOT NULL
- password_hash: VARCHAR(255) NOT NULL (Argon2id)
- mfa_secret: VARCHAR(255) ENCRYPTED
- mfa_enabled: BOOLEAN DEFAULT FALSE
- is_active: BOOLEAN DEFAULT TRUE
- is_verified: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- last_login: TIMESTAMP
```

#### portfolios
```sql
- id: UUID PRIMARY KEY
- user_id: UUID FK (users) NOT NULL
- balance_usd: DECIMAL(20, 8) DEFAULT 1000.00
- initial_balance: DECIMAL(20, 8) DEFAULT 1000.00
- total_pnl: DECIMAL(20, 8) DEFAULT 0.00
- total_trades: INTEGER DEFAULT 0
- winning_trades: INTEGER DEFAULT 0
- losing_trades: INTEGER DEFAULT 0
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### positions
```sql
- id: UUID PRIMARY KEY
- portfolio_id: UUID FK (portfolios) NOT NULL
- symbol: VARCHAR(20) NOT NULL (e.g., 'BTCUSDT')
- quantity: DECIMAL(20, 8) NOT NULL
- entry_price: DECIMAL(20, 8) NOT NULL
- current_price: DECIMAL(20, 8)
- unrealized_pnl: DECIMAL(20, 8)
- opened_at: TIMESTAMP
- is_closed: BOOLEAN DEFAULT FALSE
```

#### transactions
```sql
- id: UUID PRIMARY KEY
- portfolio_id: UUID FK (portfolios) NOT NULL
- position_id: UUID FK (positions) NULLABLE
- type: ENUM('BUY', 'SELL') NOT NULL
- symbol: VARCHAR(20) NOT NULL
- quantity: DECIMAL(20, 8) NOT NULL
- price: DECIMAL(20, 8) NOT NULL
- total_value: DECIMAL(20, 8) NOT NULL
- fee: DECIMAL(20, 8) DEFAULT 0
- pnl: DECIMAL(20, 8) NULLABLE (только для SELL)
- ai_decision_id: UUID FK (ai_decisions)
- executed_at: TIMESTAMP
- metadata: JSONB (дополнительные данные)
```

#### ai_decisions
```sql
- id: UUID PRIMARY KEY
- portfolio_id: UUID FK (portfolios) NOT NULL
- decision_type: ENUM('BUY', 'SELL', 'HOLD') NOT NULL
- symbol: VARCHAR(20) NOT NULL
- confidence: DECIMAL(5, 2) (0-100%)
- reasoning: TEXT (объяснение от AI)
- market_data: JSONB (snapshot рынка)
- model_version: VARCHAR(50)
- processing_time_ms: INTEGER
- executed: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP
```

#### market_data_cache
```sql
- id: BIGSERIAL PRIMARY KEY
- symbol: VARCHAR(20) NOT NULL
- price: DECIMAL(20, 8) NOT NULL
- volume_24h: DECIMAL(20, 8)
- change_24h: DECIMAL(10, 4)
- high_24h: DECIMAL(20, 8)
- low_24h: DECIMAL(20, 8)
- timestamp: TIMESTAMP
- INDEX on (symbol, timestamp)
```

#### audit_logs
```sql
- id: BIGSERIAL PRIMARY KEY
- user_id: UUID FK (users) NULLABLE
- action: VARCHAR(100) NOT NULL
- resource: VARCHAR(100)
- ip_address: INET
- user_agent: TEXT
- request_data: JSONB
- response_status: INTEGER
- created_at: TIMESTAMP
- INDEX on (user_id, created_at)
- INDEX on (action, created_at)
```

#### security_events
```sql
- id: BIGSERIAL PRIMARY KEY
- user_id: UUID FK (users) NULLABLE
- event_type: VARCHAR(50) NOT NULL (FAILED_LOGIN, MFA_FAILED, etc.)
- severity: ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
- ip_address: INET
- details: JSONB
- resolved: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP
```

#### chat_messages
```sql
- id: UUID PRIMARY KEY
- user_id: UUID FK (users) NOT NULL
- role: ENUM('user', 'assistant', 'system') NOT NULL
- content: TEXT NOT NULL
- context_data: JSONB (portfolio snapshot, market data при запросе)
- tokens_used: INTEGER
- model: VARCHAR(50) DEFAULT 'gpt-4'
- created_at: TIMESTAMP
- INDEX on (user_id, created_at)
```

## 6. API Endpoints

### 6.1 Authentication
```
POST   /api/v1/auth/register        - Регистрация
POST   /api/v1/auth/login           - Логин (возвращает access + refresh)
POST   /api/v1/auth/logout          - Логаут
POST   /api/v1/auth/refresh         - Обновление access token
POST   /api/v1/auth/verify-email    - Верификация email
POST   /api/v1/auth/mfa/setup       - Настройка 2FA
POST   /api/v1/auth/mfa/verify      - Верификация 2FA кода
POST   /api/v1/auth/password-reset  - Сброс пароля
```

### 6.2 Portfolio
```
GET    /api/v1/portfolio            - Получить портфель
GET    /api/v1/portfolio/stats      - Статистика (win rate, PnL и т.д.)
GET    /api/v1/portfolio/positions  - Текущие позиции
GET    /api/v1/portfolio/export-md  - Экспорт статистики торгов в .md формате
```

### 6.3 Trading
```
GET    /api/v1/trading/history      - История сделок
GET    /api/v1/trading/transactions - Все транзакции
POST   /api/v1/trading/manual-trade - Ручная сделка (для тестов)
```

### 6.4 AI
```
POST   /api/v1/ai/analyze           - Запустить AI анализ
GET    /api/v1/ai/decisions         - История решений AI
GET    /api/v1/ai/decision/:id      - Детали решения
POST   /api/v1/ai/start-bot         - Запустить AI бота (авто-режим)
POST   /api/v1/ai/stop-bot          - Остановить бота
GET    /api/v1/ai/bot-status        - Статус бота
```

### 6.5 Market Data
```
GET    /api/v1/market/price/:symbol - Текущая цена
GET    /api/v1/market/candles/:symbol - OHLCV данные
WS     /api/v1/market/ws            - WebSocket для real-time цен
```

### 6.6 User
```
GET    /api/v1/user/profile         - Профиль пользователя
PATCH  /api/v1/user/profile         - Обновить профиль
GET    /api/v1/user/security-log    - Лог безопасности
```

### 6.7 AI Chat (GPT-4)
```
POST   /api/v1/chat/message         - Отправить сообщение в аналитический чат
GET    /api/v1/chat/history         - История чата
POST   /api/v1/chat/analyze-portfolio - Запросить анализ портфеля от GPT
POST   /api/v1/chat/explain-decision - Объяснить конкретное решение AI
DELETE /api/v1/chat/clear           - Очистить историю чата
```

## 7. AI Trading Logic

### 7.1 Процесс принятия решений

```
1. Получение данных
   ├─ Текущая цена (Binance WebSocket)
   ├─ OHLCV данные (последние 100 свечей, 15m интервал)
   ├─ Объем торгов 24h
   ├─ Moving averages (MA7, MA25, MA99)
   └─ RSI, MACD (опционально)

2. Формирование промпта для DeepSeek
   ├─ Системный промпт (роль трейдера)
   ├─ Контекст рынка (форматированные данные)
   ├─ Текущие позиции пользователя
   ├─ Доступный баланс
   └─ Запрос решения (BUY/SELL/HOLD)

3. Анализ DeepSeek
   ├─ Отправка запроса к API
   ├─ Получение структурированного ответа
   │   {
   │     "decision": "BUY" | "SELL" | "HOLD",
   │     "confidence": 0-100,
   │     "reasoning": "текст объяснения",
   │     "suggested_amount": USD value
   │   }
   └─ Валидация ответа

4. ИМИТАЦИЯ исполнения решения
   ├─ Если BUY:
   │   ├─ Проверка виртуального баланса
   │   ├─ Получение текущей цены Binance (реальной)
   │   ├─ ВИРТУАЛЬНЫЙ расчет количества монет
   │   ├─ Создание записи в transactions (BUY) - имитация
   │   ├─ Создание/обновление position - виртуальная позиция
   │   ├─ ВИРТУАЛЬНОЕ списание USD с баланса
   │   └─ Запись в ai_decisions
   │
   ├─ Если SELL:
   │   ├─ Проверка наличия виртуальной позиции
   │   ├─ Получение текущей цены Binance (реальной)
   │   ├─ ВИРТУАЛЬНЫЙ расчет P&L (current_price - entry_price) * quantity
   │   ├─ Создание записи в transactions (SELL) - имитация
   │   ├─ Закрытие виртуальной position
   │   ├─ ВИРТУАЛЬНОЕ начисление USD на баланс
   │   ├─ Обновление статистики (winning/losing trades)
   │   └─ Запись в ai_decisions
   │
   └─ Если HOLD:
       └─ Только запись в ai_decisions

⚠️ ВАЖНО: Все операции ВИРТУАЛЬНЫЕ, реальных сделок на бирже НЕТ!

5. Логирование
   ├─ Audit log
   ├─ Application log
   └─ Notification (опционально)
```

### 7.2 Промпт для DeepSeek (самостоятельный анализ)

```
System: You are an autonomous cryptocurrency trading AI with FULL decision-making authority.
You must independently analyze market data, identify patterns, assess risks, and make trading decisions.
Do NOT follow rigid templates. Think critically and adapt your strategy based on market conditions.

Your responsibilities:
1. Deep market analysis (trends, momentum, volatility, support/resistance)
2. Risk assessment for each trade
3. Position sizing based on confidence and market conditions
4. Capital preservation (never risk more than 10% of balance per trade)
5. Adaptive strategy - change approach based on what's working

Raw Market Data:
- Current BTC/USDT price: ${current_price}
- Previous prices (last 100 candles, 15min): ${price_history}
- 24h high: ${high_24h}, 24h low: ${low_24h}
- 24h volume: ${volume_24h}
- 24h change: ${change_24h}%
- Order book depth (top 10 bids/asks): ${orderbook_data}

Technical Indicators (calculate more if needed):
- MA7: ${ma7}, MA25: ${ma25}, MA99: ${ma99}
- RSI(14): ${rsi}
- MACD: ${macd}
- Bollinger Bands: ${bb_upper}, ${bb_middle}, ${bb_lower}

Your Current State:
- Available USD balance: ${balance_usd}
- Current position: ${position_status}
- Entry price (if holding): ${entry_price}
- Unrealized P&L: ${unrealized_pnl}
- Total trades: ${total_trades}
- Win rate: ${win_rate}%
- Total P&L: ${total_pnl}

Recent Performance:
- Last 10 trades summary: ${recent_trades}
- Best trade: ${best_trade}
- Worst trade: ${worst_trade}

Task: Analyze the market independently and make a trading decision.

Think through:
1. What is the current market regime? (trending/ranging/volatile)
2. What patterns do you see in price action?
3. What are the key support/resistance levels?
4. What is the risk/reward ratio of potential trades?
5. How confident are you in this analysis?
6. What could go wrong? (risk factors)
7. Based on YOUR analysis - should you BUY, SELL, or HOLD?

Respond in JSON format:
{
  "market_analysis": {
    "regime": "trending_up" | "trending_down" | "ranging" | "volatile",
    "key_levels": {
      "resistance": [price1, price2],
      "support": [price1, price2]
    },
    "sentiment": "bullish" | "bearish" | "neutral",
    "patterns_identified": ["pattern1", "pattern2"]
  },
  "decision": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100,
  "reasoning": "Detailed explanation of WHY this decision (200-300 chars)",
  "risk_assessment": {
    "risk_level": "low" | "medium" | "high",
    "stop_loss": price (if applicable),
    "take_profit": price (if applicable),
    "risk_reward_ratio": number
  },
  "position_sizing": {
    "suggested_amount_usd": number,
    "percentage_of_balance": number (1-10%)
  },
  "alternative_scenarios": {
    "if_wrong": "What happens if this trade goes against you",
    "exit_plan": "When and how to exit"
  }
}

Rules:
1. THINK INDEPENDENTLY - don't just follow indicators blindly
2. Adapt your strategy - if losing, change approach
3. Capital preservation is priority #1
4. Only trade when you have STRONG conviction (confidence > 70%)
5. Consider transaction costs and slippage
6. Learn from past performance - adjust strategy accordingly
7. If uncertain (confidence < 70%) - choose HOLD
8. Maximum position size: 10% of balance per trade
9. Never average down on losing positions
10. Cut losses quickly, let winners run

IMPORTANT: Your decisions directly impact user's virtual balance. Trade wisely.
```

### 7.3 Обновление виртуального баланса (ИМИТАЦИЯ)

**Механика симуляции:**

1. **При BUY решении (ВИРТУАЛЬНАЯ покупка):**
   ```python
   # ИМИТАЦИЯ: Вычитаем из виртуального баланса
   portfolio.balance_usd -= total_value
   
   # ИМИТАЦИЯ: Создаем/обновляем виртуальную позицию
   position.quantity += bought_quantity
   position.entry_price = weighted_average_price
   position.is_simulated = True  # Флаг симуляции
   
   # Записываем транзакцию
   transaction.type = 'BUY'
   transaction.total_value = total_value
   transaction.is_simulated = True  # Это НЕ реальная сделка
   transaction.simulated_price = current_binance_price  # Реальная цена для симуляции
   ```

2. **При SELL решении (ВИРТУАЛЬНАЯ продажа):**
   ```python
   # ИМИТАЦИЯ: Рассчитываем виртуальный P&L
   pnl = (current_price - entry_price) * quantity
   
   # ИМИТАЦИЯ: Начисляем на виртуальный баланс
   portfolio.balance_usd += (entry_value + pnl)
   
   # Обновляем статистику симуляции
   portfolio.total_pnl += pnl
   if pnl > 0:
       portfolio.winning_trades += 1
   else:
       portfolio.losing_trades += 1
   
   # Закрываем виртуальную позицию
   position.is_closed = True
   
   # Записываем транзакцию
   transaction.type = 'SELL'
   transaction.pnl = pnl
   transaction.is_simulated = True  # Это НЕ реальная сделка
   ```

3. **Вычет комиссии (с виртуальной прибыли):**
   ```python
   # Комиссия берется с ВИРТУАЛЬНОЙ прибыли при продаже
   if transaction.type == 'SELL' and pnl > 0:
       fee = pnl * user_plan.commission_rate  # 35%, 25%, 15%, 7%
       portfolio.balance_usd -= fee
       transaction.fee = fee
       
       # Записываем в отдельную таблицу для отчетности
       platform_revenue.amount += fee
       platform_revenue.is_simulated = True  # Виртуальный доход
   ```

4. **Отображение баланса (после комиссии):**
   ```python
   # Frontend всегда видит чистый виртуальный баланс
   displayed_balance = portfolio.balance_usd  # УЖЕ после комиссии
   
   # Детали комиссии доступны в Settings → Billing
   ```

⚠️ **КРИТИЧЕСКИ ВАЖНО**: 
- Все операции происходят ТОЛЬКО в базе данных
- НИ ОДИН API запрос к Binance для размещения ордеров НЕ делается
- Используются только РЕАЛЬНЫЕ цены для расчета виртуальных результатов
- Это paper trading / backtesting в реальном времени

## 8. GPT-4 Аналитический чат

### 8.1 Назначение

GPT-4 чат предоставляет пользователю:
- Объяснение решений DeepSeek понятным языком
- Анализ портфеля и рекомендации
- Ответы на вопросы о торговле
- Обучающий контент

**Важно:** GPT-4 НЕ принимает торговые решения, только анализирует и объясняет.

### 8.2 Промпт для GPT-4 (аналитик)

```
System: You are a friendly financial advisor and trading analyst for Draizer AI Trading Platform.
Your role is to help users understand their portfolio performance and AI trading decisions.

Guidelines:
1. Explain trading concepts in simple, accessible language
2. Provide insights into why DeepSeek AI made certain decisions
3. Help users understand market movements
4. Give educational content about trading
5. Be encouraging but realistic about trading risks
6. Never give financial advice - only educational information
7. Always mention that results are from virtual trading

User Context:
- Portfolio balance: ${balance}
- Total P&L: ${total_pnl} (${pnl_percentage}%)
- Win rate: ${win_rate}%
- Total trades: ${total_trades}
- Current position: ${position_status}
- User plan: ${user_plan}
- Days on platform: ${days_active}

Recent Activity:
- Last 5 trades: ${recent_trades}
- Last AI decision: ${last_decision}

Available Commands:
- User can ask: "Why did AI buy/sell?"
- User can ask: "How is my portfolio doing?"
- User can ask: "What does [trading term] mean?"
- User can ask: "What should I do now?" (answer: it's virtual, let AI work)

Response Style:
- Conversational and friendly
- Use emojis sparingly (1-2 per message)
- Keep responses under 200 words unless detailed explanation needed
- Provide actionable insights when possible
- Encourage long-term perspective

Example Responses:

Q: "Why did the AI buy just now?"
A: "The AI detected a bullish pattern 📈 - BTC price broke above the MA25 with strong volume. 
   The decision had 82% confidence based on:
   • Price momentum turning positive
   • RSI showing oversold recovery
   • Support holding at $43,200
   
   The AI risked 5% of balance ($50) because the risk/reward ratio was favorable (1:3).
   
   Remember: This is virtual trading to test the strategy. Let's see how it plays out! 🎯"

Q: "How am I doing?"
A: "Your portfolio is up $285 (28.5%)! 🎉
   
   Stats breakdown:
   • 12 trades total
   • 8 wins, 4 losses (67% win rate)
   • Best trade: +$85 on BTC
   • Current position: Holding 0.0023 BTC
   
   The AI is being cautious, which is good. It's only trading when confidence > 70%.
   
   Keep in mind: Crypto markets are volatile. Past performance ≠ future results. 📊"

IMPORTANT: You are an analyst, NOT a trader. You explain, don't execute.
```

### 8.3 Интеграция GPT чата в интерфейс

**UI Components:**

```
┌─────────────────────────────────────┐
│  💬 AI Trading Assistant            │
│  ─────────────────────────────────  │
│                                     │
│  👤 You: How is my portfolio?       │
│                                     │
│  🤖 Assistant: Your portfolio is    │
│     up $285 (28.5%)! 🎉            │
│     [detailed stats...]             │
│                                     │
│  [Type a message...]           [📤] │
└─────────────────────────────────────┘

Quick Actions:
[📊 Analyze Portfolio] [🤔 Explain Last Trade] 
[📚 Trading Basics] [❓ Help]
```

**Features:**
- Persistent chat history (хранится в БД)
- Context-aware (знает о портфеле юзера)
- Streaming responses (для лучшего UX)
- Quick action buttons для типичных вопросов
- Возможность "объяснить это решение" прямо из списка сделок

### 8.4 Rate Limiting для GPT

**Ограничения по тарифам:**

| Тариф | GPT запросов/день | Токенов/месяц |
|-------|-------------------|---------------|
| Free | 10 | 50,000 |
| Starter | 50 | 200,000 |
| Pro | 200 | 1,000,000 |
| Elite | Unlimited | Unlimited |

**Причина:** GPT-4 дорогой, нужно контролировать расходы.

## 9. Функциональные требования

### 8.1 Пользовательские сценарии

#### Сценарий 1: Регистрация и первый запуск
1. Пользователь регистрируется (email, username, password)
2. Верифицирует email
3. Настраивает 2FA
4. Получает виртуальный портфель с $1000
5. Видит dashboard с текущим балансом

#### Сценарий 2: Автоматический AI трейдинг
1. Пользователь нажимает "Start AI Bot"
2. Система каждые N минут (настраиваемо, default: 15):
   - Получает данные с Binance
   - Отправляет в DeepSeek
   - Исполняет решение AI
   - Обновляет интерфейс
3. Пользователь видит real-time обновления
4. Может остановить бота в любой момент

#### Сценарий 3: Просмотр статистики
1. Пользователь открывает dashboard
2. Видит:
   - Текущий баланс
   - Общий P&L (в $ и %)
   - График изменения баланса
   - Win rate
   - Список всех сделок
   - История решений AI с объяснениями

### 8.2 Нефункциональные требования

- **Производительность**: API response < 200ms (p95)
- **Доступность**: 99.9% uptime (после production)
- **Масштабируемость**: Поддержка 10,000+ пользователей
- **Безопасность**: Zero tolerance к утечкам данных
- **Юзабилити**: Интуитивный интерфейс для новичков

## 9. Ограничения MVP

- Только BTC/USDT пара (одна криптовалюта)
- Виртуальные сделки (реальных денег нет)
- Один AI провайдер (DeepSeek)
- Без реферальной системы
- Без социальных функций
- Без мобильного приложения

## 10. Будущие возможности (post-MVP)

- Множество торговых пар
- Реальный трейдинг (с подтверждениями)
- Несколько AI моделей на выбор
- Кастомные стратегии
- Copy-trading
- Социальная сеть трейдеров
- Мобильные приложения (iOS, Android)
- Продвинутая аналитика
- Backtesting стратегий
- Paper trading competitions

## 11. Интеграции

### 11.1 Binance API
- **Endpoint**: https://testnet.binance.vision (dev), https://api.binance.com (prod)
- **Authentication**: API Key + Secret (хранится зашифровано)
- **Rate Limits**: 1200 req/min (weight-based)
- **WebSocket**: wss://stream.binance.com:9443/ws для real-time цен

### 11.2 DeepSeek API
- **Endpoint**: https://api.deepseek.com/v1
- **Model**: deepseek-chat
- **Authentication**: Bearer token
- **Rate Limits**: уточнить у провайдера
- **Fallback**: кэширование решений, retry logic
- **Назначение**: Автономный анализ рынка и принятие торговых решений

### 11.3 OpenAI API
- **Endpoint**: https://api.openai.com/v1
- **Model**: gpt-4-turbo (или gpt-4o)
- **Authentication**: Bearer token
- **Rate Limits**: 10,000 req/day (tier зависит от оплаты)
- **Назначение**: Аналитический чат для пользователей, объяснение решений
- **Cost optimization**: 
  - Streaming для лучшего UX
  - Context window управление (не отправлять весь history)
  - Кэширование частых вопросов

## 12. Конфигурация окружений

### Development
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Backend: localhost:8000
- Frontend: localhost:3000
- Hot reload: enabled
- Debug logging: enabled

### Production
- PostgreSQL: managed instance (AWS RDS / DigitalOcean)
- Redis: managed instance
- Backend: Dockerized, за Nginx
- Frontend: CDN (Cloudflare / Vercel)
- SSL: Let's Encrypt / AWS Certificate Manager
- Monitoring: Prometheus + Grafana
- Logs: ELK Stack / CloudWatch

### 7.4 Экспорт статистики в .md формате

**Endpoint**: `GET /api/v1/portfolio/export-md`

**Формат экспорта**:

```markdown
# Draizer AI Trading Report

**User**: @username  
**Export Date**: 2025-10-21 15:30:00 UTC  
**Account Age**: 45 days  

---

## Portfolio Summary

| Metric | Value |
|--------|-------|
| Current Balance | $1,285.00 |
| Initial Balance | $1,000.00 |
| Total P&L | +$285.00 (+28.5%) |
| Total Trades | 24 |
| Winning Trades | 16 (66.7%) |
| Losing Trades | 8 (33.3%) |
| Best Trade | +$85.00 |
| Worst Trade | -$42.00 |
| Average Win | +$32.50 |
| Average Loss | -$18.75 |
| Win/Loss Ratio | 1.73 |

---

## Current Positions

| Symbol | Quantity | Entry Price | Current Price | Unrealized P&L | Status |
|--------|----------|-------------|---------------|----------------|--------|
| BTC/USDT | 0.0023 BTC | $43,200 | $44,100 | +$2.07 (+2.08%) | Open |

---

## Trading History (Last 30 days)

### Trade #24 - BTC/USDT
- **Date**: 2025-10-21 14:15:00
- **Type**: BUY
- **Quantity**: 0.0023 BTC
- **Price**: $43,200
- **Total Value**: $99.36
- **Status**: Open

### Trade #23 - BTC/USDT
- **Date**: 2025-10-20 09:30:00
- **Type**: SELL
- **Quantity**: 0.0018 BTC
- **Entry Price**: $42,800
- **Exit Price**: $43,950
- **P&L**: +$2.07 (+2.69%)
- **Fee**: $0.72 (35%)
- **Net P&L**: +$1.35
- **AI Confidence**: 78%
- **Reasoning**: Bullish breakout above MA25, strong volume confirmation

[... more trades ...]

---

## AI Decision Analysis

| Decision Type | Count | Success Rate |
|---------------|-------|--------------|
| BUY | 12 | 75% |
| SELL | 12 | 58% |
| HOLD | 156 | N/A |

**Average AI Confidence**: 76.3%  
**Trades Executed**: 24 / 180 opportunities (13.3%)

---

## Performance Chart (Last 30 days)

```
Balance Progress:
$1,000 ████████░░░░░░░░░░░░ $1,285 (+28.5%)

Week 1: $1,050 (+5.0%)
Week 2: $1,120 (+12.0%)
Week 3: $1,180 (+18.0%)
Week 4: $1,285 (+28.5%)
```

---

## Notes

⚠️ **IMPORTANT DISCLAIMER**:
This report represents VIRTUAL TRADING SIMULATION only. All trades, P&L, and balances are simulated using real market data from Binance. No actual money was traded. Past performance does not guarantee future results.

**Risk Warning**: Cryptocurrency trading carries significant risk. This simulation does not account for:
- Real market slippage
- Exchange fees and limitations
- Emotional factors in real trading
- Black swan events
- Liquidity constraints

Use this data for educational purposes only.

---

*Generated by Draizer AI Trading Platform*  
*Report Version: 1.0*
```

**Implementation**:
```python
# app/services/export_service.py
async def generate_markdown_report(portfolio_id: UUID) -> str:
    """Генерирует отчет в markdown формате"""
    portfolio = await get_portfolio(portfolio_id)
    transactions = await get_transactions(portfolio_id)
    ai_decisions = await get_ai_decisions(portfolio_id)
    
    # Формируем markdown
    report = f"""# Draizer AI Trading Report
    
**User**: @{portfolio.user.username}
**Export Date**: {datetime.utcnow().isoformat()}
...
"""
    return report
```

**Frontend кнопка**:
```tsx
<Button
  variant="contained"
  startIcon={<DownloadIcon />}
  onClick={() => downloadMarkdownReport()}
>
  Export Stats (.md)
</Button>
```

---

## 13. Критерии успеха MVP

✅ Пользователь может зарегистрироваться безопасно (с 2FA)
✅ AI бот принимает решения и ИМИТИРУЕТ виртуальные сделки
✅ Все транзакции корректно логируются
✅ Виртуальный P&L рассчитывается правильно
✅ Интерфейс отображает данные в реальном времени
✅ Экспорт статистики в .md работает корректно
✅ Система проходит базовый security audit
✅ Нет критических багов
✅ API отвечает быстро (< 200ms)
✅ Четкий disclaimer о симуляции везде

## 14. Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| DeepSeek API недоступен | Средняя | Retry logic, fallback на кэш, circuit breaker |
| Binance rate limit | Средняя | Rate limiting, request batching, WebSocket |
| Уязвимость безопасности | Низкая | Security audit, penetration testing, bug bounty |
| Низкая производительность | Низкая | Caching, DB indexing, load testing |
| AI делает плохие решения | Высокая | Backtest validation, paper trading длительное время |

---

**Версия**: 1.0  
**Дата**: 2025-10-21  
**Автор**: AI Development Team  
**Статус**: Утверждено к разработке

