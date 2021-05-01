import os
import time

import logging
import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

HOMEWORK_STATUSES = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': ('Ревьюеру всё понравилось, '
                 'можно приступать к следующему уроку.'),
    'reviewing': 'Работа взята в ревью'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error('homework_name не обнаружен')
        return 'homework_name не обнаружен'
    homework_status = homework.get('status')
    if homework_status is None:
        logging.error('homework_status не обнаружен')
        return 'homework_status не обнаружен'
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    data = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
            headers=headers,
            params=data
        )
        return homework_statuses.json()
    except requests.RequestException as e:
        logging.error(f'Ошибка запроса: {e}', exc_info=True)
        return {}


def send_message(message, bot_client):
    logging.info('Сообщение отправлено')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug(f'Бот запущен, время запуска: {current_timestamp}')

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
        except Exception as e:
            logging.error(e, exc_info=True)
            send_message(
                f'Бот столкнулся с ошибкой {e.__class__.__name__}: {e}',
                bot_client
            )
            time.sleep(60)


if __name__ == '__main__':
    main()
