"""Класс в котором содержатся веб-странички приложения"""
from collections import OrderedDict
from datetime import datetime

from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from pdfkit import from_string

from app import APP
from app import DB
from app import excel
from app.forms import StudGroupForm
from app.forms import StudentForm
from app.forms import StudentSearchForm
from app.forms import SubjectForm
from app.forms import TeacherForm
from app.model import AttMark
from app.model import CurriculumUnit
from app.model import LessonType
from app.model import StudGroup
from app.model import Student
from app.model import Subject
from app.model import Teacher


# USER_MANAGER = UserManager(APP, DB, User)


@APP.route('/')
def index():
    """Главная страница приложения"""
    return render_template('public/index.html')


@APP.route('/stud_groups')
# @login_required
def stud_groups():
    """Страничка, отображающая все учебные группы студентов"""
    groups = DB.session.query(StudGroup). \
        filter(StudGroup.active). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum). \
        all()
    return render_template('public/stud_groups.html', stud_groups=groups)


@APP.route('/stud_group/<group_id>', methods=['GET', 'POST'])
# @login_required
def stud_group(group_id):
    """Страничка, отображающая конкретную учебную группу"""
    if group_id == 'new':
        group = StudGroup()
        group.subnum = 0
        now = datetime.now()
        if now.month >= 7 and now.day >= 1:
            group.year = now.year
        else:
            group.year = now.year - 1
        group.active = True

    else:
        try:
            group_id = int(group_id)
        except ValueError:
            return 'Bad Request', 400
        group = DB.session.query(StudGroup).filter(StudGroup.id == group_id).one_or_none()

    if group is None:
        return 'Not Found', 404

    form = StudGroupForm(request.form, obj=group)

    if form.button_save.data and form.validate():
        # unique check
        query = DB.session.query(StudGroup). \
            filter(StudGroup.year == form.year.data). \
            filter(StudGroup.semester == form.semester.data). \
            filter(StudGroup.num == form.num.data)
        if form.subnum.data > 0:
            query = query.filter(
                DB.or_(StudGroup.subnum == form.subnum.data, StudGroup.subnum == 0)
            )
        if group_id != 'new':
            query = query.filter(StudGroup.id != group_id)

        if query.count() > 0:
            form.subnum.errors.append('Группа с таким же номером существует')
        else:
            form.populate_obj(group)
            DB.session.add(group)
            if group_id == 'new':
                DB.session.flush()
                return redirect(url_for('stud_group', id=group.id))

    if form.button_delete.data and group_id != 'new':
        form.validate()
        if DB.session.query(Student).filter(Student.stud_group_id == group_id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить группу, в которой есть студенты')
        if DB.session.query(CurriculumUnit).filter(
                CurriculumUnit.stud_group_id == group_id) \
                .count() > 0:
            form.button_delete.errors.append(
                'Невозможно удалить группу, к которой привязаны единицы учебного плана'
            )

        if len(form.button_delete.errors) == 0:
            DB.session.delete(group)
            DB.session.flush()  # ???
            return redirect(url_for('stud_groups'))

    return render_template('public/stud_group.html', group=group, form=form)


@APP.route('/student/<group_id>', methods=['GET', 'POST'])
# @login_required
def student(group_id):
    """Страничка для отображения студента из группы"""
    if group_id == 'new':
        new_student = Student()
    else:
        try:
            group_id = int(group_id)
        except ValueError:
            return 'Bad Request', 400
        new_student = DB.session.query(Student).filter(Student.id == group_id).one_or_none()
        if new_student is None:
            return 'Not Found', 404

    form = StudentForm(request.form, obj=new_student)

    if form.button_delete.data:
        form.validate()
        if DB.session.query(AttMark) \
                .filter(AttMark.student_id == new_student.id) \
                .count() > 0:
            form.button_delete.errors.append(
                'Невозможно удалить студента, у которого есть оценки за аттестации'
            )

        if len(form.button_delete.errors) == 0:
            DB.session.delete(new_student)
            DB.session.flush()
            return redirect(url_for('students'))

    if form.button_save.data and form.validate():
        form.populate_obj(new_student)
        if new_student.stud_group is not None:
            new_student.semester = new_student.stud_group.semester
            new_student.alumnus_year = None
            new_student.expelled_year = None
            form = StudentForm(obj=new_student)

        DB.session.add(new_student)
        if group_id == 'new':
            DB.session.flush()  # ???
        if new_student.id != group_id:
            return redirect(url_for('student', id=new_student.id))

    return render_template('public/student.html', student=new_student, form=form)


@APP.route('/students', methods=['GET'])
# @login_required
def students():
    """Страница для отображения всех студентов"""
    form = StudentSearchForm(request.args)
    result = None
    if form.button_search.data and form.validate():
        query = DB.session.query(Student)
        if form.id.data is not None:
            query = query.filter(Student.id == form.id.data)
        if form.surname.data != '':
            query = query.filter(Student.surname.like(form.surname.data + '%'))
        if form.firstname.data != '':
            query = query.filter(Student.firstname == form.firstname.data)
        if form.middlename.data != '':
            query = query.filter(Student.middlename == form.middlename.data)

        if form.stud_group.data is not None:
            query = query.filter(Student.stud_group_id == form.stud_group.data.id)

        if form.alumnus_year.data is not None:
            query = query.filter(Student.alumnus_year == form.alumnus_year.data)

        if form.expelled_year.data is not None:
            query = query.filter(Student.expelled_year == form.expelled_year.data)

        query = query.order_by(Student.surname, Student.firstname, Student.middlename)
        result = query.all()

    return render_template('public/students.html', students=result, form=form)


@APP.route('/subjects')
# @login_required
def subjects():
    """Страничка для отображения предметов обучения"""
    fetched_subjects = DB.session.query(Subject).order_by(Subject.name)
    return render_template('public/subjects.html', subjects=fetched_subjects)


@APP.route('/subject/<subject_id>', methods=['GET', 'POST'])
# @login_required
def subject(subject_id):
    """Страничка для отображения конкретного предмета обучения"""
    if subject_id == 'new':
        new_subject = Subject()
    else:
        try:
            subject_id = int(subject_id)
        except ValueError:
            return 'Bad Request', 400
        new_subject = DB.session.query(Subject).filter(Subject.id == subject_id).one_or_none()
        if new_subject is None:
            return 'Not Found', 404

    form = SubjectForm(request.form, obj=new_subject)
    if form.button_delete.data:
        form.validate()
        if DB.session.query(CurriculumUnit) \
                .filter(CurriculumUnit.subject_id == new_subject.id) \
                .count() > 0:
            form.button_delete.errors.append(
                'Невозможно удалить предмет, к которому привязаны единицы учебного плана'
            )
        if len(form.button_delete.errors) == 0:
            DB.session.delete(new_subject)
            DB.session.flush()
            return redirect(url_for('subjects'))

    if form.button_save.data and form.validate():
        form.populate_obj(new_subject)
        DB.session.add(new_subject)
        if subject_id == 'new':
            DB.session.flush()
            return redirect(url_for('subject', id=new_subject.id))

    return render_template('public/subject.html', subject=new_subject, form=form)


@APP.route('/teachers')
# @login_required
def teachers():
    """Страничка для отображения списка учителей"""
    return render_template('public/teachers.html',
                           teachers=DB.session.query(Teacher)
                           .order_by(Teacher.surname, Teacher.firstname, Teacher.middlename))


@APP.route('/teacher/<teacher_id>', methods=['GET', 'POST'])
# @login_required
def teacher(teacher_id):
    """Страничка для отображения конкретного учителя"""
    if teacher_id == 'new':
        new_teacher = Teacher()
    else:
        try:
            teacher_id = int(teacher_id)
        except ValueError:
            return 'Bad Request', 400
        new_teacher = DB.session.query(Teacher).filter(Teacher.id == teacher_id).one_or_none()
        if new_teacher is None:
            return 'Not Found', 404

    form = TeacherForm(request.form, obj=new_teacher)

    if form.button_delete.data:
        form.validate()
        if DB.session.query(CurriculumUnit) \
                .filter(CurriculumUnit.teacher_id == new_teacher.id) \
                .count() > 0:
            form.button_delete.errors.append(
                'Невозможно удалить преподавателя, к которому привязаны единицы учебного плана')
        if len(form.button_delete.errors) == 0:
            DB.session.delete(new_teacher)
            DB.session.flush()
            return redirect(url_for('teachers'))

    if form.button_save.data and form.validate():
        form.populate_obj(new_teacher)
        DB.session.add(new_teacher)
        if teacher_id == 'new':
            DB.session.flush()
            return redirect(url_for('teacher', id=new_teacher.id))

    return render_template('public/teacher.html', teacher=new_teacher, form=form)


# код для курсовой ниже

# Что можно посмотреть:
# про авторизацию https://www.youtube.com/watch?v=K0vSCCAM2ss
# редактирование ячеек таблицы - http://jsfiddle.net/JPVUk/4/
# распечатка PDF - https://pythonhosted.org/Flask-WeasyPrint/
# распечатка Excel - https://flask-excel.readthedocs.io/en/latest/


@APP.route("/pdf_attendance")
def print_pdf():
    """Страничка для отображения посещаемости в формате PDF"""
    course = 3
    group_num = 3
    group_subnum = 1
    groups = DB.session.query(StudGroup). \
        filter(StudGroup.active). \
        filter(StudGroup.semester == 5). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum). \
        all()  # находим список групп
    group = DB.session.query(StudGroup). \
        filter(StudGroup.active). \
        filter(StudGroup.semester == 5). \
        filter(StudGroup.num == group_num). \
        filter(StudGroup.subnum == group_subnum). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum). \
        first()  # находим всех студентов по группе и семестру

    rendered = render_template('public/attendance.html', course=course, groups=groups, group=group_num,
                               lesson_type=LessonType, students=group.students)
    css = ['app/static/libs/bootstrap.min.css',
           'app/static/libs/all.min.css']
    pdf = from_string(rendered, False, css=css)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=attendance.pdf'

    return response
    # return WKHTMLTOPDF.render_template_to_pdf('public/attendance.html', course=course, groups=groups, group=group_num,
    #                                           lesson_type=LessonType, students=group.students, save=True)


