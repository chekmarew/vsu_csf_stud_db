from app_config import db

from sqlalchemy import and_
from sqlalchemy.orm import deferred
from sqlalchemy.ext.declarative import DeferredReflection

from datetime import datetime, timedelta

# Типы
StudentStates = ("study", "alumnus", "expelled", "academic_leave")
StudentStateDict = {
    "study": "учится",
    "alumnus": "успешно закончил обучение",
    "expelled": "отчислен",
    "academic_leave": "в академическом отпуске"
}

# Типы отчётности для единицы учебного плана
MarkTypes = ("test_simple", "exam", "test_diff", "no_mark", "no_att")
MarkTypeDict = {
    "test_simple": "Зачет",
    "exam": "Экзамен",
    "test_diff": "Дифференцированный зачет",
    "no_mark": "Нет",
    "no_att": "Аттестации не предусмотрены"
}

TopicTypes = ('none', 'coursework', 'project_seminar')
TopicTypeDict = {
    'none': "Не относится",
    'coursework': "Курсовая / Выпускная / Научная работа",
    'project_seminar': "Проектный семинар"
}

MarkSimpleTypes = ("test_simple", "exam", "test_diff", "course_work", "course_project")
MarkSimpleTypeDict = {
    "test_simple": "Зачет",
    "exam": "Экзамен",
    "test_diff": "Дифференцированный зачет",
    "course_work": "Курсовая работа по дисциплине",
    "course_project": "Курсовой проект по дисциплине"
}


# Состояния аттестационной ведомости
DocStatuses = ('empty', 'att_1', 'att_2', 'att_3', 'exam', 'filled', 'closed')
DocStatusDict = {
    'empty': "Не заполнена",
    'att_1': "Аттестация 1",
    'att_2': "Аттестация 2",
    'att_3': "Аттестация 3",
    'exam': "Экзамен",
    'filled': "Заполнена",
    'closed': "Закрыта"
}

# Уровни образования
EducationLevels = ('bachelor', 'specialist', 'master')
EducationLevelDict = {
    'bachelor': 'Бакалавр',
    'specialist': 'Специалист',
    'master': 'Магистр'
}

EducationStandarts = ('', 'fgos3+', 'fgos3++')
EducationStandartDict = {
    '': '',
    'fgos3+': 'ФГОС3+',
    'fgos3++': 'ФГОС3++'
}

# Формы обучения
EducationForms = ('full-time', 'part-time', 'correspondence')
EducationFormDict = {
    'full-time': "Очная",
    'part-time': "Очно-заочная",
    'correspondence': "Заочная"
}

Financing = ('budget', 'contract')
FinancingDict = {
    'budget': "бюджет",
    'contract': "договор"
}

# Типы занятий
LessonTypes = ('seminar', 'lecture')

# Типы занятий для расписания
LessonTypesScheduled = ('lecture', 'pract', 'lab')

# Формы занятий
LessonForms = ('in_class', 'remote')


class _Person:
    @property
    def surname(self):
        return self.person.surname if self.person else None

    @property
    def firstname(self):
        return self.person.firstname if self.person else None

    @property
    def middlename(self):
        return self.person.middlename if self.person else None

    @property
    def login(self):
        return self.person.login if self.person else None

    @property
    def card_number(self):
        return self.person.card_number if self.person else None

    @property
    def email(self):
        return self.person.email if self.person else None

    @property
    def phone(self):
        return self.person.phone if self.person else None

    @property
    def contacts(self):
        return self.person.contacts if self.person else None

    @property
    def full_name(self):
        return self.person.full_name if self.person else None

    @property
    def full_name2(self):
        return self.person.full_name2 if self.person else None

    @property
    def full_name_short(self):
        return self.person.full_name_short if self.person else None

    @property
    def phone_str(self):
        return self.person.phone_str if self.person else None

    @property
    def phone_format(self):
        return self.person.phone_format if self.person else None


