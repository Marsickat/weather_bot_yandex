# weather_bot_yandex
Telegram-бот с прогнозом погоды на основе API Яндекса

Настройка:
1) В файле /settings/api_config.py в переменную geo_key нужно добавить ключ API "JavaScript API и HTTP Геокодер"
2) В файле /settings/api_config.py в переменную weather_key нужно добавить ключ API "API Яндекс.Погоды"
3) В файле /settings/bot_config.py в переменную bot_token нужно добавить токен бота
4) В файле /settings/bot_config.py в список tg_bot_admin можете добавить ID пользователей Telegram для доступа к админ-панели
5) Адрес базы указывается в файле /settings/db_config.py

Админ-панель открывается отправкой боту сообщения "Администратор"
