from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View

from classes.models import Class
from users.decorators import group_required
from .models import Project
from .forms import ProjectForm, ProjectTaskFormSet


@login_required
def project_list(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    # Qualquer membro da turma pode ver a lista
    projects = Project.objects.filter(student_class=turma).order_by('-created_at')
    return render(request, 'projects/project_list.html', {
        'turma': turma,
        'projects': projects,
    })


@login_required
@group_required('professor')
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
def project_detail(request, class_id, project_id):
    turma = get_object_or_404(Class, id=class_id)
    project = get_object_or_404(Project, id=project_id, student_class=turma)
    return render(request, 'projects/project_detail.html', {
        'turma': turma,
        'project': project,
    })


# Create your views here.
