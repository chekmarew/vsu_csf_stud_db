from app_config import app, db
from model import StudGroup, Specialty, CurriculumUnit, AttMark, Student, Teacher, Subject, Person, Department, MarkSimpleTypeDict
from utils_json import person_to_json, student_to_json, teacher_to_json
import utils_info_student

from flask import jsonify, request

from sqlalchemy import or_, and_, func

from datetime import datetime
from functools import wraps

import re


def _get_api_key():
    return request.headers.get('Authorization',None) or request.form.get("api_key", None) or request.args.get("api_key", None)


def _check_api_key(right):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            api_key = _get_api_key()
            if api_key is None:
                return jsonify({"ok": False, "error": "Не указан api_key"}), 401

            if api_key not in app.config['API_KEYS']:
                return jsonify({"ok": False, "error": "Недействительный api_key"}), 403

            if right not in app.config['API_KEYS'][api_key]:
                return jsonify({"ok": False, "error": "Для api_key нет прав доступа для метода"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator


def _route_with_year_session_num():
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            year, session_num, all_data = None, None, request.args.get("all_data", "") == "True"
            if not all_data:
                if "year" in request.args and "session_num" in request.args:
                    try:
                        year, session_num = int(request.args["year"]), int(request.args["session_num"])
                    except ValueError:
                        return jsonify({
                            "ok": False,
                            "error": "Параметры 'year' и 'session_num' должны быть целыми числами"
                        }), 400

                    if session_num not in (1, 2):
                        return jsonify({
                            "ok": False,
                            "error": "Параметр 'session_num' должен иметь значение 1 или 2"
                        }), 400
            return f(year=year, session_num=session_num, all_data=all_data)
        return wrapped
    return decorator


@app.route('/public_api/marks')
@_check_api_key("marks")
def public_api_marks():
    result = {
        "errors": [],
        "ok": True
    }

    specialty_code = None
    if "specialty_code" in request.args and request.args["specialty_code"]:
        specialty_code = request.args["specialty_code"]
    else:
        result["errors"].append("Не указан параметр 'specialty_code'")

    subject_code = None
    if "subject_code" in request.args and request.args["subject_code"]:
        subject_code = request.args["subject_code"]
    else:
        result["errors"].append("Не указан параметр 'subject_code'")

    semester = None
    if "semester" in request.args and request.args["semester"]:
        try:
            semester = int(request.args["semester"])
        except ValueError:
            result["errors"].append("Параметр 'semester' должен быть целым числом")
    else:
        result["errors"].append("Не указан параметр 'semester'")

    group_num = None
    if "group_num" in request.args and request.args["group_num"]:
        try:
            group_num = int(request.args["group_num"])
        except ValueError:
            result["errors"].append("Параметр 'group_num' должен быть целым числом")

    mark_type = None
    if "test_form" in request.args:
        for _mark_type, _mark_type_name in MarkSimpleTypeDict.items():
            if _mark_type_name == request.args["test_form"]:
                mark_type = _mark_type

    if mark_type is None:
        result["errors"].append("Параметр 'test_form' не указан или имеет недопустимое значение")

    if len(result["errors"]):
        result["ok"] = False
        return jsonify(result), 400

    try:
        q = db.session.query(AttMark). \
            join(CurriculumUnit, AttMark.curriculum_unit_id == CurriculumUnit.id). \
            join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).\
            join(Specialty, StudGroup.specialty_id == Specialty.id). \
            filter(AttMark.exclude.is_(None)).\
            filter(CurriculumUnit.code == subject_code).\
            filter(Specialty.code == specialty_code).\
            filter(StudGroup.semester == semester).\
            filter(StudGroup.active).\
            filter(CurriculumUnit.closed)

        if group_num:
            q = q.filter(StudGroup.num == group_num)

        result["data"] = []
        for m in q.all():
            m_simple = m.get_simple_att_mark(mark_type)
            if m_simple and m_simple.ball_value is not None:
                result["data"].append({
                    "student_id": m.student_id,
                    "mark": m_simple.ball_value
                })

    except Exception as e:
        result["ok"] = False
        result["errors"].append(str(e))
        return jsonify(result), 500

    return jsonify(result)


@app.route('/public_api/students')
@_check_api_key("students")
def public_api_students():
    api_key = _get_api_key()
    year = datetime.now().year
    start_year_map = None
    faculty = db.session.query(Department).filter_by(id=Department.ID_DEFAULT).one()
    if request.args.get('recently', '') == 'True':
        q_students = db.session.query(Student).filter(or_(Student.status == 'study', and_(Student.status.in_(('expelled', 'academic_leave')), Student.expelled_year >= year - 1), and_(Student.status == 'alumnus', Student.alumnus_year >= year -1)))
    else:
        q_students = db.session.query(Student).filter(Student.status == 'study')
        start_year_map = dict(db.session.query(AttMark.student_id, func.min(StudGroup.year)).\
            join(Student, AttMark.student_id == Student.id).\
            join(CurriculumUnit, AttMark.curriculum_unit_id == CurriculumUnit.id).\
            join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).\
            filter(Student.status == 'study').\
            group_by(AttMark.student_id).all())

    students_j = []
    for s in q_students.all():
        student_j = student_to_json(s, faculty=faculty, ext_data=("contacts" in app.config['API_KEYS'][api_key]))
        if start_year_map is not None:
            start_year = None
            if s.id in start_year_map:
                start_year = start_year_map[s.id]

            if s.stud_group is not None:
                _y = s.stud_group.year - s.stud_group.course + 1
                start_year = min(start_year, _y) if start_year is not None else _y

            student_j["start_year"] = start_year

        students_j.append(student_j)
    return jsonify({
        "ok": True,
        "students": students_j
    })


