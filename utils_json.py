from model import AttMark, CurriculumUnit, Teacher, Student, Person, LessonTime, Exam, ScheduledLessonDraft


def att_mark_to_json(att_mark: AttMark, current_user=None, add_curriculum_unit_id=True, add_comment_hidden=None):
    cu: CurriculumUnit = att_mark.curriculum_unit
    att_mark_j = {
        "id": att_mark.att_mark_id,
        "student_id": att_mark.student_id
    }
    if add_curriculum_unit_id:
        att_mark_j["curriculum_unit_id"] = att_mark.curriculum_unit_id

    if current_user is not None:
        att_mark_j["_allow_attrs_edit"] = {}
        if add_curriculum_unit_id:
            att_mark_j["_allow_write"] = cu.get_rights(current_user)["write"]
        if add_comment_hidden is None:
            add_comment_hidden = cu.get_rights(current_user)["mark_comment_hidden"]

    for a in cu.visible_attrs:
        att_mark_j[a] = getattr(att_mark, a)
        if a == "append_ball":
            att_mark_j["is_available_att_mark_append_ball"] = att_mark.is_available_att_mark_append_ball
        if current_user is not None:
            att_mark_j["_allow_attrs_edit"][a] = att_mark.check_edit_attr(a, current_user)


    att_mark_j["ball_average"] = att_mark.ball_average
    att_mark_j["ball_attendance_add"] = att_mark.ball_attendance_add

    att_mark_res = att_mark.result_print
    if att_mark_res is not None:
        att_mark_j["res_ball"] = att_mark_res[0]
        att_mark_j["res_value"] = att_mark_res[1]["value"]
        att_mark_j["res_value_text"] = att_mark_res[1]["value_text"]
    else:
        att_mark_j["res_ball"] = None
        att_mark_j["res_value"] = None
        att_mark_j["res_value_text"] = None

    if att_mark.exclude == 2:
        att_mark_j["exclude"] = 2
    elif att_mark.att_mark_id in cu.att_marks_readonly_ids:
        att_mark_j["exclude"] = 1

    att_mark_j["comment"] = att_mark.comment
    if add_comment_hidden:
        att_mark_j["comment_hidden"] = att_mark.comment_hidden
    att_mark_j["attendance_pct"] = att_mark.attendance_pct
    return att_mark_j


def json_to_att_mark(j_att_mark, att_mark: AttMark, current_user):
    # validate
    errors = {}
    cu = att_mark.curriculum_unit
    for a in cu.visible_attrs:
        if a in j_att_mark and att_mark.check_edit_attr(a, current_user):
            v = j_att_mark[a]
            if v is None or isinstance(v, int):
                if v is not None:
                    if a in ('att_mark_1', 'att_mark_2', 'att_mark_3', 'att_mark_exam'):
                        if v < 0:
                            errors[a] = "Значение не должно быть меньше 0"
                        if v > 50:
                            errors[a] = "Значение не должно быть больше 50"
                    if a == "att_mark_append_ball":
                        if v < 0:
                            errors[a] = "Значение не должно быть меньше 0"
                        if v > 10:
                            errors[a] = "Значение не должно быть больше 10"
                    if a == "simple_mark_test_simple":
                        if v not in (0, 2, 5):
                            errors[a] = "Допустимые значения 0, 2, 5"

                    if a in ("simple_mark_exam", "simple_mark_test_diff", "simple_mark_course_work", "simple_mark_course_project"):
                        if v not in (0, 2, 3, 4, 5):
                            errors[a] = "Допустимые значения 0, 2, 3, 4, 5"

            else:
                errors[a] = "Значение должно быть null или целым числом"

    if "comment" in j_att_mark:
        if j_att_mark["comment"] is not None:
            if isinstance(j_att_mark["comment"], str):
                if len(j_att_mark["comment"]) > 4000:
                    errors["comment"] = "Длина поля не может быть больше 4000 символов"
            else:
                errors["comment"] = "Значение должно быть null или строкой"
    if cu.get_rights(current_user)["mark_comment_hidden"] and "comment_hidden" in j_att_mark:
        if j_att_mark["comment_hidden"] is not None:
            if isinstance(j_att_mark["comment_hidden"], str):
                if len(j_att_mark["comment_hidden"]) > 4000:
                    errors["comment_hidden"] = "Длина поля не может быть больше 4000 символов"
            else:
                errors["comment_hidden"] = "Значение должно быть null или строкой"

    if len(errors) > 0:
        return att_mark, errors
    # End Validate
    for a in cu.visible_attrs:
        if a in j_att_mark and att_mark.check_edit_attr(a, current_user):
            setattr(att_mark, a, j_att_mark[a])

    if "comment" in j_att_mark:
        att_mark.comment = j_att_mark["comment"]

    if cu.get_rights(current_user)["mark_comment_hidden"] and "comment_hidden" in j_att_mark:
        att_mark.comment_hidden = j_att_mark["comment_hidden"]

    return att_mark, None


