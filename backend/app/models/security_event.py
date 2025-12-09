"""Security events model"""
from sqlalchemy import Column, ForeignKey, String, Boolean, Enum as SQLEnum, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class SecurityEventSeverity(str, enum.Enum):
    """Security event severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityEvent(Base):
    """Security events and incidents"""
    
    __tablename__ = "security_events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    event_type = Column(String(50), nullable=False, comment="Event type (FAILED_LOGIN, MFA_FAILED, etc.)")
    severity = Column(SQLEnum(SecurityEventSeverity), nullable=False)
    
    ip_address = Column(INET, nullable=True)
    details = Column(JSONB, nullable=True, comment="Event details")
    
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="security_events")

