from django.contrib import admin
from .models import IndividualPlan, PlanTask


@admin.register(IndividualPlan)
class IndividualPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'student_class', 'period_label', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'student_class')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'period_label')
    date_hierarchy = 'start_date'


@admin.register(PlanTask)
class PlanTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'description', 'subject', 'state', 'order')
    list_filter = ('state', 'subject')
    search_fields = ('description', 'plan__period_label', 'plan__student__username')
    ordering = ('plan', 'order')


# Register your models here.
