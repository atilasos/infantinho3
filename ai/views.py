from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from ai.exceptions import AIServiceError, QuotaExceededError, RateLimitError, UnsafeContentError
from ai.models import AIInteractionSession, AIRequest
from ai.services import AIRequestOrchestrator


logger = logging.getLogger(__name__)

def _resolve_persona(user) -> str:
    mapping = {
        "aluno": "student",
        "professor": "teacher",
        "admin": "admin",
        "encarregado": "guardian",
    }
    return mapping.get(user.role, "staff")


def _load_payload(request: HttpRequest) -> Dict[str, Any]:
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise AIServiceError("JSON inválido.") from exc
    return request.POST.dict()


@login_required
@require_POST
def ai_assistant_view(request: HttpRequest) -> JsonResponse:
    payload = _load_payload(request)
    message = payload.get("message") or payload.get("query")
    if not message:
        return JsonResponse({"error": _("Mensagem não fornecida."), "code": "missing_message"}, status=400)

    origin_app = payload.get("origin_app", "portal")
    class_context = None
    class_id = payload.get("class_id")
    if class_id:
        from classes.models import Class

        class_context = get_object_or_404(Class, pk=class_id)

    persona = _resolve_persona(request.user)

    session: Optional[AIInteractionSession] = None
    session_id = payload.get("session_id")
    if session_id:
        try:
            session = AIInteractionSession.objects.get(
                session_id=session_id,
                user=request.user,
                is_active=True,
            )
        except AIInteractionSession.DoesNotExist:
            session = None

    history = payload.get("history") or []
    if not isinstance(history, list):
        history = []

    extras = payload.get("extras") or {}
    extras.setdefault("history", history)
    if "context_descriptor" not in extras and payload.get("context_descriptor"):
        extras["context_descriptor"] = payload["context_descriptor"]
    if "source_element" not in extras and payload.get("source_element"):
        extras["source_element"] = payload["source_element"]

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
        return JsonResponse({"error": str(exc), "code": "rate_limit"}, status=429)
    except QuotaExceededError as exc:
        return JsonResponse({"error": str(exc), "code": "quota"}, status=402)
    except UnsafeContentError as exc:
        return JsonResponse({"error": str(exc), "code": "guardrail"}, status=403)
    except AIServiceError as exc:
        return JsonResponse({"error": str(exc), "code": "service"}, status=400)
    except Exception as exc:  # pragma: no cover - fallback
        logger.exception("Erro inesperado no assistente IA", exc_info=exc)
        return JsonResponse({"error": _("Erro inesperado."), "code": "unknown"}, status=500)

    return JsonResponse(
        {
            "response": result.response_text,
            "model": result.model_used,
            "meta": result.meta,
            "session_id": result.meta.get("session_id") if result.meta else None,
            "request_id": result.meta.get("request_id") if result.meta else None,
        }
    )


@login_required
@require_GET
def session_detail_view(request: HttpRequest, session_id) -> JsonResponse:
    session = get_object_or_404(
        AIInteractionSession,
        session_id=session_id,
        user=request.user,
    )
    data = {
        "session_id": str(session.session_id),
        "origin_app": session.origin_app,
        "context_descriptor": session.context_descriptor,
        "last_interaction_at": session.last_interaction_at.isoformat(),
        "requests": list(
            session.requests.select_related("response_log").values(
                "id",
                "raw_query",
                "optimized_prompt",
                "intent_label",
                "resolved_model",
                "response_log__response_text",
                "created_at",
            )
        ),
    }
    return JsonResponse(data)


@login_required
@require_POST
def ai_feedback_view(request: HttpRequest) -> JsonResponse:
    payload = _load_payload(request)
    request_id = payload.get("request_id")
    feedback = payload.get("feedback")
    if feedback not in {"helpful", "neutral", "not_helpful"}:
        return JsonResponse({"error": _("Feedback inválido."), "code": "invalid"}, status=400)

    ai_request = get_object_or_404(AIRequest, id=request_id, user=request.user)
    if not hasattr(ai_request, "response_log"):
        return JsonResponse({"error": _("Pedido sem resposta associada."), "code": "not_found"}, status=404)

    ai_request.response_log.user_feedback = feedback
    ai_request.response_log.save(update_fields=["user_feedback"])
    return JsonResponse({"ok": True})
