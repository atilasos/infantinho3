from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, GuardianRelation, PreApprovedStudent
from impersonate.admin import UserAdminImpersonateMixin

class CustomUserAdmin(UserAdmin):
    # Add custom fields to display and edit in the admin
    # Ensure these fields are present in your User model
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'photo', 'status')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email', 'role', 'photo', 'status')}), # Ensure email is here for creation
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'status')
    list_filter = UserAdmin.list_filter + ('role', 'status')
    search_fields = UserAdmin.search_fields + ('role',)

admin.site.register(User, CustomUserAdmin)

@admin.register(GuardianRelation)
class GuardianRelationAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'encarregado', 'parentesco')
    search_fields = ('aluno__username', 'aluno__email', 'encarregado__username', 'encarregado__email')
    autocomplete_fields = ['aluno', 'encarregado']

@admin.register(PreApprovedStudent)
class PreApprovedStudentAdmin(admin.ModelAdmin):
    list_display = ('email', 'class_instance', 'status', 'added_by', 'date_added', 'claimed_by', 'date_claimed')
    list_filter = ('status', 'class_instance', 'date_added', 'date_claimed')
    search_fields = ('email', 'class_instance__name', 'added_by__username', 'claimed_by__username')
    readonly_fields = ('date_added', 'date_claimed', 'claimed_by')
    autocomplete_fields = ['class_instance', 'added_by', 'claimed_by'] # Assuming added_by and claimed_by are FKs to User

    fieldsets = (
        (None, {
            'fields': ('email', 'class_instance')
        }),
        ('Status', {
            'fields': ('status', 'claimed_by', 'date_claimed')
        }),
        ('Tracking', {
            'fields': ('added_by', 'date_added')
        }),
    )

    def get_queryset(self, request):
        # Optimize queries by prefetching related data
        return super().get_queryset(request).select_related('class_instance', 'added_by', 'claimed_by')
