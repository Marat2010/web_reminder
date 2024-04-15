import sqlite3
import random
import string
import time
from flask_login import UserMixin
from sqlite3 import Error
import json


def create_users_table(db_connection=sqlite3.connect('db/users.db')):
    cursor = db_connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER UNIQUE,
                       first_name TEXT,
                       last_name TEXT,
                       username TEXT,
                       language_code TEXT,
                       is_bot INTEGER,  
                       is_premium INTEGER,
                       timezone TEXT)  
    ''')
    db_connection.commit()


class User(UserMixin):
    def __init__(self, user_id, first_name, last_name, username, language_code, is_bot, is_premium, timezone='+3'):
        self.id = user_id
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.language_code = language_code
        self.is_bot = is_bot
        self.is_premium = is_premium
        self.timezone = timezone  # Добавляем новый атрибут
        self.db_connection = sqlite3.connect('db/users.db')
        self.create_table()


    def create_table(self):
        cursor = self.db_connection.cursor()
        # Добавляем столбец timezone в таблицу users
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           user_id INTEGER UNIQUE,
                           first_name TEXT,
                           last_name TEXT,
                           username TEXT,
                           language_code TEXT,
                           is_bot INTEGER,  
                           is_premium INTEGER,
                           timezone TEXT)  
        ''')
        self.db_connection.commit()

    def add_user(self):
        cursor = self.db_connection.cursor()
        # Добавляем timezone в запрос на добавление пользователя
        cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, last_name, username, language_code, is_bot, is_premium, timezone) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (self.user_id, self.first_name, self.last_name, self.username, self.language_code, self.is_bot, self.is_premium, self.timezone))
        self.db_connection.commit()

    @classmethod
    def find_user(cls, user_id):
        db_connection = sqlite3.connect('db/users.db')
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        db_connection.close()
        if result:
            return cls(*result[1:])  # Включаем timezone в возвращаемый объект
        return None

    def update_user(self):
        cursor = self.db_connection.cursor()
        # Обновляем информацию пользователя, включая timezone
        cursor.execute("UPDATE users SET first_name=?, last_name=?, username=?, language_code=?, is_bot=?, is_premium=?, timezone=? WHERE user_id=?",
                       (self.first_name, self.last_name, self.username, self.language_code, self.is_bot, self.is_premium, self.timezone, self.user_id))
        self.db_connection.commit()

    def delete_user(self, user_id):
        cursor = self.db_connection.cursor()
        cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        self.db_connection.commit()

    def close_connection(self):
        self.db_connection.close()

    @staticmethod
    def get(user_id):
        db_connection = sqlite3.connect('db/users.db')
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        if result:
            user = User(*result[1:])  # Создаем экземпляр пользователя с данными из БД
            db_connection.close()
            return user
        db_connection.close()
        return None

    @staticmethod
    def find_by_telegram_id(telegram_id):
        db_connection = sqlite3.connect('db/users.db')
        cursor = db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id=?",
                       (telegram_id,))  # Предполагается, что в таблице users есть поле telegram_id
        result = cursor.fetchone()
        if result:
            user = User(*result[1:])  # Создаем экземпляр пользователя с данными из БД
            db_connection.close()
            return user
        db_connection.close()
        return None

    def change_timezone(self, new_timezone):
        self.timezone = new_timezone
        cursor = self.db_connection.cursor()
        # Преобразуем new_timezone в строку
        new_timezone_str = str(new_timezone)
        # Обновляем только часовой пояс пользователя
        cursor.execute("UPDATE users SET timezone=? WHERE user_id=?",
                       (new_timezone_str, self.user_id))
        self.db_connection.commit()

# Пример использования
# if __name__ == "__main__":
#     user = User(12345, "John", "Doe", "johndoe", "en", False, True)
#     user.add_user()
#
#     found_user = user.find_user(12345)
#     if found_user:
#         print(f"Found user: {found_user}")
#     else:
#         print("User not found.")
#
#     user.first_name = "Jane"
#     user.update_user()
#     updated_user = user.find_user(12345)
#     if updated_user:
#         print(f"Updated user: {updated_user}")
#
#     user.delete_user(12345)
#     deleted_user = user.find_user(12345)
#     if deleted_user:
#         print(f"User still exists: {deleted_user}")
#     else:
#         print("User deleted.")
#
#     user.close_connection()




