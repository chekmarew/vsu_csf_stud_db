"""Файлы с классами для стущностей в БД"""
import enum

from flask_user import UserMixin

from app import DB


class _ObjectWithYear:
    """Класс для удобного представления курса и года обучения"""

    @property
    def course(self):
        """Свойство для конвертации семестра в курс обучения"""
        if self.semester is None:
            return None
        return (self.semester // 2) + 1

    @property
    def year_print(self):
        """Свойство для удобного представления года обучения"""
        if self.year is None:
            return None
        return "%d-%d" % (self.year, self.year + 1)


class _ObjectWithFullName:
    """Класс для упрощенного представления ФИО студента"""

    @property
    def full_name(self):
        """Свойство для представления полного ФИО"""
        if self.surname is None or self.firstname is None:
            return None
        return " ".join(
            (self.surname, self.firstname, self.middlename)
            if self.middlename is not None else
            (self.surname, self.firstname))

    @property
    def full_name_short(self):
        """Свойство для представления ФИО в упрощенной форме"""
        return "%s %s. %s." % \
               (self.surname, self.firstname[0], self.middlename[0]) \
            if self.middlename is not None else \
            "%s %s." % (self.surname, self.firstname[0])


class StudGroup(DB.Model, _ObjectWithYear):
    """Модель сущности 'Студенческая группа'"""
    __tablename__ = 'stud_group'
    __table_args__ = (
        DB.UniqueConstraint(
            'stud_group_year', 'stud_group_semester', 'stud_group_num', 'stud_group_subnum'
        ),
    )

    id = DB.Column('stud_group_id', DB.SMALLINT, primary_key=True, autoincrement=True)
    year = DB.Column('stud_group_year', DB.SMALLINT, nullable=False)
    semester = DB.Column('stud_group_semester', DB.SMALLINT, nullable=False)
    num = DB.Column('stud_group_num', DB.SMALLINT, nullable=False)
    subnum = DB.Column('stud_group_subnum', DB.SMALLINT, nullable=False, default=0)
    active = DB.Column('stud_group_active', DB.BOOLEAN, nullable=False, default=True)

    students = DB.relationship('Student', lazy=True, backref='stud_group',
                               order_by="Student.surname, Student.firstname, Student.middlename")
    curriculum_units = DB.relationship(
        'CurriculumUnit', lazy=True, backref='stud_group', order_by="CurriculumUnit.id"
    )

    @property
    def num_print(self):
        """Свойство для представления группы и номера группы"""
        if self.num is None or self.subnum is None:
            return None
        return "%d.%d" % (self.num, self.subnum) if self.subnum != 0 else str(self.num)

    def __repr__(self):
        return "StudGroup(id={id}, " \
               "year={year}, " \
               "semester={semester}, " \
               "num={num}, " \
               "subnum={subnum}, " \
               "active={active})" \
            .format(id=self.id,
                    year=self.year,
                    semester=self.semester,
                    num=self.num,
                    subnum=self.subnum,
                    active=self.active)


class Subject(DB.Model):
    """Класс для сущности 'Предмет обучения'"""
    __tablename__ = 'subject'

    id = DB.Column('subject_id', DB.INTEGER, primary_key=True, autoincrement=True)
    name = DB.Column('subject_name', DB.String(45), nullable=False, unique=True)

    def __repr__(self):
        return "Subject(id={id}, name={name})".format(id=self.id, name=self.name)


class Teacher(DB.Model, _ObjectWithFullName):
    """Класс для сущности 'Учитель'"""
    __tablename__ = 'teacher'

    id = DB.Column('teacher_id', DB.INTEGER, primary_key=True, autoincrement=True)
    surname = DB.Column('teacher_surname', DB.String(45), nullable=False)
    firstname = DB.Column('teacher_firstname', DB.String(45), nullable=False)
    middlename = DB.Column('teacher_middlename', DB.String(45))
    rank = DB.Column('teacher_rank', DB.String(45), nullable=False)

    def __repr__(self):
        return "Teacher(id={id}," \
               " surname={surname}," \
               " firstname={firstname}," \
               " middlename={middlename}," \
               " rank={rank})" \
            .format(id=self.id,
                    surname=self.surname,
                    firstname=self.firstname,
                    middlename=self.middlename,
                    rank=self.rank)


# Типы отчётности для единицы учебного плана
class MarkType(enum.Enum):
    """Перечисление для типа оценки"""
    # Зачёт
    test_simple = 1
    # Экзамен
    exam = 2
    # Зачёт с оценкой
    test_diff = 3


class CurriculumUnit(DB.Model):
    """Класс для сущности 'Единица учебного плана'"""
    __tablename__ = 'curriculum_unit'
    __table_args__ = (
        DB.UniqueConstraint('subject_id', 'stud_group_id'),
    )

    id = DB.Column('curriculum_unit_id', DB.INTEGER, primary_key=True, autoincrement=True)
    subject_id = DB.Column(DB.ForeignKey('subject.subject_id'), nullable=False, index=True)
    stud_group_id = DB.Column(DB.ForeignKey('stud_group.stud_group_id'), nullable=False, index=True)
    teacher_id = DB.Column(DB.ForeignKey('teacher.teacher_id'), nullable=False, index=True)
    mark_type = DB.Column('mark_type', DB.Enum(MarkType), nullable=False)
    hours_att_1 = DB.Column('hours_att_1', DB.SMALLINT, nullable=False)
    hours_att_2 = DB.Column('hours_att_2', DB.SMALLINT, nullable=False)
    hours_att_3 = DB.Column('hours_att_3', DB.SMALLINT, nullable=False)

    subject = DB.relationship('Subject')
    teacher = DB.relationship('Teacher')
    att_marks = DB.relationship('AttMark', lazy=True, backref='curriculum_unit')
    teaching_lessons = DB.relationship(
        'TeachingLesson', secondary='teaching_lesson_and_curriculum_unit'
    )

    def __repr__(self):
        return "CurriculumUnit(id={id}, subject_id={subject_id}, stud_group_id={stud_group_id}," \
               " teacher_id={teacher_id}," \
               " mark_type={mark_type}, hours_att_1={hours_att_1}," \
               " hours_att_2={hours_att_2}," \
               " hours_att_3={hours_att_3})" \
            .format(id=self.id,
                    subject_id=self.subject_id,
                    stud_group_id=self.stud_group_id,
                    teacher_id=self.teacher_id,
                    mark_type=self.mark_type,
                    hours_att_1=self.hours_att_1,
                    hours_att_2=self.hours_att_2,
                    hours_att_3=self.hours_att_3)


class Student(DB.Model, _ObjectWithFullName):
    """Класс для сущности 'Студент'"""
    __tablename__ = 'student'

    id = DB.Column('student_id', DB.BIGINT, primary_key=True)
    surname = DB.Column('student_surname', DB.String(45), nullable=False)
    firstname = DB.Column('student_firstname', DB.String(45), nullable=False)
    middlename = DB.Column('student_middlename', DB.String(45))
    stud_group_id = DB.Column(DB.ForeignKey(
        'stud_group.stud_group_id', ondelete='SET NULL', onupdate='SET NULL'
    ), index=True)
    semester = DB.Column('student_semestr', DB.SMALLINT)
    alumnus_year = DB.Column('student_alumnus_year', DB.SMALLINT)
    expelled_year = DB.Column('student_expelled_year', DB.SMALLINT)

    def __repr__(self):
        return "Student(id={id}," \
               " surname={surname}," \
               " firstname={firstname}," \
               " middlename={middlename}," \
               " stud_group_id={stud_group_id}," \
               " semester={semester}," \
               " alumnus_year={alumnus_year}," \
               " expelled_year={expelled_year})". \
            format(id=self.id,
                   surname=self.surname,
                   firstname=self.firstname,
                   middlename=self.middlename,
                   stud_group_id=self.stud_group_id,
                   semester=self.semester,
                   alumnus_year=self.alumnus_year,
                   expelled_year=self.expelled_year)


class AttMark(DB.Model):
    """Класс для сущности 'Аттестационная оценка'"""
    __tablename__ = 'att_mark'
    __table_args__ = (
        DB.UniqueConstraint('curriculum_unit_id', 'student_id'),
    )

    att_mark_id = DB.Column(DB.INTEGER, primary_key=True, autoincrement=True)
    curriculum_unit_id = DB.Column(
        DB.ForeignKey('curriculum_unit.curriculum_unit_id'), nullable=False
    )
    student_id = DB.Column(DB.ForeignKey('student.student_id'), nullable=False, index=True)
    att_mark_1 = DB.Column(DB.SMALLINT)
    att_mark_2 = DB.Column(DB.SMALLINT)
    att_mark_3 = DB.Column(DB.SMALLINT)
    att_mark_exam = DB.Column(DB.SMALLINT)
    att_mark_append_ball = DB.Column(DB.SMALLINT)
    student = DB.relationship('Student')

    def __repr__(self):
        return "AttMark(att_mark_id={att_mark_id}," \
               " curriculum_unit_id={curriculum_unit_id}," \
               " student_id={student_id}," \
               " att_mark_1={att_mark_1}," \
               " att_mark_2={att_mark_2}," \
               " att_mark_3={att_mark_3}," \
               " att_mark_exam={att_mark_exam}," \
               " att_mark_append_ball={att_mark_append_ball})". \
            format(att_mark_id=self.att_mark_id,
                   curriculum_unit_id=self.curriculum_unit_id,
                   student_id=self.student_id,
                   att_mark_1=self.att_mark_1,
                   att_mark_2=self.att_mark_2,
                   att_mark_3=self.att_mark_3,
                   att_mark_exam=self.att_mark_exam,
                   att_mark_append_ball=self.att_mark_append_ball)


# для курсовой мои таблицы ниже


class LessonType(enum.Enum):
    """Перечисление для типа занятий"""
    lection = 'Лекция'
    practice = 'Практика'
    seminar = 'Семинар'


class TeachingLesson(DB.Model):
    """Класс для сущности 'Учебное занятие'"""
    __tablename__ = 'teaching_lesson'

    teaching_lesson_id = DB.Column(DB.INTEGER, primary_key=True, autoincrement=True)
    schedule = DB.Column(DB.JSON, nullable=False)
    lesson_type = DB.Column(DB.Enum(LessonType), nullable=False)

    curriculum_units = DB.relationship(
        'CurriculumUnit', secondary='teaching_lesson_and_curriculum_unit'
    )

    def __repr__(self):
        return "TeachingLesson(teaching_lesson_id={teaching_lesson_id}," \
               " schedule={schedule}," \
               " lesson_type={lesson_type})" \
            .format(teaching_lesson_id=self.teaching_lesson_id,
                    schedule=self.schedule,
                    lesson_type=self.lesson_type)


class TeachingLessonAndCurriculumUnit(DB.Model):
    """Класс для связующей сущности между единицами учебного плана и учебного занятия"""
    __tablename__ = 'teaching_lesson_and_curriculum_unit'

    teaching_lesson_id = DB.Column(
        DB.Integer, DB.ForeignKey('curriculum_unit.curriculum_unit_id'), primary_key=True
    )
    curriculum_unit_id = DB.Column(
        DB.Integer, DB.ForeignKey('teaching_lesson.teaching_lesson_id'), primary_key=True
    )

    def __repr__(self):
        return "TeachingLessonAndCurriculumUnit(teaching_lesson_id={teaching_lesson_id}," \
               " curriculum_unit_id={curriculum_unit_id})" \
            .format(teaching_lesson_id=self.teaching_lesson_id,
                    curriculum_unit_id=self.curriculum_unit_id)


class Attendance(DB.Model):
    """Класс для сущности 'Посещаемость'"""
    __tablename__ = 'attendance'
    __table_args__ = (
        DB.ForeignKeyConstraint(['attendance_teaching_lesson_id', 'attendance_curriculum_unit_id'],
                                ['teaching_lesson_and_curriculum_unit.teaching_lesson_id',
                                 'teaching_lesson_and_curriculum_unit.curriculum_unit_id']),
    )

    attendance_teaching_lesson_id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    attendance_curriculum_unit_id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)

    lesson_attendance = DB.Column(DB.Boolean, nullable=False)
    lesson_date = DB.Column(DB.Date, nullable=False)
    student_id = DB.Column(DB.BigInteger, DB.ForeignKey('student.student_id'), nullable=False)

    def __repr__(self):
        return "Attendance(attendance_teaching_lesson_id={attendance_teaching_lesson_id}," \
               " attendance_curriculum_unit_id={attendance_curriculum_unit_id}," \
               " lesson_attendance={lesson_attendance}," \
               " lesson_date={lesson_date}, student_id={student_id})". \
            format(attendance_teaching_lesson_id=self.attendance_teaching_lesson_id,
                   attendance_curriculum_unit_id=self.attendance_curriculum_unit_id,
                   lesson_attendance=self.lesson_attendance,
                   lesson_date=self.lesson_date,
                   student_id=self.student_id)


