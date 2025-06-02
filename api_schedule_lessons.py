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
@utils.check_auth_4_api()
def api_schedule_lesson_draft(lesson_id=None):
    """
    CRUD для ScheduledLessonDraft с учётом:
      - Subject.without_specifying_schedule,
      - lesson_form == 'remote' (аудитория может быть null),
      - если есть непустой комментарий, то аудитория тоже может быть null.
    Поддерживается:
      - Создание сразу для нескольких CU через related_curriculum_unit_ids.
      - Обновление сразу нескольких драфтов через related_schedule_lesson_ids,
        при условии, что совпадают type, form, week_day, week_type, teacher_id.
    """

    # ---------- GET / DELETE ----------
    draft = None
    if request.method in ("GET", "PATCH", "DELETE"):
        draft = db.session.query(ScheduledLessonDraft).filter_by(id=lesson_id).one_or_none()
        if draft is None:
            return jsonify({"ok": False, "error": "Draft not found"}), 404

    if request.method == "GET":
        out = draft_lesson_to_json(draft)
        out["ok"] = True
        return jsonify(out)

    if request.method == "DELETE":
        db.session.delete(draft)
        db.session.commit()
        return jsonify({"ok": True})

    # ---------- POST / PATCH ----------

    rj = request.get_json(silent=True)
    if not isinstance(rj, dict):
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    # Поля, разрешённые для массового setattr
    allowed_fields = [
        "curriculum_unit_id", "teacher_id", "stud_group_subnums",
        "week_day", "week_type", "lesson_num",
        "lesson_type", "lesson_form", "classroom",
        "scheduled_lesson_comment"
    ]

    # -------- Вспомогательные функции --------

    def require_schedule_fields(src: dict) -> list:
        """
        Проверяет наличие обязательных полей:
          - teacher_id всегда обязателен, если предмет НЕ without_specifying_schedule.
          - classroom обязателен только если BOTH:
              1) form != 'remote'
              2) scheduled_lesson_comment пустая или отсутствует
        Возвращает список пропущенных полей.
        """
        missing = []
        # teacher_id обязателен всегда (для предметов с расписанием)
        if "teacher_id" not in src or src["teacher_id"] is None:
            missing.append("teacher_id")

        # Если форма != remote и нет непустого комментария, то classroom обязателен
        form_val = src.get("lesson_form")
        comment_val = src.get("scheduled_lesson_comment")
        has_nonempty_comment = isinstance(comment_val, str) and comment_val.strip() != ""
        if form_val != "remote" and not has_nonempty_comment:
            if "classroom" not in src or src["classroom"] is None or (
                    isinstance(src["classroom"], str) and not src["classroom"].strip()):
                missing.append("classroom")

        return missing

    def load_curriculum_unit(cu_id: int):
        """Загружает CurriculumUnit по id или возвращает None."""
        if not isinstance(cu_id, int):
            return None
        return db.session.query(CurriculumUnit).filter_by(id=cu_id).one_or_none()

    def validate_related_cus(main_cu, related_ids: list):
        """
        Проверяет каждый ID из related_ids:
         - существует ли CU,
         - subject_id совпадает с main_cu.subject_id
           или curriculum_unit_group_id совпадает (и не NULL).
        Возвращает (список CU-объектов, список ошибок).
        """
        errors = []
        related_objs = []
        main_sid = main_cu.subject_id
        main_gid = main_cu.curriculum_unit_group_id
        for r_id in related_ids:
            r_cu = load_curriculum_unit(r_id)
            if r_cu is None:
                errors.append(f"Invalid related_curriculum_unit_id {r_id}")
                continue

            if not (r_cu.subject_id == main_sid or (
                    main_gid is not None and r_cu.curriculum_unit_group_id == main_gid)):
                errors.append(f"Unrelated related_curriculum_unit_id {r_id}")
                continue

            related_objs.append(r_cu)

        return related_objs, errors

    def validate_related_drafts(base_draft, related_ids: list):
        """
        Проверяет каждый ID из related_ids:
         - сам draft существует,
         - у него совпадают поля (type, form, week_day, week_type, teacher_id),
         - его curriculum_unit тот же subject_id или тот же curriculum_unit_group_id.
        Возвращает (список draft-объектов, список ошибок).
        """
        errors = []
        related_objs = []
        base_cu = base_draft.curriculum_unit
        base_sid = base_cu.subject_id
        base_gid = base_cu.curriculum_unit_group_id
        base_params = (
        base_draft.type, base_draft.form, base_draft.week_day, base_draft.week_type, base_draft.teacher_id)

        for d_id in related_ids:
            rd = db.session.query(ScheduledLessonDraft).filter_by(id=d_id).one_or_none()
            if rd is None:
                errors.append(f"Related draft with ID {d_id} not found")
                continue

            rd_params = (rd.type, rd.form, rd.week_day, rd.week_type, rd.teacher_id)
            if rd_params != base_params:
                errors.append(f"Draft {d_id} parameters mismatch (type/form/week_day/week_type/teacher)")
                continue

            rc = rd.curriculum_unit
            if not (rc.subject_id == base_sid or (base_gid is not None and rc.curriculum_unit_group_id == base_gid)):
                errors.append(f"Draft {d_id} has unrelated curriculum unit")
                continue

            related_objs.append(rd)

        return related_objs, errors

    def validate_hours(
            curriculum_unit_id: int,
            lesson_type: str,
            target_mask: int,
            target_wt_factor: int,
            exclude_draft_ids: list = None
    ):
        cu = db.session.query(CurriculumUnit).filter_by(id=curriculum_unit_id).one_or_none()
        if cu is None:
            return False, f"CurriculumUnit {curriculum_unit_id} not found"

        allowed_counts = {
            "lecture": cu.hours_lect_per_week,
            "pract": cu.hours_pract_per_week,
            "lab": cu.hours_lab_per_week
        }
        allowed_for_type = allowed_counts.get(lesson_type, 0)

        # Берём только те draft'ы, у которых (existing_mask & target_mask) != 0
        query = db.session.query(ScheduledLessonDraft).filter_by(
            curriculum_unit_id=curriculum_unit_id,
            type=lesson_type
        ).filter(ScheduledLessonDraft.stud_group_subnums.op('&')(target_mask) != 0)

        if exclude_draft_ids:
            query = query.filter(ScheduledLessonDraft.id.notin_(exclude_draft_ids))

        existing_drafts = query.all()

        # load[0] — нагрузка для подгруппы 1, load[1] — для подгруппы 2
        load = [0, 0]
        for ed in existing_drafts:
            existing_mask = ed.stud_group_subnums
            wt = 2 if ed.week_type == 3 else 1
            overlap = existing_mask & target_mask

            if overlap & 1:
                load[0] += wt
            if overlap & 2:
                load[1] += wt

        # Прибавляем нагрузку нового/редактируемого драфта
        if target_mask & 1:
            load[0] += target_wt_factor
        if target_mask & 2:
            load[1] += target_wt_factor

        for idx in (0, 1):
            if load[idx] > allowed_for_type:
                subgroup_no = idx + 1
                return False, (
                    f"Превышено количество занятий типа '{lesson_type}' в неделю "
                    f"для подгруппы {subgroup_no}: допускается {allowed_for_type}, "
                    f"пытаетесь {load[idx]}"
                )
        return True, None

    # -------- Конец вспомогательных функций --------

    # === POST: создание нового черновика (включая merge для related CU) ===
    valid_hours_errors = []
    if request.method == "POST":
        # 1) Загрузим и проверим главный CurriculumUnit
        cu_id = rj.get("curriculum_unit_id")
        main_cu = load_curriculum_unit(cu_id)
        if main_cu is None:
            return jsonify({"ok": False, "error": "Invalid curriculum_unit_id"}), 400

        subj = main_cu.subject
        spec_flag = subj.without_specifying_schedule

        # 2) Если предмет требует расписания, проверяем обязательные поля
        if not spec_flag:
            missing = require_schedule_fields(rj)
            if missing:
                return jsonify({
                    "ok": False,
                    "error": f"Missing fields for scheduled subject: {', '.join(missing)}"
                }), 400

        # 3) Обрабатываем related_curriculum_unit_ids
        related_cu_ids = rj.get("related_curriculum_unit_ids") or []
        related_cus, cu_errors = validate_related_cus(main_cu, related_cu_ids)
        if cu_errors:
            return jsonify({"ok": False, "error": "; ".join(cu_errors)}), 400

        # 4) Подготавливаем общие поля (common_data)
        common_data = {
            "stud_group_subnums": rj["stud_group_subnums"],
            "type": rj["lesson_type"],
            "form": rj["lesson_form"],
            "week_day": rj["week_day"],
            "week_type": rj["week_type"],
            "lesson_num": rj["lesson_num"],
            "comment": rj.get("scheduled_lesson_comment")
        }
        if not spec_flag:
            common_data["teacher_id"] = rj["teacher_id"]
            # classroom обязателен, только если форма != 'remote' и нет непустого комментария
            form_val = rj["lesson_form"]
            comment_val = rj.get("scheduled_lesson_comment", "")
            has_nonempty_comment = isinstance(comment_val, str) and comment_val.strip() != ""
            if form_val != "remote" and not has_nonempty_comment or rj.get("classroom") is not None:
                common_data["classroom"] = rj["classroom"]

        # 5) Функция для создания одного ScheduledLessonDraft
        new_drafts = []

        def create_draft_for_cu(cu_obj):
            d = ScheduledLessonDraft(curriculum_unit_id=cu_obj.id, **common_data)
            db.session.add(d)
            db.session.flush()  # чтобы d.id сразу заполнился
            new_drafts.append(d)

        # 5.1) Создаём для главного CU
        b, e = validate_hours(main_cu.id,
                              common_data["type"],
                              common_data["stud_group_subnums"],
                              common_data["week_type"])
        if not b:
            valid_hours_errors.append(e)
        create_draft_for_cu(main_cu)
        # 5.2) Создаём для каждого related CU
        for rc in related_cus:
            b, e = validate_hours(rc.id,
                                  common_data["type"],
                                  common_data["stud_group_subnums"],
                                  common_data["week_type"])
            if not b:
                valid_hours_errors.append(e)
            create_draft_for_cu(rc)

        if valid_hours_errors:
            db.session.rollback()
            return jsonify({"ok": False, "error": "; ".join(valid_hours_errors)}), 400

        db.session.commit()

        # 8) Формируем ответ
        payload = [draft_lesson_to_json(d) for d in new_drafts]
        return jsonify({"ok": True, "created": payload}), 201

    # === PATCH: обновление одного draft + (опционально) связанных draft-ов ===

    if request.method == "PATCH":
        # 1) Получаем связанные драфты, если переданы related_schedule_lesson_ids
        related_ids = rj.get("related_schedule_lesson_ids") or []
        related_objs, rd_errors = validate_related_drafts(draft, related_ids)
        if rd_errors:
            return jsonify({"ok": False, "error": "; ".join(rd_errors)}), 400

        subj = draft.curriculum_unit.subject
        spec_flag = subj.without_specifying_schedule

        # 2) Определяем новую форму: либо та, что пришла, либо старая
        new_form = rj.get("lesson_form", draft.form)
        new_comment = rj.get("scheduled_lesson_comment", draft.comment or "")

        # 3) Если предмет требует расписания, проверяем обязательные поля:
        if not spec_flag:
            temp = {"lesson_form": new_form, "scheduled_lesson_comment": new_comment}
            temp.update(rj)
            missing = require_schedule_fields(temp)
            if missing:
                return jsonify({
                    "ok": False,
                    "error": f"Missing fields for scheduled subject: {', '.join(missing)}"
                }), 400

        # 4) Обновляем основной draft
        for fld in allowed_fields:
            if fld in rj:
                setattr(draft, fld, rj[fld])
        b, e = validate_hours(draft.curriculum_unit_id,
                              draft.type,
                              draft.stud_group_subnums,
                              draft.week_type)
        if not b:
            valid_hours_errors.append(e)
        # 5) Обновляем связанные драфты
        for rd in related_objs:
            for fld in allowed_fields:
                if fld in rj:
                    setattr(rd, fld, rj[fld])
            b, e = validate_hours(rd.curriculum_unit_id,
                                  rd.type,
                                  rd.stud_group_subnums,
                                  rd.week_type)
            if not b:
                valid_hours_errors.append(e)

        if valid_hours_errors:
            db.session.rollback()
            return jsonify({"ok": False, "error": "; ".join(valid_hours_errors)}), 400

    # 9) Сохраняем изменения
    db.session.commit()

    # 10) Возвращаем обновлённый основной draft
    out = draft_lesson_to_json(draft)
    out["ok"] = True
    return jsonify(out), 200

@app.route('/api/schedule/lesson/to_draft', methods=["POST"])
@utils.check_auth_4_api()
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