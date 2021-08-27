from dataclasses import dataclass, field
from operator import itemgetter
from typing import NamedTuple

from resources import query_hotels_by_param


class HotelsParsed(NamedTuple):
    """
    Структура возвращаемых данных после исполнения команды.

    :param hotels (optional) list[dict]: обработанная информация о найденных отелях.
    :param err_msg (optional, str): текст ошибки в случае неуспешного api запроса.
    :param warning_msg (str): текст примечания к сформированному списку отелей.
    """
    hotels: list = None
    err_msg: str = None
    warning_msg: str = ''


@dataclass
class CmdSortByPrice:
    """
    Класс исполнитель команд "lowprice" и "highprice".

    :param api_params (dict): данные для api запроса.
    :param cmd_options (dict): дополнительная информация по команде (размер вывода, диапазон расстояний).
    :param debug_mode (bool): флаг отладочного режима.
    :param required_size_result (int): размер вывода.
    """
    api_params: dict
    cmd_options: dict
    debug_mode: bool
    required_size_result: int = field(init=False)

    def __post_init__(self):
        self.required_size_result = self.cmd_options['size_result']

    def start(self) -> HotelsParsed:
        return self.cmd_sort_by_price()

    def cmd_sort_by_price(self, sort_direction: str = None, def_warning: str = '') -> HotelsParsed:
        """
        Функция отправляет api запрос на получение списка отелей в рамках команды ("lowprice" и "highprice"),
        возвращает его результат и формирует примечание, если размер полученного результата не совпадает с заданным.

        :param sort_direction: Optional, тип сортировки.
        :param def_warning: текст примечания для прикрепления к результату вывода.

        *Note: параметры sort_direction и def_warning используется при вызове метода в классе наследнике.

        :return обработанная информация по отелям
        :rtype class: HotelsParsed
        """

        api_params = self.api_params
        if sort_direction:
            api_params['sortOrder'] = sort_direction
        result = query_hotels_by_param(data_query=api_params, page_size=self.required_size_result,
                                       debug_mode=self.debug_mode)
        warning = def_warning
        warning += self._get_warning_mismatch_size_result(result.hotels)
        return HotelsParsed(hotels=result.hotels, err_msg=result.err_msg, warning_msg=warning)

    def _get_warning_mismatch_size_result(self, lst_hotels: list) -> str:
        """
        Проверяет размер полученного вывода с заданным пользователем.
        При несоответствии, формирует текст с количеством найденных предложений.

        :param lst_hotels: Список найденных отелей.
        """

        if lst_hotels is not None:
            count_hotels = len(lst_hotels)
            if count_hotels < self.required_size_result:
                return f'\n<b>Количество найденных предложений: {count_hotels}</b>'
        return ''


