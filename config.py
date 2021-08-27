import os

from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv('TG_TOKEN')

HEADERS_RAPID_API = {
    'x-rapidapi-key': os.getenv('RAPID_API_KEY'),
    'x-rapidapi-host': "hotels4.p.rapidapi.com"
    }

LOCALE = "ru_RU"
CURRENCY = "RUB"

DEBUG_NAME_CITY = 'москва'
