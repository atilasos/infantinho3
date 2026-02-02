from django import forms
from django.utils.translation import gettext_lazy as _


class ChatForm(forms.Form):
    """
    Form for submitting a message to the AI assistant.
    """
    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Escreve a tua mensagem aqui...'),
            'class': 'form-control',
        }),
        max_length=4000,
        help_text=_('Máximo 4000 caracteres.')
    )

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise forms.ValidationError(_('A mensagem não pode estar vazia.'))
        return message
