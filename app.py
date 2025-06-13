import os
import io

from datetime import datetime

from flask import request, session, render_template, redirect, url_for, send_from_directory, send_file, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from app_config import app, db

import api
import api_auth_jwt
import api_lessons
import api_schedule_exams
import api_schedule_lessons
import public_api

import utils
import utils_info_student
import utils_auth

from model import StudGroup, Specialty, Subject, SubjectParticular, Teacher, Student, CurriculumUnit, CurriculumUnitStatusHist, \
    LessonStudent, LessonCurriculumUnit, Lesson, \
    AttMark, AttMarkHist, AdminUser, Person, Department, PersonHist, Exam, CertificateOfStudy
from model import MarkSimpleTypeDict

from forms import StudGroupForm, StudentForm, SubjectForm, TeacherForm, PersonForm, \
    PersonSearchForm, \
    CurriculumUnitForm, CurriculumUnitPracticeTeacherAddForm, TeacherAddDepartmentPartTimeJobForm, \
    CurriculumUnitCopyForm, AttMarksForm, \
    StudGroupsPrintForm, RatingForm, LessonsReportForm, AdminUserForm, CertificateOfStudyForm, LoginForm, \
    LoginEmailForm, LoginSMSForm, AttMarksStudentAddForm
from forms import StudentsUnallocatedForm

from model_history_controller import hist_save_controller

from docs import create_doc, create_doc_curriculum_unit, create_doc_curriculum_unit_simple_marks
from excel import create_excel_stud_groups

from sqlalchemy import not_, or_, and_, func


# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if form.button_login.data and form.validate():
        login = form.login.data
        password = form.password.data

        auth_res, user = utils_auth.auth_by_login_password(login, password)

        if auth_res["ok"] and user is not None:
            session.permanent = not form.temporary_entrance.data
            login_user(user)
            return redirect(request.args.get("next") or url_for('index'))

        # second factor
        if auth_res.get("need_second_factor", False):
            if "email" in auth_res:
                email_code_res = utils_auth.send_code_email(auth_res["email"], second_factor=True)
                if email_code_res["ok"]:
                    session['wait_email_user'] = auth_res["email"]
                    session['wait_email_max_time'] = int(datetime.now().timestamp()) + int(email_code_res["code_timelife"])
                    session['wait_email_second_factor'] = True
                    session['temporary_entrance'] = form.temporary_entrance.data
                    return redirect(url_for('login_email', next=request.args.get('next', None)))

                else:
                    form.login.errors.append(
                        "Не удалось отправить код на e-mail для двухфакторной аутентификации. Попробуйте выполнить вход позже")

            elif "phone" in auth_res:
                phone_code_res = utils_auth.send_code_sms(auth_res["phone"])
                if phone_code_res["ok"]:
                    session['wait_sms_user'] = auth_res["phone"]
                    session['wait_sms_max_time'] = int(datetime.now().timestamp()) + int(phone_code_res["code_timelife"])
                    session['wait_sms_second_factor'] = True
                    session['temporary_entrance'] = form.temporary_entrance.data
                else:
                    form.login.errors.append(
                        "Не удалось отправить код по sms для двухфакторной аутентификации. Попробуйте выполнить вход позже")

        # end second factor
        if "error" in auth_res:
            form.login.errors.append(auth_res["error"])

    return render_template('login.html', form=form)


# login page
@app.route("/login_email", methods=["GET", "POST"])
def login_email():
    form = LoginEmailForm(request.form)

    if form.button_send_email.data and form.validate():
        email = form.email.data
        email_code_res = utils_auth.send_code_email(email=email)
        if email_code_res["ok"]:
            session['wait_email_user'] = email
            session['wait_email_max_time'] = int(datetime.now().timestamp()) + int(email_code_res["code_timelife"])
        else:
            if "error" in email_code_res:
                form.email.errors.append(email_code_res["error"])

    wait_sec = None
    if 'wait_email_user' in session and 'wait_email_max_time' in session and session['wait_email_max_time'] > int(datetime.now().timestamp()):
        form.email.data = session['wait_email_user']
        form.email.render_kw = {"disabled": True}
        form.code.render_kw = {'autofocus': True}
        wait_sec = session['wait_email_max_time'] - int(datetime.now().timestamp())

        if 'wait_email_second_factor' in session and 'temporary_entrance' in session:
            form.temporary_entrance.data = session['temporary_entrance']
            del session['temporary_entrance']

        if form.button_login.data and form.validate():
            auth_res, user = utils_auth.auth_by_email_code(form.email.data, form.code.data)

            if auth_res["ok"] and user is not None:
                session.permanent = not form.temporary_entrance.data
                login_user(user)
                del session['wait_email_user']
                del session['wait_email_max_time']
                if 'wait_email_second_factor' in session:
                    del session['wait_email_second_factor']
                return redirect(request.args.get("next") or url_for('index'))

            if "error" in auth_res:
                form.code.errors.append(auth_res["error"])

    return render_template('login_email.html', form=form,
                           wait_sec=wait_sec, second_factor=session.get('wait_email_second_factor', False))


# login page sms
@app.route("/login_sms", methods=["GET", "POST"])
def login_sms():
    if app.config.get("SMS_SENDER", None) is None:
        return render_error(403)
    form = LoginSMSForm(request.form)


    if form.button_send_sms.data and form.validate():
        phone = form.phone.data
        phone_code_res = utils_auth.send_code_sms(phone=phone)
        if phone_code_res["ok"]:
            session['wait_sms_user'] = phone
            session['wait_sms_max_time'] = int(datetime.now().timestamp()) + int(phone_code_res["code_timelife"])
        else:
            if "error" in phone_code_res:
                form.phone.errors.append(phone_code_res["error"])
    wait_sec = None

    if 'wait_sms_user' in session and 'wait_sms_max_time' in session and session['wait_sms_max_time'] > int(datetime.now().timestamp()):
        form.phone.data = session['wait_sms_user']
        form.phone.render_kw = {"disabled": True}
        form.code.render_kw = {'autofocus': True}
        wait_sec = session['wait_sms_max_time'] - int(datetime.now().timestamp())

        if 'wait_email_second_factor' in session and 'temporary_entrance' in session:
            form.temporary_entrance.data = session['temporary_entrance']
            del session['temporary_entrance']

        if form.button_login.data and form.validate():
            auth_res, user = utils_auth.auth_by_sms_code(form.phone.data, form.code.data)

            if auth_res["ok"] and user is not None:
                session.permanent = not form.temporary_entrance.data
                login_user(user)
                del session['wait_sms_user']
                del session['wait_sms_max_time']
                if 'wait_sms_second_factor' in session:
                    del session['wait_sms_second_factor']
                return redirect(request.args.get("next") or url_for('index'))

            if "error" in auth_res:
                form.code.errors.append(auth_res["error"])

    return render_template('login_sms.html', form=form,  wait_sec=wait_sec, second_factor=session.get('wait_sms_second_factor', False))


@login_manager.user_loader
def load_user(user_id):
    try:
        id = int(user_id)
    except ValueError:
        return None

    user = db.session.query(Person).filter(Person.id == id).one_or_none()

    return user


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


def render_error(code):
    return render_template('_errors/%d.html' % code), code


@app.route('/')
@login_required
def index():
    show_all_roles = False
    if "show_all_roles" in request.args:
        show_all_roles = True

    if not show_all_roles:
        if len(current_user.roles_active) == 1:
            u = current_user.roles_active[0]
            if u.role_name == "Student":
                return redirect(url_for('att_marks_report_student', id=u.id))

            if u.role_name == "Teacher":
                if u.department_secretary:
                    return redirect(url_for('department_panel', department_id=u.department_id))
                else:
                    return redirect(url_for('teacher_report', id=u.id))

            if u.role_name == "AdminUser":
                return redirect(url_for('admin_panel'))

    return render_template('index.html', show_all_roles=show_all_roles)


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/stud_groups')
@login_required
def stud_groups():
    if not current_user.user_rights["stud_groups"]:
        return render_error(403)

    archive_year, archive_semester = None, None
    if "archive_year" in request.args and "archive_semester" in request.args:
        try:
            archive_year, archive_semester = int(request.args["archive_year"]), int(request.args["archive_semester"])
        except ValueError:
            return render_error(400)

    q_groups = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id)
    if archive_year is not None and archive_semester is not None:
        s = 0 if archive_semester == 2 else archive_semester
        q_groups = q_groups.filter(not_(StudGroup.active)).\
            filter(StudGroup.year == archive_year).filter(func.mod(StudGroup.semester, 2) == s)
    else:
        q_groups = q_groups.filter(StudGroup.active)

    groups = q_groups.order_by(Specialty.education_level_order, StudGroup.year, StudGroup.semester, StudGroup.num).all()

    stud_count = None
    if archive_year is None or archive_semester is None:
        stud_count = db.session.query(Student).filter_by(status='study').count()

    return render_template('stud_groups.html', stud_groups=groups, periods_archive=utils.periods_archive(), archive_year=archive_year, archive_semester=archive_semester, stud_count=stud_count)


@app.route('/stud_groups_curator')
@login_required
def stud_groups_curator():
    user = None
    for r in current_user.roles:
        if r.role_name == 'Teacher':
            user = r
        if r.role_name == 'AdminUser':
            user = r
            break

    if user is None:
        return render_error(403)

    q_groups = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id).filter(StudGroup.active)

    if user.role_name == 'Teacher' and (not user.user_rights["stud_groups"]):
        q1 = db.session.query(CurriculumUnit.stud_group_id).filter(or_(CurriculumUnit.teacher_id == user.id, CurriculumUnit.practice_teachers.any(Teacher.id == user.id))).subquery()
        q_groups = q_groups.filter(or_(StudGroup.id.in_(q1), StudGroup.curator_id == user.id))

    groups = q_groups.order_by(Specialty.education_level_order, StudGroup.year, StudGroup.semester, StudGroup.num).all()

    if "print" in request.args:
        if not user.user_rights["stud_groups"]:
            return render_error(403)
        f = create_doc(template_name="curators", data={"stud_groups": groups})
        f_data = io.BytesIO()
        with open(f, 'rb') as fo:
            f_data.write(fo.read())
        f_data.seek(0)
        os.remove(f)

        file_name = "Кураторы ФКН"
        if len(groups) > 0:
            file_name += " "+groups[0].year_print
        file_name += ".odt"

        return send_file(f_data, mimetype="application/vnd.oasis.opendocument.text", as_attachment=True,
                         download_name=file_name)

    return render_template('stud_groups_curator.html', stud_groups=groups)


@app.route('/stud_groups_leader')
@login_required
def stud_groups_leader():
    user = None
    for r in current_user.roles:
        if r.role_name == 'Teacher':
            user = r
        if r.role_name == 'AdminUser':
            user = r
            break

    if user is None:
        return render_error(403)

    q_groups = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id).filter(StudGroup.active)

    if user.role_name == 'Teacher' and (not user.user_rights["stud_groups"]):
        q1 = db.session.query(CurriculumUnit.stud_group_id).filter(or_(CurriculumUnit.teacher_id == user.id,
                                                                       CurriculumUnit.practice_teachers.any(Teacher.id == user.id))).subquery()
        q_groups = q_groups.filter(or_(StudGroup.id.in_(q1), StudGroup.curator_id == user.id))

    groups = q_groups.order_by(Specialty.education_level_order, StudGroup.year, StudGroup.semester, StudGroup.num).all()

    if "print" in request.args:
        if not user.user_rights["stud_groups"]:
            return render_error(403)
        f = create_doc(template_name="group_leaders", data={"stud_groups": groups})
        f_data = io.BytesIO()
        with open(f, 'rb') as fo:
            f_data.write(fo.read())
        f_data.seek(0)
        os.remove(f)

        file_name = "Старосты ФКН"
        if len(groups) > 0:
            file_name += " "+groups[0].year_print
        file_name += ".odt"

        return send_file(f_data, mimetype="application/vnd.oasis.opendocument.text", as_attachment=True,
                         download_name=file_name)

    return render_template('stud_groups_leader.html', stud_groups=groups)


