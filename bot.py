import math

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from api_requests import request
from database import orm
from settings import bot_config

bot = Bot(token=bot_config.bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class ChoiceCityWeather(StatesGroup):
    waiting_city = State()


class SetUserCity(StatesGroup):
    waiting_user_city = State()


@dp.message_handler(commands=["start"])
async def start_message(message: types.Message):
    """
    Обработчик команды "/start"

    При вызове функции, она добавляет ID пользователя в базу данных, создаёт и отправляет пользователю клавиатуру
    с опциями и выводит приветственное сообщение.

    :param message: Объект, содержащий информацию о сообщении пользователя.
    :type message: types.Message
    """
    # Добавление идентификатора в базу данных
    orm.add_user(message.from_user.id)

    # Создание клавиатуры с опциями
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton("Погода в моём городе")
    btn2 = types.KeyboardButton("Погода в другом месте")
    btn3 = types.KeyboardButton("История")
    btn4 = types.KeyboardButton("Установить свой город")
    markup.add(btn1, btn2, btn3, btn4)

    # Формирование и отправка приветственного сообщения с клавиатурой пользователю
    text = f"Привет {message.from_user.first_name}, я бот, который расскажет тебе о погоде на сегодня"
    await message.answer(text, reply_markup=markup)


@dp.message_handler(regexp="Меню")
async def start_message(message: types.Message):
    """
    Обработчик команды "Меню"

    При вызове функции, она создаёт и отправляет пользователю клавиатуру с опциями и выводит приветственное сообщение

    :param message: Объект, содержащий информацию о сообщении пользователя.
    :type message: types.Message
    """
    # Создание клавиатуры с опциями
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton("Погода в моём городе")
    btn2 = types.KeyboardButton("Погода в другом месте")
    btn3 = types.KeyboardButton("История")
    btn4 = types.KeyboardButton("Установить свой город")
    markup.add(btn1, btn2, btn3, btn4)

    # Формирование и отправка приветственного сообщения с клавиатурой пользователю
    text = f"Привет {message.from_user.first_name}, я бот, который расскажет тебе о погоде на сегодня"
    await message.answer(text, reply_markup=markup)


@dp.message_handler(regexp="Погода в моём городе")
async def get_user_city_weather(message: types.Message):
    """
    Обработчик команды "Погода в моём городе"

    При вызове функции, она получает город проживания пользователя из базы данных.
    Если город не установлен, отправляет пользователю предложение установить его.
    Иначе, получает данные о погоде для данного города с помощью функции get_weather.
    Создаёт отчёт о погоде и отправляет его пользователю.

    :param message: Объект, содержащий информацию о сообщении пользователя.
    :type message: types.Message
    """
    # Создание клавиатуры "Меню" для возврата обратно
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Меню")
    markup.add(btn1)

    # Получение города пользователя из базы данных
    city = orm.get_user_city(message.from_user.id)

    # Если город не установлен, предложить пользователю установить его
    if city is None:
        text = "Пожалуйста, установите город проживания"
        markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton("Установить свой город")
        markup.add(btn1)
        await message.answer(text, reply_markup=markup)
        return

    # Получение данных о погоде для данного города
    data = request.get_weather(city)

    # Создание отчёта о погоде и сохранение его в базе данных
    orm.create_report(message.from_user.id, data["temp"], data["feels_like"], data["wind_speed"], data["pressure_mm"],
                      city)

    # Формирование и отправка приветственного сообщения с клавиатурой пользователю
    text = f"Погода в {city}\nТемпература: {data['temp']} C\nОщущается как: {data['feels_like']} C\nСкорость ветра: {data['wind_speed']} м/с\nДавление: {data['pressure_mm']} мм"
    await message.answer(text, reply_markup=markup)


@dp.message_handler(regexp="Погода в другом месте")
async def city_start(message: types.Message):
    """
    Обработчик команды "Погода в другом месте"

    При вызове функции, она создаёт клавиатуру "Меню" для возврата обратно,
    отправляет пользователю запрос на ввод названия города и переводит пользователя
    в состояние ожидания ввода названия города (ChoiceCityWeather).

    :param message: Объект, содержащий информацию о сообщении пользователя.
    :type message: types.Message
    """
    # Создание клавиатуры "Меню" для возврата обратно
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Меню")
    markup.add(btn1)

    # Отправка запроса на ввод названия города пользователю с клавиатурой "Меню"
    text = "Введите название города"
    await message.answer(text, reply_markup=markup)

    # Переход пользователя в состояние ожидания ввода названия города
    await ChoiceCityWeather.waiting_city.set()


@dp.message_handler(state=ChoiceCityWeather.waiting_city)
async def city_chosen(message: types.Message, state: FSMContext):
    """
    Обработчик ввода названия города пользователем для выбора погоды в другом месте.

    При вызове функции, она проверяет правильность ввода названия города.
    Если название города написано с маленькой буквы, отправляет сообщение об ошибке.
    Иначе, обновляет данные состояния (FSMContext) с введённым названием города.
    Получает данные о погоде и отправляет его пользователю.
    Завершает состояние и переводит пользователя в исходное состояние.

    :param message: Объект, содержащий информацию о сообщении пользователя.
    :type message: types.Message
    :param state: Объект состояния для управления текущим состоянием разговора с пользователем.
    :type state: FSMContext
    """
    # Проверка, написано ли название города с большой буквы
    if message.text[0].islower():
        await message.answer("Названия городов пишутся с большой буквы )")
        return

    # Обновление данных состояния с введённым названием города
    await state.update_data(waiting_city=message.text)

    # Создание клавиатуры "Меню" для возврата обратно
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton("Погода в моём городе")
    btn2 = types.KeyboardButton("Погода в другом месте")
    btn3 = types.KeyboardButton("История")
    btn4 = types.KeyboardButton("Установить свой город")
    markup.add(btn1, btn2, btn3, btn4)

    # Получение данных о погоде для данного города
    city = await state.get_data()
    data = request.get_weather(city.get("waiting_city"))

    # Создание отчёта о погоде и сохранение его в базе данных
    orm.create_report(message.from_user.id, data["temp"], data["feels_like"], data["wind_speed"], data["pressure_mm"],
                      city.get("waiting_city"))

    # Формирование и отправка сообщения с данными о погоде пользователю
    text = f"Погода в {city.get('waiting_city')}\nТемпература: {data['temp']} C\nОщущается как: {data['feels_like']} C\nСкорость ветра: {data['wind_speed']} м/с\nДавление: {data['pressure_mm']} мм"
    await message.answer(text, reply_markup=markup)

    # Завершение состояния и переход пользователя в исходное состояние
    await state.finish()


@dp.message_handler(regexp="Установить свой город")
async def set_user_city_start(message: types.Message):
    """
    Обработчик команды "Установить свой город"

    При вызове функции, она создаёт клавиатуру "Меню" для возврата обратно,
    отправляет пользователю запрос на ввод города проживания и переводит пользователя
    в состояние ожидания ввода города (SetUserCity)

    :param message: Объект, содержащий информацию о сообщении пользователя.
    :type message: types.Message
    """
    # Создание клавиатуры "Меню" для возврата обратно
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Меню")
    markup.add(btn1)

    # Отправка запроса на ввод названия города пользователю с клавиатурой "Меню"
    text = "В каком городе проживаете?"
    await message.answer(text, reply_markup=markup)

    # Переход пользователя в состояние ожидания ввода названия города
    await SetUserCity.waiting_user_city.set()


@dp.message_handler(state=SetUserCity.waiting_user_city)
async def user_city_chosen(message: types.Message, state: FSMContext):
    """
    Обработчик ввода города проживания пользователем для установки своего города.

    При вызове функции, она проверяет правильность ввода названия города.
    Если название города написано с маленькой буквы, отправляет сообщение об ошибке.
    Иначе, обновляет данные состояния (FSMContext) с введённым названием города.
    Записывает в базу данных город проживания пользователя.
    Создаёт клавиатуру "Меню" для возврата обратно и отправляет сообщение об успешной установке города.
    Завершает состояние и переводит пользователя в исходное состояние.

    :param message: Объект, содержащий информацию о сообщении пользователя.
    :type message: types.Message
    :param state: Объект состояния для управления текущим состоянием разговора с пользователем.
    :type state: FSMContext
    """
    # Проверка, написано ли название города с большой буквы
    if message.text[0].islower():
        await message.answer("Названия городов пишутся с большой буквы )")
        return

    # Обновление данных состояния с введённым названием города
    await state.update_data(waiting_user_city=message.text)

    # Получение данных о городе проживания пользователя
    user_data = await state.get_data()

    # Запись города проживания пользователя в базу данных
    orm.set_user_city(message.from_user.id, user_data.get("waiting_user_city"))

    # Создание клавиатуры "Меню" для возврата обратно
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton("Погода в моём городе")
    btn2 = types.KeyboardButton("Погода в другом месте")
    btn3 = types.KeyboardButton("История")
    btn4 = types.KeyboardButton("Установить свой город")
    markup.add(btn1, btn2, btn3, btn4)

    # Формирование и отправка сообщения об успешной установке города пользователю
    text = f"Запомнил, {user_data.get('waiting_user_city')} - ваш город"
    await message.answer(text, reply_markup=markup)

    # Завершение состояния и переход пользователя в исходное состояние
    await state.finish()


@dp.message_handler(regexp="История")
async def get_reports(message: types.Message):
    """
    Обработчик команды "История"

    При вызове функции, она получает список отчётов пользователя из базы данных.
    Рассчитывает общее количество страниц и отображает историю запросов с кнопками навигации.
    Каждый отчёт отображается с датой запроса и городом.
    При нажатии на кнопку с отчётом пользователем, срабатывает соответствующий callback.

    :param message: Объект, содержащий информацию о сообщении пользователя.
    :type message: types.Message
    """
    current_page = 1

    # Получение списка отчётов пользователя из базы данных и расчёт общего количества страниц
    reports = orm.get_reports(message.from_user.id)
    total_pages = math.ceil(len(reports) / 4)

    # Формирование текста сообщения и создание встроенной клавиатуры для кнопок с отчётами
    text = "История запросов:"
    inline_markup = types.InlineKeyboardMarkup()

    # Отображение первых 4 отчётов на текущей странице
    for report in reports[:current_page * 4]:
        # Создание кнопки для каждого отчёта с названием города и датой запроса
        inline_markup.add(types.InlineKeyboardButton(
            text=f"{report.city} {report.date.day}.{report.date.month}.{report.date.year}",
            callback_data=f"report_{report.id}"
        ))

    current_page += 1

    # Добавление кнопок навигации: "<текущая страница>/<общее количество страниц>" и "Вперёд"
    inline_markup.row(
        types.InlineKeyboardButton(text=f"{current_page - 1}/{total_pages}", callback_data="None"),
        types.InlineKeyboardButton(text="Вперёд", callback_data=f"next_{current_page}")
    )

    # Отправка сообщения с историей запросов пользователю с встроенной клавиатурой
    await message.answer(text, reply_markup=inline_markup)


@dp.callback_query_handler(lambda call: "users" not in call.data)
async def callback_query(call: types.CallbackQuery, state: FSMContext):
    """
    Обработчик callback-запросов для управления историей запросов пользователя.

    При вызове функции, она обрабатывает различные типы callback-запросов,
    такие, как "delete_report", "next", "prev", "report" и "reports".

    :param call: Объект, содержащий информацию о callback-запросе от пользователя.
    :type call: types.CallbackQuery
    :param state: Объект состояния для управления текущим состоянием разговора с пользователем.
    :type state: FSMContext
    """
    # Чтение типа запроса из данных обратного вызова
    query_type = call.data.split("_")[0]

    if query_type == "delete" and call.data.split("_")[1] == "report":
        # Удаление отчёта по его идентификатору
        report_id = int(call.data.split("_")[2])
        orm.delete_user_report(report_id)

        current_page = 1

        # Получение списка отчётов пользователя после удаления и расчёт общего количества страниц
        reports = orm.get_reports(call.from_user.id)
        total_pages = math.ceil(len(reports) / 4)

        # Создание встроенной клавиатуры для кнопок с отчётами
        inline_markup = types.InlineKeyboardMarkup()

        # Отображение первых 4 отчётов на текущей странице
        for report in reports[:current_page * 4]:
            inline_markup.add(types.InlineKeyboardButton(
                text=f"{report.city} {report.date.day}.{report.date.month}.{report.date.year}",
                callback_data=f"report_{report.id}"
            ))

        current_page += 1

        # Добавление кнопок навигации: "<текущая страница>/<общее количество страниц>" и "Вперёд"
        inline_markup.row(
            types.InlineKeyboardButton(text=f"{current_page - 1}/{total_pages}", callback_data="None"),
            types.InlineKeyboardButton(text="Вперёд", callback_data=f"next_{current_page}")
        )

        # Обновление сообщения с историей запросов после удаления отчёта
        await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
        return

    # Если тип запроса "next" или "prev", обрабатываем навигацию по страницам с отчётами
    async with state.proxy() as data:
        data["current_page"] = int(call.data.split("_")[1])
        await state.update_data(current_page=data["current_page"])

        if query_type == "next":
            # Обработка перехода к следующей странице
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()

            # Если текущая страница содержит меньше 4 отчётов, добавляем только имеющиеся
            if data["current_page"] * 4 >= len(reports):
                for report in reports[data["current_page"] * 4 - 4:len(reports) + 1]:
                    inline_markup.add(types.InlineKeyboardButton(
                        text=f"{report.city} {report.date.day}.{report.date.month}.{report.date.year}",
                        callback_data=f"report_{report.id}"
                    ))

                data["current_page"] -= 1

                # Добавление кнопок навигации: "Назад" и "<текущая страница>/<общее количество страниц>"
                inline_markup.row(
                    types.InlineKeyboardButton(text="Назад", callback_data=f"prev_{data['current_page']}"),
                    types.InlineKeyboardButton(text=f"{data['current_page'] + 1}/{total_pages}", callback_data="None")
                )

                # Обновление сообщения с историей запросов при переходе к следующей странице
                await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
                return

            for report in reports[data["current_page"] * 4 - 4:data["current_page"] * 4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f"{report.city} {report.date.day}.{report.date.month}.{report.date.year}",
                    callback_data=f"report_{report.id}"
                ))

            data["current_page"] += 1

            # Добавление кнопок навигации: "Назад", "<текущая страница>/<общее количество страниц>" и "Вперёд"
            inline_markup.row(
                types.InlineKeyboardButton(text="Назад", callback_data=f"prev_{data['current_page'] - 2}"),
                types.InlineKeyboardButton(text=f"{data['current_page'] + 1}/{total_pages}", callback_data="None"),
                types.InlineKeyboardButton(text="Вперёд", callback_data=f"next_{data['current_page']}")
            )

            # Обновление сообщения с историей запросов при переходе к следующей странице
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)

        if query_type == "prev":
            # Обработка перехода к предыдущей странице
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()

            if data["current_page"] == 1:
                for report in reports[0:data["current_page"] * 4]:
                    inline_markup.add(types.InlineKeyboardButton(
                        text=f"{report.city} {report.date.day}.{report.date.month}.{report.date.year}",
                        callback_data=f"report_{report.id}"
                    ))

                data["current_page"] += 1

                # Добавление кнопок навигации: "<текущая страница>/<общее количество страниц>" и "Вперёд"
                inline_markup.row(
                    types.InlineKeyboardButton(text=f"{data['current_page'] - 1}/{total_pages}", callback_data="None"),
                    types.InlineKeyboardButton(text="Вперёд", callback_data=f"next_{data['current_page']}")
                )

                # Обновление сообщения с историей запросов при переходе к предыдущей странице
                await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
                return

            for report in reports[data["current_page"] * 4 - 4:data["current_page"] * 4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f"{report.city} {report.date.day}.{report.date.month}.{report.date.year}",
                    callback_data=f"report_{report.id}"
                ))

            data["current_page"] -= 1

            # Добавление кнопок навигации: "Назад", "<текущая страница>/<общее количество страниц>" и "Вперёд"
            inline_markup.row(
                types.InlineKeyboardButton(text="Назад", callback_data=f"prev_{data['current_page'] - 2}"),
                types.InlineKeyboardButton(text=f"{data['current_page'] + 1}/{total_pages}", callback_data="None"),
                types.InlineKeyboardButton(text="Вперёд", callback_data=f"next_{data['current_page']}")
            )

            # Обновление сообщения с историей запросов при переходе к предыдущей странице
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)

        if query_type == "report":
            # Обработка запроса для показа подробностей отдельного отчёта
            reports = orm.get_reports(call.from_user.id)
            report_id = call.data.split("_")[1]
            inline_markup = types.InlineKeyboardMarkup()

            for report in reports:
                if report.id == int(report_id):
                    # Создание встроенной клавиатуры для кнопок "Назад" и "Удалить запрос"
                    inline_markup.add(
                        types.InlineKeyboardButton(text="Назад", callback_data=f"reports_{data['current_page']}"),
                        types.InlineKeyboardButton(text="Удалить запрос", callback_data=f"delete_report_{report_id}")
                    )

                    # Отправка сообщения с подробностями отчёта
                    await call.message.edit_text(
                        text=f"Данные по запросу\nГород: {report.city}\nТемпература: {report.temp}\nОщущается как: {report.feels_like}\nСкорость ветра: {report.wind_speed}\nДавление: {report.pressure_mm}",
                        reply_markup=inline_markup)
                    break

        if query_type == "reports":
            # Обработка запроса для показа первой страницы с отчётами
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            data["current_page"] = 1

            # Отображение первых 4 отчётов на текущей странице
            for report in reports[:data["current_page"] * 4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f"{report.city} {report.date.day}.{report.date.month}.{report.date.year}",
                    callback_data=f"report_{report.id}"
                ))

            data["current_page"] += 1

            # Добавление кнопок навигации: "<текущая страница>/<общее количество страниц>" и "Вперёд"
            inline_markup.row(
                types.InlineKeyboardButton(text=f"{data['current_page'] - 1}/{total_pages}", callback_data="None"),
                types.InlineKeyboardButton(text="Вперёд", callback_data=f"next_{data['current_page']}")
            )

            # Обновление сообщения с историей запросов при переходе к первой странице
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)