class User(DB.Model, UserMixin):
    """Класс для сущности 'Пользователь системы'"""
    __tablename__ = 'user'

    id = DB.Column(DB.Integer, primary_key=True)
    username = DB.Column(DB.String(50), nullable=False, unique=True)
    password = DB.Column(DB.String(255), nullable=False, server_default='')
    active = DB.Column('is_active', DB.Boolean(), nullable=False, server_default='0')

    roles = DB.relationship('Role', secondary='user_roles',
                            backref=DB.backref('users', lazy='dynamic'))

    def __repr__(self):
        return "User(id={id}, username={username}, password={password})". \
            format(id=self.id, username=self.username, password=self.password)


class Role(DB.Model):
    """Класс для сущности 'Роль пользователя в системе'"""
    __tablename__ = 'role'

    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(50), unique=True)

    def __repr__(self):
        return "Role(id={id}, name={name})". \
            format(id=self.id, name=self.name)


class UserRoles(DB.Model):
    """Связующая сущность между пользователями и их ролями"""
    __tablename__ = 'user_roles'

    id = DB.Column(DB.Integer, primary_key=True)
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = DB.Column(DB.Integer, DB.ForeignKey('role.id', ondelete='CASCADE'))

    def __repr__(self):
        return "UserRoles(id={id}, name={name}, user_id={user_id})". \
            format(id=self.id, name=self.name, user_id=self.user_id)
