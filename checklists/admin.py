# checklists/admin.py
from django.contrib import admin
from .models import ChecklistTemplate, ChecklistItem, ChecklistMark, ChecklistStatus

# Inline configuration for Checklist Items within Checklist Templates
class ChecklistItemInline(admin.TabularInline):
    """Allows editing ChecklistItems directly within the ChecklistTemplate admin page."""
    model = ChecklistItem
    # Fields to display in the inline form
    fields = ('order', 'code', 'text') 
    # Extra forms to display for adding new items
    extra = 1 
    # Add ordering if needed, e.g., based on the 'order' field
    ordering = ('order',) 
    # Provide verbose name for clarity
    verbose_name = "Template Item"
    verbose_name_plural = "Template Items"


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for ChecklistTemplate model."""
    # Fields to display in the list view
    list_display = ('name', 'description') 
    # Fields to search by
    search_fields = ('name', 'description') 
    # Include the inline form for managing items
    inlines = [ChecklistItemInline]


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    """Admin configuration for ChecklistItem model (basic)."""
    # Useful for viewing all items across templates, though primarily edited via inline
    list_display = ('code', 'text', 'template', 'order')
    list_filter = ('template',)
    search_fields = ('code', 'text', 'template__name')
    list_editable = ('order',) # Allow editing order directly in the list view
    ordering = ('template', 'order')


@admin.register(ChecklistMark)
class ChecklistMarkAdmin(admin.ModelAdmin):
    """Admin configuration for ChecklistMark model."""
    list_display = ('get_student_username', 'item', 'mark_status', 'teacher_validated', 'marked_at', 'marked_by')
    list_filter = ('mark_status', 'teacher_validated', 'item__template', 'status_record__student_class', 'status_record__student')
    search_fields = ('status_record__student__username', 'status_record__student__first_name', 'item__code', 'item__text', 'comment')
    list_editable = ('mark_status', 'teacher_validated')
    autocomplete_fields = ['status_record', 'item', 'marked_by']
    ordering = ('-marked_at',)
    readonly_fields = ('marked_at',)

    @admin.display(description='Student', ordering='status_record__student__username')
    def get_student_username(self, obj):
        if obj.status_record and obj.status_record.student:
            return obj.status_record.student.username
        return 'N/A'

@admin.register(ChecklistStatus)
class ChecklistStatusAdmin(admin.ModelAdmin):
    """Admin configuration for ChecklistStatus model."""
    list_display = ('student', 'template', 'student_class', 'percent_complete', 'updated_at')
    list_filter = ('student_class', 'template', 'student')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'template__name', 'student_class__name')
    readonly_fields = ('percent_complete', 'updated_at')
    autocomplete_fields = ['student', 'template', 'student_class']
    ordering = ('student_class', 'student', 'template')

# Note: Models were previously registered simply with admin.site.register(ModelName)
# The @admin.register decorator replaces that when using a ModelAdmin class.
