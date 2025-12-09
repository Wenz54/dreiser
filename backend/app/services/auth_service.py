"""Authentication service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import pyotp
import io
import base64

from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, encryption_service


class AuthService:
    """Authentication and user management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, email: str, username: str, password: str) -> User:
        """
        Создать нового пользователя
        
        Args:
            email: Email пользователя
            username: Username
            password: Пароль (будет захеширован)
        
        Returns:
            User object
        """
        # Проверить уникальность
        existing = await self.get_user_by_email(email)
        if existing:
            raise Exception("User with this email already exists")
        
        existing = await self.get_user_by_username(username)
        if existing:
            raise Exception("Username already taken")
        
        # Хешировать пароль (Argon2id)
        password_hash = get_password_hash(password)
        
        # Создать пользователя
        user = User(
            email=encryption_service.encrypt(email),  # Шифруем email
            username=username,
            password_hash=password_hash,
            mfa_enabled=False,
            is_active=True,
            is_verified=False  # Требуется верификация email
        )
        
        self.db.add(user)
        await self.db.flush()
        return user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Аутентификация пользователя
        
        Args:
            username: Username
            password: Пароль
        
        Returns:
            User если успешно, None если нет
        """
        user = await self.get_user_by_username(username)
        if not user:
            print(f"❌ User not found: {username}")
            return None
        
        print(f"✅ User found: {username}")
        print(f"   Password hash: {user.password_hash[:50]}...")
        print(f"   Is active: {user.is_active}")
        
        if not user.is_active:
            raise Exception("User account is inactive")
        
        try:
            password_valid = verify_password(password, user.password_hash)
            print(f"   Password valid: {password_valid}")
            if not password_valid:
                return None
        except Exception as e:
            print(f"❌ Password verification error: {e}")
            return None
        
        return user
    
    async def verify_mfa(self, user: User, code: str) -> bool:
        """
        Верификация 2FA кода
        
        Args:
            user: User object
            code: 6-digit TOTP code
        
        Returns:
            True если код валиден
        """
        if not user.mfa_enabled or not user.mfa_secret:
            return True  # MFA не включена
        
        # Дешифровать secret
        secret = encryption_service.decrypt(user.mfa_secret)
        totp = pyotp.TOTP(secret)
        
        return totp.verify(code, valid_window=1)
    
    async def setup_mfa(self, user: User) -> dict:
        """
        Настроить 2FA для пользователя
        
        Returns:
            {
                "secret": str,
                "qr_code": str (base64),
                "backup_codes": list
            }
        """
        # Генерируем secret
        secret = pyotp.random_base32()
        
        # Шифруем и сохраняем
        user.mfa_secret = encryption_service.encrypt(secret)
        
        # Генерируем QR код
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.username,
            issuer_name="Draizer AI Trading"
        )
        
        # TODO: Генерировать QR код изображение (требует qrcode library)
        # import qrcode
        # qr = qrcode.make(provisioning_uri)
        # buffer = io.BytesIO()
        # qr.save(buffer, format='PNG')
        # qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        qr_base64 = "TODO_QR_CODE"  # Placeholder для MVP
        
        # Backup codes (для восстановления)
        backup_codes = [pyotp.random_base32()[:8] for _ in range(5)]
        
        return {
            "secret": secret,
            "qr_code": qr_base64,
            "backup_codes": backup_codes
        }
    
    async def enable_mfa(self, user: User, code: str) -> bool:
        """
        Включить 2FA после верификации кода
        
        Args:
            user: User object
            code: Проверочный код
        
        Returns:
            True если успешно
        """
        if await self.verify_mfa(user, code):
            user.mfa_enabled = True
            await self.db.flush()
            return True
        return False
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Получить пользователя по ID"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email (с учетом шифрования)"""
        encrypted_email = encryption_service.encrypt(email)
        stmt = select(User).where(User.email == encrypted_email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username"""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def create_tokens(self, user_id: uuid.UUID) -> dict:
        """
        Создать JWT токены
        
        Returns:
            {
                "access_token": str,
                "refresh_token": str,
                "token_type": "bearer"
            }
        """
        access_token = create_access_token(str(user_id))
        refresh_token = create_refresh_token(str(user_id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }












