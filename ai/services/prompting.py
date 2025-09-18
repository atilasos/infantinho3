from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ai.constants import PROMPT_OPTIMIZER_MODEL, RESPONSE_GUARD_MODEL
from ai.services.config import is_fake_mode_enabled
from ai.services.providers import ProviderResponse, get_provider


@dataclass
class OptimizerResult:
    optimized_prompt: str
    intent: str
    suggested_model: Optional[str]
    optimizer_trace: Dict[str, Any]


class PromptOptimizer:
    SYSTEM_PROMPT = (
        "Atua como assistente pedagógico MEM. Analisa o pedido do utilizador, "
        "sugere melhorias ao prompt para foco educativo, classifica a intenção pedagógica "
        "e recomenda modelo (nano, mini, normal) considerando profundidade necessária."
    )

    def optimize(self, raw_query: str, persona: str, context: Dict[str, Any]) -> OptimizerResult:
        provider = get_provider()
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Persona: {persona}. Contexto: {context}. Pedido original: {raw_query}"
                ),
            },
        ]
        response: ProviderResponse = provider.chat_completion(
            messages,
            model=PROMPT_OPTIMIZER_MODEL,
            temperature=1,
        )
        trace = response.raw
        parsed = self._parse_response(response.content)
        trace.update({"model": response.model})
        return OptimizerResult(
            optimized_prompt=parsed["optimized_prompt"],
            intent=parsed["intent"],
            suggested_model=parsed.get("suggested_model"),
            optimizer_trace=trace,
        )

    @staticmethod
    def _parse_response(content: str) -> Dict[str, Any]:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        result = {
            "intent": "general",
            "optimized_prompt": content,
            "suggested_model": None,
        }
        for line in lines:
            lower = line.lower()
            if lower.startswith("intent:"):
                result["intent"] = line.split(":", 1)[1].strip()
            elif lower.startswith("prompt:") or lower.startswith("optimized prompt:"):
                result["optimized_prompt"] = line.split(":", 1)[1].strip()
            elif lower.startswith("model:"):
                result["suggested_model"] = line.split(":", 1)[1].strip()
        return result


class ResponseGuard:
    SYSTEM_PROMPT = (
        "És um guardião de segurança pedagógica. Analisa a resposta proposta e indica se "
        "cumpre princípios MEM (respeito, cooperação, estímulo à autonomia) e políticas escolares. "
        "Responde em JSON com campos allow (bool) e rationale (string curta)."
    )

    def check(self, candidate_response: str, persona: str, intent: str) -> Dict[str, Any]:
        if is_fake_mode_enabled():
            return {"allow": True, "rationale": "fake-mode", "model": RESPONSE_GUARD_MODEL}
        provider = get_provider()
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Persona: {persona}. Intenção: {intent}. Resposta proposta: {candidate_response}",
            },
        ]
        response = provider.chat_completion(
            messages,
            model=RESPONSE_GUARD_MODEL,
            temperature=1,
        )
        content = response.content.strip()
        try:
            import json

            parsed = json.loads(content)
            parsed.setdefault("model", response.model)
            return parsed
        except Exception:
            return {
                "allow": False,
                "rationale": content[:200],
                "model": response.model,
            }
