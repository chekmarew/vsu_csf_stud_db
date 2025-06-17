import datetime
from functools import wraps
import socket

from app_config import app, db, mail
from model import CurriculumUnit, Teacher, Student, Person, AttMark, Department, StudGroup, Specialty, LessonStudent, Lesson, CertificateOfStudy

from model import MarkSimpleTypeDict
from model_history_controller import hist_save_controller

from certificate_of_study import certificate_of_study_file_archive

from utils import check_auth_4_api
import utils_info_teacher
import utils_info_student
from utils_json import att_mark_to_json, json_to_att_mark, curriculum_unit_to_json, person_to_json, student_to_json, teacher_to_json, exam_to_json
from utils_auth import get_current_user

from utils_auth import user_request_code_4_change_email, user_request_code_4_change_phone, user_accept_code_4_change_email, user_accept_code_4_change_phone

from flask import jsonify, request, render_template, send_file
from flask_mail import Message

from sqlalchemy import or_, and_, func


# Уведомление о большом числе неуд. оценок
def _att_marks_email_alerts(cu: CurriculumUnit):
    if mail is not None and cu.result_failed is not None and cu.result_failed > app.config['RESULT_FAIL_WARNING']:

        teachers = db.session.query(Teacher).join(Person, Teacher.person_id == Person.id).filter(Teacher.active).filter(Person.email.isnot(None)).filter(or_(Teacher.id == cu.teacher_id, Teacher.notify_results_fail, and_(Teacher.department_leader, Teacher.department_id == cu.department_id))).all()

        msg = Message(subject=app.config['MAIL_SUBJECT'],
                      recipients=[t.person.email for t in teachers])
        msg.html = render_template('email_alerts/att_marks.html', curriculum_unit=cu, MarkSimpleTypeDict=MarkSimpleTypeDict)
        try:
            mail.send(msg)
            return True
        except socket.error:
            return False
    return True


@app.route('/api/pass_department', methods=["GET", "POST"])
def api_pass_department():
    result = {
        "ok": False
    }
    current_user = get_current_user()

    if current_user.is_anonymous:
        return jsonify(result), 401

    if "curriculumUnitId" in request.form:
        try:
            cu_id = int(request.form["curriculumUnitId"])
        except ValueError:
            return jsonify(result), 400

    v = False
    if "value" in request.form and request.form["value"]:
        v = True

    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == cu_id).one_or_none()
    if cu is None:
        return jsonify(result), 404

    if not cu.get_rights(current_user)["pass_department"]:
        return jsonify(result), 403

    if v and not cu.pass_department:
        _r = _att_marks_email_alerts(cu)
        if not _r:
            return jsonify(result), 503

    cu.pass_department = v
    hist_save_controller(db.session, cu, current_user)
    db.session.add(cu)

    db.session.commit()
    result["ok"] = True
    return jsonify(result)


@app.route('/api/favorite_teacher_student', methods=["GET", "POST"])
def api_favorite_teacher_student():
    result = {
        "ok": False
    }
    current_user = get_current_user()
    if current_user.is_anonymous:
        return jsonify(result), 403

    if "action" not in request.form or request.form["action"] not in ("add", "remove"):
        return jsonify(result), 400

    action = request.form["action"]

    if "teacherId" not in request.form or not request.form["teacherId"].isdigit():
        return jsonify(result), 400

    teacher_id = int(request.form["teacherId"])

    if "studentId" not in request.form or not request.form["studentId"].isdigit():
        return jsonify(result), 400

    student_id = int(request.form["studentId"])

    t: Teacher = db.session.query(Teacher).filter(Teacher.id == teacher_id).one_or_none()
    if t is None:
        return jsonify(result), 404

    if not ((current_user.admin_user and current_user.admin_user.active) or (current_user.teacher and teacher_id == current_user.teacher.id)):
        return jsonify(result), 403

    s: Student = db.session.query(Student).filter(Student.id == student_id).one_or_none()
    if s is None:
        return jsonify(result), 404

    if action == "add" and not s.get_rights(t.person)["read_marks"]:
        return jsonify(result), 403

    if action == "add":
        if s not in t.favorite_students:
            t.favorite_students.append(s)
            db.session.add(t)
            db.session.commit()
        result["ok"] = True

    if action == "remove":
        if s in t.favorite_students:
            t.favorite_students.remove(s)
            db.session.add(t)
            db.session.commit()
        result["ok"] = True

    return jsonify(result)


