from functools import wraps
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden


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


# --- Expansões (encarregados) ---
def is_guardian_of_any_student_in_class(user, class_obj) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "role", None) != "encarregado":
        return False
    # user é encarregado de pelo menos um aluno da turma
    return class_obj.students.filter(encarregados_relations__encarregado=user).exists()


def can_view_as_guardian(user, class_obj) -> bool:
    return is_guardian_of_any_student_in_class(user, class_obj)


def class_member_or_guardian_required(view_func):
    @wraps(view_func)
    def _wrapped(request, class_id, *args, **kwargs):
        from classes.models import Class

        turma = get_object_or_404(Class, id=class_id)
        if can_access_class(request.user, turma) or can_view_as_guardian(request.user, turma):
            return view_func(request, class_id, *args, **kwargs)
        return HttpResponseForbidden(_('Access restricted to members/guardians of this class.'))

    return _wrapped


# --- Decorators reutilizáveis (esperam um parâmetro class_id na URL) ---
def class_member_required(view_func):
    @wraps(view_func)
    def _wrapped(request, class_id, *args, **kwargs):
        from classes.models import Class  # import local para evitar ciclos

        turma = get_object_or_404(Class, id=class_id)
        if can_access_class(request.user, turma):
            return view_func(request, class_id, *args, **kwargs)
        # Responder 403 para endpoints que exigem bloqueio explícito
        return HttpResponseForbidden(_('Access restricted to members of this class.'))

    return _wrapped


def class_teacher_required(view_func):
    @wraps(view_func)
    def _wrapped(request, class_id, *args, **kwargs):
        from classes.models import Class

        turma = get_object_or_404(Class, id=class_id)
        if can_moderate_class(request.user, turma):
            return view_func(request, class_id, *args, **kwargs)
        return HttpResponseForbidden(_('Access restricted to class moderators.'))

    return _wrapped


def class_student_required(view_func):
    @wraps(view_func)
    def _wrapped(request, class_id, *args, **kwargs):
        from classes.models import Class

        turma = get_object_or_404(Class, id=class_id)
        if is_student_in_class(request.user, turma) or is_admin(request.user):
            return view_func(request, class_id, *args, **kwargs)
        return HttpResponseForbidden(_('Access restricted to students of this class.'))

    return _wrapped