@app.route('/stud_group/<id>', methods=['GET', 'POST'])
@login_required
def stud_group(id):
    if current_user.admin_user is None:
        return render_error(403)

    if id == 'new':
        group = StudGroup()
        now = datetime.now()
        if now.month >= 7 and now.day >= 1:
            group.year = now.year
        else:
            group.year = now.year - 1
        group.active = True

    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        group = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return render_error(404)

    # Запрет на редактирование неактивной группы
    if not group.active:
        return render_error(403)

    form = StudGroupForm(request.form if request.method == 'POST' else None, obj=group)
    if id == 'new':
        form.group_leader.query = form.group_leader2.query = []
    else:
        form.group_leader.query = form.group_leader2.query = db.session.query(Student).join(Person).filter(Student.stud_group_id == id).order_by(Person.surname, Person.firstname, Person.middlename).all()

    if form.button_save.data and form.validate():
        validate = True
        # unique check
        q = db.session.query(StudGroup). \
            filter(StudGroup.year == form.year.data). \
            filter(StudGroup.semester == form.semester.data). \
            filter(StudGroup.num == form.num.data)
        if id != 'new':
            q = q.filter(StudGroup.id != id)

        if q.count() > 0:
            form.num.errors.append('Группа с таким номером уже существует')
            validate = False

        lessons_start_date, session_start_date, session_end_date = form.lessons_start_date.data, form.session_start_date.data, form.session_end_date.data
        if lessons_start_date is not None and session_start_date is not None and lessons_start_date >= session_start_date:
            form.session_start_date.errors.append('Дата начала сессии должна быть позже даты начала занятий')
            validate = False

        if session_start_date is not None and session_end_date is not None and session_start_date >= session_end_date:
            form.session_end_date.errors.append('Дата окончания сессии должна быть позже даты начала')
            validate = False

        if lessons_start_date is not None and session_end_date is not None and lessons_start_date >= session_end_date:
            form.session_end_date.errors.append('Дата окончания сессии должна быть позже даты начала занятий')
            validate = False

        if validate:
            form.populate_obj(group)

            # subnum sub_count correct
            if group.sub_count == 1:
                group.sub_count = 0
                form.sub_count.data = 0

            if group.group_leader is not None and group.group_leader2 is not None and group.group_leader.id == group.group_leader2.id:
                group.group_leader2 = None
                group.group_leader2_id = None
                form.group_leader2.data = None

            db.session.add(group)
            # Корректировка подгрупп у студентов
            if id != 'new':
                for s in group.students:
                    if group.sub_count > 0 and s.stud_group_subnum == 0:
                        s.stud_group_subnum = 1
                        db.session.add(s)
                    if s.stud_group_subnum > group.sub_count:
                        s.stud_group_subnum = group.sub_count
                        db.session.add(s)

            db.session.commit()

            if id == 'new':
                db.session.flush()
                return redirect(url_for('stud_group', id=group.id))

    if form.button_delete.data and id != 'new':
        form.validate()
        if db.session.query(Student).filter(Student.stud_group_id == id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить группу, в которой есть студенты')
        if db.session.query(CurriculumUnit).filter(CurriculumUnit.stud_group_id == id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить группу, к которой привязаны единицы учебного плана')

        if len(form.button_delete.errors) == 0:
            db.session.delete(group)
            db.session.commit()
            db.session.flush()  # ???
            return redirect(url_for('stud_groups'))

    return render_template('stud_group.html', group=group, form=form)


@app.route('/persons')
@login_required
def persons():
    if not current_user.user_rights["persons"]:
        return render_error(403)
    form = PersonSearchForm(request.args)
    result = None
    role = None
    if form.button_search.data and form.validate():
        q = db.session.query(Person)
        role = form.role.data
        if role == 'Student':
            q = q.join(Student, Person.id == Student.person_id)
            if form.student_id.data is not None:
                q = q.filter(Student.id == form.student_id.data)
            else:
                if form.student_financing.data is not None:
                    q = q.filter(Student.financing == form.student_financing.data)
                if form.student_status.data is not None:
                    q = q.filter(Student.status == form.student_status.data)
                if form.student_group.data is not None:
                    q = q.filter(Student.stud_group_id == form.student_group.data.id)

                if form.student_semester.data is not None:
                    q = q.filter(Student.semester == form.student_semester.data)

                if form.student_alumnus_year.data is not None:
                    q = q.filter(Student.alumnus_year == form.student_alumnus_year.data)

                if form.student_expelled_year.data is not None:
                    q = q.filter(Student.expelled_year == form.student_expelled_year.data)

                if form.student_subject_particular.data is not None:
                    q = q.filter(Student.particular_subjects.any(SubjectParticular.id == form.student_subject_particular.data.id))

        if role == 'Teacher':
            q = q.join(Teacher, Person.id == Teacher.person_id)
            if form.teacher_department.data is not None:
                dep_id = form.teacher_department.data.id
                q = q.join(Department, Teacher.department_id == Department.id)
                q = q.filter(or_(Teacher.department_id == dep_id, Department.parent_department_id == dep_id,
                        Teacher.departments_part_time_job.any(or_(Department.id == dep_id, Department.parent_department_id == dep_id))
                    ))

            if form.teacher_status.data == 'yes':
                q = q.filter(Teacher.active)
            if form.teacher_status.data == 'no':
                q = q.filter(not_(Teacher.active))

        if role == 'AdminUser':
            q = q.join(AdminUser, Person.id == AdminUser.person_id)
            if form.admin_user_status.data == 'yes':
                q = q.filter(AdminUser.active)
            if form.admin_user_status.data == 'no':
                q = q.filter(not_(AdminUser.active))

        if form.surname.data != '':
            q = q.filter(or_(Person.surname.like(form.surname.data), Person.id.in_(db.session.query(PersonHist.person_id).filter(PersonHist.surname.like(form.surname.data)))))
        if form.firstname.data != '':
            q = q.filter(Person.firstname.like(form.firstname.data))
        if form.middlename.data != '':
            q = q.filter(Person.middlename.like(form.middlename.data))
        if form.gender.data is not None:
            q = q.filter(Person.gender == form.gender.data)
        if form.login.data != '':
            q = q.filter(Person.login == form.login.data)
        if form.email.data != '':
            q = q.filter(Person.email == form.email.data)
        if form.phone.data is not None:
            q = q.filter(Person.phone == form.phone.data)
        if form.card_number.data is not None:
            q = q.filter(Person.card_number == form.card_number.data)

        q = q.order_by(Person.surname, Person.firstname, Person.middlename)
        page = 1
        if 'page' in request.args:
            try:
                page = int(request.args["page"])
            except ValueError:
                return render_error(400)

        result = q.paginate(page=page, error_out=False)

    return render_template('persons.html', persons=result, form=form, role=role)


@app.route('/person/<id>', methods=['GET', 'POST'])
@login_required
def person(id):
    if current_user.admin_user is None or (not current_user.admin_user.active):
        return render_error(403)
    if id == 'new':
        p = Person()
    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        p = db.session.query(Person).filter(Person.id == id).one_or_none()
        if p is None:
            return render_error(404)

    form = PersonForm(request.form if request.method == 'POST' else None, obj=p)  # WFORMS-Alchemy Объект на форму

    if form.button_delete.data:
        if len(p.roles_all) > 0:
            return render_error(400)

        db.session.delete(p)
        db.session.commit()
        db.session.flush()
        return redirect(url_for('persons'))

    if form.button_save.data and form.validate():
        form.populate_obj(p)
        db.session.add(p)
        if id == 'new':
            db.session.flush()
        hist_save_controller(db.session, p, current_user)
        db.session.commit()
        if id == 'new':
            return redirect(url_for('person', id=p.id))

    return render_template('person.html', person=p, form=form)


@app.route('/profile/<int:id>', methods=['GET', 'POST'])
@login_required
def profile(id):
    if not(current_user.id == id or (current_user.admin_user is not None and current_user.admin_user.active)):
        return render_error(403)

    p: Person = db.session.query(Person).filter(Person.id == id).one_or_none()
    if p is None:
        return render_error(404)

    return render_template('profile.html', person=p)


@app.route('/student/<id>', methods=['GET', 'POST'])
@login_required
def student(id):
    if current_user.admin_user is None or (not current_user.admin_user.active):
        return render_error(403)
    try:
        if id == 'new':
            if "person_id" not in request.args:
                return render_error(400)
            person_id = int(request.args["person_id"])
            p = db.session.query(Person).filter_by(id=person_id).one_or_none()
            if p is None:
                return render_error(400)
            s = Student(person=p)
        else:
            id = int(id)
            s = db.session.query(Student).filter(Student.id == id).one_or_none()
            if s is None:
                return render_error(404)
    except ValueError:
        return render_error(400)

    stud_group_old = s.stud_group if id != 'new' else None

    form = StudentForm(request.form if request.method == 'POST' else None, obj=s)  # WFORMS-Alchemy Объект на форму

    if form.button_delete.data:
        form.validate()
        if db.session.query(AttMark).filter(AttMark.student_id == s.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить студента, у которого есть оценки за аттестации')

        if len(form.button_delete.errors) == 0:
            db.session.delete(s)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('person', id=s.person_id))

    if form.button_save.data and form.validate():
        form.populate_obj(s)  # WFORMS-Alchemy с формы на объект
        if s.status == "alumnus":
            s.stud_group = None
            s.stud_group_subnum = None
            s.expelled_year = None
            if s.alumnus_year is None:
                s.alumnus_year = datetime.now().year

        if s.status in ("expelled", "academic_leave"):
            s.stud_group = None
            s.stud_group_subnum = None
            s.alumnus_year = None
            if s.expelled_year is None:
                s.expelled_year = datetime.now().year

        if s.stud_group is not None:
            s.status = "study"
            # s.semester = s.stud_group.semester
            if s.stud_group.sub_count == 0:
                s.stud_group_subnum = 0
            else:
                if not s.stud_group_subnum:
                    s.stud_group_subnum = 1
                elif s.stud_group_subnum > s.stud_group.sub_count:
                    s.stud_group_subnum = s.stud_group.sub_count

        if s.status == "study":
            s.alumnus_year = None
            s.expelled_year = None

        form = StudentForm(obj=s)

        if form.validate():
            if s.stud_group is not None:
                if s.semester != s.stud_group.semester:
                    form.stud_group.errors.append("Студенческая группа не соответствует семестру студента")
                if s.specialty.id != s.stud_group.specialty_id:
                    form.stud_group.errors.append("Студенческая группа не соответствует направлению/специальности студента")

            if len(form.stud_group.errors) == 0:
                db.session.add(s)
                # снятие старосты группы, при переходе в другую группу
                if stud_group_old is not None and (s.stud_group is None or stud_group_old.id != s.stud_group.id):
                    if stud_group_old.group_leader_id == s.id:
                        stud_group_old.group_leader_id = None
                        db.session.add(stud_group_old)
                    if stud_group_old.group_leader2_id == s.id:
                        stud_group_old.group_leader2_id = None
                        db.session.add(stud_group_old)

                db.session.commit()
                if id == 'new':
                    db.session.flush()
                if s.id != id:
                    return redirect(url_for('student', id=s.id))

    favorite_list_teachers = []
    if id != 'new':
        favorite_list_teachers = db.session.query(Teacher).join(Person).filter(Teacher.favorite_students.any(Student.id == id)).order_by(Person.surname, Person.firstname, Person.middlename).all()

    return render_template('student.html', student=s, form=form, favorite_list_teachers=favorite_list_teachers, stud_groups=db.session.query(StudGroup).filter(StudGroup.active).all())


# Нераспределённые студенты
@app.route('/students_unallocated', methods=['GET'])
@app.route('/students_unallocated/<int:semester>/<int:specialty_id>', methods=['GET', 'POST'])
@login_required
def students_unallocated(semester=None, specialty_id=None):
    if current_user.admin_user is None or (not current_user.admin_user.active):
        return render_error(403)

    specialty = None
    form = None
    stud_groups = None
    if semester is not None and specialty_id is not None:
        specialty = db.session.query(Specialty).filter_by(id=specialty_id).one_or_none()
        if specialty is None:
            return render_error(404)

        students = db.session.query(Student).join(Person) \
                .filter(Student.status == "study") \
                .filter(Student.stud_group_id.is_(None)) \
                .filter(Student.semester == semester) \
                .filter(Student.specialty_id == specialty_id).order_by(Person.surname, Person.firstname, Person.middlename).all()

        form = StudentsUnallocatedForm(request.form)
        form.students_selected.query = students
        stud_groups = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id) \
                .filter(StudGroup.semester == semester) \
                .filter(StudGroup.active) \
                .filter(or_(StudGroup.specialty_id == specialty_id, Specialty.parent_specialty_id == specialty_id)) \
                .order_by(StudGroup.num).all()
        form.stud_group.query = stud_groups

    # Перенос студентов в группы
    result_transfer = None
    if form is not None:
        if form.button_transfer.data and form.validate() and len(form.students_selected.data) > 0:
            g = form.stud_group.data
            stud_group_subnum = form.stud_group_subnum.data
            if g.sub_count == 0:
                stud_group_subnum = 0
            else:
                if stud_group_subnum < 1:
                    stud_group_subnum = 1
                if stud_group_subnum > g.sub_count:
                    stud_group_subnum = g.sub_count

            result_transfer = {
                "students": [],
                "stud_group": g,
                "stud_group_subnum": stud_group_subnum,
                "specialty": g.specialty,
                "semester": semester
            }

            for s in form.students_selected.data:
                s.stud_group = g
                s.stud_group_subnum = stud_group_subnum
                s.specialty_id = g.specialty_id
                s.specialty = g.specialty

                db.session.add(s)
                result_transfer["students"].append(s)
            db.session.commit()
            result_transfer["student_ids"] = set(str(s.id) for s in result_transfer["students"])

    students_count = []
    for _semester, _specialty_id, _cnt in db.session.query(Student.semester, Student.specialty_id, func.count(Student.id)).filter(Student.status == "study").filter(Student.stud_group_id.is_(None)).group_by(Student.semester, Student.specialty_id).order_by(Student.semester, Student.specialty_id):
        students_count.append({
            "semester": _semester,
            "specialty": db.session.query(Specialty).filter_by(id=_specialty_id).one(),
            "count": _cnt
        })

    return render_template('students_unallocated.html',
                           form=form, semester=semester, specialty=specialty, result=result_transfer,
                           students_count=students_count, stud_groups=stud_groups)


# Перевод студентов на следующий семестр
@app.route('/students_transfer', methods=['GET', 'POST'])
@login_required
def students_transfer():
    if current_user.admin_user is None:
        return render_error(403)


@app.route('/subjects')
@login_required
def subjects():
    if current_user.admin_user is None:
        return render_error(403)
    s = db.session.query(Subject).order_by(Subject.name)
    return render_template('subjects.html', subjects=s)


@app.route('/subject/<id>', methods=['GET', 'POST'])
@login_required
def subject(id):
    if current_user.admin_user is None:
        return render_error(403)
    if id == 'new':
        s = Subject()
    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        s = db.session.query(Subject).filter(Subject.id == id).one_or_none()
        if s is None:
            return render_error(404)

    form = SubjectForm(request.form if request.method == 'POST' else None, obj=s)

    # Запретить редактирование предмета связанного с SubjectParticular
    if id != 'new' and db.session.query(SubjectParticular).filter_by(replaced_subject_id=id).count() > 0:
        for field in form:
            field.render_kw = {"disabled": True}

    if form.button_delete.data:
        if db.session.query(SubjectParticular).filter_by(replaced_subject_id=id).count() > 0:
            return render_error(403)
        form.validate()
        if db.session.query(CurriculumUnit).filter(CurriculumUnit.subject_id == s.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить предмет, к которому привязаны единицы учебного плана')
        if len(form.button_delete.errors) == 0:
            db.session.delete(s)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('subjects'))

    if form.button_save.data and form.validate():
        form.populate_obj(s)
        db.session.add(s)
        db.session.commit()
        if id == 'new':
            db.session.flush()
            return redirect(url_for('subject', id=s.id))

    if id != 'new':
        periods_archive = utils.periods_archive(
            query=lambda q: q.join(CurriculumUnit, StudGroup.id == CurriculumUnit.stud_group_id).filter(CurriculumUnit.subject_id == s.id)
        )
        q_curriculum_unit = db.session.query(CurriculumUnit).join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).filter(CurriculumUnit.subject_id == s.id)
        archive_year, archive_semester = None, None
        if "archive_year" in request.args and "archive_semester" in request.args:
            try:
                archive_year, archive_semester = int(request.args["archive_year"]), int(
                    request.args["archive_semester"])
            except ValueError:
                return render_error(400)
        if archive_year is not None and archive_semester is not None:
            sem = 0 if archive_semester == 2 else archive_semester
            q_curriculum_unit = q_curriculum_unit.filter(not_(StudGroup.active)).filter(StudGroup.year == archive_year).filter(
                func.mod(StudGroup.semester, 2) == sem)
        else:
            q_curriculum_unit = q_curriculum_unit.filter(StudGroup.active)

        cus = q_curriculum_unit.order_by(StudGroup.semester, StudGroup.num).all()
    else:
        periods_archive = []
        cus = []
        archive_year = None
        archive_semester = None

    return render_template('subject.html', subject=s, form=form, curriculum_units=cus,
                           periods_archive=periods_archive, archive_year=archive_year,
                           archive_semester=archive_semester)


