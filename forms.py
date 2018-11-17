from datetime import datetime

from app_config import db
from model import StudGroup, Subject, Teacher, Student, CurriculumUnit, AttMark
from wtforms import validators, Form, SubmitField, IntegerField, StringField
from wtforms_alchemy import ModelForm
from wtforms_alchemy.fields import QuerySelectField
from wtforms_alchemy.validators import Unique


class StudGroupForm(ModelForm):
    class Meta:
        model = StudGroup
        exclude = ['active']

    year = IntegerField('Учебный год с 1 сентября',
                        [validators.DataRequired(), validators.NumberRange(min=2000, max=datetime.now().year + 1)])
    semester = IntegerField('Семестр', [validators.DataRequired(), validators.NumberRange(min=1, max=10)])
    num = IntegerField('Группа', [validators.DataRequired(), validators.NumberRange(min=1, max=255)])
    subnum = IntegerField('Подгруппа', [validators.NumberRange(min=0, max=3)])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentForm(ModelForm):
    class Meta:
        model = Student
        include_primary_keys = True

    id = IntegerField('Номер студенческого билета', [validators.DataRequired(), validators.NumberRange(min=1), Unique(Student.id, get_session=lambda: db.session, message='Номер студенческого билета занят')])
    surname = StringField('Фамилия', [validators.DataRequired()])
    firstname = StringField('Имя', [validators.DataRequired()])
    middlename = StringField('Отчество')
    semester = IntegerField('Семестр', [validators.NumberRange(min=1, max=10), validators.Optional()])
    stud_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).filter(StudGroup.active).order_by(
                                      StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num_print),
                                  blank_text='Не указана', allow_blank=True)
    alumnus_year = IntegerField('Учебный год выпуск', [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    expelled_year = IntegerField('Учебный год отчисления', [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentSearchForm(Form):
    id = IntegerField('Номер студенческого билета', [validators.NumberRange(min=1), validators.Optional()])
    surname = StringField('Фамилия', [validators.Length(min=2, max=Student.surname.property.columns[0].type.length), validators.Optional()])
    firstname = StringField('Имя', [validators.Length(min=2, max=Student.firstname.property.columns[0].type.length), validators.Optional()])
    middlename = StringField('Отчество', [validators.Length(min=2, max=Student.middlename.property.columns[0].type.length), validators.Optional()])
    semester = IntegerField('Семестр', [validators.NumberRange(min=1, max=10), validators.Optional()])
    stud_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).filter(StudGroup.active).order_by(
                                      StudGroup.year, StudGroup.semester, StudGroup.num, StudGroup.subnum).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num_print),
                                  blank_text='Неизвестно', allow_blank=True)
    alumnus_year = IntegerField('Учебный год выпуск',
                                [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    expelled_year = IntegerField('Учебный год отчисления',
                                 [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    button_search = SubmitField('Поиск')


class SubjectForm(ModelForm):
    class Meta:
        model = Subject
    name = StringField('Название предмета', [validators.DataRequired(), Unique(Subject.name, get_session=lambda: db.session, message='Предмет с таким названием существует')])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class TeacherForm(ModelForm):
    class Meta:
        model = Teacher

    surname = StringField('Фамилия', [validators.DataRequired()])
    firstname = StringField('Имя', [validators.DataRequired()])
    middlename = StringField('Отчество')
    rank = StringField('Должность', [validators.DataRequired()])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')