@app.route('/public_api/student/<int:id>/create_login', methods=["POST"])
@_check_api_key("student_login")
def public_api_student_create_login(id: int):
    result = {
        "ok": False
    }

    s: Student = db.session.query(Student).filter(Student.id == id).one_or_none()
    if s is None:
        result["error"] = "Студент %d не найден"
        return jsonify(result), 404

    if "login" not in request.form:
        result["error"] = "Не указан параметр 'login'"
        return jsonify(result), 400

    login = request.form["login"]

    if len(login) < 3:
        result["error"] = "Параметр 'login' не может быть меньше 3-х символов"
        return jsonify(result), 400

    if len(login) > 45:
        result["error"] = "Параметр 'login' не может быть больше 45-ти символов"
        return jsonify(result), 400

    if not re.match("^[a-z0-9_\\-]+$", login):
        result["error"] = "Параметр 'login' не соответствует регулярному выражению '^[a-z0-9_\\-]+$'"
        return jsonify(result), 400

    s_other: Student = db.session.query(Student).join(Person, Student.person_id == Person.id).filter(Person.id != s.person_id).filter(Person.login == login).one_or_none()
    if s_other:
        result["error"] = "Уже есть студент с login=%s" % login
        result["student_other"] = student_to_json(s_other)
        return jsonify(result), 400

    p = s.person
    p.login = login
    db.session.add(p)
    db.session.commit()

    result["ok"] = True
    return jsonify(result)


@app.route('/public_api/teachers', methods=["GET"])
@_check_api_key("teachers")
def public_api_teachers():
    api_key = _get_api_key()
    j_teachers = []

    q_teachers = db.session.query(Teacher).filter_by(active=True)
    if "department_id" in request.args and request.args["department_id"].isdigit():
        department_id = int(request.args["department_id"])
        q_teachers = q_teachers.filter(or_(Teacher.department_id == department_id, Teacher.departments_part_time_job.any(Department.id == department_id)))

    for t in q_teachers.all():
        j_teacher = teacher_to_json(t)
        if "contacts" in app.config['API_KEYS'][api_key]:
            j_teacher.update({
                "email": t.person.email,
                "phone": t.person.phone
            })
        j_teachers.append(j_teacher)

    return jsonify({
        "ok": True,
        "teachers": j_teachers
    })


@app.route('/public_api/subjects', methods=["GET"])
@_check_api_key("subjects")
def public_api_subjects():
    j_subjects = []
    for s in db.session.query(Subject).all():
        j_subjects.append({
            "id": s.id,
            "name": s.name,
            "short_name": s.short_name
        })

    return jsonify({
        "ok": True,
        "subjects": j_subjects
    })


@app.route('/public_api/stud_groups', methods=["GET"])
@_check_api_key("stud_groups")
@_route_with_year_session_num()
def public_api_stud_groups(year, session_num, all_data):
    api_key = _get_api_key()
    q_groups = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id)

    if not all_data:
        if year is not None and session_num is not None:
            q_groups = q_groups.filter(StudGroup.year == year).filter(func.mod(StudGroup.semester, 2) == (0 if session_num == 2 else 1))
        else:
            q_groups = q_groups.filter(StudGroup.active)

    j_stud_groups = []
    for g in q_groups.order_by(Specialty.education_level_order, StudGroup.semester, StudGroup.num).all():
        j_stud_group = {
            "id": g.id,
            "year": g.year,
            "semester": g.semester,
            "session_num": g.session_num,
            "course": g.course,
            "num": g.num,
            "sub_count": g.sub_count,
            "specialty_code": g.specialty.code,
            "specialty_name": g.specialty.name,
            "specialization": g.specialty.specialization,
            "education_form": g.specialty.education_form,
            "education_level_order": g.specialty.education_level_order,
            "education_level": g.specialty.education_level,
            "specialty_department_id": g.specialty.department_id,
            "lessons_start_date": g.lessons_start_date.isoformat() if g.lessons_start_date else None,
            "session_start_date": g.session_start_date.isoformat() if g.session_start_date else None,
            "session_end_date": g.session_end_date.isoformat() if g.session_end_date else None,
            "active": g.active
        }
        if "students" in app.config['API_KEYS'][api_key]:
            j_stud_group["group_leader_id"] = g.group_leader_id
            j_stud_group["group_leader2_id"] = g.group_leader2_id
        if "teachers" in app.config['API_KEYS'][api_key]:
            j_stud_group["curator_id"] = g.curator_id

        j_stud_groups.append(j_stud_group)

    return jsonify({
        "ok": True,
        "stud_groups": j_stud_groups
    })


