from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView
from django.views import View
from .models import ChecklistStatus, ChecklistTemplate, ChecklistItem, ChecklistMark
from django.contrib import messages
from classes.models import Class
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

# Create your views here.

@method_decorator(login_required, name='dispatch')
class MyChecklistsView(ListView):
    model = ChecklistStatus
    template_name = 'checklists/my_checklists.html'
    context_object_name = 'checklists'

    def get_queryset(self):
        return ChecklistStatus.objects.filter(aluno=self.request.user).select_related('template')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_status = context['checklists']
        context['ativas'] = [s for s in all_status if s.percent_complete < 100]
        context['concluidas'] = [s for s in all_status if s.percent_complete >= 100]
        return context

class ChecklistDetailView(View):
    template_name = 'checklists/checklist_detail.html'

    @method_decorator(login_required)
    def get(self, request, template_id):
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        status = get_object_or_404(ChecklistStatus, template=template, aluno=request.user)
        items = ChecklistItem.objects.filter(template=template).order_by('ordem')
        marks_qs = ChecklistMark.objects.filter(status=status).order_by('-criado_em')
        marks_by_item = {}
        for m in marks_qs:
            if m.item_id not in marks_by_item:
                marks_by_item[m.item_id] = m
        items_and_marks = [(item, marks_by_item.get(item.id)) for item in items]
        highlight = request.GET.get('highlight')
        return render(request, self.template_name, {
            'template': template,
            'status': status,
            'items_and_marks': items_and_marks,
            'highlight': highlight,
            'total': items.count(),
        })

    @method_decorator(login_required)
    def post(self, request, template_id):
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        status = get_object_or_404(ChecklistStatus, template=template, aluno=request.user)
        item_id = request.POST.get('item_id')
        estado = request.POST.get('estado')
        comentario = request.POST.get('comentario', '')
        item = get_object_or_404(ChecklistItem, id=item_id, template=template)
        # Cria novo mark (histórico)
        mark = ChecklistMark.objects.create(
            status=status,
            item=item,
            estado=estado,
            comentario=comentario,
            marcado_por=request.user,
            validacao_professor=False
        )
        # Notificar professores da turma
        turma = status.classe
        profs = turma.teachers.all()
        prof_emails = [p.email for p in profs if p.email]
        if prof_emails:
            subject = f"[Infantinho] {request.user.get_full_name() or request.user.username} marcou um objetivo em {template.nome} ({template.disciplina})"
            url = request.build_absolute_uri(reverse('checklists:checklist_turma', args=[turma.id, template.id]))
            message = f"O aluno {request.user.get_full_name() or request.user.username} atualizou o item '{item.descricao}' para '{mark.get_estado_display()}'.\nComentário: {comentario}\n\nVer visão coletiva: {url}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, prof_emails, fail_silently=True)
        messages.success(request, 'Objetivo atualizado com sucesso!')
        return redirect(f'{request.path}?highlight={item_id}')

def is_prof_or_admin(user, turma):
    if not user.is_authenticated:
        return False
    if hasattr(user, 'role') and user.role == 'admin':
        return True
    return hasattr(user, 'role') and user.role == 'professor' and turma in user.classes_taught.all()

@method_decorator(login_required, name='dispatch')
class ChecklistTurmaView(View):
    template_name = 'checklists/checklist_turma.html'

    def get(self, request, class_id, template_id):
        turma = get_object_or_404(Class, id=class_id)
        if not is_prof_or_admin(request.user, turma):
            messages.error(request, 'Acesso restrito a professores da turma ou admin.')
            return redirect('class_detail', class_id=class_id)
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        alunos = turma.students.all().order_by('first_name', 'last_name')
        itens = ChecklistItem.objects.filter(template=template).order_by('ordem')
        status_map = {s.aluno_id: s for s in ChecklistStatus.objects.filter(template=template, classe=turma)}
        marks = ChecklistMark.objects.filter(status__in=status_map.values()).order_by('item_id', '-criado_em')
        marks_by_aluno_item = {}
        for mark in marks:
            key = (mark.status.aluno_id, mark.item_id)
            if key not in marks_by_aluno_item:
                marks_by_aluno_item[key] = mark
        # Progresso individual
        progresso_individual = {}
        for aluno in alunos:
            done = 0
            for item in itens:
                mark = marks_by_aluno_item.get((aluno.id, item.id))
                if mark and mark.estado == 'concluido':
                    done += 1
            total = len(itens)
            progresso_individual[aluno.id] = int((done / total) * 100) if total > 0 else 0
        # Progresso coletivo
        if alunos:
            progresso_coletivo = int(sum(progresso_individual.values()) / len(alunos))
        else:
            progresso_coletivo = 0
        context = {
            'turma': turma,
            'template': template,
            'alunos': alunos,
            'itens': itens,
            'marks_by_aluno_item': marks_by_aluno_item,
            'progresso_individual': progresso_individual,
            'progresso_coletivo': progresso_coletivo,
        }
        return render(request, self.template_name, context)

    def post(self, request, class_id, template_id):
        turma = get_object_or_404(Class, id=class_id)
        if not is_prof_or_admin(request.user, turma):
            messages.error(request, 'Acesso restrito a professores da turma ou admin.')
            return redirect('class_detail', class_id=class_id)
        template = get_object_or_404(ChecklistTemplate, id=template_id)
        aluno_id = request.POST.get('aluno_id')
        item_id = request.POST.get('item_id')
        estado = request.POST.get('estado')
        comentario = request.POST.get('comentario', '')
        if not (aluno_id and item_id and estado):
            messages.error(request, 'Dados insuficientes para validar/retificar.')
            return redirect(request.path)
        aluno = get_object_or_404(turma.students, id=aluno_id)
        item = get_object_or_404(ChecklistItem, id=item_id, template=template)
        status = get_object_or_404(ChecklistStatus, template=template, classe=turma, aluno=aluno)
        mark = ChecklistMark.objects.create(
            status=status,
            item=item,
            estado=estado,
            comentario=comentario,
            marcado_por=request.user,
            validacao_professor=True
        )
        # Notificar aluno
        if aluno.email:
            subject = f"[Infantinho] Sua marcação foi validada/retificada pelo professor em {template.nome} ({template.disciplina})"
            url = request.build_absolute_uri(reverse('checklists:checklist_detail', args=[template.id]))
            message = f"O professor {request.user.get_full_name() or request.user.username} validou/retificou o item '{item.descricao}' para '{mark.get_estado_display()}'.\nComentário: {comentario}\n\nVeja sua lista: {url}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [aluno.email], fail_silently=True)
        messages.success(request, f'Marcação validada/retificada para {aluno.get_full_name() or aluno.username}.')
        return redirect(request.path)

class HelpView(TemplateView):
    template_name = 'checklists/help.html'
