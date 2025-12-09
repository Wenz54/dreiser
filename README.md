# 🚀 Draizer Ultra-Low Latency Quantitative Arbitrage Platform v2.0.00

**Spot-Futures Arbitrage** | **Bitfinex + Deribit** | **Target: 7μs Detection**

Ultra-low latency quantitative arbitrage platform with C-engine core optimized for spot-futures arbitrage between Bitfinex (spot) and Deribit (futures perpetual).

⚠️ **PAPER TRADING**: All trades are simulated with real market data. No real money involved.

## 🎯 Features

### Core Trading
- **Autonomous AI Trading**: DeepSeek AI analyzes market data and makes independent trading decisions
- **Virtual Portfolio**: Start with $1000 virtual balance for risk-free testing
- **Real Market Data**: Uses real-time prices from Binance (testnet supported)
- **AI Assistant**: GPT-4 powered chat to explain trading decisions and analyze results
- **Complete Trading History**: Track all simulated trades with P&L calculations
- **Markdown Reports**: Export detailed trading statistics

### 🆕 NEW in v1.1.0
- **📰 Telegram News Monitor**: GPT-4 analyzes news from Telegram channels every 30 minutes
- **🧠 Context Compression**: Auto-summarizes DeepSeek history every 10 decisions (85% token savings)
- **🔒 Enhanced Security**: HMAC request signing, real-time anomaly detection, API key rotation

### Security
- **Banking-Level Security**: Argon2id password hashing, JWT auth, 2FA support, AES-256 encryption
- **Audit Logging**: Every action tracked and encrypted
- **Anomaly Detection**: Real-time suspicious pattern detection

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with SQLAlchemy ORM
- **Cache**: Redis 7+
- **APIs**: Binance (market data), DeepSeek (trading AI), OpenAI GPT-4 (chat assistant)

### Frontend
- **Framework**: React 18 + TypeScript
- **UI**: Material-UI (MUI) v5
- **State**: Redux Toolkit
- **Build**: Vite

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Database Migrations**: Alembic
- **Security**: JWT tokens, 2FA (TOTP), encryption at rest and in transit

## 🚀 Quick Start

### 📦 **ONE-CLICK DEPLOYMENT:**

#### **🐧 Ubuntu Server (Production):**
```bash
./deploy.sh
```

#### **🪟 Windows (Development):**
```powershell
.\deploy.ps1
```

**See full instructions:** [QUICKSTART.md](QUICKSTART.md)

---

### Prerequisites (if deploying manually)

- **Ubuntu:** gcc, cmake, PostgreSQL, Redis, Node.js
- **Windows:** Docker Desktop 24+
- Node.js 20+ (if running frontend locally)
- Python 3.11+ (if running backend locally)

### 1. Clone Repository

```bash
git clone <repository-url>
cd draizer
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required API Keys
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for real Binance data)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
BINANCE_TESTNET=True
```

### 3. Start with Docker Compose

```bash
docker-compose up --build
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Frontend (port 3000)

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

### 5. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 6. Create Account

1. Go to http://localhost:3000/register
2. Create an account (min 12 character password)
3. Login
4. Start trading with $1000 virtual balance!

## 📁 Project Structure

```
draizer/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Config, security
│   │   ├── db/               # Database setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── store/            # Redux store
│   │   ├── services/         # API services
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile.dev
├── docs/
│   ├── tech.md               # Technical specification
│   └── tasks.md              # Implementation guide
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🎮 How to Use

### 1. Dashboard
- View virtual portfolio balance
- See total P&L and win rate
- Quick access to key features

### 2. AI Analysis
- Click "Analyze Market" to run DeepSeek AI
- AI will analyze real-time Binance data
- Makes autonomous BUY/SELL/HOLD decisions
- Executes virtual trades automatically

### 3. Portfolio
- View open positions
- See trading history
- Export detailed markdown report

### 4. Manual Trading
- Test manual virtual trades
- Uses real Binance prices
- Simulates trade execution

### 5. AI Chat
- Ask GPT-4 to explain trading decisions
- Get portfolio analysis
- Learn about trading concepts

## 🔐 Security Features

- **Argon2id** password hashing (64MB memory, 3 iterations)
- **JWT** access (15 min) + refresh (7 days) tokens
- **2FA/MFA** support (TOTP)
- **AES-256-GCM** encryption for sensitive data
- **Rate limiting** (100 req/min general, 10 req/min auth)
- **HTTPS/TLS 1.3** (production)
- **CORS** protection
- **Security headers** (CSP, X-Frame-Options, etc.)
- **Audit logging** for all actions

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/mfa/setup` - Setup 2FA

### Portfolio
- `GET /api/v1/portfolio` - Get portfolio
- `GET /api/v1/portfolio/stats` - Detailed statistics
- `GET /api/v1/portfolio/export-md` - Export report

### Trading
- `GET /api/v1/trading/history` - Trading history
- `POST /api/v1/trading/manual-trade` - Manual trade

### AI
- `POST /api/v1/ai/analyze` - Run AI analysis
- `GET /api/v1/ai/decisions` - AI decision history

### Market
- `GET /api/v1/market/price/:symbol` - Current price
- `GET /api/v1/market/ticker/:symbol` - 24h ticker
- `GET /api/v1/market/candles/:symbol` - OHLCV data

### Chat
- `POST /api/v1/chat/message` - Send message to GPT-4
- `GET /api/v1/chat/history` - Chat history

## 🧪 Development

### Run Backend Locally

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🌍 Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DEEPSEEK_API_KEY` - DeepSeek AI API key (required)
- `OPENAI_API_KEY` - OpenAI GPT-4 API key (required)
- `BINANCE_API_KEY` - Binance API key (optional, uses public endpoints)
- `POSTGRES_PASSWORD` - Database password
- `SECRET_KEY` - JWT secret (change in production!)
- `ENCRYPTION_KEY` - AES encryption key (change in production!)

## ⚠️ Important Disclaimers

1. **Virtual Trading Only**: This platform simulates trades using real market data. No actual money is involved.
2. **Educational Purpose**: Use for learning and testing trading strategies only.
3. **No Financial Advice**: AI decisions are not financial advice. Past performance ≠ future results.
4. **Risk Warning**: Real cryptocurrency trading involves significant risk. This simulation does not account for:
   - Real market slippage
   - Exchange fees and limitations
   - Emotional factors
   - Black swan events
   - Liquidity constraints

## 🤝 Contributing

This is an MVP project. Contributions welcome!

## 📝 License

MIT License

## 🔗 Links

- [Technical Specification](docs/tech.md)
- [Implementation Guide](docs/tasks.md)
- [API Documentation](http://localhost:8000/docs)

## 🆘 Troubleshooting

### Docker Issues
```bash
# Clean rebuild
docker-compose down -v
docker-compose up --build
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps
docker-compose logs postgres
```

### API Key Errors
- Ensure API keys are correctly set in `.env`
- DeepSeek and OpenAI keys are required for core functionality

### Port Conflicts
- Backend (8000), Frontend (3000), PostgreSQL (5432), Redis (6379)
- Change ports in `docker-compose.yml` if needed

---

**Built with ❤️ using DeepSeek AI, GPT-4, and React**
