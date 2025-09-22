from django import forms
from .models import IndividualPlan, PlanTask


class IndividualPlanForm(forms.ModelForm):
    class Meta:
        model = IndividualPlan
        fields = [
            'period_label', 'start_date', 'end_date', 'general_objectives',
        ]


class PlanTaskForm(forms.ModelForm):
    class Meta:
        model = PlanTask
        fields = ['description', 'subject', 'state', 'evidence_link', 'order']


class StudentEvaluationForm(forms.ModelForm):
    class Meta:
        model = IndividualPlan
        fields = ['self_evaluation']
        widgets = {
            'self_evaluation': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }


class TeacherEvaluationForm(forms.ModelForm):
    class Meta:
        model = IndividualPlan
        fields = ['teacher_evaluation']
        widgets = {
            'teacher_evaluation': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
        }


PlanTaskFormSet = forms.inlineformset_factory(
    parent_model=IndividualPlan,
    model=PlanTask,
    form=PlanTaskForm,
    extra=3,
    can_delete=True,
)

