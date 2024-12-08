from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import Session
from model import Person


def hist_save_controller(session: Session, obj, user: Person, check_journalize_attributes=True):
    now = datetime.now()
    pk = next(k for k, c in inspect(obj.__class__).c.items() if c.primary_key)
    journalize_class = obj.__class__.journalize_class

    pk_h = next(k for k, c in inspect(journalize_class).c.items() if c.primary_key and c.foreign_keys)

    obj_h = session.query(journalize_class).filter(and_(getattr(journalize_class, pk_h) == getattr(obj, pk), journalize_class.etime.is_(None))).one_or_none()

    if check_journalize_attributes:
        # Прервать запись, если все журналируемые атрибуты не изменились
        if obj_h is not None and all(getattr(obj, attr) == getattr(obj_h, attr) for attr in obj.journalize_attributes):
            return obj_h, None

    if obj_h is not None:
        obj_h.etime = now
        session.add(obj_h)

    obj_h_n = journalize_class(**{pk_h: getattr(obj, pk), "stime": now})
    obj_h_n.changed_person_id = user.id

    for attr in obj.journalize_attributes:
        setattr(obj_h_n, attr, getattr(obj, attr))

    if hasattr(obj.__class__, 'journalize_relations'):
        for journalize_relation in obj.__class__.journalize_relations:
            getattr(obj_h_n, journalize_relation).extend(getattr(obj, journalize_relation))

    session.add(obj_h_n)
    return obj_h, obj_h_n
