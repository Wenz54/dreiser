"""Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, MFASetup, MFAVerify
from app.schemas.token import Token
from app.services.auth_service import AuthService
from app.services.portfolio_service import PortfolioService
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя
    
    - Создает пользователя
    - Создает виртуальный портфель с $1000
    """
    auth_service = AuthService(db)
    portfolio_service = PortfolioService(db)
    
    try:
        # Создать пользователя
        user = await auth_service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password
        )
        
        # Создать портфель
        await portfolio_service.create_portfolio(user.id)
        
        await db.commit()
        await db.refresh(user)
        
        # Вернуть с расшифрованным email
        return UserResponse(
            id=user.id,
            email=user.decrypted_email,
            username=user.username,
            is_active=user.is_active,
            is_verified=user.is_verified,
            mfa_enabled=user.mfa_enabled,
            last_login=user.last_login,
            created_at=user.created_at
        )
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Вход в систему
    
    - Проверяет username и password
    - Проверяет 2FA (если включен)
    - Возвращает JWT токены
    """
    print(f"🔐 Login attempt: username={credentials.username}, password='{credentials.password}'")
    
    auth_service = AuthService(db)
    
    # Аутентификация
    user = await auth_service.authenticate_user(
        username=credentials.username,
        password=credentials.password
    )
    
    if not user:
        print(f"❌ Authentication failed for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    print(f"✅ User authenticated: {user.username}")
    
    # Проверка 2FA
    if user.mfa_enabled:
        if not credentials.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA code required"
            )
        
        if not await auth_service.verify_mfa(user, credentials.mfa_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )
    
    # Создать токены
    tokens = auth_service.create_tokens(user.id)
    
    # Обновить last_login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()
    
    return tokens


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Выход из системы
    
    В MVP просто endpoint для симметрии
    В production - invalidate токены в Redis
    """
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    # TODO: Implement refresh token logic
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить access token используя refresh token
    
    TODO: Implement
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented yet"
    )


@router.post("/mfa/setup", response_model=MFASetup)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Настроить 2FA
    
    Возвращает secret и QR код
    """
    auth_service = AuthService(db)
    
    mfa_data = await auth_service.setup_mfa(current_user)
    await db.commit()
    
    return mfa_data


@router.post("/mfa/verify")
async def verify_mfa(
    mfa_data: MFAVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Верифицировать и включить 2FA
    
    Проверяет TOTP код и активирует 2FA
    """
    auth_service = AuthService(db)
    
    success = await auth_service.enable_mfa(current_user, mfa_data.code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code"
        )
    
    await db.commit()
    
    return {"message": "MFA enabled successfully"}



