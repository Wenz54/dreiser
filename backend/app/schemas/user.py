"""User schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """User registration schema"""
    password: str = Field(..., min_length=12, max_length=100)


class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str
    mfa_code: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: uuid.UUID
    email: EmailStr  # Decrypted email
    username: str
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None


class MFASetup(BaseModel):
    """MFA setup response"""
    secret: str
    qr_code: str
    backup_codes: list[str]


class MFAVerify(BaseModel):
    """MFA verification"""
    code: str



