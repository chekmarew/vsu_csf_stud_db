import json

from app_config import app, db
from model import Teacher, CurriculumUnit, Subject, Student, StudGroup, LessonTypes, LessonForms, Lesson, LessonCurriculumUnit, LessonStudent, LessonTime, AttMark, Person, Holiday

from utils import check_auth_4_api
from utils_json import att_mark_to_json, teacher_to_json, curriculum_unit_to_json, lesson_time_to_json
import utils_info_teacher
from utils_auth import get_current_user

from flask import jsonify, request

from datetime import date, datetime, timedelta

from model_history_controller import hist_save_controller



# проверка по дате времени на возможность установления student_mark_active
def _validate_student_mark_active(lesson_date, lesson_num):
    now = datetime.now()

    lesson_time: LessonTime = db.session.query(LessonTime).filter_by(lesson_num=lesson_num).one_or_none()
    if lesson_time is None:
        return False

    return datetime.combine(lesson_date, lesson_time.stime) <= now <= (datetime.combine(lesson_date, lesson_time.etime) + timedelta(minutes=10))


@app.route('/api/lessons/times', methods=["GET"])
def api_lessons_times():
    now = datetime.now()
    lesson_times = db.session.query(LessonTime).order_by(LessonTime.lesson_num).all()
    lesson_num = None
    for t in lesson_times:
        if t.stime > now.time():
            if lesson_num is None:
                lesson_num = t.lesson_num
            break
        lesson_num = t.lesson_num
        if t.stime <= now.time() <= t.etime:
            break

    today = now.date()
    while today.isoweekday() == 7 or db.session.query(Holiday).filter_by(date=today).count() > 0:
        today = today - timedelta(days=1)

    return jsonify({
        "ok": True,
        "today": today.isoformat(),
        "curr_lesson_num": lesson_num,
        "times": [lesson_time_to_json(t) for t in lesson_times]
    })


