import  redis
from loguru import logger



def connect_redis():
    r = redis.Redis(host='localhost', port=6379, db=0, password='password', ssl=False, )

    try:
        info = r.info()
        logger.info(info['redis_version'])
        response = r.ping()

        if response:
            logger.info('Подключение успешно!')
        else:
            logger.info('Не удалось поключиться к Redis')

    except redis.exceptions.RedisError as e:
        logger.info(f'Ошибка: {e}')


if '__main__' == __name__:
    connect_redis()
