# DRAIZER V2 - MIGRATION PLAN

**Date:** 2025-10-28  
**Strategy:** Reuse V1 infrastructure, add C engine

---

## V1 INFRASTRUCTURE ASSESSMENT

### ✅ KEEP (Working, Reusable)

**Core Infrastructure:**
- ✅ `docker-compose.yml` - PostgreSQL, Redis containers
- ✅ `backend/app/core/config.py` - Settings management
- ✅ `backend/app/core/security.py` - JWT auth, encryption
- ✅ `backend/app/db/` - Database session management
- ✅ `backend/alembic/` - Migration system

**Database Models (modify):**
- ✅ `models/user.py` - User accounts
- ✅ `models/portfolio.py` - Balance tracking
- ✅ `models/position.py` - SPOT positions
- ✅ `models/futures_position.py` - Futures positions
- ✅ `models/transaction.py` - Trade history
- ✅ `models/audit_log.py` - Audit trail
- ⚠️ Modify: Add `strategy_type` (cross_exchange, funding_rate, triangular)

**API & Auth:**
- ✅ `api/v1/endpoints/auth.py` - Login, register (keep as-is)
- ✅ `api/v1/endpoints/portfolio.py` - Portfolio API (keep)
- ✅ `api/deps.py` - JWT dependency injection

**Services (reuse partially):**
- ✅ `services/auth_service.py` - User management
- ✅ `services/portfolio_service.py` - Portfolio tracking
- ✅ `services/binance_service.py` - Binance API (for backtesting, validation)
- ⚠️ Modify: Keep for Python-side tasks, C engine handles real-time

**Frontend:**
- ✅ `frontend/` - Entire React app (reuse)
- ⚠️ Update: Add V2 strategy controls, new metrics

---

### ❌ REMOVE (AI-specific, not needed)

**AI Services (obsolete):**
- ❌ `services/ai_service*.py` (8 files) - DeepSeek logic
- ❌ `services/ai_expectations.py` - AI expectations
- ❌ `services/ai_learning_service.py` - AI learning
- ❌ `services/context_manager.py` - Context compression
- ❌ `services/performance_monitor_service.py` - GPT monitoring
- ❌ `services/gpt_service.py` - GPT-4 chat
- ❌ `services/cryptopanic_service.py` - News analysis
- ❌ `services/news_relevance_service.py` - News filtering
- ❌ `services/reality_check_service.py` - AI reality check

**AI Models (obsolete):**
- ❌ `models/ai_decision.py` - DeepSeek decisions
- ❌ `models/ai_learning_note.py` - AI learning
- ❌ `models/ai_session.py` - AI sessions
- ❌ `models/deepseek_context.py` - Context storage
- ❌ `models/chat_message.py` - GPT chat
- ❌ `models/news_summary.py` - News summaries
- ❌ `models/performance_log.py` - AI monitoring

**AI API Endpoints:**
- ❌ `api/v1/endpoints/ai.py`
- ❌ `api/v1/endpoints/ai_session.py`
- ❌ `api/v1/endpoints/ai_analysis.py`
- ❌ `api/v1/endpoints/ai_learning.py`
- ❌ `api/v1/endpoints/chat.py`

**AI Tasks:**
- ❌ `tasks/ai_tasks.py` - Celery AI tasks
- ❌ `tasks/news_tasks.py` - News fetching

---

### ⚠️ MODIFY (Adapt for V2)

**Trading Service:**
- ⚠️ `services/trading_service.py`
- **Keep:** Virtual position tracking, P&L calculation
- **Remove:** AI integration, DeepSeek calls
- **Add:** C engine bridge, IPC communication

**Futures Trading:**
- ⚠️ `services/futures_trading_service.py`
- **Keep:** Futures position logic
- **Remove:** AI integration
- **Add:** Funding rate strategy support

**Performance Score:**
- ⚠️ `services/performance_score_service.py`
- **Keep:** Performance metrics
- **Modify:** Remove AI-specific metrics, add latency tracking

---

