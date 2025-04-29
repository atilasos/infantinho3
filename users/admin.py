from django.contrib import admin
from .models import User
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
    )
    list_filter = ('status', 'role')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