@app.route('/api/curriculum_unit_group_id_next', methods=["GET"])
def api_curriculum_unit_group_id_next():
    result = {
        "ok": False
    }
    current_user = get_current_user()
    if current_user.is_anonymous:
        return jsonify(result), 403

    if not (current_user.admin_user and current_user.admin_user.active):
        return jsonify(result), 403

    max_id = db.session.query(func.max(CurriculumUnit.curriculum_unit_group_id)).first()[0]
    if max_id is None:
        max_id = 1
    else:
        max_id += 1

    result["curriculum_unit_group_id"] = max_id
    result["ok"] = True
    return jsonify(result)


@app.route('/api/att_mark/<int:att_mark_id>', methods=["GET", "POST"])
def api_att_mark(att_mark_id):
    result = {
        "ok": False
    }
    current_user = get_current_user()
    if current_user.is_anonymous:
        return jsonify(result), 401

    att_mark = db.session.query(AttMark).filter(AttMark.att_mark_id == att_mark_id).one_or_none()
    if att_mark is None:
        return jsonify(result), 404
    cu: CurriculumUnit = att_mark.curriculum_unit
    if not cu.get_rights(current_user)["read"]:
        return jsonify(result), 403

    if request.method == "GET":
        result["att_mark"] = att_mark_to_json(att_mark, current_user)
        result["ok"] = True
        return jsonify(result)

    if request.method == "POST":
        if not cu.get_rights(current_user)["write"]:
            return jsonify(result), 403

        try:
            rj = request.json
        except:
            rj = None
        if rj is None:
            result["error"] = "Неверный формат JSON"
            result["error_hidden"] = True
            return jsonify(result), 400

        att_mark, result["errors"] = json_to_att_mark(rj, att_mark, current_user)

        if result["errors"] is not None:
            return jsonify(result), 400

        del result["errors"]

        db.session.add(att_mark)
        hist_save_controller(db.session, att_mark, current_user)
        db.session.commit()
        result["att_mark"] = att_mark_to_json(att_mark, current_user)
        result["ok"] = True
        return jsonify(result)


@app.route('/api/att_marks/<int:curriculum_unit_id>', methods=["GET", "POST"])
def api_att_marks(curriculum_unit_id):
    result = {
        "ok": False
    }
    current_user = get_current_user()
    if current_user.is_anonymous:
        return jsonify(result), 401

    cu: CurriculumUnit = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == curriculum_unit_id).one_or_none()
    if cu is None:
        return jsonify(result), 404

    if not cu.get_rights(current_user)["read"]:
        return jsonify(result), 403

    if request.method == "GET":
        show_exclude_students = request.args.get("show_exclude_students", "True") == "True"
        result["att_marks"] = []
        for att_mark in cu.att_marks:
            if not show_exclude_students and att_mark.att_mark_id in cu.att_marks_readonly_ids:
                continue
            result["att_marks"].append(att_mark_to_json(att_mark, current_user=current_user, add_curriculum_unit_id=False))
        result["ok"] = True
        return jsonify(result)

    if request.method == "POST":
        if not cu.get_rights(current_user)["write"]:
            return jsonify(result), 403

        # Validate
        try:
            rj = request.json
        except:
            rj = None
        if rj is None:
            result["error"] = "Неверный формат JSON"
            result["error_hidden"] = True
            return jsonify(result), 400

        is_valid = True
        try:
            marks_j = rj["att_marks"]
            result["errors"] = {
                "att_marks": [None] * len(marks_j)
            }
            marks = [None] * len(marks_j)

            for i, mark_j in enumerate(marks_j):
                q_mark = db.session.query(AttMark).filter(AttMark.curriculum_unit_id == cu.id)
                if mark_j.get("id", None) is not None:
                    q_mark = q_mark.filter(AttMark.att_mark_id == mark_j["id"])
                    mark = q_mark.one_or_none()
                    if mark is None:
                        is_valid = False
                        result["error"] = "Не найдена запись id=%d" % mark_j["id"]
                        result["error_hidden"] = True
                        break
                elif mark_j.get("student_id", None) is not None:
                    q_mark = q_mark.filter(AttMark.student_id == mark_j["student_id"])
                    mark = q_mark.one_or_none()
                    if mark is None:
                        is_valid = False
                        result["error"] = "Не найдена запись student_id=%d" % mark_j["student_id"]
                        result["error_hidden"] = True
                        break
                else:
                    is_valid = False
                    result["error"] = "Для записи att_marks[%d] не указан id или student_id" % i
                    result["error_hidden"] = True
                    break

                mark, result["errors"]["att_marks"][i] = json_to_att_mark(mark_j, mark, current_user)
                if result["errors"]["att_marks"][i] is None:
                    marks[i] = mark
                else:
                    is_valid = False

        except:
            is_valid = False

        if not is_valid:
            if "error" not in result:
                result["error"] = "Неверный формат JSON"
                result["error_hidden"] = True
            return jsonify(result), 400

        del result["errors"]
        result["att_marks"] = []
        try:
            for mark in marks:
                db.session.add(mark)
                result["att_marks"].append(att_mark_to_json(mark, current_user, add_curriculum_unit_id=False))
                hist_save_controller(db.session, mark, current_user)
            db.session.commit()
        except Exception as e:
            result["error"] = str(e)
            result["error_hidden"] = True
            del result["att_marks"]
            db.session.rollback()
            return jsonify(result), 500

        result["ok"] = True
        return jsonify(result)


