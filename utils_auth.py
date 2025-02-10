import socket
from datetime import datetime
import time
import re
from sqlalchemy import not_, or_, and_
from flask import url_for
from flask_login import current_user
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_mail import Message

from app_config import db, mail, Config

from password_checker import password_checker
from sms import sms_send

from model import Teacher, Person, CurriculumUnit, StudGroup, AuthCode
from model import AuthCode4ChangeEmail, AuthCode4ChangePhone
from auth_config import AuthCodeConfig

from model_history_controller import hist_save_controller


def _user_is_need_alert(person: Person):
    res = False
    for user in person.roles:
        if user.role_name == 'AdminUser':
            res = True

        if user.role_name == 'Teacher':
            q = db.session.query(CurriculumUnit).join(StudGroup).filter(StudGroup.active). \
                filter(not_(CurriculumUnit.closed)). \
                filter(or_(CurriculumUnit.teacher_id == user.id, and_(
                                CurriculumUnit.practice_teachers.any(Teacher.id == user.id), or_(
                                CurriculumUnit.allow_edit_practice_teacher_att_mark_1,
                                CurriculumUnit.allow_edit_practice_teacher_att_mark_2,
                                CurriculumUnit.allow_edit_practice_teacher_att_mark_3,
                                CurriculumUnit.allow_edit_practice_teacher_att_mark_exam,
                                CurriculumUnit.allow_edit_practice_teacher_att_mark_append_ball
                            )
                        )
                   )
                )
            res = res or (q.count() > 0)
    return res


def _email_alert_logon(user):
    # Уведомлять о входе Администраторов и преподавателей с возможностью редактирования
    if mail is not None and _user_is_need_alert(user) and user.email is not None:
        msg = Message(subject=Config.MAIL_SUBJECT,
                      recipients=[user.email])
        msg.body = "Здравствуйте, %s! %s Вы успешно зашли на сайт %s. Если это делали не Вы, то обязательно сообщите на %s" % (
            user.full_name, datetime.now().strftime(Config.DATE_TIME_FORMAT), url_for('index', _external=True), Config.MAIL_SUPPORT)
        try:
            mail.send(msg)
        except socket.error:
            pass


def auth_by_login_password(login, password):
    res = {"ok": False}
    user = db.session.query(Person).filter_by(login=login).one_or_none()
    if user is None:
        res["error"] = "Пользователя с таким учётным именем не существует"
        res["error_code"] = 404
        return res, None

    if not user.is_active:
        res["error"] = "Учётная запись отключена"
        res["error_code"] = 403
        return res, None

    if "password" in AuthCodeConfig.DEBUG_UNIVERSAL_PASSWORD and AuthCodeConfig.DEBUG_UNIVERSAL_PASSWORD["password"] == password:
        password_result = True
    else:
        password_result = password_checker(login=login, password=password)

    if password_result is None:
        res["error"] = "Не удалось проверить пароль. Попробуйте выполнить вход позже"
        res["error_code"] = 503
        return res, None

    if not password_result:
        res["error"] = "Неверный пароль"
        res["error_code"] = 400
        return res, None

    if AuthCodeConfig.MANDATORY_AUTHENTICATION_EMAIL and (user.email is not None or user.phone is not None) and _user_is_need_alert(user):
        res["need_second_factor"] = True
        if user.email is not None:
            res['email'] = user.email
        elif user.phone is not None:
            res['phone'] = user.phone
            res['error_code'] = 400

        return res, None

    res["ok"] = True
    res["person_id"] = user.id
    return res, user


def _check_exists_auth_code(identity_name, identity_value):
    return (db.session.query(AuthCode).filter_by(**{identity_name: identity_value}) \
            .filter(AuthCode.send_time >= datetime.now() - AuthCodeConfig.SEND_CODE_INTERVAL) \
            .filter(AuthCode.auth_time.is_(None)).count() > 0)


