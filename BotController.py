import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Union

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException
from telebot.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, Message

import fsm
from bot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE
from executor_commands import CmdSortByPriceAndDist, CmdSortByPrice
from forms_questions import form_check_entered_data, form_set_def_value, form_choice_city, form_entered_date


logger = logging.getLogger('main.bot_controller')

cmd_desc = {'/help': 'показать это сообщение',
            '/lowprice': 'самые дешёвые отели в городе',
            '/highprice': 'самые дорогие отели в городе',
            '/bestdeal': 'наиболее подходящие по цене и расположению от центра'
            }


def generate_html_hotel_info(hotel_info: dict) -> str:
    """Формирование информации по отелю в html формате, для вывода пользователю.

    :param hotel_info: вся информация по отелю в виде словаря.
    :return: :str
    """

    text = f'<b>Название</b>: {hotel_info["name"]}\n\n'
    text += f'<b>Адрес</b>: {hotel_info["address"]}\n'
    text += f'<b>До центра города</b>: {hotel_info["to_center"]}\n\n'
    text += f'<b>Цена</b>: {hotel_info["price"]} ({hotel_info["price_info"]})'

    return text


#  классы обработчиков выполнения команд
handlers_cmd = {'/lowprice': CmdSortByPrice,
                '/highprice': CmdSortByPrice,
                '/bestdeal': CmdSortByPriceAndDist
                }

#  CallbackData для календаря по вводу даты въезда/выезда
calendar_callback = CallbackData("calendar", "action", "year", "month", "day")


@dataclass
class UserData:
    """
    Класс для хранения атрибутов активной команды пользователя.

    :param active_cmd (str): имя запущенной команды.
    :param state_cmd (int): состояние запущенной команды
    :param api_params (dict): формирование данных для api запроса
    :param cmd_options (dict): дополнительная информация по команде (размер вывода, диапазон расстояний)
    :param form_confirm (dict): формирование данных для вывода в форму подтверждения
    :param locations_info (dict): сохранение данных по найденным локациям
    :param obj_message_cur_state (Message): объект последнего отправленного телеграм сообщения пользователю
    :param calendar (Calendar): объект календаря для выбора дат въезда/выезда
    """

    active_cmd: str
    state_cmd: int = field(init=False, default=None)
    api_params: dict = field(init=False, default_factory=dict)
    cmd_options: dict = field(init=False, default_factory=dict)
    form_confirm: dict = field(init=False, default_factory=dict)
    locations_info: dict = field(init=False, default_factory=dict)
    obj_message_cur_state: Message = field(init=False)
    calendar: Calendar = field(init=False, default=None)


