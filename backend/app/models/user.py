"""User model"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.db.base import BaseModel
from app.core.security import encryption_service


class User(BaseModel):
    """User account model"""
    
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
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def decrypted_email(self) -> str:
        """Расшифрованный email для отображения"""
        try:
            return encryption_service.decrypt(self.email)
        except Exception:
            return self.email  # Fallback если не зашифрован



