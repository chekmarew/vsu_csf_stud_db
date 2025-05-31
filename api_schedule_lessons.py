from datetime import timedelta
from flask import jsonify, request
from sqlalchemy import not_, func
from app_config import app, db
from model import Teacher, CurriculumUnit, Subject, StudGroup, Specialty, Classroom, Person, EducationLevels, \
    ScheduledLessonDraft, ScheduledLesson
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
    flag = False
    if _allow_write(current_user):
        flag = True
        result["schedule_draft"] = []

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
            if flag:
                cu_j["lessons_draft"] = []

            if cu.scheduled_lessons:
                for sch_l in cu.scheduled_lessons:
                    cu_j["lessons"].append(draft_lesson_to_json(sch_l))

            if cu.scheduled_lessons_draft and flag:
                for sch_l_d in cu.scheduled_lessons_draft:
                    cu_j["lessons_draft"].append(draft_lesson_to_json(sch_l_d))

            g_j["curriculum_units"].append(cu_j)

        if len(g_j["curriculum_units"]) == 0:
            continue



        result["stud_groups"].append(g_j)

    return jsonify(result)

@app.route('/api/schedule/lesson/draft', methods=["POST"])
@app.route('/api/schedule/lesson/draft/<int:lesson_id>', methods=["GET", "PATCH", "DELETE"])
# @utils.check_auth_4_api()
def api_schedule_lesson_draft(lesson_id=None):
    """
    Handler для CRUD черновиков занятий (scheduled_lesson_draft) с учётом
    поля Subject.without_specifying_schedule.
    """
    # current_user = get_current_user()
    # if not _allow_write(current_user):
    #     return jsonify({"ok": False, "error": "method not allowed to you"})

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
        cu_g_id = cu.curriculum_unit_group_id
        spec_flag = subj.without_specifying_schedule

        r_cu_ids = rj.get('related_curriculum_unit_ids')
        r_cus = []
        if r_cu_ids is not None:
            for r_cu_id in r_cu_ids:
                r_cu = db.session.query(CurriculumUnit).filter_by(id=r_cu_id).one_or_none()
                if not r_cu:
                    return jsonify({"ok": False, "error": f"Invalid related_curriculum_unit_id {r_cu_id}"}), 400
                if not (r_cu.subject_id == cu.subject_id or r_cu.curriculum_unit_group_id == cu_g_id):
                    return jsonify({"ok": False, "error": f"Oh no, unrelated related_curriculum_unit_id {r_cu_id}"}), 400
                r_cus.append(r_cu)

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
            teacher_id         = rj['teacher_id'],
            comment            = rj.get('scheduled_lesson_comment')
        )
        if not spec_flag:
            draft.teacher_id = rj['teacher_id']
            draft.classroom = rj['classroom']
        db.session.add(draft)

        # Создаем черновики для смежных занятий, если они есть
        if r_cus:
            for r_cu in r_cus:
                related_draft = ScheduledLessonDraft(
                    curriculum_unit_id=r_cu.id,
                    stud_group_subnums=rj['stud_group_subnums'],
                    type=rj['lesson_type'],
                    form=rj['lesson_form'],
                    week_day=rj['week_day'],
                    week_type=rj['week_type'],
                    lesson_num=rj['lesson_num'],
                    teacher_id=rj['teacher_id'],
                    comment=rj.get('scheduled_lesson_comment')
                )
                if not spec_flag:
                    related_draft.teacher_id = rj['teacher_id']
                    related_draft.classroom = rj['classroom']
                db.session.add(related_draft)

    # ===== PATCH =====
    if request.method == "PATCH":
        r_draft = []
        r_draft_ids = rj.get('related_schedule_lesson_ids')
        if r_draft_ids is not None:
            for r_draft_id in r_draft_ids:
                r_d = db.session.query(ScheduledLessonDraft).filter_by(id=r_draft_id).one_or_none()
                if not r_d:
                    return jsonify({"ok": False, "error": f"Related draft with ID {r_draft_id} not found"}), 404
                if (r_d.type != draft.type
                        or r_d.week_day != draft.week_day
                        or r_d.week_type != draft.week_type
                        or r_d.teacher_id != draft.teacher_id):
                    return jsonify({"ok": False, "error": f"Draft {r_draft_id} has different parameters (type, week_day, week_type, teacher)"}), 400

                    # Check if curriculum units are related (same subject or curriculum group)
                if not (r_d.curriculum_unit.subject_id == draft.curriculum_unit.subject_id or
                        r_d.curriculum_unit.curriculum_unit_group_id == draft.curriculum_unit.curriculum_unit_group_id):
                    return jsonify({"ok": False, "error": f"Draft {r_draft_id} has unrelated curriculum unit"}), 400
                r_draft.append(r_d)
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

        if r_draft:
            for r_d in r_draft:
                for field in allowed_fields:
                    if field in rj:
                        setattr(r_d, field, rj[field])

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


