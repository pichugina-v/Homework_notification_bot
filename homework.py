import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from telegram.utils.helpers import encode_conversations_to_json

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADER = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
PRAKTIKUM_API = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

HOMEWORK_VERDICTS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.',
    'reviewing': 'Работа взята в ревью'
}

STATUS_ERROR = 'Неизвестный статус домашней работы "{status}"'
CONNECTION_ERROR = ('При обращении к {url} с параметрами {headers}, '
                    '{params} произошел сбой сети, ошибка: {error}')
SERVER_ERROR = ('Сервер вернул ошибку на запрос {url} '
                'с параметрами {headers}, {params}, '
                ' причина ошибки: {error}')
BOT_ACTIVATION = 'Бот запущен, время запуска: {date}'
MESSAGE_INFO = 'Отправка сообщения "{message}"'
VERDICT_INFO = 'У вас проверили работу "{name}"!\n\n{verdict}'
LOGGING_INFO = 'Обнаружена ошибка: {error}'


def parse_homework_status(homework):
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(STATUS_ERROR.format(status=status))
    return VERDICT_INFO.format(
        name=homework['homework_name'],
        verdict=HOMEWORK_VERDICTS[status]
    )


def get_homework_statuses(current_timestamp):
    parameters = dict(
        url=PRAKTIKUM_API,
        headers=HEADER,
        params={'from_date': current_timestamp}
    )
    error_values = ['error', 'code']
    try:
        response = requests.get(**parameters)
    except requests.RequestException as error:
        raise ConnectionError(CONNECTION_ERROR.format(
            **parameters,
            error=error
        ))
    json_data = response.json()
    for value in error_values:
        if value in json_data:
            raise ValueError(SERVER_ERROR.format(
                **parameters,
                error=json_data.get(value)
            ))
    return json_data


def send_message(message, bot_client):
    logging.info(MESSAGE_INFO.format(message=message))
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug(BOT_ACTIVATION.format(date=current_timestamp))

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(900)
        except Exception as error:
            logging.error(
                LOGGING_INFO.format(error=error),
                exc_info=True
            )
            try:
                send_message(f'{error.__class__.__name__}: {error}',
                             bot_client)
            except Exception as sending_exception:
                logging.error(
                    LOGGING_INFO.format(
                        error=sending_exception,
                        exc_info=True
                    ))
            time.sleep(60)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
    )
    main()
