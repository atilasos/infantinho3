from django.conf import settings


def is_admin(user) -> bool:
    return bool(user and user.is_authenticated and (user.is_superuser or getattr(user, "role", None) == "admin"))


def is_teacher_of_class(user, class_obj) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "role", None) != "professor":
        return False
    return class_obj.teachers.filter(id=user.id).exists()


def is_student_in_class(user, class_obj) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "role", None) != "aluno":
        return False
    return class_obj.students.filter(id=user.id).exists()


def can_access_class(user, class_obj) -> bool:
    return is_admin(user) or is_teacher_of_class(user, class_obj) or is_student_in_class(user, class_obj)


def can_moderate_class(user, class_obj) -> bool:
    return is_admin(user) or is_teacher_of_class(user, class_obj)


