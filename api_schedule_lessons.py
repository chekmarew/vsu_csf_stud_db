from datetime import timedelta
from flask import jsonify, request
from sqlalchemy import not_, func
from app_config import app, db
from model import Teacher, CurriculumUnit, Subject, StudGroup, Specialty, Classroom, Person, EducationLevels, \
    ScheduledLessonDraft
from utils_auth import get_current_user
from utils_json import teacher_to_json, draft_lesson_to_json
import utils

def _allow_write(u: Person):
    if u.admin_user is not None and u.admin_user.active:
        return True

    if u.teacher is not None and u.teacher.active and u.teacher.dean_staff:
        return True

    # temp
    if u.login in ('korobejnikova_a_v', 'derevyanko_v_g'):
        return True

    return False

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
            "lessons_start_date": g.lessons_start_date.isoformat() if g.lessons_start_date else None,
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
                    "short_name": s.short_name,
                    "without_specifying_schedule": s.without_specifying_schedule
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
                "hours_lect_per_week": cu.hours_lect_per_week,
                "hours_pract_per_week": cu.hours_pract_per_week,
                "hours_lab_per_week": cu.hours_lab_per_week
            }
            g_j["curriculum_units"].append(cu_j)

        if len(g_j["curriculum_units"]) == 0:
            continue

        result["stud_groups"].append(g_j)

    return jsonify(result)

@app.route('/api/schedule/lesson/draft', methods=["POST"])
@app.route('/api/schedule/lesson/draft/<int:lesson_id>', methods=["GET", "PATCH", "DELETE"])
def api_schedule_lesson_draft(lesson_id=None):
    """
    Handler для CRUD черновиков занятий (scheduled_lesson_draft) с учётом
    поля Subject.without_specifying_schedule.
    """
    # GET/DELETE: ищем существующий черновик
    draft = None
    if request.method in ("GET", "PATCH", "DELETE"):
        draft = db.session.query(ScheduledLessonDraft).filter_by(id=lesson_id).one_or_none()
        if not draft:
            return jsonify({"ok": False, "error": "Draft not found"}), 404

    if request.method == "GET":
        data = draft_lesson_to_json(draft)
        data["ok"] = True
        return jsonify(data)

    if request.method == "DELETE":
        db.session.delete(draft)
        db.session.commit()
        return jsonify({"ok": True})

    # POST или PATCH
    rj = request.get_json(silent=True)
    if not isinstance(rj, dict):
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    # Список полей, которые обновляем через setattr
    allowed_fields = [
        'curriculum_unit_id', 'teacher_id', 'stud_group_subnums',
        'week_day', 'week_type', 'lesson_num',
        'lesson_type', 'lesson_form', 'classroom',
        'scheduled_lesson_comment'
    ]

    # Функция проверки наличия обязательных полей для предметов с расписанием
    def require_schedule_fields(src):
        missing = []
        for f in ('teacher_id', 'classroom'):
            # считаем поле «пропущенным», если его нет или оно null/пусто
            if f not in src or src[f] is None or (isinstance(src[f], str) and not src[f].strip()):
                missing.append(f)
        return missing

    # ===== POST =====
    if request.method == "POST":
        # Проверяем curriculum_unit
        cu_id = rj.get('curriculum_unit_id')
        cu = None
        if isinstance(cu_id, int):
            cu = db.session.query(CurriculumUnit).filter_by(id=cu_id).one_or_none()
        if not cu:
            return jsonify({"ok": False, "error": "Invalid curriculum_unit_id"}), 400
        subj = cu.subject
        spec_flag = subj.without_specifying_schedule

        # Если предмет требует указания преподавателя/аудитории
        if not spec_flag:
            miss = require_schedule_fields(rj)
            if miss:
                return jsonify({
                    "ok": False,
                    "error": f"Missing fields for scheduled subject: {', '.join(miss)}"
                }), 400

        # Создаем новый черновик
        draft = ScheduledLessonDraft(
            curriculum_unit_id = cu_id,
            stud_group_subnums = rj['stud_group_subnums'],
            type               = rj['lesson_type'],
            form               = rj['lesson_form'],
            week_day           = rj['week_day'],
            week_type          = rj['week_type'],
            lesson_num         = rj['lesson_num'],
            comment            = rj.get('scheduled_lesson_comment')
        )
        if not spec_flag:
            draft.teacher_id = rj['teacher_id']
            draft.classroom = rj['classroom']
        db.session.add(draft)

    # ===== PATCH =====
    if request.method == "PATCH":
        subj = draft.curriculum_unit.subject
        spec_flag = subj.without_specifying_schedule
        # Если предмет не безрасписанный, то при любом обновлении
        # проверяем, что поля присутствуют
        if not spec_flag:
            miss = require_schedule_fields(rj)
            if miss:
                return jsonify({
                    "ok": False,
                    "error": f"Missing fields for scheduled subject: {', '.join(miss)}"
                }), 400
        # обновляем только разрешённые поля
        for field in allowed_fields:
            if field in rj:
                setattr(draft, field, rj[field])

    # ===== Общая проверка часов в неделю =====
    cu_id = draft.curriculum_unit_id
    cu = db.session.query(CurriculumUnit).filter_by(id=cu_id).one_or_none()
    allowed = {
        'lecture': cu.hours_lect_per_week,
        'pract':   cu.hours_pract_per_week,
        'lab':     cu.hours_lab_per_week
    }.get(draft.type, 0)
    existing = db.session.query(ScheduledLessonDraft) \
        .filter_by(curriculum_unit_id=cu.id, type=draft.type)
    if request.method == 'PATCH':
        existing = existing.filter(ScheduledLessonDraft.id != draft.id)
    total = existing.count() + 1
    if total > allowed:
        return jsonify({
            "ok": False,
            "error": (
                f"Превышено количество занятий типа '{draft.type}' в неделю: "
                f"допускается {allowed}, пытаетесь {total}"
            )
        }), 400

    db.session.commit()
    data = draft_lesson_to_json(draft)
    data["ok"] = True
    return jsonify(data)


@app.route('/api/schedule/lesson/draft_transfer', methods=["POST"])
@utils.check_auth_4_api()
def api_schedule_lesson_draft_transfer():
    pass

