from datetime import datetime
import time
import requests

last_message = 0


def print_message(one_message):
    message_time = datetime.fromtimestamp(one_message['time']).strftime('%d.%m.%y %H:%M:%S')
    print(f'[{message_time}] {one_message["user"]}:')
    print(f'{one_message["text"]}\n')


while True:
    response = requests.get(
        'http://127.0.0.1:5000/get_messages',
        params={'last_message': last_message}
    )
    messages = response.json()['messages']

    for message in messages:
        print_message(message)
        last_message = message['time']

    time.sleep(1)
