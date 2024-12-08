from datetime import datetime

from app_config import db
from model import StudGroup, Subject, SubjectParticular, Teacher, Student, StudentStates, StudentStateDict, CurriculumUnit, AttMark, MarkTypes, MarkTypeDict, AdminUser, Specialty, Department, Person
from wtforms import validators, Form, SubmitField, IntegerField, StringField, SelectField, HiddenField, PasswordField, FormField, BooleanField, DateField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms_alchemy import ModelForm, ModelFieldList, QuerySelectMultipleField
from wtforms_alchemy.fields import QuerySelectField
from wtforms_alchemy.validators import Unique

from sqlalchemy import or_, desc


class PersonForm(ModelForm):
    class Meta:
        model = Person
        exclude = ['allow_jwt_auth']

    surname = StringField('Фамилия', filters=[lambda val: val.strip() if val else None], validators=[validators.Length(min=2, max=45), validators.DataRequired()])
    firstname = StringField('Имя', filters=[lambda val: val.strip() if val else None], validators=[validators.Length(min=2, max=45), validators.DataRequired()])
    middlename = StringField(
        'Отчество',
        validators=[validators.Length(min=2, max=45), validators.Optional()],
        filters=[lambda val: val.strip() if val else None]
    )
    gender = QuerySelectField('Пол', query_factory=lambda: ['M', 'W'],
                              get_pk=lambda val: val,
                              get_label=lambda val: {'M': 'мужской', 'W': 'женский'}[val],
                              blank_text='Не указан', allow_blank=True, validators=[validators.DataRequired(message='Укажите пол')])
    birthday = DateField('Дата рождения', validators=[validators.Optional()], render_kw={"type": "date"})
    login = StringField('Login', filters=[lambda val: val.lower().strip() if val else None], validators=[
            validators.Optional(),
            validators.Length(min=3, max=45),
            validators.Regexp("^[a-z0-9_\\-]+$",
                message="Учётное имя может содержать только латинские символы, цифры и знак подчёркивания"
            ),
            Unique(Person.login, get_session=lambda: db.session, message='Логин занят')
        ])
    email = StringField('E-mail', filters=[lambda val: val.lower().strip() if val else None], validators = [
            validators.Optional(),
            validators.Length(min=4, max=45),
            validators.Email(),
            Unique(Person.email, get_session=lambda: db.session, message='E-mail занят другим пользователем')
        ])
    phone = IntegerField('Сотовый телефон', validators = [
            validators.Optional(),
            validators.NumberRange(min=79000000000, max=79999999999),
            Unique(Person.phone, get_session=lambda: db.session, message='Телефон занят другим пользователем')
        ])

    card_number = IntegerField('Номер карты (пропуска)', [validators.Optional(), validators.NumberRange(min=1),
                                                          Unique(Person.card_number, get_session=lambda: db.session,
                                                                 message='Номер занят')])
    contacts = StringField('Другие контактные данные',
                           validators=[validators.Length(min=4, max=4000), validators.Optional()],
                           filters=[lambda val: val.strip() if val else None])

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class PersonAllowJWTAuthForm(Form):
    allow_jwt_auth = BooleanField('Согласие')


