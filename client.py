import requests
from server import APP_NAME, BOT_HELP

# приветствие пользователя
print(f'Добро пожаловать в {APP_NAME}\n\n')

# цикл для выбора имени пользователя и ожидание подтверждения сервера о допустимости имени
while True:
    my_name = input('Придумай себе ник: ')
    response = requests.post('http://127.0.0.1:5000/new_user', json={"new_name": my_name})
    if response.json().get('result'):
        print(f'Теперь Вы можете отправлять сообщения в чат. Напишите "{BOT_HELP}", чтобы узнать, что умеет чат-бот.\n')
        break
    else:
        print(f'К сожалению, в чате уже есть пользователь с именем "{my_name}"\n')

# цикл для приёма сообщений от пользователя и их отправка на сервер
while True:
    my_text = input('Введите текст сообщения [Q - закрыть чат]: ')
    if my_text == 'Q':
        print(f'Даже не попрощаетесь? Что ж, до скорых встреч, {my_name}\n')
        break
    else:
        requests.post('http://127.0.0.1:5000/send_message',
                      json={"user": my_name,
                            "text": my_text
                            }
                      )
