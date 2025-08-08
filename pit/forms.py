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


PlanTaskFormSet = forms.inlineformset_factory(
    parent_model=IndividualPlan,
    model=PlanTask,
    form=PlanTaskForm,
    extra=3,
    can_delete=True,
)