class StudGroupForm(ModelForm):
    class Meta:
        model = StudGroup
        exclude = ['active']

    year = IntegerField('Учебный год с 1 сентября',
                        [validators.DataRequired(), validators.NumberRange(min=2000, max=datetime.now().year + 1)])
    semester = IntegerField('Семестр', [validators.DataRequired(), validators.NumberRange(min=1, max=12)])
    num = IntegerField('Группа', [validators.DataRequired(), validators.NumberRange(min=1, max=255)])
    sub_count = IntegerField('Количество подгрупп', [validators.NumberRange(min=0, max=StudGroup.STUD_GROUP_MAX_SUB_COUNT)])

    specialty = QuerySelectField('Направление (специальность)',
                                  query_factory=lambda: db.session.query(Specialty).filter(Specialty.active).
                                    order_by(Specialty.education_level_order, Specialty.code,
                                             Specialty.name, Specialty.specialization,
                                             Specialty.education_level, Specialty.education_standart).
                                    all(),
                                  get_pk=lambda s: s.id,
                                  get_label=lambda s: s.full_name,
                                  allow_blank=False)

    curator = QuerySelectField('Куратор',
                               query_factory=lambda: db.session.query(Teacher).join(Person, Teacher.person_id == Person.id).join(Department, Teacher.department_id == Department.id).filter(or_(Teacher.department_id == Department.ID_DEFAULT, Department.parent_department_id == Department.ID_DEFAULT)).filter(Teacher.active).order_by(Person.surname, Person.firstname, Person.middlename).all(),
                               get_pk=lambda t: t.id,
                               get_label=lambda t: t.full_name,
                               allow_blank=True,
                               blank_text='Не указан'
                               )

    group_leader = QuerySelectField('Староста',
                               get_pk=lambda s: s.id,
                               get_label=lambda s: s.full_name_short,
                               allow_blank=True,
                               blank_text='Не указан'
                               )

    group_leader2 = QuerySelectField('Староста зам.',
                                    get_pk=lambda s: s.id,
                                    get_label=lambda s: s.full_name_short,
                                    allow_blank=True,
                                    blank_text='Не указан'
                                    )

    lessons_start_date = DateField('Дата начала занятий', validators=[validators.Optional()], render_kw={"type": "date"})
    session_start_date = DateField('Дата начала экзаменационной сессии', validators=[validators.Optional()], render_kw={"type": "date"})
    session_end_date = DateField('Дата окончания экзаменационной сессии', validators=[validators.Optional()], render_kw={"type": "date"})

    weeks_training = IntegerField('Недель теоретического обучения', [validators.DataRequired(), validators.NumberRange(min=0, max=255)])

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudentForm(ModelForm):
    class Meta:
        model = Student
        include_primary_keys = True

    id = IntegerField('Номер студенческого билета', [validators.DataRequired(), validators.NumberRange(min=1), Unique(Student.id, get_session=lambda: db.session, message='Номер студенческого билета занят')])
    student_ext_id = IntegerField('Идентификатор учебной деятельности ВГУ', [validators.Optional(), validators.NumberRange(min=1),
                                                     Unique(Student.student_ext_id, get_session=lambda: db.session,
                                                            message='Идентификатор занят')])
    status = QuerySelectField('Состояние',
                              query_factory=lambda: StudentStates,
                              get_pk=lambda s: s,
                              get_label=lambda s: StudentStateDict[s],
                              allow_blank=False, validators=[validators.DataRequired()])
    semester = IntegerField('Семестр', [validators.NumberRange(min=1, max=12), validators.Optional()])
    stud_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).join(Specialty, StudGroup.specialty_id == Specialty.id).filter(StudGroup.active).order_by(
                                      Specialty.education_level_order, StudGroup.year, StudGroup.semester, StudGroup.num).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс%s группа %s" % (g.course, " маг." if g.specialty.education_level == "master" else "", g.num),
                                  blank_text='Не указана', allow_blank=True)
    stud_group_subnum = IntegerField('Подгруппа', [validators.NumberRange(min=0, max=3), validators.Optional()])

    alumnus_year = IntegerField('Учебный год выпуск', [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    expelled_year = IntegerField('Учебный год отчисления', [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])

    particular_subjects = QuerySelectMultipleField(
        'Особые предметы',
        query_factory=lambda: db.session.query(SubjectParticular).order_by(SubjectParticular.id).all(),
        get_pk=lambda s: s.id,
        get_label=lambda s: s.name,
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput()
    )

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class PersonSearchForm(Form):
    surname = StringField('Фамилия', [validators.Length(min=2, max=Person.surname.property.columns[0].type.length),
                                      validators.Optional()])
    firstname = StringField('Имя', [validators.Length(min=2, max=Person.firstname.property.columns[0].type.length),
                                    validators.Optional()])
    middlename = StringField('Отчество',
                             [validators.Length(min=2, max=Person.middlename.property.columns[0].type.length),
                              validators.Optional()])
    gender = QuerySelectField('Пол', query_factory=lambda: ['M', 'W'],
                       get_pk=lambda val: val,
                       get_label=lambda val: {'M': 'мужской', 'W': 'женский'}[val],
                       blank_text='Не важно', allow_blank=True, validators=[validators.Optional()])

    login = StringField('Login', validators=[
            validators.Optional(),
            validators.Length(min=3, max=Person.login.property.columns[0].type.length),
            validators.Regexp("^[a-z0-9_\\-]+$",
                message="Учётное имя может содержать только латинкие символы, цифры и знак подчёркивания"
            )]
    )
    email = StringField('E-mail', validators=[
        validators.Optional(),
        validators.Length(min=4, max=45),
        validators.Email()
    ])
    phone = IntegerField('Сотовый телефон', validators=[
        validators.Optional(),
        validators.NumberRange(min=79000000000, max=79999999999)
    ])
    card_number = IntegerField('Номер карты (пропуска)', [validators.Optional(), validators.NumberRange(min=1)])
    allow_jwt_auth = SelectField('Разрешение на обработку персональных данных третьему лицу', choices=[('any', 'Не важно'), ('yes', 'Да'), ('no', 'Нет')], default='any')

    role = SelectField('Роль пользователя',
                            choices=[('', 'Не важно'), ('Student', 'Студент'), ('Teacher', 'Преподаватель'),
                                     ('AdminUser', 'Администратор')], default='')

    # Student
    student_id = IntegerField('Номер студенческого билета', [validators.NumberRange(min=1), validators.Optional()])
    student_status = QuerySelectField('Состояние',
                              query_factory=lambda: StudentStates,
                              get_pk=lambda s: s,
                              get_label=lambda s: StudentStateDict[s],
                              blank_text='Не важно', allow_blank=True,
                              validators=[validators.Optional()], default="study")

    student_semester = IntegerField('Семестр', [validators.NumberRange(min=1, max=11), validators.Optional()])
    student_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).filter(StudGroup.active).order_by(
                                      StudGroup.year, StudGroup.semester, StudGroup.num).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num),
                                  blank_text='Неизвестно', allow_blank=True)
    student_alumnus_year = IntegerField('Учебный год выпуск',
                                [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])
    student_expelled_year = IntegerField('Учебный год отчисления',
                                 [validators.NumberRange(min=2000, max=datetime.now().year + 1), validators.Optional()])


    student_subject_particular = QuerySelectField('Изучает особые предметы',
                            query_factory=lambda: db.session.query(SubjectParticular).order_by(SubjectParticular.id).all(),
                            get_pk=lambda s: s.id,
                            get_label=lambda s: s.name,
                            blank_text='Не важно', allow_blank=True)

    student_foreigner = SelectField('Изучает русский язык как иностранный', choices=[('any', 'Не важно'), ('yes', 'Да'), ('no', 'Нет')], default='any')

    # Teacher
    teacher_status = SelectField('Состояние', choices=[('any', 'Не важно'), ('yes', 'Работает'), ('no', 'Не работает')], default='yes')
    teacher_department = QuerySelectField('Факультет / Кафедра',
                                  query_factory=lambda: db.session.query(Department).order_by(Department.id).all(),
                                  get_pk=lambda d: d.id,
                                  get_label=lambda d: d.full_name,
                                  blank_text='Не важно', allow_blank=True)

    # AdminUser
    admin_user_status = SelectField('Состояние', choices=[('any', 'Не важно'), ('yes', 'Работает'), ('no', 'Не работает')], default='yes')

    button_search = SubmitField('Поиск')


