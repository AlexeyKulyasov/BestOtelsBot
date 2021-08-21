import json
import logging
import os
import re
from typing import NamedTuple

import requests

import config


logger = logging.getLogger('main.resources')

LOCATION_URL = "https://hotels4.p.rapidapi.com/locations/search"
LIST_HOTEL_URL = "https://hotels4.p.rapidapi.com/properties/list"


class LocationInfo(NamedTuple):
    """
    Структура возвращаемых данных при выполнении api запроса на получения списка локаций.

    :param locations: (optional) list[dict], найденные локации (города, районы, селения) и их id.
    :param err_msg: (optional) Str, текст ошибки в случае неуспешного api запроса
    """
    locations: dict = None
    err_msg: str = None


class HotelsInfo(NamedTuple):
    """
    Структура возвращаемых данных при выполнении api запроса на получения списка отелей.

    :param hotels: (optional) list[dict], информация о найденных отелях.
    :param next_page_number: (optional) Int, пагинация, номер следующей страницы с отелями
    :param err_msg: (optional) Str, текст ошибки в случае неуспешного api запроса
    """
    hotels: list = None
    err_msg: str = None
    next_page_number: int = None


ERR_MSG = 'Ошибка запроса{desc}. Попробуйте выполнить команду позднее.'


def query_locations_info(name_city: str, debug_mode: bool) -> LocationInfo:
    """
    Выполнение api запроса на получения списка локаций по запрашиваемому городу.

    :param name_city: название города.
    :param debug_mode: флаг тестового режима.

    :return список полученных локаций.
    :rtype class: LocationInfo
    """

    query_dict = {"query": name_city, "locale": config.LOCALE}

    res_data = {}
    if debug_mode and name_city.strip().lower() == config.DEBUG_NAME_CITY:
        mock_file = 'debug_data/locations.json'
        if os.path.exists(mock_file):
            logger.debug(f'Загрузка локаций из файла {mock_file}')
            with open(mock_file, 'r') as f_json:
                res_data = json.load(f_json)
        else:
            logger.error(f'Файл с локациями {mock_file} не найден!')
    else:
        try:
            res = requests.get(LOCATION_URL, headers=config.HEADERS_RAPID_API, params=query_dict, timeout=15)
        except requests.exceptions.ReadTimeout:
            logger.exception('Превышен таймаут ответа при запросе локаций!')
            return LocationInfo(err_msg=ERR_MSG.format(desc=' (превышен таймаут ответа)'))

        if res.status_code != 200:
            logger.error(f'При запросе локаций сервер вернул status_code [{res.status_code}].'
                         f' Текст ответа: "{res.text}"')
            return LocationInfo(err_msg=ERR_MSG.format(desc=''))
        res_data = res.json()

    suggestions = res_data.get('suggestions', [])
    ct_group = [group for group in suggestions if group.get('group') == 'CITY_GROUP']
    if not ct_group:
        return LocationInfo(locations={})

    ct_group = ct_group[0]
    city_ids = {}
    for item in ct_group.get('entities', []):
        id_city = int(item.get('destinationId', -1))
        caption = item.get('caption')
        if id_city == -1 or not caption:
            continue
        caption = caption.replace("<span class='highlighted'>", '')
        caption = caption.replace("</span>", '')
        city_ids[caption] = id_city

    return LocationInfo(locations=city_ids)


