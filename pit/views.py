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
from .forms import IndividualPlanForm, PlanTaskFormSet


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
        elif action == 'return':
            plan.status = IndividualPlan.PlanStatus.DRAFT
            plan.save(update_fields=['status'])
            messages.info(request, _('PIT devolvido para revisão.'))
        return redirect('pit:teacher_plan_list', class_id=turma.id)


# Create your views here.
