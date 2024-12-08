from app_config import app, db
from model import Teacher, CurriculumUnit, Subject, SubjectParticular, StudGroup, Specialty, Classroom, Person, EducationLevels
from model import ScheduledLesson, ScheduledLessonDraft, ScheduledSubjectParticular, ScheduledSubjectParticularDraft
import utils
from utils_auth import get_current_user


from flask import jsonify, request
from sqlalchemy import not_, func



@app.route('/api/schedule/lessons', methods=["GET"])
@utils.check_auth_4_api()
def api_schedule_lessons():
    current_user = get_current_user()
    return jsonify({"ok": True})