@dp.message_handler(lambda message: message.from_user.id in bot_config.tg_bot_admin and message.text == "Администратор")
async def admin_panel(message: types.Message):
    """
    Обработчик команды "Администратор"

    При вызове функции, она проверяет, является ли пользователь администратором,
    сравнивая его идентификатор с идентификаторами администраторов, указанными в конфигурационном файле.
    Если пользователь является администратором, то открывается административная панель с кнопкой "Список пользователей".

    :param message: Объект, содержащий информацию о сообщении от пользователя.
    :type message: types.Message
    """
    # Создание клавиатуры с кнопкой "Список пользователей"
    markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Список пользователей")
    markup.add(btn1)

    # Отправка сообщения с административной панелью и кнопкой "Список пользователей"
    text = "Админ-панель"
    await message.answer(text, reply_markup=markup)


@dp.message_handler(
    lambda message: message.from_user.id in bot_config.tg_bot_admin and message.text == "Список пользователей")
async def admin_panel(message: types.Message):
    """
    Обработчик команды "Список пользователей"

    При вызове функции, она проверяет, является ли пользователь администратором,
    сравнивая его идентификатор с идентификаторами администраторов, указанными в конфигурационном файле.
    Если пользователь является администратором, то отображается список всех пользователей с информацией о каждом из них.

    :param message: Объект, содержащий информацию о сообщении от пользователя.
    :type message: types.Message
    """
    # Получение списка всех пользователей из базы данных
    users = orm.get_all_users()

    # Расчёт общего количества страниц
    current_page = 1
    total_pages = math.ceil(len(users) / 4)

    # Формирование текста сообщения и создание встроенной клавиатуры для кнопок с пользователями
    text = "Все пользователи:"
    inline_markup = types.InlineKeyboardMarkup()

    # Отображение первых 4 пользователей на текущей странице
    for user in users[:current_page * 4]:
        inline_markup.add(types.InlineKeyboardButton(
            text=f"{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}",
            callback_data="None"
        ))

    current_page += 1

    # Добавление кнопок навигации: "<текущая страница>/<общее количество страниц>" и "Вперёд"
    inline_markup.row(
        types.InlineKeyboardButton(text=f"{current_page - 1}/{total_pages}", callback_data="None"),
        types.InlineKeyboardButton(text="Вперёд", callback_data=f"next_users_{current_page}")
    )

    # Отправка сообщения со списком всех пользователей и клавиатурой с кнопками навигации
    await message.answer(text, reply_markup=inline_markup)


