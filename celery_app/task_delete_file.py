import requests

from celery import Celery
from config import settings, redis_url


celery_app = Celery(
    "celery_app",
    broker=redis_url,  # URL брокера задач (Redis)
    backend=redis_url,  # URL для хранения результатов выполнения задач
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    enable_utc=True,
    timezone='Europe/Moscow',
    broker_connection_retry_on_startup=True,
)


@celery_app.task(
    name='delete_file_scheduled',
    bind=True,
    max_retries=3,
    default_retry_delay=5
)
def delete_file_scheduled(self, file_id, dell_id):
    """Задача для отложенного удаления файла"""

    try:
        response = requests.delete(f"{settings.BASE_URL}/delete/{file_id}/{dell_id}")
        response.raise_for_status()
        return response.status_code
    except requests.RequestException as exc:
        self.retry(exc=exc)
    except Exception as e:
        return None