def send_code_email(email, second_factor=False):
    res = {"ok": False}
    user = db.session.query(Person).filter_by(email=email).one_or_none()
    if user is None:
        res["error"] = "Пользователя с таким email нет в системе"
        res["error_code"] = 404
        return res

    if not user.is_active:
        res["error"] = "Учётная запись отключена"
        res["error_code"] = 403
        return res

    if _check_exists_auth_code('email', email):
        res["error"] = "Код для входа уже был запрошен. Повторите запрос позже"
        res["error_code"] = 400
        return res
    is_send = True
    if email in AuthCodeConfig.DEBUG_UNIVERSAL_PASSWORD.get("emails", []):
        code = AuthCodeConfig.DEBUG_UNIVERSAL_PASSWORD["code"]
        if hasattr(AuthCodeConfig, "DEBUG_NOT_SEND_EMAIL"):
            is_send = not AuthCodeConfig.DEBUG_NOT_SEND_EMAIL
    else:
        code = AuthCodeConfig.generate_code()

    if is_send:
        try:
            msg = Message(subject=Config.MAIL_SUBJECT, recipients=[email])

            msg.body = "Ваш код для подтверждения входа в систему:"
            msg.body += "\r\n"
            msg.body += str(code)
            msg.body += "\r\n"
            if second_factor:
                msg.body += "Если вы не запрашивали данный код, то обязательно сообщите на %s" % Config.MAIL_SUPPORT
            else:
                msg.body += "Если вы не запрашивали данный код, то просто проигнорируйте это письмо."
            mail.send(msg)
        except socket.error:
            res["error"] = "Не удалось отправить код email. Повторите запрос позже"
            res["error_code"] = 503
            return res

    auth_code = AuthCode(email=email, code=code, send_time=datetime.now(), auth_err_count=0)
    db.session.add(auth_code)
    db.session.commit()

    res["code_timelife"] = AuthCodeConfig.SEND_CODE_TIMELIFE.total_seconds() - (datetime.now() - auth_code.send_time).total_seconds()
    res["ok"] = True
    return res


def send_code_sms(phone):
    res = {"ok": False}
    user = db.session.query(Person).filter_by(phone=phone).one_or_none()
    if user is None:
        res["error"] = "Пользователя с таким номером телефона нет в системе"
        res["error_code"] = 404
        return res
    if not user.is_active:
        res["error"] = "Учётная запись отключена"
        res["error_code"] = 403
        return res

    if _check_exists_auth_code('phone', phone):
        res["error"] = "Код для входа уже был запрошен. Повторите запрос позже"
        res["error_code"] = 400
        return res
    is_send = True
    if phone in AuthCodeConfig.DEBUG_UNIVERSAL_PASSWORD.get("phones", []):
        code = AuthCodeConfig.DEBUG_UNIVERSAL_PASSWORD["code"]
        if hasattr(AuthCodeConfig, "DEBUG_NOT_SEND_SMS"):
            is_send = not AuthCodeConfig.DEBUG_NOT_SEND_SMS
    else:
        code = AuthCodeConfig.generate_code()

    if is_send:
        send_sms_result = sms_send(number=user.phone_str, text="ВГУ ФКН БРС Код для входа в систему: %d" % code)
        if not send_sms_result:
            res["error"] = "Не удалось отправить SMS. Попробуйте повторить запрос позже"
            res["error_code"] = 503
            return res

    auth_code = AuthCode(phone=phone, code=code, send_time=datetime.now(), auth_err_count=0)
    db.session.add(auth_code)
    db.session.commit()
    res["code_timelife"] = AuthCodeConfig.SEND_CODE_TIMELIFE.total_seconds() - (datetime.now() - auth_code.send_time).total_seconds()
    res["ok"] = True
    return res


def _auth_by_code(identity_name, identity_value, code):
    res = {"ok": False}

    auth_code: AuthCode = None
    for _auth_code in db.session.query(AuthCode).filter_by(**{identity_name: identity_value}).filter(AuthCode.send_time >= datetime.now() - AuthCodeConfig.SEND_CODE_TIMELIFE, AuthCode.auth_time.is_(None)).order_by(AuthCode.id.desc()).all():
        auth_code = _auth_code
        break

    if auth_code is None:
        res["error"] = "Проверочный код не запрашивался или устарел"
        res["error_code"] = 400
        return res, None

    if auth_code.auth_err_count >= AuthCodeConfig.MAX_FAIL_CODE_COUNT:
        res["error"] = "Проверочный код был введён неверно несколько раз подряд. Попробуйте выполнить вход позже"
        res["error_code"] = 400
        return res, None

    if auth_code.code != code:
        res["error"] = "Неверный проверочный код"
        res["error_code"] = 400
        auth_code.auth_err_count += 1
        db.session.add(auth_code)
        db.session.commit()
        return res, None

    user = db.session.query(Person).filter_by(**{identity_name: identity_value}).one_or_none()
    if user is None:
        res["error"] = "Пользователя с такими учётными данными нет в системе"
        res["error_code"] = 404
        return res, None

    auth_code.auth_time = datetime.now()
    db.session.add(auth_code)
    db.session.commit()

    res["ok"] = True
    res["person_id"] = user.id

    if identity_name == "email":
        if not(hasattr(AuthCodeConfig, "DEBUG_NOT_SEND_EMAIL") and AuthCodeConfig.DEBUG_NOT_SEND_EMAIL and identity_value in AuthCodeConfig.DEBUG_UNIVERSAL_PASSWORD.get("emails", [])):
            _email_alert_logon(user)

    return res, user


