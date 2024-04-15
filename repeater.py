from models import *

import time
import json


import telebot
from telebot import apihelper

from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo





def calculate_next_trigger_unix(current_trigger_unix, remind_type, timezone_str='UTC'):
    """
    Calculate the next trigger time for a reminder based on its type and timezone.

    :param current_trigger_unix: Current trigger time in UNIX timestamp.
    :param remind_type: Type of the reminder ('daily', 'weekly', 'monthly', 'yearly').
    :param timezone_str: String representation of the timezone.
    :return: Next trigger time in UNIX timestamp.
    """
    timezone = ZoneInfo(timezone_str)
    current_trigger_datetime = datetime.fromtimestamp(current_trigger_unix, tz=timezone)
    if remind_type == 'daily':
        next_trigger_datetime = current_trigger_datetime + timedelta(days=1)
    elif remind_type == 'weekly':
        next_trigger_datetime = current_trigger_datetime + timedelta(weeks=1)
    elif remind_type == 'monthly':
        next_trigger_datetime = current_trigger_datetime + relativedelta(months=+1)
    elif remind_type == 'yearly':
        # Using relativedelta to properly account for leap years
        next_trigger_datetime = current_trigger_datetime + relativedelta(years=+1)
    elif remind_type == 'single':
        # Using relativedelta to properly account for leap years
        return None
    else:
        raise ValueError("Unsupported remind_type provided.")
    return int(next_trigger_datetime.timestamp())

def is_future_unix(unix_time):
    current_unix_time = int(datetime.now().timestamp())
    return unix_time > current_unix_time


def move_reminders(source_table, destination_table, trigger_time, database):
    """
    Переносит напоминания из одной таблицы в другую.
    Args:
        source_table (str): Название исходной таблицы.
        destination_table (str): Название целевой таблицы.
        trigger_time (int): Время, после которого напоминание переносится в другую таблицу.
        database (str): Путь к файлу базы данных.
    """
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            current_time = int(time.time())
            c.execute(f"SELECT * FROM {source_table} WHERE nearest_trigger <= ?", (current_time + trigger_time,))
            reminders_to_move = c.fetchall()
            print(f"Число напоминаний для переноса: {len(reminders_to_move)}")
            for reminder in reminders_to_move:
                print(reminder[1] <= current_time)
                if reminder[1] <= current_time:  # Если напоминание в прошлом
                    c.execute(f"INSERT INTO Срабатывания_в_ближайшие_15_минут (ruid, nearest_trigger) VALUES (?, ?)",
                              (reminder[0], reminder[1]))
                    c.execute(f"DELETE FROM {source_table} WHERE ruid = ?", (reminder[0],))
                else:
                    c.execute(f"INSERT INTO {destination_table} (ruid, nearest_trigger) VALUES (?, ?)", reminder)
                    c.execute(f"DELETE FROM {source_table} WHERE ruid = ?", (reminder[0],))
            conn.commit()
    except sqlite3.Error as e:
        print(e)

def get_past_reminds(database):
    """
    Получает и возвращает ruid каждого напоминания в прошлом из таблицы "Срабатывания в ближайшие 15 минут".
    Args:
        database (str): Путь к файлу базы данных.
    Returns:
        list: Список ruid напоминаний в прошлом.
    """
    past_reminds = []
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            current_time = int(time.time())
            c.execute("SELECT ruid FROM reminds WHERE nearest_trigger <= ?", (current_time,))
            reminds_in_past = c.fetchall()
            for reminder in reminds_in_past:
                past_reminds.append(reminder[0])
    except sqlite3.Error as e:
        print(e)
    return past_reminds

def send_telegram_message(token, message_text, telegram_id):
    try:
        # Создание экземпляра бота
        bot = telebot.TeleBot(token)

        # Отправка сообщения
        bot.send_message(telegram_id, message_text)
        return True, None
    except apihelper.ApiTelegramException as e:
        return False, f"Ошибка при отправке сообщения: {e}"
    except Exception as e:
        return False, f"Произошла ошибка: {e}"

def remove_reminder_by_ruid(ruid, database):
    """
    Удаляет напоминание из таблицы "Срабатывания в ближайшие 15 минут" по его ruid.
    Args:
        ruid (int): Уникальный идентификатор напоминания.
        database (str): Путь к файлу базы данных.
    """
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM Срабатывания_в_ближайшие_15_минут WHERE ruid = ?", (ruid,))
            conn.commit()
    except sqlite3.Error as e:
        print(e)

