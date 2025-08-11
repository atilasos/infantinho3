from django.contrib import admin
from .models import CouncilDecision, StudentProposal


@admin.register(CouncilDecision)
class CouncilDecisionAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_class', 'date', 'category', 'status', 'responsible')
    list_filter = ('student_class', 'category', 'status')
    search_fields = ('description',)
    date_hierarchy = 'date'


@admin.register(StudentProposal)
class StudentProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_class', 'author', 'status', 'date_submitted')
    list_filter = ('student_class', 'status')
    search_fields = ('text', 'author__username')


# Register your models here.
