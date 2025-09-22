"""Headless API endpoints for AI assistant interactions."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.exceptions import AIServiceError, QuotaExceededError, RateLimitError, UnsafeContentError
from ai.models import AIInteractionSession, AIRequest
from ai.services import AIRequestOrchestrator
from core.permissions import IsAuthenticatedAndActive

logger = logging.getLogger(__name__)


def _resolve_persona(user) -> str:
    mapping = {
        "aluno": "student",
        "professor": "teacher",
        "admin": "admin",
        "encarregado": "guardian",
    }
    return mapping.get(getattr(user, 'role', None), "staff")


class AssistantAPIView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def _load_payload(self, request) -> Dict[str, Any]:
        if request.content_type == "application/json":
            return request.data
        return request.POST.dict()

    def post(self, request, *args, **kwargs):
        payload = self._load_payload(request)
        message = payload.get('message') or payload.get('query')
        if not message:
            return Response({'error': _('Mensagem não fornecida.'), 'code': 'missing_message'}, status=status.HTTP_400_BAD_REQUEST)

        origin_app = payload.get('origin_app', 'portal')
        class_context = None
        class_id = payload.get('class_id')
        if class_id:
            from classes.models import Class
            class_context = get_object_or_404(Class, pk=class_id)

        persona = _resolve_persona(request.user)

        session: Optional[AIInteractionSession] = None
        session_id = payload.get('session_id')
        if session_id:
            session = AIInteractionSession.objects.filter(
                session_id=session_id,
                user=request.user,
                is_active=True,
            ).first()

        history = payload.get('history') or []
        if not isinstance(history, list):
            history = []

        extras = payload.get('extras') or {}
        extras.setdefault('history', history)
        if 'context_descriptor' not in extras and payload.get('context_descriptor'):
            extras['context_descriptor'] = payload['context_descriptor']
        if 'source_element' not in extras and payload.get('source_element'):
            extras['source_element'] = payload['source_element']

        orchestrator = AIRequestOrchestrator()
        try:
            result = orchestrator.handle_request(
                user=request.user,
                persona=persona,
                origin_app=origin_app,
                raw_query=message,
                class_context=class_context,
                session=session,
                extras=extras,
            )
        except RateLimitError as exc:
            return Response({'error': str(exc), 'code': 'rate_limit'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except QuotaExceededError as exc:
            return Response({'error': str(exc), 'code': 'quota'}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except UnsafeContentError as exc:
            return Response({'error': str(exc), 'code': 'guardrail'}, status=status.HTTP_403_FORBIDDEN)
        except AIServiceError as exc:
            return Response({'error': str(exc), 'code': 'service'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # pragma: no cover
            logger.exception('Erro inesperado no assistente IA', exc_info=exc)
            return Response({'error': _('Erro inesperado.'), 'code': 'unknown'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {
                'response': result.response_text,
                'model': result.model_used,
                'meta': result.meta,
                'session_id': result.meta.get('session_id') if result.meta else None,
                'request_id': result.meta.get('request_id') if result.meta else None,
            }
        )


class SessionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(
            AIInteractionSession,
            session_id=session_id,
            user=request.user,
        )
        data = {
            'session_id': str(session.session_id),
            'origin_app': session.origin_app,
            'context_descriptor': session.context_descriptor,
            'last_interaction_at': session.last_interaction_at.isoformat() if session.last_interaction_at else None,
            'requests': list(
                session.requests.select_related('response_log').values(
                    'id',
                    'raw_query',
                    'optimized_prompt',
                    'intent_label',
                    'resolved_model',
                    'response_log__response_text',
                    'created_at',
                )
            ),
        }
        return Response(data)


class AssistantFeedbackAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        request_id = request.data.get('request_id')
        feedback = request.data.get('feedback')
        if feedback not in {'helpful', 'neutral', 'not_helpful'}:
            return Response({'error': _('Feedback inválido.'), 'code': 'invalid'}, status=status.HTTP_400_BAD_REQUEST)

        ai_request = get_object_or_404(AIRequest, id=request_id, user=request.user)
        if not hasattr(ai_request, 'response_log'):
            return Response({'error': _('Pedido sem resposta associada.'), 'code': 'not_found'}, status=status.HTTP_404_NOT_FOUND)

        ai_request.response_log.user_feedback = feedback
        ai_request.response_log.save(update_fields=['user_feedback'])
        return Response({'ok': True})
