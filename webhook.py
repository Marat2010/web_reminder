"""
Converted auth_bot.py file to a webhook for use with nginx
"""
import os
import sys
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.filters import CommandStart, CommandObject

from dotenv import load_dotenv
from models import User, Auth_code

# Загрузка переменных среды из .env файла
load_dotenv(".env")

TOKEN = os.getenv("BOT_TOKEN")  # Получение токена бота

# Webserver settings
# bind localhost only to prevent any external access
WEB_SERVER_HOST = "127.0.0.1"
# Port for incoming request from reverse proxy. Should be any available port
WEB_SERVER_PORT = 8080

# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = "/auth_bot"

# Base URL for webhook will be used to generate webhook URL for Telegram,
# in this example it is used public DNS with HTTPS support
DOMAIN = os.getenv("DOMAIN_NAME")
EXTERNAL_PORT = 8443
# Example WEBHOOK_URL = "https://bot.sviatsreminder.ru:8443"
WEBHOOK_URL = "https://" + DOMAIN + ":" + str(EXTERNAL_PORT)

# Secret key to validate requests from Telegram (optional)
WEBHOOK_SECRET = "my-secret"

# All handlers should be attached to the Router (or Dispatcher)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    logging.info("get started")
    # await message.answer('Тагил')

    payload = command.args
    user_data = message.from_user

    try:
        if len(payload) == 16:
            user = User(
                user_id=user_data.id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                username=user_data.username,
                language_code=user_data.language_code,
                is_bot=user_data.is_bot,
                is_premium=getattr(user_data, 'is_premium', False)  # Добавление is_premium с проверкой на его наличие
            )
            # Вывод информации о пользователе (закомментировать)
            print(vars(user))
            print(payload)
            # запуск функции обработки пользователя в базе данных
            if Auth_code(payload).find_code(payload):
                user.add_user()
                # запуск функции допуска к сайту
                Auth_code(payload).update_telegram_id(payload, user.user_id)
                await message.answer('Вы были авторизованы, пожалуйста вернитесь на сайт и нажмите "Дальше"')
            else:
                print('нету')
    except TypeError:
        await message.answer('Я умею авторизовывать пользователей, а не разговаривать с ними :(')


async def on_startup(bot: Bot) -> None:
    logging.info(f"== PATH: {os.path.dirname(__file__)} ==")
    logging.info(f"== WEBHOOK_URL: {WEBHOOK_URL} ==")
    logging.info("Bot has been started")
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)
    logging.info("Webhook has been set up")


def main() -> None:
    # Dispatcher is a root router
    dp = Dispatcher()
    # ... and all other routers should be attached to Dispatcher
    dp.include_router(router)

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)

    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.getLogger('aiogram').setLevel(logging.DEBUG)
    main()


# ================================
# from aiogram.filters import CommandStart
# from aiogram.types import Message
# from aiogram.utils.markdown import hbold
# from aiogram.filters.command import Command
# ================================
# from pathlib import Path
# print("---000--- ", Path.cwd())
# WEB_SERVER_HOST = "https://sviatsreminder.ru"

# from dotenv import load_dotenv
# dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
# if os.path.exists(dotenv_path):
#     load_dotenv(dotenv_path)

# load_dotenv(override=True)
# load_dotenv(find_dotenv())
# logging.basicConfig(level=logging.INFO)
# ================================
# ftp://marat:123qwe@bot.z2024.site
# sed -i -e 's/\r$//' script.sh
# sed -i -e 's/\r$//'