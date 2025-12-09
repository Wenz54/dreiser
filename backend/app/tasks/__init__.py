"""Celery background tasks"""

# Import all tasks to register them with Celery
from app.tasks.ai_tasks import *  # noqa
from app.tasks.news_tasks import *  # noqa
from app.tasks.security_tasks import *  # noqa

