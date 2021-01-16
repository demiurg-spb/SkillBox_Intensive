from flask import Flask, request, abort
from datetime import datetime
import time
import json
import pickle
import requests
import re

# константы для работы
APP_NAME = 'SimChat'
DB_PATH = 'messages.db'
BANK_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'
WORD_URL = 'https://ru.wiktionary.org/wiki/'

# константы с командами чат-бота
BOT_NAME = 'БОТ'
BOT_WORD = 'СЛОВО'
BOT_MONEY = 'ВАЛЮТА'

# инициализация серверного приложения
app = Flask(APP_NAME)


# функция загрузки базы данных с именами пользователей и сообщениями
def load_db(path):
    try:
        with open(path, 'rb') as db_file:
            return pickle.load(db_file)
    except:
        return {
            'users': [],
            'messages': []
        }


# функция сохранения базы данных с именами пользователей и сообщениями
def save_db(database, path):
    try:
        with open(path, 'wb') as db_file:
            pickle.dump(database, db_file)
    except:
        pass


chat_database = load_db(DB_PATH)


# стартовая страница сервера
@app.route("/")
def index():
    return f'Это сервер для работы {APP_NAME}.'


# запрос на добавление пользователя в чат, проверка его имени на уникальность
@app.route("/new_user", methods=['POST'])
def check_unique_user():
    if not isinstance(request.json, dict):
        return abort(400)
    new_name = request.json.get('new_name')
    if new_name in chat_database['users']:
        return {'result': False}
    else:
        chat_database['users'].append(new_name)
        return {'result': True}


# обработка нового сообщения от пользователя
@app.route("/send_message", methods=['POST'])
def send_message():
    if not isinstance(request.json, dict):
        return abort(400)

    user = request.json.get('user')
    text = request.json.get('text')

    # проверка сообщения на корректность
    if not isinstance(user, str) or user == "" \
            or not isinstance(text, str) or text == "":
        return abort(400)

    # обработка нового сообщения от пользователя, занесение его в базу сообщений
    chat_database['messages'].append({
        'user': user,
        'time': time.time(),
        'text': text
    })

    bot_message = None

    # обработка команды бота (поиск значения слова)
    if text.upper().find(BOT_NAME + '.' + BOT_WORD) != -1:
        try:
            query_word = text.split(' ')[1]

            if query_word != '':
                meanings = requests.get(WORD_URL + query_word).text
                meanings = re.sub("\n", "", meanings)
                pattern_exist = '<li>(.+?)<span class="example'
                pattern_wrong = '<td><b>Такое написание слова ошибочно!.+?</td>'
                matches_exist = re.findall(pattern_exist, meanings)
                matches_wrong = re.findall(pattern_wrong, meanings)

                # найдены значения искомого слова и их парсинг для вывода
                if len(matches_exist):
                    bot_message = f'Значения слова "{query_word.capitalize()}":\n'
                    pattern_exist = '<.+?>|\[.+?\]|[^А-Яа-я., ]'
                    count = 1
                    for match in matches_exist:
                        bot_message += f'{count}. {re.sub(pattern_exist, "", match)}\n'
                        count += 1

                # найдена подсказка о возможном неправильном написании
                elif len(matches_wrong):
                    pattern_wrong = '<.+?>'
                    bot_message = re.sub(pattern_wrong, "", matches_wrong[0]) + '\n'
                else:
                    # значения слова не найдены, равно как и подсказка об ошибке
                    bot_message = f'Я тоже не знаю, что значит слово "{query_word}"'
            else:
                bot_message = f'Если напишете в формате {BOT_NAME}.{BOT_WORD}:СЛОВО, то я найду значение этого СЛОВА'
        except:
            bot_message = f'Если напишете в формате {BOT_NAME}.{BOT_WORD}:СЛОВО, то я найду значение этого СЛОВА'

    # обработка команды бота (перевод валюты)
    elif text.upper().find(BOT_NAME + '.' + BOT_MONEY) != -1:
        try:
            query_amount = float(text.split(' ')[1])
            query_currency1 = text.split(' ')[2].upper()
            query_currency2 = text.split(' ')[3].upper()
            rates = json.loads(requests.get(BANK_URL).content)['Valute']
            rates['RUR'] = {"Nominal": 1, "Value": 1}

            if query_currency1 not in rates.keys():
                bot_message = f'''Я не знаю валюту {query_currency1}
Пишите {BOT_NAME}.{BOT_MONEY} 123.45 XXX YYY - переведу 123.45 единиц XXX в YYY
Нужно указать коды валют, и всё это по курсу ЦБ РФ на текущий момент'''
            elif query_currency2 not in rates.keys():
                bot_message = f'''Я не знаю валюту {query_currency2}
Пишите {BOT_NAME}.{BOT_MONEY} 123.45 XXX YYY - переведу 123.45 единиц XXX в YYY
Нужно указать коды валют, и всё это по курсу ЦБ РФ на текущий момент'''
            else:
                fr_rate = float(rates[query_currency1]['Value']) / float(rates[query_currency1]['Nominal'])
                to_rate = float(rates[query_currency2]['Value']) / float(rates[query_currency2]['Nominal'])
                result_amount = query_amount * fr_rate / to_rate
                bot_message = f'По курсу ЦБ РФ {"%.2f" % query_amount} {query_currency1} = ' \
                              f'{"%.2f" % result_amount} {query_currency2}'
        except:
            bot_message = f'''Пишите {BOT_NAME}.{BOT_MONEY} 123.45 XXX YYY - переведу 123.45 единиц XXX в YYY
Нужно указать коды валют, и всё это по курсу ЦБ РФ на текущий момент'''

    # обработка обращения к боту без знакомой команды - вывод подсказки
    elif text.upper().find(BOT_NAME) != -1:
        bot_message = f'''Привет, я чат-бот я кое-что умею: 
    1. Я умею переводить валюту - команда {BOT_NAME}.{BOT_MONEY} 100 XXX YYY
    2. Я могу найти значения слов - команда {BOT_NAME}.{BOT_WORD} СЛОВО'''
    else:
        pass

    # было обращение к боту и сгенерирован его ответ - запись в базу
    if bot_message is not None:
        chat_database['messages'].append({
            'user': BOT_NAME,
            'time': time.time(),
            'text': bot_message
        })

    # сохранение базы сообщений
    if save_db(chat_database, DB_PATH):
        return {"result": "true"}
    else:
        return {"result": "false"}


# проверка новых сообщений и возвращение новых сообщений клиентскому приложению
@app.route("/get_messages")
def get_messages():
    try:
        from_time = float(request.args['last_message'])
    except:
        return abort(400)

    new_messages = []
    for message in chat_database['messages']:
        if message['time'] > from_time:
            new_messages.append(message)
    return {'messages': new_messages[:100]}


# ответ для страницы статуса сервера
@app.route("/status")
def status():
    status_string = f'''Это сервер для работы {APP_NAME}<br>
           Время сервера: {datetime.now().strftime("%d.%m.%y %H:%M:%S")}<br> 
           В чате принимает участие пользователей: {len(chat_database["users"])}<br>
           Общее число отправленных сообщений: {len(chat_database["messages"])}'''
    return status_string


if __name__ == '__main__':
    app.run()
