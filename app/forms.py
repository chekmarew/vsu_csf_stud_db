"""Файл с различными формами, необходимыми для приложения"""
from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import Form
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import validators
from wtforms_alchemy import ModelForm
from wtforms_alchemy.fields import QuerySelectField
from wtforms_alchemy.validators import Unique

from app import DB
from app.model import StudGroup
from app.model import Student
from app.model import Subject
from app.model import Teacher


class StudGroupForm(ModelForm):
    """Форма для удаления/добавления группы студента"""

    class Meta:
        """Метаданные к форме"""
        model = StudGroup
        exclude = ['active']

    year = IntegerField('Учебный год с 1 сентября',
                        [validators.DataRequired(),
                         validators.NumberRange(min=2000, max=datetime.now().year + 1)])
    semester = IntegerField('Семестр', [validators.DataRequired(),
                                        validators.NumberRange(min=1, max=10)])
    num = IntegerField('Группа', [validators.DataRequired(),
                                  validators.NumberRange(min=1, max=255)])
    subnum = IntegerField('Подгруппа', [validators.NumberRange(min=0, max=3)])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentForm(ModelForm):
    """Форма для добавления/удаления студента"""

    class Meta:
        """Метаданные для формы"""
        model = Student
        include_primary_keys = True

    id = IntegerField('Номер студенческого билета',
                      [validators.DataRequired(),
                       validators.NumberRange(min=1),
                       Unique(Student.id,
                              get_session=lambda: DB.session,
                              message='Номер студенческого билета занят')])
    surname = StringField('Фамилия', [validators.DataRequired()])
    firstname = StringField('Имя', [validators.DataRequired()])
    middlename = StringField('Отчество')
    semester = IntegerField('Семестр',
                            [validators.NumberRange(min=1, max=10),
                             validators.Optional()])
    stud_group = QuerySelectField('Группа',
                                  query_factory=
                                  lambda: DB.session.query(StudGroup).
                                  filter(StudGroup.active).order_by(
                                      StudGroup.year,
                                      StudGroup.semester,
                                      StudGroup.num,
                                      StudGroup.subnum
                                  ).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num_print),
                                  blank_text='Не указана', allow_blank=True)
    alumnus_year = IntegerField('Учебный год выпуск',
                                [validators.NumberRange(min=2000, max=datetime.now().year + 1),
                                 validators.Optional()])
    expelled_year = IntegerField('Учебный год отчисления',
                                 [validators.NumberRange(min=2000, max=datetime.now().year + 1),
                                  validators.Optional()])

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentSearchForm(Form):
    """Форма для поиска студента по его данным"""
    id = IntegerField('Номер студенческого билета',
                      [validators.NumberRange(min=1),
                       validators.Optional()])
    surname = StringField('Фамилия',
                          [validators.Length(
                              min=2, max=Student.surname.property.columns[0].type.length),
                           validators.Optional()])
    firstname = StringField('Имя',
                            [validators.Length(
                                min=2, max=Student.firstname.property.columns[0].type.length),
                             validators.Optional()])
    middlename = StringField('Отчество',
                             [validators.Length(
                                 min=2, max=Student.middlename.property.columns[0].type.length),
                              validators.Optional()])
    semester = IntegerField('Семестр',
                            [validators.NumberRange(min=1, max=10),
                             validators.Optional()])
    stud_group = QuerySelectField('Группа',
                                  query_factory=
                                  lambda: DB.session.query(StudGroup).
                                  filter(StudGroup.active).order_by(
                                      StudGroup.year,
                                      StudGroup.semester,
                                      StudGroup.num,
                                      StudGroup.subnum
                                  ).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num_print),
                                  blank_text='Неизвестно', allow_blank=True)
    alumnus_year = IntegerField('Учебный год выпуск',
                                [validators.NumberRange(min=2000, max=datetime.now().year + 1),
                                 validators.Optional()])
    expelled_year = IntegerField('Учебный год отчисления',
                                 [validators.NumberRange(min=2000, max=datetime.now().year + 1),
                                  validators.Optional()])
    button_search = SubmitField('Поиск')


class SubjectForm(ModelForm):
    """Форма для добавления/удаления учебного предмета"""

    class Meta:
        """Метаданные для формы"""
        model = Subject

    name = StringField('Название предмета',
                       [validators.DataRequired(),
                        Unique(Subject.name,
                               get_session=lambda: DB.session,
                               message='Предмет с таким названием существует')])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class TeacherForm(ModelForm):
    """Форма для добавления/удаления учителя"""

    class Meta:
        """Метаданные для формы"""
        model = Teacher

    surname = StringField('Фамилия', [validators.DataRequired()])
    firstname = StringField('Имя', [validators.DataRequired()])
    middlename = StringField('Отчество')
    rank = StringField('Должность', [validators.DataRequired()])
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


# код для курсовой ниже


class LoginForm(FlaskForm):
    """Форма авторизации пользователя в системе"""
    username = StringField('username',
                           validators=[
                               validators.InputRequired(), validators.Length(max=50)
                           ])
    password = PasswordField('password',
                             validators=[
                                 validators.InputRequired(), validators.Length(max=255)
                             ])


class RegisterForm(FlaskForm):
    """Форма регистрации пользователя в системе"""
    username = StringField('username',
                           validators=[
                               validators.InputRequired(), validators.Length(max=50)
                           ])
    password = PasswordField('password',
                             validators=[
                                 validators.InputRequired(), validators.Length(max=255)
                             ])