def auth_by_email_code(email, code):
    return _auth_by_code('email', email, code)


def auth_by_sms_code(phone, code):
    return _auth_by_code('phone', phone, code)


def get_current_user():
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id is not None:
            user = db.session.query(Person).filter_by(id=user_id).one_or_none()
            if user is not None:
                return user if not getattr(AuthCodeConfig, "USE_ALLOW_JWT_AUTH", True) or user.allow_jwt_auth else Person()
    except:
        pass

    return current_user


def user_request_code_4_change_email(u: Person, email: str):
    res = {
        "ok": False
    }
    email = email.strip().lower()
    if len(email) > Person.email.property.columns[0].type.length or not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email):
        res['error'] = "Введён некоррекный email"
        res["error_code"] = 400
        return res

    if db.session.query(AuthCode4ChangeEmail).filter_by(person_id=u.id).filter(AuthCode4ChangeEmail.accept_time.is_(None)).filter(AuthCode4ChangeEmail.send_time >= datetime.now() - AuthCodeConfig.SEND_CODE_INTERVAL).count() > 0:
        res['error'] = "Уже был запрошен код на изменение e-mail. Повторите запрос позже."
        res["error_code"] = 400
        return res

    u_other = db.session.query(Person).filter_by(email=email).one_or_none()
    if u_other is not None:
        if u_other.id == u.id:
            res['error'] = "Вы введи свой e-mail."
        else:
            res['error'] = "E-mail уже занят другим пользователем."

        res["error_code"] = 400
        return res

    code_old = None
    if u.email:
        code_old = AuthCodeConfig.generate_code()
        try:
            msg = Message(subject=Config.MAIL_SUBJECT, recipients=[u.email])

            msg.body = "Был произведён запрос на изменение Вашего e-mail с на %s на %s" % (u.email, email)
            msg.body += "\r\n"
            msg.body = "Код для подтверждения старого e-mail:"
            msg.body += "\r\n"
            msg.body += str(code_old)
            msg.body += "\r\n"

            msg.body += "Если вы не делали данный запрос, то обязательно сообщите на %s" % Config.MAIL_SUPPORT

            mail.send(msg)
        except socket.error:
            res["error"] = "Не удалось отправить код email %s. Повторите запрос позже" % u.email
            res["error_code"] = 503
            return res

    code = AuthCodeConfig.generate_code()
    try:
        msg = Message(subject=Config.MAIL_SUBJECT, recipients=[email])

        msg.body = "Код для подтверждения e-mail:"
        msg.body += "\r\n"
        msg.body += str(code)

        mail.send(msg)
    except socket.error:
        res["error"] = "Не удалось отправить код email %s. Повторите запрос позже" % email
        res["error_code"] = 503
        return res

    a_code = AuthCode4ChangeEmail(person_id=u.id, email_old=u.email, email=email, code_old=code_old, code=code, send_time=datetime.now(), auth_err_count=0)
    db.session.add(a_code)
    db.session.commit()

    res["code_timelife"] = AuthCodeConfig.SEND_CODE_TIMELIFE.total_seconds() - (datetime.now() - a_code.send_time).total_seconds()
    res["ok"] = True

    return res


