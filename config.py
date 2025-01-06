import os
import ssl
import redis

from loguru import logger
from celery import Celery
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс для управления настройками
    """

    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_HOST: str
    REDIS_USERNAME: str
    BASE_URL: str = "http://127.0.0.1:8000"
    BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")

    model_config = SettingsConfigDict(env_file=f"{os.path.join(BASE_DIR, '.env')}")


# Инициализация настроек
settings = Settings()

# Формирование URL для подключения к Redis
redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

# Настройка клиента Redis
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        password=settings.REDIS_PASSWORD,
        ssl=False,
        ssl_cert_reqs=None
    )
    redis_client.ping()
    logger.info("Подключение к Redis успешно выполнено.")
except redis.exceptions.RedisError as e:
    logger.error(f"Ошибка подключения к Redis: {e}")