@dp.callback_query_handler(lambda call: "users" in call.data)
async def callback_query(call: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для обработки встроенных кнопок в административной панели "Список пользователей".

    При вызове функции обрабатывается запрос пользователя через встроенные кнопки.
    Функция позволяет администратору просматривать список всех пользователей с информацией о каждом пользователе.
    Администратор может использовать кнопки "Вперёд" и "Назад" для перехода по страницам с пользователями.

    :param call: Объект, содержащий информацию о запросе пользователя через встроенные кнопки.
    :type call: types.CallbackQuery
    :param state: Объект, представляющий состояние конечного автомата, используемый в боте.
    :type state: FSMContext
    """
    # Чтение типа запроса из данных обратного вызова
    query_type = call.data.split("_")[0]

    # Получение текущей страницы из хранилища состояний
    async with state.proxy() as data:
        data["current_page"] = int(call.data.split("_")[2])
        await state.update_data(current_page=data["current_page"])

        # Определение действия в зависимости от типа запроса
        if query_type == "next":
            users = orm.get_all_users()
            total_pages = math.ceil(len(users) / 4)
            inline_markup = types.InlineKeyboardMarkup()

            # Если текущая страница слишком большая, чтобы отобразить пользователей, показываем последних
            if data["current_page"] * 4 >= len(users):
                for user in users[data["current_page"] * 4 - 4:len(users) + 1]:
                    inline_markup.add(types.InlineKeyboardButton(
                        text=f"{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}",
                        callback_data="None"
                    ))
                data["current_page"] -= 1
                inline_markup.row(
                    types.InlineKeyboardButton(text="Назад", callback_data=f"prev_users_{data['current_page']}"),
                    types.InlineKeyboardButton(text=f"{data['current_page'] + 1}/{total_pages}", callback_data="None")
                )
                await call.message.edit_text(text="Все пользователи:", reply_markup=inline_markup)
                return

            # Выводим пользователей на текущей странице
            for user in users[data["current_page"] * 4 - 4:data["current_page"] * 4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f"{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}",
                    callback_data="None"
                ))

            data["current_page"] += 1

            # Добавление кнопок навигации: "Назад", "<текущая страница>/<общее количество страниц>" и "Вперёд"
            inline_markup.row(
                types.InlineKeyboardButton(text="Назад", callback_data=f"prev_users_{data['current_page'] - 2}"),
                types.InlineKeyboardButton(text=f"{data['current_page'] - 1}/{total_pages}", callback_data="None"),
                types.InlineKeyboardButton(text=f"Вперёд", callback_data=f"next_users_{data['current_page']}")
            )

            # Отправка сообщения со списком всех пользователей и клавиатурой с кнопками навигации
            await call.message.edit_text(text="Все пользователи:", reply_markup=inline_markup)

        if query_type == "prev":
            users = orm.get_all_users()
            total_pages = math.ceil(len(users) / 4)
            inline_markup = types.InlineKeyboardMarkup()

            # Если текущая страница - первая, показываем первых пользователей
            if data["current_page"] == 1:
                for user in users[0:data["current_page"] * 4]:
                    inline_markup.add(types.InlineKeyboardButton(
                        text=f"{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}",
                        callback_data="None"
                    ))
                data["current_page"] += 1
                inline_markup.row(
                    types.InlineKeyboardButton(text=f"{data['current_page'] - 1}/{total_pages}", callback_data="None"),
                    types.InlineKeyboardButton(text="Вперёд", callback_data=f"next_users_{data['current_page']}")
                )
                await call.message.edit_text(text="Все пользователи:", reply_markup=inline_markup)
                return

            # Выводим пользователей на текущей странице
            for user in users[data["current_page"] * 4 - 4:data["current_page"] * 4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f"{user.id}) id: {user.tg_id} Подключился: {user.connection_date.day}.{user.connection_date.month}.{user.connection_date.year} Отчётов: {len(user.reports)}",
                    callback_data="None"
                ))

            data["current_page"] -= 1

            # Добавление кнопок навигации: "Назад", "<текущая страница>/<общее количество страниц>" и "Вперёд"
            inline_markup.row(
                types.InlineKeyboardButton(text="Назад", callback_data=f"prev_users_{data['current_page']}"),
                types.InlineKeyboardButton(text=f"{data['current_page'] + 1}/{total_pages}", callback_data="None"),
                types.InlineKeyboardButton(text=f"Вперёд", callback_data=f"next_users_{data['current_page']}")
            )

            # Отправка сообщения со списком всех пользователей и клавиатурой с кнопками навигации
            await call.message.edit_text(text="Все пользователи:", reply_markup=inline_markup)


# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
