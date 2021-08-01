from datetime import datetime, timedelta

from telebot import TeleBot
from telebot.types import CallbackQuery

import fsm
from BotController import BotController


def handle_callback_set_default_value(bot: TeleBot, bot_controller: BotController):
    @bot.callback_query_handler(func=lambda call: call.data in ['set_default', 'change_default'])
    def callback_set_default_value(call: CallbackQuery):
        # убирает состояние загрузки, к которому переходит бот после нажатия кнопки
        bot.answer_callback_query(str(call.id))

        id_user = call.message.chat.id
        if bot_controller.get_state_cmd(id_user) != fsm.IS_SET_DEF_VALUE:
            return
        if call.data == 'set_default':
            in_date = datetime.utcnow()
            out_date = in_date + timedelta(days=3)
            default_api_param = {'adults1': 1,
                                 'checkIn': in_date.strftime('%Y-%m-%d'),
                                 'checkOut': out_date.strftime('%Y-%m-%d'),
                                 }
            bot_controller.add_api_params(id_user, **default_api_param)
            for state, value in zip([fsm.GET_NUM_HUMANS, fsm.GET_CHECKIN_DATE, fsm.GET_CHECKOUT_DATE],
                                    default_api_param.values()):
                bot_controller.add_data_to_form_confirm(id_user, value, state)
            bot.send_message(id_user, '<b>Оставляем значения по умолчанию.</b>', parse_mode='HTML')
            bot_controller.set_new_state(id_user, fsm.END)
        else:
            bot.send_message(id_user, '<b>Вводим свои значения для поиска.</b>', parse_mode='HTML')
            bot_controller.go_next_state(id_user)
        # после ответа, клавиатура будет исчезать из чата
        bot.edit_message_reply_markup(id_user, call.message.message_id)


def handle_callback_check_entered_data(bot: TeleBot, bot_controller: BotController):
    @bot.callback_query_handler(func=lambda call: call.data in ['start_cmd_again', 'exec_cmd'])
    def callback_check_entered_data(call: CallbackQuery):
        # убирает состояние загрузки, к которому переходит бот после нажатия кнопки
        bot.answer_callback_query(str(call.id))

        id_user = call.message.chat.id
        if bot_controller.get_state_cmd(id_user) != fsm.END:
            return
        if call.data == 'start_cmd_again':
            name_cmd = bot_controller.get_active_cmd(id_user)
            bot.send_message(id_user, f'<b>Ок. Запуск команды {name_cmd} сначала.</b>', parse_mode='HTML')
            bot_controller.set_new_state(id_user, fsm.START)
        else:
            bot.send_message(id_user, 'Данные приняты, ожидайте результат.')
            bot.send_chat_action(id_user, 'typing')  # показывает индикатор «набора текста»
            bot_controller.exec_cmd(id_user)

        # после ответа, клавиатура будет исчезать из чата
        bot.edit_message_reply_markup(id_user, call.message.message_id)