@app.route('/api/current_user', methods=["GET"])
@check_auth_4_api()
def api_current_user():
    result = {
        "ok": False
    }
    current_user = get_current_user()

    attrs = ('id', 'surname', 'firstname', 'firstname', 'middlename', 'login', 'email', 'phone')
    for attr in attrs:
        result[attr] = getattr(current_user, attr)

    for u in current_user.roles:
        if u.role_name == "Student":
            if "students" not in result:
                result["students"] = []
            j_student = {
                "id": u.id,
                "status": u.status
            }
            group = u.stud_group
            if group is not None:
                j_student.update({
                    "semester": group.semester,
                    "course": group.course,
                    "group": group.num,
                    "sub_group": u.stud_group_subnum if u.stud_group_subnum != 0 else 1,
                    "specialty": {
                        "id": group.specialty.id,
                        "code": group.specialty.code,
                        "full_name": group.specialty.full_name
                    },
                })

            result["students"].append(j_student)

        if u.role_name == "Teacher":
            result["teacher"] = {
                "id": u.id,
                "rank": u.rank,
                "dean_staff": u.dean_staff,
                "department_leader": u.department_leader,
                "department_secretary": u.department_secretary,
                "right_read_all": u.right_read_all,
                "department": {
                    "id": u.department.id,
                    "name": u.department.full_name
                }
            }

        if u.role_name == "AdminUser":
            result["admin_user"] = {
                "id": u.id
            }

    result["ok"] = True
    return jsonify(result)


@app.route('/api/current_user/change_email/request_code', methods=["POST"])
@check_auth_4_api()
def api_current_user_change_email_request_code():
    current_user: Person = get_current_user()
    email = request.form.get("email", None)
    if email is None:
        return jsonify({"ok": False, "error": "Отсутствует поле 'email'"}), 400

    res = user_request_code_4_change_email(current_user, email)
    http_code = res.pop("error_code", 200)
    return jsonify(res), http_code


@app.route('/api/current_user/change_phone/request_code', methods=["POST"])
@check_auth_4_api()
def api_current_user_change_phone_request_code():
    current_user: Person = get_current_user()
    phone = request.form.get("phone", None)
    if phone is None:
        return jsonify({"ok": False, "error": "Отсутствует поле 'phone'"}), 400
    try:
        phone = int(phone)
    except ValueError:
        return jsonify({"ok": False, "error": "Поле 'phone' должно быть целым числом"}), 400

    res = user_request_code_4_change_phone(current_user, phone)
    http_code = res.pop("error_code", 200)
    return jsonify(res), http_code