@app.route('/teacher/<id>', methods=['GET', 'POST'])
@login_required
def teacher(id):
    if current_user.admin_user is None or (not current_user.admin_user.active):
        return render_error(403)

    form_department_part_job_time_add = None

    try:
        if id == 'new':
            if "person_id" not in request.args:
                return render_error(400)
            person_id = int(request.args["person_id"])
            p = db.session.query(Person).filter_by(id=person_id).one_or_none()
            if p is None:
                return render_error(400)
            t = Teacher(person=p, active=True)

            if request.args.get('department_id') is not None:
                department_id = int(request.args.get('department_id'))

                d = db.session.query(Department).filter_by(id=department_id).one_or_none()
                if d is not None:
                    t.department = d
        else:
            id = int(id)
            t = db.session.query(Teacher).filter_by(id=id).one_or_none()
            if t is None:
                return render_error(404)

    except ValueError:
        return render_error(400)

    form = TeacherForm(request.form if request.method == 'POST' else None, obj=t)
    if t.id is not None:
        form_department_part_job_time_add = TeacherAddDepartmentPartTimeJobForm()
        form_department_part_job_time_add.department.query_factory = \
            lambda: db.session.query(Department) \
                    .filter(Department.id != t.department_id) \
                    .filter(Department.id.notin_([d.id for d in t.departments_part_time_job]) if len(t.departments_part_time_job) > 0 else True) \
                    .order_by(Department.id).all()

    if form.button_delete.data:
        form.validate()
        if db.session.query(CurriculumUnit).filter(
                or_(CurriculumUnit.teacher_id == t.id, CurriculumUnit.practice_teachers.any(Teacher.id == t.id))).count() > 0:
            form.button_delete.errors.append(
                'Невозможно удалить преподавателя, к которому привязаны единицы учебного плана')

        if len(form.button_delete.errors) == 0:
            db.session.delete(t)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('person', id=t.person_id))

    if form.button_save.data and form.validate():
        form.populate_obj(t)

        if not t.active and id != 'new' and db.session.query(CurriculumUnit).join(StudGroup).filter(
                StudGroup.active).filter(
            or_(CurriculumUnit.teacher_id == t.id, CurriculumUnit.practice_teachers.any(Teacher.id == t.id))).count() > 0:
            form.active.errors.append(
                'Невозможно снять атрибут "Работает". К преподавателю привязаны действующие единицы учебного плана')
        else:
            if not t.active or (t.department.id != Department.ID_DEFAULT and t.department.parent_department_id != Department.ID_DEFAULT):
                t.dean_staff = False
                t.department_leader = False
                t.right_read_all = False

            # удалить кафедру по совместительству, если она поставлена как основная
            for d in t.departments_part_time_job:
                if d.id == t.department.id:
                    t.departments_part_time_job.remove(d)
                    break

            if not t.dean_staff:
                t.notify_results_fail = False

            db.session.add(t)

            # Удалить кураторство действующих групп
            if not t.active and id != 'new':
                for sg in db.session.query(StudGroup).filter(StudGroup.active).filter(StudGroup.curator_id == id).all():
                    sg.curator_id = None
                    db.session.add(sg)

            db.session.commit()
            if id == 'new':
                db.session.flush()
                return redirect(url_for('teacher', id=t.id))

    return render_template('teacher.html', teacher=t, form=form, form_department_part_job_time_add=form_department_part_job_time_add)


@app.route('/teacher/<int:id>/department_part_job_time/add', methods=['GET', 'POST'])
@login_required
def teacher_department_part_job_time_add(id):
    t = db.session.query(Teacher).filter(Teacher.id == id).one_or_none()
    if t is None:
        return render_error(404)

    if current_user.admin_user is None or (not current_user.admin_user.active):
        return render_error(403)

    form = TeacherAddDepartmentPartTimeJobForm(request.form)

    department = form.department.data

    if not department or department.id == t.department_id:
        return render_error(400)

    for d in t.departments_part_time_job:
        if d.id == department.id:
            return redirect(url_for('teacher', id=id))

    t.departments_part_time_job.append(department)
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('teacher', id=id))


@app.route('/teacher/<int:id>/department_part_job_time/remove/<int:department_id>', methods=['GET', 'POST'])
@login_required
def teacher_department_part_job_time_remove(id, department_id):
    t = db.session.query(Teacher).filter(Teacher.id == id).one_or_none()
    if t is None:
        return render_error(404)

    if current_user.admin_user is None or (not current_user.admin_user.active):
        return render_error(403)

    department = None
    for d in t.departments_part_time_job:
        if d.id == department_id:
            department = d
            break

    if department:
        t.departments_part_time_job.remove(department)
        db.session.add(t)
        db.session.commit()
    return redirect(url_for('teacher', id=id))


@app.route('/teacher_report/<int:id>')
@login_required
def teacher_report(id):
    # Проверка прав доступа
    if not ((current_user.admin_user is not None and current_user.admin_user.active) or
            (current_user.teacher is not None and current_user.teacher.id == id) or current_user.user_rights["persons"]):
        return render_error(403)

    t = db.session.query(Teacher).filter(Teacher.id == id).one_or_none()
    if t is None:
        return render_error(404)

    archive_year, archive_semester = None, None
    if "archive_year" in request.args and "archive_semester" in request.args:
        try:
            archive_year, archive_semester = int(request.args["archive_year"]), int(request.args["archive_semester"])
        except ValueError:
            return render_error(400)
    if archive_year is not None and archive_semester is not None:
        s = 0 if archive_semester == 2 else archive_semester
        q_stud_groups = lambda q: q.filter(not_(StudGroup.active)).filter(StudGroup.year == archive_year).filter(func.mod(StudGroup.semester, 2) == s)
    else:
        q_stud_groups = lambda q: q.filter(StudGroup.active)

    curriculum_units = q_stud_groups(db.session.query(CurriculumUnit).join(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id)) \
        .filter(CurriculumUnit.teacher_id == id) \
        .order_by(func.isnull(CurriculumUnit.curriculum_unit_group_id), func.IF(CurriculumUnit.curriculum_unit_group_id.isnot(None), CurriculumUnit.curriculum_unit_group_id, CurriculumUnit.subject_id), Specialty.education_level_order, StudGroup.semester, StudGroup.num) \
        .all()

    curriculum_units_practice = q_stud_groups(db.session.query(CurriculumUnit).join(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id)) \
        .filter(CurriculumUnit.practice_teachers.any(Teacher.id == id)) \
        .order_by(func.isnull(CurriculumUnit.curriculum_unit_group_id), func.IF(CurriculumUnit.curriculum_unit_group_id.isnot(None), CurriculumUnit.curriculum_unit_group_id, CurriculumUnit.subject_id), Specialty.education_level_order, StudGroup.semester, StudGroup.num) \
        .all()

    groups = q_stud_groups(db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id)) \
        .filter(StudGroup.curator_id == id) \
        .order_by(StudGroup.year, Specialty.education_level_order, StudGroup.semester, StudGroup.num) \
        .all()
    periods_archive = utils.periods_archive(
        query=lambda q: q.join(CurriculumUnit, StudGroup.id == CurriculumUnit.stud_group_id). \
            filter(or_(CurriculumUnit.teacher_id == t.id, CurriculumUnit.practice_teachers.any(Teacher.id == t.id), StudGroup.curator_id == t.id))
    )

    return render_template('teacher_report.html',
                           curriculum_units=curriculum_units,
                           curriculum_units_practice=curriculum_units_practice,
                           stud_groups=groups,
                           periods_archive=periods_archive,
                           archive_year=archive_year,
                           archive_semester=archive_semester,
                           teacher=t)