class _ObjectWithSemester:
    @property
    def course(self):
        if self.semester is None:
            return None
        return ((self.semester - 1) // 2) + 1

    @property
    def session_num(self):
        if self.semester is None:
            return None
        if self.semester % 2 == 1:
            return 1
        else:
            return 2

    @property
    def session_type(self):
        if self.semester is None:
            return None
        if self.semester % 2 == 1:
            return 'зимняя сессия'
        else:
            return 'летняя сессия'


class _ObjectWithYear:
    @property
    def year_print(self):
        if self.year is None:
            return None
        return "%d-%d" % (self.year, self.year + 1)


class _ObjectWithStudGroupSubnumsMap:

    @property
    def stud_group_subnums_map(self):
        stud_group = self.stud_group if hasattr(self, "stud_group") else self.curriculum_unit.stud_group

        if stud_group.sub_count == 0:
            return [True]
        _r = [None] * (stud_group.sub_count + 1)
        for num in range(stud_group.sub_count):
            _r[num + 1] = bool((self.stud_group_subnums >> num) & 1)

        return _r

    @stud_group_subnums_map.setter
    def stud_group_subnums_map(self, value):
        stud_group = self.stud_group if hasattr(self, "stud_group") else self.curriculum_unit.stud_group
        self.stud_group_subnums = 0
        if stud_group.sub_count > 1:
            for num in range(stud_group.sub_count):
                if value[num + 1]:
                    self.stud_group_subnums |= (1 << num)


class Person(db.Model):
    __tablename__ = 'person'

    id = db.Column('person_id', db.INTEGER, primary_key=True, autoincrement=True)
    surname = db.Column('surname', db.String(45), nullable=False)
    firstname = db.Column('firstname', db.String(45), nullable=False)
    middlename = db.Column('middlename', db.String(45))
    login = db.Column('login', db.String(45), unique=True)
    card_number = db.Column('card_number', db.BIGINT, unique=True)
    email = db.Column('email', db.String(45), unique=True)
    phone = db.Column('phone', db.BIGINT, unique=True)
    contacts = db.Column('contacts', db.String(4000))
    gender = db.Column('gender', db.Enum('M', 'W'))
    birthday = db.Column('birthday', db.Date)

    students = db.relationship('Student', lazy='subquery', backref='person')
    teacher = db.relationship('Teacher', backref='person', uselist=False)
    admin_user = db.relationship('AdminUser', backref='person', uselist=False)
    history = db.relationship('PersonHist', lazy='dynamic', primaryjoin='Person.id == PersonHist.person_id', backref='person')

    @property
    def surname_old(self):
        r = []
        for h in self.history.filter(PersonHist.surname != self.surname).filter(PersonHist.etime >= datetime.now() - timedelta(days=150)).order_by(PersonHist.stime.desc()).all():
            if h.surname not in r:
                r.append(h.surname)
        if len(r) == 0:
            return None
        else:
            return ", ".join(r)

    @property
    def surname_old_all_time(self):
        r = []
        for h in self.history.filter(PersonHist.surname != self.surname).order_by(PersonHist.stime.desc()).all():
            if h.surname not in r:
                r.append(h.surname)
        if len(r) == 0:
            return None
        else:
            return ", ".join(r)

    @property
    def surname_with_old(self):
        surname_old = self.surname_old
        if surname_old is not None:
            return "%s (%s)" % (self.surname, surname_old)
        else:
            return self.surname

    @property
    def full_name(self):
        if self.surname is None or self.firstname is None:
            return None

        return " ".join((self.surname_with_old, self.firstname, self.middlename) if self.middlename is not None and len(
            self.middlename) > 0 else (
            self.surname, self.firstname))

    @property
    def full_name2(self):
        if self.surname is None or self.firstname is None:
            return None
        return "%s %s" % (self.surname_with_old, self.firstname)

    @property
    def full_name_short(self):
        if self.surname is None or self.firstname is None:
            return None
        return "%s %s. %s." % (
        self.surname_with_old, self.firstname[0], self.middlename[0]) if self.middlename is not None and len(self.middlename) > 0 \
            else "%s %s." % (self.surname, self.firstname[0])

    @property
    def phone_str(self):
        if self.phone:
            return "+%d" % self.phone

    @property
    def phone_format(self):
        if self.phone:
            return self.phone_str[:-10] + '-' + self.phone_str[-10:-7] + '-' + self.phone_str[-7:-4] + '-' + self.phone_str[-4:-2] + '-' + self.phone_str[-2:]

    @property
    def roles(self):
        _roles = []
        if self.admin_user and self.admin_user.active:
            _roles.append(self.admin_user)
        if self.teacher and self.teacher.active:
            _roles.append(self.teacher)
        if len(self.students) > 0:
            _roles.extend(self.students)

        return _roles

    @property
    def roles_active(self):
        _roles = []
        if self.admin_user and self.admin_user.active:
            _roles.append(self.admin_user)
        if self.teacher and self.teacher.active:
            _roles.append(self.teacher)

        for s in self.students:
            if s.status in ("study", "academic_leave"):
                _roles.append(s)

        return _roles

    @property
    def roles_all(self):
        _roles = []
        if self.admin_user:
            _roles.append(self.admin_user)
        if self.teacher:
            _roles.append(self.teacher)
        if len(self.students) > 0:
            _roles.extend(self.students)
        return _roles

    @property
    def user_rights(self):
        _rights = {}
        for r in self.roles:
            for k, v in r.user_rights.items():
                if k not in _rights:
                    _rights[k] = v
                else:
                    _rights[k] = _rights[k] or v

        return _rights

    # Активная запись студента
    @property
    def student(self):
        for s in self.students:
            if s.status in ("study", "academic_leave"):
                return s

        return None

    # Flask-Login Support
    @property
    def is_active(self):
        """True, as all users are active."""
        return len(self.roles) > 0

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    journalize_attributes = ('surname', 'firstname', 'middlename', 'login', 'card_number', 'email', 'phone', 'contacts')


class PersonHist(db.Model):
    person_id = db.Column(db.ForeignKey('person.person_id', ondelete='CASCADE', onupdate='CASCADE'),
                            nullable=False)
    stime = db.Column(db.DateTime, nullable=False)
    etime = db.Column(db.DateTime)

    changed_person_id = db.Column(db.ForeignKey('person.person_id'))
    user = db.relationship('Person', foreign_keys=[changed_person_id])

    surname = db.Column('surname', db.String(45), nullable=False)
    firstname = db.Column('firstname', db.String(45), nullable=False)
    middlename = db.Column('middlename', db.String(45))
    login = db.Column('login', db.String(45), unique=True)
    card_number = db.Column('card_number', db.BIGINT, unique=True)
    email = db.Column('email', db.String(45), unique=True)
    phone = db.Column('phone', db.BIGINT, unique=True)
    contacts = db.Column('contacts', db.String(4000))

    __table_args__ = (
        db.PrimaryKeyConstraint('person_id', 'stime'),
    )


Person.journalize_class = PersonHist


class Student(db.Model, _Person, _ObjectWithSemester):
    __tablename__ = 'student'

    id = db.Column('student_id', db.BIGINT, primary_key=True)
    person_id = db.Column(db.ForeignKey('person.person_id'))
    student_ext_id = db.Column('student_ext_id', db.BIGINT, unique=True, nullable=False)

    specialty_id = db.Column(db.ForeignKey('specialty.specialty_id'), index=True, nullable=False)
    specialty = db.relationship('Specialty', foreign_keys=[specialty_id])

    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id', ondelete='SET NULL'), index=True)
    stud_group_subnum = db.Column('student_stud_group_subnum', db.SMALLINT)
    semester = db.Column('student_semestr', db.SMALLINT)
    alumnus_year = db.Column('student_alumnus_year', db.SMALLINT)
    expelled_year = db.Column('student_expelled_year', db.SMALLINT)
    status = db.Column('student_status', db.Enum(*StudentStateDict.keys()), nullable=False)
    financing = db.Column('financing', db.Enum(*FinancingDict.keys()), nullable=False)
    particular_subjects = db.relationship('SubjectParticular',
        secondary=db.Table(
            'student_subject_particular',
            db.Column('student_id', db.ForeignKey('student.student_id')),
            db.Column('subject_particular_id', db.ForeignKey('subject_particular.subject_particular_id'))
        ))

    certificates_of_study = db.relationship('CertificateOfStudy', lazy='dynamic',
                               backref='student')

    # foreigner = db.Column('student_foreigner', db.BOOLEAN, nullable=False, default=False)
    @property
    def foreigner(self):
        for sp in self.particular_subjects:
            if sp.id in SubjectParticular.IDS_FOREIGN_LANGUAGE:
                return True
        return False

    @property
    def status_name(self):
        if self.status and self.status in StudentStateDict:
            return StudentStateDict[self.status]

    @property
    def financing_name(self):
        if self.financing and self.financing in FinancingDict:
            return FinancingDict[self.financing]

    @property
    def active(self):
        return True

    @property
    def user_rights(self):
        return {
            "stud_groups": False,
            "persons": False,
            "rating": True
        }

    @property
    def role_name(self):
        return 'Student'

    def get_rights(self, person):
        r = {
            "read_marks": False,
            "write": False,
        }

        for u in person.roles:
            if u.role_name == 'AdminUser':
                r["read_marks"] = True
                r["write"] = True

            if u.role_name == 'Teacher' and u.id is not None:
                if u.dean_staff or u.department_leader or u.right_read_all or u.department_secretary:
                    r["read_marks"] = True
                else:
                    if self.stud_group is not None and self.stud_group.curator_id == u.id:
                        r["read_marks"] = True

            if u.role_name == 'Student':
                if self.id == u.id:
                    r["read_marks"] = True
        return r


class Department(db.Model):

    ID_DEFAULT = 1600

    __tablename__ = 'department'

    id = db.Column('department_id', db.INTEGER, primary_key=True)
    name = db.Column('department_name', db.String(128), nullable=False, unique=True)
    name_short = db.Column('department_name_short', db.String(32), unique=True)
    parent_department_id = db.Column(db.ForeignKey('department.department_id'), index=True)
    parent_department = db.relationship('Department', remote_side=[id])

    chief_id = db.Column(db.ForeignKey('person.person_id'), index=True)
    chief = db.relationship('Person', foreign_keys=[chief_id])
    chief_title = db.Column('chief_title', db.String(128))



    @property
    def full_name(self):
        if self.parent_department is not None and \
                not (self.parent_department_id == self.ID_DEFAULT):
            return "%s: %s" % (self.parent_department.name, self.name)
        else:
            return self.name


class Specialty(db.Model):
    __tablename__ = 'specialty'
    __table_args__ = (
        db.UniqueConstraint('specialty_code', 'specialty_name', 'specialization', 'module_name', 'education_level',
                            'education_standart'),
    )

    id = db.Column('specialty_id', db.INTEGER, primary_key=True, autoincrement=True)
    code = db.Column('specialty_code', db.String(16), nullable=False)
    name = db.Column('specialty_name', db.String(256), nullable=False)
    specialization = db.Column('specialization', db.String(256), nullable=False, default='')
    module_name = db.Column('module_name', db.String(256), nullable=False, default='')
    education_level_order = db.Column('education_level_order', db.SMALLINT, nullable=False, default=1)
    education_level = db.Column('education_level', db.Enum(*EducationLevels), nullable=False, default='bachelor')
    education_standart = db.Column('education_standart', db.Enum(*EducationStandarts), nullable=False,
                                   default='fgos3++')
    education_form = db.Column('education_form', db.Enum(*EducationForms), nullable=False,
                                   default='full-time')

    active = db.Column('specialty_active', db.BOOLEAN, nullable=False, default=True)

    department_id = db.Column(db.ForeignKey('department.department_id'), index=True, nullable=False, default=Department.ID_DEFAULT)
    department = db.relationship('Department', foreign_keys=[department_id])

    parent_specialty_id = db.Column(db.ForeignKey('specialty.specialty_id'), index=True)
    parent_specialty = db.relationship('Specialty', remote_side=[id])

    semestr_distirib = db.Column('semestr_distirib', db.SMALLINT)
    semestr_end = db.Column('semestr_end', db.SMALLINT, nullable=False)

    faculty_id = db.Column(db.ForeignKey('department.department_id'), index=True, nullable=False, default=Department.ID_DEFAULT)
    faculty = db.relationship('Department', foreign_keys=[faculty_id])

    @property
    def education_level_name(self):
        if self.education_level:
            return EducationLevelDict[self.education_level]

    @property
    def education_standart_name(self):
        if self.education_standart is not None:
            return EducationStandartDict[self.education_standart]

    @property
    def education_form_name(self):
        if self.education_form:
            return EducationFormDict[self.education_form]

    @property
    def full_name(self):
        if self.code and self.name and self.education_level and self.education_standart is not None:
            if self.specialization:
                if self.module_name:
                    return "%s %s(%s, модуль: %s) %s(%s)" % (self.code,
                                                 self.name,
                                                 self.specialization,
                                                 self.module_name,
                                                 self.education_level_name,
                                                 self.education_standart_name)
                else:

                    return "%s %s(%s) %s(%s)" % (self.code,
                                                 self.name,
                                                 self.specialization,
                                                 self.education_level_name,
                                                 self.education_standart_name)
            else:
                return "%s %s %s(%s)" % (self.code,
                                         self.name,
                                         self.education_level_name,
                                         self.education_standart_name)


class StudGroup(db.Model, _ObjectWithSemester, _ObjectWithYear):
    __tablename__ = 'stud_group'
    __table_args__ = (
        db.UniqueConstraint('stud_group_year', 'stud_group_semester', 'stud_group_num'),
    )
    # Максимальное количество подгрупп
    STUD_GROUP_MAX_SUB_COUNT = 3

    id = db.Column('stud_group_id', db.INTEGER, primary_key=True, autoincrement=True)
    year = db.Column('stud_group_year', db.SMALLINT, nullable=False)
    semester = db.Column('stud_group_semester', db.SMALLINT, nullable=False)
    num = db.Column('stud_group_num', db.SMALLINT, nullable=False)

    sub_count = db.Column('stud_group_sub_count', db.SMALLINT, nullable=False, default=0)
    specialty_id = db.Column(db.ForeignKey('specialty.specialty_id'), nullable=False, index=True)
    specialty = db.relationship('Specialty')

    active = db.Column('stud_group_active', db.BOOLEAN, nullable=False, default=True)

    curator_id = db.Column(db.ForeignKey('teacher.teacher_id', ondelete='SET NULL'), index=True)
    group_leader_id = db.Column(db.ForeignKey('student.student_id', ondelete='SET NULL', onupdate='CASCADE'), index=True)
    group_leader2_id = db.Column(db.ForeignKey('student.student_id', ondelete='SET NULL', onupdate='CASCADE'), index=True)

    curator = db.relationship('Teacher', foreign_keys=[curator_id])
    group_leader = db.relationship('Student', foreign_keys=[group_leader_id])
    group_leader2 = db.relationship('Student', foreign_keys=[group_leader2_id])

    lessons_start_date = db.Column('lessons_start_date', db.Date)
    session_start_date = db.Column('session_start_date', db.Date)
    session_end_date = db.Column('session_end_date', db.Date)

    weeks_training = db.Column('weeks_training', db.SMALLINT, nullable=False, default=0)

    students = db.relationship('Student', lazy=True,
                               order_by="Student.id",
                               backref='stud_group',
                               foreign_keys=[Student.stud_group_id]
                               )

    curriculum_units = db.relationship('CurriculumUnit', lazy=True,
                                       backref='stud_group',
                                       order_by="CurriculumUnit.id")

    scheduled_subject_particular = db.relationship('ScheduledSubjectParticular', lazy=True, backref='stud_group')
    scheduled_subject_particular_draft = db.relationship('ScheduledSubjectParticularDraft', lazy=True, backref='stud_group')


    def get_rights(self, person):
        # Проверка прав доступа
        r = {
            "read_list": False,
            "read_marks": False,
            "write": False,
        }
        for u in person.roles:
            if u.role_name == 'AdminUser':
                r["read_list"] = True
                r["read_marks"] = True
                r["write"] = self.active

            if u.role_name == 'Teacher':
                if u.dean_staff or u.department_leader or u.right_read_all or u.department_secretary or self.curator_id == u.id:
                    r["read_list"] = True
                    r["read_marks"] = True
                else:
                    if any(cu.teacher_id == u.id or any(t.id == u.id for t in cu.practice_teachers) for cu in self.curriculum_units):
                        r["read_list"] = True

            if u.role_name == 'Student':
                if u.id in (group_leader_id for group_leader_id in (self.group_leader_id, self.group_leader2_id) if group_leader_id is not None):
                    r["read_list"] = True
                    r["read_marks"] = True
                elif u.stud_group_id is not None and self.id == u.stud_group_id:
                    r["read_list"] = True
        return r

    @property
    def department(self):
        if self.specialty is not None and self.specialty.department is not None and self.specialty.department.id != Department.ID_DEFAULT:
            return self.specialty.department

        if self.curator is not None and self.curator.department is not None and self.curator.department.id != Department.ID_DEFAULT:
            return self.curator.department

    @property
    def students_subgroup_count_map(self):
        if not self.active:
            return None

        r = [None]*(self.STUD_GROUP_MAX_SUB_COUNT + 1)
        if self.sub_count == 0:
            r[0] = 0
        else:
            for i in range(1, self.sub_count+1):
                r[i] = 0
        for s in self.students:
            if s.stud_group_subnum is None or r[s.stud_group_subnum] is None:
                continue
            r[s.stud_group_subnum] += 1

        return r

    @property
    def course_print(self):
        if self.specialty and self.specialty.education_level == "master":
            return "%d маг." % self.course
        else:
            return str(self.course)


class Subject(db.Model):

    __tablename__ = 'subject'

    id = db.Column('subject_id', db.INTEGER, primary_key=True, autoincrement=True)
    name = db.Column('subject_name', db.String(256), nullable=False, unique=True)
    short_name = db.Column('subject_short_name', db.String(48), unique=True)
    without_specifying_schedule = db.Column('subject_without_specifying_schedule', db.BOOLEAN, nullable=False, default=False)


class SubjectParticular(db.Model):

    # Идентификатор в БД предмета иностранный язык для иностранцев
    IDS_FOREIGN_LANGUAGE = (1, 2)

    __tablename__ = 'subject_particular'

    id = db.Column('subject_particular_id', db.INTEGER, primary_key=True, autoincrement=True)
    name = db.Column('subject_particular_name', db.String(256), nullable=False, unique=True)
    short_name = db.Column('subject_particular_short_name', db.String(48), nullable=False, unique=True)

    replaced_subject_id = db.Column(db.ForeignKey('subject.subject_id'))
    replaced_subject = db.relationship('Subject', foreign_keys=[replaced_subject_id])


class Teacher(db.Model, _Person):
    __tablename__ = 'teacher'

    id = db.Column('teacher_id', db.INTEGER, primary_key=True, autoincrement=True)
    person_id = db.Column(db.ForeignKey('person.person_id'))

    rank = db.Column('teacher_rank', db.String(45), nullable=False)
    academic_degree = db.Column('teacher_academic_degree', db.String(128))
    active = db.Column('teacher_active', db.BOOLEAN, nullable=False, default=True)
    department_id = db.Column(db.ForeignKey('department.department_id'), index=True, nullable=False, default=Department.ID_DEFAULT)
    department = db.relationship('Department', foreign_keys=[department_id])

    departments_part_time_job = db.relationship('Department',
        secondary=db.Table(
            'teacher_department_part_time_job',
            db.Column('teacher_id', db.ForeignKey('teacher.teacher_id')),
            db.Column('department_id', db.ForeignKey('department.department_id'))
        )
    )

    dean_staff = db.Column('teacher_dean_staff', db.BOOLEAN, nullable=False, default=False)
    notify_results_fail = db.Column('teacher_notify_results_fail', db.BOOLEAN, nullable=False, default=False)
    department_leader = db.Column('teacher_department_leader', db.BOOLEAN, nullable=False, default=False)
    department_secretary = db.Column('teacher_department_secretary', db.BOOLEAN, nullable=False, default=False)
    right_read_all = db.Column('teacher_right_read_all', db.BOOLEAN, nullable=False, default=False)

    favorite_students = db.relationship("Student", secondary=db.Table('favorite_teacher_student', db.Model.metadata,
            db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.teacher_id')),
            db.Column('student_id', db.BIGINT, db.ForeignKey('student.student_id'))
        ), lazy=True)

    @property
    def user_rights(self):
        r = {
            "stud_groups": self.department_leader or self.dean_staff or self.right_read_all or self.department_secretary,
        }
        r["persons"] = r["stud_groups"]
        r["rating"] = r["stud_groups"] or (self.department is not None and Department.ID_DEFAULT in (self.department.id, self.department.parent_department_id))
        return r

    @property
    def departments(self):
        return ([self.department] if self.department else []) + list(self.departments_part_time_job)

    @property
    def rank_short(self):
        return {
            'доцент': 'доц.',
            'старший преподаватель': 'ст.преп.',
            'профессор': 'проф.',
            'ассистент': 'асс.',
            'преподаватель': 'преп.'
        }.get(self.rank, self.rank)

    @property
    def role_name(self):
        return 'Teacher'


class CurriculumUnit(db.Model):
    __tablename__ = 'curriculum_unit'
    __table_args__ = (
        db.UniqueConstraint('subject_id', 'stud_group_id'),
        db.UniqueConstraint('curriculum_unit_code', 'stud_group_id')
    )

    id = db.Column('curriculum_unit_id', db.INTEGER, primary_key=True, autoincrement=True)
    code = db.Column('curriculum_unit_code', db.String(16), nullable=False)
    curriculum_unit_group_id = db.Column('curriculum_unit_group_id', db.INTEGER)
    subject_id = db.Column(db.ForeignKey('subject.subject_id'), nullable=False, index=True)
    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id'), nullable=False, index=True)
    teacher_id = db.Column(db.ForeignKey('teacher.teacher_id'), nullable=False, index=True)
    department_id = db.Column(db.ForeignKey('department.department_id'), nullable=False)
    mark_type = db.Column('mark_type', db.Enum(*MarkTypes), nullable=False)
    use_topic = db.Column('use_topic', db.Enum(*TopicTypes), nullable=False, default='none')

    has_simple_mark_test_simple = db.Column('has_simple_mark_test_simple', db.BOOLEAN, nullable=False, default=False)
    has_simple_mark_exam = db.Column('has_simple_mark_exam', db.BOOLEAN, nullable=False, default=False)
    has_simple_mark_test_diff = db.Column('has_simple_mark_test_diff', db.BOOLEAN, nullable=False, default=False)
    has_simple_mark_course_work = db.Column('has_simple_mark_course_work', db.BOOLEAN, nullable=False, default=False)
    has_simple_mark_course_project = db.Column('has_simple_mark_course_project', db.BOOLEAN, nullable=False, default=False)

    hours_att_1 = db.Column('hours_att_1', db.SMALLINT, nullable=False)
    hours_att_2 = db.Column('hours_att_2', db.SMALLINT, nullable=False)
    hours_att_3 = db.Column('hours_att_3', db.SMALLINT, nullable=False)

    hours_lect = db.Column('hours_lect', db.SMALLINT, nullable=False, default=0)
    hours_pract = db.Column('hours_pract', db.SMALLINT, nullable=False, default=0)
    hours_lab = db.Column('hours_lab', db.SMALLINT, nullable=False, default=0)

    moodle_id = db.Column('moodle_id', db.INTEGER)

    subject = db.relationship('Subject')
    department = db.relationship('Department', foreign_keys=[department_id])
    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])

    practice_teachers = db.relationship('Teacher',
        secondary=db.Table('curriculum_unit_practice_teacher',
            db.Column('curriculum_unit_id', db.ForeignKey('curriculum_unit.curriculum_unit_id')),
            db.Column('teacher_id', db.ForeignKey('teacher.teacher_id'))
        )
    )

    allow_edit_practice_teacher_att_mark_1 = db.Column('allow_edit_practice_teacher_att_mark_1', db.BOOLEAN,
                                                       nullable=False, default=False)
    allow_edit_practice_teacher_att_mark_2 = db.Column('allow_edit_practice_teacher_att_mark_2', db.BOOLEAN,
                                                       nullable=False, default=False)
    allow_edit_practice_teacher_att_mark_3 = db.Column('allow_edit_practice_teacher_att_mark_3', db.BOOLEAN,
                                                       nullable=False, default=False)
    allow_edit_practice_teacher_att_mark_exam = db.Column('allow_edit_practice_teacher_att_mark_exam', db.BOOLEAN,
                                                          nullable=False, default=False)
    allow_edit_practice_teacher_att_mark_append_ball = db.Column('allow_edit_practice_teacher_att_mark_append_ball',
                                                                 db.BOOLEAN, nullable=False, default=False)

    allow_edit_practice_teacher_simple_mark_test_simple = db.Column('allow_edit_practice_teacher_simple_mark_test_simple',
                                                                 db.BOOLEAN, nullable=False, default=False)

    allow_edit_practice_teacher_simple_mark_exam = db.Column('allow_edit_practice_teacher_simple_mark_exam', db.BOOLEAN, nullable=False, default=False)
    allow_edit_practice_teacher_simple_mark_test_diff = db.Column('allow_edit_practice_teacher_simple_mark_test_diff', db.BOOLEAN, nullable=False, default=False)
    allow_edit_practice_teacher_simple_mark_course_work = db.Column('allow_edit_practice_teacher_simple_mark_course_work', db.BOOLEAN, nullable=False, default=False)
    allow_edit_practice_teacher_simple_mark_course_project = db.Column('allow_edit_practice_teacher_simple_mark_course_project', db.BOOLEAN, nullable=False, default=False)

    pass_department = db.Column('pass_department', db.BOOLEAN, nullable=False, default=False)
    closed = db.Column('closed', db.BOOLEAN, nullable=False, default=False)

    att_marks = db.relationship('AttMark', lazy=True, backref='curriculum_unit')
    status_history = db.relationship('CurriculumUnitStatusHist', lazy=True, backref='curriculum_unit',
                                     order_by="CurriculumUnitStatusHist.stime.desc()")

    lessons_curriculum_unit = db.relationship('LessonCurriculumUnit',
                                              lazy=True,
                                              primaryjoin='LessonCurriculumUnit.curriculum_unit_id == CurriculumUnit.id',
                                              backref='curriculum_unit')

    exams = db.relationship('Exam', lazy=True, backref='curriculum_unit')
    scheduled_lessons = db.relationship('ScheduledLesson', lazy=True, backref='curriculum_unit')
    scheduled_lessons_draft = db.relationship('ScheduledLessonDraft', lazy=True, backref='curriculum_unit')

    journalize_attributes = ('allow_edit_practice_teacher_att_mark_1',
                             'allow_edit_practice_teacher_att_mark_2', 'allow_edit_practice_teacher_att_mark_3',
                             'allow_edit_practice_teacher_att_mark_exam',
                             'allow_edit_practice_teacher_att_mark_append_ball',
                             'allow_edit_practice_teacher_simple_mark_test_simple',
                             'allow_edit_practice_teacher_simple_mark_exam',
                             'allow_edit_practice_teacher_simple_mark_test_diff',
                             'allow_edit_practice_teacher_simple_mark_course_work',
                             'allow_edit_practice_teacher_simple_mark_course_project',
                             'hours_att_1', 'hours_att_2', 'hours_att_3', 'pass_department', 'closed')

    journalize_relations = ('practice_teachers',)

    @property
    def visible_attrs_4_report(self):
        attrs = tuple()
        if self.mark_type != "no_att":
            if self.hours_att_1 > 0:
                attrs += ("att_mark_1",)
            if self.hours_att_2 > 0:
                attrs += ("att_mark_2",)
            if self.hours_att_3 > 0:
                attrs += ("att_mark_3",)
            if self.mark_type == "exam":
                attrs += ("att_mark_exam",)
            if self.mark_type in ("exam", "test_diff"):
                attrs += ("att_mark_append_ball",)

        if self.has_simple_mark_test_simple:
            attrs += ("simple_mark_test_simple",)
        if self.has_simple_mark_exam:
            attrs += ("simple_mark_exam",)
        if self.has_simple_mark_test_diff:
            attrs += ("simple_mark_test_diff",)
        if self.has_simple_mark_course_work:
            attrs += ("simple_mark_course_work",)
        if self.has_simple_mark_course_project:
            attrs += ("simple_mark_course_project",)
        return attrs

    @property
    def visible_attrs(self):
        attrs = self.visible_attrs_4_report
        if self.use_topic == 'coursework':
            attrs += ("theme", "teacher")
        if self.use_topic == 'project_seminar':
            attrs += ("theme",)
        return attrs


    @property
    def visible_ball_average(self):
        return self.mark_type in ('exam', 'test_diff', 'no_mark')

    @property
    def mark_type_name(self):
        return MarkTypeDict[self.mark_type]

    @property
    def mark_types_name(self):
        s = [MarkTypeDict[self.mark_type]] if self.mark_type != "no_att" else []

        if self.has_simple_mark_test_simple:
            s.append("Зачет")
        if self.has_simple_mark_exam:
            s.append("Экзамен")
        if self.has_simple_mark_test_diff:
            s.append("Дифференцированный зачет")
        if self.has_simple_mark_course_work:
            s.append("Курсовая работа")
        if self.has_simple_mark_course_project:
            s.append("Курсовой проект")
        return ", ".join(s)

    @property
    def mark_types(self):
        t = [self.mark_type] if self.mark_type != "no_att" else []
        if self.has_simple_mark_test_simple and self.mark_type != "test_simple":
            t.append("test_simple")
        if self.has_simple_mark_exam and self.mark_type != "exam":
            t.append("exam")
        if self.has_simple_mark_test_diff and self.mark_type != "test_diff":
            t.append("test_diff")
        if self.has_simple_mark_course_work:
            t.append("course_work")
        if self.has_simple_mark_course_project:
            t.append("course_project")
        return t

    @property
    def hours(self):
        attrs = ('hours_att_1', 'hours_att_2', 'hours_att_3')
        if any(getattr(self, a) is None for a in attrs):
            return None
        return tuple(getattr(self, a) for a in attrs if getattr(self, a) > 0)

    @property
    def hours_sum(self):
        if self.hours is None:
            return None
        return sum(self.hours)

    @property
    def hours_lab_per_week(self):
        if self.stud_group.weeks_training == 0:
            return 0
        return round(self.hours_lab / self.stud_group.weeks_training)

    @property
    def hours_lect_per_week(self):
        if self.stud_group.weeks_training == 0:
            return 0
        return round(self.hours_lect / self.stud_group.weeks_training)

    @property
    def hours_pract_per_week(self):
        if self.stud_group.weeks_training == 0:
            return 0
        return round(self.hours_pract / self.stud_group.weeks_training)


    @property
    def status(self):
        if self.closed:
            return 'closed'
        att_marks_readonly_ids = self.att_marks_readonly_ids
        _status = 'empty'
        if next((m for m in self.att_marks if m.att_mark_id not in att_marks_readonly_ids), None) is None:
            return _status

        if self.mark_type != "no_att":
            _attr_status = {
                "att_mark_1": 'att_1',
                "att_mark_2": 'att_2',
                "att_mark_3": 'att_3',
                "att_mark_exam": 'exam'
            }

            for a in self.visible_attrs:
                if a not in _attr_status:
                    continue
                _status = _attr_status[a]
                if any((getattr(m, a) is None for m in self.att_marks if m.att_mark_id not in att_marks_readonly_ids)):
                    return _status

        for _a in MarkSimpleTypes:
            a_has = 'has_simple_mark_' + _a
            a = 'simple_mark_' + _a
            if getattr(self, a_has):
                if any((getattr(m, a) is None for m in self.att_marks if
                        m.att_mark_id not in att_marks_readonly_ids)):
                    return _status

        return 'filled'

    @property
    def status_name(self):
        return DocStatusDict[self.status]

    @property
    def att_marks_readonly_ids(self):
        if self.closed:
            return tuple(m.att_mark_id for m in self.att_marks if m.exclude)
        else:
            return tuple(
                    m.att_mark_id for m in self.att_marks if
                    not m.manual_add and m.student.stud_group_id != m.curriculum_unit.stud_group_id or m.exclude == 2)

    @property
    def subject_name_print(self):
        if self.code is not None and self.subject is not None and self.subject.name is not None:
            return "%s (%s)" % (self.subject.name, self.code)

    def get_rights(self, person):
        # Проверка прав доступа
        r = {
            "read": False,
            "write": False,
            "pass_department": False,
            "mark_comment_hidden": False,
            "close": False,
            "open": False
        }
        for u in person.roles:
            if u.role_name == 'AdminUser':
                r["read"] = True
                r["mark_comment_hidden"] = True
                r["write"] = not self.closed
                r["pass_department"] = (self.status == 'filled')
                r["close"] = (not self.closed) and self.pass_department
                r["open"] = self.closed
                break

            if u.role_name == "Teacher":
                if u.id == self.teacher_id or any(u.id == t.id for t in self.practice_teachers):
                    r["read"] = True
                    r["mark_comment_hidden"] = True
                    r["write"] = (not self.pass_department) and (not self.closed)

                if u.dean_staff or u.department_leader or u.right_read_all or u.department_secretary:
                    r["read"] = True

                if u.department_secretary and self.department_id in [d.id for d in u.departments]:
                    r["pass_department"] = (self.status == 'filled')

        # запрет для редактирования оценок для неактивной студенческой группы
        if r["read"] and not self.stud_group.active:
            for k, v in r.items():
                if k not in ('read', 'mark_comment_hidden') and v:
                    r[k] = False
        return r

    # процент неудовлетворительных оценок
    @property
    def result_failed(self):
        k = 0
        s = 0
        for m in self.att_marks:
            if m.att_mark_id not in self.att_marks_readonly_ids:
                s += 1
                fail = False
                for mark_type in self.mark_types:
                    _m: AttMarkSimple = m.get_simple_att_mark(mark_type)
                    if _m is None or _m.ball_value is None:
                        return None
                    if _m.ball_value in (False, 0, 2):
                        fail = True
                if fail:
                    k += 1
        if s == 0:
            return None
        return round((k * 100) / s, 2)

    # Версия подсчёта баллов
    @property
    def calc_version(self):
        year = None
        semester = None
        if self.stud_group:
            year = self.stud_group.year
            semester = 1 if self.stud_group.semester % 2 == 1 else 2

        if year is not None and semester is not None:
            if year <= 2020:
                return 1
            if year == 2021 and semester == 1:
                return 1

            if year == 2021 and semester == 2:
                return 2
            if year == 2022:
                return 2
            if year == 2023 and semester == 1:
                return 2

            return 3

        return None

    @property
    def calc_attendance(self):
        return self.calc_version >= 3

    @property
    def file_name(self):
        return "Аттестационная_ведомость_%d_к_%s_гр_%s_%s.odt" % (
            self.stud_group.course,
            str(self.stud_group.num),
            self.subject_name_print.replace("(", "").replace(")", "").replace(" ", "_"),
            self.status_name.replace(" ", "_")
        )

    def file_name_mark_type_format(self, mark_type):
        return "Аттестационная_ведомость_%d_к_%s_гр_%s_%s.odt" % (
            self.stud_group.course,
            str(self.stud_group.num),
            self.subject_name_print.replace("(", "").replace(")", "").replace(" ", "_"),
            MarkSimpleTypeDict.get(mark_type, "").replace(" ", "_")
        )

    @property
    def count_lessons(self):
        result = 0

        for lcu in self.lessons_curriculum_unit:
            if self.stud_group.sub_count == 0:
                result += 1
            else:
                result += sum(map(int, lcu.stud_group_subnums_map[1:]))

        if self.stud_group.sub_count > 0:
            if result % self.stud_group.sub_count > 0:
                result = round(result / self.stud_group.sub_count, 1)
            else:
                result = result // self.stud_group.sub_count

        return result