@app.route('/public_api/curriculum_units', methods=["GET"])
@_check_api_key("curriculum_units")
@_route_with_year_session_num()
def public_api_curriculum_units(year, session_num, all_data):
    q_cus = db.session.query(CurriculumUnit).join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id)
    if not all_data:
        if year is not None and session_num is not None:
            q_cus = q_cus.filter(StudGroup.year == year).filter(func.mod(StudGroup.semester, 2) == (0 if session_num == 2 else 1))
        else:
            q_cus = q_cus.filter(StudGroup.active)

    if "department_id" in request.args and request.args["department_id"].isdigit():
        q_cus = q_cus.filter(CurriculumUnit.department_id == int(request.args["department_id"]))

    j_curriculum_units = []
    for cu in q_cus.all():
        cu: CurriculumUnit = cu
        j_curriculum_units.append({
            "id": cu.id,
            "subject_id": cu.subject_id,
            "stud_group_id": cu.stud_group_id,
            "mark_type": cu.mark_type,
            "teacher_id": cu.teacher_id,
            "department_id": cu.department_id,
            "curriculum_unit_group_id": cu.curriculum_unit_group_id,
            "practice_teacher_ids": [t.id for t in cu.practice_teachers]
        })

    return jsonify({
        "ok": True,
        "curriculum_units": j_curriculum_units
    })


@app.route('/public_api/att_marks', methods=["GET"])
@_check_api_key("att_marks")
@_route_with_year_session_num()
def public_api_att_marks(year, session_num, all_data):
    q_marks = db.session.query(AttMark).join(CurriculumUnit, AttMark.curriculum_unit_id == CurriculumUnit.id).join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id)

    if not all_data:
        if year is not None and session_num is not None:
            q_marks = q_marks.filter(StudGroup.year == year).filter(func.mod(StudGroup.semester, 2) == (0 if session_num == 2 else 1))
        else:
            q_marks = q_marks.filter(StudGroup.active)

    j_marks = []
    for m in q_marks.order_by(AttMark.curriculum_unit_id).order_by(AttMark.student_id).all():
        m: AttMark = m
        if m.att_mark_id in m.curriculum_unit.att_marks_readonly_ids:
            continue

        r = m.result_print
        j_marks.append(
            {
                "id": m.att_mark_id,
                "att_mark_1": m.att_mark_1,
                "att_mark_2": m.att_mark_2,
                "att_mark_3": m.att_mark_3,
                "result": r[0] if r is not None else None,
                "curriculum_unit_id": m.curriculum_unit_id,
                "student_id": m.student_id,
            }
        )
    return jsonify({
        "ok": True,
        "marks": j_marks
    })


@app.route('/public_api/rating', methods=["GET"])
@_check_api_key("rating")
def public_api_rating():

    def _get_actual_rating(groups):
        for stage in ('total', 'att_mark_3', 'att_mark_2', 'att_mark_1'):
            res = utils_info_student.rating(groups, stage)
            if res:
                return res
        return []

    def _prepare_response(groups):
        return [{'rating': s['avg_ball'], 'id': s['student'].person_id} for s in _get_actual_rating(groups)]

    user_id = request.args.get('id', None)
    if not user_id:
        return jsonify({'error': 'Не указан id пользователя'}), 400

    calc_course = request.args.get('calc_course') == 'True'
    calc_specialty = request.args.get('calc_specialty') == 'True'
    calc_group = request.args.get('calc_group') == 'True'

    student = db.session.query(Student).filter(Student.person_id == user_id).filter(
        Student.status == 'study').one_or_none()
    if not student or not student.stud_group:
        return jsonify({'error': 'Рейтинг для данного студента не доступен'}), 400
    group = student.stud_group
    specialty = group.specialty

    response = {}

    if calc_specialty:
        specialty_groups = db.session.query(StudGroup).join(Specialty).filter(StudGroup.active).filter(
            StudGroup.semester == student.semester).filter(Specialty.code == specialty.code).all()
        response['specialty'] = _prepare_response(specialty_groups)

    if calc_course:
        course_groups = db.session.query(StudGroup).join(Specialty).filter(Specialty.education_level_order == specialty.education_level_order, StudGroup.semester == student.semester,
                                                           StudGroup.active).all()
        response['course'] = _prepare_response(course_groups)

    if calc_group:
        response['group'] = _prepare_response([group])

    return jsonify(response), 200
