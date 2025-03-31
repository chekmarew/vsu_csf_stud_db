from datetime import timedelta
from flask import jsonify, request
from sqlalchemy import not_, func
from app_config import app, db
from model import Teacher, CurriculumUnit, Subject, StudGroup, Specialty, Classroom, Person, EducationLevels
from utils_auth import get_current_user
from utils_json import teacher_to_json
import utils

def _allow_write(u: Person):
    if u.admin_user is not None and u.admin_user.active:
        return True

    if u.teacher is not None and u.teacher.active and u.teacher.dean_staff:
        return True

    # temp
    if u.login in ('redin_n_a', 'savchenko_n_a', 'shatkov_p_v', 'smirnov_i_g', 'korobejnikova_a_v'):
        return True

    return False

# def scheduled_lesson_to_json(lesson):
#     return { "id": lesson.id,
#              "type" : lesson.type,
#              "form" : lesson.form,
#              "comment" : lesson.comment }

# def exam_to_json(lesson: Exam, curriculum_unit_id=False, teacher_id=True, stud_group_subnums=True):
#     exam_j = {
#         "id": exam.id,
#         "stime": exam.stime.isoformat(),
#         "etime": exam.etime.isoformat(),
#         "classroom": exam.classroom,
#         "comment": exam.comment
#     }
#     if teacher_id:
#         exam_j["teacher_id"] = exam.teacher_id
#     if curriculum_unit_id:
#         exam_j["curriculum_unit_id"] = exam.curriculum_unit_id
#     if stud_group_subnums:
#         exam_j["stud_group_subnums"] = exam.stud_group_subnums_map
#     return exam_j
# @app.route('/api/schedule/lessons', methods=["GET"])
# @utils.check_auth_4_api()
# def api_schedule_lessons():
#     current_user = get_current_user()
#     return jsonify({"ok": True})

