"""Enhanced Security Audit model"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy import BigInteger, ForeignKey
import enum

from app.db.base import Base


class AnomalyType(str, enum.Enum):
    """Types of detected anomalies"""
    UNUSUAL_IP = "UNUSUAL_IP"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SUSPICIOUS_PATTERN = "SUSPICIOUS_PATTERN"
    FAILED_AUTH_SPIKE = "FAILED_AUTH_SPIKE"
    UNUSUAL_TRADING_VOLUME = "UNUSUAL_TRADING_VOLUME"
    API_KEY_MISUSE = "API_KEY_MISUSE"


class SecurityAuditLog(Base):
    """Enhanced audit log with encryption and anomaly detection"""
    
    __tablename__ = "security_audit_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Request details
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    method = Column(String(10), nullable=False, comment="HTTP method")
    endpoint = Column(String(255), nullable=False)
    
    # Security context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(50), nullable=True, comment="Unique request ID")
    
    # HMAC signature verification
    signature_valid = Column(Boolean, nullable=True, comment="Was request signature valid?")
    signature_hash = Column(String(64), nullable=True, comment="Request HMAC-SHA256 signature")
    
    # Data (encrypted)
    request_data_encrypted = Column(Text, nullable=True, comment="AES encrypted request data")
    response_status = Column(Integer, nullable=True)
    
    # Anomaly detection
    is_anomaly = Column(Boolean, default=False)
    anomaly_type = Column(SQLEnum(AnomalyType), nullable=True)
    anomaly_score = Column(Integer, default=0, comment="Anomaly score 0-100")
    
    # Performance
    response_time_ms = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    
    # Encryption flag
    is_encrypted = Column(Boolean, default=False)


class APIKeyRotation(Base):
    """API key rotation tracking"""
    
    __tablename__ = "api_key_rotations"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Key info
    key_hash = Column(String(64), nullable=False, comment="SHA256 hash of API key")
    key_prefix = Column(String(8), nullable=False, comment="First 8 chars for identification")
    
    # Status
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(255), nullable=True)
    
    # Usage stats
    last_used_at = Column(DateTime, nullable=True)
    total_requests = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True, comment="Auto-expiry date")







