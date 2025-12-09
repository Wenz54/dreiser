"""Chat messages model - для GPT-4 аналитического чата"""
from sqlalchemy import Column, ForeignKey, String, Text, Integer, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.db.base import BaseModel


class ChatRole(str, enum.Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """GPT-4 chat message"""
    
    __tablename__ = "chat_messages"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    role = Column(SQLEnum(ChatRole), nullable=False)
    content = Column(Text, nullable=False)
    
    context_data = Column(JSONB, nullable=True, comment="Portfolio/market snapshot")
    tokens_used = Column(Integer, nullable=True)
    model = Column(String(50), default="gpt-4", nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    
    __table_args__ = (
        Index('idx_chat_user_created', 'user_id', 'created_at'),
    )