def teacher_to_json(t: Teacher):
    return {
        "id": t.id,
        "person_id": t.person_id,
        "rank": t.rank,
        "rank_short": t.rank_short,
        "academic_degree": t.academic_degree,
        "surname": t.person.surname,
        "firstname": t.person.firstname,
        "middlename": t.person.middlename,
        "gender": t.person.gender,
        "department_id": t.department_id,
        "department_part_time_job_ids": [d.id for d in t.departments_part_time_job],
        "department_leader": t.department_leader,
        "department_secretary": t.department_secretary
    }


def curriculum_unit_to_json(cu: CurriculumUnit, contacts=False, exam_schedule=False, exam_schedule_teacher_id=None):
    res = {
        "id": cu.id,
        "code": cu.code,
        "subject": {
            "id": cu.subject.id,
            "name": cu.subject.name,
            "short_name": cu.subject.short_name
        },
        "curriculum_unit_group_id": cu.curriculum_unit_group_id,
        "stud_group": {
            "id": cu.stud_group.id,
            "course": cu.stud_group.course,
            "semester": cu.stud_group.semester,
            "education_level": cu.stud_group.specialty.education_level,
            "education_level_order": cu.stud_group.specialty.education_level_order,
            "num": cu.stud_group.num,
            "sub_count": cu.stud_group.sub_count if cu.stud_group.active else None,
            "specialty": {
                "id": cu.stud_group.specialty.id,
                "code": cu.stud_group.specialty.code,
                "full_name": cu.stud_group.specialty.full_name
            },
            "active": cu.stud_group.active,
            "year": cu.stud_group.year
        },
        "teacher": teacher_to_json(cu.teacher),
        "practice_teachers": [teacher_to_json(t) for t in cu.practice_teachers],
        "department_id": cu.department_id,
        "mark_type": cu.mark_type,
        "has_simple_mark_test_simple": cu.has_simple_mark_test_simple,
        "has_simple_mark_exam": cu.has_simple_mark_exam,
        "has_simple_mark_test_diff": cu.has_simple_mark_test_diff,
        "has_simple_mark_course_work": cu.has_simple_mark_course_work,
        "has_simple_mark_course_project": cu.has_simple_mark_course_project,
        "hours": cu.hours,
        "moodle_id": cu.moodle_id,
        "att_mark_attrs":  cu.visible_attrs if cu.mark_type not in ("no_mark", "no_att") else cu.visible_attrs + ('res_ball', 'res_value_text'),
        "pass_department": cu.pass_department,
        "closed": cu.closed
    }
    if contacts:
        if cu.stud_group.group_leader is not None:
            res["stud_group"]["group_leader"] = person_to_json(cu.stud_group.group_leader.person, contact_data=True)
            res["stud_group"]["group_leader"]["student_id"] = cu.stud_group.group_leader_id
        if cu.stud_group.group_leader2 is not None:
            res["stud_group"]["group_leader2"] = person_to_json(cu.stud_group.group_leader2.person, contact_data=True)
            res["stud_group"]["group_leader2"]["student_id"] = cu.stud_group.group_leader_id

        if cu.stud_group.curator is not None:
            res["stud_group"]["curator"] = person_to_json(cu.stud_group.curator.person, contact_data=True)
            res["stud_group"]["curator"]["teacher_id"] = cu.stud_group.curator_id

    if exam_schedule and cu.stud_group.active and cu.mark_type == "exam":
        res["exam_schedule"] = [exam_to_json(e, curriculum_unit_id=False, stud_group_subnums=True, teacher_id=(exam_schedule_teacher_id is None)) for e in cu.exams if (exam_schedule_teacher_id is None or exam_schedule_teacher_id == e.teacher_id)]

    return res


