from typing import Optional, Type

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import db_config
from .models import Base, User, WeatherReport

engine = create_engine(db_config.url, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def add_user(tg_id: int):
    """
    Добавляет нового пользователя в базу данных, если пользователь с таким tg_id не существует.

    Функция проверяет наличие пользователя с указанным tg_id в базе данных.
    Если пользователь не найден, создаётся новый объект User с указанным tg_id и добавляется в базу данных.

    :param tg_id: Идентификатор пользователя Telegram.
    :type tg_id: int
    """
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    if user is None:
        new_user = User(tg_id=tg_id)
        session.add(new_user)
        session.commit()


def set_user_city(tg_id: int, city: str):
    """
    Устанавливает город проживания для пользователя с указанным tg_id.

    Функция ищет пользователя с указанным tg_id в базе данных.
    Если пользователь найден, обновляется значение поля "city" на указанный город.
    После обновления данных, изменения сохраняются в базе данных.

    :param tg_id: Идентификатор пользователя Telegram.
    :type tg_id: int
    :param city: Название города, который нужно установить для пользователя.
    :type tg_id: str
    """
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    user.city = city
    session.commit()


def create_report(tg_id: int, temp: int, feels_like: int, wind_speed: int, pressure_mm: int, city: str):
    """
    Создаёт отчёт о погоде для указанного пользователя с заданными данными.

    Функция ищет пользователя с указанным tg_id в базе данных.
    Если пользователь найден, создаётся новый объект WeatherReport с указанными данными о погоде.
    Новый отчёт добавляется в базу данных и сохраняется.

    :param tg_id: Идентификатор пользователя Telegram.
    :type tg_id: int
    :param temp: Температура в градусах Цельсия.
    :type temp: int
    :param feels_like: Ощущаемая температура в градусах Цельсия.
    :type feels_like: int
    :param wind_speed: Скорость ветра в м/с.
    :type wind_speed: int
    :param pressure_mm: Давление в мм рт. ст.
    :type pressure_mm: int
    :param city: Название города, для которого создаётся отчёт о погоде.
    :type tg_id: str
    """
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    new_report = WeatherReport(temp=temp, feels_like=feels_like, wind_speed=wind_speed, pressure_mm=pressure_mm,
                               city=city, owner=user.id)
    session.add(new_report)
    session.commit()


def get_user_city(tg_id: int) -> Optional[str]:
    """
    Возвращает город проживания пользователя с указанным tg_id.

    Функция ищет пользователя с указанным tg_id в базе данных.
    Если пользователь найден, возвращается значение поля "city", содержащее название города проживания.
    Если пользователь не найден или поле "city" не заполнено, функция возвращает None.

    :param tg_id: Идентификатор пользователя Telegram.
    :type tg_id: int
    :return: Название города проживания пользователя или None, если пользователь не найден или город не установлен.
    :rtype: Optional[str]
    """
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    return user.city


def get_reports(tg_id: int) -> list[WeatherReport]:
    """
    Возвращает список отчётов о погоде для пользователя с указанным tg_id.

    Функция ищет пользователя с указанным tg_id в базе данных.
    Если пользователь найден, возвращается список объектов WeatherReport, содержащих отчёты о погоде для пользователя.
    Если пользователь не найден или у пользователя нет отчётов, функция возвращает пустой список.

    :param tg_id: Идентификатор пользователя Telegram.
    :type tg_id: int
    :return: Список отчётов о погоде для пользователя или пустой список, если пользователь не найден или отчётов нет.
    :rtype: list[WeatherReport]
    """
    session = Session()
    user = session.query(User).filter(User.tg_id == tg_id).first()
    reports = user.reports
    return reports


def delete_user_report(report_id: int):
    """
    Удаляет отчёт о погоде с указанным report_id.

    Функция ищет отчёт о погоде с указанным report_id в базе данных.
    Если отчёт найден, он удаляется из базы данных и изменения сохраняются.
    Если отчёт не найден, функция не выполняет никаких действий.

    :param report_id: Идентификатор отчёта о погоде.
    :type report_id: int
    """
    session = Session()
    report = session.get(WeatherReport, report_id)
    session.delete(report)
    session.commit()


def get_all_users() -> list[Type[User]]:
    """
    Возвращает список всех зарегистрированных пользователей.

    Функция запрашивает все записи о пользователях из базы данных и возвращает их в виде списка.
    Если нет зарегистрированных пользователей, функция возвращает пустой список.

    :return: Список объектов пользователей или пустой список, если пользователи не найдены.
    :rtype: list[User]
    """
    session = Session()
    users = session.query(User).all()
    return users
