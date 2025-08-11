from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from classes.models import Class
from users.decorators import group_required
from users.permissions import class_member_required, class_teacher_required
from .models import CouncilDecision, StudentProposal
from .forms import CouncilDecisionForm, StudentProposalForm


@login_required
@class_member_required
def decision_list(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    decisions = CouncilDecision.objects.filter(student_class=turma).order_by('-date')
    proposals = StudentProposal.objects.filter(student_class=turma).order_by('-date_submitted')[:10]
    return render(request, 'council/decision_list.html', {
        'turma': turma,
        'decisions': decisions,
        'proposals': proposals,
    })


@login_required
@class_teacher_required
def decision_create(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        form = CouncilDecisionForm(request.POST)
        if form.is_valid():
            decision = form.save(commit=False)
            decision.student_class = turma
            decision.save()
            messages.success(request, _('Decisão registada.'))
            return redirect('council:decision_list', class_id=turma.id)
    else:
        form = CouncilDecisionForm()
    return render(request, 'council/decision_form.html', {'turma': turma, 'form': form})


@login_required
@class_member_required
def proposal_create(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        form = StudentProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.student_class = turma
            proposal.author = request.user
            proposal.save()
            messages.success(request, _('Proposta submetida.'))
            return redirect('council:decision_list', class_id=turma.id)
    else:
        form = StudentProposalForm()
    return render(request, 'council/proposal_form.html', {'turma': turma, 'form': form})


# Create your views here.
