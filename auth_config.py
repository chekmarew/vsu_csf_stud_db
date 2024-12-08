import random
from datetime import timedelta


class AuthCodeConfig:
    # Минимальный интервал между отправкой кода
    SEND_CODE_INTERVAL = timedelta(minutes=2)

    # Время "жизни" кода для авторизации
    SEND_CODE_TIMELIFE = timedelta(minutes=3)

    # Максимальное количество неправильных попыток ввода кода
    MAX_FAIL_CODE_COUNT = 3

    # Обзательная аутентификация по e-mail для пользователей с возможностью редактирования
    MANDATORY_AUTHENTICATION_EMAIL = False
    DEBUG_UNIVERSAL_PASSWORD = {

    }
    DEBUG_NOT_SEND_EMAIL = False
    DEBUG_NOT_SEND_SMS = False
    @staticmethod
    def generate_code():
        return random.randrange(start=100000, stop=999999, step=1)