@app.route('/curriculum_unit/<id>', methods=['GET', 'POST'])
@login_required
def curriculum_unit(id):
    if id == 'new':
        if current_user.admin_user is None or not current_user.admin_user.active:
            return render_error(403)
        sg = None
        sbj = None
        if 'stud_group_id' in request.args:
            try:
                sg = db.session.query(StudGroup). \
                    filter(StudGroup.id == int(request.args['stud_group_id'])).one_or_none()
            except ValueError:
                sg = None
        if 'subject_id' in request.args:
            try:
                sbj = db.session.query(Subject). \
                    filter(Subject.id == int(request.args['subject_id'])).one_or_none()
            except ValueError:
                sbj = None

        cu = CurriculumUnit(stud_group=sg, subject=sbj, closed=False)
    else:
        try:
            id = int(id)
        except ValueError:
            return render_error(400)
        cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
        if cu is None:
            return render_error(404)

        if current_user.admin_user is None or not current_user.admin_user.active:
            if current_user.teacher is None or cu.teacher_id != current_user.teacher.id:
                return render_error(403)

    # Запрет редактирования неактивной единицы учебного плана
    readonly = (cu.stud_group is not None and not cu.stud_group.active) or cu.closed or cu.pass_department

    readonly_fields = {}
    hours_old = None
    if current_user.admin_user is None or (not current_user.admin_user.active):
        readonly_fields = {
            "curriculum_unit_group_id": cu.curriculum_unit_group_id,
            "code": cu.code,
            "teacher": cu.teacher,
            "department": cu.department,
            "stud_group": cu.stud_group,
            "subject": cu.subject,
            "mark_type": cu.mark_type,
            "use_topic": cu.use_topic,
            "hours_lect": cu.hours_lect,
            "hours_pract": cu.hours_pract,
            "hours_lab": cu.hours_lab,
            "has_simple_mark_test_simple": cu.has_simple_mark_test_simple,
            "has_simple_mark_exam": cu.has_simple_mark_exam,
            "has_simple_mark_test_diff": cu.has_simple_mark_test_diff,
            "has_simple_mark_course_work": cu.has_simple_mark_course_work,
            "has_simple_mark_course_project": cu.has_simple_mark_course_project
        }
        hours_old = (cu.hours_att_1, cu.hours_att_2, cu.hours_att_3)

    form = CurriculumUnitForm(request.form if request.method == 'POST' else None, obj=cu)

    form_practice_teacher_add = None

    if cu.teacher is not None and not readonly:
        form_practice_teacher_add = CurriculumUnitPracticeTeacherAddForm()
        form_practice_teacher_add.teacher.query_factory = lambda:  db.session.query(Teacher).join(Person).order_by(Person.surname, Person.firstname, Person.middlename).filter(
                    Teacher.active).filter(or_(Teacher.department_id == cu.department_id, Teacher.departments_part_time_job.any(Department.id == cu.department_id))).filter(Teacher.id != cu.teacher.id).filter(Teacher.id.notin_([t.id for t in cu.practice_teachers]) if len(cu.practice_teachers) > 0 else True).all()

    curriculum_unit_group_rels = None
    teacher_departments = []

    if readonly:
        for field in form:
            field.render_kw = {"disabled": True}
    else:
        for k in readonly_fields:
            setattr(cu, k, readonly_fields[k])
            getattr(form, k).data = readonly_fields[k]
            getattr(form, k).render_kw = {"disabled": True}

        if "curriculum_unit_group_id" not in readonly_fields and form.teacher.data is not None and form.stud_group.data is not None:
            q_curriculum_unit_group_rel_ids = db.session.query(CurriculumUnit.curriculum_unit_group_id).join(StudGroup).filter(CurriculumUnit.curriculum_unit_group_id.isnot(None)).filter(StudGroup.active).filter(CurriculumUnit.stud_group_id != form.stud_group.data.id).filter(CurriculumUnit.teacher_id == form.teacher.data.id)
            if id != 'new':
                q_curriculum_unit_group_rel_ids = q_curriculum_unit_group_rel_ids.filter(CurriculumUnit.id != id)
            curriculum_unit_group_rel_ids = [row[0] for row in q_curriculum_unit_group_rel_ids.distinct()]
            curriculum_unit_group_rels = []
            for curriculum_unit_group_rel_id in curriculum_unit_group_rel_ids:
                curriculum_unit_group_rels.append((curriculum_unit_group_rel_id,
                                                   db.session.query(Subject).join(CurriculumUnit, CurriculumUnit.subject_id == Subject.id).filter(CurriculumUnit.curriculum_unit_group_id == curriculum_unit_group_rel_id).distinct().all()))

        if "teacher" not in readonly_fields and "department" not in readonly_fields:
            for t in form.teacher.query_factory():
                teacher_departments.append({"teacher_id": t.id, "department_ids": [d.id for d in t.departments]})

        if form.button_delete.data:
            if current_user.admin_user is None:
                return render_error(403)
            form.validate()
            if db.session.query(AttMark).filter(AttMark.curriculum_unit_id == cu.id).count() > 0:
                form.button_delete.errors.append('Невозможно удалить единицу учебного плана к которой привязаны оценки')
            if len(form.button_delete.errors) == 0:
                for cu_h in cu.status_history:
                    db.session.delete(cu_h)
                db.session.delete(cu)
                db.session.commit()
                db.session.flush()
                return redirect(url_for('stud_group', id=cu.stud_group.id, _anchor='curriculum_units'))

        if form.button_save.data and form.validate():
            # unique check
            q_u_chk1 = db.session.query(CurriculumUnit).filter(CurriculumUnit.stud_group_id == form.stud_group.data.id). \
                filter(CurriculumUnit.subject_id == form.subject.data.id)
            q_u_chk2 = db.session.query(CurriculumUnit).filter(CurriculumUnit.stud_group_id == form.stud_group.data.id). \
                filter(CurriculumUnit.code == form.code.data)

            if id != 'new':
                q_u_chk1 = q_u_chk1.filter(CurriculumUnit.id != id)
                q_u_chk2 = q_u_chk2.filter(CurriculumUnit.id != id)
            if q_u_chk1.count() > 0:
                form.subject.errors.append('Уже существует единица учебного плана с таким предметом у данной группы')
            if q_u_chk2.count() > 0:
                form.code.errors.append('Уже существует единица учебного плана с таким кодом у данной группы')

            if form.mark_type.data != "no_att" and form.hours_att_1.data == form.hours_att_2.data == form.hours_att_3.data == 0:
                form.hours_att_3.errors.append("Количество часов не может быть равно нулю")

            if form.curriculum_unit_group_id.data is not None:
                # Проверка на корректность кода объединения предметов
                q_u_g_chk = db.session.query(CurriculumUnit).join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).filter(CurriculumUnit.curriculum_unit_group_id == form.curriculum_unit_group_id.data)

                if q_u_g_chk.filter(not_(StudGroup.active)).count() > 0:
                    form.curriculum_unit_group_id.errors.append("Код объединения предметов уже был использован для неактивных студенческих групп")

                if q_u_g_chk.filter(CurriculumUnit.teacher_id != form.teacher.data.id).count() > 0:
                    form.curriculum_unit_group_id.errors.append(
                        "Код объединения предметов уже был использован другим преподавателем")

                if id != 'new':
                    q_u_g_chk = q_u_g_chk.filter(CurriculumUnit.id != id)

                if q_u_g_chk.filter(StudGroup.id == form.stud_group.data.id).count() > 0:
                    form.curriculum_unit_group_id.errors.append(
                        "Код объединения предметов уже используется для данной студенческой группы")

            if len(form.subject.errors) == 0 and len(form.code.errors) == 0 and len(form.hours_att_3.errors) == 0 and len(form.curriculum_unit_group_id.errors) == 0:
                form.populate_obj(cu)
                if not cu.stud_group.active:
                    form.stud_group.errors.append('Невозможно добавить запись для неактивной студенческой группы')
                else:
                    hours = (cu.hours_att_1, cu.hours_att_2, cu.hours_att_3)
                    if hours_old is not None and (sum(hours) != sum(hours_old) or tuple(map(bool, hours_old)) != tuple(map(bool, hours))):
                        if bool(hours_old[0]) != bool(cu.hours_att_1):
                            form.hours_att_1.errors.append('Сумма часов должна быть %s' % 'больше нуля' if hours_old[0] else 'равна нулю')
                        if bool(hours_old[1]) != bool(cu.hours_att_2):
                            form.hours_att_2.errors.append('Сумма часов должна быть %s' % 'больше нуля' if hours_old[1] else 'равна нулю')
                        if bool(hours_old[2]) != bool(cu.hours_att_3):
                            form.hours_att_3.errors.append('Сумма часов должна быть %s' % 'больше нуля' if hours_old[2] else 'равна нулю')
                        if sum(cu.hours) != sum(hours_old):
                            form.hours_att_3.errors.append('Сумма часов должна быть равна %d' % sum(hours_old))
                    else:
                        # SAVE CU
                        if cu.mark_type == "no_att":
                            cu.hours_att_1 = 0
                            cu.hours_att_2 = 0
                            cu.hours_att_3 = 0
                        if cu.mark_type == "no_mark":
                            cu.use_topic = 'none'
                            cu.has_simple_mark_test_simple = False
                            cu.has_simple_mark_exam = False
                            cu.has_simple_mark_test_diff = False
                            cu.has_simple_mark_course_work = False
                            cu.has_simple_mark_course_project = False

                        if cu.mark_type == "test_simple":
                            cu.has_simple_mark_test_simple = False
                        if cu.mark_type == "exam":
                            cu.has_simple_mark_exam = False
                        if cu.mark_type == "test_diff":
                            cu.has_simple_mark_test_diff = False

                        if cu.use_topic == 'coursework' and len(cu.practice_teachers) == 0:
                            teachers_list = db.session.query(Teacher) \
                                .filter(Teacher.department_id == cu.department_id) \
                                .filter(Teacher.id != cu.teacher_id) \
                                .filter(Teacher.active) \
                                .filter(Teacher.rank != "магистр") \
                                .all()
                            for t in teachers_list:
                                cu.practice_teachers.append(t)

                        if len(cu.practice_teachers) == 0:
                            cu.allow_edit_practice_teacher_att_mark_1 = \
                                cu.allow_edit_practice_teacher_att_mark_2 = \
                                cu.allow_edit_practice_teacher_att_mark_3 = \
                                cu.allow_edit_practice_teacher_att_mark_exam = \
                                cu.allow_edit_practice_teacher_att_mark_append_ball = \
                                cu.allow_edit_practice_teacher_simple_mark_test_simple = \
                                cu.allow_edit_practice_teacher_simple_mark_exam = \
                                cu.allow_edit_practice_teacher_simple_mark_test_diff = \
                                cu.allow_edit_practice_teacher_simple_mark_course_work = \
                                cu.allow_edit_practice_teacher_simple_mark_course_project = False
                        else:
                            if "att_mark_1" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_att_mark_1 = False
                            if "att_mark_2" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_att_mark_2 = False
                            if "att_mark_3" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_att_mark_3 = False
                            if "att_mark_exam" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_att_mark_exam = False
                            if "att_mark_append_ball" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_att_mark_append_ball = False
                            if "simple_mark_test_simple" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_simple_mark_test_simple = False
                            if "simple_mark_exam" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_simple_mark_exam = False
                            if "simple_mark_test_diff" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_simple_mark_test_diff = False
                            if "simple_mark_course_work" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_simple_mark_course_work = False
                            if "simple_mark_course_project" not in cu.visible_attrs:
                                cu.allow_edit_practice_teacher_simple_mark_course_project = False

                        db.session.add(cu)

                        if id == 'new':
                            db.session.flush()

                        hist_save_controller(db.session, cu, current_user)
                        db.session.commit()
                        if id == 'new':
                            return redirect(url_for('curriculum_unit', id=cu.id))
                        # END SAVE CU

        if cu.stud_group is not None:
            form.stud_group.render_kw = {"disabled": True}

        if cu.subject is not None:
            form.subject.render_kw = {"disabled": True}

        # end not readonly

    return render_template('curriculum_unit.html', curriculum_unit=cu, form=form, form_practice_teacher_add=form_practice_teacher_add, curriculum_unit_group_rels=curriculum_unit_group_rels, teacher_departments=teacher_departments)


@app.route('/curriculum_unit/<int:id>/practice_teacher/add', methods=['GET', 'POST'])
@login_required
def curriculum_unit_practice_teacher_add(id):
    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return render_error(404)

    if current_user.admin_user is None:
        if current_user.teacher is None or cu.teacher_id != current_user.teacher.id:
            return render_error(403)
    if (not cu.stud_group.active) or cu.closed or cu.pass_department:
        return render_error(403)

    form = CurriculumUnitPracticeTeacherAddForm(request.form)

    practice_teacher = form.teacher.data

    if not practice_teacher or practice_teacher.id == cu.teacher_id:
        return render_error(400)

    for t in cu.practice_teachers:
        if t.id == practice_teacher.id:
            return redirect(url_for('curriculum_unit', id=id))

    cu.practice_teachers.append(practice_teacher)

    db.session.add(cu)

    hist_save_controller(db.session, cu, current_user, check_journalize_attributes=False)

    db.session.commit()
    return redirect(url_for('curriculum_unit', id=id))


@app.route('/curriculum_unit/<int:id>/practice_teacher/remove/<int:practice_teacher_id>')
@login_required
def curriculum_unit_practice_teacher_remove(id, practice_teacher_id):
    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return render_error(404)

    if current_user.admin_user is None or not current_user.admin_user.active:
        if current_user.teacher is None or cu.teacher_id != current_user.teacher.id:
            return render_error(403)
    if (not cu.stud_group.active) or cu.closed or cu.pass_department:
        return render_error(403)

    practice_teacher = None
    for t in cu.practice_teachers:
        if t.id == practice_teacher_id:
            practice_teacher = t
            break
    if practice_teacher:
        cu.practice_teachers.remove(practice_teacher)
    else:
        return redirect(url_for('curriculum_unit', id=id))

    if len(cu.practice_teachers) == 0:
        cu.allow_edit_practice_teacher_att_mark_1 = \
            cu.allow_edit_practice_teacher_att_mark_2 = \
            cu.allow_edit_practice_teacher_att_mark_3 = \
            cu.allow_edit_practice_teacher_att_mark_exam = \
            cu.allow_edit_practice_teacher_att_mark_append_ball = \
            cu.allow_edit_practice_teacher_simple_mark_test_simple = \
            cu.allow_edit_practice_teacher_simple_mark_exam = \
            cu.allow_edit_practice_teacher_simple_mark_test_diff = \
            cu.allow_edit_practice_teacher_simple_mark_course_work = \
            cu.allow_edit_practice_teacher_simple_mark_course_project = False
    db.session.add(cu)

    hist_save_controller(db.session, cu, current_user, check_journalize_attributes=False)

    db.session.commit()
    return redirect(url_for('curriculum_unit', id=id))


