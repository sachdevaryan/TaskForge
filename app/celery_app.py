from celery import Celery
from app.config import settings

celery_app = Celery(
    "taskforge",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.task_routes = {
    "app.tasks.process_image_high": {"queue": "high_priority"},
    "app.tasks.process_image_low": {"queue": "low_priority"},
}