@app.route('/api/schedule/lesson/to_draft', methods=["POST"])
# @utils.check_auth_4_api()
def api_schedule_lesson_to_draft_transfer():

    # Удаляем все черновики
    db.session.query(ScheduledLessonDraft).delete(synchronize_session=False)

    # Считываем все финальные записи
    clean = (db.session.query(ScheduledLesson)
             .join(CurriculumUnit, ScheduledLesson.curriculum_unit_id == CurriculumUnit.id)
             .join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id)
             .filter(StudGroup.active == True))

    # Копируем их в ScheduledLessonDraft
    new_drafts = []
    for f in clean:
        d = ScheduledLessonDraft(
            curriculum_unit_id=f.curriculum_unit_id,
            teacher_id=f.teacher_id,
            stud_group_subnums=f.stud_group_subnums,
            week_day=f.week_day,
            week_type=f.week_type,
            lesson_num=f.lesson_num,
            type=f.type,
            form=f.form,
            classroom=f.classroom,
            comment=f.comment
        )
        new_drafts.append(d)
        db.session.add(d)

    db.session.commit()

    # Формируем ответ
    resp = {"ok": True, "drafts": []}
    for d in new_drafts:
        resp["drafts"].append({
            "id": d.id,
            "curriculum_unit_id": d.curriculum_unit_id,
            "teacher_id": d.teacher_id,
            "stud_group_subnums": d.stud_group_subnums,
            "week_day": d.week_day,
            "week_type": d.week_type,
            "lesson_num": d.lesson_num,
            "lesson_type": d.type,
            "lesson_form": d.form,
            "classroom": d.classroom,
            "scheduled_lesson_comment": d.comment
        })
    return jsonify(resp), 200

@app.route('/api/schedule/lesson/from_draft', methods=["POST"])
# @utils.check_auth_4_api()
def api_schedule_lesson_from_draft_transfer():

    # 1) Считываем все draft-записи по контексту
    drafts = db.session.query(ScheduledLessonDraft).all()

    # 2) БАЗОВАЯ ВАЛИДАЦИЯ
    errors = []
    # хотя бы один draft должен существовать
    if not drafts:
        errors.append("Нет записей в черновике")

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    # 3) Если всё ок — удаляем все финальные записи для этого контекста
    db.session.query(ScheduledLesson).delete(synchronize_session=False)

    # 4) Копируем из Draft → Final
    for d in drafts:
        f = ScheduledLesson(
            id=d.id,
            curriculum_unit_id=d.curriculum_unit_id,
            teacher_id=d.teacher_id,
            stud_group_subnums=d.stud_group_subnums,
            week_day=d.week_day,
            week_type=d.week_type,
            lesson_num=d.lesson_num,
            type=d.type,
            form=d.form,
            classroom=d.classroom,
            comment=d.comment
        )
        db.session.add(f)

    # 5) Удаляем все записи из черновика
    db.session.query(ScheduledLessonDraft).delete(synchronize_session=False)

    db.session.commit()  # финальный коммит

    return jsonify({"ok": True, "message": "Чистовик успешно обновлён"}), 200