from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from datetime import timedelta


class Config:

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user:pass@localhost/db"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False # Autocommit
    SQLALCHEMY_TRACK_MODIFICATIONS = False # ??? Если не прописать, то будет Warning
    SECRET_KEY = '$_SECRET_KEY_$'

    PERMANENT_SESSION_LIFETIME = timedelta(days=3)

    DATE_TIME_FORMAT = '%d.%m.%Y %H:%M:%S'
    RESULT_FAIL_WARNING = 25

    DEBUG = True

    #API KEYS
    API_KEYS = {
        
    }

    # SERVER_NAME = '127.0.0.1:5000'

    SMS_SENDER = '+7-900-000-00-00'

    MOODLE_LINK = "https://edu.vsu.ru/course/view.php?id=%d"
    


app = Flask(__name__)
app.config.from_object(Config())
db = SQLAlchemy(app=app, session_options={'autoflush': False})
jwt = JWTManager(app)
# mail = Mail(app)
mail = None