@dataclass
class CmdSortByPriceAndDist(CmdSortByPrice):
    """
    Класс исполнитель команды "bestdeal".

    :param page_number (int): текущий номер страницы для api запроса.
    :param next_page_number (int): ожидаемый номер следующей страницы.
    """
    page_number: int = field(init=False, default=1)
    next_page_number: int = field(init=False, default=1)

    def is_last_page(self) -> bool:
        return self.page_number >= self.next_page_number

    def start(self) -> HotelsParsed:
        """
        Отправка api запроса на получение списка отелей в рамках команды "bestdeal", получение результата
        и его обработка согласно логике команды.

        :return обработанная информация по отелям
        :rtype class: HotelsParsed
        """

        cur_lst_hotels = []
        prev_lst_hotels = []
        while True:
            result = query_hotels_by_param(data_query=self.api_params, debug_mode=self.debug_mode,
                                           page_number=self.page_number)

            if (result.err_msg or not result.hotels) and not cur_lst_hotels:
                return HotelsParsed(result.hotels, result.err_msg)

            if (result.err_msg or not result.hotels) and cur_lst_hotels:
                warning = ''
                if result.err_msg:
                    warning = '\n<b>При выполнении запроса возникли ошибки. Результат вывода может быть не точный!</b>'
                return self._sort_and_parsed_hotels(cur_lst_hotels, ('price_exact', 'to_center_exact'), warning)

            #  формируем список отелей с обозначенным расстоянием от центра города
            hotels_with_def_dist = [hotel for hotel in result.hotels if hotel['to_center_exact']]
            if not hotels_with_def_dist:
                warning = '\nВ указанной локации не найдено отелей с обозначенным расстоянием от центра города. ' \
                          'Показаны отели по росту цены (аналогично команде low_price).'
                return self.cmd_sort_by_price(sort_direction='PRICE', def_warning=warning)

            hotels = hotels_with_def_dist
            min_dist_user, max_dist_user = self.cmd_options['range_dist']
            #  получаем мин. и макс. дистанцию отеля от центра города на текущей странице
            min_dist_hotel = hotels[0]['to_center_exact']
            max_dist_hotel = hotels[-1]['to_center_exact']

            #  когда заданный диапазон расстояния находится слева от реально существующего диапазона отелей
            if max_dist_user < min_dist_hotel:
                warning = '\nНи один из отелей не попадает в указанный диапазон расстояния от центра города. ' \
                          f'Минимальное расстояние от центра {min_dist_hotel}. ' \
                          f'Показаны отели с минимально возможным расстоянием!'
                #  если есть список отелей полученный на предыдущих страницах, то возвращаем отели из этого списка
                if cur_lst_hotels:
                    hotels = cur_lst_hotels
                    warning = ''
                #  сортировка и проверка соответствия размеру вывода первых N отелей,
                #  где N - кол-во отелей для вывода
                return self._sort_and_parsed_hotels(hotels[:self.required_size_result],
                                                    ('price_exact', 'to_center_exact'), warning)

            self.next_page_number = result.next_page_number
            #  когда заданный диапазон расстояния находится справа от реально существующего диапазона отелей
            if max_dist_hotel < min_dist_user:
                if self.is_last_page():
                    warning = '\nНи один из отелей не попадает в указанный диапазон расстояния от центра города. ' \
                              f'Максимальное расстояние от центра {max_dist_hotel}. ' \
                              f'Показаны отели с максимально возможным расстоянием!'

                    #  если длина результата < требуемого, то добавляем текущие отели к отелям на пред. странице
                    if len(hotels) < self.required_size_result:
                        prev_lst_hotels.extend(hotels)
                        hotels = prev_lst_hotels
                    #  сортировка и проверка соответствия размеру вывода последних N отелей,
                    #  где N - кол-во отелей для вывода
                    return self._sort_and_parsed_hotels(hotels[-self.required_size_result:],
                                                        ('price_exact', 'to_center_exact'), warning)
                else:
                    self.page_number += 1
                    prev_lst_hotels = hotels[:]
                    continue

            #  когда заданный диапазон расстояний находится внутри диапазона расстояний полученного списка отелей
            #  получаем список отелей из заданного диапазона
            hotels_with_req_dist = [hotel for hotel in hotels
                                    if min_dist_user <= hotel['to_center_exact'] <= max_dist_user]
            cur_lst_hotels.extend(hotels_with_req_dist)
            #  если размер накопленного результата не меньше требуемого и правая граница заданного диапазона
            #  расстояния < макс. расстояния у отеля на текущей странице или текущая стр. последняя
            if (len(cur_lst_hotels) >= self.required_size_result
                and max_dist_user < max_dist_hotel) \
                    or self.is_last_page():
                return self._sort_and_parsed_hotels(cur_lst_hotels, ('price_exact', 'to_center_exact'), '')
            else:
                self.page_number += 1

    def _sort_and_parsed_hotels(self, lst_hotels: list, keys_sort: tuple, warning: str) -> HotelsParsed:
        """
        Сортировка результирующего списка отелей и формирование примечания, если размер полученного
        списка не совпадает с заданным пользователем.

        :param lst_hotels (list): результрующий список отелей для сортировки результатов
        :param keys_sort (tuple): ключи сортировки.
        :param warning (str): текст примечания.

        :return обработанная информация по отелям
        :rtype class: HotelsParsed
        """

        res_hotels = sorted(lst_hotels, key=itemgetter(*keys_sort))
        res_hotels = res_hotels[:self.required_size_result]
        warning += self._get_warning_mismatch_size_result(res_hotels)

        return HotelsParsed(hotels=res_hotels, warning_msg=warning)
