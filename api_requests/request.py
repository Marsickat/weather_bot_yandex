import json

import requests

from settings import api_config


def get_city_coord(city: str) -> str:
    """
    Возвращает координаты указанного города.

    Функция отправляет запрос к сервису геокодирования Яндекса JavaScript API и HTTP Геокодер для получения координат.
    В ответе на запрос содержатся данные о координатах города.
    Функция возвращает строку широты и долготы, разделённую пробелом.

    :param city: Название города, координаты которого необходимо получить.
    :type city: str
    :return: Строка, содержащая широту и долготу в формате "широта долгота".
    :rtype: str
    """
    payload = {"geocode": city, "apikey": api_config.geo_key, "format": "json"}
    r = requests.get("https://geocode-maps.yandex.ru/1.x", params=payload)
    geo = json.loads(r.text)
    return geo["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]


def get_weather(city: str) -> dict:
    """
    Получает данные о погоде для указанного города.

    Функция отправляет запрос к сервису погоды Яндекса API Яндекс.Погоды для получения данных о погоде для города.
    В ответе на запрос содержатся данные о погоде.
    Функция возвращает строку с данными о текущей погоде.

    :param city: Координаты города, для которого необходимо получить данные о погоде.
    :type city: str
    :return: Словарь с данными о текущей погоде для указанного города.
    :rtype: dict
    """
    coords = get_city_coord(city).split()
    payload = {"lon": coords[0], "lat": coords[1], "lang": "ru_RU"}
    r = requests.get("https://api.weather.yandex.ru/v2/forecast", params=payload, headers=api_config.weather_key)
    weather_data = json.loads(r.text)
    return weather_data["fact"]
