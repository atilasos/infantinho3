from django.contrib import admin
from .models import Project, ProjectTask


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'student_class', 'state', 'start_date', 'end_date')
    list_filter = ('student_class', 'state')
    search_fields = ('title', 'student_class__name')


@admin.register(ProjectTask)
class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'description', 'responsible', 'state', 'due_date', 'order')
    list_filter = ('state',)
    search_fields = ('description', 'project__title')


# Register your models here.