def _current_user_change_profile_accept_code(f):
    @wraps(f)
    def wrapper():
        code = request.form.get("code", None)
        if code is None:
            return jsonify({"ok": False, "error": "Отсутствует поле 'code'"}), 400
        try:
            code = int(code)
        except ValueError:
            return jsonify({"ok": False, "error": "Поле 'code' должно быть целым числом"}), 400

        if code < 100000 or code > 999999:
            return jsonify({"ok": False, "error": "Неверный формат поля 'code'"}), 400

        code_old = None
        if "code_old" in request.form:
            try:
                code_old = int(request.form["code_old"])
            except ValueError:
                return jsonify({"ok": False, "error": "Поле 'code_old' должно быть целым числом"}), 400

            if code_old < 100000 or code_old > 999999:
                return jsonify({"ok": False, "error": "Неверный формат поля 'code_old'"}), 400

        return f(code, code_old)

    return wrapper


@app.route('/api/current_user/change_email/accept_code', methods=["POST"])
@check_auth_4_api()
@_current_user_change_profile_accept_code
def api_current_user_change_email_accept_code(code, code_old):
    current_user: Person = get_current_user()

    res = user_accept_code_4_change_email(current_user, code, code_old)
    http_code = res.pop("error_code", 200)
    return jsonify(res), http_code


@app.route('/api/current_user/change_phone/accept_code', methods=["POST"])
@check_auth_4_api()
@_current_user_change_profile_accept_code
def api_current_user_change_phone_accept_code(code, code_old):
    current_user: Person = get_current_user()

    res = user_accept_code_4_change_phone(current_user, code, code_old)
    http_code = res.pop("error_code", 200)
    return jsonify(res), http_code


def _teacher_request(f):
    @wraps(f)
    def wrapper(teacher_id=None):
        current_user: Person = get_current_user()

        if teacher_id is None:
            teacher = current_user.teacher
            if teacher is None:
                return jsonify({"ok": False}), 403
        else:
            teacher: Teacher = db.session.query(Teacher).filter_by(id=teacher_id).one_or_none()
            if teacher is None:
                return jsonify({"ok": False}), 404

            if not ((current_user.admin_user is not None and current_user.admin_user.active) or
                    (current_user.teacher is not None and current_user.teacher.id == teacher_id)):
                return jsonify({"ok": False}), 403
        return f(teacher)

    return wrapper


@app.route('/api/teacher_info', methods=["GET"])
@app.route('/api/teacher_info/<int:teacher_id>', methods=["GET"])
@check_auth_4_api()
@_teacher_request
def api_teacher_info(teacher):
    teacher_j = person_to_json(teacher.person, ext_data=True)
    teacher_j["teacher_id"] = teacher.id
    teacher_j["rank"] = teacher.rank
    teacher_j["department_id"] = teacher.department_id
    teacher_j["department_name"] = teacher.department.name
    faculty = teacher.department.parent_department
    if faculty is not None:
        teacher_j["faculty_id"] = faculty.id
        teacher_j["faculty_name"] = faculty.name

    teacher_j["ok"] = True
    return jsonify(teacher_j)


@app.route('/api/teacher_curriculum_units', methods=["GET"])
@app.route('/api/teacher_curriculum_units/<int:teacher_id>', methods=["GET"])
@check_auth_4_api()
@_teacher_request
def api_teacher_curriculum_units(teacher):
    curriculum_units = utils_info_teacher.curriculum_units(teacher)
    return jsonify({
        "ok": True,
        "curriculum_units": [curriculum_unit_to_json(cu, contacts=True, exam_schedule=True, exam_schedule_teacher_id=teacher.id) for cu in curriculum_units]
    })


def _student_request(f):
    @wraps(f)
    def wrapper(student_id=None):
        current_user: Person = get_current_user()

        if student_id is None:
            student = current_user.student
            if student is None:
                return jsonify({"ok": False}), 403
        else:
            student: Student = db.session.query(Student).filter_by(id=student_id).one_or_none()
            if student is None:
                return jsonify({"ok": False}), 404

            if not student.get_rights(current_user)["read_marks"]:
                return jsonify({"ok": False}), 403
        return f(student)

    return wrapper


@app.route('/api/student_info', methods=["GET"])
@app.route('/api/student_info/<int:student_id>', methods=["GET"])
@check_auth_4_api()
@_student_request
def api_student_info(student):
    student_j = student_to_json(student, faculty=db.session.query(Department).filter_by(id=Department.ID_DEFAULT).one(), ext_data=True)
    student_j["ok"] = True
    return jsonify(student_j)


