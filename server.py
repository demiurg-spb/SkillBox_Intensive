from flask import Flask, jsonify, request, abort
from datetime import datetime
import time
import pickle

# константы для работы
APP_NAME = 'SimChat'
DB_PATH = 'messages.db'

# константы с командами чат-бота
BOT_HELP = 'БОТ'
BOT_WORD = 'ЗНАЧЕНИЕ'
BOT_ROAST = 'ТОСТ'

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

    if not isinstance(user, str) or user == "" \
            or not isinstance(text, str) or text == "":
        return abort(400)

    if text.find(BOT_HELP) != -1:   #обработка команды бота (не вносится в список сообщений)

    else:
        chat_database['messages'].append({
            'user': user,
            'time': time.time(),
            'text': text
        })

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
