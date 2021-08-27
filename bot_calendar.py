"""
Доработанная библиотека для выбора даты из календаря посредством инлайн клавиатуры бота.
Оригинал: https://github.com/FlymeDllVa/telebot-calendar

Мои доработки (by Kulyasov Alexey):
1. Запрет выбора даты въезда ранее текущей (есть всплывающее оповещение).
2. Запрет выбора даты выезда ранее и равной дате въезда.
3. Утверждение выбранной даты кнопкой "ОК" (появляется возможность перевыбора даты).
4. Иконка на кнопке дня календаря "⤴" - при выборе даты въезда и "⤵" - при выезде.
5. Сохранение иконок въезда/выезда при перелистывании календаря.
6. Добавление к тексту вопроса (отправляемый вместе с календарем) по указанию даты, информации о выбранной дате.
7. Сохранение в календаре информации о дате въезда, чтобы при показе календаря для выбора даты выезда,
 показать отмеченный день въезда.

"""

import datetime
import calendar
import re
import typing
from dataclasses import dataclass

from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


@dataclass
class Language:
    days: tuple
    months: tuple


ENGLISH_LANGUAGE = Language(
    days=("Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"),
    months=(
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ),
)

RUSSIAN_LANGUAGE = Language(
    days=("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"),
    months=(
        "Январь",
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь",
    ),
)


class Calendar:
    """
    Calendar data factory
    """

    __lang: Language

    def __init__(self, language: Language = ENGLISH_LANGUAGE):
        self.__lang = language
        self.cur_selection = None
        self.save_date = None

    def create_calendar(
        self,
        name: str = "calendar",
        year: int = None,
        month: int = None,
    ) -> InlineKeyboardMarkup:
        """
        Create a built in inline keyboard with calendar

        :param name:
        :param year: Year to use in the calendar if you are not using the current year.
        :param month: Month to use in the calendar if you are not using the current month.
        :return: Returns an InlineKeyboardMarkup object with a calendar.
        """

        now_day = datetime.datetime.utcnow()

        if year is None:
            year = now_day.year
        if month is None:
            month = now_day.month

        calendar_callback = CallbackData(name, "action", "year", "month", "day")
        data_ignore = calendar_callback.new("IGNORE", year, month, "!")
        data_months = calendar_callback.new("MONTHS", year, month, "!")

        keyboard = InlineKeyboardMarkup(row_width=7)

        keyboard.add(
            InlineKeyboardButton(
                self.__lang.months[month - 1] + " " + str(year),
                callback_data=data_months,
            )
        )

        keyboard.add(
            *[
                InlineKeyboardButton(day, callback_data=data_ignore)
                for day in self.__lang.days
            ]
        )

        for week in calendar.monthcalendar(year, month):
            row = list()
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
                elif datetime.datetime(year, month, day) in (self.cur_selection, self.save_date):
                    if self.save_date and self.cur_selection == datetime.datetime(year, month, day):
                        symbol = "⤵"
                    else:
                        symbol = "⤴"
                    row.append(
                        InlineKeyboardButton(
                            symbol,
                            callback_data=calendar_callback.new(
                                "DAY", year, month, day
                            ),
                        )
                    )
                elif (
                    f"{now_day.day}.{now_day.month}.{now_day.year}"
                    == f"{day}.{month}.{year}"
                ):
                    row.append(
                        InlineKeyboardButton(
                            f"<{day}>",
                            callback_data=calendar_callback.new(
                                "DAY", year, month, day
                            ),
                        )
                    )
                else:
                    row.append(
                        InlineKeyboardButton(
                            str(day),
                            callback_data=calendar_callback.new(
                                "DAY", year, month, day
                            ),
                        )
                    )
            keyboard.add(*row)

        keyboard.add(
            InlineKeyboardButton(
                "<",
                callback_data=calendar_callback.new("PREVIOUS-MONTH", year, month, "!"),
            ),
            InlineKeyboardButton(
                "OK",
                callback_data=calendar_callback.new("OK", year, month, "!"),
            ),
            InlineKeyboardButton(
                ">", callback_data=calendar_callback.new("NEXT-MONTH", year, month, "!")
            ),
        )

        return keyboard

    def create_months_calendar(
        self, name: str = "calendar", year: int = None
    ) -> InlineKeyboardMarkup:
        """
        Creates a calendar with month selection

        :param name:
        :param year:
        :return:
        """

        if year is None:
            year = datetime.datetime.now().year

        calendar_callback = CallbackData(name, "action", "year", "month", "day")

        keyboard = InlineKeyboardMarkup()

        for i, month in enumerate(
            zip(self.__lang.months[0::2], self.__lang.months[1::2])
        ):
            keyboard.add(
                InlineKeyboardButton(
                    month[0],
                    callback_data=calendar_callback.new("MONTH", year, 2 * i + 1, "!"),
                ),
                InlineKeyboardButton(
                    month[1],
                    callback_data=calendar_callback.new(
                        "MONTH", year, (i + 1) * 2, "!"
                    ),
                ),
            )

        return keyboard

    def calendar_query_handler(
        self,
        bot: TeleBot,
        call: CallbackQuery,
        name: str,
        action: str,
        year: int,
        month: int,
        day: int,
    ) -> None or datetime.datetime:
        """
        The method creates a new calendar if the forward or backward button is pressed
        This method should be called inside CallbackQueryHandler.


        :param bot: The object of the bot CallbackQueryHandler
        :param call: CallbackQueryHandler data
        :param day:
        :param month:
        :param year:
        :param action:
        :param name:
        :return: Returns a tuple
        """

        current = datetime.datetime(int(year), int(month), 1)
        msg_template = ' <b>Выбранная дата: {}</b>'
        if self.cur_selection:
            msg_txt = re.sub(r' Выбранная.+', msg_template.format(self.cur_selection.strftime("%d.%m.%Y")),
                             call.message.text)
        else:
            msg_txt = call.message.text
        if action == "IGNORE":
            bot.answer_callback_query(callback_query_id=str(call.id))
            return False, None
        elif action == "DAY":
            sel_date = datetime.datetime(int(year), int(month), int(day))
            if sel_date == self.cur_selection:
                bot.answer_callback_query(str(call.id))
                return
            if self.save_date and sel_date <= self.save_date:
                bot.answer_callback_query(str(call.id), 'Дата выезда должна быть позже даты въезда!')
                return
            if sel_date.date() >= datetime.datetime.utcnow().date():
                if self.cur_selection:
                    msg_txt = re.sub(r' Выбранная.+', msg_template.format(sel_date.strftime("%d.%m.%Y")),
                                     call.message.text)
                else:
                    msg_txt = call.message.text + msg_template.format(sel_date.strftime("%d.%m.%Y"))
                self.cur_selection = sel_date
                bot.edit_message_text(
                    text=msg_txt,
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=self.create_calendar(
                        name=name,
                        year=current.year,
                        month=current.month,
                    ),
                    parse_mode='HTML'
                )
            else:
                bot.answer_callback_query(str(call.id), 'Дата не должна быть ранее текущей!')
            return datetime.datetime(int(year), int(month), int(day))

        elif action == "PREVIOUS-MONTH":
            preview_month = current - datetime.timedelta(days=1)
            bot.edit_message_text(
                text=msg_txt,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=self.create_calendar(
                    name=name,
                    year=int(preview_month.year),
                    month=int(preview_month.month),
                ),
                parse_mode='HTML'
            )
            return None
        elif action == "NEXT-MONTH":
            next_month = current + datetime.timedelta(days=31)
            bot.edit_message_text(
                text=msg_txt,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=self.create_calendar(
                    name=name, year=int(next_month.year), month=int(next_month.month)
                ),
                parse_mode='HTML'
            )
            return None
        elif action == "MONTHS":
            bot.edit_message_text(
                text=msg_txt,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=self.create_months_calendar(name=name, year=current.year),
                parse_mode='HTML'
            )
            return None
        elif action == "MONTH":
            bot.edit_message_text(
                text=msg_txt,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=self.create_calendar(
                    name=name, year=int(year), month=int(month)
                ),
                parse_mode='HTML'
            )
            return None
        elif action == "OK":
            if self.cur_selection:
                self.save_date = self.cur_selection
                self.cur_selection = None
                return self.save_date
            else:
                bot.answer_callback_query(str(call.id), 'Сначала нужно указать дату!')
            return None

        else:
            bot.answer_callback_query(callback_query_id=str(call.id), text="ERROR!")
            bot.delete_message(
                chat_id=call.message.chat.id, message_id=call.message.message_id
            )
            return None