if __name__ == "__main__":
    last_move_time = datetime.now() - timedelta(minutes=14)  # Установка начального значения для отслеживания времени
    database_path = "db/reminds.db"
    token = '1774003261:AAEtsJ-XHenBzJgg80UfYgeB8ukzVXEy7h0'

    print('repeater has been activated')

    while True:
        current_time = datetime.now()

        # Находим все напоминания, время срабатывания которых уже прошло
        past_reminds = get_past_reminds(database_path)
        if past_reminds:
            print(f"[{current_time}] Найдены напоминания с прошедшим временем срабатывания:")
            for remind_ruid in past_reminds:
                # #получить
                telegram_id = json.loads(get_remind_json_by_ruid(database_path, remind_ruid))['user_id']
                message_text = json.loads(get_remind_json_by_ruid(database_path, remind_ruid))['task']
                # print(telegram_id)
                # print(message_text)
                # #отправить
                send_telegram_message(token, message_text, telegram_id)
                # #поменять
                new_nearest_trigger = calculate_next_trigger_unix(json.loads(get_remind_json_by_ruid(database_path, remind_ruid))['nearest_trigger'],
                                                                   json.loads(get_remind_json_by_ruid(database_path, remind_ruid))['type'])

                if new_nearest_trigger:
                    update_nearest_trigger_by_ruid(database_path, remind_ruid, str(new_nearest_trigger))
                    print(f"Напоминание с ruid {remind_ruid} отправлено и обновлено.")
                else:
                    delete_remind_by_ruid(database_path, remind_ruid)
                    print(f"Напоминание с ruid {remind_ruid} отправлено и удалено.")

        else:
            print(f"[{current_time}] Напоминания с прошедшим временем срабатывания не найдены.")

        time.sleep(60)  # Подождать 1 минуту перед следующей проверкой


    # while True:
    #     print('repeater searching reminds')
    #     current_time = int(time.time())
    #
    #     # Проверка и перенос напоминаний из основной таблицы в таблицу "Срабатывания в ближайшие сутки" раз в 23 часа
    #     if current_time % (23 * 3600) == 0:
    #         move_reminders("reminds", "Срабатывания_в_ближайшие_сутки", 86400, database_path)
    #
    #     # Проверка и перенос напоминаний из таблицы "Срабатывания в ближайшие сутки" в таблицу "Срабатывания в ближайшие 12 часов" раз в 11 часов
    #     if current_time % (11 * 3600) == 0:
    #         move_reminders("Срабатывания_в_ближайшие_сутки", "Срабатывания_в_ближайшие_12_часов", 43200, database_path)
    #
    #     # Проверка и перенос напоминаний из таблицы "Срабатывания в ближайшие 12 часов" в таблицу "Срабатывания в ближайшие 6 часов" раз в 5 часов
    #     if current_time % (5 * 3600) == 0:
    #         move_reminders("Срабатывания_в_ближайшие_12_часов", "Срабатывания_в_ближайшие_6_часов", 21600,
    #                        database_path)
    #
    #     # Проверка и перенос напоминаний из таблицы "Срабатывания в ближайшие 6 часов" в таблицу "Срабатывания в ближайшие 3 часа" раз в 2 часа
    #     if current_time % (2 * 3600) == 0:
    #         move_reminders("Срабатывания_в_ближайшие_6_часов", "Срабатывания_в_ближайшие_3_часа", 10800, database_path)
    #
    #     # Проверка и перенос напоминаний из таблицы "Срабатывания в ближайшие 3 часа" в таблицу "Срабатывания в ближайший час" раз в 50 минут
    #     if current_time % (50 * 60) == 0:
    #         move_reminders("Срабатывания_в_ближайшие_3_часа", "Срабатывания_в_ближайший_час", 3600, database_path)
    #
    #     # Проверка и перенос напоминаний из таблицы "Срабатывания в ближайший час" в таблицу "Срабатывания в ближайшие 15 минут" раз в 10 минут
    #     if current_time % (10 * 60) == 0:
    #         move_reminders("Срабатывания_в_ближайший_час", "Срабатывания_в_ближайшие_15_минут", 900, database_path)
    #
    #     # Получение ruid каждого напоминания в прошлом
    #     past_reminds = get_past_reminds(database_path)
    #
    #     # Обработка каждого напоминания в прошлом по отдельности
    #     for remind in past_reminds:
    #         #получить
    #         telegram_id = json.loads(get_remind_json_by_ruid(database_path, remind))['user_id']
    #         message_text = json.loads(get_remind_json_by_ruid(database_path, remind))['task']
    #         #отправить
    #         send_telegram_message(token, message_text, telegram_id)
    #         #поменять
    #         new_nearest_trigger = calculate_next_trigger_unix(json.loads(get_remind_json_by_ruid(database_path, remind))['nearest_trigger'],
    #                                                           json.loads(get_remind_json_by_ruid(database_path, remind))['type'])
    #         update_nearest_trigger_by_ruid(database_path, remind, str(new_nearest_trigger))
    #         #удалить
    #         remove_reminder_by_ruid(remind, database_path)
    #         #print("Напоминание в прошлом:", remind)
    #
    #     # Подождать до следующей проверки
    #     time.sleep(1)  # Подождать 1 минуту перед следующей проверкой


# while True:
#     next_trigger_unix = calculate_next_trigger_unix(current_trigger_unix, remind_type)
#     if is_future_unix(next_trigger_unix):
#         print("Next trigger time is in the future:", next_trigger_unix)
#         break
#     current_trigger_unix = next_trigger_unix


# def unix_to_local(unix_timestamp, timezone_offset_hours):
#     """
#     Преобразует UNIX timestamp в локальное время с учетом часового пояса пользователя.
#
#     Args:
#         unix_timestamp (int): Время в формате UNIX timestamp.
#         timezone_offset_hours (int): Смещение часового пояса пользователя в часах относительно UTC.
#
#     Returns:
#         datetime: Локальное время пользователя.
#     """
#     utc_time = datetime.fromtimestamp(unix_timestamp, timezone.utc)
#     timezone_offset = timedelta(hours=timezone_offset_hours)
#     local_time = utc_time + timezone_offset
#     return local_time


# # Пример использования:
# unix_timestamp = 1609459200  # 1 января 2021 года, 00:00:00 UTC
# timezone_offset_hours = 5  # Смещение часового пояса для Екатеринбурга
#
# local_time = unix_to_local(unix_timestamp, timezone_offset_hours)
# print(f"Локальное время: {local_time}")