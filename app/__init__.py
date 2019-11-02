"""Инициализация приложения и его частей"""
import flask_excel as excel
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

APP = Flask(__name__)

if APP.config['ENV'] == 'production':
    APP.config.from_object('app.config.ProductionConfig')
else:
    APP.config.from_object('app.config.DevelopmentConfig')

DB = SQLAlchemy(APP)
LOGIN_MANAGER = LoginManager(APP)
LOGIN_MANAGER.login_view = 'login'
excel.init_excel(APP)

from app import views