class StudentsUnallocatedForm(Form):
    semester = HiddenField()
    students_selected = QuerySelectMultipleField(
        'Студенты',
        get_pk=lambda s: s.id,
        get_label=lambda s: "%d %s" % (s.id, s.full_name),
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput()
    )
    stud_group = QuerySelectField('Группа в которую нужно перевести',
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: g.num,
                                  blank_text='Не указана', allow_blank=True,
                                  validators=[validators.DataRequired('Укажите группу')])

    stud_group_subnum = IntegerField('Подгруппа', [validators.NumberRange(min=0, max=3)])
    button_transfer = SubmitField('Перевести в выбранную группу')


class SubjectForm(ModelForm):
    class Meta:
        model = Subject

    name = StringField('Название предмета', validators=[
        validators.DataRequired(),
        validators.Length(min=3, max=Subject.name.property.columns[0].type.length),
        Unique(Subject.name, get_session=lambda: db.session, message="Предмет с таким названием уже существует")
    ])

    short_name = StringField('Сокращённое название',
        validators=[
            validators.Optional(),
            validators.Length(min=2, max=Subject.short_name.property.columns[0].type.length),
            Unique(Subject.short_name, get_session=lambda: db.session, message="Краткое название предмета уже существует")
        ],
        filters=[lambda val: val if val else None]
    )

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class TeacherForm(ModelForm):
    class Meta:
        model = Teacher

    rank = StringField('Должность', validators=[validators.DataRequired()], filters=[lambda val: val.lower().strip() if val else None])
    academic_degree = StringField('Учёная степень', filters=[lambda val: val.lower().strip() if val else None])
    department = QuerySelectField('Факультет / Кафедра',
                                  validators=[validators.DataRequired(message="Укажите факультет или кафедру")],
                                  query_factory=lambda: db.session.query(Department).order_by(Department.id).all(),
                                  get_pk=lambda d: d.id,
                                  get_label=lambda d: d.full_name,
                                  blank_text='Не указано', allow_blank=True)

    active = BooleanField('Работает')
    dean_staff = BooleanField('Сотрудник деканата')
    department_leader = BooleanField('Зав. кафедрой')
    department_secretary = BooleanField('Секретарь кафедры')
    right_read_all = BooleanField('Разрешено чтение всех данных')

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class AttMarkForm(ModelForm):
    class Meta:
        model = AttMark
        include_primary_keys = True
        only = ['att_mark_id', 'att_mark_1', 'att_mark_2', 'att_mark_3', 'att_mark_exam', 'att_mark_append_ball',
                'simple_mark_test_simple', 'simple_mark_exam', 'simple_mark_test_diff', 'simple_mark_course_work', 'simple_mark_course_project'
                ]

    att_mark_1 = IntegerField('Оценка за 1-ю аттестацию', [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_2 = IntegerField('Оценка за 2-ю аттестацию', [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_3 = IntegerField('Оценка за 3-ю аттестацию', [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_exam = IntegerField('Оценка за экзамен', [validators.NumberRange(min=0, max=50), validators.Optional()])
    att_mark_append_ball = IntegerField('Доп. балл', [validators.NumberRange(min=0, max=10), validators.Optional()])
    simple_mark_test_simple = QuerySelectField('Оценка за зачет',
                                               query_factory=lambda: [0, 2, 5],
                                               get_pk=lambda v: v,
                                               get_label=lambda v: {0: "н.я.", 2: "н.з.", 5: "зач"}.get(v),
                                               blank_text='', allow_blank=True)
    simple_mark_exam = QuerySelectField('Оценка за экзамен',
                                               query_factory=lambda: [0, 2, 3, 4, 5],
                                               get_pk=lambda v: v,
                                               get_label=lambda v: "н.я." if v == 0 else str(v),
                                               blank_text='', allow_blank=True)

    simple_mark_test_diff = QuerySelectField('Оценка за дифференцированный зачет',
                                        query_factory=lambda: [0, 2, 3, 4, 5],
                                        get_pk=lambda v: v,
                                        get_label=lambda v: "н.я." if v == 0 else str(v),
                                        blank_text='', allow_blank=True)

    simple_mark_course_work = QuerySelectField('Оценка за курсовую работу',
                       query_factory=lambda: [0, 2, 3, 4, 5],
                       get_pk=lambda v: v,
                       get_label=lambda v: "н.я." if v == 0 else str(v),
                       blank_text='', allow_blank=True)

    simple_mark_course_project = QuerySelectField('Оценка за курсовую работу',
                                               query_factory=lambda: [0, 2, 3, 4, 5],
                                               get_pk=lambda v: v,
                                               get_label=lambda v: "н.я." if v == 0 else str(v),
                                               blank_text='', allow_blank=True)

    att_mark_id = HiddenField()


class CurriculumUnitForm(ModelForm):
    class Meta:
        model = CurriculumUnit
        exclude = ['closed']

    code = StringField('Шифр по УП', validators=[
        validators.DataRequired(),
        validators.Length(min=1, max=CurriculumUnit.code.property.columns[0].type.length)
    ])

    stud_group = QuerySelectField('Группа',
                                  query_factory=lambda: db.session.query(StudGroup).filter(StudGroup.active).order_by(
                                    StudGroup.year, StudGroup.semester, StudGroup.num).all(),
                                  get_pk=lambda g: g.id,
                                  get_label=lambda g: "%d курс группа %s" % (g.course, g.num),
                                  allow_blank=False)

    teacher = QuerySelectField('Преподаватель',
                                  query_factory=lambda: db.session.query(Teacher).join(Person).order_by(
                                    Person.surname, Person.firstname, Person.middlename).filter(Teacher.active).all(),
                                  get_pk=lambda t: t.id,
                                  get_label=lambda t: t.full_name_short,
                                  blank_text='Не указан', allow_blank=True, validators=[validators.DataRequired()])

    department = QuerySelectField('Кафедра',
                                  validators=[validators.DataRequired(message="Укажите кафедру")],
                                  query_factory=lambda: db.session.query(Department).order_by(Department.id).all(),
                                  get_pk=lambda d: d.id,
                                  get_label=lambda d: d.full_name,
                                  blank_text='Не указана', allow_blank=True)

    subject = QuerySelectField('Предмет',
                               query_factory=lambda: db.session.query(Subject).order_by(
                                   Subject.name).all(),
                               get_pk=lambda s: s.id,
                               get_label=lambda s: s.name,
                               blank_text='Не указан', allow_blank=True, validators=[validators.DataRequired()])

    curriculum_unit_group_id = IntegerField("Код объединения предметов", [validators.NumberRange(min=1, max=4294967295), validators.Optional()])

    hours_att_1 = IntegerField('Часов на 1-ю аттестацию',
                                [validators.NumberRange(min=0, max=255)], render_kw={"required": True})
    hours_att_2 = IntegerField('Часов на 2-ю аттестацию',
                               [validators.NumberRange(min=0, max=255)], render_kw={"required": True})
    hours_att_3 = IntegerField('Часов на 3-ю аттестацию',
                               [validators.NumberRange(min=0, max=255)], render_kw={"required": True})

    hours_lect = IntegerField('Часов лекционных занятий',
                              [validators.NumberRange(min=0, max=255)], render_kw={"required": True})
    hours_pract = IntegerField('Часов практических занятий',
                               [validators.NumberRange(min=0, max=255)], render_kw={"required": True})
    hours_lab = IntegerField('Часов лабораторных занятий',
                             [validators.NumberRange(min=0, max=255)], render_kw={"required": True})

    moodle_id = IntegerField('Код учебного курса Moodle',
                               [validators.NumberRange(min=1, max=4294967295), validators.Optional()])
    mark_type = QuerySelectField('Тип отчётности', query_factory=lambda: MarkTypes,
                                 get_pk=lambda t: t,
                                 get_label=lambda t: MarkTypeDict[t],
                                 blank_text='Не указан', allow_blank=True, validators=[validators.DataRequired()])

    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class CurriculumUnitPracticeTeacherAddForm(Form):
    teacher = QuerySelectField('Преподаватель',
                               query_factory=lambda: db.session.query(Teacher).join(Person).filter(Teacher.active).order_by(Person.surname, Person.firstname, Person.middlename).all(),
                               get_pk=lambda t: t.id,
                               get_label=lambda t: t.full_name_short,
                               allow_blank=False)

    button_add = SubmitField('Добавить')


class TeacherAddDepartmentPartTimeJobForm(Form):
    department = QuerySelectField('Кафедра',
                                  query_factory=lambda: db.session.query(Department).order_by(Department.id).all(),
                                  get_pk=lambda d: d.id,
                                  get_label=lambda d: d.full_name,
                               allow_blank=False)

    button_add = SubmitField('Добавить')


class AttMarksForm(ModelForm):
    att_marks = ModelFieldList(FormField(AttMarkForm))
    button_print = SubmitField('Печать')

    button_print_simple_marks_test_simple = SubmitField('Печать ведомости - Зачет')
    button_print_simple_marks_exam = SubmitField('Печать ведомости - Экзамен')
    button_print_simple_marks_test_diff = SubmitField('Печать ведомости - Дифференцированный зачёт')
    button_print_simple_marks_course_work = SubmitField('Печать ведомости - Курсовая работа')
    button_print_simple_marks_course_project = SubmitField('Печать ведомости - Курсовой проект')

    button_save = SubmitField('Сохранить')
    button_clear = SubmitField('Очистить данные ведомости')
    button_open = SubmitField('Открыть ведомость')
    button_close = SubmitField('Закрыть ведомость')


class CurriculumUnitCopyForm(Form):
    stud_groups_selected = QuerySelectMultipleField(
        'Группы',
        get_pk=lambda g: g.id,
        get_label=lambda g: "%s %s" % (g.num, g.specialty.full_name),
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput()
    )
    button_copy = SubmitField('Копировать')


class AdminUserForm(ModelForm):
    class Meta:
        model = AdminUser

    active = BooleanField('Учётная запись включена')
    button_save = SubmitField('Сохранить')
    button_delete = SubmitField('Удалить')


class StudGroupsPrintForm(Form):
    stud_groups_selected = QuerySelectMultipleField(
        'Студенческие группы',
        get_pk=lambda g: g.id,
        get_label=lambda g: "Курс %d%s Группа %s %s" % (g.course, " маг." if g.specialty.education_level == "master" else "", g.num, g.specialty.full_name),
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput()
    )
    name_format = SelectField('Формат имени студента',
                            choices=[('full_name', 'Фамилия Имя Отчество'), ('full_name2', 'Фамилия Имя'),
                                     ('full_name_short', 'Фамилия И. О.')])

    split_sub_group = BooleanField('Разделять подгруппы')

    button_excel = SubmitField('Сформировать Excel файл')


class RatingForm(Form):
    education_level_order = SelectField('Уровень образования', choices=[(1, 'бакалавр/специалист'), (2, 'магистр')], default=1)
    year = QuerySelectField("Учебный год",
        query_factory=lambda: [row[0] for row in db.session.query(StudGroup.year).order_by(desc(StudGroup.year)).distinct()],
        get_pk=lambda y: y,
        get_label=lambda y: "%d-%d" % (y, y+1),
        allow_blank=True,
        blank_text="Выберите учебный год"
    )

    semester = SelectField('Семестр', choices=[(1, 'осень-зима'), (2, 'весна-лето')])

    course = QuerySelectField(
        'Курс',
        query_factory=lambda: [],
        get_pk=lambda c: c,
        get_label=lambda c: str(c),
        allow_blank=True,
        blank_text="Выберите курс"
    )

    specialty = QuerySelectField("Направление / специальность",
        query_factory=lambda: db.session.query(Specialty.code, Specialty.name).order_by(Specialty.code).distinct(),
        get_pk=lambda row: row[0],
        get_label=lambda row: "%s %s" % (row[0], row[1]),
        allow_blank=True,
        blank_text="Все"
    )

    stud_group = QuerySelectField("Группа",
        query_factory=lambda: [],
        get_pk=lambda g: g.id,
        get_label=lambda g: "%d (%s)" % (
        g.num, g.specialty.specialization) if g.specialty.specialization else g.num,
        allow_blank=True,
        blank_text="Все"
    )

    stage = SelectField('Этап', choices=[
        ('att_mark_1', 'Аттестация 1'),
        ('att_mark_2', 'Аттестация 2'),
        ('att_mark_3', 'Аттестация 3'),
        ('total', 'Итог'),
    ])


class LessonsReportForm(Form):
    year = QuerySelectField("Учебный год",
        get_pk=lambda y: y,
        get_label=lambda y: "%d-%d" % (y, y + 1),
        allow_blank=True,
        blank_text="Выберите учебный год"
    )
    semester = QuerySelectField("Курс / семестр",
        get_pk=lambda s: s,
        get_label=lambda s: "%d курс %d семестр" % (((s - 1) // 2) + 1, s),
        allow_blank=True,
        blank_text="Выберите семестр"
    )

    curriculum_unit = QuerySelectField("Предмет",
        get_pk=lambda cu: cu.id,
        get_label=lambda cu: cu.subject_name_print,
        allow_blank=True,
        blank_text="Все"
    )


class _LoginForm(Form):
    temporary_entrance = BooleanField("Чужой компьютер")
    button_login = SubmitField('Вход')


class LoginForm(_LoginForm):
    login = StringField('Login', filters=[lambda val: val.lower().strip() if val else None])
    password = PasswordField('Пароль')


class LoginEmailForm(_LoginForm):
    email = StringField('E-mail', validators=[validators.DataRequired(), validators.Email()], filters=[lambda val: val.lower().strip() if val else None])
    code = IntegerField('Введите код, отправленный на ваш e-mail', validators=[validators.Optional(), validators.NumberRange(min=100000, max=999999, message='Проверочный код должен состоять из 6-ти цифр')], render_kw={"autocomplete": "off"})
    button_send_email = SubmitField('Отправить код на E-mail')


class LoginSMSForm(_LoginForm):
    phone = IntegerField('Телефон', validators=[validators.DataRequired(), validators.NumberRange(min=79000000000, max=79999999999)])
    code = IntegerField('Введите код из SMS', validators=[validators.Optional(), validators.NumberRange(min=100000, max=999999, message='Проверочный код должен состоять из 6-ти цифр')], render_kw={"autocomplete": "off"})
    button_send_sms = SubmitField('Отправить SMS с кодом')