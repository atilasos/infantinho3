from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from classes.models import Class
from .models import Project
from .forms import ProjectForm, ProjectTaskFormSet


def _is_teacher(user, turma):
    return hasattr(user, 'classes_taught') and turma in user.classes_taught.all()


def _is_student(user, turma):
    return hasattr(user, 'classes_attended') and turma in user.classes_attended.all()


def _is_admin(user):
    return user.is_superuser or getattr(user, 'role', None) == 'admin'


def _is_class_member(user, turma):
    if not user or not user.is_authenticated:
        return False
    return _is_admin(user) or _is_teacher(user, turma) or _is_student(user, turma)


def _is_project_editor(user, turma, project):
    if not user or not user.is_authenticated:
        return False
    if _is_admin(user) or _is_teacher(user, turma):
        return True
    return project.members.filter(id=user.id).exists()


def _available_members_qs(turma):
    return (turma.students.all() | turma.teachers.all()).distinct()


def _configure_task_formset(formset, members_qs):
    for form in formset.forms:
        if 'responsible' in form.fields:
            form.fields['responsible'].queryset = members_qs


@login_required
def project_list(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if not _is_class_member(request.user, turma):
        messages.error(request, _('Acesso restrito aos membros da turma.'))
        return redirect('classes:class_list')

    projects = Project.objects.filter(student_class=turma).prefetch_related('members').order_by('-created_at')
    return render(request, 'projects/project_list.html', {
        'turma': turma,
        'projects': projects,
        'can_create_project': (_is_admin(request.user) or _is_teacher(request.user, turma) or _is_student(request.user, turma)),
    })


@login_required
def project_create(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if not _is_class_member(request.user, turma):
        messages.error(request, _('Apenas membros da turma podem criar projetos.'))
        return redirect('projects:project_list', class_id=turma.id)

    members_qs = _available_members_qs(turma)

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        form.fields['members'].queryset = members_qs
        if form.is_valid():
            project = form.save(commit=False)
            project.student_class = turma
            project.save()
            form.save_m2m()
            project.members.add(request.user)
            formset = ProjectTaskFormSet(request.POST, instance=project)
            _configure_task_formset(formset, project.members.all())
            if formset.is_valid():
                formset.save()
                messages.success(request, _('Projeto criado.'))
                return redirect('projects:project_detail', class_id=turma.id, project_id=project.id)
        formset = ProjectTaskFormSet(request.POST)
        _configure_task_formset(formset, members_qs)
    else:
        form = ProjectForm()
        form.fields['members'].queryset = members_qs
        formset = ProjectTaskFormSet()
        _configure_task_formset(formset, members_qs)

    return render(request, 'projects/project_form.html', {
        'turma': turma,
        'form': form,
        'formset': formset,
        'is_create': True,
    })


@login_required
def project_detail(request, class_id, project_id):
    turma = get_object_or_404(Class, id=class_id)
    project = get_object_or_404(Project, id=project_id, student_class=turma)
    if not _is_class_member(request.user, turma):
        messages.error(request, _('Acesso restrito aos membros da turma.'))
        return redirect('classes:class_list')
    return render(request, 'projects/project_detail.html', {
        'turma': turma,
        'project': project,
        'can_edit': _is_project_editor(request.user, turma, project),
    })


@login_required
def project_update(request, class_id, project_id):
    turma = get_object_or_404(Class, id=class_id)
    project = get_object_or_404(Project, id=project_id, student_class=turma)

    if not _is_project_editor(request.user, turma, project):
        messages.error(request, _('Só membros do projeto ou professores da turma podem editá-lo.'))
        return redirect('projects:project_detail', class_id=turma.id, project_id=project.id)

    members_qs = _available_members_qs(turma)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        form.fields['members'].queryset = members_qs
        if form.is_valid():
            project = form.save()
            project.members.add(request.user)
            formset = ProjectTaskFormSet(request.POST, instance=project)
            _configure_task_formset(formset, project.members.all())
            if formset.is_valid():
                formset.save()
                messages.success(request, _('Projeto atualizado.'))
                return redirect('projects:project_detail', class_id=turma.id, project_id=project.id)
        formset = ProjectTaskFormSet(request.POST, instance=project)
        _configure_task_formset(formset, members_qs)
    else:
        form = ProjectForm(instance=project)
        form.fields['members'].queryset = members_qs
        formset = ProjectTaskFormSet(instance=project)
        _configure_task_formset(formset, project.members.all())

    return render(request, 'projects/project_form.html', {
        'turma': turma,
        'form': form,
        'formset': formset,
        'project': project,
        'is_create': False,
    })


# Create your views here.
