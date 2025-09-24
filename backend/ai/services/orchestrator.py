from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

from django.db import transaction

from django.conf import settings
from ai.exceptions import AIServiceError, RateLimitError, UnsafeContentError
from ai.models import AIInteractionSession, AIRequest, AIResponseLog
from ai.services.cache import AIResponseCache
from ai.services.context import ContextBroker
from ai.services.prompting import PromptOptimizer, ResponseGuard
from ai.services.providers import get_provider
from ai.services.quotas import QuotaManager
from ai.services.router import ModelRouter


@dataclass
class OrchestratorResult:
    response_text: str
    model_used: str
    meta: Dict[str, Any]


class AIRequestOrchestrator:
    def __init__(
        self,
        *,
        optimizer: Optional[PromptOptimizer] = None,
        router: Optional[ModelRouter] = None,
        context_broker: Optional[ContextBroker] = None,
        response_guard: Optional[ResponseGuard] = None,
        cache: Optional[AIResponseCache] = None,
        quota_manager: Optional[QuotaManager] = None,
    ) -> None:
        self.optimizer = optimizer or PromptOptimizer()
        self.router = router or ModelRouter()
        self.context_broker = context_broker or ContextBroker()
        self.response_guard = response_guard or ResponseGuard()
        self.cache = cache or AIResponseCache()
        self.quota_manager = quota_manager or QuotaManager(self.router.rate_limits)

    def handle_request(
        self,
        *,
        user,
        persona: str,
        origin_app: str,
        raw_query: str,
        class_context=None,
        session: Optional[AIInteractionSession] = None,
        extras: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> OrchestratorResult:
        extras = (extras or {}).copy()
        if not session:
            session_payload = self._session_payload(extras)
            session = self._ensure_session(user, persona, origin_app, class_context, session_payload)

        context_data = self.context_broker.build_context(
            user,
            persona,
            class_context=class_context,
            origin_app=origin_app,
            extras=extras,
            raw_query=raw_query,
        )

        optimization = self.optimizer.optimize(raw_query, persona, context_data.payload)
        selected_model = self.router.select_model(persona, optimization.intent, optimization.suggested_model)
        conversation_messages = self._conversation_messages(extras)

        if use_cache:
            cached = self.cache.get(
                persona,
                optimization.intent,
                optimization.optimized_prompt,
                context_data.payload,
            )
            if cached:
                request = self._log_request(
                    session,
                    user,
                    persona,
                    origin_app,
                    raw_query,
                    optimization,
                    context_data.payload,
                )
                request.mark_completed(selected_model, 0, 0, Decimal("0.00000"), 0)
                AIResponseLog.objects.create(
                    request=request,
                    response_text=cached["response_text"],
                    model_metadata={"source": "cache"},
                    guardrail_decision=cached.get("guardrail"),
                    used_cache=True,
                )
                return OrchestratorResult(
                    response_text=cached["response_text"],
                    model_used=selected_model,
                    meta={
                        "cached": True,
                        "intent": optimization.intent,
                        "session_id": str(session.session_id),
                        "request_id": request.id,
                    },
                )

        estimated_cost = self.router.estimate_cost(selected_model, tokens=600)
        self.quota_manager.ensure_within_limits(user, persona, class_context, estimated_cost)

        request = self._log_request(
            session,
            user,
            persona,
            origin_app,
            raw_query,
            optimization,
            context_data.payload,
        )

        provider = get_provider()
        # If teacher has multiple classes and none selected, or student is ambiguous, add a short clarification line
        disambig = context_data.payload.get("disambiguation")
        clarification = ""
        if disambig and disambig.get("type") == "class":
            opts = ", ".join(o.get("name") for o in (disambig.get("options") or []) if o.get("name"))
            clarification = f"Nota: o professor tem várias turmas. Confirme uma turma: {opts}."
        system_prompt = self._build_system_prompt(persona, context_data.payload)
        if clarification:
            system_prompt = system_prompt + "\n" + clarification
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_messages,
            {"role": "user", "content": optimization.optimized_prompt},
        ]

        # Log selected model + intent for traceability
        import logging
        logging.getLogger(__name__).info(
            "AI Orchestrator intent=%s suggested=%s selected=%s persona=%s",
            optimization.intent,
            optimization.suggested_model,
            selected_model,
            persona,
        )

        response = provider.chat_completion(
            messages,
            model=selected_model,
            temperature=1,
        )

        guard_decision = self.response_guard.check(response.content, persona, optimization.intent)
        if not guard_decision.get("allow", False):
            raise UnsafeContentError(guard_decision.get("rationale", "Resposta bloqueada."))

        usage = response.usage or {}
        total_tokens = usage.get("total_tokens", usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0))
        cost = self.router.estimate_cost(selected_model, total_tokens)

        with transaction.atomic():
            request.mark_completed(
                response.model,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
                cost,
                usage.get("latency_ms", 0),
            )
            AIResponseLog.objects.create(
                request=request,
                response_text=response.content,
                model_metadata=response.raw,
                guardrail_decision=guard_decision,
                used_cache=False,
            )
        self.quota_manager.register_usage(user, persona, class_context, cost)

        if use_cache:
            self.cache.set(
                persona,
                optimization.intent,
                optimization.optimized_prompt,
                context_data.payload,
                {
                    "response_text": response.content,
                    "guardrail": guard_decision,
                },
            )

        return OrchestratorResult(
            response_text=response.content,
            model_used=response.model,
            meta={
                "intent": optimization.intent,
                "optimizer_trace": optimization.optimizer_trace,
                "context": context_data.payload,
                "usage": usage,
                "session_id": str(session.session_id),
                "request_id": request.id,
            },
        )

    def _ensure_session(
        self,
        user,
        persona: str,
        origin_app: str,
        class_context,
        extras: Optional[Dict[str, Any]],
    ) -> AIInteractionSession:
        descriptor = ""
        if extras:
            descriptor = extras.get("context_descriptor") or ""
        session = AIInteractionSession.objects.create(
            user=user,
            persona=persona,
            origin_app=origin_app,
            class_context=class_context,
            context_descriptor=descriptor,
            context_payload=extras or {},
        )
        return session

    def _log_request(
        self,
        session: AIInteractionSession,
        user,
        persona: str,
        origin_app: str,
        raw_query: str,
        optimization,
        context_payload,
    ) -> AIRequest:
        return AIRequest.objects.create(
            session=session,
            user=user,
            persona=persona,
            origin_app=origin_app,
            raw_query=raw_query,
            optimized_prompt=optimization.optimized_prompt,
            optimizer_trace=optimization.optimizer_trace,
            intent_label=optimization.intent,
            target_model=optimization.suggested_model or "",
            meta_context=context_payload,
        )

    def _build_system_prompt(self, persona: str, context_payload: Dict[str, Any]) -> str:
        intro = (
            "És um assistente pedagógico alinhado com o Movimento da Escola Moderna. "
            "Foca-te em promover autonomia, cooperação e participação democrática. "
        )
        learner_profile = context_payload.get("learner_profile", {})
        grade_level = learner_profile.get("grade_level")
        age_hint = learner_profile.get("age_hint")
        checklist_focus = learner_profile.get("checklist_focus", [])

        focus_text = (
            "; ".join(f"{item.get('template')}: {item.get('item')}" for item in checklist_focus)
            if checklist_focus
            else "sem itens em destaque"
        )
        profile_text = "Aluno"
        if grade_level:
            profile_text += f" do {grade_level}º ano"
        if age_hint:
            profile_text += f", aproximadamente {age_hint} anos"

        guidance_lines = [
            intro,
            f"Perfil do interlocutor: {profile_text}.",
            f"Objetivos prioritários da checklist: {focus_text}.",
            "Não menciones modelos de IA, prompts internos ou detalhes técnicos.",
            "Se o pedido estiver em português, responde em Português Europeu (pt-PT).",
        ]
        if getattr(settings, "AI_ENFORCE_PT", True):
            guidance_lines.append(
                "Evita palavras/frases noutras línguas; se surgirem, reescreve para pt-PT."
            )

        if getattr(settings, "MEM_ENABLE", False):
            mem_block = settings.MEM_GUIDELINES or (
                "Princípios MEM: construtivismo social; cooperação; autonomia; participação democrática. "
                "Instrumentos: Checklists de Aprendizagens (autoavaliação/validação), PIT (planeamento individual), "
                "Projetos (trabalho cooperativo), Diário (reflexão/registo), Conselho (decisões coletivas). "
                "Ao responder: sugere sempre próximos passos concretos (individual, em par/pequeno grupo, com professor/família), "
                "liga-os a um instrumento MEM adequado e usa linguagem clara e acolhedora (pt‑PT)."
            )
            guidance_lines.append(f"MEM: {mem_block}")

        if persona == "student":
            guidance_lines.extend(
                [
                    "Responde no máximo em 3 frases curtas ou 3 pontos simples.",
                    "Usa vocabulário acessível e orienta um passo de cada vez.",
                    "Escolhe apenas 1 objetivo em destaque (ou 2 no máximo) e sugere passos concretos e rápidos.",
                    "Inclui uma sugestão de evidência ou forma de mostrar progresso.",
                    "Organiza a resposta como lista numerada: 1) tarefa individual/PIT, 2) trabalho com um colega ou pequeno grupo (indica como pedir apoio), 3) momento com o professor ou a família.",
                    "Evita perguntas abertas; termina convidando o aluno a dizer se quer mais ideias adicionais.",
                ]
            )
        else:
            guidance_lines.append("Adapta o discurso ao papel do utilizador mantendo foco pedagógico.")

        guidance_lines.append(f"Contexto adicional: {context_payload}.")
        return "\n".join(guidance_lines)

    def _conversation_messages(self, extras: Dict[str, Any]) -> list[Dict[str, str]]:
        history = extras.get("history") or []
        if not history:
            return []
        messages = []
        for entry in history[-6:]:
            role = entry.get("role")
            content = entry.get("content")
            if role not in {"user", "assistant"} or not content:
                continue
            mapped_role = "assistant" if role == "assistant" else "user"
            messages.append({"role": mapped_role, "content": content})
        return messages

    def _session_payload(self, extras: Dict[str, Any]) -> Dict[str, Any]:
        if not extras:
            return {}
        payload = extras.copy()
        payload.pop("history", None)
        return payload
