"""Finite State Machine"""

'''States'''

START = 0
GET_LOCATION = 1
CHOICE_CITY = 9
GET_NUM_HUMANS = 2
GET_CHECKIN_DATE = 3
GET_CHECKOUT_DATE = 4
GET_RANGE_PRICE = 5
GET_RANGE_DIST = 6
GET_SIZE_OUT = 7
IS_SET_DEF_VALUE = 8
END = 100

states = {'/lowprice': (START, GET_LOCATION, CHOICE_CITY, GET_SIZE_OUT, IS_SET_DEF_VALUE, GET_NUM_HUMANS,
                        GET_CHECKIN_DATE, GET_CHECKOUT_DATE, END),
          '/highprice': (START, GET_LOCATION, CHOICE_CITY, GET_SIZE_OUT, IS_SET_DEF_VALUE, GET_NUM_HUMANS,
                         GET_CHECKIN_DATE, GET_CHECKOUT_DATE, END),
          '/bestdeal': (START, GET_LOCATION, CHOICE_CITY, GET_RANGE_PRICE, GET_RANGE_DIST, GET_SIZE_OUT,
                        IS_SET_DEF_VALUE, GET_NUM_HUMANS, GET_CHECKIN_DATE, GET_CHECKOUT_DATE, END)
          }

questions = {
    GET_LOCATION: 'Укажите город, где будет проводиться поиск?',
    CHOICE_CITY: 'Подтвердите/уточните местоположение, выберите кнопкой один из вариантов ниже:',
    GET_NUM_HUMANS: 'Количество гостей?',
    GET_CHECKIN_DATE: 'Дата въезда (гггг-мм-дд) ?',
    GET_CHECKOUT_DATE: 'Ок. Теперь дата выезда (гггг-мм-дд) ?',
    GET_RANGE_PRICE: '',
    GET_RANGE_DIST: '',
    GET_SIZE_OUT: 'Количество отелей в выводе (max 25) ?',
    IS_SET_DEF_VALUE: 'По умолчанию, поиск ведется для одного гостя и ближайших 3-х суток проживания.'
}

title_form_confirm = {
    CHOICE_CITY: 'Город для поиска',
    GET_NUM_HUMANS: 'Количество гостей',
    GET_CHECKIN_DATE: 'Дата въезда',
    GET_CHECKOUT_DATE: 'Дата выезда',
    GET_RANGE_PRICE: '',
    GET_RANGE_DIST: '',
    GET_SIZE_OUT: 'Количество отелей в выводе'
}
