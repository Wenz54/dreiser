"""Application configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, List, Union
import secrets


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application
    PROJECT_NAME: str = "Draizer AI Trading"
    VERSION: str = "1.3.15"
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
    POSTGRES_PASSWORD: str = "changeme"
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
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    
    # External APIs
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    BINANCE_USE_TESTNET: bool = False  # Use mainnet for real prices
    
    # Trading pairs for AI analysis
    TRADING_PAIRS: List[str] = [
        "BTCUSDT",   # Bitcoin
        "ETHUSDT",   # Ethereum  
        "BNBUSDT",   # Binance Coin
        "SOLUSDT",   # Solana
        "ADAUSDT",   # Cardano
        "DOGEUSDT",  # Dogecoin
        "XRPUSDT",   # Ripple
        "DOTUSDT",   # Polkadot
    ]
    
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: Optional[str] = None
    
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: Optional[str] = None
    
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
    
    # Trading Settings (SIMULATION)
    INITIAL_BALANCE_USD: float = 1000.00
    DEFAULT_TRADING_SYMBOL: str = "BTCUSDT"
    AI_DECISION_INTERVAL_MINUTES: int = 15
    
    # News Sources
    # Option 1: CryptoPanic (RECOMMENDED - easier, better)
    CRYPTOPANIC_API_TOKEN: Optional[str] = None
    
    # Option 2: Telegram (optional, more complex)
    TELEGRAM_API_ID: Optional[int] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TELEGRAM_PHONE: Optional[str] = None
    TELEGRAM_NEWS_CHANNEL: Optional[str] = None  # e.g. "@crypto_news"
    
    # Context Management (NEW)
    DEEPSEEK_CONTEXT_COMPRESSION_THRESHOLD: int = 10  # Compress after N decisions
    
    # Enhanced Security (NEW)
    API_KEY_ROTATION_DAYS: int = 90
    AUDIT_LOG_RETENTION_DAYS: int = 365
    ENABLE_REQUEST_SIGNING: bool = False  # Enable for production
    ANOMALY_DETECTION_ENABLED: bool = True


settings = Settings()

