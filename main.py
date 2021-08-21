import os
import sys

from telebot import apihelper, TeleBot

from config import TG_TOKEN
from BotController import BotController
from MessageHandler import MessageHandler
from utils import configure_telebot_logger, configure_app_logger


if not os.path.exists('logs'):
    os.mkdir('logs')
logger_telebot = configure_telebot_logger()
logger = configure_app_logger('main')

apihelper.ENABLE_MIDDLEWARE = True
tg_bot = TeleBot(TG_TOKEN)


if __name__ == '__main__':
    args = sys.argv[1:]
    debug_mode = False
    if '--debug' in args:
        debug_mode = True

    logger.info(f'Bot start. Debug modes is {debug_mode}')
    bot_controller = BotController(tg_bot, debug_mode)
    message_handler = MessageHandler(tg_bot, bot_controller, debug_mode)
    message_handler.start()

    tg_bot.infinity_polling()
