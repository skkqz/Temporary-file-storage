import os
import ssl

from loguru import logger
from celery import Celery
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс для управления настройками
    """

    REDIS_PORT: int
    REDIS_PASSWORD: str
    BASE_URL: str = 'http://127.0.0.1:8000'
    REDIS_HOST: str
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    model_config = SettingsConfigDict(env_file=f"{BASE_DIR}/.env")


settings = Settings()

redis_url = f'rediss://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'

# Опции для работы с SSL, отключаем проверку сертификата (подходит для отладки)
ssl_options = {"ssl_cert_reqs": ssl.CERT_NONE}

# Инициализация экземпляра Celery
celery_app = Celery(
    'celery_tasks',  # Имя приложения Celery
    broker=redis_url,  # URL брокера задач (Redis)
    backend=redis_url  # URL для хранения результатов выполнения задач
)
