from model import Student, StudGroup
from app_config import db, app
from datetime import datetime

with app.app_context():
    # old -> new stud_group
    stud_groups_map = {}

    stud_groups_old = db.session.query(StudGroup).filter(StudGroup.active).all()

    stud_groups_new = {}

    for sg_old in stud_groups_old:
        sg_old.active = False

        db.session.add(sg_old)

        if sg_old.semester == 4 and sg_old.specialty.code == "09.03.02":
            stud_groups_map[sg_old.id] = 'no_group'
            continue

        if (sg_old.semester == 8 and sg_old.specialty.education_level == 'bachelor') or (sg_old.semester == 11 and sg_old.specialty.education_level == 'specialist') or (sg_old.semester == 4 and sg_old.specialty.education_level == 'master'):
            stud_groups_map[sg_old.id] = 'alumnus'
            continue

        sg_new = StudGroup(
            year=sg_old.year if sg_old.semester % 2 == 1 else sg_old.year+1,
            semester=sg_old.semester+1,
            num=sg_old.num,
            sub_count=sg_old.sub_count,
            specialty_id=sg_old.specialty_id,
            curator_id=sg_old.curator_id,
            group_leader=sg_old.group_leader,
            group_leader2=sg_old.group_leader2,
            weeks_training=0,
            active=True
        )

        db.session.add(sg_new)
        db.session.flush()
        stud_groups_map[sg_old.id] = sg_new.id
        stud_groups_new[sg_new.id] = sg_new

    for s in db.session.query(Student).filter(Student.status == 'study'):
        if s.stud_group_id is None:
            print("Студент %d %s не находится ни в одной группе" % (s.id, s.full_name))
            continue
        if s.stud_group_id not in stud_groups_map.keys():
            print("Студент %d %s не находится в недействующей группе" % (s.id, s.full_name))
            continue

        sg_new_id = stud_groups_map[s.stud_group_id]
        if isinstance(sg_new_id, str):
            s.stud_group_id = None
            s.stud_group = None
            s.stud_group_subnum = None
            if sg_new_id == "alumnus":
                s.status = "alumnus"
                s.alumnus_year = datetime.now().year
            if sg_new_id == "no_group":
                s.semester = s.semester + 1
        else:
            sg_new = stud_groups_new[sg_new_id]
            s.stud_group_id = sg_new_id
            s.semester = sg_new.semester
        db.session.add(s)

    db.session.commit()
