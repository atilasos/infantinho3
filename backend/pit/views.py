from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.utils.decorators import method_decorator

from classes.models import Class
from users.decorators import group_required
from .models import IndividualPlan
from .forms import (
    IndividualPlanForm,
    PlanTaskFormSet,
    StudentEvaluationForm,
    TeacherEvaluationForm,
)

from core.notifications import dispatch_notification


def _teacher_emails(turma):
    return [teacher.email for teacher in turma.teachers.all() if teacher.email]


def _notify_teachers_submission(request, plan):
    recipients = _teacher_emails(plan.student_class)
    subject = _('[Infantinho] Novo PIT submetido por {student}').format(
        student=plan.student.get_full_name() or plan.student.username
    )
    plan_url = request.build_absolute_uri(
        reverse('pit:teacher_plan_list', args=[plan.student_class.id])
    )
    message = _(
        'O aluno {student} submeteu o PIT "{period}" da turma {class_name}.\n'
        'Revise e aprove em: {url}'
    ).format(
        student=plan.student.get_full_name() or plan.student.username,
        period=plan.period_label,
        class_name=plan.student_class.name,
        url=plan_url,
    )
    dispatch_notification(
        subject=subject,
        message=message,
        recipients=recipients,
        category='pit_submission',
        metadata={'plan_id': plan.id, 'class_id': plan.student_class_id},
    )


def _notify_student_status(request, plan, approved):
    if not plan.student.email:
        return
    plan_url = request.build_absolute_uri(
        reverse('pit:plan_edit', args=[plan.student_class.id, plan.id])
    )
    if approved:
        subject = _('[Infantinho] O teu PIT foi aprovado')
        message = _(
            'O teu PIT "{period}" da turma {class_name} foi aprovado pelo professor.\n'
            'Podes continuar o acompanhamento em: {url}'
        )
    else:
        subject = _('[Infantinho] O teu PIT foi devolvido para ajustes')
        message = _(
            'O teu PIT "{period}" da turma {class_name} foi devolvido para ajustes.\n'
            'Revê o plano em: {url}'
        )
    dispatch_notification(
        subject=subject,
        message=message.format(
            period=plan.period_label,
            class_name=plan.student_class.name,
            url=plan_url,
        ),
        recipients=[plan.student.email],
        category='pit_student_status',
        metadata={
            'plan_id': plan.id,
            'class_id': plan.student_class_id,
            'approved': approved,
        },
    )


def _notify_teachers_self_evaluation(request, plan):
    recipients = _teacher_emails(plan.student_class)
    subject = _('[Infantinho] Autoavaliação submetida por {student}').format(
        student=plan.student.get_full_name() or plan.student.username
    )
    plan_url = request.build_absolute_uri(
        reverse('pit:teacher_plan_list', args=[plan.student_class.id])
    )
    message = _(
        'O aluno {student} registou a autoavaliação do PIT "{period}" na turma {class_name}.\n'
        'Consulte os comentários em: {url}'
    ).format(
        student=plan.student.get_full_name() or plan.student.username,
        period=plan.period_label,
        class_name=plan.student_class.name,
        url=plan_url,
    )
    dispatch_notification(
        subject=subject,
        message=message,
        recipients=recipients,
        category='pit_self_evaluation',
        metadata={'plan_id': plan.id, 'class_id': plan.student_class_id},
    )


def _notify_student_teacher_eval(request, plan):
    if not plan.student.email:
        return
    plan_url = request.build_absolute_uri(
        reverse('pit:plan_edit', args=[plan.student_class.id, plan.id])
    )
    subject = _('[Infantinho] O professor avaliou o teu PIT')
    message = _(
        'O professor registou a avaliação do PIT "{period}" da turma {class_name}.\n'
        'Lê o feedback em: {url}'
    ).format(
        period=plan.period_label,
        class_name=plan.student_class.name,
        url=plan_url,
    )
    dispatch_notification(
        subject=subject,
        message=message,
        recipients=[plan.student.email],
        category='pit_teacher_evaluation',
        metadata={'plan_id': plan.id, 'class_id': plan.student_class_id},
    )


@login_required
@group_required('aluno')
def my_current_plan_redirect(request):
    turma_id = request.GET.get('class_id')
    if not turma_id:
        messages.error(request, _('É necessária uma turma.'))
        return redirect('classes:class_list')
    turma = get_object_or_404(Class, id=turma_id)
    plan = (
        IndividualPlan.objects
        .filter(student=request.user, student_class=turma)
        .order_by('-start_date', '-created_at')
        .first()
    )
    if plan:
        return redirect('pit:plan_edit', class_id=turma.id, plan_id=plan.id)
    return redirect('pit:plan_create', class_id=turma.id)


