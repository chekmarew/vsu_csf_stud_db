import enum

from flask_user import UserMixin

from app_config import db


class _ObjectWithYear:
    @property
    def course(self):
        if self.semester is None:
            return None
        return (self.semester // 2) + 1

    @property
    def year_print(self):
        if self.year is None:
            return None
        return "%d-%d" % (self.year, self.year + 1)


class _ObjectWithFullName:
    @property
    def full_name(self):
        if self.surname is None or self.firstname is None:
            return None
        return " ".join((self.surname, self.firstname, self.middlename) if self.middlename is not None else (
            self.surname, self.firstname))

    @property
    def full_name_short(self):
        return "%s %s. %s." % (self.surname, self.firstname[0], self.middlename[0]) if self.middlename is not None \
            else "%s %s." % (self.surname, self.firstname[0])


class StudGroup(db.Model, _ObjectWithYear):
    __tablename__ = 'stud_group'
    __table_args__ = (
        db.UniqueConstraint('stud_group_year', 'stud_group_semester', 'stud_group_num', 'stud_group_subnum'),
    )

    id = db.Column('stud_group_id', db.SMALLINT, primary_key=True, autoincrement=True)
    year = db.Column('stud_group_year', db.SMALLINT, nullable=False)
    semester = db.Column('stud_group_semester', db.SMALLINT, nullable=False)
    num = db.Column('stud_group_num', db.SMALLINT, nullable=False)
    subnum = db.Column('stud_group_subnum', db.SMALLINT, nullable=False, default=0)
    active = db.Column('stud_group_active', db.BOOLEAN, nullable=False, default=True)

    students = db.relationship('Student', lazy=True, backref='stud_group',
                               order_by="Student.surname, Student.firstname, Student.middlename")
    curriculum_units = db.relationship('CurriculumUnit', lazy=True, backref='stud_group', order_by="CurriculumUnit.id")

    @property
    def num_print(self):
        if self.num is None or self.subnum is None:
            return None
        return "%d.%d" % (self.num, self.subnum) if self.subnum != 0 else str(self.num)

    def __repr__(self):
        return "StudGroup(id={id}, year={year}, semester={semester}, num={num}, subnum={subnum}, active={active})" \
            .format(id=self.id, year=self.year, semester=self.semester, num=self.num, subnum=self.subnum,
                    active=self.active)


class Subject(db.Model):
    __tablename__ = 'subject'

    id = db.Column('subject_id', db.INTEGER, primary_key=True, autoincrement=True)
    name = db.Column('subject_name', db.String(45), nullable=False, unique=True)

    def __repr__(self):
        return "Subject(id={id}, name={name})".format(id=self.id, name=self.name)


class Teacher(db.Model, _ObjectWithFullName):
    __tablename__ = 'teacher'

    id = db.Column('teacher_id', db.INTEGER, primary_key=True, autoincrement=True)
    surname = db.Column('teacher_surname', db.String(45), nullable=False)
    firstname = db.Column('teacher_firstname', db.String(45), nullable=False)
    middlename = db.Column('teacher_middlename', db.String(45))
    rank = db.Column('teacher_rank', db.String(45), nullable=False)

    def __repr__(self):
        return "Teacher(id={id}, surname={surname}, firstname={firstname}, middlename={middlename}, rank={rank})" \
            .format(id=self.id, surname=self.surname, firstname=self.firstname, middlename=self.middlename,
                    rank=self.rank)


# Типы отчётности для единицы учебного плана
class MarkType(enum.Enum):
    # Зачёт
    test_simple = 1
    # Экзамен
    exam = 2
    # Зачёт с оценкой
    test_diff = 3


class CurriculumUnit(db.Model):
    __tablename__ = 'curriculum_unit'
    __table_args__ = (
        db.UniqueConstraint('subject_id', 'stud_group_id'),
    )

    id = db.Column('curriculum_unit_id', db.INTEGER, primary_key=True, autoincrement=True)
    subject_id = db.Column(db.ForeignKey('subject.subject_id'), nullable=False, index=True)
    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id'), nullable=False, index=True)
    teacher_id = db.Column(db.ForeignKey('teacher.teacher_id'), nullable=False, index=True)
    mark_type = db.Column('mark_type', db.Enum(MarkType), nullable=False)
    hours_att_1 = db.Column('hours_att_1', db.SMALLINT, nullable=False)
    hours_att_2 = db.Column('hours_att_2', db.SMALLINT, nullable=False)
    hours_att_3 = db.Column('hours_att_3', db.SMALLINT, nullable=False)

    subject = db.relationship('Subject')
    teacher = db.relationship('Teacher')
    att_marks = db.relationship('AttMark', lazy=True, backref='curriculum_unit')
    teaching_lessons = db.relationship('TeachingLesson', secondary='teaching_lesson_and_curriculum_unit')

    def __repr__(self):
        return "CurriculumUnit(id={id}, subject_id={subject_id}, stud_group_id={stud_group_id}," \
               " teacher_id={teacher_id}," \
               " mark_type={mark_type}, hours_att_1={hours_att_1}," \
               " hours_att_2={hours_att_2}, hours_att_3={hours_att_3})".format(id=self.id, subject_id=self.subject_id,
                                                                               stud_group_id=self.stud_group_id,
                                                                               teacher_id=self.teacher_id,
                                                                               mark_type=self.mark_type,
                                                                               hours_att_1=self.hours_att_1,
                                                                               hours_att_2=self.hours_att_2,
                                                                               hours_att_3=self.hours_att_3)


class Student(db.Model, _ObjectWithFullName):
    __tablename__ = 'student'

    id = db.Column('student_id', db.BIGINT, primary_key=True)
    surname = db.Column('student_surname', db.String(45), nullable=False)
    firstname = db.Column('student_firstname', db.String(45), nullable=False)
    middlename = db.Column('student_middlename', db.String(45))
    stud_group_id = db.Column(db.ForeignKey('stud_group.stud_group_id', ondelete='SET NULL', onupdate='SET NULL'),
                              index=True)
    semester = db.Column('student_semestr', db.SMALLINT)
    alumnus_year = db.Column('student_alumnus_year', db.SMALLINT)
    expelled_year = db.Column('student_expelled_year', db.SMALLINT)

    def __repr__(self):
        return "Student(id={id}, surname={surname}, firstname={firstname}, middlename={middlename}," \
               " stud_group_id={stud_group_id}, semester={semester}, alumnus_year={alumnus_year}," \
               " expelled_year={expelled_year})". \
            format(id=self.id, surname=self.surname, firstname=self.firstname, middlename=self.middlename,
                   stud_group_id=self.stud_group_id, semester=self.semester, alumnus_year=self.alumnus_year,
                   expelled_year=self.expelled_year)


class AttMark(db.Model):
    __tablename__ = 'att_mark'
    __table_args__ = (
        db.UniqueConstraint('curriculum_unit_id', 'student_id'),
    )

    att_mark_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    curriculum_unit_id = db.Column(db.ForeignKey('curriculum_unit.curriculum_unit_id'), nullable=False)
    student_id = db.Column(db.ForeignKey('student.student_id'), nullable=False, index=True)
    att_mark_1 = db.Column(db.SMALLINT)
    att_mark_2 = db.Column(db.SMALLINT)
    att_mark_3 = db.Column(db.SMALLINT)
    att_mark_exam = db.Column(db.SMALLINT)
    att_mark_append_ball = db.Column(db.SMALLINT)
    student = db.relationship('Student')

    def __repr__(self):
        return "AttMark(att_mark_id={att_mark_id}, curriculum_unit_id={curriculum_unit_id}, student_id={student_id}," \
               " att_mark_1={att_mark_1}, att_mark_2={att_mark_2}, att_mark_3={att_mark_3}," \
               " att_mark_exam={att_mark_exam}, att_mark_append_ball={att_mark_append_ball})". \
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
    lection = 'Лекция'
    practice = 'Практика'
    seminar = 'Семинар'


class TeachingLesson(db.Model):
    __tablename__ = 'teaching_lesson'

    teaching_lesson_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    schedule = db.Column(db.JSON, nullable=False)
    lesson_type = db.Column(db.Enum(LessonType), nullable=False)

    curriculum_units = db.relationship('CurriculumUnit', secondary='teaching_lesson_and_curriculum_unit')

    def __repr__(self):
        return "TeachingLesson(teaching_lesson_id={teaching_lesson_id}, schedule={schedule}," \
               " lesson_type={lesson_type})".format(teaching_lesson_id=self.teaching_lesson_id, schedule=self.schedule,
                                                    lesson_type=self.lesson_type)


class TeachingLessonAndCurriculumUnit(db.Model):
    __tablename__ = 'teaching_lesson_and_curriculum_unit'

    teaching_lesson_id = db.Column(db.Integer, db.ForeignKey('curriculum_unit.curriculum_unit_id'), primary_key=True)
    curriculum_unit_id = db.Column(db.Integer, db.ForeignKey('teaching_lesson.teaching_lesson_id'), primary_key=True)

    def __repr__(self):
        return "TeachingLessonAndCurriculumUnit(teaching_lesson_id={teaching_lesson_id}," \
               " curriculum_unit_id={curriculum_unit_id})".format(teaching_lesson_id=self.teaching_lesson_id,
                                                                  curriculum_unit_id=self.curriculum_unit_id)


# ссылка на ключ из таблицы(2) - что это значит?


class Attendance(db.Model):
    __tablename__ = 'attendance'
    __table_args__ = (
        db.ForeignKeyConstraint(['attendance_teaching_lesson_id', 'attendance_curriculum_unit_id'],
                                ['teaching_lesson_and_curriculum_unit.teaching_lesson_id',
                                 'teaching_lesson_and_curriculum_unit.curriculum_unit_id']),
    )

    attendance_teaching_lesson_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attendance_curriculum_unit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    lesson_attendance = db.Column(db.Boolean, nullable=False)
    lesson_date = db.Column(db.Date, nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.student_id'), nullable=False)

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


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')

    roles = db.relationship('Role', secondary='user_roles',
                            backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return "User(id={id}, username={username}, password={password})". \
            format(id=self.id, username=self.username, password=self.password)


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return "Role(id={id}, name={name})". \
            format(id=self.id, name=self.name)


class UserRoles(db.Model):
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete='CASCADE'))

    def __repr__(self):
        return "UserRoles(id={id}, name={name}, user_id={user_id})". \
            format(id=self.id, name=self.name, user_id=self.user_id)
