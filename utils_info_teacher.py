from app_config import db
from sqlalchemy import func, or_, not_
from model import Teacher, CurriculumUnit, StudGroup, Specialty


def curriculum_units(t: Teacher):
    if t is None:
        return []
    return db.session.query(CurriculumUnit).join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).\
        join(Specialty, StudGroup.specialty_id == Specialty.id).\
        filter(or_(CurriculumUnit.teacher_id == t.id, CurriculumUnit.practice_teachers.any(Teacher.id == t.id))).\
        filter(not_(CurriculumUnit.pass_department)).filter(not_(CurriculumUnit.closed)).filter(StudGroup.active).\
        order_by(func.isnull(CurriculumUnit.curriculum_unit_group_id), func.IF(CurriculumUnit.curriculum_unit_group_id.isnot(None), CurriculumUnit.curriculum_unit_group_id, CurriculumUnit.subject_id), Specialty.education_level_order, StudGroup.semester, StudGroup.num).all()
