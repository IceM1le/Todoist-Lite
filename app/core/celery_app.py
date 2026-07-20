from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "todoist",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.core.tasks"]
)
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,
)
celery_app.conf.beat_schedule = {
    "check-deadlines": {
        "task": "app.core.tasks.check_deadlines",
        "schedule": crontab(hour=9, minute=0),
    },
}
celery_app.autodiscover_tasks(["app.core"])
