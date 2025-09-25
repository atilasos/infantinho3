from django.contrib import admin
from .models import (
    IndividualPlan,
    PlanTask,
    PitTemplate,
    TemplateSection,
    TemplateSuggestion,
    PlanSuggestion,
    PlanSection,
    PlanLogEntry,
)


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


@admin.register(PitTemplate)
class PitTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'version', 'student_class', 'is_active', 'updated_at')
    list_filter = ('is_active', 'student_class', 'cycle_label')
    search_fields = ('name', 'cycle_label', 'student_class__name')
    ordering = ('-updated_at',)


@admin.register(TemplateSection)
class TemplateSectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'template', 'title', 'area_code', 'order')
    list_filter = ('template',)
    search_fields = ('title', 'template__name', 'area_code')
    ordering = ('template', 'order')


@admin.register(TemplateSuggestion)
class TemplateSuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'template', 'section', 'text', 'is_pending', 'order')
    list_filter = ('template', 'is_pending')
    search_fields = ('text', 'template__name')
    ordering = ('template', 'order')


@admin.register(PlanSuggestion)
class PlanSuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'origin', 'is_pending', 'order')
    list_filter = ('origin', 'is_pending')
    search_fields = ('text', 'plan__period_label', 'plan__student__username')
    ordering = ('plan', 'order')


@admin.register(PlanSection)
class PlanSectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'title', 'area_code', 'order')
    list_filter = ('area_code',)
    search_fields = ('title', 'plan__period_label')
    ordering = ('plan', 'order')


@admin.register(PlanLogEntry)
class PlanLogEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'action', 'actor', 'created_at')
    list_filter = ('action', 'actor')
    search_fields = ('plan__period_label', 'message')
    ordering = ('-created_at',)


# Register your models here.
