import requests

import config


def get_city_coord(city):
    payload = {"geocode": city, "apikey": config.geo_key, "format": "json"}  # параметры запроса
    r = requests.get("https://geocode-maps.yandex.ru/1.x", params=payload)
    print(r)


get_city_coord("Ставрополь")
