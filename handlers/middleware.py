from telebot import types, TeleBot

from BotController import BotController


def handle_cancel_command(bot: TeleBot, bot_controller: BotController):
    @bot.middleware_handler(update_types=['message'])
    def cancel_command(bot_instance, msg: types.Message):
        """ Обработка ввода команды "отмена".  """

        id_user = msg.from_user.id
        active_cmd = bot_controller.get_active_cmd(id_user)
        if msg.text == 'Отмена' and active_cmd:
            bot_controller.cancel_cmd(id_user)
            bot.send_message(id_user, f'Команда {active_cmd} отменена', reply_markup=types.ReplyKeyboardRemove())
