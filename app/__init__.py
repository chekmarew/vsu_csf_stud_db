"""Инициализация приложения и его частей"""
import flask_excel as excel
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wkhtmltopdf import Wkhtmltopdf

# ToDo - поправить excel и pdf печать

# ToDo - в pdf печати решить вопрос с encoding-ом файла (кириллица)
# ToDo - в excel сделать так,
#  чтобы HTML-таблица преобразовывалась в необходимую структуру данных и потом выводилась в Excel

# ToDo - настроить авторизацию и регистрацию
# ToDo - сделать посещаемость (чтоб все было через базу)

# ToDo - добавить тестовые данные для своих таблиц
# ToDo - статистика по студентам (по %, по пропускам, посещениям)
# ToDo - Экспорт, импорт pdf, Excel
# ToDo - авторизация, регистрация? (роли: студент, преподаватель, староста???)
# ToDo - настройка баллов по посещаемости???
# ToDo - отметка праздничных неучебных дней???

# ToDo - при регистрации задать еще роль бы как-то...

# ToDo - отображение посещаемости за день/неделю/месяц
# ToDo - Разобраться со считываетелем кодов


APP = Flask(__name__)

if APP.config['ENV'] == 'production':
    APP.config.from_object('app.config.ProductionConfig')
else:
    APP.config.from_object('app.config.DevelopmentConfig')

DB = SQLAlchemy(APP)
excel.init_excel(APP)
WKHTMLTOPDF = Wkhtmltopdf(APP)

from app import views
