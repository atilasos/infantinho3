from django import forms
from django.utils.translation import gettext_lazy as _

from .models import FeedbackItem

class FeedbackItemForm(forms.ModelForm):
    class Meta:
        model = FeedbackItem
        fields = ['category', 'content', 'page_url', 'turma']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': _('Descreva detalhadamente o seu feedback aqui...')}),
            'page_url': forms.TextInput(attrs={'placeholder': _('Ex: /diario/turma/1/')}),
        }
        labels = {
            'category': _('Tipo de Feedback'),
            'content': _('O seu Feedback'),
            'page_url': _('Página Específica (Opcional)'),
            'turma': _('Turma Associada (Opcional)'),
        }
        help_texts = {
            'page_url': _('Se o seu feedback se refere a uma página específica, por favor, copie o URL (endereço da página) aqui.'),
            'turma': _('Se o seu feedback é específico para uma das suas turmas, selecione-a aqui.'),
        }

    def __init__(self, *args, **kwargs):
        # O utilizador que submete o formulário pode ser passado para o form para filtrar as turmas
        # Ex: self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['category'].empty_label = _("Selecione uma categoria")

        if 'turma' in self.fields:
            self.fields['turma'].required = False
            self.fields['turma'].empty_label = _("Nenhuma (feedback geral)")
            # Se um utilizador for passado para o formulário, pode filtrar o queryset de turmas:
            # if self.user and hasattr(self.user, 'get_teacher_classes'): # Exemplo
            #     self.fields['turma'].queryset = self.user.get_teacher_classes()
            # elif self.user and hasattr(self.user, 'get_student_classes'): # Exemplo
            #     self.fields['turma'].queryset = self.user.get_student_classes()
            # else: # Para admins ou users sem turmas específicas, ou se não filtrar
            #     self.fields['turma'].queryset = Class.objects.all()

        # O campo 'author' será preenchido automaticamente na view 