from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Checks if a user belongs to a specific group.
    Usage: {% if request.user|has_group:"professor" %}
    """
    # Superuser implicitly has all permissions / belongs to all groups
    if user.is_superuser:
        return True
    if user.is_authenticated:
        try:
            group = Group.objects.get(name=group_name)
            return group in user.groups.all()
        except Group.DoesNotExist:
            return False
    return False 