@app.route('/api/lessons/new', methods=["GET", "POST"])
@app.route('/api/lessons/new/<int:teacher_id>', methods=["GET", "POST"])
@check_auth_4_api()
def api_lessons_new(teacher_id=None):
    current_user = get_current_user()

    result = {"ok": False}

    if not(
            (current_user.teacher is not None and (teacher_id is None or current_user.teacher.id == teacher_id) and current_user.teacher.active) or
            (current_user.admin_user is not None and current_user.admin_user.active)
    ):
        result["error"] = "Нет прав доступа"
        return jsonify(result), 403

    if teacher_id is None:
        teacher = current_user.teacher
        teacher_id = current_user.teacher.id
    else:
        teacher = db.session.query(Teacher).filter_by(id=teacher_id).one_or_none()

    curriculum_units = utils_info_teacher.curriculum_units(teacher)

    if request.method == "GET":
        result["curriculum_units"] = [curriculum_unit_to_json(cu) for cu in curriculum_units]
        result["ok"] = True

    if request.method == "POST":
        # Validate
        try:
            rj = request.json
        except:
            rj = None
        if rj is None:
            result["error"] = "Неверный формат JSON"
            result["error_hidden"] = True
            return jsonify(result), 400

        result["errors"] = {}

        try:
            lesson_date = date.fromisoformat(rj["date"])
            today = date.today()
            if lesson_date > today:
                result["errors"]["date"] = "Дата не может быть указана в будущем"
            elif lesson_date.isoweekday() == 7:
                result["errors"]["date"] = "День недели не может быть воскресеньем"
            elif db.session.query(Holiday).filter_by(date=lesson_date).count() > 0:
                result["errors"]["date"] = "Указан праздничный день"
        except Exception:
            result["errors"]["date"] = "Неверный формат поля"
            lesson_date = None

        if "lesson_num" not in rj:
            result["errors"]["lesson_num"] = "Пустое поле"
        elif not isinstance(rj["lesson_num"], int):
            result["errors"]["lesson_num"] = "Неверный формат поля"
        elif rj["lesson_num"] not in ((lesson_time.lesson_num for lesson_time in db.session.query(LessonTime).all())):
            result["errors"]["lesson_num"] = "Недопустимый номер пары"

        try:
            if rj["type"] not in LessonTypes:
                result["errors"]["type"] = "Неверное значение"
        except Exception:
            result["errors"]["type"] = "Неверный формат поля"

        try:
            if rj["form"] not in LessonForms:
                result["errors"]["form"] = "Неверное значение"
        except Exception:
            result["errors"]["form"] = "Неверный формат поля"

        upsert = rj.get("upsert", False)
        student_mark_active = False
        if "student_mark_active" in rj:
            if isinstance(rj["student_mark_active"], bool):
                student_mark_active = rj["student_mark_active"]
                # validate student_mark_active
                if student_mark_active:
                    if "form" not in result["errors"] and rj["form"] != 'remote':
                        result["errors"]["student_mark_active"] = "Включить отметку посещаемости студентом можно только на дистанционных занятиях"
                    elif "date" not in result["errors"] and "lesson_num" not in result["errors"] and not _validate_student_mark_active(lesson_date=lesson_date, lesson_num=rj["lesson_num"]):
                        result["errors"]["student_mark_active"] = "Включить отметку посещаемости студентом можно только на занятии, проходящем в текущий момент времени"
            else:
                result["errors"]["student_mark_active"] = "Неверный формат поля"


        default_attendance = 0 if student_mark_active else 1
        if "default_attendance" in rj:
            if isinstance(rj["default_attendance"], bool):
                default_attendance = 1 if rj["default_attendance"] else 0
            elif isinstance(rj["default_attendance"], int) and rj["default_attendance"] in (0, 1):
                default_attendance = rj["default_attendance"]
            else:
                result["errors"]["default_attendance"] = "Неверный формат поля"

        other_lesson = None

        # unique_check date and lesson_num for teacher_id
        if "date" not in result["errors"] and "lesson_num" not in result["errors"]:
            other_lesson = db.session.query(Lesson).filter_by(date=lesson_date, lesson_num=rj["lesson_num"], teacher_id=teacher.id).one_or_none()
            if other_lesson is not None and not upsert:
                result["errors"]["lesson_num"] = "Вы уже создали занятие в указанное время"
                result["other_lesson"] = {
                    "id": other_lesson.id,
                    "type": other_lesson.type,
                    "form": other_lesson.form,
                    "comment": other_lesson.comment,
                    "student_mark_active": student_mark_active,
                    "curriculum_units": [curriculum_unit_to_json(lcu.curriculum_unit) for lcu in other_lesson.lesson_curriculum_units ]
                }

        if "comment" in rj:
            if rj["comment"] is not None:
                if not isinstance(rj["comment"], str):
                    result["errors"]["comment"] = "Неверный формат поля"
                elif len(rj["comment"]) > 4000:
                    result["errors"]["comment"] = "Длина поля не может быть больше 4000 символов"

        if "comment_hidden" in rj:
            if rj["comment_hidden"] is not None:
                if not isinstance(rj["comment_hidden"], str):
                    result["errors"]["comment_hidden"] = "Неверный формат поля"
                elif len(rj["comment_hidden"]) > 4000:
                    result["errors"]["comment_hidden"] = "Длина поля не может быть больше 4000 символов"

        cu_map = dict(((cu.id, cu) for cu in curriculum_units))

        # {"curriculum_units": [{"id":id, "group_subnums": [null, true, false]}]}
        if other_lesson is None:
            try:
                if len(rj["curriculum_units"]) == 0:
                    result["errors"]["curriculum_units"] = "Пустой список"
                else:
                    subject_id = None
                    curriculum_unit_group_id = None
                    valid_union = True
                    lessons_start_date = None
                    session_start_date = None

                    for i, cu_row in enumerate(rj["curriculum_units"]):
                        if cu_row["id"] not in cu_map:
                            result["errors"]["curriculum_units"] = "Отсутствует единица учебного плана id=%d у текущего преподавателя" % cu_row["id"]
                            break
                        cu = cu_map[cu_row["id"]]
                        if i == 0:
                            subject_id = cu.subject.id
                            curriculum_unit_group_id = cu.curriculum_unit_group_id
                        else:
                            if not((curriculum_unit_group_id is not None and cu.curriculum_unit_group_id is not None and curriculum_unit_group_id == cu.curriculum_unit_group_id) or (subject_id == cu.subject.id)):
                                valid_union = False

                        if cu.stud_group.sub_count > 1:
                            valid_group_subnums = False
                            for g_subnum in range(1, cu.stud_group.sub_count+1):
                                if isinstance(cu_row["group_subnums"][g_subnum], bool):
                                    if cu_row["group_subnums"][g_subnum]:
                                        valid_group_subnums = True
                                else:
                                    valid_group_subnums = False
                                    break
                        else:
                            valid_group_subnums = True

                        if not valid_group_subnums:
                            result["errors"]["curriculum_units"] = "Неверный формат поля 'group_subnums' для curriculum_unit_id=" % cu_row["id"]
                            break

                        # lesson date check
                        if "date" not in result["errors"] and lesson_date is not None:
                            if cu.stud_group.lessons_start_date is not None and (lessons_start_date is None or cu.stud_group.lessons_start_date > lessons_start_date):
                                lessons_start_date = cu.stud_group.lessons_start_date
                            if cu.stud_group.session_start_date is not None and (session_start_date is None or cu.stud_group.session_start_date < session_start_date):
                                session_start_date = cu.stud_group.session_start_date

                            # Проверка нет ли занятия в это время (lesson_date и lesson_num) у группы (с учётом подгрупп)
                            if "lesson_num" not in result["errors"]:
                                lcu_others = db.session.query(LessonCurriculumUnit).join(Lesson, LessonCurriculumUnit.lesson_id == Lesson.id)\
                                    .join(CurriculumUnit, LessonCurriculumUnit.curriculum_unit_id == CurriculumUnit.id)\
                                    .filter(Lesson.date == lesson_date).filter(Lesson.lesson_num == rj["lesson_num"])\
                                    .filter(CurriculumUnit.stud_group_id == cu.stud_group_id).all()
                                for lcu_other in lcu_others:
                                    if cu.stud_group.sub_count == 0 or any((fl_sub_g1 and fl_sub_g2 for fl_sub_g1, fl_sub_g2 in zip(lcu_other.stud_group_subnums_map, cu_row["group_subnums"]))):
                                        sg_other = lcu_other.curriculum_unit.stud_group
                                        person_other: Person = lcu_other.lesson.teacher.person
                                        result["errors"]["lesson_num"] = "У группы %d курс %d %s уже %s занятие '%s' в указанное время" % (sg_other.num, sg_other.course, person_other.full_name, 'создала' if person_other.gender == "W" else "создал", lcu_other.curriculum_unit.subject.name)
                                        if person_other.email:
                                            result["errors"]["lesson_num"] +='. E-mail: %s' % person_other.email
                                        if person_other.phone:
                                            result["errors"]["lesson_num"] += '. Тел.: %s' % person_other.phone_format

                    if not valid_union:
                        result["errors"]["curriculum_units"] = "Перечисленные единицы учебного плана нельзя объединять для одного занятия"

                    if "date" not in result["errors"] and lesson_date is not None:
                        if lessons_start_date is not None and lesson_date < lessons_start_date:
                            result["errors"]["date"] = "Дата занятия раньше даты начала занятий для группы"
                        if session_start_date is not None and session_start_date <= lesson_date:
                            result["errors"]["date"] = "Дата занятия позже начала экзаменационной сессии"

            except Exception as e:
                result["errors"]["curriculum_units"] = "Неверный формат поля"
        elif upsert:
            # Проверка на одинакову передачу curriculum_units
            j_cus_old = []
            for lcu in other_lesson.lesson_curriculum_units:
                j_cus_old.append({
                    "id": lcu.curriculum_unit_id,
                    "group_subnums": lcu.stud_group_subnums_map
                })
            j_cus_old.sort(key=lambda lcu: lcu["id"])
            try:
                j_cus_new = []
                for cu_row in rj["curriculum_units"]:
                    cu = cu_map[cu_row["id"]] if cu_row["id"] in cu_map else None
                    j_cus_new.append({
                        "id": cu_row["id"],
                        "group_subnums": [True] if cu is not None and cu.stud_group.sub_count == 0 else cu_row["group_subnums"]
                    })
                j_cus_new.sort(key=lambda lcu: lcu["id"])
                if json.dumps(j_cus_old) != json.dumps(j_cus_new):
                    result["errors"]["curriculum_units"] = "Не совпадает набор curriculum_units с существующим занятием"
            except Exception:
                result["errors"]["curriculum_units"] = "Неверный формат поля"


        if len(result["errors"]) == 0:
            del result["errors"]
        else:
            return jsonify(result), 400

        # END Validate
        if upsert and other_lesson:
            lesson = other_lesson
        else:
            lesson = Lesson(teacher_id=teacher_id, date=lesson_date, lesson_num=rj["lesson_num"], type=rj["type"], form=rj["form"], comment=rj["comment"] if "comment" in rj else None, comment_hidden=rj["comment_hidden"] if "comment_hidden" in rj else None,student_mark_active=student_mark_active)
            db.session.add(lesson)
            db.session.flush()

        result["lesson_id"] = lesson.id
        result["students"] = []

        def _student_to_json(s: Student, cu: CurriculumUnit, lesson_student: Lesson):
            return {
                "id": s.id,
                "curriculum_unit_id": cu.id,
                "course": s.course,
                "semester": s.semester,
                "group_num": cu.stud_group.num,
                "group_subnum": s.stud_group_subnum if s.stud_group_id is not None and s.stud_group_id == cu.stud_group_id else None,
                "surname": s.person.surname,
                "surname_old": s.person.surname_old,
                "firstname": s.person.firstname,
                "middlename": s.person.middlename,
                "gender": s.person.gender,
                "attendance": lesson_student.attendance
            }

        if upsert and other_lesson:
            # exist lesson
            for lesson_cu in lesson.lesson_curriculum_units:
                cu = lesson_cu.curriculum_unit
                for lesson_student in lesson_cu.lesson_students:
                    s = lesson_student.student
                    result["students"].append(_student_to_json(s, cu, lesson_student))
        else:
            # new lesson
            for cu_row in rj["curriculum_units"]:
                cu = cu_map[cu_row["id"]]
                lesson_cu = LessonCurriculumUnit(lesson_id=lesson.id, curriculum_unit=cu, stud_group_subnums=0)
                if cu.stud_group.sub_count > 1:
                    lesson_cu.stud_group_subnums_map = cu_row["group_subnums"]
                db.session.add(lesson_cu)
                students_id_exclude = tuple((m.student_id for m in cu.att_marks if m.exclude))
                for s in cu.stud_group.students:
                    s: Student = s
                    if cu.subject_id in ((sp.replaced_subject_id for sp in s.particular_subjects if sp.replaced_subject_id is not None)):
                        continue
                    if s.id in students_id_exclude:
                        continue
                    if not lesson_cu.stud_group_subnums_map[s.stud_group_subnum]:
                        continue

                    lesson_student = LessonStudent(lesson_id=lesson.id, curriculum_unit_id=cu.id, student_id=s.id, attendance=default_attendance)
                    db.session.add(lesson_student)

                    result["students"].append(_student_to_json(s, cu, lesson_student))

            db.session.commit()
        result["ok"] = True

    return jsonify(result)