@app.route('/api/student_marks', methods=["GET"])
@app.route('/api/student_marks/<int:student_id>', methods=["GET"])
@check_auth_4_api()
@_student_request
def api_student_marks(student):
    att_marks_j = []
    for mark in utils_info_student.att_marks_report(student):
        result_print = mark.result_print
        cu: CurriculumUnit = mark.curriculum_unit
        sg: StudGroup = cu.stud_group

        att_mark_j = {
            'id': mark.att_mark_id,
            'curriculum_unit_id': mark.curriculum_unit_id,
            'ball_average': mark.ball_average,
            'result': result_print[0] if result_print is not None else None,
            'result5': result_print[1]["value"] if result_print is not None else None,
            'attendance_pct': mark.attendance_pct,
            'attendance_rate': mark.attendance_rate,
            'ball_attendance_add': mark.ball_attendance_add,
            'subject_name': cu.subject_name_print,
            'teacher': cu.teacher.person.full_name,
            'practice_teachers': [t.person.full_name for t in mark.curriculum_unit.practice_teachers],
            'semester': sg.semester,
            'session_num': sg.session_num,
            'year': sg.year,
            'mark_type': cu.mark_type,
            'has_simple_mark_test_simple': cu.has_simple_mark_test_simple,
            'has_simple_mark_exam': cu.has_simple_mark_exam,
            'has_simple_mark_test_diff': cu.has_simple_mark_test_diff,
            'has_simple_mark_course_work': cu.has_simple_mark_course_work,
            'has_simple_mark_course_project': cu.has_simple_mark_course_project,
            'moodle_id': cu.moodle_id,
            'comment': mark.comment
        }

        for attr in cu.visible_attrs_4_report:
            att_mark_j[attr] = getattr(mark, attr)

        if student.stud_group_id is not None and cu.mark_type == "exam" and sg.active and student.stud_group_id == sg.id:
            att_mark_j["exam_schedule"] = None
            for exam in cu.exams:
                if exam.stud_group_subnums_map[student.stud_group_subnum]:
                    att_mark_j["exam_schedule"] = exam_to_json(exam, stud_group_subnums=False, curriculum_unit_id=False)

        att_marks_j.append(att_mark_j)

    return jsonify({
        "marks": att_marks_j,
        "ok": True
    })


@app.route('/api/student_rating', methods=["GET"])
@app.route('/api/student_rating/<int:student_id>', methods=["GET"])
@check_auth_4_api()
@_student_request
def api_student_rating(student):
    group = student.stud_group
    if group is None:
        return jsonify({
            'ok': False,
            'error': 'Рейтинг для данного студента не доступен'
        }), 400

    specialty = group.specialty
    calc_types = []
    if request.args.get('calc_course', '') == 'True':
        calc_types.append('course')

    if request.args.get('calc_specialty', '') == 'True':
        calc_types.append("specialty")

    if request.args.get('calc_group', '') == 'True':
        calc_types.append("group")

    year, semester = (int(request.args['year']), int(request.args['semester'])) if 'year' in request.args and 'semester' in request.args else (None, None)

    def _get_rating(groups):
        result = {
            "rows": []
        }
        for stage in ('total', 'att_mark_3', 'att_mark_2', 'att_mark_1'):
            rating_rows, avg_ball = utils_info_student.rating_with_avg_ball(groups, stage)
            if not rating_rows:
                continue
            for row in rating_rows:
                p: Person = row['student'].person
                result["rows"].append({
                    "student_id": row['student'].id,
                    "person_id": p.id,
                    "surname": p.surname,
                    "firstname": p.firstname,
                    "middlename": p.middlename,
                    "gender": p.gender,
                    "avg_ball": float(row["avg_ball"]),
                    "rating": row["rating"]
                })
                if row['student'].id == student.id:
                    result.update({
                        "avg_ball": float(row["avg_ball"]),
                        "rating": row["rating"],
                        "count_all": len(rating_rows),
                        "avg_ball_all": float(avg_ball),
                        "stage": stage
                    })
            return result
    rating = {}
    for calc_type in calc_types:
        q_groups = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id).filter(Specialty.education_level_order == specialty.education_level_order)

        if year is not None and semester is not None:
            q_groups = q_groups.filter(StudGroup.year == year).filter(StudGroup.semester == semester)
        else:
            q_groups = q_groups.filter(StudGroup.active, StudGroup.semester == student.semester)

        if calc_type == "course":
            pass
        elif calc_type == "specialty":
            q_groups = q_groups.filter(Specialty.code == group.specialty.code)
        elif calc_type == "group":
            if year is not None and semester is not None:
                q_group_ids = db.session.query(StudGroup.id).join(CurriculumUnit, CurriculumUnit.stud_group_id == StudGroup.id).join(AttMark, AttMark.curriculum_unit_id == CurriculumUnit.id).filter(AttMark.student_id == student.id).filter(StudGroup.year == year).filter(StudGroup.semester == semester).distinct()
                group_ids = [row[0] for row in q_group_ids.all()]
                if len(group_ids) == 0:
                    group_ids = [0]
                q_groups = db.session.query(StudGroup).filter(StudGroup.id.in_(group_ids))
            else:
                q_groups = db.session.query(StudGroup).filter(StudGroup.id == group.id)

        groups = q_groups.all()

        rating[calc_type] = _get_rating(groups=groups)

    return jsonify({
        "ok": True,
        "rating": rating
    })


