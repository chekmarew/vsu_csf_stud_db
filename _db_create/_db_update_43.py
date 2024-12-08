from app import app, db

from model import  CurriculumUnit, AttMark, StudGroup




with app.app_context():

    for cu in db.session.query(CurriculumUnit).join(StudGroup).filter(CurriculumUnit.closed).filter(StudGroup.active).all():
        for m in cu.att_marks:
            m: AttMark = m
            m.attendance_rate_cached = m.attendance_rate_raw
            db.session.add(m)

    db.session.commit()