@app.route('/curriculum_unit_history_doc/<int:id>/<stime>')
@app.route('/curriculum_unit_history_doc/<int:id>/<stime>/<mark_type>')
@login_required
def curriculum_unit_history_doc(id, stime, mark_type=None):
    try:
        stime = datetime.strptime(stime, app.config['DATE_TIME_FORMAT'])
    except ValueError:
        return render_error(400)

    cu_h = db.session.query(CurriculumUnitStatusHist). \
        filter(CurriculumUnitStatusHist.curriculum_unit_id == id). \
        filter(CurriculumUnitStatusHist.stime == stime).one_or_none()

    if cu_h is None:
        return render_error(404)

    doc_attr = None
    if mark_type is None:
        doc_attr = "doc"
    elif mark_type == "test_simple":
        doc_attr = "doc_test_simple"
    elif mark_type == "exam":
        doc_attr = "doc_exam"
    elif mark_type == "test_diff":
        doc_attr = "doc_test_diff"
    elif mark_type == "course_work":
        doc_attr = "doc_course_work"
    elif mark_type == "course_project":
        doc_attr = "doc_course_project"
    if doc_attr is None:
        return render_error(400)

    if getattr(cu_h, doc_attr) is None:
        return render_error(404)

    cu = cu_h.curriculum_unit

    if not cu.get_rights(current_user)["read"]:
        return render_error(403)

    file_name = "Аттестационная_ведомость_%d_к_%s_гр_%s_%s_%s.odt" % (
        cu.stud_group.course,
        cu.stud_group.num,
        cu.subject_name_print.replace("(", "").replace(")", "").replace(" ", "_"),
        (cu_h.etime or cu_h.stime).strftime("%Y-%m-%d_%H_%M_%S"),
        MarkSimpleTypeDict[mark_type] if mark_type is not None else cu.mark_type_name
    )

    f_data = io.BytesIO(getattr(cu_h, doc_attr))
    f_data.seek(0)
    return send_file(f_data, mimetype="application/vnd.oasis.opendocument.text", as_attachment=True,
                     download_name=file_name)


@app.route('/curriculum_unit_copy/<int:id>', methods=['GET', 'POST'])
@login_required
def curriculum_unit_copy(id):
    if current_user.admin_user is None:
        return render_error(403)

    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return render_error(404)

    if cu.closed or not cu.stud_group.active:
        return render_error(400)

    form = CurriculumUnitCopyForm(request.form)
    form.stud_groups_selected.query_factory = lambda: db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id). \
        filter(StudGroup.active). \
        filter(StudGroup.year == cu.stud_group.year). \
        filter(StudGroup.semester == cu.stud_group.semester). \
        filter(Specialty.education_level_order == cu.stud_group.specialty.education_level_order). \
        filter(not_(StudGroup.id.in_(
        db.session.query(CurriculumUnit.stud_group_id).filter(CurriculumUnit.subject_id == cu.subject.id).subquery()))). \
        order_by(StudGroup.num).all()

    stud_group_ids = set()
    if form.button_copy.data and form.validate() and len(form.stud_groups_selected.data) > 0:
        cu_news = []
        for sg in form.stud_groups_selected.data:
            cu_new = CurriculumUnit(
                code=cu.code,
                stud_group=sg,
                subject=cu.subject,
                department=cu.department,
                teacher=cu.teacher,
                hours_att_1=cu.hours_att_1,
                hours_att_2=cu.hours_att_2,
                hours_att_3=cu.hours_att_3,
                hours_lect=cu.hours_lect,
                hours_pract=cu.hours_pract,
                hours_lab=cu.hours_lab,
                mark_type=cu.mark_type,
                has_simple_mark_test_simple=cu.has_simple_mark_test_simple,
                has_simple_mark_exam=cu.has_simple_mark_exam,
                has_simple_mark_test_diff=cu.has_simple_mark_test_diff,
                has_simple_mark_course_work=cu.has_simple_mark_course_work,
                has_simple_mark_course_project=cu.has_simple_mark_course_project,
                closed=False
            )
            db.session.add(cu_new)
            cu_news.append(cu_new)
            stud_group_ids.add(sg.id)
        db.session.flush()
        for cu_new in cu_news:
            hist_save_controller(db.session, cu_new, current_user)

        db.session.commit()

    curriculum_units_other = db.session.query(CurriculumUnit).join(StudGroup). \
        filter(StudGroup.semester == cu.stud_group.semester).\
        filter(CurriculumUnit.subject_id == cu.subject.id).\
        filter(StudGroup.id != cu.stud_group.id).\
        filter(StudGroup.active).order_by(StudGroup.num).all()

    return render_template('curriculum_unit_copy.html',
                           curriculum_unit=cu,
                           curriculum_units_other=curriculum_units_other,
                           stud_group_ids=stud_group_ids,
                           form=form)


@app.route('/att_marks/<int:id>', methods=['GET', 'POST'])
@login_required
def att_marks(id):
    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return render_error(404)

    if not cu.get_rights(current_user)["read"]:
        return render_error(403)

    if (not cu.closed) and (not cu.pass_department):
        # Создание записей AttMark если их нет для данной единицы учебного плана
        _students = db.session.query(Student).filter(Student.stud_group_id == cu.stud_group.id).\
                filter(not_(Student.id.in_(
                db.session.query(AttMark.student_id).filter(AttMark.curriculum_unit_id == cu.id).subquery()))).all()
        if len(_students) > 0:
            att_mark_news = []
            for s in _students:
                # не добавлять particular_subjects
                if cu.subject_id in ((sp.replaced_subject_id for sp in s.particular_subjects if sp.replaced_subject_id is not None)):
                    continue

                att_mark = AttMark(curriculum_unit=cu, student=s)
                cu.att_marks.append(att_mark)
                db.session.add(att_mark)
                att_mark_news.append(att_mark)
            db.session.flush()
            for att_mark in att_mark_news:
                hist_save_controller(db.session, att_mark, current_user)
            db.session.commit()

    form = AttMarksForm(request.form, obj=cu)

    form_student_add = None

    if current_user.admin_user is not None and current_user.admin_user.active:
        if cu.stud_group.active and not cu.closed and not cu.pass_department:
            form_student_add = AttMarksStudentAddForm()

    all_teachers = lambda: cu.practice_teachers + [cu.teacher]

    if (current_user.admin_user is not None and current_user.admin_user.active) or current_user.teacher.id == cu.teacher_id:
        teacher_query_factory = all_teachers
    else:
        teacher_query_factory = lambda: [current_user.teacher]

    for f_elem in form.att_marks:
        if f_elem.object_data.teacher is not None:
            f_elem.teacher.query_factory = all_teachers
        else:
            f_elem.teacher.query_factory = teacher_query_factory

    if form.button_clear.data:
        if current_user.admin_user is None or not current_user.admin_user.active:
            return render_error(403)
        if cu.closed or cu.pass_department or cu.status == "exam":
            return render_error(400)

        db.session.query(AttMark).filter(AttMark.curriculum_unit_id == cu.id).delete(synchronize_session=False)
        db.session.query(CurriculumUnitStatusHist).filter(
            CurriculumUnitStatusHist.curriculum_unit_id == cu.id).delete(synchronize_session=False)

        db.session.flush()
        db.session.commit()
        return redirect(url_for('curriculum_unit', id=cu.id))

    if form.button_print.data:
        if cu.mark_type == "no_att":
            return render_error(400)
        f = create_doc_curriculum_unit(cu)
        f_data = io.BytesIO()
        with open(f, 'rb') as fo:
            f_data.write(fo.read())
        f_data.seek(0)
        os.remove(f)

        return send_file(f_data, mimetype="application/vnd.oasis.opendocument.text", as_attachment=True,
                         download_name=cu.file_name)

    print_mark_type = None
    if form.button_print_simple_marks_test_simple.data:
        if not cu.has_simple_mark_test_simple:
            return render_error(400)
        print_mark_type = "test_simple"
    if form.button_print_simple_marks_exam.data:
        if not cu.has_simple_mark_exam:
            return render_error(400)
        print_mark_type = "exam"
    if form.button_print_simple_marks_test_diff.data:
        if not cu.has_simple_mark_test_diff:
            return render_error(400)
        print_mark_type = "test_diff"
    if form.button_print_simple_marks_course_work.data:
        if not cu.has_simple_mark_course_work:
            return render_error(400)
        print_mark_type = "course_work"
    if form.button_print_simple_marks_course_project.data:
        if not cu.has_simple_mark_course_project:
            return render_error(400)
        print_mark_type = "course_project"

    if print_mark_type is not None:
        f = create_doc_curriculum_unit_simple_marks(cu, print_mark_type)
        f_data = io.BytesIO()
        with open(f, 'rb') as fo:
            f_data.write(fo.read())
        f_data.seek(0)
        os.remove(f)

        return send_file(f_data, mimetype="application/vnd.oasis.opendocument.text", as_attachment=True,
                         download_name=cu.file_name_mark_type_format(print_mark_type))

    if form.button_close.data:
        if not cu.get_rights(current_user)["close"]:
            return render_error(403)

        for m in cu.att_marks:
            if m.att_mark_id in cu.att_marks_readonly_ids and m.exclude is None:
                m.exclude = 1
            m.attendance_rate_cached = m.attendance_rate_raw
            db.session.add(m)

        f_map = {}
        if cu.mark_type != "no_att":
            f_map["doc"] = create_doc_curriculum_unit(cu)
        if cu.has_simple_mark_test_simple:
            f_map["doc_test_simple"] = create_doc_curriculum_unit_simple_marks(cu, "test_simple")
        if cu.has_simple_mark_test_diff:
            f_map["doc_test_diff"] = create_doc_curriculum_unit_simple_marks(cu, "test_diff")
        if cu.has_simple_mark_exam:
            f_map["doc_exam"] = create_doc_curriculum_unit_simple_marks(cu, "exam")
        if cu.has_simple_mark_course_work:
            f_map["doc_course_work"] = create_doc_curriculum_unit_simple_marks(cu, "course_work")
        if cu.has_simple_mark_course_project:
            f_map["doc_course_project"] = create_doc_curriculum_unit_simple_marks(cu, "course_project")

        cu.closed = True
        db.session.add(cu)
        cu_h, cu_h_n = hist_save_controller(db.session, cu, current_user)
        if cu_h is not None:
            for doc_attr, f in f_map.items():
                with open(f, 'rb') as fo:
                    setattr(cu_h, doc_attr, fo.read())
                    db.session.add(cu_h)

        db.session.commit()

        for doc_attr, f in f_map.items():
            os.remove(f)

    if form.button_open.data:
        if not cu.get_rights(current_user)["open"]:
            return render_error(403)

        for m in cu.att_marks:
            if m.exclude == 1:
                m.exclude = None
            m.attendance_rate_cached = None
            db.session.add(m)

        cu.closed = False
        cu.pass_department = False
        db.session.add(cu)
        hist_save_controller(db.session, cu, current_user)
        db.session.commit()

    if form.button_save.data:
        if not cu.get_rights(current_user)["write"]:
            return render_error(403)

        if form.validate():
            for f_elem in form.att_marks:
                m = f_elem.object_data
                # update att_mark
                if m.att_mark_id not in cu.att_marks_readonly_ids:
                    for k, v in f_elem.data.items():

                        if m.check_edit_attr(k, current_user):
                            setattr(m, k, v)
                    db.session.add(m)
                    hist_save_controller(db.session, m, current_user)

            db.session.commit()

    return render_template(
        'att_marks.html',
        curriculum_unit=cu,
        form=form,
        form_student_add=form_student_add
    )


@app.route('/att_marks_history/<int:id>')
@login_required
def att_marks_history(id):

    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return render_error(404)

    # Проверка прав доступа
    if not cu.get_rights(current_user)["read"]:
        return render_error(403)

    stimes = set()
    for m in cu.att_marks:
        for h in m.history:
            stimes.add(h.stime)

    stimes = sorted(stimes, reverse=True)
    if len(stimes) == 0:
        return render_error(404)

    if "stime" in request.args:
        try:
            stime = datetime.strptime(request.args["stime"], app.config['DATE_TIME_FORMAT'])
        except ValueError:
            return render_error(400)

    else:
        stime = stimes[0]

    nvl = lambda x, default: default if x is None else x
    now = datetime.now()

    att_marks_hist = []
    att_marks_hist_pred = []
    cu.att_marks.sort(key=lambda m: (m.student.person.surname, m.student.person.firstname, m.student.person.middlename if m.student.person.middlename is not None else ''))
    for m in cu.att_marks:
        try:
            att_marks_hist.append(next(h for h in m.history if h.stime <= stime < nvl(h.etime, now)))
            att_marks_hist_pred.append(next((h for h in m.history if h.etime is not None and h.etime <= stime), None))
        except StopIteration:
            att_marks_hist.append(AttMarkHist(att_mark=m))
            att_marks_hist_pred.append(None)

    if len(att_marks_hist) == 0:
        return render_error(404)

    # Убрать атрибуты, которые все None
    attrs = list(att_marks_hist[0].att_mark.journalize_attributes)
    for attr in attrs[:0:-1]:
        if all(getattr(h, attr) is None for h in att_marks_hist):
            attrs.remove(attr)
        else:
            break

    return render_template(
        'att_marks_history.html',
        curriculum_unit=cu,
        att_marks_hist=att_marks_hist,
        att_marks_hist_pred=att_marks_hist_pred,
        attrs=attrs,
        stime=stime,
        stimes=stimes
    )