@APP.route("/excel_attendance")
def print_excel():
    """Страничка для отображения посещаемости в формате Excel"""
    content = OrderedDict([
        (
            'ФИО студента/Дата проведения занятия',
            [
                'Борисов Александр Дмитриевич',
                'Ильина Анастасия Дмитриевна',
                'Коновалов Игорь Романович',
                'Копылова Анастасия Евгеньевна',
                'Королёв Дмитрий Андреевич',
                'Кравченко Денис Александрович',
                'Кушнеренко Виктор Константинович',
                'Мущенко Илья Викторович',
                'Науменко Дмитрий Иванович',
                'Никонов Иван Евгеньевич',
                'Папина Анастасия Александровна',
                'Рудин Павел Игоревич',
                'Смольянинов Никита Сергеевич',
                'Старкин Михаил Владимирович',
                'Транина Олеся Александровна'
            ]
        ),
        (
            '01.01.2017',
            [
                '+',
                '+',
                '+',
                '-',
                '-',
                '+',
                '-',
                '+',
                '-',
                '+',
                '+',
                '-',
                '+',
                '-',
                '+'
            ]
        ),
        (
            '02.01.2017',
            [
                '+',
                '+',
                '+',
                '-',
                '-',
                '+',
                '-',
                '+',
                '-',
                '+',
                '+',
                '-',
                '+',
                '-',
                '+'
            ]
        )
    ])
    output_excel = excel.make_response_from_dict(content, file_type='xlsx')
    output_excel.headers["Content-Disposition"] = "attachment; filename=Attendance.xlsx"
    output_excel.headers["Content-type"] = "application/vnd.openxmlformats-\
    officedocument.spreadsheetml.sheet"
    return output_excel


@APP.route("/attendance", methods=['GET', 'POST'])
def attendance():
    """Веб-страничка для отображения посещаемости"""
    course = 3
    group_num = 3
    group_subnum = 1
    groups = DB.session.query(StudGroup). \
        filter(StudGroup.active). \
        filter(StudGroup.semester == 5). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum). \
        all()  # находим список групп
    group = DB.session.query(StudGroup). \
        filter(StudGroup.active). \
        filter(StudGroup.semester == 5). \
        filter(StudGroup.num == group_num). \
        filter(StudGroup.subnum == group_subnum). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum). \
        first()  # находим всех студентов по группе и семестру
    return render_template('public/attendance.html', course=course, groups=groups, group=group_num,
                           lesson_type=LessonType, students=group.students)
