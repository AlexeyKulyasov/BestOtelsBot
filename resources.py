import json
import os
import re
from typing import List, Union

import requests

import config

LOCATION_URL = "https://hotels4.p.rapidapi.com/locations/search"
LIST_HOTEL_URL = "https://hotels4.p.rapidapi.com/properties/list"


def query_locations_info(name_city: str, debug_mode: bool) -> Union[int, dict[str, int]]:
    query_dict = {"query": name_city, "locale": config.LOCALE}

    res_data = {}
    if debug_mode and name_city.strip() == config.DEBUG_NAME_CITY:
        mock_file = 'debug_data/locations.json'
        if os.path.exists(mock_file):
            print(f'load from {mock_file}')
            with open(mock_file, 'r') as f_json:
                res_data = json.load(f_json)
    else:
        try:
            res = requests.get(LOCATION_URL, headers=config.HEADERS_RAPID_API, params=query_dict, timeout=10)
        except requests.exceptions.ReadTimeout as e:
            #  логируем
            return -1
        if res.status_code != 200:
            #  логируем
            return -1
        res_data = res.json()

    suggestions = res_data.get('suggestions', [])
    ct_group = [group for group in suggestions if group.get('group') == 'CITY_GROUP']
    if not ct_group:
        return {}

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

    return city_ids


def query_hotels_by_param(data_query: dict, debug_mode: bool,
                          page_number: int = 1, page_size: int = 25) -> Union[int, List[dict]]:
    data_query.update({'pageNumber': page_number, 'pageSize': page_size,
                       'locale': config.LOCALE, 'currency': config.CURRENCY})

    if debug_mode:
        file_name = 'hotels_low_price.json' if data_query['sortOrder'] == 'PRICE' else 'hotels_high_price.json'
        mock_file = f'debug_data/{file_name}'
        res_data = {}
        if os.path.exists(mock_file):
            print(f'load from {mock_file}')
            with open(mock_file, 'r') as f_json:
                res_data = json.load(f_json)
    else:
        try:
            res = requests.get(LIST_HOTEL_URL, headers=config.HEADERS_RAPID_API, params=data_query, timeout=10)
        except requests.exceptions.ReadTimeout as e:
            #  логируем
            return -1
        if res.status_code != 200:
            #  логируем
            return -1

        res_data = res.json()

        # для отладки, просмотр api ответа, если вдруг какие ошибки
        with open('debug_data/hotels_load.json', 'w', encoding='utf8') as f_json:
            json.dump(res_data, f_json, indent=2, ensure_ascii=False)

        if res_data.get('result') != 'OK':
            #  логируем, ошибка будет в res_data['error_message']
            return -1

    if not res_data.get('data'):
        return []
    search_results = res_data.get('data', {}).get('body', {}).get('searchResults', {}).get('results', [])

    if debug_mode:
        search_results = search_results[:page_size]
    hotels_lst = []
    for hotel in search_results:
        name = hotel.get('name', 'не определено')
        street = hotel.get('address', {}).get('streetAddress', 'не определено')
        locality = hotel.get('address', {}).get('locality', 'не определено')
        address = ', '.join([street, locality])
        price = hotel.get('ratePlan', {}).get('price', {}).get('exactCurrent', 'не определено')
        price_info = hotel.get('ratePlan', {}).get('price', {}).get('info', 'не определено')
        for label in hotel.get('landmarks', []):
            if label.get('label', '') == 'Центр города':
                dist_to_center = label.get('distance', 'не определено')
                break
        else:
            dist_to_center = 'не определено'

        photo_hotel = open('debug_data/hotel.png', 'rb')
        thumbnail_url = hotel.get('optimizedThumbUrls', {}).get('srpDesktop')
        if thumbnail_url:
            url_photo = 'https://exp.cdn-hotels.com/' + re.search(r'hotels.+', thumbnail_url).group()
            res = requests.head(url_photo, allow_redirects=True)
            if res.status_code == 200:
                photo_hotel = url_photo
        hotels_lst.append({'name': name,
                           'address': address,
                           'price': price,
                           'price_info': price_info,
                           'to_center': dist_to_center,
                           'url_photo': photo_hotel}
                          )

    return hotels_lst
