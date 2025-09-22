from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.urls import reverse

from classes.models import Class
from .models import Project
from .forms import ProjectForm, ProjectTaskFormSet
from core.notifications import dispatch_notification


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


def _teacher_emails(turma):
    return [teacher.email for teacher in turma.teachers.all() if teacher.email]


def _project_recipients(project, exclude_user=None):
    recipients = {email for email in _teacher_emails(project.student_class)}
    for member in project.members.all():
        if member.email:
            recipients.add(member.email)
    if exclude_user and getattr(exclude_user, 'email', None):
        recipients.discard(exclude_user.email)
    return [email for email in recipients if email]


def _notify_project_created(request, project, actor):
    recipients = _project_recipients(project, exclude_user=actor)
    if not recipients:
        return
    actor_name = actor.get_full_name() or actor.username
    turma = project.student_class
    project_url = request.build_absolute_uri(
        reverse('projects:project_detail', args=[turma.id, project.id])
    )
    subject = _('[Infantinho] Novo projeto "{project}"').format(project=project.title)
    message = _(
        '{actor} criou o projeto "{project}" na turma {class_name}.\n'
        'Consulta os detalhes em: {url}'
    ).format(
        actor=actor_name,
        project=project.title,
        class_name=turma.name,
        url=project_url,
    )
    dispatch_notification(
        subject=subject,
        message=message,
        recipients=recipients,
        category='project_created',
        metadata={
            'project_id': project.id,
            'class_id': turma.id,
            'actor_id': actor.id,
            'event': 'created',
            'project_title': project.title,
        },
    )


def _notify_project_updated(request, project, actor):
    recipients = _project_recipients(project, exclude_user=actor)
    if not recipients:
        return
    actor_name = actor.get_full_name() or actor.username
    turma = project.student_class
    project_url = request.build_absolute_uri(
        reverse('projects:project_detail', args=[turma.id, project.id])
    )
    subject = _('[Infantinho] Atualização no projeto "{project}"').format(project=project.title)
    message = _(
        '{actor} atualizou o projeto "{project}" na turma {class_name}.\n'
        'Revê o plano em: {url}'
    ).format(
        actor=actor_name,
        project=project.title,
        class_name=turma.name,
        url=project_url,
    )
    dispatch_notification(
        subject=subject,
        message=message,
        recipients=recipients,
        category='project_updated',
        metadata={
            'project_id': project.id,
            'class_id': turma.id,
            'actor_id': actor.id,
            'event': 'updated',
            'project_title': project.title,
        },
    )


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
                _notify_project_created(request, project, request.user)
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
                _notify_project_updated(request, project, request.user)
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
