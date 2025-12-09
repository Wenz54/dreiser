# Подробная инструкция по реализации Draizer AI Trading Platform

## Фаза 0: Подготовка окружения (1-2 дня)

### 0.1 Установка базового инструментария
```bash
# Проверить наличие
- Docker Desktop 24+
- Docker Compose v2
- Node.js 20+ LTS
- Python 3.11+
- PostgreSQL client (psql)
- Git
- IDE (VS Code / PyCharm)
```

### 0.2 Создание структуры проекта
```
draizer/
├── backend/
├── frontend/
├── nginx/
├── docs/
├── .github/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

### 0.3 Настройка Git и безопасности
```bash
# Создать .gitignore
echo "
.env
.env.*
!.env.example
*.pyc
__pycache__/
node_modules/
dist/
build/
.DS_Store
*.log
venv/
.venv/
.idea/
.vscode/
*.swp
secrets/
*.pem
*.key
coverage/
.pytest_cache/
" > .gitignore

# Инициализация репозитория
git init
git add .
git commit -m "Initial project structure"
```

---

## Фаза 1: Backend - Базовая настройка (3-5 дней)

### 1.1 Создание структуры backend

```bash
cd backend
mkdir -p app/{api/{v1/endpoints},core,db,models,schemas,services,middleware,utils}
mkdir -p alembic/versions
mkdir -p tests/{unit,integration,security}
```

**Структура:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencies (auth, db)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router aggregator
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py        # Auth endpoints
│   │           ├── portfolio.py   # Portfolio endpoints
│   │           ├── trading.py     # Trading endpoints
│   │           ├── ai.py          # AI endpoints
│   │           ├── market.py      # Market data endpoints
│   │           └── user.py        # User endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings (Pydantic BaseSettings)
│   │   ├── security.py            # JWT, hashing, encryption
│   │   ├── rate_limiter.py        # Rate limiting logic
│   │   └── audit_logger.py        # Audit trail logging
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                # Base model class
│   │   ├── session.py             # Database session
│   │   └── init_db.py             # Database initialization
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                # User SQLAlchemy model
│   │   ├── portfolio.py           # Portfolio model
│   │   ├── position.py            # Position model
│   │   ├── transaction.py         # Transaction model
│   │   ├── ai_decision.py         # AI Decision model
│   │   ├── market_data.py         # Market data cache
│   │   ├── audit_log.py           # Audit log model
│   │   └── security_event.py      # Security events
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py                # Pydantic schemas for User
│   │   ├── portfolio.py           # Portfolio schemas
│   │   ├── transaction.py         # Transaction schemas
│   │   ├── ai_decision.py         # AI decision schemas
│   │   ├── market.py              # Market data schemas
│   │   └── token.py               # JWT token schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py        # Authentication logic
│   │   ├── mfa_service.py         # 2FA/MFA logic (TOTP)
│   │   ├── encryption_service.py  # AES encryption for sensitive data
│   │   ├── portfolio_service.py   # Portfolio management
│   │   ├── trading_service.py     # Trading execution logic
│   │   ├── ai_service.py          # DeepSeek integration
│   │   ├── binance_service.py     # Binance API integration
│   │   ├── market_service.py      # Market data aggregation
│   │   └── notification_service.py# Email/alerts
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── security_headers.py    # Security headers middleware
│   │   ├── rate_limit.py          # Rate limiting middleware
│   │   └── audit.py               # Audit logging middleware
│   └── utils/
│       ├── __init__.py
│       ├── validators.py          # Custom validators
│       └── helpers.py             # Helper functions
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── .dockerignore
└── pytest.ini
```

### 1.2 Создание requirements.txt

```txt
# FastAPI и зависимости
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Security
python-jose[cryptography]==3.3.0
passlib[argon2]==1.7.4
python-multipart==0.0.6
cryptography==41.0.7
pyotp==2.9.0  # TOTP для 2FA

# Redis
redis==5.0.1
hiredis==2.2.3

# HTTP клиенты
httpx==0.25.2
aiohttp==3.9.1
websockets==12.0

# Validation & Serialization
email-validator==2.1.0
python-dateutil==2.8.2

# Monitoring & Logging
prometheus-fastapi-instrumentator==6.1.0
python-json-logger==2.0.7

# Rate Limiting
slowapi==0.1.9

# Utils
python-dotenv==1.0.0
tenacity==8.2.3  # Retry logic

# Testing (optional, но рекомендуется)
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2  # для тестирования API
faker==20.1.0
```

