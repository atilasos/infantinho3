"""Custom middleware for user-specific constraints."""
from __future__ import annotations

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """Redirect users flagged with ``must_change_password`` to update credentials."""

    def __init__(self, get_response):
        self.get_response = get_response
        self._allowed_paths = None

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and getattr(request.user, 'must_change_password', False)
            and not self._is_path_allowed(request)
        ):
            return redirect('users:force_password_change')

        return self.get_response(request)

    def _is_path_allowed(self, request) -> bool:
        path = request.path
        if path.startswith(getattr(settings, 'STATIC_URL', '/static/')):
            return True
        media_url = getattr(settings, 'MEDIA_URL', None)
        if media_url and path.startswith(media_url):
            return True

        allowed_paths = self._get_allowed_paths()
        if path in allowed_paths:
            return True

        if request.method == 'POST' and path in allowed_paths:
            return True

        return False

    def _get_allowed_paths(self) -> set[str]:
        if self._allowed_paths is None:
            self._allowed_paths = {
                reverse('users:force_password_change'),
                reverse('users:logout'),
                reverse('users:password_reset'),
            }
            login_url = getattr(settings, 'LOGIN_URL', None)
            if login_url:
                self._allowed_paths.add(str(login_url))
        return self._allowed_paths