def _previous_stud_groups_map(stud_group: StudGroup, current_user: Person):
    result = {}
    if not stud_group.active:
        return result
    semester = stud_group.semester
    year = stud_group.year
    num = stud_group.num
    while semester > 1:
        semester -= 1
        if semester % 2 == 0:
            year -= 1
        sg = db.session.query(StudGroup).filter_by(year=year, semester=semester, num=num).one_or_none()
        if sg is not None:
            if current_user is None or sg.get_rights(current_user)["read_marks"]:
                result[semester] = sg

    return result


@app.route('/att_marks_report_stud_group/<int:id>')
@login_required
def att_marks_report_stud_group(id):
    group = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return render_error(404)

    if not group.get_rights(current_user)["read_marks"]:
        return render_error(403)

    students_map = {}

    ball_avg = []

    for cu in group.curriculum_units:
        if len(cu.att_marks)-len(cu.att_marks_readonly_ids) > 0:
            ball_avg.append({"att_mark_1": 0, "att_mark_2": 0, "att_mark_3": 0, "attendance_pct": 0, "ball_average": 0, "att_mark_exam": 0, "total": 0, 'simple_mark_test_simple': 0, 'simple_mark_exam': 0, 'simple_mark_test_diff': 0, 'simple_mark_course_work': 0, 'simple_mark_course_project': 0})
        else:
            ball_avg.append({"att_mark_1": None, "att_mark_2": None, "att_mark_3": None, "attendance_pct": None, "ball_average": None, "att_mark_exam": None, "total": None, 'simple_mark_test_simple': None, 'simple_mark_exam': None, 'simple_mark_test_diff': None, 'simple_mark_course_work': None, 'simple_mark_course_project': None})

    if group.active:
        for s in group.students:
            students_map[s.id] = {"student": s, "att_marks": [None] * len(group.curriculum_units)}

    for cu_index, cu in enumerate(group.curriculum_units):
        for att_mark in cu.att_marks:
            if att_mark.student_id not in students_map:
                students_map[att_mark.student_id] = {"student": att_mark.student,
                                                     "att_marks": [None] * len(group.curriculum_units)}
            students_map[att_mark.student_id]["att_marks"][cu_index] = att_mark

            for attr_name in ("att_mark_1", "att_mark_2", "att_mark_3", "attendance_pct", "ball_average", "att_mark_exam", "total", "simple_mark_exam", "simple_mark_test_diff", "simple_mark_course_work", "simple_mark_course_project"):
                if attr_name == "total":
                    val = None if att_mark.result_print is None else att_mark.result_print[0]
                else:
                    val = getattr(att_mark, attr_name)
                    if attr_name in ("simple_mark_exam", "simple_mark_test_diff", "simple_mark_course_work", "simple_mark_course_project") and val == 0:
                        val = 2
                if ball_avg[cu_index][attr_name] is not None and att_mark.att_mark_id not in cu.att_marks_readonly_ids:
                    if val is not None:
                        ball_avg[cu_index][attr_name] += val
                    else:
                        ball_avg[cu_index][attr_name] = None

    result = list(students_map.values())
    if "sort_key" in request.args and request.args["sort_key"] == "stud_group_subnum" and group.active and group.sub_count > 1:
        result.sort(key=lambda r: (r["student"].stud_group_subnum if r['student'].stud_group_id == group.id else group.sub_count+1, r["student"].surname, r["student"].firstname, r["student"].middlename))
        sort_key = "stud_group_subnum"
    else:
        result.sort(key=lambda r: (r["student"].surname, r["student"].firstname, r["student"].middlename))
        sort_key = "student_name"

    if len(result) > 0:
        for cu_index, cu in enumerate(group.curriculum_units):
            for attr_name in ball_avg[cu_index]:
                if ball_avg[cu_index][attr_name] is not None:
                    l = len(cu.att_marks) - len(cu.att_marks_readonly_ids)
                    if l > 0:
                        ball_avg[cu_index][attr_name] = int(ball_avg[cu_index][attr_name]) // l if ball_avg[cu_index][attr_name] % l == 0 else round(ball_avg[cu_index][attr_name] / l, 2)

    return render_template(
        'att_marks_report_stud_group_print.html' if "print" in request.args else 'att_marks_report_stud_group.html',
        stud_group=group, result=result, ball_avg=ball_avg, sort_key=sort_key, previous_stud_groups_map=_previous_stud_groups_map(group, current_user))


@app.route('/att_marks/<int:id>/student/add', methods=['GET', 'POST'])
@login_required
def att_marks_student_add(id):
    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return render_error(404)

    if current_user.admin_user is None or not current_user.admin_user.active:
        return render_error(403)
    if (not cu.stud_group.active) or cu.closed or cu.pass_department:
        return render_error(403)

    form = AttMarksStudentAddForm(request.form)

    student_id = form.student.data

    s = db.session.query(Student).filter(Student.id == student_id).one_or_none()
    if s is None:
        return render_error(404)

    if s.status != "study":
        return render_error(400)

    for a in cu.att_marks:
        if a.student_id == student_id:
            return redirect(url_for('att_marks', id=id))

    group_subnum = form.group_subnum.data

    att_mark = AttMark(curriculum_unit=cu, student=s, manual_add=True, group_subnum=group_subnum)
    cu.att_marks.append(att_mark)

    db.session.add(cu)

    hist_save_controller(db.session, cu, current_user, check_journalize_attributes=False)

    db.session.commit()
    return redirect(url_for('att_marks', id=id))


@app.route('/att_marks/<int:id>/student/remove/<int:student_id>')
@login_required
def att_marks_student_remove(id, student_id):
    cu = db.session.query(CurriculumUnit).filter(CurriculumUnit.id == id).one_or_none()
    if cu is None:
        return render_error(404)

    if current_user.admin_user is None or not current_user.admin_user.active:
        return render_error(403)
    if (not cu.stud_group.active) or cu.closed or cu.pass_department:
        return render_error(403)

    att_mark = None
    for a in cu.att_marks:
        if a.student_id == student_id:
            att_mark = a
            break
    if att_mark:
        db.session.query(AttMarkHist).filter_by(att_mark_id=att_mark.att_mark_id).delete()
        db.session.delete(att_mark)
        db.session.commit()

    return redirect(url_for('att_marks', id=id))


@app.route('/lessons_report_stud_group/<int:id>')
@login_required
def lessons_report_stud_group(id):
    group = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return render_error(404)

    if not group.get_rights(current_user)["read_marks"]:
        return render_error(403)

    lessons = []
    lessons_attendance_pct = []

    curriculum_units = []

    students = []
    student_ids = []

    if group.active:
        students.extend(group.students)
        student_ids.extend((s.id for s in group.students))

    # [lesson_id][student_id] = LessonStudent
    lessons_attendance_map = {}

    # [student_id] = LessonStudent[]
    students_attendance_map = {}

    q_lcu = db.session.query(LessonCurriculumUnit).\
        join(Lesson, Lesson.id == LessonCurriculumUnit.lesson_id).\
        join(CurriculumUnit, LessonCurriculumUnit.curriculum_unit_id == CurriculumUnit.id).\
        filter(CurriculumUnit.stud_group_id == group.id)

    # filters

    q_lcu = q_lcu.order_by(Lesson.date, Lesson.lesson_num)

    for lcu in q_lcu.all():
        lesson = lcu.lesson

        lessons.append(lesson)
        lessons_attendance_pct.append(lcu.attendance_pct)
        curriculum_units.append(lcu.curriculum_unit)
        lessons_attendance_map[lesson.id] = {}

        for lesson_student in lcu.lesson_students:
            s = lesson_student.student
            if s.id not in student_ids:
                students.append(s)
                student_ids.append(s.id)
            lessons_attendance_map[lesson.id][s.id] = lesson_student

            if s.id not in students_attendance_map:
                students_attendance_map[s.id] = []
            students_attendance_map[s.id].append(lesson_student)

    students_attendance_pct = {}
    for student_id, lessons_student in students_attendance_map.items():
        students_attendance_pct[student_id] = round(100 * sum((1 for ls in lessons_student if ls.attendance)) / len(lessons_student), 2)
        if students_attendance_pct[student_id] - int(students_attendance_pct[student_id]) == 0:
            students_attendance_pct[student_id] = int(students_attendance_pct[student_id])

    if "sort_key" in request.args and request.args["sort_key"] == "stud_group_subnum" and group.active and group.sub_count > 1:
        students.sort(key=lambda s: (s.stud_group_subnum if s.stud_group_id == group.id else group.sub_count+1, s.person.surname, s.person.firstname, s.person.middlename if s.person.middlename is not None else ''))
        sort_key = "stud_group_subnum"
    else:
        students.sort(key=lambda s: (s.person.surname, s.person.firstname, s.person.middlename if s.person.middlename is not None else ''))
        sort_key = "student_name"

    return render_template('lessons_report_stud_group.html',
                           stud_group=group,
                           lessons=lessons,
                           students=students,
                           curriculum_units=curriculum_units,
                           lessons_attendance_map=lessons_attendance_map,
                           lessons_attendance_pct=lessons_attendance_pct,
                           students_attendance_pct=students_attendance_pct,
                           sort_key=sort_key,
                           previous_stud_groups_map=_previous_stud_groups_map(group, current_user))


@app.route('/att_mark_exclude2/<int:id>', methods=['GET', 'POST'])
@login_required
def att_mark_exclude2(id):
    if current_user.admin_user is None or not current_user.admin_user.active:
        return render_error(403)

    mark = db.session.query(AttMark).filter(AttMark.att_mark_id == id).one_or_none()
    if mark is None:
        return render_error(404)
    cu = mark.curriculum_unit
    if cu.closed:
        return render_error(400)
    s = mark.student
    if s.stud_group_id != cu.stud_group_id:
        return render_error(400)

    value = False
    if "value" in request.args and request.args["value"]:
        value = True

    if value:
        for attr in cu.visible_attrs:
            setattr(mark, attr, None)
        mark.exclude = 2
        hist_save_controller(db.session, mark, current_user)
    else:
        mark.exclude = None

    db.session.add(mark)
    db.session.commit()
    return redirect(url_for('att_marks', id=cu.id))


@app.route('/att_marks_report_student/<int:id>')
@login_required
def att_marks_report_student(id):
    s = db.session.query(Student).filter(Student.id == id).one_or_none()

    if s is None:
        return render_error(404)

    if not s.get_rights(current_user)["read_marks"]:
        return render_error(403)

    result = utils_info_student.att_marks_report(s)
    current_lesson_for_mark = utils_info_student.current_lesson_for_mark(s)
    return render_template('att_marks_report_student.html', student=s, result=result, current_lesson_for_mark=current_lesson_for_mark)


