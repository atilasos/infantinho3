"""Base permission classes for MEM role-aware access control."""
from rest_framework.permissions import BasePermission


class IsAuthenticatedAndActive(BasePermission):
    """Allow access only to authenticated users that are not guests."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and getattr(user, 'is_active', False)):
            return False
        is_guest = getattr(user, 'is_guest', None)
        if callable(is_guest) and is_guest():
            return False
        return True