class Auth_code:
    def __init__(self, auth_code=None, telegram_id=None):
        self.auth_code = auth_code
        self.telegram_id = telegram_id
        self.db_connection = sqlite3.connect('db/auth_codes.db')
        self.create_table()

    def create_table(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS auth_codes
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           auth_code TEXT,
                           time INTEGER,
                           telegram_id TEXT)''')
        self.db_connection.commit()
        print('table created')

    @staticmethod
    def generate_random_code(length=16):
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(length))
        return code

    def add_code(self, telegram_id=1):
        code = self.generate_random_code()
        current_time = int(time.time())
        cursor = self.db_connection.cursor()
        cursor.execute("INSERT INTO auth_codes (auth_code, time, telegram_id) VALUES (?, ?, ?)",
                       (code, current_time, telegram_id))
        self.db_connection.commit()
        return code

    def find_code(self, code):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM auth_codes WHERE auth_code=?", (code,))
        result = cursor.fetchone()
        if result:
            return {'id': result[0], 'auth_code': result[1], 'time': result[2], 'telegram_id': result[3]}
        else:
            return None

    def delete_code(self, code):
        cursor = self.db_connection.cursor()
        cursor.execute("DELETE FROM auth_codes WHERE auth_code=?", (code,))
        self.db_connection.commit()

    def delete_code_by_telegram_id(self, telegram_id):
        cursor = self.db_connection.cursor()
        cursor.execute("DELETE FROM auth_codes WHERE telegram_id=?", (telegram_id,))
        self.db_connection.commit()

    def close_connection(self):
        self.db_connection.close()

    def update_telegram_id(self, code, telegram_id):
        cursor = self.db_connection.cursor()
        cursor.execute("UPDATE auth_codes SET telegram_id=? WHERE auth_code=?", (telegram_id, code))
        self.db_connection.commit()


# Example usage
# if __name__ == "__main__":
#     auth_code_manager = Auth_code("your_auth_code_here")
#     generated_code = auth_code_manager.add_code()
#     print(f"Generated code: {generated_code}")
#
#     found_code = auth_code_manager.find_code(generated_code)
#     if found_code:
#         print(f"Found code: {found_code}")
#     else:
#         print("Code not found.")
#
#     auth_code_manager.delete_code(generated_code)
#     found_code = auth_code_manager.find_code(generated_code)
#     if found_code:
#         print(f"Code still exists: {found_code}")
#     else:
#         print("Code deleted.")
#
#     telegram_id = "your_telegram_id_here"
#     auth_code_manager.add_code(telegram_id)
#     auth_code_manager.delete_code_by_telegram_id(telegram_id)
#
#     found_code_by_telegram_id = auth_code_manager.find_code(telegram_id)
#     if found_code_by_telegram_id:
#         print(f"Code with telegram_id still exists: {found_code_by_telegram_id}")
#     else:
#         print("Code with telegram_id deleted.")
#
#     auth_code_manager.close_connection()


class Remind:
    """
    Класс для представления напоминания.

    Attributes:
        ruid (int): Уникальный идентификатор напоминания.
        creator_id (int): Идентификатор создателя напоминания.
        user_id (int): Идентификатор пользователя, для которого предназначено напоминание.
        task (str): Описание задачи напоминания.
        type_ (str): Тип напоминания (например, "daily").
        nearest_trigger (int): Время ближайшего срабатывания напоминания.
        counter (int): Делитель напоминания. В будущем, чтобы делать напоминания, например, каждые две недели
        advance_time (int): Время предварительного уведомления перед срабатыванием.
    """

    def __init__(self, ruid, creator_id, user_id, task, type_, nearest_trigger, counter=1, advance_time=0):
        self.ruid = ruid
        self.creator_id = creator_id
        self.user_id = user_id
        self.task = task
        self.type = type_
        self.nearest_trigger = nearest_trigger
        self.counter = counter
        self.advance_time = advance_time

    def to_json(self):
        """
        Конвертирует объект напоминания в JSON-строку.
        """
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def create_reminds_table(database):
    """
    Создает таблицу напоминаний и индекс для столбца nearest_trigger, если они еще не существуют.
    Args:
        database (str): Путь к файлу базы данных.
    """
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            # Создание таблицы, если она не существует
            c.execute('''CREATE TABLE IF NOT EXISTS reminds
                         (ruid INTEGER PRIMARY KEY AUTOINCREMENT,
                          creator_id INTEGER,
                          user_id INTEGER,
                          task TEXT,
                          type TEXT,
                          nearest_trigger INTEGER,
                          counter INTEGER,
                          advance_time INTEGER)''')
            # Создание индекса для улучшения производительности запросов по nearest_trigger
            c.execute('''CREATE INDEX IF NOT EXISTS idx_nearest_trigger ON reminds (nearest_trigger)''')
    except sqlite3.Error as e:
        print(e)

def fix_daily_typo(database):
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            # Обновление записей, где type равно "dayly" на "daily"
            c.execute("UPDATE reminds SET type = 'daily' WHERE type = 'dayly'")
            conn.commit()  # Применение изменений
    except sqlite3.Error as e:
        print(e)

def add_remind(database, remind, user_timezone_offset):
    """
    Добавляет новое напоминание в базу данных с учетом часового пояса пользователя.

    Args:
        database (str): Путь к файлу базы данных.
        remind (Remind): Объект напоминания, который необходимо добавить.
        user_timezone_offset (int): Смещение часового пояса пользователя в секундах относительно UTC.
    """
    try:
        # Корректировка nearest_trigger с учетом часового пояса пользователя
        corrected_nearest_trigger = int(remind.nearest_trigger) - int(user_timezone_offset.split(':')[0])*60*60
        #utc0 = remind.nearest_trigger - int(user.timezone.split(':')[0]) * 60 * 60
        #user_timezon = int(user.timezone.split(':')[0])
        #print(f"Событие в UNIX UTC 0 {utc0}")
        #print(f"Событие в UTC 0: {datetime.datetime.utcfromtimestamp(utc0).strftime('%d.%m.%Y %H:%M')}")
        #print(f"Часовой пояс пользователя: {user_timezon}")
        # Преобразование времени Unix в объект Arrow
        #arrow_time = arrow.get(utc0)
        # Добавление смещения часового пояса
        #arrow_time = arrow_time.shift(hours=user_timezon)
        # Преобразование времени в UTC
        #utc_time = arrow_time.to('UTC')
        #print(f"Событие в UTC пользователя: {utc_time.format('DD.MM.YYYY HH:mm')}")

        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO reminds (creator_id, user_id, task, type, nearest_trigger, counter, advance_time)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (remind.creator_id, remind.user_id, remind.task, remind.type, corrected_nearest_trigger,
                       remind.counter, remind.advance_time))
            print('added')
    except sqlite3.Error as e:
        print(e)

def update_remind(database, task, type, nearest_trigger, ruid, user_timezone_offset):
    """
    Обновляет информацию о напоминании в базе данных.

    Args:
        database (str): Путь к файлу базы данных.
        ruid (int): Уникальный идентификатор напоминания, которое необходимо обновить.
        new_remind (Remind): Новый объект напоминания с обновленными данными.
        user_timezone_offset (int): Смещение часового пояса пользователя в секундах относительно UTC.
    """
    try:
        # Корректировка nearest_trigger с учетом часового пояса пользователя
        corrected_nearest_trigger = int(nearest_trigger) - int(user_timezone_offset.split(':')[0]) * 60 * 60
        #{'task': 'йцвйыф', 'remind_type': 'single', 'nearest_trigger': 1709294520, 'creator': 599033114, 'ruid': 1}
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute('''UPDATE reminds 
                         SET task=?, type=?, nearest_trigger=? 
                         WHERE ruid=?''',
                      (task, type, corrected_nearest_trigger, ruid))
            print('updated')
    except sqlite3.Error as e:
        print(e)

def find_reminds_by_user_id(database, user_id):
    """
    Находит напоминания по идентификатору пользователя.

    Args:
        database (str): Путь к файлу базы данных.
        user_id (int): Идентификатор пользователя, для которого ищутся напоминания.

    Returns:
        list: Список уникальных идентификаторов напоминаний для заданного пользователя.
    """
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute("SELECT ruid FROM reminds WHERE user_id=?", (user_id,))
            return [row[0] for row in c.fetchall()]
    except sqlite3.Error as e:
        print(e)
        return []


def find_remind_by_creator_id(database, creator_id):
    """
    Находит напоминания по идентификатору создателя.

    Args:
        database (str): Путь к файлу базы данных.
        creator_id (int): Идентификатор создателя напоминания.

    Returns:
        list: Список уникальных идентификаторов напоминаний для заданного создателя.
    """
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute("SELECT ruid FROM reminds WHERE creator_id=?", (creator_id,))
            return [row[0] for row in c.fetchall()]
    except sqlite3.Error as e:
        print(e)
        return []


def get_remind_json_by_ruid(database, ruid):
    """
    Получает данные напоминания в формате JSON по его уникальному идентификатору.

    Args:
        database (str): Путь к файлу базы данных.
        ruid (int): Уникальный идентификатор напоминания.

    Returns:
        str: Строковое представление данных напоминания в формате JSON или None, если напоминание не найдено.
    """
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM reminds WHERE ruid=?", (ruid,))
            remind_data = c.fetchone()
            if remind_data:
                remind = Remind(*remind_data)
                return remind.to_json()
            else:
                return None
    except sqlite3.Error as e:
        print(e)
        return None


def delete_remind_by_ruid(database, ruid):
    #print(f"trying to delete {ruid}")
    """
    Удаляет напоминание по его уникальному идентификатору.

    Args:
        database (str): Путь к файлу базы данных.
        ruid (int): Уникальный идентификатор напоминания для удаления.
    """
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM reminds WHERE ruid=?", (ruid,))
            #print('success')
    except sqlite3.Error as e:
        print(e)


def create_reminds_tables(database):
    """
    Создает таблицы для различных временных интервалов срабатывания напоминаний.
    Args:
        database (str): Путь к файлу базы данных.
    """
    intervals = {
        "Срабатывания в ближайшие сутки": 86400,  # 1 день = 24 часа * 60 минут * 60 секунд
        "Срабатывания в ближайшие 12 часов": 43200,  # 12 часов = 12 * 60 минут * 60 секунд
        "Срабатывания в ближайшие 6 часов": 21600,  # 6 часов = 6 * 60 минут * 60 секунд
        "Срабатывания в ближайшие 3 часа": 10800,  # 3 часа = 3 * 60 минут * 60 секунд
        "Срабатывания в ближайший час": 3600,  # 1 час = 60 минут * 60 секунд
        "Срабатывания в ближайшие 15 минут": 900  # 15 минут = 15 * 60 секунд
    }

    try:
        create_reminds_table(database)
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            for name, trigger_time in intervals.items():
                c.execute(f'''CREATE TABLE IF NOT EXISTS {name.replace(" ", "_")}
                             (ruid INTEGER PRIMARY KEY AUTOINCREMENT,
                              nearest_trigger INTEGER)''')
                c.execute(f'''CREATE INDEX IF NOT EXISTS idx_nearest_trigger_{name.replace(" ", "_")} 
                              ON {name.replace(" ", "_")} (nearest_trigger)''')
    except sqlite3.Error as e:
        print(e)

def update_nearest_trigger_by_ruid(database, ruid, new_nearest_trigger):
    """
    Изменяет значение nearest_trigger для напоминания по его уникальному идентификатору.

    Args:
        database (str): Путь к файлу базы данных.
        ruid (int): Уникальный идентификатор напоминания для изменения.
        new_nearest_trigger (str): Новое значение nearest_trigger.
    """
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute("UPDATE reminds SET nearest_trigger=? WHERE ruid=?", (new_nearest_trigger, ruid))
            conn.commit()
    except sqlite3.Error as e:
        print(e)

# Пример использования:
#create_reminds_tables("your_database.db")

if __name__ == "__main__":
    import datetime
    import sqlite3
    import random
    import time


    # Добавление напоминания в базу данных
    def add_remind(database, remind):
        try:
            with sqlite3.connect(database) as conn:
                c = conn.cursor()
                c.execute('''INSERT INTO reminds (creator_id, user_id, task, type, nearest_trigger, counter, advance_time)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''', remind)
                print('added')
                conn.commit()  # Не забываем сохранить изменения в базе данных
        except sqlite3.Error as e:
            print(e)


    # Генерация напоминания с случайным типом
    def generate_remind(nearest_trigger):
        creator_id = 599033114
        user_id = 599033114
        task = "Sample Task"
        type_ = random.choice(["daily", "weekly", "monthly"])
        counter = 1  # Только одно напоминание для этой задачи
        advance_time = 0  # Без предварительного уведомления
        return creator_id, user_id, task, type_, nearest_trigger, counter, advance_time


    # Путь к базе данных
    database = "db/reminds.db"


    # Добавление напоминаний на сутки вперед с интервалом в 5 минут и случайным типом
    # current_time = datetime.datetime.now()
    # start_time = current_time + datetime.timedelta(days=1)
    # start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    # while current_time < start_time:
    #     nearest_trigger = int(current_time.timestamp())
    #     remind = generate_remind(nearest_trigger)
    #     add_remind(database, remind)
    #     current_time += datetime.timedelta(minutes=5)

    print("Napomneniya za sutki zagrujeni!")

    # database_path = "../db/reminds.db"
    # create_reminds_table(database_path)

    # Создаем новое напоминание
    # remind = Remind(None, 599033114, 599033114, "Проверить почту", "daily", 1644404645)
    # add_remind(database_path, remind)

    #Находим напоминания по ID пользователя
    # remind_ruids_for_user = find_remind_by_user_id(database_path, user_id=599033114)
    # print("Remind ruids for user_id 456:", remind_ruids_for_user)
    # #
    # # # Находим напоминания по ID создателя
    # # remind_ruids_for_creator = find_remind_by_creator_id(database_path, creator_id=599033114)
    # # print("Remind ruids for creator_id 123:", remind_ruids_for_creator)
    # #
    # # # Получаем данные о напоминании в формате JSON по его ruid (предполагаем, что ruid существует)
    # if remind_ruids_for_user:
    #     remind_json = get_remind_json_by_ruid(database_path, ruid=remind_ruids_for_user[0])
    #     print("Remind JSON for the first found reminder:", remind_json)
    #
    # # Удаляем напоминание по его ruid (предполагаем, что ruid существует)
    # if remind_ruids_for_user:
    #     delete_remind_by_ruid(database_path, ruid=remind_ruids_for_user[0])
    #     print(f"Remind with ruid {remind_ruids_for_user[0]} has been deleted.")



