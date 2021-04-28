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

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework.get('status') == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    data = {'from_date': current_timestamp}
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        headers=headers,
        params=data,
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Message sent')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = 0
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug(f'Bot activated, activation time: {current_timestamp}')

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
                f'Бот столкнулся с ошибкой: {e.__class__.__name__}',
                bot_client
            )
            time.sleep(60)


if __name__ == '__main__':
    main()
