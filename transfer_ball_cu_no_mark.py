from app import app, db

from model import StudGroup, CurriculumUnit, AttMark, Person
from model_history_controller import hist_save_controller
from sqlalchemy import not_

import datetime


with app.app_context():
    admin_user = db.session.query(Person).filter(Person.login == 'chekmarew').one_or_none()

    now = datetime.datetime.now()
    year, month = now.year, now.month

    year -= 1
    semesters = (1, 3, 5, 7, 9) if month < 9 else (2, 4, 6, 8, 10)
    for cu_old in db.session.query(CurriculumUnit).join(StudGroup).filter(CurriculumUnit.mark_type == 'no_mark').filter(not_(StudGroup.active)).filter(StudGroup.year == year).filter(StudGroup.semester.in_(semesters)).order_by(CurriculumUnit.subject_id, StudGroup.semester, StudGroup.num).all():
        cu_new = db.session.query(CurriculumUnit).join(StudGroup).filter(StudGroup.active).filter(CurriculumUnit.subject_id == cu_old.subject_id).filter(StudGroup.year == (year + 1 if cu_old.stud_group.semester % 2 == 0 else year)).filter(StudGroup.semester == (cu_old.stud_group.semester + 1)).filter(StudGroup.num == cu_old.stud_group.num).one()

        for att_mark_old in cu_old.att_marks:
            s = att_mark_old.student
            if s.status != "study" or s.stud_group_id is None or s.stud_group_id != cu_new.stud_group_id:
                continue

            ball_average = att_mark_old.ball_average
            att_mark_new = db.session.query(AttMark).filter(AttMark.curriculum_unit_id == cu_new.id).filter(AttMark.student_id == s.id).one_or_none()
            is_new = False
            if att_mark_new is None:
                is_new = True
                att_mark_new = AttMark(curriculum_unit=cu_new, student=s, att_mark_1=ball_average)
            else:
                att_mark_new.att_mark_1 = ball_average
            db.session.add(att_mark_new)
            if is_new:
                db.session.flush()
            hist_save_controller(db.session, att_mark_new, admin_user)

    db.session.commit()
