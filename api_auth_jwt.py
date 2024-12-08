from flask import request, jsonify, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

from app_config import app
from auth_config import AuthCodeConfig
import utils_auth
import re


def _add_auth_url(user, res_auth):
    if getattr(AuthCodeConfig, "USE_ALLOW_JWT_AUTH", True) and not user.allow_jwt_auth:
        res_auth['auth_url'] = url_for('login_jwt', jwt=res_auth['access_token'], next=url_for('profile', id=user.id), _external=True)
        # Костыль из-за proxy
        if "JWT_AUTH_HOST_URL" in app.config and app.config["JWT_AUTH_HOST_URL"] != request.host_url :
            res_auth['auth_url'] = res_auth['auth_url'][len(request.host_url):]
            res_auth['auth_url'] = app.config["JWT_AUTH_HOST_URL"] + res_auth['auth_url']

    return res_auth

@app.route('/api/auth_jwt/refresh', methods=["POST"])
@jwt_required(refresh=True)
def api_auth_jwt_refresh():
    person_id = get_jwt_identity()
    return {
        "ok": True,
        "access_token": create_access_token(identity=person_id),
        "refresh_token": create_refresh_token(identity=person_id),
    }


@app.route('/api/auth_jwt/login', methods=["POST"])
def api_auth_jwt_login():
    data = request.get_json()

    if 'username' not in data or 'password' not in data or not isinstance(data['username'], str) or not isinstance(data['password'], str):
        return jsonify({
            "ok": False,
            "error": "Не указаны параметры 'username' и 'password' или они не строка"
        }), 400

    username = data['username'].lower()
    password = data['password']

    res_auth, user = utils_auth.auth_by_login_password(username, password)
    if res_auth["ok"] and res_auth["person_id"]:
        res_auth['access_token'] = create_access_token(identity=res_auth["person_id"])
        res_auth['refresh_token'] = create_refresh_token(identity=res_auth["person_id"])
        res_auth = _add_auth_url(user, res_auth)

    http_code = res_auth.pop("error_code", 200)
    return jsonify(res_auth), http_code


@app.route('/api/auth_jwt/send_code_email', methods=["POST"])
def api_auth_jwt_send_code_email():
    data = request.get_json()
    if 'email' not in data or not isinstance(data['email'], str):
        return jsonify({
            "ok": False,
            "error": "Не указан параметр 'email' или тип не строка"
        }), 400
    email = data['email'].lower()
    if not re.match(r'^([a-z0-9]+[.-_])*[a-z0-9]+@[a-z0-9-]+(\.[a-z]{2,})+$', email):
        return jsonify({
            "ok": False,
            "error": "Некорректный email"
        }), 400

    res_auth = utils_auth.send_code_email(email=email)
    http_code = res_auth.pop("error_code", 200)
    return jsonify(res_auth), http_code


@app.route('/api/auth_jwt/send_code_sms', methods=["POST"])
def api_auth_jwt_send_code_sms():
    data = request.get_json()
    if 'phone' not in data:
        return jsonify({
            "ok": False,
            "error": "Не указан параметр 'phone'"
        }), 400

    phone = data['phone']
    if not isinstance(phone, int) or phone < 79000000000 or phone > 79999999999:
        return jsonify({
            "ok": False,
            "error": "'phone' должен быть целым числом от 79000000000 до 79999999999"
        }), 400
    res_auth = utils_auth.send_code_sms(phone=phone)
    http_code = res_auth.pop("error_code", 200)
    return jsonify(res_auth), http_code


@app.route('/api/auth_jwt/email_code', methods=["POST"])
def api_auth_jwt_email_code():
    data = request.get_json()
    if 'email' not in data or not isinstance(data['email'], str):
        return jsonify({
            "ok": False,
            "error": "Не указан параметр 'email' или тип не строка"
        }), 400
    email = data['email'].lower()
    if not re.match(r'^([a-z0-9]+[.-_])*[a-z0-9]+@[a-z0-9-]+(\.[a-z]{2,})+$', email):
        return jsonify({
            "ok": False,
            "error": "Некорректный email"
        }), 400
    if 'code' not in data:
        return jsonify({
            "ok": False,
            "error": "Не указан параметр 'code'"
        }), 400
    code = data['code']

    if not isinstance(code, int) or code < 100000 or code > 999999:
        return jsonify({
            "ok": False,
            "error": "'code' должен быть целым числом от 100000 до 999999"
        }), 400

    res_auth, user = utils_auth.auth_by_email_code(email=email, code=code)
    if res_auth["ok"] and res_auth["person_id"]:
        res_auth['access_token'] = create_access_token(identity=res_auth["person_id"])
        res_auth['refresh_token'] = create_refresh_token(identity=res_auth["person_id"])
        res_auth = _add_auth_url(user, res_auth)

    http_code = res_auth.pop("error_code", 200)
    return jsonify(res_auth), http_code


@app.route('/api/auth_jwt/sms_code', methods=["POST"])
def api_auth_jwt_sms_code():
    data = request.get_json()
    if 'phone' not in data:
        return jsonify({
            "ok": False,
            "error": "Не указан параметр 'phone'"
        }), 400

    phone = data['phone']
    if not isinstance(phone, int) or phone < 79000000000 or phone > 79999999999:
        return jsonify({
            "ok": False,
            "error": "'phone' должен быть целым числом от 79000000000 до 79999999999"
        }), 400
    if 'code' not in data:
        return jsonify({
            "ok": False,
            "error": "Не указан параметр 'code'"
        }), 400
    code = data['code']

    if not isinstance(code, int) or code < 100000 or code > 999999:
        return jsonify({
            "ok": False,
            "error": "'code' должен быть целым числом от 100000 до 999999"
        }), 400

    res_auth, user = utils_auth.auth_by_sms_code(phone=phone, code=code)
    if res_auth["ok"] and res_auth["person_id"]:
        res_auth['access_token'] = create_access_token(identity=res_auth["person_id"])
        res_auth['refresh_token'] = create_refresh_token(identity=res_auth["person_id"])
        res_auth = _add_auth_url(user, res_auth)

    http_code = res_auth.pop("error_code", 200)
    return jsonify(res_auth), http_code