class CallbackData:
    """
    Callback data factory
    """

    def __init__(self, prefix, *parts, sep=":"):
        if not isinstance(prefix, str):
            raise TypeError(
                f"Prefix must be instance of str not {type(prefix).__name__}"
            )
        if not prefix:
            raise ValueError("Prefix can't be empty")
        if sep in prefix:
            raise ValueError(f"Separator {sep!r} can't be used in prefix")
        if not parts:
            raise TypeError("Parts were not passed!")

        self.prefix = prefix
        self.sep = sep

        self._part_names = parts

    def new(self, *args, **kwargs) -> str:
        """
        Generate callback data

        :param args:
        :param kwargs:
        :return:
        """

        args = list(args)

        data = [self.prefix]

        for part in self._part_names:
            value = kwargs.pop(part, None)
            if value is None:
                if args:
                    value = args.pop(0)
                else:
                    raise ValueError(f"Value for {part!r} was not passed!")

            if value is not None and not isinstance(value, str):
                value = str(value)

            if not value:
                raise ValueError(f"Value for part {part!r} can't be empty!'")
            if self.sep in value:
                raise ValueError(
                    f"Symbol {self.sep!r} is defined as the separator and can't be used in parts' values"
                )

            data.append(value)

        if args or kwargs:
            raise TypeError("Too many arguments were passed!")

        callback_data = self.sep.join(data)
        if len(callback_data) > 64:
            raise ValueError("Resulted callback data is too long!")

        return callback_data

    def parse(self, callback_data: str) -> typing.Dict[str, str]:
        """
        Parse data from the callback data

        :param callback_data:
        :return:
        """

        prefix, *parts = callback_data.split(self.sep)

        if prefix != self.prefix:
            raise ValueError("Passed callback data can't be parsed with that prefix.")
        elif len(parts) != len(self._part_names):
            raise ValueError("Invalid parts count!")

        result = {"@": prefix}
        result.update(zip(self._part_names, parts))

        return result

    def filter(self, **config):
        """
        Generate filter

        :param config:
        :return:
        """

        print(config, self._part_names)
        for key in config.keys():
            if key not in self._part_names:
                return False

        return True
