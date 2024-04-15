from os import getenv

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, CommandObject
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import Message

from dotenv import load_dotenv

from models import User, Auth_code

# Загрузка переменных среды из .env файла
load_dotenv()

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()
# Получение токена бота
TOKEN = getenv("BOT_TOKEN")

bot = Bot(TOKEN)

#@dp.message(CommandStart(deep_link=True))
@dp.message(Command("start"))
#async def command_start_handler(message: Message, command: CommandObject) -> None:
async def cmd_start(message: types.Message, command: CommandObject):

    #await message.answer('Тагил')
    args = command.args
    #print(args)
    payload = args
    user_data = message.from_user
    # print(payload)
    # print(len(payload))
    # print(user_data)

    try:
        #print(payload)
        if len(payload) == 16:
            user = User(
                user_id=user_data.id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                username=user_data.username,
                language_code=user_data.language_code,
                is_bot=user_data.is_bot,
                is_premium=getattr(user_data, 'is_premium', False) #Добавление is_premium с проверкой на его наличие
            )
            # Вывод информации о пользователе (закомментировать)
            print(vars(user))
            print(payload)
            #запуск функции обработки пользователя в базе данных
            if Auth_code(payload).find_code(payload):
                user.add_user()
                # запуск функции допуска к сайту
                Auth_code(payload).update_telegram_id(payload,user.user_id)
                await message.answer('Вы были авторизованы, пожалуйста вернитесь на сайт и нажмите "Дальше"')
            else:
                print('нету')
    except TypeError:
        await message.answer('Я умею авторизовывать пользователей, а не разговаривать с ними :(')

# Обработка входящих вебхуков
async def on_startup():
    await bot.set_webhook("https://yourserver.com/webhook")  #url для вебхука

async def on_shutdown():
    await bot.delete_webhook()

async def main():
    # Запуск поллинга с использованием созданных экземпляров бота и диспетчера
    await dp.start_polling(bot)

# Запуск асинхронной функции main
if __name__ == "__main__":
    asyncio.run(main())
