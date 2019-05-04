from datetime import datetime
from flask import request, render_template, redirect, url_for

from app_config import app, db
from model import StudGroup, Subject, Teacher, Student, CurriculumUnit, AttMark
from forms import StudGroupForm, StudentForm, StudentSearchForm, SubjectForm, TeacherForm


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stud_groups')
def stud_groups():
    groups = db.session.query(StudGroup). \
        filter(StudGroup.active). \
        order_by(StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum). \
        all()
    return render_template('stud_groups.html', stud_groups=groups)


@app.route('/stud_group/<id>', methods=['GET', 'POST'])
def stud_group(id):
    if id == 'new':
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
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        group = db.session.query(StudGroup).filter(StudGroup.id == id).one_or_none()

    if group is None:
        return 'Not Found', 404

    form = StudGroupForm(request.form, obj=group)

    if form.button_save.data and form.validate():
        # unique check
        q = db.session.query(StudGroup). \
            filter(StudGroup.year == form.year.data). \
            filter(StudGroup.semester == form.semester.data). \
            filter(StudGroup.num == form.num.data)
        if form.subnum.data > 0:
            q = q.filter(db.or_(StudGroup.subnum == form.subnum.data, StudGroup.subnum == 0))
        if id != 'new':
            q = q.filter(StudGroup.id != id)

        if q.count() > 0:
            form.subnum.errors.append('Группа с таким же номером существует')
        else:
            form.populate_obj(group)
            db.session.add(group)
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
            db.session.flush() # ???
            return redirect(url_for('stud_groups'))

    return render_template('stud_group.html', group=group, form=form)


@app.route('/student/<id>', methods=['GET', 'POST'])
def student(id):
    if id == 'new':
        s = Student()
    else:
        try:
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        s = db.session.query(Student).filter(Student.id == id).one_or_none()
        if s is None:
            return 'Not Found', 404

    form = StudentForm(request.form, obj=s)

    if form.button_delete.data:
        form.validate()
        if db.session.query(AttMark).filter(AttMark.student_id == s.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить студента, у которого есть оценки за аттестации')

        if len(form.button_delete.errors) == 0:
            db.session.delete(s)
            db.session.flush()
            return redirect(url_for('students'))

    if form.button_save.data and form.validate():
        form.populate_obj(s)
        if s.stud_group is not None:
            s.semester = s.stud_group.semester
            s.alumnus_year = None
            s.expelled_year = None
            form = StudentForm(obj=s)

        db.session.add(s)
        if id == 'new':
            db.session.flush() # ???
        if s.id != id:
            return redirect(url_for('student', id=s.id))

    return render_template('student.html', student=s, form=form)


@app.route('/students', methods=['GET'])
def students():
    form = StudentSearchForm(request.args)
    result = None
    if form.button_search.data and form.validate():
        q = db.session.query(Student)
        if form.id.data is not None:
            q = q.filter(Student.id == form.id.data)
        if form.surname.data != '':
            q = q.filter(Student.surname.like(form.surname.data+'%'))
        if form.firstname.data != '':
            q = q.filter(Student.firstname == form.firstname.data)
        if form.middlename.data != '':
            q = q.filter(Student.middlename == form.middlename.data)

        if form.stud_group.data is not None:
            q = q.filter(Student.stud_group_id == form.stud_group.data.id)

        if form.alumnus_year.data is not None:
            q = q.filter(Student.alumnus_year == form.alumnus_year.data)

        if form.expelled_year.data is not None:
            q = q.filter(Student.expelled_year == form.expelled_year.data)

        q = q.order_by(Student.surname, Student.firstname, Student.middlename)
        result = q.all()

    return render_template('students.html', students=result, form=form)


@app.route('/subjects')
def subjects():
    s = db.session.query(Subject).order_by(Subject.name)
    return render_template('subjects.html', subjects=s)


@app.route('/subject/<id>', methods=['GET', 'POST'])
def subject(id):
    if id == 'new':
        s = Subject()
    else:
        try:
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        s = db.session.query(Subject).filter(Subject.id == id).one_or_none()
        if s is None:
            return 'Not Found', 404

    form = SubjectForm(request.form, obj=s)
    if form.button_delete.data:
        form.validate()
        if db.session.query(CurriculumUnit).filter(CurriculumUnit.subject_id == s.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить предмет, к которому привязаны единицы учебного плана')
        if len(form.button_delete.errors) == 0:
            db.session.delete(s)
            db.session.flush()
            return redirect(url_for('subjects'))

    if form.button_save.data and form.validate():
        form.populate_obj(s)
        db.session.add(s)
        if id == 'new':
            db.session.flush()
            return redirect(url_for('subject', id=s.id))

    return render_template('subject.html', subject=s, form=form)


@app.route('/teachers')
def teachers():
    return render_template('teachers.html', teachers=db.session.query(Teacher).order_by(Teacher.surname, Teacher.firstname, Teacher.middlename))


@app.route('/teacher/<id>', methods=['GET', 'POST'])
def teacher(id):
    if id == 'new':
        t = Teacher()
    else:
        try:
            id = int(id)
        except ValueError:
            return 'Bad Request', 400
        t = db.session.query(Teacher).filter(Teacher.id == id).one_or_none()
        if t is None:
            return 'Not Found', 404

    form = TeacherForm(request.form, obj=t)

    if form.button_delete.data:
        form.validate()
        if db.session.query(CurriculumUnit).filter(CurriculumUnit.teacher_id == t.id).count() > 0:
            form.button_delete.errors.append('Невозможно удалить преподавателя, к которому привязаны единицы учебного плана')
        if len(form.button_delete.errors) == 0:
            db.session.delete(t)
            db.session.flush()
            return redirect(url_for('teachers'))

    if form.button_save.data and form.validate():
        form.populate_obj(t)
        db.session.add(t)
        if id == 'new':
            db.session.flush()
            return redirect(url_for('teacher', id=t.id))

    return render_template('teacher.html', teacher=t, form=form)

# код для курсовой ниже

if __name__ == '__main__':
    app.run()