_curriculum_unit_practice_teacher_hist = db.Table('curriculum_unit_practice_teacher_hist',
                db.Column('curriculum_unit_id', db.ForeignKey('curriculum_unit_status_hist.curriculum_unit_id'), primary_key=True),
                db.Column('stime', db.ForeignKey('curriculum_unit_status_hist.stime'), primary_key=True),
                db.Column('teacher_id', db.ForeignKey('teacher.teacher_id'), primary_key=True)
            )


class CurriculumUnitStatusHist(db.Model):
    __tablename__ = 'curriculum_unit_status_hist'
    curriculum_unit_id = db.Column(
        db.ForeignKey('curriculum_unit.curriculum_unit_id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
    stime = db.Column(db.DateTime, primary_key=True)
    etime = db.Column(db.DateTime)

    changed_person_id = db.Column(db.ForeignKey('person.person_id'))
    user = db.relationship('Person')

    allow_edit_practice_teacher_att_mark_1 = db.Column('allow_edit_practice_teacher_att_mark_1', db.BOOLEAN,
                                                       nullable=False, default=False)
    allow_edit_practice_teacher_att_mark_2 = db.Column('allow_edit_practice_teacher_att_mark_2', db.BOOLEAN,
                                                       nullable=False, default=False)
    allow_edit_practice_teacher_att_mark_3 = db.Column('allow_edit_practice_teacher_att_mark_3', db.BOOLEAN,
                                                       nullable=False, default=False)
    allow_edit_practice_teacher_att_mark_exam = db.Column('allow_edit_practice_teacher_att_mark_exam', db.BOOLEAN,
                                                          nullable=False, default=False)
    allow_edit_practice_teacher_att_mark_append_ball = db.Column('allow_edit_practice_teacher_att_mark_append_ball',
                                                                 db.BOOLEAN,
                                                                 nullable=False, default=False)

    allow_edit_practice_teacher_simple_mark_test_simple = db.Column('allow_edit_practice_teacher_simple_mark_test_simple', db.BOOLEAN,
                                                             nullable=False, default=False)
    allow_edit_practice_teacher_simple_mark_exam = db.Column('allow_edit_practice_teacher_simple_mark_exam', db.BOOLEAN,
                                                             nullable=False, default=False)
    allow_edit_practice_teacher_simple_mark_test_diff = db.Column('allow_edit_practice_teacher_simple_mark_test_diff',
                                                                  db.BOOLEAN, nullable=False, default=False)
    allow_edit_practice_teacher_simple_mark_course_work = db.Column(
        'allow_edit_practice_teacher_simple_mark_course_work', db.BOOLEAN, nullable=False, default=False)
    allow_edit_practice_teacher_simple_mark_course_project = db.Column(
        'allow_edit_practice_teacher_simple_mark_course_project', db.BOOLEAN, nullable=False, default=False)

    hours_att_1 = db.Column('hours_att_1', db.SMALLINT, nullable=False)
    hours_att_2 = db.Column('hours_att_2', db.SMALLINT, nullable=False)
    hours_att_3 = db.Column('hours_att_3', db.SMALLINT, nullable=False)
    pass_department = db.Column('pass_department', db.BOOLEAN, nullable=False, default=False)
    closed = db.Column('closed', db.BOOLEAN, nullable=False, default=False)

    practice_teachers = db.relationship('Teacher',
            secondary=_curriculum_unit_practice_teacher_hist,
            primaryjoin=and_(
                curriculum_unit_id == _curriculum_unit_practice_teacher_hist.c.curriculum_unit_id,
                stime == _curriculum_unit_practice_teacher_hist.c.stime
            ),
            secondaryjoin=Teacher.id == _curriculum_unit_practice_teacher_hist.c.teacher_id,
            lazy=True
    )

    doc = deferred(db.Column('curriculum_unit_doc', db.LargeBinary))

    doc_test_simple = deferred(db.Column('curriculum_unit_doc_test_simple', db.LargeBinary))
    doc_exam = deferred(db.Column('curriculum_unit_doc_exam', db.LargeBinary))
    doc_test_diff = deferred(db.Column('curriculum_unit_doc_test_diff', db.LargeBinary))
    doc_course_work = deferred(db.Column('curriculum_unit_doc_course_work', db.LargeBinary))
    doc_course_project = deferred(db.Column('curriculum_unit_doc_course_project', db.LargeBinary))


CurriculumUnit.journalize_class = CurriculumUnitStatusHist


class AdminUser(db.Model, _Person):
    __tablename__ = 'admin_user'

    id = db.Column('admin_user_id', db.BIGINT, primary_key=True, autoincrement=True)
    person_id = db.Column(db.ForeignKey('person.person_id'))
    active = db.Column('admin_user_active', db.BOOLEAN, nullable=False, default=True)


    @property
    def user_rights(self):
        return {
            "stud_groups": True,
            "rating": True,
            "persons": True,
        }

    @property
    def role_name(self):
        return 'AdminUser'


MARK_RESULT_ATT_MIN_BALL = 25

MarkResult = {
    "test_simple": (
        {"min": 0, "max": 49, "value": False, "value_text": "не зачтено", "value_text_short": "н.з."},
        {"min": 50, "max": 100, "value": True, "value_text": "зачтено", "value_text_short": "зач"}
    ),
    "exam": (
        {"min": 0, "max": 49, "value": 2, "value_text": "неудовл.", "value_text_short": "2"},
        {"min": 50, "max": 69, "value": 3, "value_text": "удовл.", "value_text_short": "3"},
        {"min": 70, "max": 89, "value": 4, "value_text": "хорошо", "value_text_short": "4"},
        {"min": 90, "max": 100, "value": 5, "value_text": "отлично", "value_text_short": "5"}
    ),
    "test_diff": (
        {"min": 0, "max": 49, "value": 2, "value_text": "неудовл.", "value_text_short": "2"},
        {"min": 50, "max": 69, "value": 3, "value_text": "удовл.", "value_text_short": "3"},
        {"min": 70, "max": 89, "value": 4, "value_text": "хорошо", "value_text_short": "4"},
        {"min": 90, "max": 100, "value": 5, "value_text": "отлично", "value_text_short": "5"}
    )
}


class LessonStudent(db.Model):
    __tablename__ = 'lesson_student'
    lesson_id = db.Column(db.ForeignKey('lesson_curriculum_unit.lesson_id', ondelete='CASCADE'), primary_key=True)
    curriculum_unit_id = db.Column(db.ForeignKey('curriculum_unit.curriculum_unit_id'), primary_key=True)

    student_id = db.Column(db.ForeignKey('student.student_id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
    student = db.relationship('Student', foreign_keys=[student_id])
    # 0 - Отсутствовал; 1 - Присутствовал; 2 - Отсутствовал по уважительной причине
    attendance = db.Column('attendance', db.SMALLINT)
    comment = db.Column('lesson_student_comment', db.String(4000))
    comment_hidden = db.Column('lesson_student_comment_hidden', db.String(4000))

    @property
    def attendance_str(self):
        if self.attendance == 0:
            return 'н'
        if self.attendance == 1:
            return '+'
        if self.attendance == 2:
            return 'У'

    @property
    def attendance_str_comment(self):
        if self.attendance == 0:
            return 'отсутствовала' if self.student.person.gender == 'W' else 'отсутствовал'
        if self.attendance == 1:
            return 'присутствовала' if self.student.person.gender == 'W' else 'присутствовал'
        if self.attendance == 2:
            return '%s по уважительной причине' % ('отсутствовала' if self.student.person.gender == 'W' else 'отсутствовал')


class AttMarkSimple:

    def __init__(self, mark_type, m):
        self.mark_type = mark_type
        self.att_mark_id = m.att_mark_id
        self.curriculum_unit = m.curriculum_unit
        self.student = m.student
        self.exclude = m.exclude
        if not self.exclude and self.curriculum_unit and not self.curriculum_unit.closed and self.att_mark_id in self.curriculum_unit.att_marks_readonly_ids:
            self.exclude = 1

        self.ball_value = None
        self.ball_simple_value = None
        self.ball_print_short = None
        self.ball_print = None
        # return ball, {"value": 0, "value_text": "неявка", "value_text_short": "н.я."}

        if self.mark_type == "test_simple":
            if self.curriculum_unit.mark_type == "test_simple":
                r = m.result_print
                if r:
                    self.ball_value, self.ball_print, self.ball_print_short = r[1]["value"], r[1]["value_text"], r[1]["value_text_short"]
            elif self.curriculum_unit.has_simple_mark_test_simple:
                if m.simple_mark_test_simple == 0:
                    self.ball_value, self.ball_print, self.ball_print_short = 0, "неявка", "н.я."
                if m.simple_mark_test_simple == 2:
                    self.ball_value, self.ball_print, self.ball_print_short = False, "не зачтено", "н.з."
                if m.simple_mark_test_simple == 5:
                    self.ball_value, self.ball_print, self.ball_print_short = True, "зачтено", "зач"
        else:
            r = None
            simple_mark = None
            if self.mark_type == "exam":
                if self.curriculum_unit.mark_type == "exam":
                    r = m.result_print
                elif self.curriculum_unit.has_simple_mark_exam:
                    simple_mark = m.simple_mark_exam

            if self.mark_type == "test_diff":
                if self.curriculum_unit.mark_type == "test_diff":
                    r = m.result_print
                elif self.curriculum_unit.has_simple_mark_test_diff:
                    simple_mark = m.simple_mark_test_diff

            if self.mark_type == "course_work" and self.curriculum_unit.has_simple_mark_course_work:
                simple_mark = m.simple_mark_course_work

            if self.mark_type == "course_project" and self.curriculum_unit.has_simple_mark_course_project:
                simple_mark = m.simple_mark_course_project

            if r is not None:
                self.ball_value, self.ball_print, self.ball_print_short = r[1]["value"], r[1]["value_text"], r[1]["value_text_short"]
            elif simple_mark is not None:
                self.ball_value = simple_mark
                self.ball_print, self.ball_print_short = {
                    0: ("неявка", "н.я."),
                    2: ("неудовл.", "2"),
                    3: ("удовл.", "3"),
                    4: ("хорошо", "4"),
                    5: ("отлично", "5")
                }.get(simple_mark, (None, None))

        if isinstance(self.ball_value, bool):
            self.ball_simple_value = 5 if self.ball_value else 2
        else:
            self.ball_simple_value = self.ball_value


class AttMark(db.Model):
    __tablename__ = 'att_mark'
    __table_args__ = (
        db.UniqueConstraint('curriculum_unit_id', 'student_id'),
    )

    att_mark_id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    curriculum_unit_id = db.Column(db.ForeignKey('curriculum_unit.curriculum_unit_id'), nullable=False)
    student_id = db.Column(db.ForeignKey('student.student_id', onupdate='CASCADE'), nullable=False, index=True)
    att_mark_1 = db.Column(db.SMALLINT)
    att_mark_2 = db.Column(db.SMALLINT)
    att_mark_3 = db.Column(db.SMALLINT)
    att_mark_exam = db.Column(db.SMALLINT)
    att_mark_append_ball = db.Column(db.SMALLINT)

    theme = db.Column('work_theme', db.String(1000))
    teacher_id = db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.teacher_id'))

    simple_mark_test_simple = db.Column(db.SMALLINT)
    simple_mark_exam = db.Column(db.SMALLINT)
    simple_mark_test_diff = db.Column(db.SMALLINT)
    simple_mark_course_work = db.Column(db.SMALLINT)
    simple_mark_course_project = db.Column(db.SMALLINT)


    attendance_rate_cached = db.Column(db.Numeric(5, 4, asdecimal=False))
    # 1 - при отчислении студнта; 2 - перезачтено
    exclude = db.Column('att_mark_exclude', db.SMALLINT)
    comment = db.Column('att_mark_comment', db.String(4000))
    comment_hidden = db.Column('att_mark_comment_hidden', db.String(4000))

    teacher = db.relationship('Teacher')
    student = db.relationship('Student')

    manual_add = db.Column('att_mark_manual_add', db.BOOLEAN, nullable=False, default=False)
    group_subnum = db.Column('att_mark_group_subnum', db.SMALLINT)

    history = db.relationship('AttMarkHist', lazy=True, backref='att_mark', order_by="AttMarkHist.stime.desc()")
    lessons_student = db.relationship('LessonStudent', lazy=True, uselist=True,
                                    foreign_keys=[student_id, curriculum_unit_id],
                                    primaryjoin=and_(student_id == LessonStudent.student_id, curriculum_unit_id == LessonStudent.curriculum_unit_id),
                                    overlaps="att_marks,student,curriculum_unit"
    )

    @property
    def attendance_rate_raw(self):
        cnt_all = sum((1 for ls in self.lessons_student if ls.attendance is not None))
        if cnt_all == 0:
            return None
        cnt = sum((1 for ls in self.lessons_student if ls.attendance))
        if cnt == cnt_all:
            return 1
        if cnt == 0:
            return 0
        return round(cnt / cnt_all, 4)

    @property
    def attendance_rate(self):
        if self.curriculum_unit:
            return self.attendance_rate_raw if not self.curriculum_unit.closed else self.attendance_rate_cached

    @property
    def attendance_pct(self):
        attendance_rate = self.attendance_rate
        if attendance_rate is not None:
            pct = attendance_rate*100
            if not isinstance(pct, int):
                pct = round(pct, 2)
                if pct - int(pct) == 0:
                    pct = int(pct)
            return pct

    @property
    def att_marks(self):
        marks = []
        if self.curriculum_unit.hours_att_1 > 0:
            marks.append(self.att_mark_1)
        if self.curriculum_unit.hours_att_2 > 0:
            marks.append(self.att_mark_2)
        if self.curriculum_unit.hours_att_3 > 0:
            marks.append(self.att_mark_3)
        return marks

    @property
    def is_success_ball_att_marks(self):
        att_marks = self.att_marks
        if any(m is None for m in att_marks):
            return None

        return all(m >= MARK_RESULT_ATT_MIN_BALL for m in att_marks)

    @property
    def is_available_att_mark_append_ball(self):
        if self.curriculum_unit.mark_type not in ("exam", "test_diff"):
            return False
        if any(m is None for m in self.att_marks):
            return True

        if self.curriculum_unit.mark_type == "exam":
            if self.curriculum_unit.calc_version == 1:
                return True
            if self.curriculum_unit.calc_version >= 2:
                return self.att_mark_exam is None or self.att_mark_exam >= MARK_RESULT_ATT_MIN_BALL

        if self.curriculum_unit.mark_type == "test_diff":
            return self.is_success_ball_att_marks

    @property
    def ball_average_raw(self):
        if self.curriculum_unit.mark_type == "no_att":
            return None
        att_marks = self.att_marks
        if any(m is None for m in att_marks):
            return None

        if self.curriculum_unit.mark_type in ("test_simple", "test_diff") and not self.is_success_ball_att_marks:
            return min(att_marks)

        hours = self.curriculum_unit.hours
        return sum([att_marks[i] * hours[i] for i in range(len(att_marks))]) / sum(hours)

    @property
    def ball_attendance_add(self):
        if not self.curriculum_unit.calc_attendance:
            return None

        if self.attendance_rate is None:
            return None
        r = -10 * (1 - self.attendance_rate)
        if not isinstance(r, int):
            r = round(r, 2)
            if r - int(r) == 0:
                r = int(r)
        return max(-5, r)

    @property
    def ball_average_without_attendance(self):
        ball_raw = self.ball_average_raw
        if ball_raw is None:
            return None
        # Округление
        ball = int(ball_raw)
        if ball_raw - ball >= 0.5:
            ball += 1

        if self.curriculum_unit.mark_type in ("test_simple", "test_diff"):
            ball *= 2
        return ball

    @property
    def ball_average_with_attendance(self):
        if not self.curriculum_unit.calc_attendance:
            return self.ball_average_without_attendance

        ball_raw = self.ball_average_raw
        if ball_raw is None:
            return None

        attendance_rate = self.attendance_rate
        if attendance_rate is None:
            return self.ball_average_without_attendance

        ball_raw += self.ball_attendance_add
        # Округление
        ball = int(ball_raw)
        if ball_raw - ball >= 0.5:
            ball += 1

        if ball < 0:
            ball = 0

        if self.curriculum_unit.mark_type in ("test_simple", "test_diff"):
            ball *= 2
        return ball


    @property
    def ball_average(self):
        if self.curriculum_unit.mark_type == "no_att":
            return None
        return self.ball_average_with_attendance if self.curriculum_unit.calc_attendance else self.ball_average_without_attendance

    @property
    def result_print(self):
        if self.curriculum_unit.mark_type in ("no_mark", "no_att"):
            return None

        ball = self.ball_average

        if ball is None:
            return None

        if self.curriculum_unit.mark_type == "exam" and self.att_mark_exam is None:
            return None

        mark_results = MarkResult[self.curriculum_unit.mark_type]
        max_ball = mark_results[-1]["max"]

        if self.curriculum_unit.mark_type == "exam":
            if self.curriculum_unit.calc_version == 1:
                ball += self.att_mark_exam

            if self.curriculum_unit.calc_version >= 2:
                if self.att_mark_exam >= MARK_RESULT_ATT_MIN_BALL:
                    ball += self.att_mark_exam
                else:
                    ball = min(self.att_mark_exam * 2, self.ball_average)

        if self.att_mark_append_ball is not None and self.is_available_att_mark_append_ball:
            ball += self.att_mark_append_ball

        if ball > max_ball:
            ball = max_ball

        last_att_attr = "att_mark_3"
        if "att_mark_3" not in self.curriculum_unit.visible_attrs:
            last_att_attr = "att_mark_2"
        if "att_mark_2" not in self.curriculum_unit.visible_attrs:
            last_att_attr = "att_mark_1"

        for i, mr in enumerate(mark_results):
            if mr["min"] <= ball <= mr["max"]:
                # Фиксирование неявки
                if i == 0 and (
                        (self.curriculum_unit.mark_type in ("test_simple", "test_diff") and getattr(self, last_att_attr) == 0) or
                        (self.curriculum_unit.mark_type == "exam" and self.att_mark_exam == 0)):
                    return ball, {"value": 0, "value_text": "неявка", "value_text_short": "н.я."}

                return ball, mr

    # Проверка на возможность редактирования атрибута
    def check_edit_attr(self, attr, person: Person):
        if self.curriculum_unit.closed or self.curriculum_unit.pass_department:
            return False

        if self.att_mark_id in self.curriculum_unit.att_marks_readonly_ids:
            return False

        if attr not in self.curriculum_unit.visible_attrs:
            return False

        if attr == "att_mark_append_ball" and not self.is_available_att_mark_append_ball:
            return False

        if person.admin_user is not None and person.admin_user.active:
            return True

        if person.teacher is not None:
            if person.teacher.id != self.curriculum_unit.teacher_id and not any(
                    t.id == person.teacher.id for t in self.curriculum_unit.practice_teachers):
                return False

            if person.teacher.id == self.curriculum_unit.teacher_id:
                return True

            if attr == "att_mark_1" and not self.curriculum_unit.allow_edit_practice_teacher_att_mark_1:
                return False
            if attr == "att_mark_2" and not self.curriculum_unit.allow_edit_practice_teacher_att_mark_2:
                return False
            if attr == "att_mark_3" and not self.curriculum_unit.allow_edit_practice_teacher_att_mark_3:
                return False
            if attr == "att_mark_exam" and not self.curriculum_unit.allow_edit_practice_teacher_att_mark_exam:
                return False
            if attr == "att_mark_append_ball" and not self.curriculum_unit.allow_edit_practice_teacher_att_mark_append_ball:
                return False
            if attr == "simple_mark_test_simple" and not self.curriculum_unit.allow_edit_practice_teacher_simple_mark_test_simple:
                return False
            if attr == "simple_mark_exam" and not self.curriculum_unit.allow_edit_practice_teacher_simple_mark_exam:
                return False
            if attr == "simple_mark_test_diff" and not self.curriculum_unit.allow_edit_practice_teacher_simple_mark_test_diff:
                return False
            if attr == "simple_mark_course_work" and not self.curriculum_unit.allow_edit_practice_teacher_simple_mark_course_work:
                return False
            if attr == "simple_mark_course_project" and not self.curriculum_unit.allow_edit_practice_teacher_simple_mark_course_project:
                return False
            if attr == "theme" and self.teacher_id != person.teacher.id:
                return False
            if attr == "teacher" and self.teacher_id is not None:
                return False

            return True

        return False


    @property
    def doc_attrs(self):
        doc_attrs = {
            "att_mark_1": "-",
            "att_mark_2": "-",
            "att_mark_3": "-",
            "att_mark_exam": "-",
            "att_mark_append_ball": "-"
        }

        for a, v in doc_attrs.items():
            if a not in self.curriculum_unit.visible_attrs:
                continue
            if a == "att_mark_append_ball" and not self.is_available_att_mark_append_ball:
                continue

            doc_attrs[a] = getattr(self, a)

        doc_attrs["ball_attendance"] = self.ball_attendance_add if self.ball_attendance_add is not None else '-'
        ball_average = self.ball_average
        doc_attrs["ball_average"] = ball_average if ball_average is not None else ""
        doc_attrs["ball_100"] = ""
        doc_attrs["ball_print"] = ""
        if self.result_print:
            doc_attrs["ball_100"], doc_attrs["ball_print"] = self.result_print
            doc_attrs["ball_print"] = doc_attrs["ball_print"]["value_text"]

        return doc_attrs

    def get_simple_att_mark(self, mark_type):
        if mark_type != self.curriculum_unit.mark_type and not getattr(self.curriculum_unit, "has_simple_mark_%s" % mark_type, False):
            return None
        return AttMarkSimple(mark_type, self)

    @property
    def journalize_attributes(self):
        return self.curriculum_unit.visible_attrs


class AttMarkHist(db.Model):
    __tablename__ = 'att_mark_hist'
    att_mark_id = db.Column(db.ForeignKey('att_mark.att_mark_id', ondelete='CASCADE', onupdate='CASCADE'),
                            nullable=False)
    stime = db.Column(db.DateTime, nullable=False)
    etime = db.Column(db.DateTime)

    changed_person_id = db.Column(db.ForeignKey('person.person_id'))
    user = db.relationship('Person')

    att_mark_1 = db.Column(db.SMALLINT)
    att_mark_2 = db.Column(db.SMALLINT)
    att_mark_3 = db.Column(db.SMALLINT)
    att_mark_exam = db.Column(db.SMALLINT)
    att_mark_append_ball = db.Column(db.SMALLINT)

    theme = db.Column('work_theme', db.String(1000))
    teacher_id = db.Column('teacher_id', db.Integer, db.ForeignKey('teacher.teacher_id'))
    teacher = db.relationship('Teacher')

    simple_mark_test_simple = db.Column(db.SMALLINT)
    simple_mark_exam = db.Column(db.SMALLINT)
    simple_mark_test_diff = db.Column(db.SMALLINT)
    simple_mark_course_work = db.Column(db.SMALLINT)
    simple_mark_course_project = db.Column(db.SMALLINT)

    __table_args__ = (
        db.PrimaryKeyConstraint('att_mark_id', 'stime'),
    )


AttMark.journalize_class = AttMarkHist


class LessonCurriculumUnit(db.Model, _ObjectWithStudGroupSubnumsMap):
    __tablename__ = 'lesson_curriculum_unit'
    lesson_id = db.Column(db.ForeignKey('lesson.lesson_id', ondelete='CASCADE'), primary_key=True)
    curriculum_unit_id = db.Column(db.ForeignKey('curriculum_unit.curriculum_unit_id'), primary_key=True)

    stud_group_subnums = db.Column('stud_group_subnums', db.SMALLINT, nullable=False, default=0)

    # curriculum_unit = db.relationship('CurriculumUnit', foreign_keys=[curriculum_unit_id])

    lesson_students = db.relationship('LessonStudent', lazy=True,
                                backref='lesson_curriculum_unit',
                                primaryjoin=and_(lesson_id == LessonStudent.lesson_id, curriculum_unit_id == LessonStudent.curriculum_unit_id))

    @property
    def attendance_rate(self):
        cnt_all = sum((1 for ls in self.lesson_students if ls.attendance is not None))
        if cnt_all == 0:
            return None
        cnt = sum((1 for ls in self.lesson_students if ls.attendance))
        return 1 if cnt == cnt_all else round(cnt / cnt_all, 4)

    @property
    def attendance_pct(self):
        attendance_rate = self.attendance_rate
        if attendance_rate is not None:
            pct = attendance_rate * 100
            if isinstance(pct, int):
                return pct
            return int(pct) if pct - int(pct) == 0 else round(pct, 2)


class Lesson(db.Model):
    __tablename__ = 'lesson'
    id = db.Column('lesson_id', db.BIGINT, primary_key=True, autoincrement=True)
    teacher_id = db.Column(db.ForeignKey('teacher.teacher_id'), nullable=False, index=True)
    date = db.Column('lesson_date', db.Date, nullable=False)
    lesson_num = db.Column(db.ForeignKey('lesson_time.lesson_num'), nullable=False, index=True)
    type = db.Column('lesson_type', db.Enum(*LessonTypes), nullable=False, default='seminar')
    form = db.Column('lesson_form', db.Enum(*LessonForms), nullable=False, default='in_class')
    comment = db.Column('lesson_comment', db.String(4000))
    comment_hidden = db.Column('lesson_comment_hidden', db.String(4000))

    student_mark_active = db.Column('lesson_student_mark_active', db.BOOLEAN, nullable=False, default=False)

    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])
    time = db.relationship('LessonTime', foreign_keys=[lesson_num])

    lesson_curriculum_units = db.relationship('LessonCurriculumUnit', lazy=True,
                               backref='lesson',
                               foreign_keys=[LessonCurriculumUnit.lesson_id])

    def get_rights(self, person):
        r = {
            "read": False,
            "write": False,
            "comment_hidden": False
        }

        for u in person.roles:
            if u.role_name == 'AdminUser':
                r["read"] = True
                r["write"] = True
                r["comment_hidden"] = True

            if u.role_name == 'Teacher':
                if u.id == self.teacher_id or u.id in (lcu.curriculum_unit.teacher_id for lcu in self.lesson_curriculum_units):
                    r["read"] = True
                    r["write"] = True
                    r["comment_hidden"] = True
                elif any((u.id in (lcu.curriculum_unit.teacher_id,)+tuple((t.id for t in lcu.curriculum_unit.practice_teachers)) for lcu in self.lesson_curriculum_units)):
                    r["read"] = True
                    r["comment_hidden"] = True

        if not r["read"]:
            if any((lcu.curriculum_unit.stud_group.get_rights(person)["read_marks"] for lcu in self.lesson_curriculum_units)):
                r["read"] = True

        if r["write"]:
            for lcu in self.lesson_curriculum_units:
                cu: CurriculumUnit = lcu.curriculum_unit
                sg: StudGroup = cu.stud_group
                if cu.closed or cu.pass_department or (not sg.active):
                    r["write"] = False
                    break
        return r


class Exam(db.Model, _ObjectWithStudGroupSubnumsMap):
    __tablename__ = 'exam'
    id = db.Column('exam_id', db.INTEGER, primary_key=True, autoincrement=True)
    curriculum_unit_id = db.Column(db.ForeignKey('curriculum_unit.curriculum_unit_id'), nullable=False)
    stud_group_subnums = db.Column('stud_group_subnums', db.SMALLINT, nullable=False, default=0)
    stime = db.Column('exam_stime', db.DateTime, nullable=False)
    etime = db.Column('exam_etime', db.DateTime, nullable=False)

    teacher_id = db.Column(db.ForeignKey('teacher.teacher_id'))
    teacher = db.relationship('Teacher', foreign_keys=[teacher_id])

    classroom = db.Column(db.ForeignKey('classroom.classroom'))

    comment = db.Column('exam_comment', db.String(4000))

    # curriculum_unit = db.relationship('CurriculumUnit', foreign_keys=[curriculum_unit_id])


class LessonTime(db.Model):
    __tablename__ = 'lesson_time'
    lesson_num = db.Column('lesson_num', db.SMALLINT, primary_key=True)
    stime = db.Column('lesson_stime', db.Time, nullable=False)
    etime = db.Column('lesson_etime', db.Time, nullable=False)

    def __str__(self):
        return "%s - %s" %(self.stime.strftime("%H:%M"), self.etime.strftime("%H:%M"))


class Classroom(db.Model):
    __tablename__ = 'classroom'
    classroom = db.Column('classroom', db.String(6), primary_key=True)


class _ScheduledCommon(db.Model, _ObjectWithStudGroupSubnumsMap):
    __abstract__ = True

    stud_group_subnums = db.Column('stud_group_subnums', db.SMALLINT, nullable=False, default=0)
    week_day = db.Column('week_day', db.SMALLINT, nullable=False)
    # 1 - числитель; 2 - знаменатель; 3 - каждую неделю
    week_type = db.Column('week_type', db.SMALLINT, nullable=False)
    lesson_num = db.Column(db.ForeignKey('lesson_time.lesson_num'), nullable=False)
    classroom = db.Column(db.ForeignKey('classroom.classroom'))


class _ScheduledLesson(_ScheduledCommon):
    __abstract__ = True

    curriculum_unit_id = db.Column(db.ForeignKey('curriculum_unit.curriculum_unit_id'), nullable=False)
    teacher_id = db.Column(db.ForeignKey('teacher.teacher_id'))
    type = db.Column('lesson_type', db.Enum(*LessonTypesScheduled), nullable=False)
    form = db.Column('lesson_form', db.Enum(*LessonForms), nullable=False, default='in_class')
    comment = db.Column('scheduled_lesson_comment', db.String(4000))


class ScheduledLesson(_ScheduledLesson):
    __abstract__ = False
    __tablename__ = 'scheduled_lesson'
    id = db.Column('scheduled_lesson_id', db.BIGINT, primary_key=True)

    teacher = db.relationship('Teacher')


class ScheduledLessonDraft(_ScheduledLesson):
    __abstract__ = False
    __tablename__ = 'scheduled_lesson_draft'

    id = db.Column('scheduled_lesson_id', db.BIGINT, primary_key=True, autoincrement=True)
    teacher = db.relationship('Teacher')


class _ScheduledSubjectParticular(_ScheduledCommon):
    __abstract__ = True

    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id'), nullable=False)
    subject_particular_id = db.Column(db.ForeignKey('subject_particular.subject_particular_id'), nullable=False)
    comment = db.Column('scheduled_subject_particular_comment', db.String(4000))


class ScheduledSubjectParticular(_ScheduledSubjectParticular):
    __abstract__ = False
    __tablename__ = 'scheduled_subject_particular'

    id = db.Column('scheduled_subject_particular_id', db.BIGINT, primary_key=True)
    subject_particular = db.relationship('SubjectParticular')


class ScheduledSubjectParticularDraft(_ScheduledSubjectParticular):
    __abstract__ = False
    __tablename__ = 'scheduled_subject_particular_draft'

    id = db.Column('scheduled_subject_particular_id', db.BIGINT, primary_key=True, autoincrement=True)
    subject_particular = db.relationship('SubjectParticular')


class AuthCode(db.Model):
    __tablename__ = 'auth_code'
    id = db.Column('auth_id', db.BIGINT, primary_key=True, autoincrement=True)
    email = db.Column('email', db.String(45))
    phone = db.Column('phone', db.BIGINT)
    code = db.Column('code', db.INTEGER, nullable=False)

    send_time = db.Column('code_send_time', db.DateTime, nullable=False)
    auth_time = db.Column('code_auth_time', db.DateTime)

    auth_err_count = db.Column('auth_err_count', db.SMALLINT, default=0)


class AuthCode4ChangeEmail(db.Model):
    __tablename__ = 'auth_code_4_change_email'
    id = db.Column('auth_code_4_change_email_id', db.BIGINT, primary_key=True, autoincrement=True)
    person_id = db.Column(db.ForeignKey('person.person_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    email_old = db.Column('email_old', db.String(45))
    email = db.Column('email', db.String(45), nullable=False)
    code_old = db.Column('code_old', db.INTEGER)
    code = db.Column('code', db.INTEGER, nullable=False)
    send_time = db.Column('code_send_time', db.DateTime, nullable=False)
    accept_time = db.Column('code_accept_time', db.DateTime)
    auth_err_count = db.Column('auth_err_count', db.SMALLINT, default=0)
    person = db.relationship('Person')


class AuthCode4ChangePhone(db.Model):
    __tablename__ = 'auth_code_4_change_phone'
    id = db.Column('auth_code_4_change_phone_id', db.BIGINT, primary_key=True, autoincrement=True)
    person_id = db.Column(db.ForeignKey('person.person_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    phone_old = db.Column('phone_old', db.BIGINT)
    phone = db.Column('phone', db.BIGINT, nullable=False)
    code_old = db.Column('code_old', db.INTEGER)
    code = db.Column('code', db.INTEGER, nullable=False)
    send_time = db.Column('code_send_time', db.DateTime, nullable=False)
    accept_time = db.Column('code_accept_time', db.DateTime)
    auth_err_count = db.Column('auth_err_count', db.SMALLINT, default=0)
    person = db.relationship('Person')


class CertificateOfStudy(db.Model):
    __tablename__ = 'certificate_of_study'
    __table_args__ = (
        db.UniqueConstraint('certificate_of_study_year', 'certificate_of_study_num'),
    )

    MAX_PER_ORDER = 5

    id = db.Column('certificate_of_study_id', db.BIGINT, primary_key=True, autoincrement=True)
    student_id = db.Column(db.ForeignKey('student.student_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    specialty_id = db.Column(db.ForeignKey('specialty.specialty_id'), index=True, nullable=False)
    specialty = db.relationship('Specialty', foreign_keys=[specialty_id])
    surname = db.Column('certificate_of_study_surname', db.String(45), nullable=False)
    firstname = db.Column('certificate_of_study_firstname', db.String(45), nullable=False)
    middlename = db.Column('certificate_of_study_middlename', db.String(45))
    course = db.Column('certificate_of_study_course', db.SMALLINT)
    student_status = db.Column('certificate_of_study_student_status', db.Enum(*StudentStateDict.keys()), nullable=False)

    request_time = db.Column('certificate_of_study_request_time', db.DateTime, nullable=False)
    print_time = db.Column('certificate_of_study_print_time', db.DateTime)
    ready_time = db.Column('certificate_of_study_ready_time', db.DateTime)
    year = db.Column('certificate_of_study_year', db.SMALLINT)
    num = db.Column('certificate_of_study_num', db.INTEGER)

    comment = db.Column('certificate_of_study_comment', db.String(4000))

    @property
    def print_num(self):
        if self.num is not None:
            return "%d-%d" % (Department.ID_DEFAULT, self.num)


class Holiday(db.Model):
    __tablename__ = 'holiday'
    date = db.Column('date', db.Date, primary_key=True)
