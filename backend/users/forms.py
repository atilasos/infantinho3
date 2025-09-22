from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from .models import GuardianRelation

User = get_user_model()


class GuardianRegistrationForm(forms.ModelForm):
    """Formulário de registo para encarregados de educação."""

    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput,
        strip=False,
        help_text=_('Crie uma password com pelo menos 8 caracteres.'),
    )
    password2 = forms.CharField(
        label=_('Confirmar password'),
        widget=forms.PasswordInput,
        strip=False,
    )
    student_number = forms.CharField(
        label=_('Número do aluno'),
        max_length=32,
        help_text=_('Introduza o número escolar partilhado pela escola.'),
    )
    relationship = forms.CharField(
        label=_('Relação com o aluno'),
        required=False,
        max_length=50,
        help_text=_('Ex.: Mãe, Pai, Encarregado Legal'),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': _('Primeiro nome'),
            'last_name': _('Apelido'),
            'email': _('Email'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = None
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} form-control".strip()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('Já existe uma conta com este email.'))
        return email

    def clean_student_number(self):
        number = self.cleaned_data['student_number'].strip()
        try:
            student = User.objects.get(student_number=number)
        except User.DoesNotExist as exc:
            raise forms.ValidationError(_('Não encontrámos um aluno com esse número.')) from exc

        if student.role != 'aluno':
            raise forms.ValidationError(_('O número indicado não pertence a um aluno ativo.'))

        self.student = student
        return number

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', _('As passwords não coincidem.'))
        if password1:
            validate_password(password1, user=self.instance)
        return cleaned

    def save(self, commit: bool = True):
        guardian = super().save(commit=False)
        guardian.username = self.cleaned_data['email']
        guardian.email = self.cleaned_data['email']
        guardian.is_active = True
        guardian.status = 'ativo'
        guardian.set_password(self.cleaned_data['password1'])

        if commit:
            guardian.save()
            try:
                guardian.promote_to_role('encarregado')
            except Exception:
                guardian.role = 'encarregado'
                guardian.save(update_fields=['role'])
        return guardian

    def guardian_relation_exists(self) -> bool:
        if not self.student:
            return False
        return GuardianRelation.objects.filter(
            aluno=self.student,
            encarregado__email__iexact=self.cleaned_data.get('email', ''),
        ).exists()