@app.route('/api/schedule/lessons', methods=["GET"])
@utils.check_auth_4_api()
def api_schedule_lesson():

    current_user = get_current_user()
    education_level_order = None
    if "education_level_order" in request.args:
        try:
            education_level_order = int(request.args["education_level_order"])
            if education_level_order not in (1, 2):
                return jsonify({"ok": False, "error": "Неверное значение 'education_level_order'"}), 404
        except ValueError:
            return jsonify({"ok": False, "error": "Неверное значение 'education_level_order'"}), 404

    education_level = None
    if "education_level" in request.args:
        education_level = request.args["education_level"]
        if education_level not in EducationLevels:
            return jsonify({"ok": False, "error": "Неверное значение 'education_level'"}), 404

    course = None
    if "course" in request.args:
        try:
            course = int(request.args["course"])
        except ValueError:
            return jsonify({"ok": False, "error": "Неверное значение 'course'"}), 404

    archive_year, archive_semester = None, None
    if "archive_year" in request.args and "archive_semester" in request.args:
        try:
            archive_year, archive_semester = int(request.args["archive_year"]), int(request.args["archive_semester"])
        except ValueError:
            return jsonify(
                {"ok": False, "error": "Неверное значение GET-параметра 'archive_year' или 'archive_semester'"}), 400

    q_groups = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id) \
                                                .filter(StudGroup.weeks_training > 0)
    if archive_year is not None and archive_semester is not None:
        s = 0 if archive_semester == 2 else archive_semester
        q_groups = q_groups.filter(not_(StudGroup.active)) \
            .filter(StudGroup.year == archive_year) \
            .filter(func.mod(StudGroup.semester, 2) == s)
    else:
        q_groups = q_groups.filter(StudGroup.active)

    if education_level_order is not None:
        q_groups = q_groups.filter(Specialty.education_level_order == education_level_order)
    if education_level is not None:
        q_groups = q_groups.filter(Specialty.education_level == education_level)
    if course is not None:
        q_groups = q_groups.filter(func.floor((StudGroup.semester + 1) / 2) == course)

    groups = q_groups.order_by(StudGroup.year, StudGroup.semester, StudGroup.num).all()

    result = {
        "_allow_write": archive_year is None and archive_semester is None and _allow_write(current_user),
        "stud_groups": [],
        "teachers": [],
        "subjects": [],
        "ok": True,
        "periods_archive": [{"year": y, "semester": s} for y, s in utils.periods_archive()],
        "classrooms": [r.classroom for r in db.session.query(Classroom.classroom).order_by(Classroom.classroom).all()]
    }

    teacher_ids = set()
    subject_ids = set()

    for g in groups:
        g: StudGroup = g
        g_j = {
            "id": g.id,
            "course": g.course,
            "semester": g.semester,
            "num": g.num,
            "sub_count": g.sub_count,
            "specialty_code": g.specialty.code,
            "specialty_name": g.specialty.name,
            "specialization": g.specialty.specialization,
            "lessons_start_date": g.lessons_start_date.isoformat(),
            "curriculum_units": []
        }

        for cu in g.curriculum_units:

            # Включаем только те единицы, у которых сумма учебных часов больше нуля
            if (cu.hours_lect + cu.hours_pract + cu.hours_lab) <= 0:
                continue

            if cu.subject_id not in subject_ids:
                subject_ids.add(cu.subject_id)
                s = cu.subject
                result["subjects"].append({
                    "id": s.id,
                    "name": s.name,
                    "short_name": s.short_name
                })

            if cu.teacher_id not in teacher_ids:
                teacher_ids.add(cu.teacher_id)
                result["teachers"].append(teacher_to_json(cu.teacher))
            for t in cu.practice_teachers:
                if t.id not in teacher_ids:
                    teacher_ids.add(t.id)
                    result["teachers"].append(teacher_to_json(t))

            cu_j = {
                "id": cu.id,
                "curriculum_unit_group_id": cu.curriculum_unit_group_id,
                "subject_id": cu.subject_id,
                "teacher_id": cu.teacher_id,
                "practice_teacher_ids": [t.id for t in cu.practice_teachers],
                "lessons": [],
                "hours_lect": cu.hours_lect_per_week,
                "hours_pract": cu.hours_pract_per_week,
                "hours_lab": cu.hours_lab_per_week
            }
            g_j["curriculum_units"].append(cu_j)

        if len(g_j["curriculum_units"]) == 0:
            continue

        result["stud_groups"].append(g_j)

    return jsonify(result)


