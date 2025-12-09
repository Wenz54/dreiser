"""Audit log model"""
from sqlalchemy import Column, ForeignKey, String, Integer, Text, Index, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship

from app.db.base import Base


class AuditLog(Base):
    """Audit log for all user actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    action = Column(String(100), nullable=False, comment="Action performed")
    resource = Column(String(100), nullable=True, comment="Resource affected")
    
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    request_data = Column(JSONB, nullable=True, comment="Request data")
    response_status = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_action_created', 'action', 'created_at'),
    )

