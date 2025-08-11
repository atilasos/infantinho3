from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from .models import FeedbackItem
from users.permissions import is_admin
from .forms import FeedbackItemForm
# from classes.models import Class # Import Class if you implement dynamic queryset filtering in the form

@login_required
def feedback_submit_view(request):
    if request.method == 'POST':
        form = FeedbackItemForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
                feedback.author = request.user
            # Se o formulário não incluir a turma e quiser associar a turma ativa do user:
            # if hasattr(request.user, 'active_class') and request.user.active_class:
            #     feedback.turma = request.user.active_class
            feedback.save()
            messages.success(request, _('O seu feedback foi enviado com sucesso. Obrigado!'))
            return redirect(reverse_lazy('infantinho_feedback:feedback_thank_you'))
        else:
            messages.error(request, _('Por favor, corrija os erros abaixo.'))
    else:
        form = FeedbackItemForm()

    if is_admin(request.user):
        feedback_list_qs = FeedbackItem.objects.all().order_by('-created_at')
    elif request.user.is_authenticated:
        feedback_list_qs = FeedbackItem.objects.filter(author=request.user).order_by('-created_at')
    else:
        feedback_list_qs = FeedbackItem.objects.none()

    feedback_column_choices = FeedbackItem.CATEGORY_CHOICES
    feedbacks_by_category = {category_key: [] for category_key, _ in feedback_column_choices}

    for item in feedback_list_qs:
        if item.category in feedbacks_by_category:
            feedbacks_by_category[item.category].append(item)

    # Para garantir que a ordem das colunas no template é a mesma de CATEGORY_CHOICES,
    # passamos feedback_column_choices que é uma lista ordenada.
    # E o template irá iterar por feedback_column_choices para obter a chave e o nome da coluna.

    context = {
        'form': form,
        'feedback_list': feedback_list_qs, # Mantido para possível uso, ou se a vista de colunas for opcional
        'feedback_column_choices': feedback_column_choices,
        'feedbacks_by_category': feedbacks_by_category,
    }
    return render(request, 'infantinho_feedback/feedback_form.html', context)

def feedback_thank_you_view(request):
    return render(request, 'infantinho_feedback/feedback_thank_you.html')

@require_POST
@login_required
def feedback_update_status_view(request, pk):
    if not (request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin')):
        messages.error(request, _("Não tem permissão para realizar esta ação."))
        return redirect(reverse_lazy('infantinho_feedback:feedback_submit'))

    feedback_item = get_object_or_404(FeedbackItem, pk=pk)
    new_status = request.POST.get('status')

    if new_status in [status[0] for status in FeedbackItem.STATUS_CHOICES]:
        feedback_item.status = new_status
        feedback_item.save()
        messages.success(request, _("Status do feedback atualizado com sucesso."))
    else:
        messages.error(request, _("Status inválido fornecido."))
    
    return redirect(reverse_lazy('infantinho_feedback:feedback_submit'))

@require_POST
@login_required
def feedback_delete_view(request, pk):
    if not (request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin')):
        messages.error(request, _("Não tem permissão para realizar esta ação."))
        return redirect(reverse_lazy('infantinho_feedback:feedback_submit'))

    feedback_item = get_object_or_404(FeedbackItem, pk=pk)
    feedback_item.delete()
    messages.success(request, _("Item de feedback apagado com sucesso."))
    
    return redirect(reverse_lazy('infantinho_feedback:feedback_submit'))

# Se quiser uma vista para os utilizadores verem o seu próprio feedback:
# @login_required
# def my_feedback_list_view(request):
#     feedback_items = FeedbackItem.objects.filter(author=request.user).order_by('-created_at')
#     return render(request, 'infantinho_feedback/my_feedback_list.html', {'feedback_items': feedback_items})