@login_required
@group_required('aluno')
def plan_create(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        form = IndividualPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.student = request.user
            plan.student_class = turma
            plan.save()
            formset = PlanTaskFormSet(request.POST, instance=plan)
            if formset.is_valid():
                formset.save()
                messages.success(request, _('PIT guardado.'))
                return redirect('pit:plan_edit', class_id=turma.id, plan_id=plan.id)
        else:
            formset = PlanTaskFormSet(request.POST)
    else:
        form = IndividualPlanForm()
        formset = PlanTaskFormSet()
    return render(request, 'pit/plan_form.html', {
        'turma': turma,
        'form': form,
        'formset': formset,
        'is_create': True,
    })


@login_required
@group_required('aluno')
def plan_edit(request, class_id, plan_id):
    turma = get_object_or_404(Class, id=class_id)
    plan = get_object_or_404(IndividualPlan, id=plan_id, student=request.user, student_class=turma)
    if request.method == 'POST':
        form = IndividualPlanForm(request.POST, instance=plan)
        formset = PlanTaskFormSet(request.POST, instance=plan)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _('PIT atualizado.'))
            if 'submit' in request.POST:
                plan.status = IndividualPlan.PlanStatus.SUBMITTED
                plan.save(update_fields=['status'])
                messages.success(request, _('PIT submetido para aprovação.'))
                _notify_teachers_submission(request, plan)
            return redirect('pit:plan_edit', class_id=turma.id, plan_id=plan.id)
    else:
        form = IndividualPlanForm(instance=plan)
        formset = PlanTaskFormSet(instance=plan)
    return render(request, 'pit/plan_form.html', {
        'turma': turma,
        'form': form,
        'formset': formset,
        'plan': plan,
        'is_create': False,
    })


@login_required
@group_required('aluno')
def plan_self_evaluate(request, class_id, plan_id):
    turma = get_object_or_404(Class, id=class_id)
    plan = get_object_or_404(IndividualPlan, id=plan_id, student=request.user, student_class=turma)

    if plan.status in [IndividualPlan.PlanStatus.DRAFT, IndividualPlan.PlanStatus.SUBMITTED]:
        messages.warning(request, _('A autoavaliação só fica disponível após a aprovação do PIT.'))
        return redirect('pit:plan_edit', class_id=turma.id, plan_id=plan.id)

    if request.method == 'POST':
        form = StudentEvaluationForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save(commit=False)
            if plan.status != IndividualPlan.PlanStatus.EVALUATED:
                plan.status = IndividualPlan.PlanStatus.CONCLUDED
            plan.save(update_fields=['self_evaluation', 'status', 'updated_at'])
            messages.success(request, _('Autoavaliação registada. Obrigado pela reflexão!'))
            _notify_teachers_self_evaluation(request, plan)
            return redirect('pit:plan_edit', class_id=turma.id, plan_id=plan.id)
    else:
        form = StudentEvaluationForm(instance=plan)

    return render(request, 'pit/plan_self_evaluation.html', {
        'turma': turma,
        'plan': plan,
        'form': form,
    })


@login_required
@group_required('professor')
def plan_teacher_evaluate(request, class_id, plan_id):
    turma = get_object_or_404(Class, id=class_id)
    plan = get_object_or_404(IndividualPlan, id=plan_id, student_class=turma)

    if request.user not in turma.teachers.all():
        messages.error(request, _('Apenas professores da turma podem avaliar este PIT.'))
        return redirect('pit:teacher_plan_list', class_id=turma.id)

    if plan.status in [IndividualPlan.PlanStatus.DRAFT, IndividualPlan.PlanStatus.SUBMITTED]:
        messages.warning(request, _('Aguarde o aluno concluir ou autoavaliar o PIT antes de registar a avaliação.'))
        return redirect('pit:teacher_plan_list', class_id=turma.id)

    if request.method == 'POST':
        form = TeacherEvaluationForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.status = IndividualPlan.PlanStatus.EVALUATED
            plan.save(update_fields=['teacher_evaluation', 'status', 'updated_at'])
            messages.success(request, _('Avaliação do professor registada.'))
            _notify_student_teacher_eval(request, plan)
            return redirect('pit:teacher_plan_list', class_id=turma.id)
    else:
        form = TeacherEvaluationForm(instance=plan)

    return render(request, 'pit/plan_teacher_evaluation.html', {
        'turma': turma,
        'plan': plan,
        'form': form,
    })


class TeacherPlanListView(View):
    @method_decorator(login_required)
    @method_decorator(group_required('professor'))
    def get(self, request, class_id):
        turma = get_object_or_404(Class, id=class_id)
        plans = IndividualPlan.objects.filter(student_class=turma).select_related('student').order_by('-created_at')
        return render(request, 'pit/plan_list_teacher.html', {
            'turma': turma,
            'plans': plans,
        })


class TeacherPlanApproveView(View):
    @method_decorator(login_required)
    @method_decorator(group_required('professor'))
    def post(self, request, class_id, plan_id):
        turma = get_object_or_404(Class, id=class_id)
        plan = get_object_or_404(IndividualPlan, id=plan_id, student_class=turma)
        action = request.POST.get('action')
        if action == 'approve':
            plan.status = IndividualPlan.PlanStatus.APPROVED
            plan.save(update_fields=['status'])
            messages.success(request, _('PIT aprovado.'))
            _notify_student_status(request, plan, approved=True)
        elif action == 'return':
            plan.status = IndividualPlan.PlanStatus.DRAFT
            plan.save(update_fields=['status'])
            messages.info(request, _('PIT devolvido para revisão.'))
            _notify_student_status(request, plan, approved=False)
        return redirect('pit:teacher_plan_list', class_id=turma.id)


# Create your views here.