@app.route('/api/lessons/<int:lesson_id>', methods=["GET", "POST", "DELETE"])
@check_auth_4_api()
def api_lessons(lesson_id):
    current_user = get_current_user()
    result = {"ok": False}
    lesson = db.session.query(Lesson).filter(Lesson.id == lesson_id).one_or_none()
    if lesson is None:
        result["error"] = "Занятие не найдено"
        return jsonify(result), 404

    lesson_rights = lesson.get_rights(current_user)
    if not lesson_rights["read"]:
        result["error"] = "Нет прав доступа"
        return jsonify(result), 403

    teacher: Teacher = lesson.teacher
    if request.method == "GET":
        # снять возможность отметиться студенту, если занятие уже закончилось
        if lesson.student_mark_active and not _validate_student_mark_active(lesson_date=lesson.date, lesson_num=lesson.lesson_num):
            lesson.student_mark_active = False
            db.session.add(lesson)
            db.session.commit()

        result["_allow_write"] = lesson_rights["write"]
        result["lesson_id"] = lesson.id
        result["date"] = lesson.date.isoformat()
        result["lesson_num"] = lesson.lesson_num
        result["type"] = lesson.type
        result["form"] = lesson.form
        result["comment"] = lesson.comment
        if lesson_rights["comment_hidden"]:
            result["comment_hidden"] = lesson.comment_hidden
        result["student_mark_active"] = lesson.student_mark_active
        result["teacher"] = {
            "id": teacher.id,
            "surname": teacher.person.surname,
            "firstname": teacher.person.firstname,
            "middlename": teacher.person.middlename
        }

        result["curriculum_units"] = []
        result["students"] = []

        for lesson_curriculum_unit in lesson.lesson_curriculum_units:
            cu: CurriculumUnit = lesson_curriculum_unit.curriculum_unit
            result["curriculum_units"].append(curriculum_unit_to_json(cu))
            for lesson_student in lesson_curriculum_unit.lesson_students:
                s: Student = lesson_student.student
                lesson_student_j = {
                    "id": s.id,
                    "curriculum_unit_id": cu.id,
                    "group_subnum": s.stud_group_subnum if s.stud_group_id == cu.stud_group_id else None,
                    "surname": s.person.surname,
                    "surname_old": s.person.surname_old,
                    "firstname": s.person.firstname,
                    "middlename": s.person.middlename,
                    "gender": s.person.gender,
                    "attendance": lesson_student.attendance,
                    "comment": lesson_student.comment
                }
                if lesson_rights["comment_hidden"]:
                    lesson_student_j["comment_hidden"] = lesson_student.comment_hidden
                result["students"].append(lesson_student_j)

        result["ok"] = True

    if request.method in ("POST", "DELETE"):
        if not lesson_rights["write"]:
            result["error"] = "Нет прав доступа"
            return jsonify(result), 403

    if request.method == "POST":
        # Validate
        try:
            rj = request.json
        except:
            rj = None
        if rj is None:
            result["error"] = "Неверный формат JSON"
            result["error_hidden"] = True
            return jsonify(result), 400

        result["errors"] = {}

        lesson_date = lesson.date
        if "date" in rj:
            try:
                lesson_date = date.fromisoformat(rj["date"])
                today = date.today()
                if lesson_date > today:
                    result["errors"]["date"] = "Дата не может быть указана в будущем"
                elif lesson_date.isoweekday() == 7:
                    result["errors"]["date"] = "День недели не может быть воскресеньем"
                elif db.session.query(Holiday).filter_by(date=lesson_date).count() > 0:
                    result["errors"]["date"] = "Указан праздничный день"
            except:
                result["errors"]["date"] = "Неверный формат поля"

            # lesson date check
            if "date" not in result["errors"]:
                lessons_start_date = None
                session_start_date = None
                for lcu in lesson.lesson_curriculum_units:
                    stud_group = lcu.curriculum_unit.stud_group
                    if stud_group.lessons_start_date is not None and (lessons_start_date is None or stud_group.lessons_start_date > lessons_start_date):
                        lessons_start_date = stud_group.lessons_start_date
                    if stud_group.session_start_date is not None and (session_start_date is None or stud_group.session_start_date < session_start_date):
                        session_start_date = stud_group.session_start_date

                if lessons_start_date is not None and lesson_date < lessons_start_date:
                    result["errors"]["date"] = "Дата занятия раньше даты начала занятий для группы"
                if session_start_date is not None and session_start_date <= lesson_date:
                    result["errors"]["date"] = "Дата занятия позже начала экзаменационной сессии"

            # end lesson date check

        lesson_num = lesson.lesson_num
        if "lesson_num" in rj:
            if not isinstance(rj["lesson_num"], int):
                result["errors"]["lesson_num"] = "Неверный формат поля"
            elif rj["lesson_num"] not in ((lesson_time.lesson_num for lesson_time in db.session.query(LessonTime).all())):
                result["errors"]["lesson_num"] = "Недопустимый номер пары"
            else:
                lesson_num = rj["lesson_num"]

        # unique_check date and lesson_num for teacher_id
        if (lesson_num, lesson_date) != (lesson.lesson_num, lesson.date) and "date" not in result["errors"] and "lesson_num" not in result["errors"]:
            other_lesson = db.session.query(Lesson).filter(Lesson.id != lesson.id).filter_by(date=lesson_date, lesson_num=lesson_num, teacher_id=lesson.teacher_id).one_or_none()

            if other_lesson is not None:
                result["errors"]["lesson_num"] = "Вы уже создали занятие в указанное время"
                result["other_lesson"] = {
                    "id": other_lesson.id,
                    "type": other_lesson.type,
                    "form": other_lesson.form,
                    "comment": other_lesson.comment,
                    "curriculum_units": [curriculum_unit_to_json(lcu.curriculum_unit) for lcu in other_lesson.lesson_curriculum_units ]
                }
            else:
                for lcu in lesson.lesson_curriculum_units:
                    cu: CurriculumUnit = lcu.curriculum_unit
                    lcu_others = db.session.query(LessonCurriculumUnit)\
                            .join(Lesson, LessonCurriculumUnit.lesson_id == Lesson.id)\
                            .join(CurriculumUnit, LessonCurriculumUnit.curriculum_unit_id == CurriculumUnit.id)\
                            .filter(Lesson.id != lesson.id)\
                            .filter(Lesson.date == lesson_date).filter(Lesson.lesson_num == lesson_num)\
                            .filter(CurriculumUnit.stud_group_id == cu.stud_group_id).all()
                    for lcu_other in lcu_others:
                        if cu.stud_group.sub_count == 0 or any((fl_sub_g1 and fl_sub_g2 for fl_sub_g1, fl_sub_g2 in zip(lcu_other.stud_group_subnums_map, lcu.stud_group_subnums_map))):
                            sg_other = lcu_other.curriculum_unit.stud_group
                            person_other: Person = lcu_other.lesson.teacher.person
                            result["errors"]["lesson_num"] = "У группы %d курс %d %s уже %s занятие '%s' в указанное время" % (sg_other.num, sg_other.course, person_other.full_name, 'создала' if person_other.gender == "W" else "создал", lcu_other.curriculum_unit.subject.name)
                            if person_other.email:
                                result["errors"]["lesson_num"] += '. E-mail: %s' % person_other.email
                            if person_other.phone:
                                result["errors"]["lesson_num"] += '. Тел.: %s' % person_other.phone_format

        if "type" in rj:
            if not isinstance(rj["type"], str) or rj["type"] not in LessonTypes:
                result["errors"]["type"] = "Неверное значение"

        if "form" in rj:
            if not isinstance(rj["form"], str) or rj["form"] not in LessonForms:
                result["errors"]["form"] = "Неверное значение"

        if "comment" in rj:
            if rj["comment"] is not None:
                if not isinstance(rj["comment"], str):
                    result["errors"]["comment"] = "Неверный формат поля"
                elif len(rj["comment"]) > 4000:
                    result["errors"]["comment"] = "Длина поля не может быть больше 4000 символов"

        if lesson_rights["comment_hidden"] and "comment_hidden" in rj:
            if rj["comment_hidden"] is not None:
                if not isinstance(rj["comment_hidden"], str):
                    result["errors"]["comment_hidden"] = "Неверный формат поля"
                elif len(rj["comment_hidden"]) > 4000:
                    result["errors"]["comment_hidden"] = "Длина поля не может быть больше 4000 символов"

        if "student_mark_active" in rj:
            if not isinstance(rj["student_mark_active"], bool):
                result["errors"]["student_mark_active"] = "Неверный формат поля"
            else:
                if rj["student_mark_active"]:
                    if "form" not in result["errors"] and rj.get("form", lesson.form) != 'remote':
                        result["errors"]["student_mark_active"] = "Включить отметку посещаемости студентом можно только на дистанционных занятиях"
                    elif "date" not in result["errors"] and "lesson_num" not in result["errors"] and not _validate_student_mark_active(lesson_date=lesson_date, lesson_num=lesson_num):
                        result["errors"]["student_mark_active"] = "Включить отметку посещаемости студентом можно только на занятии, проходящем в текущий момент времени"

        lesson_students_map = {}
        if "students" in rj:
            if not isinstance(rj["students"], list):
                result["errors"]["students"] = "Неверный формат поля"
            else:
                result["errors"]["students"] = {}
                for s_row in rj["students"]:
                    s_id = None
                    try:
                        s_id = s_row["id"]
                        lesson_student = db.session.query(LessonStudent).filter(LessonStudent.lesson_id == lesson_id).filter(LessonStudent.student_id == s_id).one_or_none()
                        if lesson_student is None:
                            result["errors"]["students"][s_id] = "Не найдена запись"
                        else:
                            lesson_students_map[s_id] = lesson_student
                            if "attendance" in s_row:
                                # Для обратной совместимости
                                if isinstance(s_row["attendance"], bool):
                                    s_row["attendance"] = 1 if s_row["attendance"] else 0

                                if not isinstance(s_row["attendance"], int) or s_row["attendance"] not in (0, 1, 2):
                                    result["errors"]["students"][s_id] = "Неверный формат поля attendance"

                            if "comment" in s_row:
                                if s_row["comment"] is not None:
                                    if not isinstance(s_row["comment"], str):
                                        result["errors"]["students"][s_id] = "Неверный формат поля comment"
                                    elif len(s_row["comment"]) > 4000:
                                        result["errors"]["students"][s_id] = "Поле comment не должно быть больше 4000 символов"

                            if lesson_rights["comment_hidden"] and "comment_hidden" in s_row:
                                if s_row["comment_hidden"] is not None:
                                    if not isinstance(s_row["comment_hidden"], str):
                                        result["errors"]["students"][s_id] = "Неверный формат поля comment_hidden"
                                    elif len(s_row["comment_hidden"]) > 4000:
                                        result["errors"]["students"][s_id] = "Поле comment_hidden не должно быть больше 4000 символов"

                    except:
                        result["errors"]["students"][s_id] = "Неверный формат поля"

                if len(result["errors"]["students"]) == 0:
                    del result["errors"]["students"]

        if len(result["errors"]) == 0:
            del result["errors"]
        else:
            return jsonify(result), 400
        # END Validate

        if "date" in rj:
            lesson.date = date.fromisoformat(rj["date"])

        if "lesson_num" in rj:
            lesson.lesson_num = rj["lesson_num"]

        if "type" in rj:
            lesson.type = rj["type"]

        if "form" in rj:
            lesson.form = rj["form"]

        if "comment" in rj:
            lesson.comment = rj["comment"]

        if lesson_rights["comment_hidden"] and "comment_hidden" in rj:
            lesson.comment_hidden = rj["comment_hidden"]

        if "student_mark_active" in rj:
            lesson.student_mark_active = rj["student_mark_active"]

        db.session.add(lesson)

        if "students" in rj:
            for s_row in rj["students"]:
                lesson_student = lesson_students_map[s_row["id"]]
                if "attendance" in s_row:
                    lesson_student.attendance = s_row["attendance"]
                if "comment" in s_row:
                    lesson_student.comment = s_row["comment"]
                if lesson_rights["comment_hidden"] and "comment_hidden" in s_row:
                    lesson_student.comment_hidden = s_row["comment_hidden"]
                db.session.add(lesson_student)

        db.session.commit()
        result["ok"] = True

    if request.method == "DELETE":
        for cu_lesson in lesson.lesson_curriculum_units:
            for lesson_student in cu_lesson.lesson_students:
                db.session.delete(lesson_student)
            db.session.delete(cu_lesson)
        db.session.delete(lesson)
        db.session.commit()
        db.session.flush()
        result["ok"] = True

    return jsonify(result)


