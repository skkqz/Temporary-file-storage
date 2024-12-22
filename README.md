# Temporary-file-storage

### Запуск celery
~~~Python
celery -A config.celery_app worker --loglevel=INFO -P solo
~~~

### Запуск doker-compose
~~~Python
docker-compose up -d
~~~
