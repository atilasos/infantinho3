# checklists/admin.py
from django.contrib import admin
from .models import ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark

# Inline configuration for Checklist Items within Checklist Templates
class ChecklistItemInline(admin.TabularInline):
    """Allows editing ChecklistItems directly within the ChecklistTemplate admin page."""
    model = ChecklistItem
    # Fields to display in the inline form
    fields = ('order', 'description', 'criteria', 'council_agreed') 
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
    list_display = ('name', 'subject', 'grade_level', 'item_count', 'updated_at') 
    # Fields to filter by in the sidebar
    list_filter = ('subject', 'grade_level') 
    # Fields to search by
    search_fields = ('name', 'subject', 'description') 
    # Include the inline form for managing items
    inlines = [ChecklistItemInline]

    @admin.display(description='Item Count')
    def item_count(self, obj):
        """Calculated field to show the number of items in the list view."""
        return obj.items.count()


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    """Admin configuration for ChecklistItem model (basic)."""
    # Useful for viewing all items across templates, though primarily edited via inline
    list_display = ('description', 'template', 'order', 'council_agreed')
    list_filter = ('template__subject', 'template__grade_level', 'council_agreed')
    search_fields = ('description', 'criteria', 'template__name')
    # Make template selectable via raw_id_fields for performance if many templates exist
    raw_id_fields = ('template',)
    list_editable = ('order',) # Allow editing order directly in the list view


@admin.register(ChecklistStatus)
class ChecklistStatusAdmin(admin.ModelAdmin):
    """Admin configuration for ChecklistStatus model."""
    list_display = ('student', 'template', 'student_class', 'percent_complete', 'updated_at')
    list_filter = ('student_class__name', 'template__subject', 'template__grade_level')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'template__name')
    # Use raw_id_fields for better performance with many users/templates/classes
    raw_id_fields = ('student', 'template', 'student_class')
    readonly_fields = ('percent_complete', 'updated_at') # These are calculated/automatic


@admin.register(ChecklistMark)
class ChecklistMarkAdmin(admin.ModelAdmin):
    """Admin configuration for ChecklistMark model."""
    list_display = ('item', 'get_student', 'mark_status', 'teacher_validated', 'marked_at', 'marked_by')
    list_filter = ('mark_status', 'teacher_validated', 'status__template__subject', 'status__student_class__name')
    search_fields = ('item__description', 'status__student__username', 'comment')
    # Use raw_id_fields for performance
    raw_id_fields = ('status', 'item', 'marked_by')
    readonly_fields = ('created_at', 'marked_at') # Automatic timestamps
    list_editable = ('mark_status', 'teacher_validated') # Allow quick updates

    @admin.display(description='Student', ordering='status__student')
    def get_student(self, obj):
        """Helper to display the student associated with the mark status."""
        return obj.status.student

# Note: Models were previously registered simply with admin.site.register(ModelName)
# The @admin.register decorator replaces that when using a ModelAdmin class.
