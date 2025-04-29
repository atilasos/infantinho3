from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _

def group_required(*group_names):
    """Requires user membership in at least one of the groups passed in."""
    def check_groups(user):
        if user.is_authenticated:
            # Check if the user belongs to any of the specified groups
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        # Optionally, redirect to login or return a specific response
        # For simplicity, returning False will let user_passes_test handle redirection/403
        return False

    # Use user_passes_test decorator, which handles login redirection or 403
    # login_url: where to redirect if not logged in
    # redirect_field_name: parameter to pass for redirection after login
    # We could customize the failure view by passing a custom function 
    # instead of None to user_passes_test, but the default 403 is often sufficient.
    return user_passes_test(check_groups, login_url='users:login_choice')

# Example of how to use it in views.py:
# from .decorators import group_required
#
# @login_required
# @group_required('professor', 'administrador')
# def my_admin_or_teacher_view(request):
#     ... 