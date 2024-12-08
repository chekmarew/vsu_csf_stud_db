import decimal
from sqlalchemy import not_

from app_config import db
from model import StudGroup, CurriculumUnit, AttMark, Subject, LessonStudent, Lesson


def att_marks_report(s):
    result = []

    if s.stud_group is None or not s.stud_group.active:
        result.extend(db.session.query(AttMark).join(CurriculumUnit).join(StudGroup) \
                      .filter(AttMark.student_id == s.id) \
                      .order_by(StudGroup.year.desc(), StudGroup.semester.desc(), AttMark.curriculum_unit_id).all())
    else:
        for cu in s.stud_group.curriculum_units:
            att_mark = db.session.query(AttMark).filter(AttMark.student_id == s.id).filter(
                AttMark.curriculum_unit_id == cu.id).one_or_none()
            if att_mark is None:
                if cu.subject_id in ((sp.replaced_subject_id for sp in s.particular_subjects)):
                    continue
                att_mark = AttMark(student=s, curriculum_unit=cu)
            result.append(att_mark)

        result.extend(db.session.query(AttMark).join(CurriculumUnit).join(StudGroup) \
                      .filter(AttMark.student_id == s.id) \
                      .filter(not_(StudGroup.active)) \
                      .order_by(StudGroup.year.desc(), StudGroup.semester.desc(), AttMark.curriculum_unit_id).all())
    return result


def current_lesson_for_mark(s):
    if s.status != "study":
        return None

    return db.session.query(LessonStudent).join(Lesson, LessonStudent.lesson_id == Lesson.id) \
        .filter(LessonStudent.student_id == s.id) \
        .filter(LessonStudent.attendance == 0) \
        .filter(Lesson.student_mark_active).one_or_none()


def rating(stud_groups, stage):
    students_map = {}
    for g in stud_groups:
        for cu in g.curriculum_units:
            if stage != "total" and stage not in cu.visible_attrs:
                continue
            if stage == "total" and cu.mark_type == 'no_mark':
                continue

            marks = [m for m in cu.att_marks if m.att_mark_id not in cu.att_marks_readonly_ids]

            if g.active and len(marks) == 0:
                return None

            for m in marks:
                val = None
                if stage == "total":
                    if m.result_print is not None:
                        val = m.result_print[0]
                else:
                    val = getattr(m, stage, None)

                if val is None:
                    if g.active:
                        return None
                    else:
                        continue
                if m.student_id not in students_map:
                    students_map[m.student_id] = (m.student, g, [])
                students_map[m.student_id][2].append(val)

    data = []
    decimal.getcontext().prec = 5
    for student_id, v in students_map.items():
        data.append({
            "student": v[0],
            "stud_group": v[1],
            "avg_ball": decimal.Decimal(sum(v[2])) / decimal.Decimal(len(v[2]))
        })
    data.sort(key=lambda row: (-1*row["avg_ball"], row["student"].surname, row["student"].firstname, row["student"].middlename))

    for i, row in enumerate(data):
        if i > 0 and data[i-1]["avg_ball"] == row["avg_ball"]:
            row["rating"] = data[i-1]["rating"]
        else:
            row["rating"] = i+1

    return data


def rating_with_avg_ball(stud_groups, stage):
    data = rating(stud_groups, stage)
    if data is None:
        return None, None
    else:
        avg_ball = None
        if len(data) > 0:
            decimal.getcontext().prec = 6
            avg_ball = sum((r["avg_ball"] for r in data)) / len(data)
        return data, avg_ball
