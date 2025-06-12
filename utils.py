import traceback
import sys

from functools import wraps
from utils_auth import get_current_user

from flask import jsonify

from sqlalchemy import not_

from app_config import db
from model import StudGroup


def check_auth_4_api():
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            current_user = get_current_user()
            if current_user is None or current_user.is_anonymous:
                return jsonify({"ok": False, "error": "Пользователь не авторизован"}), 401
            if not current_user.is_active:
                return jsonify({"ok": False, "error": "Учётная запись отключена"}), 403
            try:
                return f(*args, **kwargs)
            except Exception as e:
                sys.stderr.write(traceback.format_exc())

                return jsonify({"ok": False, "error_hidden": True, "error": str(e), "exception_traceback": traceback.format_exc()}), 500
        return wrapped
    return decorator


def periods_archive(query=None):
    q = db.session.query(StudGroup.year, StudGroup.semester)
    if query is not None:
        q = query(q)
    q = q.filter(not_(StudGroup.active)).distinct()

    res = []
    for y, s in q.all():
        s = s % 2
        if s == 0:
            s = 2
        if (y, s) not in res:
            res.append((y, s))

    res.sort(reverse=True)

    return res
