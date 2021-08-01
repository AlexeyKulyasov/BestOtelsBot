from dataclasses import dataclass, field
from typing import Optional, Dict, Union

from telebot import TeleBot, types

import fsm
from config import CURRENCY
from forms_questions import form_check_entered_data, form_set_def_value, form_choice_city
from resources import query_hotels_by_param


cmd_desc = {'/help': 'показать это сообщение',
            '/lowprice': 'самые дешёвые отели в городе',
            '/highprice': 'самые дорогие отели в городе',
            '/bestdeal': 'наиболее подходящие по цене и расположению от центра'
            }


def generate_html_hotel_info(hotel_info: dict) -> str:
    text = f'<b>Название</b>: {hotel_info["name"]}\n\n'
    text += f'<b>Адрес</b>: {hotel_info["address"]}\n'
    text += f'<b>До центра города</b>: {hotel_info["to_center"]}\n\n'
    text += f'<b>Цена</b>: {hotel_info["price"]} {CURRENCY} ({hotel_info["price_info"]})'

    return text


#  хранение атрибутов активной команды пользователя
@dataclass
class UserData:
    active_cmd: str
    state_cmd: int = field(init=False, default=None)
    api_params: dict = field(init=False, default_factory=dict)
    cmd_options: dict = field(init=False, default_factory=dict)
    form_confirm: dict = field(init=False, default_factory=dict)
    locations_info: dict = field(init=False, default_factory=dict)
    obj_message_cur_state: types.Message = field(init=False)
    # dist_range: tuple[int] (входит в cmd_options)
    # price_range: tuple[int] (входит в api_params)


class BotController:
    users: Dict[int, UserData] = {}

    def __init__(self, tg_bot: TeleBot, debug_mode: bool):
        self.bot = tg_bot
        self.debug_mode = debug_mode

    def set_command(self, user_id: int, cmd_name: str) -> None:
        self.users[user_id] = UserData(active_cmd=cmd_name)

    def add_api_params(self, user_id: int, **data) -> None:
        self.users[user_id].api_params.update(data)

    def add_cmd_options(self, user_id: int, **data) -> None:
        self.users[user_id].cmd_options.update(data)

    def cancel_cmd(self, user_id: int) -> None:
        if user_id in self.users:
            self.users.pop(user_id)

    def get_active_cmd(self, user_id: int) -> Optional[str]:
        if user_id in self.users:
            return self.users[user_id].active_cmd

    def get_state_cmd(self, user_id: int) -> Optional[int]:
        if user_id in self.users:
            return self.users[user_id].state_cmd

    def get_obj_msg_cur_state(self, user_id: int):
        if user_id in self.users:
            return self.users[user_id].obj_message_cur_state

    def save_locations_info(self, user_id: int, locations: dict):
        self.users[user_id].locations_info.update(locations)

    def add_data_to_form_confirm(self, user_id: int, value: Union[str, int], state: int = None) -> None:
        if state is None:
            state = self.get_state_cmd(user_id)
        data_form = {fsm.title_form_confirm[state]: value}
        self.users[user_id].form_confirm.update(data_form)

    def get_state_attrs(self, user_id: int, new_state: int):
        if new_state == fsm.END:
            return form_check_entered_data(self.users[user_id].active_cmd, self.users[user_id].form_confirm)
        if new_state == fsm.CHOICE_CITY:
            return form_choice_city(self.users[user_id].locations_info)
        if new_state == fsm.IS_SET_DEF_VALUE:
            return form_set_def_value()

        btn_cancel = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_cancel.row('Отмена')
        return fsm.questions[new_state], btn_cancel

    def set_new_state(self, user_id: int, new_state: int) -> None:
        self.users[user_id].state_cmd = new_state
        if new_state == fsm.START:
            self.go_next_state(user_id)
            return
        msg, markup = self.get_state_attrs(user_id, new_state)
        obj_message = self.bot.send_message(user_id, msg, reply_markup=markup, parse_mode='HTML')
        self.users[user_id].obj_message_cur_state = obj_message

    def go_next_state(self, user_id: int):
        states_cmd = fsm.states[self.get_active_cmd(user_id)]
        ind_next_state = states_cmd.index(self.get_state_cmd(user_id)) + 1
        new_state = states_cmd[ind_next_state]
        self.set_new_state(user_id, new_state)

    def exec_cmd(self, user_id: int):
        if not self.users.get(user_id):
            return
        user_data = self.users[user_id]
        if user_data.active_cmd in ['/lowprice', '/highprice']:
            hotels_info = query_hotels_by_param(data_query=user_data.api_params,
                                                page_size=user_data.cmd_options['size_result'],
                                                debug_mode=self.debug_mode)
            if self.users.get(user_id):
                if hotels_info == -1:
                    self.bot.send_message(user_id, 'Ошибка запроса.Попробуйте выполнить команду позднее.')
                elif not hotels_info:
                    self.bot.send_message(user_id, 'К сожалению по вашему запросу доступных отелей не найдено.')
                else:
                    head_text = f'<b>Получен результат команды {user_data.active_cmd}</b>\n' \
                                f'({cmd_desc[user_data.active_cmd]})\n'
                    count_hotels = len(hotels_info)
                    if count_hotels < user_data.cmd_options['size_result']:
                        head_text += f'Количество найденных предложений: {count_hotels}'
                    self.bot.send_message(user_id, head_text, parse_mode='HTML',
                                          reply_markup=types.ReplyKeyboardRemove())

                    for hotel in hotels_info:
                        self.bot.send_chat_action(user_id, 'typing')  # показывает индикатор «набора текста»
                        html_hotel_info = generate_html_hotel_info(hotel)
                        self.bot.send_photo(user_id, hotel['url_photo'], caption=html_hotel_info, parse_mode='HTML')
                self.cancel_cmd(user_id)