### 1.3 Создание базовой конфигурации (core/config.py)

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import secrets

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application
    PROJECT_NAME: str = "Draizer AI Trading"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Encryption (для AES шифрования)
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "draizer_user"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "draizer_db"
    POSTGRES_PORT: int = 5432
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    
    # External APIs
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = True
    
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    
    # Email (для верификации и уведомлений)
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Security Settings
    MFA_REQUIRED: bool = True
    PASSWORD_MIN_LENGTH: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Trading Settings
    INITIAL_BALANCE_USD: float = 1000.00
    DEFAULT_TRADING_SYMBOL: str = "BTCUSDT"
    AI_DECISION_INTERVAL_MINUTES: int = 15
    
settings = Settings()
```

### 1.4 Настройка безопасности (core/security.py)

```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib
from .config import settings

# Password hashing (Argon2id)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64MB
    argon2__time_cost=3,
    argon2__parallelism=4,
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str) -> str:
    """Создание JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

# AES-256 шифрование для чувствительных данных
class EncryptionService:
    def __init__(self):
        # Генерируем Fernet ключ из настроек
        key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key))
    
    def encrypt(self, data: str) -> str:
        """Шифрование строки"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Дешифрование строки"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

encryption_service = EncryptionService()
```

### 1.5 Docker Compose для разработки

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: draizer_postgres
    environment:
      POSTGRES_USER: draizer_user
      POSTGRES_PASSWORD: draizer_password_dev_only
      POSTGRES_DB: draizer_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U draizer_user -d draizer_db"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    container_name: draizer_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: draizer_backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - POSTGRES_SERVER=postgres
      - REDIS_HOST=redis
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: draizer_frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

### 1.6 .env.example

```env
# Application
DEBUG=True
PROJECT_NAME="Draizer AI Trading"

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-change-this-in-production
ENCRYPTION_KEY=your-encryption-key-change-this-too

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=draizer_user
POSTGRES_PASSWORD=draizer_password_dev_only
POSTGRES_DB=draizer_db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# External APIs
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
BINANCE_TESTNET=True

DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Email (опционально для MVP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAILS_FROM_EMAIL=noreply@draizer.com
EMAILS_FROM_NAME=Draizer

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Trading
INITIAL_BALANCE_USD=1000.00
AI_DECISION_INTERVAL_MINUTES=15
```

---

## Фаза 2: Database Models (2-3 дня)

### 2.1 Создание базовой модели

```python
# app/db/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

### 2.2 User Model

```python
# app/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # MFA
    mfa_secret = Column(String(255), nullable=True)  # Encrypted TOTP secret
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    security_events = relationship("SecurityEvent", back_populates="user", cascade="all, delete-orphan")
```

### 2.3 Portfolio Model

```python
# app/models/portfolio.py
from sqlalchemy import Column, ForeignKey, DECIMAL, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class Portfolio(BaseModel):
    __tablename__ = "portfolios"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Balances
    balance_usd = Column(DECIMAL(20, 8), default=1000.00, nullable=False)
    initial_balance = Column(DECIMAL(20, 8), default=1000.00, nullable=False)
    total_pnl = Column(DECIMAL(20, 8), default=0.00, nullable=False)
    
    # Statistics
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="portfolio")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    ai_decisions = relationship("AIDecision", back_populates="portfolio", cascade="all, delete-orphan")
```

### 2.4 Остальные модели создавать аналогично согласно схеме из tech.md

---

## Фаза 3: API Endpoints (5-7 дней)

### 3.1 FastAPI main.py

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers (добавить middleware)
# Rate Limiting (добавить middleware)
# Audit Logging (добавить middleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}
```

### 3.2 Реализовать все endpoints согласно tech.md секция 6

**Приоритет реализации:**
1. Auth endpoints (register, login, refresh)
2. Portfolio endpoints (get portfolio, stats)
3. Market endpoints (get price, candles)
4. Trading endpoints (manual trade для тестов)
5. AI endpoints (analyze, start/stop bot)
6. User endpoints

---

## Фаза 4: External Integrations (3-4 дня)

### 4.1 Binance Service

```python
# app/services/binance_service.py
import aiohttp
import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from app.core.config import settings

class BinanceService:
    def __init__(self):
        if settings.BINANCE_TESTNET:
            self.base_url = "https://testnet.binance.vision"
            self.ws_url = "wss://testnet.binance.vision/ws"
        else:
            self.base_url = "https://api.binance.com"
            self.ws_url = "wss://stream.binance.com:9443/ws"
        
        self.api_key = settings.BINANCE_API_KEY
        self.api_secret = settings.BINANCE_API_SECRET
    
    async def get_ticker_price(self, symbol: str = "BTCUSDT") -> Optional[float]:
        """Получить текущую цену"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v3/ticker/price"
            params = {"symbol": symbol}
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data["price"])
                return None
    
    async def get_klines(self, symbol: str = "BTCUSDT", interval: str = "15m", limit: int = 100) -> list:
        """Получить свечи (OHLCV)"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/v3/klines"
            params = {"symbol": symbol, "interval": interval, "limit": limit}
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return []
    
    # Добавить методы для WebSocket подключения
```

### 4.2 DeepSeek Service

```python
# app/services/ai_service.py
import aiohttp
import json
from typing import Dict, Any
from app.core.config import settings

class AIService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
    
    async def get_trading_decision(
        self,
        current_price: float,
        market_data: Dict[str, Any],
        position_status: str,
        balance_usd: float
    ) -> Dict[str, Any]:
        """Получить торговое решение от AI"""
        
        # Формирование промпта
        system_prompt = "You are a professional cryptocurrency trader analyzing BTC/USDT market."
        
        user_prompt = f"""
Context:
- Current BTC/USDT price: ${current_price:,.2f}
- 24h change: {market_data.get('change_24h', 0)}%
- 24h volume: {market_data.get('volume_24h', 0)}
- Your current position: {position_status}
- Available balance: ${balance_usd:,.2f} USD

Task: Analyze the market and decide whether to BUY, SELL, or HOLD.

Respond in JSON format:
{{
  "decision": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100,
  "reasoning": "brief explanation",
  "suggested_amount": 100
}}

Rules:
- Only BUY if you have available USD balance
- Only SELL if you have an open position
- Be conservative, protect capital
"""
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    # Парсинг JSON из ответа
                    try:
                        decision = json.loads(content)
                        return decision
                    except json.JSONDecodeError:
                        # Fallback если AI не вернул валидный JSON
                        return {
                            "decision": "HOLD",
                            "confidence": 0,
                            "reasoning": "Failed to parse AI response",
                            "suggested_amount": 0
                        }
                else:
                    raise Exception(f"DeepSeek API error: {response.status}")
```

---

## Фаза 5: Trading Logic (4-5 дней)

### 5.1 Trading Service - ядро системы

```python
# app/services/trading_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import Optional, Dict, Any
from app.models import Portfolio, Position, Transaction, AIDecision
from app.services.binance_service import BinanceService
from app.services.ai_service import AIService
import uuid

class TradingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.binance = BinanceService()
        self.ai = AIService()
    
    async def execute_buy(
        self,
        portfolio: Portfolio,
        symbol: str,
        amount_usd: Decimal,
        ai_decision_id: Optional[uuid.UUID] = None
    ) -> Transaction:
        """Исполнение покупки"""
        # 1. Получить текущую цену
        current_price = await self.binance.get_ticker_price(symbol)
        if not current_price:
            raise Exception("Failed to get market price")
        
        price = Decimal(str(current_price))
        
        # 2. Проверить баланс
        if portfolio.balance_usd < amount_usd:
            raise Exception("Insufficient balance")
        
        # 3. Рассчитать количество монет
        quantity = amount_usd / price
        
        # 4. Создать/обновить позицию
        position = await self._get_or_create_position(portfolio.id, symbol)
        position.quantity += quantity
        position.entry_price = (position.entry_price * position.quantity + price * quantity) / (position.quantity + quantity)
        position.current_price = price
        
        # 5. Создать транзакцию
        transaction = Transaction(
            portfolio_id=portfolio.id,
            position_id=position.id,
            type="BUY",
            symbol=symbol,
            quantity=quantity,
            price=price,
            total_value=amount_usd,
            ai_decision_id=ai_decision_id
        )
        
        # 6. Обновить баланс
        portfolio.balance_usd -= amount_usd
        portfolio.total_trades += 1
        
        # 7. Сохранить в БД
        self.db.add(transaction)
        self.db.add(position)
        await self.db.commit()
        
        return transaction
    
    async def execute_sell(
        self,
        portfolio: Portfolio,
        symbol: str,
        quantity: Optional[Decimal] = None,  # None = sell all
        ai_decision_id: Optional[uuid.UUID] = None
    ) -> Transaction:
        """Исполнение продажи"""
        # 1. Получить позицию
        position = await self._get_position(portfolio.id, symbol)
        if not position or position.is_closed:
            raise Exception("No open position to sell")
        
        # 2. Получить текущую цену
        current_price = await self.binance.get_ticker_price(symbol)
        if not current_price:
            raise Exception("Failed to get market price")
        
        price = Decimal(str(current_price))
        
        # 3. Определить количество для продажи
        sell_quantity = quantity if quantity else position.quantity
        if sell_quantity > position.quantity:
            raise Exception("Insufficient position size")
        
        # 4. Рассчитать P&L
        total_value = sell_quantity * price
        cost_basis = sell_quantity * position.entry_price
        pnl = total_value - cost_basis
        
        # 5. Создать транзакцию
        transaction = Transaction(
            portfolio_id=portfolio.id,
            position_id=position.id,
            type="SELL",
            symbol=symbol,
            quantity=sell_quantity,
            price=price,
            total_value=total_value,
            pnl=pnl,
            ai_decision_id=ai_decision_id
        )
        
        # 6. Обновить позицию
        position.quantity -= sell_quantity
        if position.quantity == 0:
            position.is_closed = True
        
        # 7. Обновить портфель
        portfolio.balance_usd += total_value
        portfolio.total_pnl += pnl
        portfolio.total_trades += 1
        
        if pnl > 0:
            portfolio.winning_trades += 1
        else:
            portfolio.losing_trades += 1
        
        # 8. Сохранить
        self.db.add(transaction)
        self.db.add(position)
        await self.db.commit()
        
        return transaction
    
    async def ai_trading_cycle(self, portfolio: Portfolio) -> AIDecision:
        """Полный цикл AI трейдинга"""
        # 1. Получить рыночные данные
        current_price = await self.binance.get_ticker_price()
        market_data = await self._prepare_market_data()
        
        # 2. Проверить текущую позицию
        position = await self._get_position(portfolio.id, "BTCUSDT")
        position_status = "open" if position and not position.is_closed else "no position"
        
        # 3. Получить решение от AI
        ai_response = await self.ai.get_trading_decision(
            current_price=current_price,
            market_data=market_data,
            position_status=position_status,
            balance_usd=float(portfolio.balance_usd)
        )
        
        # 4. Сохранить решение AI
        ai_decision = AIDecision(
            portfolio_id=portfolio.id,
            decision_type=ai_response["decision"],
            symbol="BTCUSDT",
            confidence=ai_response.get("confidence", 0),
            reasoning=ai_response.get("reasoning", ""),
            market_data=market_data,
            executed=False
        )
        self.db.add(ai_decision)
        await self.db.flush()  # Получить ID
        
        # 5. Исполнить решение
        if ai_response["decision"] == "BUY" and portfolio.balance_usd > 10:
            amount = min(
                Decimal(str(ai_response.get("suggested_amount", 100))),
                portfolio.balance_usd
            )
            await self.execute_buy(portfolio, "BTCUSDT", amount, ai_decision.id)
            ai_decision.executed = True
        
        elif ai_response["decision"] == "SELL" and position and not position.is_closed:
            await self.execute_sell(portfolio, "BTCUSDT", ai_decision_id=ai_decision.id)
            ai_decision.executed = True
        
        await self.db.commit()
        return ai_decision
```

---

## Фаза 6: Frontend React + TypeScript (7-10 дней)

### 6.1 Создание React приложения

```bash
cd frontend
npx create-react-app . --template typescript
# или с Vite (быстрее)
npm create vite@latest . -- --template react-ts
```

### 6.2 Установка зависимостей

```bash
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled
npm install @reduxjs/toolkit react-redux
npm install react-router-dom
npm install recharts  # для графиков
npm install axios
npm install dayjs
npm install react-toastify  # для уведомлений
```

### 6.3 Структура frontend (детально распишу отдельно при реализации)

---

## Фаза 7: Security Hardening (3-4 дня)

### 7.1 Чеклист безопасности
- [ ] Все пароли хешируются Argon2id
- [ ] API ключи шифруются AES-256
- [ ] JWT с коротким TTL (15 мин)
- [ ] Refresh tokens в httpOnly cookies
- [ ] Rate limiting на всех endpoints
- [ ] CORS настроен правильно
- [ ] SQL injection защита (ORM + validation)
- [ ] XSS защита (CSP headers)
- [ ] CSRF tokens
- [ ] 2FA обязательна
- [ ] Audit logging работает
- [ ] Failed login tracking
- [ ] Security events мониторинг

### 7.2 Тестирование безопасности
- Penetration testing с OWASP ZAP
- Dependency scanning
- SQL injection тесты
- XSS тесты
- CSRF тесты
- Rate limiting тесты

---

## Фаза 8: Testing & QA (3-5 дней)

### 8.1 Backend тесты
```bash
# Unit tests
pytest tests/unit -v --cov=app

# Integration tests
pytest tests/integration -v

# Security tests
pytest tests/security -v
```

### 8.2 Frontend тесты
```bash
npm test
npm run test:coverage
```

---

## Фаза 9: Deployment (2-3 дня)

### 9.1 Production docker-compose
### 9.2 Nginx конфигурация с SSL
### 9.3 Environment variables production
### 9.4 Database migrations
### 9.5 Monitoring setup

---

## Общая временная оценка: 35-50 рабочих дней (7-10 недель)

## Приоритеты для MVP:
1. ✅ Backend API core (auth, trading logic)
2. ✅ Binance + DeepSeek integration
3. ✅ Basic frontend (dashboard, login)
4. ✅ Security essentials (JWT, encryption, rate limiting)
5. ⏸ Advanced features (можно отложить)

---

**Версия**: 1.0  
**Последнее обновление**: 2025-10-21












