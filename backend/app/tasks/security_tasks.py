"""Celery tasks для security maintenance"""
from celery import shared_task
from sqlalchemy import delete, select
from datetime import datetime, timedelta
import asyncio

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.security_audit import SecurityAuditLog, APIKeyRotation
from app.core.security_enhanced import api_key_manager


@celery_app.task(name="app.tasks.security_tasks.check_api_key_rotation")
def check_api_key_rotation():
    """
    Проверить API keys, требующие ротации
    
    Отправляет уведомления пользователям о необходимости обновления ключей
    """
    asyncio.run(_check_api_key_rotation_async())


async def _check_api_key_rotation_async():
    """Async implementation"""
    
    async with AsyncSessionLocal() as db:
        # Получить активные ключи
        stmt = select(APIKeyRotation).where(
            APIKeyRotation.is_active == True,
            APIKeyRotation.revoked_at.is_(None)
        )
        result = await db.execute(stmt)
        active_keys = result.scalars().all()
        
        rotation_needed = []
        
        for key in active_keys:
            if api_key_manager.should_rotate(key.created_at, rotation_days=90):
                rotation_needed.append(key)
        
        if rotation_needed:
            print(f"⚠️ {len(rotation_needed)} API keys need rotation:")
            for key in rotation_needed:
                print(f"  - User {key.user_id}: key {key.key_prefix}*** (age: {(datetime.utcnow() - key.created_at).days} days)")
                
                # TODO: Send email notification to user
                # await send_email(user.email, "API Key Rotation Required", ...)
        
        else:
            print("✅ All API keys are fresh")


@celery_app.task(name="app.tasks.security_tasks.cleanup_old_audit_logs")
def cleanup_old_audit_logs():
    """
    Очистка старых audit logs (>1 год)
    
    Для compliance храним logs 1 год, потом удаляем
    """
    asyncio.run(_cleanup_old_audit_logs_async())


async def _cleanup_old_audit_logs_async():
    """Async implementation"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=365)
    
    async with AsyncSessionLocal() as db:
        # Удалить старые audit logs
        stmt = delete(SecurityAuditLog).where(
            SecurityAuditLog.created_at < cutoff_date
        )
        result = await db.execute(stmt)
        await db.commit()
        
        deleted_count = result.rowcount
        
        if deleted_count > 0:
            print(f"🗑️ Deleted {deleted_count} old audit log entries (older than 1 year)")
        else:
            print("✅ No old audit logs to cleanup")


@celery_app.task(name="app.tasks.security_tasks.analyze_security_anomalies")
def analyze_security_anomalies():
    """
    Анализ security anomalies за последние 24 часа
    
    Отправляет алерты если обнаружены подозрительные паттерны
    """
    asyncio.run(_analyze_security_anomalies_async())


async def _analyze_security_anomalies_async():
    """Async implementation"""
    
    since_time = datetime.utcnow() - timedelta(hours=24)
    
    async with AsyncSessionLocal() as db:
        # Получить аномалии за 24 часа
        stmt = select(SecurityAuditLog).where(
            SecurityAuditLog.created_at >= since_time,
            SecurityAuditLog.is_anomaly == True
        )
        result = await db.execute(stmt)
        anomalies = result.scalars().all()
        
        if anomalies:
            # Группировать по типам
            by_type = {}
            for anomaly in anomalies:
                anomaly_type = anomaly.anomaly_type.value if anomaly.anomaly_type else "UNKNOWN"
                if anomaly_type not in by_type:
                    by_type[anomaly_type] = []
                by_type[anomaly_type].append(anomaly)
            
            print(f"⚠️ {len(anomalies)} security anomalies detected in last 24h:")
            for anomaly_type, events in by_type.items():
                print(f"  - {anomaly_type}: {len(events)} events")
                
                # Высокий приоритет для критичных типов
                if anomaly_type in ["FAILED_AUTH_SPIKE", "API_KEY_MISUSE"]:
                    print(f"    ⚠️ CRITICAL: Immediate attention required!")
                    # TODO: Send alert to admin
            
        else:
            print("✅ No security anomalies in last 24h")