class BotController:
    """
    Класс по управлению ботом. Хранит всю полученную от пользователей информацию
    и текущее состояние команды (FSM). Имеет методы записи/извлечения полученной информации,
    перевод команды в следующее FSM. Запуск команды на исполнение и вывод результатов пользователю.

    :param users (dict): хранит информация по атрибутам команд пользователей.
    """

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

    def get_obj_msg_cur_state(self, user_id: int) -> Message:
        if user_id in self.users:
            return self.users[user_id].obj_message_cur_state

    def get_calendar(self, user_id: int) -> Calendar:
        if user_id in self.users:
            return self.users[user_id].calendar

    def save_locations_info(self, user_id: int, locations: dict) -> None:
        self.users[user_id].locations_info.update(locations)

    def add_data_to_form_confirm(self, user_id: int, value: Union[str, int], state: int = None) -> None:
        """
        Добавление/сохранение параметров команды в виде: название параметра - значение.
        Информация используется перед запуском исполнения команды, когда пользователю
        предлагается подтвердить все введенные параметры команды.

        :param user_id: id пользователя
        :param value: значение параметра
        :param state: id состояния команды
        """

        if state is None:
            state = self.get_state_cmd(user_id)
        data_form = {fsm.title_form_confirm[state]: value}
        self.users[user_id].form_confirm.update(data_form)

    def get_state_attrs(self, user_id: int, new_state: int):
        """
        Получение текста вопроса и клавиатуры в зависимости от текущего состояния команды.

        :param user_id: id пользователя
        :param new_state: id состояния команды

        :return текст вопроса и клавиатура
        :rtype str, ReplyKeyboardMarkup|InlineKeyboardMarkup
        """

        if new_state == fsm.END:
            return form_check_entered_data(self.users[user_id].active_cmd, self.users[user_id].form_confirm)

        if new_state == fsm.CHOICE_CITY:
            return form_choice_city(self.users[user_id].locations_info)

        if new_state == fsm.IS_SET_DEF_VALUE:
            return form_set_def_value()

        if new_state in (fsm.GET_CHECKIN_DATE, fsm.GET_CHECKOUT_DATE):
            if not self.users[user_id].calendar:
                calendar = Calendar(language=RUSSIAN_LANGUAGE)
                self.users[user_id].calendar = calendar
            else:
                calendar = self.users[user_id].calendar
            return form_entered_date(new_state, calendar, calendar_callback)

        btn_cancel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_cancel.row('Отмена')
        return fsm.questions[new_state], btn_cancel

    def set_new_state(self, user_id: int, new_state: int) -> None:
        """
        Присвоение команде указанного состояния, запрос её атрибутов (вопрос, клавиатура),
        отправка пользователю полученных атрибутов команды.

        :param user_id: id пользователя
        :param new_state: id состояния команды
        """

        self.users[user_id].state_cmd = new_state
        if new_state == fsm.START:
            self.go_next_state(user_id)
            return
        msg, markup = self.get_state_attrs(user_id, new_state)
        obj_message = self.bot.send_message(user_id, msg, reply_markup=markup, parse_mode='HTML')
        self.users[user_id].obj_message_cur_state = obj_message

    def go_next_state(self, user_id: int) -> None:
        """
        Определение следующего состояния команды и
        вызов метода для установки нового состояния.

        :param user_id: id пользователя
        """

        states_cmd = fsm.states[self.get_active_cmd(user_id)]
        ind_next_state = states_cmd.index(self.get_state_cmd(user_id)) + 1
        new_state = states_cmd[ind_next_state]
        self.set_new_state(user_id, new_state)

    def send_lst_hotels(self, user_id: int, hotels: list) -> None:
        """
        Отправка пользователю сформированную информацию по отелям.
        При возникновении исключения делается попытка отправки фото отеля из файла.

        :param user_id: id пользователя
        :param hotels: обработанный список с информацией по отелям
        """

        for hotel in hotels:
            self.bot.send_chat_action(user_id, 'typing')  # показывает индикатор «набора текста»
            html_hotel_info = generate_html_hotel_info(hotel)
            try:
                self.bot.send_photo(user_id, hotel['url_photo'], caption=html_hotel_info, parse_mode='HTML')
            except ApiTelegramException:
                logger.exception(f'Ошибка при отправке информации по отелю: {hotel}')
                with open('debug_data/hotel.png', 'rb') as photo_hotel:
                    self.bot.send_photo(user_id, photo_hotel, caption=html_hotel_info, parse_mode='HTML')

    def exec_cmd(self, user_id: int) -> None:
        """
        Запуск команды на исполнение, получение результатов и отправка их пользователю.

        :param user_id: id пользователя
        """

        if not self.users.get(user_id):
            return
        user_data = self.users[user_id]
        active_cmd = user_data.active_cmd
        implementer = handlers_cmd[active_cmd](user_data.api_params,
                                               user_data.cmd_options,
                                               self.debug_mode)
        result = implementer.start()

        if self.users.get(user_id) and self.get_state_cmd(user_id) == fsm.END:
            if result.err_msg:
                self.bot.send_message(user_id, result.err_msg, reply_markup=ReplyKeyboardRemove())
            elif not result.hotels:
                self.bot.send_message(user_id, 'К сожалению по вашему запросу доступных отелей не найдено.',
                                      reply_markup=ReplyKeyboardRemove())
            else:
                head_text = f'<b>Получен результат команды {active_cmd}</b>\n' \
                            f'({cmd_desc[active_cmd]})'
                head_text += '<i>' + result.warning_msg + '</i>'
                self.bot.send_message(user_id, head_text, parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
                self.send_lst_hotels(user_id, result.hotels)

            self.cancel_cmd(user_id)
