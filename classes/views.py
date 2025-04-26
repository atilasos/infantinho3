from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from classes.models import Class
from users.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django import forms

# Create your views here.

@login_required
def class_list(request):
    # Mostra apenas as turmas em que o utilizador é professor
    turmas = Class.objects.filter(teachers=request.user)
    return render(request, 'classes/class_list.html', {'turmas': turmas})

@login_required
def class_detail(request, class_id):
    turma = Class.objects.get(id=class_id)
    return render(request, 'classes/class_detail.html', {'turma': turma})

@login_required
def add_student(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    # Só professores da turma podem aceder
    if request.user.role != 'professor' or request.user not in turma.teachers.all():
        messages.error(request, 'Acesso negado.')
        return redirect('class_detail', class_id=class_id)

    convidados = User.objects.filter(status='convidado', role__isnull=True)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        user.promote_to_role('aluno')
        turma.students.add(user)
        messages.success(request, f'{user.get_full_name() or user.username} promovido a aluno e adicionado à turma.')
        return redirect('class_detail', class_id=class_id)

    return render(request, 'classes/add_student.html', {'turma': turma, 'convidados': convidados})

class ClassCreateForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'year', 'teachers']
        widgets = {
            'teachers': forms.SelectMultiple(attrs={'size': 8}),
        }

@login_required
def manage_classes(request):
    if request.user.role not in ('admin', 'professor'):
        messages.error(request, 'Acesso restrito a administradores e professores.')
        return redirect('class_list')

    if request.method == 'POST':
        form = ClassCreateForm(request.POST)
        if form.is_valid():
            turma = form.save()
            messages.success(request, f'Turma "{turma.name}" criada com sucesso!')
            return redirect('manage_classes')
    else:
        form = ClassCreateForm()
        # Limitar professores possíveis
        form.fields['teachers'].queryset = User.objects.filter(role='professor')

    turmas = Class.objects.all().order_by('-year', 'name')
    return render(request, 'classes/manage_classes.html', {'form': form, 'turmas': turmas})

@login_required
def landing_page(request):
    return render(request, 'classes/landing.html')