# @app.route('/api/schedule/exams', methods=["POST"])
# @app.route('/api/schedule/exams/<int:exam_id>', methods=["GET", "PATCH", "DELETE"])
# @utils.check_auth_4_api()
# def api_schedule_exam(exam_id=None):
#     result = {"ok": False}
#     exam = None
#     if request.method in ("GET", "PATCH", "DELETE"):
#         exam = db.session.query(Exam).filter_by(id=exam_id).one_or_none()
#         if exam is None:
#             result['error'] = "Запись не найдена"
#             return jsonify(result), 404
#     if request.method == "GET":
#         result.update(exam_to_json(exam, curriculum_unit_id=True))
#         result["ok"] = True
#         return jsonify(result)
#
#     current_user = get_current_user()
#     if not _allow_write(current_user):
#         result["error"] = "Нет прав доступа"
#         return jsonify(result), 403
#
#     if request.method in ("POST", "PATCH"):
#         # Validate
#         try:
#             rj = request.json
#         except:
#             rj = None
#         if rj is None:
#             result["error"] = "Неверный формат JSON"
#             return jsonify(result), 400
#
#         result["errors"] = {}
#
#         cu = None
#         related_curriculum_units = None
#         if request.method == "POST":
#             if "curriculum_unit_id" not in rj:
#                 result["errors"]["curriculum_unit_id"] = "Не заполнено поле"
#             elif not isinstance(rj["curriculum_unit_id"], int):
#                 result["errors"]["curriculum_unit_id"] = "Неверный формат поля"
#             else:
#                 cu: CurriculumUnit = db.session.query(CurriculumUnit).filter_by(id=rj["curriculum_unit_id"]).one_or_none()
#                 if cu is None:
#                     result["errors"]["curriculum_unit_id"] = "Не найден curriculum_unit"
#                 elif cu.mark_type != 'exam' and not cu.has_simple_mark_exam:
#                     cu = None
#                     result["errors"]["curriculum_unit_id"] = "Единица учебного плана должна иметь тип отчётности 'exam'"
#                 elif not cu.stud_group.active:
#                     cu = None
#                     result["errors"]["curriculum_unit_id"] = "Указана единица учебного плана для предыдущей экзаменационной сессии"
#                 if len(result["errors"]) > 0:
#                     return jsonify(result), 400
#
#                 if "related_curriculum_unit_ids" in rj:
#                     if not isinstance(rj["related_curriculum_unit_ids"], list) or not (all(((isinstance(id, int) and id != cu.id) for id in rj["related_curriculum_unit_ids"]))):
#                         result["errors"]["related_curriculum_unit_ids"] = "Неверный формат поля"
#                     if len(rj["related_curriculum_unit_ids"]) > 0:
#                         related_curriculum_units = db.session.query(CurriculumUnit).filter(CurriculumUnit.id.in_(rj["related_curriculum_unit_ids"])).all()
#                         for _cu in related_curriculum_units:
#                             if _cu.mark_type != 'exam' and not _cu.has_simple_mark_exam:
#                                 result["errors"]["related_curriculum_unit_ids"] = "Единица учебного плана (id=%d) должна иметь тип отчётности 'exam'" % _cu.id
#                             if not _cu.stud_group.active:
#                                 result["errors"]["related_curriculum_unit_ids"] = "Указана единица учебного плана (id=%d) для предыдущей экзаменационной сессии" % _cu.id
#                             if not (cu.subject_id == _cu.subject_id or (cu.curriculum_unit_group_id is not None and _cu.curriculum_unit_group_id is not None and cu.curriculum_unit_group_id == _cu.curriculum_unit_group_id)):
#                                 result["errors"]["related_curriculum_unit_ids"] = "Нельзя добавлять единицу учебного плана (id=%d) другого предмета" % _cu.id
#                             if cu.stud_group_id == _cu.stud_group_id:
#                                 result["errors"]["related_curriculum_unit_ids"] = "Нельзя добавлять единицу учебного плана (id=%d) из текущей студенческой группы" % _cu.id
#                             if len(_cu.exams) > 0:
#                                 result["errors"]["related_curriculum_unit_ids"] = "Нельзя добавлять единицу учебного плана (id=%d) с уже созданным экзаменом" % _cu.id
#
#                     if len(result["errors"]) > 0:
#                         return jsonify(result), 400
#
#         related_exams = None
#         if request.method == "PATCH":
#             cu = exam.curriculum_unit
#             if not cu.stud_group.active:
#                 result["error"] = "Редактирование предыдущей экзаменационной сессии недопускается"
#                 return jsonify(result), 403
#
#             if "related_exam_ids" in rj:
#                 if not isinstance(rj["related_exam_ids"], list) or not (all(((isinstance(id, int) and id != exam_id) for id in rj["related_exam_ids"]))):
#                     result["errors"]["related_exam_ids"] = "Неверный формат поля"
#                 if len(rj["related_exam_ids"]) > 0:
#                     if "teacher_id" in rj:
#                         if rj["teacher_id"] != exam.teacher_id:
#                             result["errors"]["teacher_id"] = "Недопускается редактирование, если указан 'related_exam_ids'"
#                         else:
#                             del rj["teacher_id"]
#
#                     if len(result["errors"]) > 0:
#                         return jsonify(result), 400
#
#                     related_exams = db.session.query(Exam).filter(Exam.id != exam_id).filter(Exam.id.in_(rj["related_exam_ids"])).all()
#                     for _exam in related_exams:
#                         _cu: CurriculumUnit = _exam.curriculum_unit
#                         if not _cu.stud_group.active:
#                             result["errors"]["related_exam_ids"] = "Нельзя добавлять экзамен из предыдущей экзаменационной сессии"
#                         if exam.teacher_id != _exam.teacher_id:
#                             result["errors"]["related_exam_ids"] = "Нельзя добавлять экзамен другого преподавателя"
#                         if not(cu.subject_id == _cu.subject_id or (cu.curriculum_unit_group_id is not None and _cu.curriculum_unit_group_id is not None and cu.curriculum_unit_group_id == _cu.curriculum_unit_group_id)):
#                             result["errors"]["related_exam_ids"] = "Нельзя добавлять экзамен другого предмета"
#                         if exam.stime != _exam.stime or exam.etime != _exam.etime:
#                             result["errors"]["related_exam_ids"] = "Нельзя добавлять экзамен, проходящий в другое время"
#                         if exam.classroom != _exam.classroom:
#                             result["errors"]["related_exam_ids"] = "Нельзя добавлять экзамен, проходящий в другой аудитории"
#
#                     if len(result["errors"]) > 0:
#                         return jsonify(result), 400
#                 # end if len(rj["related_exam_ids"]) > 0
#             # end related_exam
#
#         if not cu:
#             return jsonify(result), 400
#
#         if exam:
#             stud_group_subnums = exam.stud_group_subnums_map
#         else:
#             if cu.stud_group.sub_count == 0:
#                 stud_group_subnums = [True]
#             else:
#                 stud_group_subnums = [None]+[True]*cu.stud_group.sub_count
#
#         if "stud_group_subnums" in rj:
#             try:
#                 if cu.stud_group.sub_count > 1:
#                     valid_group_subnums = False
#                     for g_subnum in range(1, cu.stud_group.sub_count + 1):
#                         if isinstance(rj["stud_group_subnums"][g_subnum], bool):
#                             if rj["stud_group_subnums"][g_subnum]:
#                                 valid_group_subnums = True
#                         else:
#                             valid_group_subnums = False
#                             break
#                 else:
#                     valid_group_subnums = isinstance(rj["stud_group_subnums"][0], bool) and rj["stud_group_subnums"][0]
#                 if not valid_group_subnums:
#                     result["errors"]["stud_group_subnums"] = "Неверный формат поля"
#             except Exception as e:
#                 result["errors"]["stud_group_subnums"] = "Неверный формат поля"
#
#             if "stud_group_subnums" not in result["errors"]:
#                 stud_group_subnums = rj["stud_group_subnums"]
#
#         teacher_id = exam.teacher_id if exam else cu.teacher_id
#         if "teacher_id" in rj:
#             if not isinstance(rj["teacher_id"], int):
#                 result["errors"]["teacher_id"] = "Неверный формат поля"
#             elif rj["teacher_id"] != cu.teacher_id and rj["teacher_id"] not in [t.id for t in cu.practice_teachers]:
#                 result["errors"]["teacher_id"] = "Указан преподаватель за которым не закреплён данный curriculum_unit"
#
#             if "teacher_id" not in result["errors"]:
#                 teacher_id = rj["teacher_id"]
#
#         stime = exam.stime if exam else None
#         if "stime" in rj:
#             try:
#                 stime = datetime.fromisoformat(rj["stime"])
#             except ValueError:
#                 result["errors"]["stime"] = "Неверный формат поля"
#
#         if "stime" not in result["errors"] and stime is None:
#             result["errors"]["stime"] = "Поле обязательно для заполнения"
#
#         etime = exam.etime if exam else None
#
#         if etime is None and stime is not None:
#             etime = stime + timedelta(hours=4)
#
#         if "etime" in rj:
#             try:
#                 etime = datetime.fromisoformat(rj["etime"])
#             except ValueError:
#                 result["errors"]["etime"] = "Неверный формат поля"
#
#         if "stime" not in result["errors"] and "etime" not in result["errors"]:
#             if etime - stime < timedelta(hours=1):
#                 result["errors"]["etime"] = "Продолжительность экзамена должна быть не менее 1 часа"
#             if etime - stime > timedelta(hours=8):
#                 result["errors"]["etime"] = "Продолжительность экзамена не должна быть более 8 часов"
#
#         classroom = exam.classroom if exam else None
#         if "classroom" in rj:
#             if rj["classroom"] is not None:
#                 if not isinstance(rj["classroom"], str) or len(rj["classroom"]) > 5:
#                     result["errors"]["classroom"] = "Неверный формат поля"
#                 else:
#                     if db.session.query(Classroom).filter_by(classroom=rj["classroom"]).count() == 0:
#                         result["errors"]["classroom"] = "Аудитория не найдена в списке"
#                     else:
#                         classroom = rj["classroom"]
#             else:
#                 classroom = None
#
#         comment = exam.comment if exam else None
#         if "comment" in rj:
#             if rj["comment"] is not None:
#                 if not isinstance(rj["comment"], str) or len(rj["comment"]) > 4000:
#                     result["errors"]["comment"] = "Неверный формат поля"
#                 else:
#                     comment = rj["comment"] if rj["comment"] else None
#             else:
#                 comment = None
#
#         if "classroom" not in result["errors"] and "comment" not in result["errors"] and not classroom and not comment:
#             result["errors"]["comment"] = "Если не указана аудитория, комментарий обязателен"
#
#         if len(result["errors"]) > 0:
#             return jsonify(result), 400
#
#         # Попадает ли дата экзамена в период сессии
#         def _exam_date_session_validate(_stud_group, _exam_date):
#
#             if _stud_group.session_start_date is None or _stud_group.session_end_date is None:
#                 return "Для студенческой группы не указаны сроки экзаменационной сессии"
#
#             if _exam_date < _stud_group.session_start_date:
#                 return "Дата экзамена не может быть раньше %s" % _stud_group.session_start_date.isoformat()
#
#             if _exam_date > _stud_group.session_end_date:
#                 return "Дата экзамена не может быть позже %s" % _stud_group.session_end_date.isoformat()
#             return None
#
#         stud_group: StudGroup = cu.stud_group
#         exam_date = stime.date()
#         stime_err = _exam_date_session_validate(stud_group, exam_date)
#         if stime_err:
#             result["errors"]["stime"] = stime_err
#             return jsonify(result), 400
#
#         if related_exams is not None and len(related_exams)>0:
#             for _exam in related_exams:
#                 _stud_group: StudGroup = _exam.curriculum_unit.stud_group
#                 stime_err = _exam_date_session_validate(_stud_group, exam_date)
#                 if stime_err:
#                     result["errors"]["stime"] = stime_err
#                     return jsonify(result), 400
#         if related_curriculum_units is not None and len(related_curriculum_units) > 0:
#             for _cu in related_curriculum_units:
#                 if teacher_id != _cu.teacher_id and teacher_id not in [t.id for t in _cu.practice_teachers]:
#                     result["errors"]["related_curriculum_unit_ids"] = "Нельзя добавлять единицу учебного плана (id=%d) с другим преподавателем" % _cu.id
#                     return jsonify(result), 400
#                 _stud_group: StudGroup = _cu.stud_group
#                 stime_err = _exam_date_session_validate(_stud_group, exam_date)
#                 if stime_err:
#                     result["errors"]["stime"] = stime_err
#                     return jsonify(result), 400
#
#         # Проверка на выходной день
#         if exam_date.isoweekday() == 7:
#             result["errors"]["stime"] = "Экзамен не может быть в воскресенье"
#             return jsonify(result), 400
#         if db.session.query(Holiday).filter_by(date=exam_date).count() > 0:
#             result["errors"]["stime"] = "Экзамен не может быть в праздничный день"
#             return jsonify(result), 400
#
#         # Создан ли экзамен для данного curriculum_unit_id
#
#         q_exam_other = db.session.query(Exam).filter(Exam.curriculum_unit_id == cu.id)
#         if exam is not None:
#             q_exam_other = q_exam_other.filter(Exam.id != exam.id)
#
#         for exam_other in q_exam_other.all():
#             if stud_group.sub_count == 0 or any((fl_sub_g1 and fl_sub_g2 for fl_sub_g1, fl_sub_g2 in zip(exam_other.stud_group_subnums_map, stud_group_subnums))):
#                 result["errors"]["stud_group_subnums"] = "Уже создан экзамен для данного curriculum_unit"
#                 result["exam_other"] = exam_to_json(exam_other)
#                 return jsonify(result), 400
#
#         # Есть ли экзамен у текущей группы в этот день
#         q_exam_other = db.session.query(Exam).join(CurriculumUnit, Exam.curriculum_unit_id == CurriculumUnit.id).filter(func.DATE(Exam.stime) == exam_date)
#
#         # stud_group_id -> stud_group_subnums (с экзаменами)
#         stud_group_id_subnums_map = {
#             cu.stud_group_id: stud_group_subnums
#         }
#         if exam is not None:
#             q_exam_other = q_exam_other.filter(Exam.id != exam.id)
#         if related_exams is not None and len(related_exams) > 0:
#             q_exam_other = q_exam_other.filter(Exam.id.notin_((e.id for e in related_exams)))
#             for related_exam in related_exams:
#                 if related_exam.curriculum_unit.stud_group_id not in stud_group_id_subnums_map:
#                     stud_group_id_subnums_map[related_exam.curriculum_unit.stud_group_id] = related_exam.stud_group_subnums_map
#                 else:
#                     stud_group_id_subnums_map[related_exam.curriculum_unit.stud_group_id] = list(fl_sub_g1 and fl_sub_g2 for fl_sub_g1, fl_sub_g2 in zip(stud_group_id_subnums_map[related_exam.curriculum_unit.stud_group_id], related_exam.stud_group_subnums_map))
#         if related_curriculum_units is not None and len(related_curriculum_units) > 0:
#             for _cu in related_curriculum_units:
#                 if _cu.stud_group.sub_count == 0:
#                     _stud_group_subnums = [True]
#                 else:
#                     _stud_group_subnums = [None] + [True] * _cu.stud_group.sub_count
#                 stud_group_id_subnums_map[_cu.stud_group_id] = _stud_group_subnums
#
#         q_exam_other = q_exam_other.filter(CurriculumUnit.stud_group_id.in_(stud_group_id_subnums_map.keys()))
#
#         for exam_other in q_exam_other.all():
#             _stud_group_subnums = stud_group_id_subnums_map[exam_other.curriculum_unit.stud_group_id]
#             if exam_other.curriculum_unit.stud_group.sub_count == 0 or any((fl_sub_g1 and fl_sub_g2 for fl_sub_g1, fl_sub_g2 in zip(exam_other.stud_group_subnums_map, _stud_group_subnums))):
#                 result["errors"]["stime"] = "Уже создан экзамен для данной группы в этот день"
#                 result["exam_other"] = exam_to_json(exam_other, curriculum_unit_id=True)
#                 return jsonify(result), 400
#
#         # Проверку на экзамены проходящие в указанное время
#         q_exam_other_time = db.session.query(Exam).filter(Exam.stime < etime).filter(Exam.etime > stime)
#         if exam is not None:
#             q_exam_other_time = q_exam_other_time.filter(Exam.id != exam.id)
#         if related_exams is not None and len(related_exams) > 0:
#             q_exam_other_time = q_exam_other_time.filter(Exam.id.notin_((e.id for e in related_exams)))
#         # :
#         # для текущего преподавателя
#         q_exam_other = q_exam_other_time.filter(Exam.teacher_id == teacher_id)
#         for exam_other in q_exam_other.all():
#             if classroom != exam_other.classroom:
#                 result["errors"]["stime"] = "В данное время проходит экзамен у преподавателя в другой аудитории"
#                 result["exam_other"] = exam_to_json(exam_other, curriculum_unit_id=True)
#                 return jsonify(result), 400
#
#             cu_other = exam_other.curriculum_unit
#             if not(cu.subject_id == cu_other.subject_id or (cu.curriculum_unit_group_id is not None and cu_other.curriculum_unit_group_id is not None and cu.curriculum_unit_group_id == cu_other.curriculum_unit_group_id)):
#                 result["errors"]["stime"] = "В данное время проходит экзамен у преподавателя по другому предмету"
#                 result["exam_other"] = exam_to_json(exam_other, curriculum_unit_id=True)
#                 return jsonify(result), 400
#
#         # для текущей аудитории
#         if classroom is not None:
#             q_exam_other = q_exam_other_time.filter(Exam.teacher_id != teacher_id).filter(Exam.classroom == classroom)
#             for exam_other in q_exam_other.all():
#                 result["errors"]["classroom"] = "В данное время аудитория занята"
#                 result["exam_other"] = exam_to_json(exam_other, curriculum_unit_id=True)
#                 break
#
#             # поиск свободной аудитории
#             if "classroom" in result["errors"]:
#                 result["classrooms_free"] = [r.classroom for r in db.session.query(Classroom.classroom).filter(Classroom.classroom != classroom).order_by(Classroom.classroom)]
#                 for _classroom, in db.session.query(Exam.classroom).filter(Exam.stime < etime).filter(Exam.etime > stime).filter(Exam.classroom != classroom).filter(Exam.classroom.isnot(None)).distinct():
#                     if _classroom in result["classrooms_free"]:
#                         result["classrooms_free"].remove(_classroom)
#
#         if len(result["errors"]) == 0:
#             del result["errors"]
#         else:
#             return jsonify(result), 400
#
#         # END Validate
#
#         if exam is None:
#             exam = Exam(curriculum_unit_id=cu.id, curriculum_unit=cu)
#
#         exam.stud_group_subnums_map = stud_group_subnums
#         exam.teacher_id = teacher_id
#         exam.stime = stime
#         exam.etime = etime
#         exam.classroom = classroom
#         exam.comment = comment
#         db.session.add(exam)
#         if related_exams is not None:
#             for _exam in related_exams:
#                 _exam.stime = stime
#                 _exam.etime = etime
#                 _exam.classroom = classroom
#                 _exam.comment = comment
#                 db.session.add(_exam)
#
#         related_exams_new = None
#         if related_curriculum_units is not None:
#             related_exams_new = []
#             for _cu in related_curriculum_units:
#                 _exam = Exam(
#                     curriculum_unit_id=_cu.id,
#                     curriculum_unit=_cu,
#                     stud_group_subnums_map=stud_group_id_subnums_map[_cu.stud_group_id],
#                     teacher_id=teacher_id,
#                     stime=stime,
#                     etime=etime,
#                     classroom=classroom,
#                     comment=comment)
#                 db.session.add(_exam)
#                 related_exams_new.append(_exam)
#
#         db.session.commit()
#         if exam_id is None:
#             db.session.flush()
#
#         result["exam"] = exam_to_json(exam, curriculum_unit_id=True)
#         if related_exams is not None:
#             result["related_exams"] = []
#             for _exam in related_exams:
#                 result["related_exams"].append(exam_to_json(_exam, curriculum_unit_id=True))
#         if related_exams_new is not None:
#             result["related_exams"] = []
#             for _exam in related_exams_new:
#                 result["related_exams"].append(exam_to_json(_exam, curriculum_unit_id=True))
#
#         result["ok"] = True
#         return jsonify(result)
#
#     if request.method == "DELETE":
#         cu = exam.curriculum_unit
#         if not cu.stud_group.active:
#             result["error"] = "Редактирование предыдущей экзаменационной сессии недопускается"
#             return jsonify(result), 403
#
#         db.session.delete(exam)
#         db.session.commit()
#         result["ok"] = True
#         return jsonify(result)