@app.route('/api/lessons/<int:lesson_id>/<int:student_id>', methods=["GET", "POST"])
@check_auth_4_api()
def api_lessons_student(lesson_id, student_id):
    current_user = get_current_user()
    result = {"ok": False}
    lesson_student = db.session.query(LessonStudent).filter(LessonStudent.lesson_id == lesson_id).filter(LessonStudent.student_id == student_id).one_or_none()
    if lesson_student is None:
        result['error'] = "Запись не найдена"
        return jsonify(result), 404

    lesson = lesson_student.lesson_curriculum_unit.lesson

    lesson_rights = lesson.get_rights(current_user)

    # Если разрешена отметка Включить посещаемости студентом
    if lesson.student_mark_active and student_id in (s.id for s in current_user.students) and _validate_student_mark_active(lesson_date=lesson.date, lesson_num=lesson.lesson_num):
        lesson_rights["read"] = True
        lesson_rights["mark_attendance"] = True

    if not lesson_rights["read"]:
        result["error"] = "Нет прав доступа"
        return jsonify(result), 403

    if request.method == "GET":
        result["_allow_write"] = lesson_rights["write"]
        result["lesson_id"] = lesson.id
        result["curriculum_unit_id"] = lesson_student.curriculum_unit_id
        result["student_id"] = lesson_student.student_id
        result["attendance"] = lesson_student.attendance
        result["comment"] = lesson_student.comment
        if lesson_rights["comment_hidden"]:
            result["comment_hidden"] = lesson_student.comment_hidden

        result["ok"] = True

    if request.method == "POST":
        if (not lesson_rights["write"]) and (not lesson_rights["mark_attendance"]):
            result["error"] = "Нет прав доступа"
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

        result["errors"] = {}

        if "attendance" in rj:
            # Для обратной совместимости
            if isinstance(rj["attendance"], bool):
                rj["attendance"] = 1 if rj["attendance"] else 0

            if not isinstance(rj["attendance"], int) or rj["attendance"] not in (0, 1, 2):
                result["errors"]["attendance"] = "Неверный формат поля"

        if "comment" in rj:
            if rj["comment"] is not None:
                if not isinstance(rj["comment"], str):
                    result["errors"]["comment"] = "Неверный формат поля"
                elif len(rj["comment"]) > 4000:
                    result["errors"]["comment"] = "Поле не должно быть больше 4000 символов"

        if lesson_rights["comment_hidden"] and "comment_hidden" in rj:
            if rj["comment_hidden"] is not None:
                if not isinstance(rj["comment_hidden"], str):
                    result["errors"]["comment_hidden"] = "Неверный формат поля"
                elif len(rj["comment_hidden"]) > 4000:
                    result["errors"]["comment_hidden"] = "Поле не должно быть больше 4000 символов"

        if len(result["errors"]) == 0:
            del result["errors"]
        else:
            return jsonify(result), 400
        # END Validate

        if "attendance" in rj:
            lesson_student.attendance = rj["attendance"]
        if "comment" in rj:
            lesson_student.comment = rj["comment"]
        if lesson_rights["comment_hidden"] and "comment_hidden" in rj:
            lesson_student.comment_hidden = rj["comment_hidden"]

        db.session.add(lesson_student)
        db.session.commit()

        if "attendance" in rj:
            att_mark = db.session.query(AttMark).filter(AttMark.student_id == lesson_student.student_id).filter(AttMark.curriculum_unit_id == lesson_student.curriculum_unit_id).one_or_none()
            if att_mark is not None:
                result["att_mark"] = att_mark_to_json(att_mark, current_user, add_comment_hidden=lesson_rights["comment_hidden"])
            result["attendance_pct"] = lesson_student.lesson_curriculum_unit.attendance_pct

        result["ok"] = True

    return jsonify(result)


