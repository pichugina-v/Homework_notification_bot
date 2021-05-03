import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

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

NAME_NOT_FOUND = 'Ключ "homework_name" не найден'
STATUS_NOT_FOUND = 'Ключ "status" не найден'
STATUS_ERROR = 'Неизвестный статус домашней работы "{status}"'
CONNECTION_ERROR = ('При обращении к {api} с параметрами токен - {token}, '
                    'дата - {date} произошел сбой сети, ошибка: {error}')
SERVER_ERROR = ('Сервер вернул ошибку на запрос {api} '
                'с параметрами токен - {token}, дата - {date}, '
                ' причина ошибки: {error}')
BOT_ACTIVATION = 'Бот запущен, время запуска: {date}'
MESSAGE_INFO = 'Отправка сообщения "{message}"'
VERDICT_INFO = 'У вас проверили работу "{name}"!\n\n{verdict}'


def parse_homework_status(homework):
    try:
        name = homework['homework_name']
    except KeyError:
        raise KeyError(NAME_NOT_FOUND)
    try:
        status = homework['status']
    except KeyError:
        raise KeyError(STATUS_NOT_FOUND)
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        raise KeyError(STATUS_ERROR.format(status=status))
    return VERDICT_INFO.format(name=name, verdict=verdict)


def get_homework_statuses(current_timestamp):
    data = {'from_date': current_timestamp}
    try:
        response = requests.get(
            PRAKTIKUM_API,
            headers=HEADER,
            params=data
        )
    except requests.RequestException as error:
        raise requests.RequestException(CONNECTION_ERROR.format(
            api=PRAKTIKUM_API,
            token=PRAKTIKUM_TOKEN,
            date=current_timestamp,
            error=error
        ))
    json_data = response.json()
    if json_data.get('error'):
        raise ValueError(SERVER_ERROR.format(
            api=PRAKTIKUM_API,
            token=PRAKTIKUM_TOKEN,
            date=current_timestamp,
            error=json_data['error']
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
            logging.error(error, exc_info=True)
            time.sleep(60)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
