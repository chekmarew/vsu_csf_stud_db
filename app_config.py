import os

import flask_excel as excel
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_user import LoginManager


class Config:
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://<user>:<password>@<host>/<db_name>?auth_plugin=mysql_native_password"
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://vitya535:dffgrtrw43;Q@localhost/check_attendance_db"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # Autocommit
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # ??? Если не прописать, то будет Warning

    USER_ENABLE_EMAIL = False
    USER_ENABLE_REMEMBER_ME = False

    # Flask-User settings
    USER_APP_NAME = "CheckAttendance"  # Used by email templates


app = Flask(__name__)
app.config.from_object(Config())
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
excel.init_excel(app)
