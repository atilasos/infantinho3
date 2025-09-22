from django import forms
from .models import Project, ProjectTask


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'product_description', 'members']


class ProjectTaskForm(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ['description', 'responsible', 'due_date', 'state', 'order']


ProjectTaskFormSet = forms.inlineformset_factory(
    parent_model=Project,
    model=ProjectTask,
    form=ProjectTaskForm,
    extra=3,
    can_delete=True,
)


