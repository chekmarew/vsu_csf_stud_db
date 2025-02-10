import sys

from app import app, db

from model import Specialty, StudGroup, Subject, Teacher, CurriculumUnit, Person
from model_history_controller import hist_save_controller

f = open('import_subjects.csv', encoding='utf-8')
with app.app_context():
    admin_user = db.session.query(Person).filter(Person.login == 'chekmarew').one_or_none()
    for row in f:
        # Б1.О.02;История России;2;09.03.02;Информационные системы и технологии;Инженерия информационных систем и технологий;Дифференцированный зачет;144;34;32;;Лавлинский;Сергей;Александрович;доцент (к.н., доцент);116;17;406
        subject_code, subject_name, semester, s_code, s_name, specialization, mark_type, hours, hours_lect, hours_pract, hours_lab, t_surname, t_firstname, t_middlename, t_rank, hours_contact, weeks_training, department_id = tuple(x.strip() for x in row.strip().split(";"))
        hours = int(hours)
        semester = int(semester)
        department_id = int(department_id)

        weeks_training = int(weeks_training)
        hours_lect = int(hours_lect) if hours_lect else 0
        hours_pract = int(hours_pract) if hours_pract else 0
        hours_lab = int(hours_lab) if hours_lab else 0

        if mark_type == "Зачет":
            mark_type = "test_simple"
        elif mark_type == "Экзамен":
            mark_type = "exam"
        elif mark_type == "Дифференцированный зачет":
            mark_type = "test_diff"
        else:
            mark_type = "no_mark"

        subject = db.session.query(Subject).filter(Subject.name == subject_name).one_or_none()
        if subject is None:
            subject = Subject(name=subject_name)
            db.session.add(subject)
            db.session.flush()
            print("Добавлен предмет %s" % subject.name)

        teacher = db.session.query(Teacher).join(Person, Teacher.person_id == Person.id).filter(Person.surname == t_surname).filter(
            Person.firstname == t_firstname).filter(Person.middlename == t_middlename).one_or_none()

        if teacher is None:
            print("Не найден преподаватель %s %s %s %s" % (t_surname, t_firstname, t_middlename, t_rank ))
            db.session.rollback()
            sys.exit(1)

        stud_groups_q = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id).filter(StudGroup.active).filter(StudGroup.semester == semester).filter(Specialty.code == s_code).filter(Specialty.education_form != 'correspondence')
        if specialization:
            stud_groups_q = stud_groups_q.filter(Specialty.specialization == specialization)

        if stud_groups_q.count() == 0:
            print("Не найдены группы")
            print(row)

        for stud_group in stud_groups_q.all():
            e_level = stud_group.specialty.education_level
            if e_level == 'master':
                hours_att_1 = hours_att_2 = hours_att_3 = 0
            elif e_level == 'bachelor' and semester == 8:
                hours_att_3 = 0
                hours_att_1 = hours_att_2 = hours // 2
                if hours % 2 == 1:
                    hours_att_2 += 1
            elif e_level == 'specialist' and semester == 10:
                hours_att_1 = 0
                hours_att_2 = hours_att_3 = hours // 2
                if hours % 2 == 1:
                    hours_att_3 += 1
            else:
                hours_att_1 = hours_att_2 = hours_att_3 = hours // 3
                if hours % 3 == 1:
                    hours_att_3 += 1
                if hours % 3 == 2:
                    hours_att_2 += 1
                    hours_att_3 += 1

            cu_new = CurriculumUnit(
                code=subject_code,
                stud_group=stud_group,
                subject=subject,
                teacher=teacher,
                hours_att_1=hours_att_1,
                hours_att_2=hours_att_2,
                hours_att_3=hours_att_3,
                mark_type=("no_att" if e_level == "master" else mark_type),
                closed=False,
                department_id=department_id,
                hours_lect=hours_lect,
                hours_pract=hours_pract,
                hours_lab=hours_lab
            )
            if e_level == "master":
                if mark_type == "test_simple":
                    cu_new.has_simple_mark_test_simple = True
                if mark_type == "exam":
                    cu_new.has_simple_mark_exam = True
                if mark_type == "test_diff":
                    cu_new.has_simple_mark_test_diff = True

            db.session.add(cu_new)

            if stud_group.weeks_training != weeks_training:
                stud_group.weeks_training = weeks_training
                db.session.add(stud_group)

            db.session.flush()
            hist_save_controller(db.session, cu_new, admin_user)

    db.session.commit()

f.close()
