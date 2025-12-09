"""Enhanced Security Layer - Maximum Protection"""
import hmac
import hashlib
import secrets
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import json

from app.core.config import settings
from app.core.security import encryption_service


class RequestSigner:
    """
    HMAC-SHA256 request signing для защиты API
    
    Client должен подписывать каждый request:
    signature = HMAC-SHA256(api_key_secret, request_body + timestamp)
    """
    
    @staticmethod
    def sign_request(api_key_secret: str, request_body: str, timestamp: int) -> str:
        """
        Создать подпись запроса
        
        Args:
            api_key_secret: Secret key пользователя
            request_body: JSON body request
            timestamp: Unix timestamp
        
        Returns:
            HMAC-SHA256 hex signature
        """
        message = f"{request_body}{timestamp}"
        signature = hmac.new(
            api_key_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_request(
        api_key_secret: str,
        request_body: str,
        timestamp: int,
        provided_signature: str,
        max_age_seconds: int = 300  # 5 минут
    ) -> bool:
        """
        Проверить подпись запроса
        
        Args:
            api_key_secret: Secret key пользователя
            request_body: JSON body request
            timestamp: Unix timestamp из request
            provided_signature: Подпись из header
            max_age_seconds: Максимальный возраст запроса
        
        Returns:
            True if valid, False otherwise
        """
        # Проверка времени (защита от replay attacks)
        current_time = int(time.time())
        if abs(current_time - timestamp) > max_age_seconds:
            return False
        
        # Вычислить ожидаемую подпись
        expected_signature = RequestSigner.sign_request(api_key_secret, request_body, timestamp)
        
        # Constant-time comparison (защита от timing attacks)
        return hmac.compare_digest(expected_signature, provided_signature)


class AnomalyDetector:
    """
    Real-time anomaly detection
    
    Отслеживает подозрительные паттерны:
    - Необычные IP адреса
    - Спайки failed auth
    - Подозрительные объемы торговли
    """
    
    def __init__(self):
        # In-memory cache для быстрого детектирования
        # В production использовать Redis
        self.failed_attempts: Dict[str, list] = {}
        self.request_rates: Dict[str, list] = {}
        self.user_ips: Dict[str, set] = {}
    
    def check_failed_auth(self, user_id: str) -> tuple[bool, int]:
        """
        Проверить failed auth spike
        
        Returns:
            (is_anomaly, score)
        """
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = []
        
        # Очистить старые attempts (>1 час)
        cutoff = datetime.now() - timedelta(hours=1)
        self.failed_attempts[user_id] = [
            ts for ts in self.failed_attempts[user_id]
            if ts > cutoff
        ]
        
        # Добавить текущий attempt
        self.failed_attempts[user_id].append(datetime.now())
        
        count = len(self.failed_attempts[user_id])
        
        # Аномалия если >5 за час
        if count > 5:
            return (True, min(count * 10, 100))
        
        return (False, 0)
    
    def check_unusual_ip(self, user_id: str, ip_address: str) -> tuple[bool, int]:
        """
        Проверить unusual IP для пользователя
        
        Returns:
            (is_anomaly, score)
        """
        if user_id not in self.user_ips:
            self.user_ips[user_id] = set()
        
        # Если новый IP (и не первый login)
        if ip_address not in self.user_ips[user_id] and len(self.user_ips[user_id]) > 0:
            # Это может быть легитимно, но отмечаем
            self.user_ips[user_id].add(ip_address)
            return (True, 30)  # Medium severity
        
        self.user_ips[user_id].add(ip_address)
        return (False, 0)
    
    def check_rate_limit(self, user_id: str, endpoint: str) -> tuple[bool, int]:
        """
        Проверить rate limit per user per endpoint
        
        Returns:
            (is_exceeded, score)
        """
        key = f"{user_id}:{endpoint}"
        
        if key not in self.request_rates:
            self.request_rates[key] = []
        
        # Очистить старые requests (>1 минута)
        cutoff = datetime.now() - timedelta(minutes=1)
        self.request_rates[key] = [
            ts for ts in self.request_rates[key]
            if ts > cutoff
        ]
        
        # Добавить текущий request
        self.request_rates[key].append(datetime.now())
        
        count = len(self.request_rates[key])
        
        # Разные лимиты для разных endpoints
        limit = 10 if "/auth/" in endpoint else 50
        
        if count > limit:
            return (True, min((count - limit) * 5, 100))
        
        return (False, 0)


class SecureDataEncryption:
    """
    Дополнительное шифрование для sensitive logs
    """
    
    @staticmethod
    def encrypt_audit_data(data: Dict[str, Any]) -> str:
        """
        Шифровать audit log data
        
        Args:
            data: Dictionary с данными
        
        Returns:
            Encrypted string
        """
        json_str = json.dumps(data)
        return encryption_service.encrypt(json_str)
    
    @staticmethod
    def decrypt_audit_data(encrypted: str) -> Dict[str, Any]:
        """
        Дешифровать audit log data
        
        Args:
            encrypted: Encrypted string
        
        Returns:
            Decrypted dictionary
        """
        json_str = encryption_service.decrypt(encrypted)
        return json.loads(json_str)


class APIKeyManager:
    """
    API Key generation and rotation
    """
    
    @staticmethod
    def generate_api_key_pair() -> tuple[str, str]:
        """
        Генерировать пару API key + secret
        
        Returns:
            (api_key, api_secret)
        """
        # API Key: публичный идентификатор
        api_key = f"dk_{secrets.token_urlsafe(32)}"
        
        # API Secret: приватный ключ для подписи
        api_secret = secrets.token_urlsafe(64)
        
        return (api_key, api_secret)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """
        Хешировать API key для хранения в БД
        
        Returns:
            SHA256 hash
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def should_rotate(created_at: datetime, rotation_days: int = 90) -> bool:
        """
        Проверить, нужна ли ротация ключа
        
        Args:
            created_at: Дата создания ключа
            rotation_days: Период ротации (default: 90 дней)
        
        Returns:
            True if rotation needed
        """
        age = datetime.utcnow() - created_at
        return age.days >= rotation_days


# Singletons
request_signer = RequestSigner()
anomaly_detector = AnomalyDetector()
secure_encryption = SecureDataEncryption()
api_key_manager = APIKeyManager()


async def verify_request_signature(request: Request):
    """
    Middleware для проверки HMAC подписи
    
    Headers требуемые:
    - X-API-Key: API key пользователя
    - X-Signature: HMAC-SHA256 signature
    - X-Timestamp: Unix timestamp
    """
    # Проверяем только для критичных endpoints
    if request.url.path.startswith("/api/v1/trading") or \
       request.url.path.startswith("/api/v1/ai"):
        
        api_key = request.headers.get("X-API-Key")
        signature = request.headers.get("X-Signature")
        timestamp_str = request.headers.get("X-Timestamp")
        
        if not all([api_key, signature, timestamp_str]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing signature headers"
            )
        
        # TODO: Получить api_secret из БД по api_key
        # api_secret = await get_user_api_secret(api_key)
        
        # Для localhost MVP - пропускаем
        # В production - обязательно проверять
        pass







