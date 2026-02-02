from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View

from classes.models import Class
from users.decorators import group_required
from users.permissions import class_member_required, class_teacher_required
from .models import Project
from django.core.paginator import Paginator
from .forms import ProjectForm, ProjectTaskFormSet


@login_required
@class_member_required
def project_list(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    # Filtros simples
    state = request.GET.get('state', '')
    q = request.GET.get('q', '')
    projects_qs = Project.objects.filter(student_class=turma)
    if state:
        projects_qs = projects_qs.filter(state=state)
    if q:
        projects_qs = projects_qs.filter(title__icontains=q)

    projects_qs = projects_qs.order_by('-created_at')

    # Paginação
    paginator = Paginator(projects_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'projects/project_list.html', {
        'turma': turma,
        'projects': page_obj,
        'state': state,
        'q': q,
    })


@login_required
@class_teacher_required
def project_create(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.student_class = turma
            project.save()
            form.save_m2m()
            formset = ProjectTaskFormSet(request.POST, instance=project)
            if formset.is_valid():
                formset.save()
            # Mesmo que o formset tenha erros, prosseguir para detalhe do projeto criado
            messages.success(request, _('Projeto criado.'))
            return redirect('projects:project_detail', class_id=turma.id, project_id=project.id)
        else:
            formset = ProjectTaskFormSet(request.POST)
    else:
        form = ProjectForm()
        formset = ProjectTaskFormSet()
    return render(request, 'projects/project_form.html', {
        'turma': turma,
        'form': form,
        'formset': formset,
    })


@login_required
@class_member_required
def project_detail(request, class_id, project_id):
    turma = get_object_or_404(Class, id=class_id)
    project = get_object_or_404(Project, id=project_id, student_class=turma)
    
    # Check if user can edit (member of project or teacher/admin)
    user = request.user
    is_member = project.members.filter(id=user.id).exists()
    is_teacher = hasattr(user, 'role') and user.role == 'professor' and turma in user.classes_taught.all()
    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    can_edit = is_member or is_teacher or is_admin
    
    return render(request, 'projects/project_detail.html', {
        'turma': turma,
        'project': project,
        'can_edit': can_edit,
    })


@login_required
@class_member_required
def project_edit(request, class_id, project_id):
    """Edit an existing project. Only members, teachers, or admins can edit."""
    turma = get_object_or_404(Class, id=class_id)
    project = get_object_or_404(Project, id=project_id, student_class=turma)
    user = request.user
    
    # Permission check: member of project, teacher of class, or admin
    is_member = project.members.filter(id=user.id).exists()
    is_teacher = hasattr(user, 'role') and user.role == 'professor' and turma in user.classes_taught.all()
    is_admin = user.is_superuser or (hasattr(user, 'role') and user.role == 'admin')
    
    if not (is_member or is_teacher or is_admin):
        messages.error(request, _('Não tens permissão para editar este projeto.'))
        return redirect('projects:project_detail', class_id=class_id, project_id=project_id)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        formset = ProjectTaskFormSet(request.POST, instance=project)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _('Projeto atualizado.'))
            return redirect('projects:project_detail', class_id=class_id, project_id=project_id)
        else:
            messages.error(request, _('Corrige os erros abaixo.'))
    else:
        form = ProjectForm(instance=project)
        formset = ProjectTaskFormSet(instance=project)
    
    return render(request, 'projects/project_form.html', {
        'turma': turma,
        'form': form,
        'formset': formset,
        'project': project,
        'is_edit': True,
    })


# Create your views here.
