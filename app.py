from flask import Flask, render_template_string, request, redirect, url_for, jsonify, render_template
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import *
from models import find_reminds_by_user_id
import datetime
import arrow

create_reminds_tables("db/reminds.db")

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # поменять

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/login'  # Страница входа
create_users_table()

def Translate(name):
    sl = {'single': 'Разовый', 'daily': 'Еженедельный', 'weekly': 'Еженедельный', 'monthly': 'Ежемесячный', 'yearly': 'Ежегодный'}
    return sl[name]

def GetDisplay(display):
    sl = {'1': 'comp', '2': 'phone'}
    return sl[display]

def unix_to_datetime(unix_timestamp, user_timezon):
    # Преобразование времени Unix в объект Arrow
    arrow_time = arrow.get(unix_timestamp)
    # Добавление смещения часового пояса
    arrow_time = arrow_time.shift(hours=user_timezon)
    # Преобразование времени в UTC
    utc_time = arrow_time.to('UTC')
    # print(f"Событие в UTC пользователя: {utc_time.format('DD.MM.YYYY HH:mm')}")
    formatted_datetime = utc_time.format('DD.MM.YYYY HH:mm')
    return formatted_datetime


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route('/login', methods=['GET'])
def index():
    user_id = current_user.get_id()
    print(user_id)
    if user_id:
        return render_template("reminds.html", display='1')
    else:
        auth_code_manager = Auth_code(Auth_code.generate_random_code())
        generated_code = auth_code_manager.add_code()
        telegram_bot_url = f'https://t.me/SviatServicesSecurityBot?start={generated_code}'
        return render_template("telegram.html", telegram_bot_url=telegram_bot_url, generated_code=generated_code)


@app.route('/process', methods=['POST'])
def process():
    code = request.form['code']
    auth_code_manager = Auth_code()  # Создаем экземпляр без передачи кода
    found_code_info = auth_code_manager.find_code(code)
    if found_code_info:
        # Используйте 'telegram_id' для поиска пользователя, так как в вашей логике 'user_id' хранится в 'telegram_id'
        user = User.find_user(found_code_info['telegram_id'])
        if user:
            login_user(user)
            return redirect(url_for('show_reminds', display='1'))  # Перенаправляем на защищенную страницу после логина
        else:
            print("User not found.")
    else:
        print("Code not found.")
    return redirect(url_for('index'))


@app.route('/', methods=['GET'])
@login_required
def main():
    user_id = current_user.get_id()
    if user_id:
        template = 'qq epta its main string and u are logged in'
        return redirect(url_for('reminds', display='1'))
    else:
        template = 'who are u???!!!'
    return render_template_string(template)


@app.route('/protected')
@login_required
def protected():
    user_id = current_user.get_id()
    template = '''
    <p>"Welcome to the protected area!"</p>
        <a href="{{ url_for('logout') }}">Выход</a>
    ''' + str(user_id)
    # return render_template_string(template)
    return redirect(url_for('reminds', display='1'))


@app.route('/reminds/<display>')
@login_required
def show_reminds(display):
    """
    Отображает напоминания пользователя в формате JSON.
    Использует параметр `user_id` из строки запроса для фильтрации напоминаний.
    """
    user_id = current_user.get_id()  # Получаем user_id
    user = User.find_user(user_id)
    user_timezon = int(user.timezone.split(':')[0])
    print(user_id)
    database_path = "db/reminds.db"
    remind_ruids = find_reminds_by_user_id(database_path, user_id)  # Получаем список ruid для пользователя
    reminds = []
    for ruid in remind_ruids:
        remind_json_string = get_remind_json_by_ruid(database_path, ruid)  # Получаем напоминание в формате строки JSON
        if remind_json_string:
            remind_json = json.loads(remind_json_string)  # Преобразуем строку JSON в словарь
            remind_json['nearest_trigger'] = unix_to_datetime(remind_json['nearest_trigger'], user_timezon)
            remind_json['type'] = Translate(remind_json['type'])
            reminds.append(remind_json)  # Словарь уже, нет необходимости использовать json.loads снова

    display = GetDisplay(str(display))
    return render_template(f"reminds_{display}.html", context={'reminds': reminds, 'telegram_id': user_id})


