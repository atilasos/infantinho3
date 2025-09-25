"""Projeto: middleware para auditoria de ações relevantes."""
from __future__ import annotations

import json
from typing import Callable

from django.http import HttpRequest, HttpResponse


class AuditLogMiddleware:
    """Regista metadados de pedidos POST/PATCH/DELETE para auditoria."""

    SENSITIVE_HEADERS = {'authorization', 'cookie'}

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        try:
            self._log_request_response(request, response)
        except Exception:  # pragma: no cover
            # nunca quebrar o fluxo por causa do audit logger
            pass
        return response

    def _log_request_response(self, request: HttpRequest, response: HttpResponse) -> None:
        if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            return

        user = getattr(request, 'user', None)

        payload = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user_id': getattr(user, 'id', None),
            'user_role': getattr(user, 'role', None),
            'query_params': request.GET.dict(),
        }

        if request.body:
            try:
                payload['body'] = json.loads(request.body.decode('utf-8'))
            except Exception:
                payload['body'] = '<<non-json>>'

        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in self.SENSITIVE_HEADERS
        }
        payload['headers'] = headers

        # neste momento apenas enviamos para o logger "audit"
        from logging import getLogger

        logger = getLogger('audit')
        logger.info('audit_event', extra={'payload': payload})

