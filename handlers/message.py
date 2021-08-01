from datetime import datetime

from telebot import TeleBot
from telebot.types import Message

import fsm
from BotController import BotController, cmd_desc
from resources import query_locations_info
from utils import is_valid_number, is_valid_date


def handle_cmd_send_welcome(bot: TeleBot):
    @bot.message_handler(commands=['start', 'help'])
    def cmd_send_welcome(msg: Message):
        """Вывод команд бота. """

        text = '<b><u>Бот для поиска топовых предложений по отелям</u></b>\n\n'
        text += '<i>Команды</i>:\n'
        for cmd_name, desc in cmd_desc.items():
            text += f'<b>{cmd_name}</b> -&gt; {desc}\n'
        bot.send_message(msg.from_user.id, text, parse_mode='HTML')


def handle_cmd_low_price_and_high_price(bot: TeleBot, bot_controller: BotController):
    @bot.message_handler(commands=['lowprice', 'highprice'])
    def cmd_sort_price(msg: Message):
        id_user = msg.from_user.id
        print(f'{datetime.now()} Запущена команда {msg.text}, user_id={id_user}')
        bot_controller.set_command(id_user, cmd_name=msg.text)
        sort_order = 'PRICE' if msg.text == '/lowprice' else 'PRICE_HIGHEST_FIRST'
        bot_controller.add_api_params(id_user, sortOrder=sort_order)
        bot_controller.set_new_state(id_user, fsm.START)


def handle_cmd_best_deal(bot: TeleBot, bot_controller: BotController):
    @bot.message_handler(commands=['bestdeal'])
    def cmd_best_deal(msg: Message):
        bot.send_message(msg.from_user.id, 'Команда находится в разработке')


def handle_get_location(bot: TeleBot, bot_controller: BotController, debug_mode: bool):
    @bot.message_handler(func=lambda msg: bot_controller.get_state_cmd(msg.from_user.id) == fsm.GET_LOCATION,
                         content_types=['text'])
    def get_location_step(msg: Message):
        id_user = msg.from_user.id
        bot.send_chat_action(id_user, 'typing')  # показывает индикатор «набора текста»

        locations_info = query_locations_info(msg.text, debug_mode)
        if not locations_info:
            bot.reply_to(msg, 'Такой город не найден. Проверьте название и повторите ввод.')
            return
        if locations_info == -1:
            bot.reply_to(msg, 'Ошибка запроса. Попробуйте повторить позднее.')
            return

        bot_controller.save_locations_info(id_user, locations_info)
        bot_controller.go_next_state(id_user)


def handle_get_city(bot: TeleBot, bot_controller: BotController):
    @bot.message_handler(func=lambda msg: bot_controller.get_state_cmd(msg.from_user.id) == fsm.CHOICE_CITY,
                         content_types=['text'])
    def get_city_step(msg: Message):
        id_user = msg.from_user.id
        locations_info = bot_controller.users[id_user].locations_info
        if msg.text not in locations_info:
            bot.reply_to(msg, 'Некорректный ввод. Выберите кнопкой один из вариантов ниже.')
            return
        bot_controller.add_api_params(id_user, destinationId=locations_info[msg.text])
        bot_controller.add_data_to_form_confirm(id_user, msg.text)
        bot_controller.go_next_state(id_user)


def handle_get_count_humans(bot: TeleBot, bot_controller: BotController):
    @bot.message_handler(func=lambda msg: bot_controller.get_state_cmd(msg.from_user.id) == fsm.GET_NUM_HUMANS,
                         content_types=['text'])
    def get_count_humans_step(msg: Message):
        if not is_valid_number(msg.text, min_val=1, max_val=15):
            bot.reply_to(msg, 'Введите число в диапазоне 1..15.')
            return
        bot_controller.add_api_params(msg.from_user.id, adults1=msg.text)
        bot_controller.add_data_to_form_confirm(msg.from_user.id, int(msg.text))
        bot_controller.go_next_state(msg.from_user.id)


def handle_get_checkin_date(bot: TeleBot, bot_controller: BotController):
    @bot.message_handler(func=lambda msg: bot_controller.get_state_cmd(msg.from_user.id) == fsm.GET_CHECKIN_DATE,
                         content_types=['text'])
    def get_checkin_date_step(msg: Message):
        if not is_valid_date(msg.text):
            bot.reply_to(msg, f'Неправильный формат даты, она должна быть не ранее текущей и вида гггг-мм-дд,'
                              f' например {datetime.utcnow():%Y-%m-%d}')
            return
        bot_controller.add_api_params(msg.from_user.id, checkIn=msg.text)
        bot_controller.add_data_to_form_confirm(msg.from_user.id, msg.text)
        bot_controller.go_next_state(msg.from_user.id)


def handle_get_checkout_date(bot: TeleBot, bot_controller: BotController):
    @bot.message_handler(func=lambda msg: bot_controller.get_state_cmd(msg.from_user.id) == fsm.GET_CHECKOUT_DATE,
                         content_types=['text'])
    def get_checkout_date_step(msg: Message):
        if not is_valid_date(msg.text):
            bot.reply_to(msg, f'Неправильный формат даты, она должна быть не ранее текущей и вида гггг-мм-дд,'
                              f' например {datetime.utcnow():%Y-%m-%d}')
            return

        in_date = bot_controller.users[msg.from_user.id].api_params['checkIn']
        in_date = datetime.strptime(in_date, '%Y-%m-%d').date()
        out_date = datetime.strptime(msg.text, '%Y-%m-%d').date()
        if in_date >= out_date:
            bot.reply_to(msg, 'Дата выезда должна быть позже даты въезда. Попробуйте ещё раз.')
            return

        bot_controller.add_api_params(msg.from_user.id, checkOut=msg.text)
        bot_controller.add_data_to_form_confirm(msg.from_user.id, msg.text)
        bot_controller.go_next_state(msg.from_user.id)


def handle_get_count_hotels(bot: TeleBot, bot_controller: BotController):
    @bot.message_handler(func=lambda msg: bot_controller.get_state_cmd(msg.from_user.id) == fsm.GET_SIZE_OUT,
                         content_types=['text'])
    def get_count_hotels_step(msg: Message):
        if not is_valid_number(msg.text, 1, 25):
            bot.reply_to(msg, 'Введите число в диапазоне 1..25')
            return

        bot_controller.add_cmd_options(msg.from_user.id, size_result=int(msg.text))
        bot_controller.add_data_to_form_confirm(msg.from_user.id, msg.text)
        bot_controller.go_next_state(msg.from_user.id)


def handle_unknown_message(bot: TeleBot, bot_controller: BotController):
    @bot.message_handler(func=lambda msg: msg.text != 'Отмена')
    def unknown_message(msg):
        bot.reply_to(msg, 'Неизвестная команда. Список команд: /help')
        id_user = msg.from_user.id
        obj_msg_form = bot_controller.get_obj_msg_cur_state(id_user)
        if obj_msg_form:
            text_form = obj_msg_form.text
            keyboard_form = obj_msg_form.reply_markup
            bot.send_message(id_user, text_form, parse_mode='HTML', reply_markup=keyboard_form)