@app.route('/api/student_lessons', methods=["GET"])
@app.route('/api/student_lessons/<int:student_id>', methods=["GET"])
@check_auth_4_api()
@_student_request
def api_student_lessons(student):
    result = {"ok": False}
    curriculum_unit_id = None
    if "curriculum_unit_id" in request.args:
        try:
            curriculum_unit_id = int(request.args["curriculum_unit_id"])
        except ValueError:
            result["error"] = "Параметр 'curriculum_unit_id' должен быть целым числом"
            result["error_hidden"] = True
            return jsonify(result), 400

    year = None
    if "year" in request.args:
        try:
            year = int(request.args["year"])
        except ValueError:
            result["error"] = "Параметр 'year' должен быть целым числом"
            result["error_hidden"] = True
            return jsonify(result), 400

    semester = None
    if "semester" in request.args:
        try:
            semester = int(request.args["semester"])
        except ValueError:
            result["error"] = "Параметр 'semester' должен быть целым числом"
            result["error_hidden"] = True
            return jsonify(result), 400

    q_lessons = db.session.query(LessonStudent).join(Lesson, LessonStudent.lesson_id == Lesson.id).join(CurriculumUnit, LessonStudent.curriculum_unit_id == CurriculumUnit.id).join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).filter(LessonStudent.student_id == student.id)
    if curriculum_unit_id is not None:
        q_lessons = q_lessons.filter(LessonStudent.curriculum_unit_id == curriculum_unit_id)
    if year is not None:
        q_lessons = q_lessons.filter(StudGroup.year == year)
    if semester is not None:
        q_lessons = q_lessons.filter(StudGroup.semester == semester)

    q_lessons = q_lessons.order_by(Lesson.date.desc(), Lesson.lesson_num.desc())
    result["lessons"] = []
    result["teachers"] = []
    result["attendance_pct"] = None
    teacher_ids = set()

    count_lessons = 0
    count_lessons_attendance = 0

    for l_s in q_lessons:
        l_s: LessonStudent = l_s
        l: Lesson = l_s.lesson_curriculum_unit.lesson
        result["lessons"].append({
            "id": l_s.lesson_id,
            "curriculum_unit_id": l_s.curriculum_unit_id,
            "date": l.date.isoformat(),
            "lesson_num": l.lesson_num,
            "teacher_id": l.teacher_id,
            "lesson_comment": l.comment,
            "attendance": l_s.attendance,
            "comment": l_s.comment
        })
        if l.teacher_id not in teacher_ids:
            teacher_ids.add(l.teacher_id)
            t: Teacher = l.teacher
            result["teachers"].append(teacher_to_json(t))
        count_lessons += 1
        if l_s.attendance != 0:
            count_lessons_attendance += 1

    result["teachers"].sort(key=lambda t: t["id"])
    if count_lessons > 0:
        result["attendance_pct"] = (count_lessons_attendance*100) // count_lessons if (count_lessons_attendance*100) % count_lessons == 0 else round((count_lessons_attendance*100)/count_lessons, 2)

    result["ok"] = True
    return jsonify(result)