def query_hotels_by_param(data_query: dict, debug_mode: bool,
                          page_number: int = 1, page_size: int = 25) -> HotelsInfo:
    """
    Выполнение api запроса на получения списка отелей по запрашиваемым параметрам.
    Извлечение из результата необходимых характеристик отелей.

    :param data_query: параметры api запроса.
    :param debug_mode: флаг тестового режима.
    :param page_number: номер запрашиваемой страницы.
    :param page_size: кол-во отелей на странице.

    :return список отелей с характеристиками, номер след. страницы, текст ошибки.
    :rtype class: HotelsInfo.
    """

    data_query.update({'pageNumber': page_number, 'pageSize': page_size,
                       'locale': config.LOCALE, 'currency': config.CURRENCY})

    if debug_mode:
        test_files = {'PRICE': 'hotels_low_price.json', 'PRICE_HIGHEST_FIRST': 'hotels_high_price.json',
                      'DISTANCE_FROM_LANDMARK': 'hotels_by_range_price_{}.json'}

        #  определение json файла с тестовыми данными
        file_name = test_files[data_query['sortOrder']]
        if file_name.find('range') != -1:
            file_name = file_name.format(page_number)

        cwd = os.path.dirname(os.path.abspath(__file__))
        mock_file = os.path.join(cwd, 'debug_data', file_name)
        res_data = {}
        if os.path.exists(mock_file):
            logger.debug(f'Загрузка отелей из файла {mock_file}')
            with open(mock_file, 'r') as f_json:
                res_data = json.load(f_json)
        else:
            logger.error(f'Файл с отелями {mock_file} не найден!')
    else:
        try:
            res = requests.get(LIST_HOTEL_URL, headers=config.HEADERS_RAPID_API, params=data_query, timeout=15)
        except requests.exceptions.ReadTimeout:
            logger.exception('Превышен таймаут ответа при запросе списка отелей!')
            return HotelsInfo(err_msg=ERR_MSG.format(desc=' (превышен таймаут ответа)'))

        if res.status_code != 200:
            logger.error(f'При запросе списка отелей сервер вернул status_code [{res.status_code}].'
                         f' Текст ответа: "{res.text}"')
            return HotelsInfo(err_msg=ERR_MSG.format(desc=''))

        res_data = res.json()

        # для отладки, просмотр api ответа, если вдруг какие ошибки
        with open('debug_data/hotels_load.json', 'w', encoding='utf8') as f_json:
            json.dump(res_data, f_json, indent=2, ensure_ascii=False)

    if res_data.get('result') != 'OK':
        err_msg = res_data.get('error_message')
        logger.error(f'При запросе списка отелей в возвращенном json - result none OK.'
                     f' Текст ошибки: {err_msg}. Подробности в debug_data/hotels_load.json.')
        return HotelsInfo(err_msg=ERR_MSG.format(desc=' (Result none OK)'))

    try:
        search_results = res_data['data']['body']['searchResults']
        results = search_results['results']
    except KeyError as e:
        logger.error(f'При запросе списка отелей в возвращенном json неожиданно отсутствует ключ: {e}.'
                     f' Параметры запроса: {data_query}')
        return HotelsInfo(hotels=[])
    next_page_number = search_results.get('pagination', {}).get('nextPageNumber', 0)

    if debug_mode:
        results = results[:page_size]
    hotels_lst = []
    for hotel in results:
        name = hotel.get('name', 'не определено')
        street = hotel.get('address', {}).get('streetAddress', 'не определено')
        locality = hotel.get('address', {}).get('locality', 'не определено')
        address = ', '.join([street, locality])
        price_exact = hotel.get('ratePlan', {}).get('price', {}).get('exactCurrent')
        if not price_exact:
            continue
        price = hotel.get('ratePlan', {}).get('price', {}).get('current', 'не определено')
        price_info = hotel.get('ratePlan', {}).get('price', {}).get('info', 'не определено')
        to_center_exact = None
        for label in hotel.get('landmarks', []):
            if label.get('label', '') == 'Центр города':
                dist_to_center = label.get('distance', 'не определено')
                if dist_to_center != 'не определено':
                    to_center_number, *_ = dist_to_center.split()
                    if re.sub(r'\.|,', '', to_center_number, count=1).isdigit():
                        to_center_exact = float(to_center_number.replace(',', '.'))
                break
        else:
            dist_to_center = 'не определено'

        photo_hotel = ''
        thumbnail_url = hotel.get('optimizedThumbUrls', {}).get('srpDesktop')
        if thumbnail_url:
            photo_hotel = 'https://exp.cdn-hotels.com/' + re.search(r'hotels.+', thumbnail_url).group()

        hotels_lst.append({'name': name,
                           'address': address,
                           'price_exact': float(price_exact),
                           'price': price,
                           'price_info': price_info,
                           'to_center': dist_to_center,
                           'to_center_exact': to_center_exact,
                           'url_photo': photo_hotel}
                          )

    return HotelsInfo(hotels=hotels_lst, next_page_number=next_page_number)