def _api_lessons_curriculum_units(current_user, rj):
    result = {
        "ok": False
    }
    cu_map = {}
    allow_new_lesson = True
    # Validate
    try:
        if len(rj["curriculum_units"]) == 0:
            result['error'] = "Пустой список 'curriculum_units'"
            result["error_hidden"] = True
            result['error_code'] = 400
            return result

        year = None
        session_num = None
        stud_grop_ids = []

        for cu_row in rj["curriculum_units"]:
            cu: CurriculumUnit = db.session.query(CurriculumUnit).filter(
                CurriculumUnit.id == cu_row["id"]).one_or_none()
            if cu is None:
                result['error'] = "Запись с id=%d не найдена" % cu_row["id"]
                result["error_hidden"] = True
                result['error_code'] = 404
                return result
            cu_map[cu_row["id"]] = cu
            stud_group: StudGroup = cu.stud_group

            _allow_read = False
            _allow_new_lesson = False

            if current_user.admin_user is not None and current_user.admin_user.active:
                _allow_read = True
                _allow_new_lesson = True
            elif current_user.teacher is not None and current_user.teacher.active and (cu.teacher_id == current_user.teacher.id or any((t.id == current_user.teacher.id for t in cu.practice_teachers))):
                _allow_read = True
                _allow_new_lesson = True
            else:
                if stud_group.get_rights(current_user)["read_marks"]:
                    _allow_read = True

            if _allow_new_lesson and (cu.pass_department or cu.closed or (not stud_group.active)):
                _allow_new_lesson = False

            if not _allow_read:
                result["error"] = "Нет прав доступа"
                result['error_code'] = 403
                return result

            allow_new_lesson = allow_new_lesson and _allow_new_lesson
            group_subnums = cu_row.get("group_subnums", None)

            if group_subnums is not None:
                if not stud_group.active:
                    result["error"] = "Недопустимо указывать поле 'group_subnums'"
                    result["error_hidden"] = True
                    result['error_code'] = 400
                    return result
                if stud_group.sub_count > 1:
                    valid_group_subnums = False
                    try:
                        for g_subnum in range(1, cu.stud_group.sub_count + 1):
                            if isinstance(group_subnums[g_subnum], bool):
                                if group_subnums[g_subnum]:
                                    valid_group_subnums = True
                            else:
                                valid_group_subnums = False
                                break
                    except:
                        valid_group_subnums = False
                    if not valid_group_subnums:
                        result["error"] = "Неверный формат поля 'group_subnums'"
                        result["error_hidden"] = True
                        result['error_code'] = 400
                        return result
                else:
                    del cu_row["group_subnums"]

            # union check
            if year is None or session_num is None:
                year = stud_group.year
                session_num = stud_group.session_num
            elif (year, session_num) != (stud_group.year, stud_group.session_num):
                result["error"] = "Перечисленные единицы учебного плана нельзя объединять в одну ведомость"
                result['error_code'] = 400
                return result

            if stud_group.id in stud_grop_ids:
                result["error"] = "Перечисленные единицы учебного плана нельзя объединять в одну ведомость"
                result['error_code'] = 400
                return result
            else:
                stud_grop_ids.append(stud_group.id)

    except:
        result['error'] = "Неправильный формат поля 'curriculum_units'"
        result['error_hidden'] = True
        result['error_code'] = 400
        return result

    if "show_exclude_students" in rj and not isinstance(rj["show_exclude_students"], bool):
        result['error'] = "Неправильный формат поля 'show_exclude_students'"
        result['error_hidden'] = True
        result['error_code'] = 400
        return result

    show_exclude_students = rj.get("show_exclude_students", True)

    # End Validate

    result["_allow_new_lesson"] = allow_new_lesson
    result["curriculum_units"] = [curriculum_unit_to_json(cu_map[cu_row["id"]]) for cu_row in rj["curriculum_units"]]
    result["curriculum_unit_others"] = []
    result["students"] = []
    result["lessons"] = []

    students_exclude_ids = []
    students_ids = []
    curriculum_unit_other_ids = []

    def _student_to_json(s, sg=None):
        s_json = {
            "id": s.id,
            "surname": s.surname,
            "surname_old": s.person.surname_old,
            "firstname": s.firstname,
            "middlename": s.middlename,
            "gender": s.person.gender
        }
        if stud_group.active and stud_group.sub_count > 1 \
                and s.stud_group_id is not None and s.stud_group_id == stud_group.id:
            s_json["group_subnum"] = s.stud_group_subnum

        if sg is not None:
            s_json.update({
                "course": sg.course,
                "semester": sg.semester,
                "group_num": sg.num
            })

        return s_json

    for cu_row in rj["curriculum_units"]:
        cu = cu_map[cu_row["id"]]
        stud_group = cu.stud_group
        group_subnums = cu_row.get("group_subnums", None)
        for att_mark in cu.att_marks:

            if not show_exclude_students and att_mark.att_mark_id in cu.att_marks_readonly_ids:
                students_exclude_ids.append(att_mark.student_id)
                continue

            if att_mark.student.stud_group_subnum is not None and att_mark.student.stud_group_id == cu.stud_group_id:
                if group_subnums is not None and not group_subnums[att_mark.student.stud_group_subnum]:
                    continue

            s_j = _student_to_json(att_mark.student, cu.stud_group)
            s_j["att_mark"] = att_mark_to_json(att_mark, current_user)
            students_ids.append(att_mark.student_id)
            result["students"].append(s_j)

        if stud_group.active and (not cu.pass_department) and (not cu.closed):
            att_mark_news = []
            for s in stud_group.students:
                if not show_exclude_students and s.id in students_exclude_ids:
                    continue

                if group_subnums is not None and s.stud_group_subnum is not None and not group_subnums[s.stud_group_subnum]:
                    continue

                if cu.subject_id in ((sp.replaced_subject_id for sp in s.particular_subjects if sp.replaced_subject_id is not None)):
                    continue
                if s.id not in students_ids:
                    students_ids.append(s.id)
                    att_mark = AttMark(curriculum_unit=cu, student=s)
                    db.session.add(att_mark)
                    att_mark_news.append(att_mark)

            if len(att_mark_news) > 0:
                db.session.flush()
                for att_mark in att_mark_news:
                    hist_save_controller(db.session, att_mark, current_user)
                db.session.commit()
                for att_mark in att_mark_news:
                    s_j = _student_to_json(att_mark.student, cu.stud_group)
                    s_j["att_mark"] = att_mark_to_json(att_mark, current_user)
                    students_ids.append(att_mark.student.id)
                    result["students"].append(s_j)

        for lcu in db.session.query(LessonCurriculumUnit).join(Lesson, LessonCurriculumUnit.lesson_id == Lesson.id).filter(
                LessonCurriculumUnit.curriculum_unit_id == cu.id).order_by(Lesson.date, Lesson.lesson_num):
            if group_subnums is not None:
                group_subnums_intersect = False
                for g_subnum in range(1, lcu.curriculum_unit.stud_group.sub_count + 1):
                    if lcu.stud_group_subnums_map[g_subnum] and group_subnums[g_subnum]:
                        group_subnums_intersect = True

                if not group_subnums_intersect:
                    continue

            lesson: Lesson = lcu.lesson
            lesson_rights = lesson.get_rights(current_user)
            # снять возможность отметиться студенту, если занятие уже закончилось
            if lesson.student_mark_active and not _validate_student_mark_active(lesson_date=lesson.date, lesson_num=lesson.lesson_num):
                lesson.student_mark_active = False
                db.session.add(lesson)
                db.session.commit()

            teacher: Teacher = lesson.teacher
            lesson_j = {
                "_allow_write": lesson_rights["write"],
                "id": lesson.id,
                "date": lesson.date.isoformat(),
                "lesson_num": lesson.lesson_num,
                "type": lesson.type,
                "form": lesson.form,
                "student_mark_active": lesson.student_mark_active,
                "comment": lesson.comment,
                "teacher": teacher_to_json(teacher),
                "curriculum_unit_other_ids": [],
                "attendance_pct": lcu.attendance_pct,
                "students": []
            }

            if lesson_rights["comment_hidden"]:
                lesson_j["comment_hidden"] = lesson.comment_hidden

            for _lcu in lesson.lesson_curriculum_units:
                if _lcu.curriculum_unit_id not in cu_map:
                    lesson_j["curriculum_unit_other_ids"].append(_lcu.curriculum_unit_id)
                    if _lcu.curriculum_unit_id not in curriculum_unit_other_ids:
                        curriculum_unit_other_ids.append(_lcu.curriculum_unit_id)
                        result["curriculum_unit_others"].append(curriculum_unit_to_json(_lcu.curriculum_unit))

            for lesson_student in lcu.lesson_students:
                s = lesson_student.student

                if not show_exclude_students and s.id in students_exclude_ids:
                    continue

                if s.stud_group_subnum is not None and s.stud_group_id == cu.stud_group_id:
                    if group_subnums is not None and not group_subnums[s.stud_group_subnum]:
                        continue

                if lesson_student.student_id not in students_ids:
                    students_ids.append(lesson_student.student_id)
                    result["students"].append(_student_to_json(s))

                lesson_student_j = {
                    "id": lesson_student.student_id,
                    "attendance": lesson_student.attendance,
                    "comment": lesson_student.comment
                }
                if lesson_rights["comment_hidden"]:
                    lesson_student_j["comment_hidden"] = lesson_student.comment_hidden
                lesson_j["students"].append(lesson_student_j)
            result["lessons"].append(lesson_j)

    result["students"].sort(key=lambda s:(s['surname'], s['firstname'], s['middlename'], s['id']))

    result["ok"] = True
    return result


@app.route('/api/lessons/curriculum_unit/<int:curriculum_unit_id>', methods=["GET"])
@check_auth_4_api()
def api_lessons_curriculum_unit(curriculum_unit_id):
    current_user = get_current_user()
    show_exclude_students = request.args.get("show_exclude_students", "True") == "True"

    result = _api_lessons_curriculum_units(current_user, {
        "curriculum_units": [
            {"id": curriculum_unit_id}
        ],
        "show_exclude_students": show_exclude_students
    })
    if "curriculum_units" in result and len(result["curriculum_units"]) == 1:
        result["curriculum_unit"] = result["curriculum_units"][0]
        del result["curriculum_units"]
    http_code = result.pop("error_code", 200)

    return jsonify(result), http_code


@app.route('/api/lessons/curriculum_units', methods=["POST"])
@check_auth_4_api()
def api_lessons_curriculum_units():
    # Validate
    try:
        rj = request.json
    except:
        rj = None
    if rj is None:
        return jsonify({
            "error": "Неверный формат JSON",
            "ok": False
        }), 400
    current_user = get_current_user()
    result = _api_lessons_curriculum_units(current_user, rj)
    http_code = result.pop("error_code", 200)

    return jsonify(result), http_code
