-- Создание таблиц для Draizer
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    mfa_secret VARCHAR(32),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    balance_usd DECIMAL(20, 8) DEFAULT 1000.00,
    initial_balance DECIMAL(20, 8) DEFAULT 1000.00,
    total_profit_loss DECIMAL(20, 8) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    position_type VARCHAR(10) CHECK (position_type IN ('LONG', 'SHORT')),
    status VARCHAR(10) CHECK (status IN ('OPEN', 'CLOSED')) DEFAULT 'OPEN',
    profit_loss DECIMAL(20, 8),
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    trade_type VARCHAR(4) CHECK (trade_type IN ('BUY', 'SELL')) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    total_amount DECIMAL(20, 8) NOT NULL,
    profit_loss DECIMAL(20, 8),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    decision_type VARCHAR(4) CHECK (decision_type IN ('BUY', 'SELL', 'HOLD', 'WAIT')) NOT NULL,
    confidence INTEGER CHECK (confidence >= 0 AND confidence <= 100),
    reasoning TEXT,
    market_data JSONB,
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS news_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    raw_news JSONB,
    relevance_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_hours INTEGER,
    status VARCHAR(20) CHECK (status IN ('ACTIVE', 'COMPLETED', 'STOPPED', 'ERROR')) DEFAULT 'ACTIVE',
    total_analyses INTEGER DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    profit_loss DECIMAL(20, 8) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id ON positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_trades_portfolio_id ON trades(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_ai_decisions_portfolio_id ON ai_decisions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_portfolio_id ON ai_sessions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_session_id ON ai_sessions(session_id);

