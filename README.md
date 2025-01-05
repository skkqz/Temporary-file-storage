# Temporary-file-storage
## Временное хранение файлов

### Запуск celery
~~~Python
celery -A celery_app.task_delete_file.celery_app worker --loglevel=INFO -P solo
~~~

### Запуск doker-compose
~~~Python
docker-compose up -d
~~~
