from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'status', 'role')
    list_filter = ('status', 'role')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_editable = ('status', 'role')
    ordering = ('-date_joined',)