@app.route('/api/certificate_of_study/<ids>', methods=["GET", "POST", "DELETE"])
@check_auth_4_api()
def api_certificate_of_study(ids: str):
    current_user = get_current_user()
    if current_user.is_anonymous:
        return jsonify({"ok": False}), 401

    if not((current_user.admin_user and current_user.admin_user.active) or (current_user.teacher and current_user.teacher.active and current_user.teacher.dean_staff)):
        return jsonify({"ok": False}), 403

    try:
        cert_ids = [int(id) for id in ids.split(",")]
    except ValueError:
        return jsonify({"ok": False, "error": "Неправильный формат ID"}), 400

    certs = db.session.query(CertificateOfStudy).filter(CertificateOfStudy.id.in_(cert_ids)).order_by(CertificateOfStudy.id).all()
    if len(certs) < len(cert_ids):
        return jsonify({"ok": False, "error": "Запись(и) не найдены"}), 404

    if request.method == "GET":
        if any((cert.print_time is None or cert.year is None or cert.num is None for cert in certs)):
            return jsonify({"ok": False, "error": "Нельзя печатать справки без номера или даты"}), 400
        # Печать справки InfoSys

        now = datetime.datetime.now()
        zip_bytes = certificate_of_study_file_archive(
            certs,
            secretary_name=request.args.get('secretary_name', current_user.full_name_short),
            one_file=(len(certs) == 1 or request.args.get('one_file', '') not in ('', '0', 'false', 'False', 'off')),
            file_prefix=now.strftime('_%Y_%m_%d_%H_%M'))

        return send_file(zip_bytes, mimetype="application/x-zip-compressed", as_attachment=True,
                  download_name='certificates_of_study_%s.zip' % now.strftime('%Y_%m_%d_%H_%M'))

    if request.method == "POST":
        if "action" not in request.form:
            return jsonify({"ok": False, "error": "Отсутствует параметр 'action'"}), 400

        if request.form["action"] == "issue_number":
            if any((cert.print_time is not None and cert.year is not None and cert.num is not None for cert in certs)):
                return jsonify({"ok": False, "error": "Справке уже выдан номер"}), 400

            now = datetime.datetime.now()
            max_num = db.session.query(func.max(CertificateOfStudy.num)).filter(CertificateOfStudy.year == now.year).with_for_update().first()[0]
            if max_num is None:
                max_num = 0
            for cert in certs:
                max_num += 1
                cert.print_time = now
                cert.year = now.year
                cert.num = max_num
                db.session.add(cert)
            db.session.commit()
        elif request.form["action"] == "mark_issued":
            if not all((cert.print_time is not None and cert.year is not None and cert.num is not None and cert.ready_time is None for cert in certs)):
                return jsonify({"ok": False, "error": "Справке не выдан номер или она уже отмечена как выданная"}), 400

            # map person_id -> [] certs
            certs_map = {}
            now = datetime.datetime.now()
            for cert in certs:
                cert.ready_time = now
                if cert.student.person_id not in certs_map:
                    certs_map[cert.student.person_id] = []
                certs_map[cert.student.person_id].append(cert)

            if mail is not None:
                for person_id, _certs in certs_map.items():
                    p: Person = db.session.query(Person).filter_by(id=person_id).one()
                    if p.email is not None:
                        msg = Message(subject=app.config['MAIL_SUBJECT'], recipients=[p.email])
                        msg.html = render_template('email_alerts/certificate_of_study_ready.html', certificates=_certs)
                        mail.send(msg)
            db.session.commit()
        elif request.form["action"] == "change_comment":
            if "comment" not in request.form:
                return jsonify({"ok": False, "error": "Отсутствует параметр 'comment'"}), 400
            comment = request.form["comment"].strip()
            if len(comment) > 4000:
                return jsonify({"ok": False, "error": "Длина комментария не может быть больше 4000 символов"}), 400
            if not comment:
                comment = None

            if any((cert.ready_time is not None for cert in certs)):
                return jsonify({"ok": False, "error": "Нельзя изменять комментарий у выданных справок"}), 400

            for cert in certs:
                cert.comment = comment
                db.session.add(cert)
            db.session.commit()

        else:
            return jsonify({"ok": False, "error": "Недопустимое значение параметра 'action'"}), 400

    if request.method == "DELETE":
        if any((cert.print_time is not None or cert.year is not None or cert.num is not None for cert in certs)):
            return jsonify({"ok": False, "error": "Нельзя удалять справку с выданным номером"}), 400
        for cert in certs:
            db.session.delete(cert)
        db.session.commit()

    return jsonify({"ok": True})
