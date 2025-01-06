import os
import datetime

from loguru import logger
from fastapi import APIRouter, UploadFile, HTTPException, Form
from starlette.responses import FileResponse

from api.utils import generate_random_string
from config import settings, redis_client
from celery_app.task_delete_file import celery_app

router = APIRouter(tags=['API'])


@router.post('/api/upload')
async def upload_file(file: UploadFile, expiration_minutes: int = Form(...)):
    """
    Загружает файл и сохраняет метаданные в Redis.
    :param file: Файл для загрузки.
    :param expiration_minutes: Срок жизни файла в минутах.
    :return: Метаданные загруженного файла.
    """
    try:
        # Прочитать загруженный файл
        file_content = await file.read()

        max_file_size = 5 * 1024 * 1024  # 5 МБ в байтах
        if len(file_content) > max_file_size:
            raise HTTPException(status_code=413, detail='Превышен максимальный размер файла (5 МБ).')

        upload_dir = settings.UPLOAD_DIR
        total_size = sum(
            os.path.getsize(os.path.join(upload_dir, f)) for f in os.listdir(upload_dir) if os.path.join(upload_dir, f)
        )

        max_total_size = 100 * 1024 * 1024  # 100 МБ в байтах
        if total_size + len(file_content) > max_total_size:
            raise HTTPException(
                status_code=507,
                detail='Превышен общий лимит размера файлов (100 МБ). Освободите место и повторите попытку.'
            )
        start_file_name = file.filename

        # Генерация уникального имени файла и ID для удаления
        file_extension = os.path.splitext(file.filename)[1]
        file_id = generate_random_string(12)
        dell_id = generate_random_string(12)

        # Сохранить файл на диск
        file_path = os.path.join(settings.UPLOAD_DIR, file_id + file_extension)
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Рассчитать время истечения в секундах
        expiration_seconds = expiration_minutes * 60
        expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expiration_seconds)

        logger.info(f'Отправка задачи на удаление файла {file_id} с задержкой {expiration_seconds} секунд.')
        celery_app.send_task('delete_file_scheduled', args=[file_id, dell_id], countdown=expiration_seconds)
        logger.info('Задача успешно отправлена в Celery.')

        # URL-адреса для метаданных
        download_url = f'{settings.BASE_URL}/file/{file_id}'

        # Сохранить метаданные в Redis
        redis_key = f'file:{file_id}'  # Уникальный ключ для файла
        redis_client.hmset(
            redis_key,
            {
                'file_path': file_path,
                'dell_id': dell_id,
                'download_url': download_url,
                'expiration_time': int(expiration_time.timestamp()),
                'start_file_name': start_file_name
            }
        )
        return {
            "message": "Файл успешно загружен",
            "file_id": file_id,
            "dell_id": dell_id,
            "download_url": download_url,
            "expiration_time": expiration_time.isoformat(),
            "expiration_seconds": expiration_seconds
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {str(e)}")


@router.delete('/delete/{file_id}/{dell_id}/')
async def delete_file(file_id: str, dell_id: str):
    """
    Удаляет файл и очищает данные в Redis.
    :param file_id: Уникальный идентификатор файла.
    :param dell_id: Уникальный идентификатор для удаления файла.
    :return: Сообщение об успешном удалении.
    """
    redis_key = f'file:{file_id}'
    file_info = redis_client.hgetall(redis_key)

    if not file_info:
        raise HTTPException(status_code=404, detail='Файл не найден')

    dell_id_redis = file_info.get(b'dell_id').decode()
    if dell_id_redis != dell_id:
        raise HTTPException(status_code=403, detail='ID удаления не совпадает.')

    file_path = file_info.get(b'file_path').decode()

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f'Файл {file_path} успешно удалён!')
        else:
            logger.warning(f'Файл {file_path} не найден')

        redis_client.delete(redis_key)
        return {'message': 'Файл успешно удалён и запись в Redis очищена'}
    except OSError as e:
        logger.error(f"Ошибка при удалении файла {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления файла: {str(e)}")


@router.get("/view_file/{file_id}")
async def get_file_info(file_id: str):
    """
    Получает информацию о файле.
    :param file_id: Уникальный идентификатор файла.
    :return: Информация о файле.
    """
    redis_key = f"file:{file_id}"
    file_info = redis_client.hgetall(redis_key)

    if not file_info:
        raise HTTPException(status_code=404, detail="Файл не найден.")

    file_path = file_info.get(b"file_path").decode()
    download_url = file_info.get(b"download_url").decode()
    expiration_time = int(file_info.get(b"expiration_time").decode())
    start_file_name = file_info.get(b"start_file_name").decode()

    return {
        "file_id": file_id,
        "file_path": file_path,
        "download_url": download_url,
        "expiration_time": expiration_time,
        "start_file_name": start_file_name,
    }


@router.get("/file/{file_id}")
async def download_file(file_id: str):
    """
    Скачивает файл по идентификатору.
    :param file_id: Уникальный идентификатор файла.
    :return: Файл для скачивания.
    """
    redis_key = f"file:{file_id}"
    file_info = redis_client.hgetall(redis_key)

    if not file_info:
        logger.warning(f'Запрашиваемый файл {file_id} не найден.')
        raise HTTPException(status_code=404, detail='Срок жизни файла истёк.')

    file_path = file_info.get(b"file_path").decode()
    start_file_name = file_info.get(b"start_file_name").decode()

    return FileResponse(
        path=file_path,
        filename=start_file_name,
        media_type="application/octet-stream"
    )