## NEW V2 COMPONENTS

### C Engine (NEW)
```
backend/c_engine/
├── src/
│   ├── main.c
│   ├── network/         # WebSocket, io_uring
│   ├── data/            # Lock-free structures
│   ├── strategies/      # Arbitrage detection
│   ├── execution/       # Order placement
│   ├── risk/            # Risk management
│   ├── ipc/             # Python communication
│   └── utils/           # RDTSC, pools, logger
├── config/
│   ├── engine.json
│   └── strategies.json
├── tests/
└── CMakeLists.txt
```

### Python Bridge (NEW)
```python
# backend/app/services/c_engine_bridge.py
class CEngineBridge:
    def __init__(self):
        self.shm = mmap.mmap(-1, SHARED_MEM_SIZE)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    def start_strategy(self, strategy_name: str):
        # Send command via Unix socket
    
    def get_stats(self) -> dict:
        # Read from shared memory
    
    def get_latest_opportunities(self) -> list:
        # Read from shared memory
```

### New API Endpoints (v2)
```python
# backend/app/api/v2/endpoints/arbitrage.py
@router.get("/opportunities")
async def get_opportunities():
    # Read from C engine shared memory

@router.post("/strategy/start")
async def start_strategy(strategy: str):
    # Send command to C engine

@router.get("/strategy/status")
async def get_status():
    # Read C engine stats
```

### New Database Tables
```sql
-- Arbitrage opportunities (detected)
CREATE TABLE arbitrage_opportunities (
    id UUID PRIMARY KEY,
    strategy_type VARCHAR(50),  -- cross_exchange, funding_rate, triangular
    symbol VARCHAR(20),
    exchange_buy VARCHAR(20),
    exchange_sell VARCHAR(20),
    spread_bps DECIMAL(10, 4),
    profit_usd DECIMAL(20, 8),
    detected_at TIMESTAMP,
    executed BOOLEAN
);

-- Arbitrage executions (completed)
CREATE TABLE arbitrage_executions (
    id UUID PRIMARY KEY,
    opportunity_id UUID REFERENCES arbitrage_opportunities(id),
    portfolio_id UUID REFERENCES portfolios(id),
    buy_order_id VARCHAR(100),
    sell_order_id VARCHAR(100),
    actual_profit_usd DECIMAL(20, 8),
    latency_us INTEGER,
    executed_at TIMESTAMP,
    settled_at TIMESTAMP
);

-- Engine performance metrics
CREATE TABLE engine_metrics (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP,
    opportunities_detected INTEGER,
    opportunities_executed INTEGER,
    avg_latency_us INTEGER,
    p99_latency_us INTEGER,
    total_profit_usd DECIMAL(20, 8)
);
```

---

## MIGRATION STEPS

### Step 1: Cleanup (1 day)
```bash
# Backup first
cp -r backend/app backend/app.v1.backup

# Remove AI services
rm backend/app/services/ai_*.py
rm backend/app/services/gpt_service.py
rm backend/app/services/cryptopanic_service.py
rm backend/app/services/news_relevance_service.py
rm backend/app/services/context_manager.py
rm backend/app/services/performance_monitor_service.py
rm backend/app/services/reality_check_service.py

# Remove AI endpoints
rm backend/app/api/v1/endpoints/ai*.py
rm backend/app/api/v1/endpoints/chat.py

# Remove AI tasks
rm backend/app/tasks/ai_tasks.py
rm backend/app/tasks/news_tasks.py

# Comment out AI models (keep for historical data)
# Later: create migration to archive old data
```

### Step 2: Database Migration (1 day)
```bash
# Create new migration
cd backend
alembic revision -m "add_v2_arbitrage_tables"

# Edit migration file: add new tables
# - arbitrage_opportunities
# - arbitrage_executions  
# - engine_metrics

# Run migration
alembic upgrade head

# Optional: archive old AI data
alembic revision -m "archive_v1_ai_data"
```

