import string
from random import choices

def generate_random_string(length: int) -> str:
    """
    Генерация рандомной строки
    :param length: Длина строки
    :return: Рандомно сгенерированнная строка
    """

    return ''.join(choices(string.ascii_letters, k=length))