@app.route('/lessons_report_student/<int:id>')
@login_required
def lessons_report_student(id):
    s: Student = db.session.query(Student).filter(Student.id == id).one_or_none()
    if s is None:
        return render_error(404)

    if not s.get_rights(current_user)["read_marks"]:
        return render_error(403)

    form = LessonsReportForm(request.args)

    lessons = None
    attendance_pct = None
    marks = None
    cu_ids = []

    for cu_id, in db.session.query(LessonStudent.curriculum_unit_id).filter(LessonStudent.student_id == s.id).distinct():
        cu_ids.append(cu_id)

    for cu_id, in db.session.query(AttMark.curriculum_unit_id).filter(AttMark.student_id == s.id):
        if cu_id not in cu_ids:
            cu_ids.append(cu_id)

    if s.stud_group is not None and s.stud_group.active:
        cu_ids.extend((cu.id for cu in s.stud_group.curriculum_units if cu.subject_id not in ((sp.replaced_subject_id for sp in s.particular_subjects if sp.replaced_subject_id is not None)) and cu.id not in cu_ids))

    # Костыль для пустого списка
    if len(cu_ids) == 0:
        cu_ids.append(0)

    years = sorted((row[0] for row in db.session.query(StudGroup.year).join(CurriculumUnit, CurriculumUnit.stud_group_id == StudGroup.id).filter(CurriculumUnit.id.in_(cu_ids)).distinct()), reverse=True)
    form.year.query = years

    semesters = []
    if form.year.data is not None:
        semesters = sorted((row[0] for row in db.session.query(StudGroup.semester).join(CurriculumUnit, CurriculumUnit.stud_group_id == StudGroup.id).filter(CurriculumUnit.id.in_(cu_ids)).filter(StudGroup.year == form.year.data).distinct()), reverse=True)
    form.semester.query = semesters

    if form.year.data is not None and form.semester.data is not None:
        q_cu = db.session.query(CurriculumUnit).join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).filter(
            CurriculumUnit.id.in_(cu_ids)).filter(StudGroup.year == form.year.data).filter(StudGroup.semester == form.semester.data)

        form.curriculum_unit.query = q_cu.order_by(CurriculumUnit.id).all()
        if form.curriculum_unit.data is not None:
            selected_cu_ids = [form.curriculum_unit.data.id]
        else:
            selected_cu_ids = [cu.id for cu in form.curriculum_unit.query]

        lessons = db.session.query(LessonStudent).join(Lesson, LessonStudent.lesson_id == Lesson.id).\
            filter(LessonStudent.student_id == id).\
            filter(LessonStudent.curriculum_unit_id.in_(selected_cu_ids)).\
            order_by(Lesson.date.desc(), Lesson.lesson_num.desc()).all()

        if len(lessons) > 0:
            count_lessons = sum((1 for l in lessons if l.attendance != 0))
            attendance_pct = (count_lessons*100) // len(lessons) if (count_lessons*100)  % len(lessons) == 0 else round((count_lessons*100) / len(lessons), 2)

        marks = db.session.query(AttMark).\
            filter(AttMark.comment.isnot(None)).filter(AttMark.curriculum_unit_id.in_(selected_cu_ids)).\
            filter(AttMark.student_id == s.id).\
            order_by(AttMark.curriculum_unit_id).all()

    else:
        form.curriculum_unit.query = []

    return render_template('lessons_report_student.html', student=s, form=form, lessons=lessons, att_marks=marks, attendance_pct=attendance_pct)


@app.route('/stud_group_leader/<int:id>')
@login_required
def stud_group_leader(id):
    group: StudGroup = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return render_error(404)

    if not group.get_rights(current_user)["read_list"]:
        return render_error(403)

    show_contact_leader = False
    show_contact_curator = False
    if current_user.admin_user is not None:
        show_contact_leader = show_contact_curator = True

    if current_user.teacher is not None and group.active:
        show_contact_leader = show_contact_curator = True

    for s in current_user.students:
        if s.stud_group_id == group.id:
            show_contact_leader = True
            if s.id in (group.group_leader_id, group.group_leader2_id):
                show_contact_curator = True

    return render_template('stud_group_leader.html', stud_group=group,
                           show_contact_leader=show_contact_leader, show_contact_curator=show_contact_curator)


@app.route('/favorite_teacher_students/<int:id>')
@login_required
def favorite_teacher_students(id):
    if not((current_user.admin_user is not None and current_user.admin_user.active) or (current_user.teacher is not None and current_user.teacher.id == id)):
        return render_error(403)

    t = db.session.query(Teacher).filter(Teacher.id == id).one_or_none()
    if t is None:
        return render_error(404)

    return render_template('favorite_teacher_student.html', students=t.favorite_students, teacher=t)


@app.route('/admin_user/<id>', methods=['GET', 'POST'])
@login_required
def admin_user(id):

    if current_user.admin_user is None or not current_user.admin_user.active:
        return render_error(403)

    try:
        if id == 'new':
            if "person_id" not in request.args:
                return render_error(400)
            person_id = int(request.args["person_id"])
            p = db.session.query(Person).filter_by(id=person_id).one_or_none()
            if p is None:
                return render_error(400)
            u = AdminUser(person=p, active=True)
        else:
            id = int(id)
            u = db.session.query(AdminUser).filter(AdminUser.id == id).one_or_none()
            if u is None:
                return render_error(404)

    except ValueError:
        return render_error(400)

    form = AdminUserForm(request.form if request.method == 'POST' else None, obj=u)

    if form.button_delete.data:
        form.validate()
        if id != 'new':
            if current_user.admin_user.id == id:
                form.button_delete.errors.append("Невозможно удалить самого себя")

        if len(form.button_delete.errors) == 0:
            db.session.delete(u)
            db.session.commit()
            db.session.flush()
            return redirect(url_for('person', id=u.person_id))

    if form.button_save.data and form.validate():
        form.populate_obj(u)

        if id == current_user.admin_user.id and not u.active:
            form.active.errors.append("Невозможно отключить самого себя")
        else:
            db.session.add(u)
            db.session.commit()
            if id == 'new':
                db.session.flush()
                return redirect(url_for('admin_user', id=u.id))

    return render_template('admin_user.html', admin_user=u, form=form)


@app.route('/admin_panel/<int:education_level_order>/<int:semester>')
@app.route('/admin_panel')
@login_required
def admin_panel(education_level_order=None, semester=None):
    if current_user.admin_user is None:
        return render_error(403)

    semesters = sorted(db.session.query(Specialty.education_level_order, StudGroup.semester).join(Specialty, StudGroup.specialty_id == Specialty.id).filter(StudGroup.active).order_by(
        StudGroup.semester).distinct().all())

    groups = []
    # teacher / subjects
    columns = []
    rows = []
    if education_level_order is not None and semester is not None:

        c_units = db.session.query(CurriculumUnit).join(Teacher, CurriculumUnit.teacher_id == Teacher.id).join(Person, Teacher.person_id == Person.id).join(
            StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).join(Specialty, StudGroup.specialty_id == Specialty.id) \
            .filter(StudGroup.active).filter(StudGroup.semester == semester).filter(Specialty.education_level_order == education_level_order) \
            .order_by(Person.surname, Person.firstname, Person.middlename, CurriculumUnit.subject_id, StudGroup.num).all()
        column = None
        for cu in c_units:
            if cu.stud_group not in groups:
                groups.append(cu.stud_group)
            if column is None or column[0].id != cu.teacher_id:
                column = (cu.teacher, [])
                columns.append(column)
            if cu.subject not in column[1]:
                column[1].append(cu.subject)

        groups.sort(key=lambda g: g.num)

        for g in groups:
            row = []
            for column in columns:
                t: Teacher = column[0]
                for s in column[1]:
                    try:
                        cu = next(cu for cu in g.curriculum_units if cu.teacher_id == t.id and cu.subject_id == s.id)
                        row.append(cu)
                    except StopIteration:
                        row.append(None)
            rows.append(row)

    return render_template('admin_panel.html', education_level_order=education_level_order, semester=semester, semesters=semesters, groups=groups, columns=columns,
                           rows=rows)


@app.route('/department_panel/<int:department_id>')
@app.route('/department_panel')
@login_required
def department_panel(department_id=None):
    if not ((current_user.admin_user is not None and current_user.admin_user.active) or (
            current_user.teacher is not None and (current_user.teacher.department_secretary or current_user.teacher.department_leader))):
        return render_error(403)

    if current_user.admin_user is not None and current_user.admin_user.active:
        departments = db.session.query(Department).filter(Department.parent_department_id == Department.ID_DEFAULT).order_by(Department.id).all()
    elif current_user.teacher is not None and (current_user.teacher.department_secretary or current_user.teacher.department_leader) and (len(current_user.teacher.departments) > 1 or department_id is None):
        departments = [d for d in current_user.teacher.departments if d.parent_department_id == Department.ID_DEFAULT]
    else:
        departments = None

    if department_id is None:
        d = None
        curriculum_units_department = None
    else:
        d = db.session.query(Department).filter(Department.id == department_id).filter(Department.parent_department_id == Department.ID_DEFAULT).one_or_none()
        if d is None:
            return render_error(404)

        if not ((current_user.admin_user is not None and current_user.admin_user.active) or (current_user.teacher is not None and (current_user.teacher.department_secretary or current_user.teacher.department_leader) and department_id in [d.id for d in current_user.teacher.departments])):
            return render_error(403)

        curriculum_units_department = db.session.query(CurriculumUnit).join(Teacher, CurriculumUnit.teacher_id == Teacher.id).join(Person, Teacher.person_id == Person.id).join(
            StudGroup, CurriculumUnit.stud_group_id == StudGroup.id) \
            .filter(StudGroup.active).filter(CurriculumUnit.department_id == department_id).join(Specialty, StudGroup.specialty_id == Specialty.id) \
            .order_by(Person.surname, Person.firstname, Person.middlename, func.isnull(CurriculumUnit.curriculum_unit_group_id), func.IF(CurriculumUnit.curriculum_unit_group_id.isnot(None), CurriculumUnit.curriculum_unit_group_id, CurriculumUnit.subject_id), Specialty.education_level_order, StudGroup.semester, StudGroup.num).all()

    if current_user.teacher is not None and current_user.admin_user is None:

        curriculum_units = db.session.query(CurriculumUnit).join(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id) \
            .filter(CurriculumUnit.teacher_id == current_user.teacher.id) \
            .filter(StudGroup.active) \
            .order_by(func.isnull(CurriculumUnit.curriculum_unit_group_id), func.IF(CurriculumUnit.curriculum_unit_group_id.isnot(None), CurriculumUnit.curriculum_unit_group_id, CurriculumUnit.subject_id), Specialty.education_level_order, StudGroup.semester, StudGroup.num) \
            .all()

        curriculum_units_practice = db.session.query(CurriculumUnit).join(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id) \
            .filter(CurriculumUnit.practice_teachers.any(Teacher.id == current_user.teacher.id)) \
            .filter(StudGroup.active) \
            .order_by(func.isnull(CurriculumUnit.curriculum_unit_group_id), func.IF(CurriculumUnit.curriculum_unit_group_id.isnot(None), CurriculumUnit.curriculum_unit_group_id, CurriculumUnit.subject_id), Specialty.education_level_order, StudGroup.semester, StudGroup.num) \
            .all()

        groups = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id). \
            filter(StudGroup.active).filter(StudGroup.curator_id == current_user.teacher.id). \
            order_by(StudGroup.year, Specialty.education_level_order, StudGroup.semester, StudGroup.num). \
            all()
    else:
        curriculum_units = []
        curriculum_units_practice = []
        groups = []



    return render_template('department_panel.html',
                           curriculum_units_department=curriculum_units_department,
                           curriculum_units=curriculum_units,
                           curriculum_units_practice=curriculum_units_practice,
                           stud_groups=groups,
                           department=d,
                           departments=departments)


@app.route('/curriculum_units_open')
@login_required
def curriculum_units_open():
    if current_user.admin_user is None:
        return render_error(403)

    curriculum_units_open = db.session.query(CurriculumUnit).join(Teacher, CurriculumUnit.teacher_id == Teacher.id).join(Person, Teacher.person_id == Person.id).join(
            StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).join(Specialty, StudGroup.specialty_id == Specialty.id) \
            .filter(StudGroup.active).filter(not_(CurriculumUnit.closed)) \
            .order_by(Person.surname, Person.firstname, Person.middlename, func.isnull(CurriculumUnit.curriculum_unit_group_id), func.IF(CurriculumUnit.curriculum_unit_group_id.isnot(None), CurriculumUnit.curriculum_unit_group_id, CurriculumUnit.subject_id), Specialty.education_level_order, StudGroup.semester, StudGroup.num).all()

    semesters = sorted(db.session.query(Specialty.education_level_order, StudGroup.semester).join(Specialty, StudGroup.specialty_id == Specialty.id).filter(StudGroup.active).order_by(StudGroup.semester).distinct().all())
    return render_template('curriculum_units_open.html',
                           curriculum_units_open=curriculum_units_open,
                           semesters=semesters)


@app.route('/rating')
@login_required
def rating():
    if not current_user.user_rights["rating"]:
        return render_error(403)
    data = None
    avg_ball = None

    form = RatingForm(request.args)
    if len(request.args) == 0:
        now = datetime.now()
        if 3 <= now.month <= 9:
            form.year.data = now.year - 1
            form.semester.data = '2'
        else:
            if now.month < 3:
                form.year.data = now.year - 1
            else:
                form.year.data = now.year
            form.semester.data = '1'

    year = None
    s = None
    stage = None
    education_level_order = 1
    try:
        education_level_order = int(form.education_level_order.data)
    except ValueError:
        education_level_order = 1
        form.education_level_order.data = '1'

    if form.year.data and form.semester.data in ('1', '2'):
        year = form.year.data
        s = int(form.semester.data)
        if s == 2:
            s = 0
        form.course.query_factory = lambda: [(row[0]+1)//2 for row in db.session.query(StudGroup.semester).join(Specialty, StudGroup.specialty_id==Specialty.id).filter(Specialty.education_level_order == education_level_order).filter(StudGroup.year == year).filter(func.mod(StudGroup.semester, 2) == s).order_by(StudGroup.semester).distinct()]
        form.specialty.query_factory = lambda: db.session.query(Specialty.code, Specialty.name).join(StudGroup, Specialty.id==StudGroup.specialty_id).filter(Specialty.education_level_order == education_level_order).order_by(Specialty.code).filter(StudGroup.year == year).filter(func.mod(StudGroup.semester, 2) == s).distinct()
    else:
        form.specialty.query_factory = lambda: db.session.query(Specialty.code, Specialty.name).filter(Specialty.education_level_order == education_level_order).order_by(Specialty.code).distinct()

    if year is not None and s is not None and form.course.data is not None:
        stage = form.stage.data
        if stage in ('att_mark_1', 'att_mark_2', 'att_mark_3', 'total'):
            course = form.course.data
            specialty_code = form.specialty.data[0] if form.specialty.data else None
            stud_groups_q = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id).filter(Specialty.education_level_order == education_level_order)

            stud_groups_q = stud_groups_q.filter(StudGroup.year == year).\
                filter(func.mod(StudGroup.semester, 2) == s).\
                filter(func.floor((StudGroup.semester+1) / 2) == course)

            if specialty_code:
                stud_groups_q = stud_groups_q.filter(Specialty.code == specialty_code)
                form.stud_group.query_factory = lambda: stud_groups_q.order_by(StudGroup.num).all()
                if form.stud_group.data:
                    stud_groups_q = db.session.query(StudGroup).filter(StudGroup.id == form.stud_group.data.id)

            stud_groups = stud_groups_q.all()

            data, avg_ball = utils_info_student.rating_with_avg_ball(stud_groups, stage)
            if data is None:
                flash("Недостаточно данных для формирования рейтинга", category='error')
        else:
            flash("Не указан этап", category='error')

    else:
        if year is None:
            flash("Не указан учебный год", category='error')
        if s is None:
            flash("Не указан семестр", category='error')
        if form.course.data is None:
            flash("Не указан курс", category='error')

    return render_template('rating.html', data=data, avg_ball=avg_ball, stage=stage, form=form)


