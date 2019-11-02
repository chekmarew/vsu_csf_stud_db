"""Файл конфигураций проекта"""
from os import urandom


class Config:
    """Основной класс конфигурации"""
    DEBUG = False
    CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = 'dffgrtrw45'
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://" \
                              "vitya535:dffgrtrw43;Q@localhost/check_attendance_db"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # Autocommit
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # ??? Если не прописать, то будет Warning
    SECRET_KEY = urandom(24)
    MINIFY_PAGE = True
    SESSION_COOKIE_HTTPONLY = True


class ProductionConfig(Config):
    """Конфигурация для Production"""
    ASSETS_DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    ASSETS_DEBUG = True
