"""Celery application configuration"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


# Create Celery app
celery_app = Celery(
    "draizer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    # AI trading sessions monitoring - каждые 2 минуты
    "monitor-ai-sessions": {
        "task": "app.tasks.ai_tasks.run_active_ai_sessions",
        "schedule": 120.0,  # Каждые 2 минуты (120 секунд)
    },
    # CryptoPanic news monitoring - каждые 2 минуты (ТОЛЬКО при активной AI сессии!)
    "monitor-crypto-news": {
        "task": "app.tasks.news_tasks.monitor_crypto_news",
        "schedule": crontab(minute="*/2"),  # Каждые 2 минуты
    },
    # API key rotation check - каждый день в 3:00
    "check-api-key-rotation": {
        "task": "app.tasks.security_tasks.check_api_key_rotation",
        "schedule": crontab(hour=3, minute=0),  # 03:00 daily
    },
    # Security audit cleanup - каждый день в 4:00
    "cleanup-old-audit-logs": {
        "task": "app.tasks.security_tasks.cleanup_old_audit_logs",
        "schedule": crontab(hour=4, minute=0),  # 04:00 daily
    },
}

celery_app.conf.task_routes = {
    "app.tasks.ai_tasks.*": {"queue": "celery"},  # Use default queue
    "app.tasks.news_tasks.*": {"queue": "celery"},
    "app.tasks.security_tasks.*": {"queue": "celery"},
}

# Auto-discover tasks in these modules
celery_app.autodiscover_tasks(['app.tasks'], force=True)

# Explicitly import tasks to ensure they're registered
from app.tasks import ai_tasks, news_tasks, security_tasks  # noqa
