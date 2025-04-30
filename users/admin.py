from django.contrib import admin
from .models import User, PreApprovedStudent
from impersonate.admin import UserAdminImpersonateMixin

@admin.register(User)
class UserAdmin(UserAdminImpersonateMixin, admin.ModelAdmin):
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'status', 
        'role',
        'is_staff'
    )
    list_filter = ('status', 'role', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

@admin.register(PreApprovedStudent)
class PreApprovedStudentAdmin(admin.ModelAdmin):
    list_display = ('email', 'class_instance', 'status', 'added_by', 'date_added', 'claimed_by', 'date_claimed')
    list_filter = ('status', 'class_instance', 'date_added')
    search_fields = ('email', 'class_instance__name', 'added_by__username', 'claimed_by__username')
    ordering = ('-date_added',)
    readonly_fields = ('date_added', 'date_claimed', 'claimed_by')
    autocomplete_fields = ['class_instance', 'added_by', 'claimed_by']