### Step 3: Setup C Engine (3 days)
```bash
# Create structure
mkdir -p backend/c_engine/{src,config,tests}
cd backend/c_engine

# Install dependencies (Ubuntu/Debian)
sudo apt-get install -y \
    build-essential \
    cmake \
    liburing-dev \
    libwebsockets-dev \
    libcurl4-openssl-dev \
    libjansson-dev

# Create CMakeLists.txt
# Create initial main.c
# Build hello world
cmake -B build && cmake --build build
./build/draizer_engine --version
```

### Step 4: Python Bridge (2 days)
```python
# backend/app/services/c_engine_bridge.py
# Implement shared memory communication
# Implement Unix socket commands
# Add to FastAPI startup

# backend/app/api/v2/endpoints/arbitrage.py
# Create v2 endpoints
# Wire up to C engine bridge
```

### Step 5: Frontend Updates (2 days)
```typescript
// frontend/src/pages/ArbitrageMonitor.tsx
// New page for V2 arbitrage monitoring

// frontend/src/pages/Dashboard.tsx  
// Update to show V2 metrics

// frontend/src/services/api.ts
// Add v2 API calls
```

### Step 6: Testing (3 days)
```bash
# Unit tests (C engine)
cd backend/c_engine
make test

# Integration tests (Python ↔ C)
cd backend
pytest tests/integration/test_c_engine_bridge.py

# End-to-end (paper trading)
docker-compose up -d
./backend/c_engine/build/draizer_engine --mode paper --capital 1000
```

---

## DOCKER SETUP

### Update docker-compose.yml
```yaml
services:
  postgres:
    # Keep as-is
  
  redis:
    # Keep as-is
  
  backend:
    # Keep as-is
    volumes:
      - ./backend:/app
      - c_engine_shm:/dev/shm  # NEW: shared memory
  
  c_engine:  # NEW SERVICE
    build:
      context: ./backend/c_engine
      dockerfile: Dockerfile
    depends_on:
      - redis
    volumes:
      - c_engine_shm:/dev/shm
      - ./backend/c_engine/config:/app/config
    environment:
      - ENGINE_MODE=live
      - CAPITAL_USD=1000
    # Requires --privileged for io_uring (optional)
    # privileged: true
  
  frontend:
    # Keep as-is

volumes:
  postgres_data:
  redis_data:
  c_engine_shm:  # NEW: shared memory volume
```

---

## ENVIRONMENT VARIABLES

### Keep from V1
```bash
# Database
POSTGRES_SERVER=postgres
POSTGRES_USER=draizer_user
POSTGRES_PASSWORD=***
POSTGRES_DB=draizer_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Auth
SECRET_KEY=***
ENCRYPTION_KEY=***

# Binance (for validation)
BINANCE_API_KEY=***
BINANCE_API_SECRET=***
```

### Remove from V1
```bash
# AI (not needed)
# DEEPSEEK_API_KEY=***
# OPENAI_API_KEY=***
# CRYPTOPANIC_API_TOKEN=***
```

### Add for V2
```bash
# C Engine
C_ENGINE_MODE=live  # or paper
C_ENGINE_CAPITAL_USD=1000
C_ENGINE_LOG_LEVEL=info

# Shared memory
SHM_SIZE=268435456  # 256MB
```

---

## FILE STRUCTURE COMPARISON

### V1 (Current)
```
backend/
├── app/
│   ├── api/v1/endpoints/  (14 files, remove 5 AI endpoints)
│   ├── services/          (24 files, remove 9 AI services)
│   ├── models/            (17 files, archive 7 AI models)
│   └── tasks/             (5 files, remove 2 AI tasks)
```

### V2 (Target)
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/endpoints/  (9 files: auth, portfolio, trading, market)
│   │   └── v2/endpoints/  (NEW: arbitrage.py, strategy.py)
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── portfolio_service.py
│   │   ├── trading_service.py (modified)
│   │   ├── binance_service.py (keep for validation)
│   │   └── c_engine_bridge.py (NEW)
│   ├── models/            (10 files: users, portfolios, positions, transactions)
│   └── tasks/             (3 files: security, monitoring)
└── c_engine/              (NEW)
    ├── src/               (C code)
    ├── config/            (JSON configs)
    ├── tests/             (C tests)
    └── CMakeLists.txt
