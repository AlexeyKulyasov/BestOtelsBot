from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

import fsm


def make_inline_keyboard(btn_property_lst: list, size_kb: int = 1) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=size_kb)
    button_lst = []
    for btn_property in btn_property_lst:
        button = InlineKeyboardButton(btn_property['caption'], callback_data=btn_property['callback'])
        button_lst.append(button)
    keyboard.add(*button_lst)

    return keyboard


def make_reply_keyboard(btn_caption_lst: tuple, size_kb: int = 1) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=size_kb)
    [keyboard.add(caption) for caption in btn_caption_lst]
    keyboard.add('Отмена')

    return keyboard


def form_check_entered_data(cmd_name: str, cmd_params: dict):
    text_form = '<u>Проверьте, все ли верно:</u>\n\n'
    text_form += f'<b>Команда:</b> {cmd_name}\n'
    for title, val in cmd_params.items():
        text_form += f'<b>{title}:</b> {val}\n'

    keyboard = make_inline_keyboard([{'caption': 'Да, все верно', 'callback': 'exec_cmd'},
                                     {'caption': 'Нет, начать сначала', 'callback': 'start_cmd_again'}
                                     ], size_kb=2)

    return text_form, keyboard


def form_set_def_value():
    text_form = fsm.questions[fsm.IS_SET_DEF_VALUE]
    keyboard = make_inline_keyboard([{'caption': 'Оставить по умолчанию', 'callback': 'set_default'},
                                     {'caption': 'Изменить', 'callback': 'change_default'}
                                     ])
    return text_form, keyboard


def form_choice_city(locations_info: dict):
    text_form = fsm.questions[fsm.CHOICE_CITY]
    keyboard = make_reply_keyboard(tuple(locations_info.keys()))

    return text_form, keyboard