def person_to_json(p: Person, ext_data=False, contact_data=False):

    person_j = {
        "person_id": p.id,
        "surname": p.surname,
        "surname_old": p.surname_old,
        "firstname": p.firstname,
        "middlename": p.middlename,
        "gender": p.gender
    }
    if contact_data:
        person_j.update({
            "email": p.email,
            "phone": p.phone
        })
    if ext_data:
        person_j.update({
            "birthday": p.birthday.isoformat() if p.birthday is not None else None,
            "email": p.email,
            "phone": p.phone
        })

    return person_j


def student_to_json(s: Student, ext_data=False, contact_data=False, faculty=None):
    student_j = person_to_json(s.person, ext_data=ext_data, contact_data=contact_data)
    student_j.update({
        "student_id": s.id,
        "login": s.login,
        "status": s.status
    })
    if s.alumnus_year:
        student_j["alumnus_year"] = s.alumnus_year
    if s.expelled_year:
        student_j["expelled_year"] = s.expelled_year

    if faculty is not None:
        student_j["faculty_id"] = faculty.id
        student_j["faculty_name"] = faculty.name

    if s.status == "study":
        student_j["semester"] = s.semester
        student_j["course"] = s.course

    group = s.stud_group
    if group is not None:
        student_j["specialty_code"] = group.specialty.code
        student_j["specialty_name"] = group.specialty.name
        student_j["specialization"] = group.specialty.specialization
        student_j["education_level_order"] = group.specialty.education_level_order
        student_j["education_level"] = group.specialty.education_level
        student_j["semester"] = group.semester
        student_j["course"] = group.course
        student_j["group"] = group.num
        student_j["sub_group"] = s.stud_group_subnum if s.stud_group_subnum != 0 else 1

    return student_j


def lesson_time_to_json(lesson_time: LessonTime):
    return {
        "stime": lesson_time.stime.hour*3600+lesson_time.stime.minute*60+lesson_time.stime.second,
        "etime": lesson_time.etime.hour * 3600 + lesson_time.etime.minute * 60 + lesson_time.etime.second,
        "num": lesson_time.lesson_num,
        "time_str": str(lesson_time),
    }


def exam_to_json(exam: Exam, curriculum_unit_id=False, teacher_id=True, stud_group_subnums=True):
    exam_j = {
        "id": exam.id,
        "stime": exam.stime.isoformat(),
        "etime": exam.etime.isoformat(),
        "classroom": exam.classroom,
        "comment": exam.comment
    }
    if teacher_id:
        exam_j["teacher_id"] = exam.teacher_id
    if curriculum_unit_id:
        exam_j["curriculum_unit_id"] = exam.curriculum_unit_id
    if stud_group_subnums:
        exam_j["stud_group_subnums"] = exam.stud_group_subnums_map
    return exam_j


def draft_lesson_to_json(lesson: ScheduledLessonDraft) -> dict:
    subj = lesson.curriculum_unit.subject
    j = {
        "id": lesson.id,
        "curriculum_unit_id": lesson.curriculum_unit_id,
        "stud_group_subnums": lesson.stud_group_subnums,
        "lesson_type": lesson.type,
        "lesson_form": lesson.form,
        "week_day": lesson.week_day,
        "week_type": lesson.week_type,
        "lesson_num": lesson.lesson_num,
        "classroom": lesson.classroom,
        "teacher_id": lesson.teacher_id,
        "scheduled_lesson_comment": lesson.comment,
        # новый флаг
        "without_specifying_schedule": subj.without_specifying_schedule
    }
    return j