```

**Lines of code reduction:**
- V1: ~15,000 lines Python
- V2: ~5,000 lines Python + ~5,000 lines C = 10,000 total
- **33% reduction!**

---

## RISKS & MITIGATION

### Risk 1: Data loss during migration
**Mitigation:**
- Full database backup before migration
- Keep V1 code in `app.v1.backup/`
- Archive AI data, don't delete

### Risk 2: C engine bugs crash system
**Mitigation:**
- Auto-restart (systemd/Docker)
- Circuit breaker in Python
- Extensive testing before production

### Risk 3: IPC communication fails
**Mitigation:**
- Fallback to REST API (slower but works)
- Comprehensive error handling
- Health checks every 10 seconds

### Risk 4: Frontend breaks
**Mitigation:**
- Keep V1 endpoints working during transition
- Gradual rollout (v2 alongside v1)
- Feature flags

---

## TIMELINE

```
Week 1: Cleanup + DB Migration
├─ Day 1-2: Remove AI code
├─ Day 3-4: Database migrations
└─ Day 5: Testing, rollback plan

Week 2-3: C Engine Foundation
├─ Day 6-8: Project setup, build system
├─ Day 9-11: Core data structures (SPSC, pools, timestamp)
└─ Day 12-15: Unit tests, benchmarks

Week 4-5: Python Bridge
├─ Day 16-18: Shared memory IPC
├─ Day 19-20: Unix socket commands
└─ Day 21-25: FastAPI v2 endpoints

Week 6: Frontend Updates
├─ Day 26-28: New pages (ArbitrageMonitor)
├─ Day 29-30: Update Dashboard

Week 7-8: Integration Testing
├─ Day 31-35: End-to-end tests
├─ Day 36-40: Paper trading (1 week)

Week 9: Production Deployment
├─ Day 41-42: Deploy to VPS
├─ Day 43-45: Monitor, fix bugs
```

**Total:** 9 weeks (~2 months)

---

## SUCCESS CRITERIA

### Week 2 (Foundation)
- ✅ C engine compiles
- ✅ RDTSC timestamp works (<10ns)
- ✅ SPSC buffer works (<50ns)
- ✅ All unit tests pass

### Week 5 (Integration)
- ✅ Python ↔ C communication works
- ✅ Can send commands, read stats
- ✅ Shared memory updated in real-time

### Week 7 (Testing)
- ✅ Paper trading runs 24 hours without crash
- ✅ Detects opportunities correctly
- ✅ Latency <100μs (P99)

### Week 9 (Production)
- ✅ Live trading with $1,000
- ✅ First profitable trade executed
- ✅ Dashboard shows real-time metrics

---

## ROLLBACK PLAN

If V2 fails, can rollback to V1:

```bash
# 1. Stop V2
docker-compose down

# 2. Restore V1 code
rm -rf backend/app
mv backend/app.v1.backup backend/app

# 3. Restore V1 database
psql -U draizer_user -d draizer_db < backup_v1.sql

# 4. Restart V1
docker-compose up -d

# 5. Verify V1 works
curl http://localhost:8000/api/v1/auth/status
```

**Data preserved:**
- Users, portfolios (unchanged)
- Transaction history (unchanged)
- V2 data (separate tables, ignored by V1)

---

## NEXT ACTION

**Start with Week 1, Day 1:**
```bash
# 1. Backup everything
cp -r backend/app backend/app.v1.backup
pg_dump -U draizer_user draizer_db > backup_v1_$(date +%Y%m%d).sql

# 2. Create cleanup branch
git checkout -b v2-migration
git add -A
git commit -m "V1 backup before V2 migration"

# 3. Start cleanup
# (see Step 1 above)
```

**Ready to start?** → Confirm and begin cleanup.

