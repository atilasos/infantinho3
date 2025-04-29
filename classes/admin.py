from django.contrib import admin
from .models import Class

# Register your models here.
# admin.site.register(Class) # Replaced with ModelAdmin registration below

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """Admin configuration for the Class model."""
    list_display = ('name', 'year', 'get_teacher_count', 'get_student_count')
    list_filter = ('year',)
    search_fields = ('name', 'year') # Define search fields
    filter_horizontal = ('teachers', 'students') # Better interface for M2M
    ordering = ('-year', 'name')

    # Methods to display counts in list view
    @admin.display(description='Teachers')
    def get_teacher_count(self, obj):
        return obj.teachers.count()

    @admin.display(description='Students')
    def get_student_count(self, obj):
        return obj.students.count()