def user_request_code_4_change_phone(u: Person, phone: int):
    res = {
        "ok": False
    }

    if phone < 79000000000 or phone > 79999999999:
        res['error'] = "Введён некоррекный номер телефона"
        res["error_code"] = 400
        return res

    if db.session.query(AuthCode4ChangePhone).filter_by(person_id=u.id).filter(AuthCode4ChangePhone.accept_time.is_(None)).filter(AuthCode4ChangePhone.send_time >= datetime.now() - AuthCodeConfig.SEND_CODE_INTERVAL).count() > 0:
        res['error'] = "Уже был запрошен код на изменение номера телефона. Повторите запрос позже."
        res["error_code"] = 400
        return res

    u_other = db.session.query(Person).filter_by(phone=phone).one_or_none()
    if u_other is not None:
        if u_other.id == u.id:
            res['error'] = "Вы введи свой номер телефона."
        else:
            res['error'] = "Номер телефона уже занят другим пользователем."

        res["error_code"] = 400
        return res

    phone_str = "+%d" % phone

    code_old = None
    if u.phone:
        code_old = AuthCodeConfig.generate_code()
        send_sms_result = sms_send(number=u.phone_str, text="ВГУ ФКН БРС Поступил запрос: изменение телефона на %s. Код для подтверждения старого номера телефона: %d" % (phone_str, code_old))
        if not send_sms_result:
            res["error"] = "Не удалось отправить код на телефон %s. Повторите запрос позже." % u.phone_str
            res["error_code"] = 503
            return res
        time.sleep(4)

    code = AuthCodeConfig.generate_code()
    send_sms_result = sms_send(number=phone_str, text="ВГУ ФКН БРС Код для подтверждения номера телефона: %d" % code)
    if not send_sms_result:
        res["error"] = "Не удалось отправить код на телефон %s. Повторите запрос позже." % phone_str
        res["error_code"] = 503
        return res

    a_code = AuthCode4ChangePhone(person_id=u.id, phone_old=u.phone, phone=phone, code_old=code_old, code=code, send_time=datetime.now(), auth_err_count=0)
    db.session.add(a_code)
    db.session.commit()

    res["code_timelife"] = AuthCodeConfig.SEND_CODE_TIMELIFE.total_seconds() - (datetime.now() - a_code.send_time).total_seconds()
    res["ok"] = True

    return res


def _user_accept_code_4_change(type_code, u: Person, code, code_old=None):
    res = {
        "ok": False
    }

    a_code = None
    type_class = None
    if type_code == "email":
        type_class = AuthCode4ChangeEmail
    if type_code == "phone":
        type_class = AuthCode4ChangePhone

    if type_class is not None:
        for _a_code in db.session.query(type_class).filter_by(person_id=u.id).filter(type_class.send_time >= datetime.now() - AuthCodeConfig.SEND_CODE_TIMELIFE, type_class.accept_time.is_(None)).order_by(type_class.id.desc()).all():
            a_code = _a_code
            break

    if a_code is None:
        res["error"] = "Проверочный код не запрашивался или устарел"
        res["error_code"] = 400
        return res

    if a_code.auth_err_count >= AuthCodeConfig.MAX_FAIL_CODE_COUNT:
        res["error"] = "Проверочный код был введён неверно несколько раз подряд. Попробуйте повторить запрос позже"
        res["error_code"] = 400
        return res

    if a_code.code != code:
        if type_code == "email":
            res["error"] = "Неверный проверочный код для подтверждения e-mail"
        if type_code == "phone":
            res["error"] = "Неверный проверочный код для подтверждения номера телефона"

        res["error_code"] = 400
        a_code.auth_err_count += 1
        db.session.add(a_code)
        db.session.commit()
        res["code_incorrect"] = True
        return res

    if a_code.code_old is not None and (code_old is None or a_code.code_old != code_old):
        if type_code == "email":
            res["error"] = "Неверный проверочный код для подтверждения старого e-mail"
        if type_code == "phone":
            res["error"] = "Неверный проверочный код для подтверждения старого номера телефона"
        res["error_code"] = 400
        a_code.auth_err_count += 1
        db.session.add(a_code)
        db.session.commit()
        res["code_incorrect"] = True
        return res

    a_code.accept_time = datetime.now()
    db.session.add(a_code)
    if type_code == "email":
        u.email = a_code.email
    if type_code == "phone":
        u.phone = a_code.phone
    db.session.add(u)
    hist_save_controller(db.session, u, u)
    db.session.commit()
    res["ok"] = True
    return res


def user_accept_code_4_change_email(u: Person, code, code_old=None):
    return _user_accept_code_4_change("email", u, code, code_old)


def user_accept_code_4_change_phone(u: Person, code, code_old=None):
    return _user_accept_code_4_change("phone", u, code, code_old)
