import socket
from datetime import datetime
from sqlalchemy import not_, or_, and_
from flask import url_for
from flask_login import current_user
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_mail import Message

from app_config import db, mail, Config

from password_checker import password_checker
from sms import sms_send


from model import Teacher, Person, CurriculumUnit, StudGroup, AuthCode
from auth_config import AuthCodeConfig


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
