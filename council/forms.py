from django import forms
from .models import CouncilDecision, StudentProposal


class CouncilDecisionForm(forms.ModelForm):
    class Meta:
        model = CouncilDecision
        fields = ['date', 'description', 'category', 'status', 'responsible']


class StudentProposalForm(forms.ModelForm):
    class Meta:
        model = StudentProposal
        fields = ['text']


