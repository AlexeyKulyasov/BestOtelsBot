import sys

from telebot import apihelper, TeleBot

from config import TG_TOKEN
from BotController import BotController
from MessageHandler import MessageHandler


apihelper.ENABLE_MIDDLEWARE = True
tg_bot = TeleBot(TG_TOKEN)


if __name__ == '__main__':
    args = sys.argv[1:]
    debug_mode = False
    if '--debug' in args:
        debug_mode = True

    print('debug_mode', debug_mode)
    bot_controller = BotController(tg_bot, debug_mode)
    message_handler = MessageHandler(tg_bot, bot_controller, debug_mode)
    message_handler.start()

    tg_bot.infinity_polling()
    # tg_bot.polling(none_stop=True)