@app.route('/settings/<display>', methods=['POST', 'GET'])
@login_required
def settings(display):
    if request.method == "POST":
        timezone = request.get_json()['timezone']
        user_id = current_user.get_id()
        user = User.find_user(user_id)
        user.change_timezone(timezone)
        print(timezone)
        return jsonify({'status': 'success', 'timezone': timezone})

    else:
        user_id = current_user.get_id()
        user = User.find_user(user_id)
        if user:
            user_info = {
                'user_id': user.user_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'language_code': user.language_code,
                'is_bot': user.is_bot,
                'is_premium': user.is_premium,
                'timezone': user.timezone
            }
            print(user_info)
            display = GetDisplay(str(display))
            return render_template(f"settings_{display}.html", context={'user_info': user_info, 'telegram_id': user_id})


@app.route('/remind_add/<display>', methods=['POST', 'GET'])
@login_required
def remind_add(display):
    telegram_id = current_user.get_id()
    user = User.find_user(telegram_id)
    if request.method == "POST":
        print('btn pushed')
        data = request.get_json()  # Получаем JSON данные из запроса
        print(data)
        # Создаем объект Remind
        remind = Remind(
            ruid=None,  # None, так как это новое напоминание и ruid будет создан базой данных
            creator_id=data['creator'],
            user_id=data['creator'],
            task=data['task'],
            type_=data['remind_type'],
            nearest_trigger=data['nearest_trigger'],
            counter=data.get('counter', 1),  # Предоставляем значение по умолчанию 1, если counter не предоставлен
            advance_time=data.get('advance_time', 0)
            # Предоставляем значение по умолчанию 0, если advance_time не предоставлен
        )
        # print(remind.to_json())
        # Добавляем напоминание в базу данных
        database_path = "db/reminds.db"  # путь к бд
        add_remind(database_path, remind, user_timezone_offset=user.timezone)
        return jsonify({'status': 'success'}), 200
        # return jsonify(success=True)  # Отвечаем клиенту, что все хорошо
    # Если GET запрос, просто рендерим страницу
    display = GetDisplay(str(display))
    return render_template(f"remind_add_{display}.html", context={'telegram_id': telegram_id})

@app.route('/remind_edit/<int:ruid>/<display>', methods=['GET', 'POST'])
@login_required
def remind_edit(ruid, display):
    database_path = "db/reminds.db"
    user_id = current_user.get_id()
    user = User.find_user(user_id)
    try:
        remind_json = json.loads(get_remind_json_by_ruid(database_path, ruid))
        if request.method == "POST":
            new_remind = request.get_json()
            #print('btn pressed')
            #print(request.get_json())  # заглушка для сохранения изменений
            #print(request.get_json()['ruid'])  # заглушка для сохранения изменений
            update_remind(database_path, new_remind['task'], new_remind["remind_type"], new_remind['nearest_trigger'],
                          new_remind['ruid'], user.timezone)
            #update_remind(database_path, request.get_json(), user_timezone_offset=user.timezone)
            return jsonify(request.get_json())
        else:
            if remind_json:
                # Возвращаем JSON напоминания
                # {
                #     "advance_time": 0,
                #     "counter": 1,
                #     "creator_id": 599033114,
                #     "nearest_trigger": 1644404645,
                #     "ruid": 1,
                #     "task": "\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u043f\u043e\u0447\u0442\u0443",
                #     "type": "daily",
                #     "user_id": 599033114
                # }
                if str(remind_json['user_id']) == str(user_id):
                    # print(type(remind_json))
                    # print(remind_json)
                    # print(type(json.load(remind_json)))

                    display = GetDisplay(str(display))
                    return render_template(f"remind_edit_{display}.html", context={'remind': remind_json, 'telegram_id': remind_json['user_id']})
                else:
                    return redirect(url_for('show_reminds', display='1'))
            else:
                print('not get')
                # Если напоминание не найдено, возвращаем пользователя к напоминаниям
                return redirect(url_for('show_reminds', display='1'))
    except TypeError:
        return redirect(url_for('show_reminds', display='1'))


@app.route('/remind_delete', methods=['POST', 'GET'])
@login_required
def remind_delete():
    database_path = "db/reminds.db"
    if request.method == "POST":
        print('deleting')
        id = request.get_json()['id']
        # Определить remind по id
        delete_remind_by_ruid(database_path, id)
        return jsonify({'success': '200'}), 404


@app.route('/profile')
@login_required
def user_info():
    user_id = current_user.get_id()
    user = User.find_user(user_id)
    if user:
        user_info = {
            'user_id': user.user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'language_code': user.language_code,
            'is_bot': user.is_bot,
            'is_premium': user.is_premium,
        }
        # return jsonify(user_info)
        return render_template("profile.html", telegram_id=user_id, user=user_info)
    else:
        return jsonify({'error': 'User not found'}), 404


@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
