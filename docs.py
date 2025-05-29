from py3o.template import Template
import os



_DIR_TEMPLATES = os.path.join(os.path.dirname(__file__), "templates_docs")
_DIR_TEMPLATES_OUT = os.path.join(os.path.dirname(__file__), "templates_docs_out")


def create_doc_curriculum_unit(cu, _file_out=None):
    file_out = _file_out if _file_out else os.path.join(_DIR_TEMPLATES_OUT, "%s.odt" % str(cu.id))
    document = {}

    att_marks = [m for m in cu.att_marks if m.att_mark_id not in cu.att_marks_readonly_ids]
    att_marks.sort(key=lambda m: (m.student.surname, m.student.firstname, m.student.middlename))
    i = 0
    for m in att_marks:
        i += 1
        m.num = i
        if m.manual_add:
            m.num = "%d*" % i
    file_template = ""

    students_exclude2 = [m.student for m in cu.att_marks if m.exclude == 2]

    if cu.closed or cu.pass_department or cu.status in ("exam", "filled"):
        f = ("template_%s_with_attendance.odt" if cu.calc_attendance else "template_%s.odt") % cu.mark_type
        file_template = os.path.join(_DIR_TEMPLATES, f)
        document["total"] = {}
        if cu.mark_type in ("exam", "test_diff"):
            document["total"] = {"v0": 0, "v2": 0, "v3": 0, "v4": 0, "v5": 0}
        if cu.mark_type == "test_simple":
            document["total"] = {"v0": 0, "vFalse": 0, "vTrue": 0}
        for m in att_marks:
            v = m.result_print
            if v is None:
                for k in document["total"].keys():
                    document["total"][k] = ''
                break
            else:
                k = "v%s" % v[1]["value"]
                document["total"][k] += 1
    else:
        file_template = os.path.join(_DIR_TEMPLATES, "template_att.odt")

    t = Template(file_template, file_out)
    t.render({"document": document, "cu": cu, "att_marks": att_marks, "students_exclude2": students_exclude2})
    for m in att_marks:
        delattr(m, "num")

    return file_out


def create_doc_curriculum_unit_simple_marks(cu, mark_type, _file_out=None):
    file_out = _file_out if _file_out else os.path.join(_DIR_TEMPLATES_OUT, "%s_%s.odt" % (str(cu.id), mark_type))

    file_template = os.path.join(_DIR_TEMPLATES, "template_simple_mark.odt")
    document = {}
    mark_type_name = {
        "test_simple": "Зачет",
        "exam": "Экзамен",
        "test_diff": "Дифференцированный зачет",
        "course_work": "Курсовая работа",
        "course_project": "Курсовой проект"
    }.get(mark_type, "")

    att_marks = [m.get_simple_att_mark(mark_type) for m in cu.att_marks if m.att_mark_id not in cu.att_marks_readonly_ids]
    att_marks.sort(key=lambda m: (m.student.surname, m.student.firstname, m.student.middlename))
    i = 0
    for m in att_marks:
        i += 1
        m.num = i

    students_exclude2 = [m.student for m in cu.att_marks if m.exclude == 2]

    document["total"] = {}

    if mark_type == "test_simple":
        document["total"] = {"v0": 0, "vFalse": 0, "vTrue": 0}
    else:
        document["total"] = {"v0": 0, "v2": 0, "v3": 0, "v4": 0, "v5": 0}

    for m in att_marks:
        v = m.ball_value
        if v is None:
            for k in document["total"].keys():
                document["total"][k] = ''
            break
        else:
            k = "v%s" % v
            document["total"][k] += 1

    t = Template(file_template, file_out)
    # t.render({})
    t.render({"document": document, "cu": cu, "att_marks": att_marks, "students_exclude2": students_exclude2, "mark_type_name": mark_type_name, "mark_type_is_test_simple": (mark_type == "test_simple")})
    for m in att_marks:
        delattr(m, "num")

    return file_out


def create_doc(template_name, data, _file_out=None):
    file_out = _file_out if _file_out else os.path.join(_DIR_TEMPLATES_OUT, "%s.odt" % template_name)
    file_template = os.path.join(_DIR_TEMPLATES, "%s.odt" % template_name)
    t = Template(file_template, file_out)
    t.render(data)
    return file_out
