def allow_write(u):
    if u is None or u.is_anonymous:
        return False

    if u.admin_user is not None and u.admin_user.active:
        return True

    if u.teacher is not None and u.teacher.active and u.teacher.dean_staff:
        return True

    # temp
    # if u.login in ('korobejnikova_a_v', 'derevyanko_v_g'):
    #     return True

    return False