@app.route('/stud_groups_print', methods=['GET', 'POST'])
@login_required
def stud_groups_print():
    form = StudGroupsPrintForm(request.form)

    q = db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id==Specialty.id).filter(StudGroup.active).order_by(Specialty.education_level_order, StudGroup.semester, StudGroup.num)

    l_stud_groups = [sg for sg in q.all() if sg.get_rights(current_user)["read_list"]]

    form.stud_groups_selected.query = l_stud_groups

    if form.button_excel.data and form.validate():
        s_stud_groups = form.stud_groups_selected.data
        if len(s_stud_groups) == 0:
            return render_error(400)
        f = create_excel_stud_groups(s_stud_groups, form.name_format.data, form.split_sub_group.data)
        f.seek(0)
        file_name = "Студенты ФКН %s.xlsx" % s_stud_groups[0].year_print
        return send_file(f, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True,
                         download_name=file_name)
    else:
        if (current_user.admin_user is None or current_user.admin_user.active) or \
                (current_user.teacher is not None and
                 (current_user.teacher.department_secretary or current_user.teacher.dean_staff or
                  current_user.teacher.department_leader or current_user.teacher.right_read_all)):
            stud_groups_lists = {}
            if current_user.teacher is not None:
                for sg in l_stud_groups:
                    if any(current_user.teacher.id == cu.teacher_id or any(current_user.teacher.id == t.id for t in cu.practice_teachers) for cu in sg.curriculum_units):
                        key = "Группы, где есть занятия"
                        if key not in stud_groups_lists:
                            stud_groups_lists[key] = []
                        stud_groups_lists[key].append(sg)

                for sg in l_stud_groups:
                    if sg.curator_id == current_user.teacher.id:
                        key = "Курируемые группы"
                        if key not in stud_groups_lists:
                            stud_groups_lists[key] = []
                        stud_groups_lists[key].append(sg)

            # По курсам
            for sg in l_stud_groups:
                key = "%d курс" % sg.course
                if sg.specialty.education_level == "master":
                    key = "%d курс маг." % sg.course
                if key not in stud_groups_lists:
                    stud_groups_lists[key] = []
                stud_groups_lists[key].append(sg)
            form.button_excel.render_kw = {"disabled": True}
        else:
            form.stud_groups_selected.data = l_stud_groups
            stud_groups_lists = None
            if len(l_stud_groups) == 0:
                form.button_excel.render_kw = {"disabled": True}

        return render_template("stud_groups_print.html", form=form,
                               stud_groups=l_stud_groups,
                               stud_groups_lists=stud_groups_lists)


@app.route('/certificate_of_study/<int:student_id>', methods=['GET', 'POST'])
@login_required
def certificate_of_study(student_id):
    if not (
            (current_user.admin_user is not None and current_user.admin_user.active) or
            (current_user.teacher is not None and current_user.teacher.active and current_user.teacher.dean_staff) or
            (student_id in (s.id for s in current_user.students))):
        return render_error(403)

    s: Student = db.session.query(Student).filter_by(id=student_id).one_or_none()
    if s is None:
        return render_error(404)

    if s.student_ext_id is None:
        return render_error(400)

    form = CertificateOfStudyForm(request.form)
    if form.button_submit.data:
        if form.validate():
            count_avalible = CertificateOfStudy.MAX_PER_ORDER - s.certificates_of_study.filter(CertificateOfStudy.ready_time.is_(None)).count()
            if count_avalible < 0:
                count_avalible = 0
            if form.count.data > count_avalible:
                if count_avalible == 0:
                    flash('Превышено максимальное количество запросов', category='error')
                else:
                    form.count.errors.append("Максимальное количество справок доступных для заказа в данный момент: %d" % count_avalible)
                    flash('Произошла ошибка при заказе справки об обучении', category='error')
            else:
                for _ in range(form.count.data):
                    cert = CertificateOfStudy(
                        student_id=s.id,
                        specialty_id=s.specialty_id,
                        surname=s.person.surname,
                        firstname=s.person.firstname,
                        middlename=s.person.middlename,
                        course=s.course if s.status in ('study', 'academic_leave') else None,
                        student_status=s.status,
                        request_time=datetime.now(),
                        comment=form.comment.data
                    )
                    db.session.add(cert)
                db.session.flush()
                db.session.commit()
                if form.count.data == 1:
                    flash('Запрос успешно обработан. Справка об обучении будет готова в течение 1-2 рабочих дней.', category='success')
                else:
                    flash('Запрос успешно обработан. Справки об обучении будут готовы в течение 1-2 рабочих дней.', category='success')

                form = None
        else:
            flash('Произошла ошибка при заказе справки об обучении', category='error')

    certificates_in_progress = s.certificates_of_study.filter(CertificateOfStudy.ready_time.is_(None)).order_by(CertificateOfStudy.id).all()
    certificates_ready = s.certificates_of_study.filter(CertificateOfStudy.ready_time.isnot(None)).order_by(CertificateOfStudy.id.desc()).all()

    return render_template('certificate_of_study.html', student=s, form=form, certificates_in_progress=certificates_in_progress, certificates_ready=certificates_ready)


@app.route('/certificates_of_study', methods=['GET'])
@login_required
def certificates_of_study():
    if not ((current_user.admin_user is not None and current_user.admin_user.active) or
            (current_user.teacher is not None and current_user.teacher.active and current_user.teacher.dean_staff)):
        return render_error(403)

    certificates_new = db.session.query(CertificateOfStudy).filter(CertificateOfStudy.print_time.is_(None)).order_by(CertificateOfStudy.id).all()
    certificates_with_num = db.session.query(CertificateOfStudy).filter(CertificateOfStudy.print_time.isnot(None)).filter(CertificateOfStudy.ready_time.is_(None)).order_by(CertificateOfStudy.year, CertificateOfStudy.num).all()

    return render_template('certificates_of_study.html', certificates_new=certificates_new, certificates_with_num=certificates_with_num)


@app.route('/certificates_of_study_archive/<int:year>', methods=['GET'])
@app.route('/certificates_of_study_archive', methods=['GET'])
@login_required
def certificates_of_study_archive(year=None):
    if not ((current_user.admin_user is not None and current_user.admin_user.active) or
            (current_user.teacher is not None and current_user.teacher.active and current_user.teacher.dean_staff)):
        return render_error(403)

    if year is None:
        year = db.session.query(func.max(CertificateOfStudy.year)).filter(CertificateOfStudy.ready_time.isnot(None)).with_for_update().first()[0]
        if year is None:
            render_error(404)

    years = [_[0] for _ in db.session.query(CertificateOfStudy.year).filter(CertificateOfStudy.ready_time.isnot(None)).order_by(CertificateOfStudy.year.desc()).distinct()]

    page = 1
    if 'page' in request.args:
        try:
            page = int(request.args["page"])
        except ValueError:
            return render_error(400)

    q = db.session.query(CertificateOfStudy).filter(CertificateOfStudy.year == year).filter(CertificateOfStudy.ready_time.isnot(None)).order_by(CertificateOfStudy.num.desc())
    if page == 0:
        certificates = q.all()
    else:
        certificates = q.paginate(page=page, error_out=False)

    return render_template('certificates_of_study_archive.html', certificates=certificates,
                           year=year, years=years, page=page)


@app.route('/schedule/<schedule_type>/<object_type>/<int:object_id>', methods=["GET"])
@login_required
def schedule(schedule_type, object_type, object_id: int):
    t: Teacher = None
    s: Student = None
    sg: StudGroup = None
    if object_type == "teacher":
        t = db.session.query(Teacher).filter_by(id=object_id).one_or_none()
        if t is None:
            return render_error(404)

    elif object_type == "student":
        s = db.session.query(Student).filter_by(id=object_id).one_or_none()
        if s is None:
            return render_error(404)
        if not s.get_rights(current_user)["read_marks"]:
            return render_error(403)

    elif object_type == "stud_group":
        sg = db.session.query(StudGroup).filter_by(id=object_id).one_or_none()
        if sg is None:
            return render_error(404)
    else:
        return render_error(404)



    if schedule_type == "exams":
        q_exams = db.session.query(Exam).join(CurriculumUnit, Exam.curriculum_unit_id==CurriculumUnit.id)
        if s is not None:
            q_exams = q_exams.filter(CurriculumUnit.stud_group_id == s.stud_group_id)
            if s.stud_group is not None and s.stud_group.sub_count > 1 and s.stud_group_subnum > 0:
                q_exams = q_exams.filter(Exam.stud_group_subnums.op('&')((1<<(s.stud_group_subnum - 1))))
            q_exams = q_exams.order_by(Exam.stime)
        if t is not None:
            q_exams = q_exams.join(StudGroup, CurriculumUnit.stud_group_id == StudGroup.id).filter(StudGroup.active)
            q_exams = q_exams.filter(Exam.teacher_id == t.id)
            q_exams = q_exams.order_by(Exam.stime, StudGroup.semester, StudGroup.num, Exam.stud_group_subnums)

        if sg is not None:
            q_exams = q_exams.filter(CurriculumUnit.stud_group_id == object_id)
            q_exams = q_exams.order_by(Exam.stime, Exam.stud_group_subnums)

        exams = q_exams.all()

        return render_template('schedule_exams.html', teacher=t, student=s, exams=exams, stud_group=sg, now=datetime.now())
    else:
        return render_error(404)

@app.route('/lessons', methods=["GET"])
@login_required
def lessons():
    index_js_file = None
    index_js_file_st_mtime = None

    for f in os.listdir(os.path.join(app.static_folder,'lessons', 'assets')):
        if len(f) > 9 and f[-3:] == '.js' and f[:6] == "index-":
            f_st_mtime = os.stat(os.path.join(app.static_folder, 'lessons', 'assets', f)).st_mtime
            if index_js_file_st_mtime is None or f_st_mtime > index_js_file_st_mtime:
                index_js_file_st_mtime = f_st_mtime
                index_js_file = f

    if index_js_file is None:
        return render_error(404)

    index_js_file = "/".join(('lessons', 'assets', index_js_file))
    return render_template('lessons.html', index_js_file=index_js_file)


@app.route('/schedule/exams', methods=["GET"])
@app.route('/schedule', methods=["GET"])
def schedule_all():
    index_js_file = None
    index_js_file_st_mtime = None

    index_css_file = None
    index_css_file_st_mtime = None

    for f in os.listdir(os.path.join(app.static_folder,'schedule', 'assets')):
        f_st_mtime = os.stat(os.path.join(app.static_folder, 'schedule', 'assets', f)).st_mtime

        if len(f) > 9 and f[-3:] == '.js' and f[:6] == "index-":
            if index_js_file_st_mtime is None or f_st_mtime > index_js_file_st_mtime:
                index_js_file_st_mtime = f_st_mtime
                index_js_file = f

        if len(f) > 10 and f[-4:] == '.css' and f[:6] == "index-":
            if index_css_file_st_mtime is None or f_st_mtime > index_css_file_st_mtime:
                index_css_file_st_mtime = f_st_mtime
                index_css_file = f

    if index_js_file is None or index_css_file is None:
        return render_error(404)

    index_js_file = "/".join(('schedule', 'assets', index_js_file))
    index_css_file = "/".join(('schedule', 'assets', index_css_file))
    return render_template('schedule.html', index_js_file=index_js_file, index_css_file=index_css_file)


app.register_error_handler(404, lambda code: render_error(404))


if __name__ == '__main__':
    app.run(debug=True)
