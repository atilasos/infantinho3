from __future__ import annotations

from decimal import Decimal
from typing import Dict

from django.conf import settings

from ai.constants import DEFAULT_RATE_LIMITS
from ai.services.config import get_model_costs


class ModelRouter:
    """Decide qual modelo utilizar com base no resultado do PromptOptimizer."""

    def __init__(self, rate_limits: Dict[str, int] | None = None) -> None:
        self.model_costs = get_model_costs()
        config_limits = getattr(settings, "AI_RATE_LIMITS", {})
        if rate_limits:
            self.rate_limits = rate_limits
        else:
            merged = DEFAULT_RATE_LIMITS.copy()
            merged.update({k: int(v) for k, v in config_limits.items() if str(v).isdigit()})
            self.rate_limits = merged

    def select_model(self, persona: str, intent: str, suggestion: str | None) -> str:
        # Normalize suggestion if it's a tier keyword (nano/mini/normal)
        tiers = getattr(settings, "AI_MODEL_TIERS", {}) or {}
        if suggestion in {"nano", "mini", "normal"}:
            mapped = tiers.get(suggestion)
            if mapped:
                suggestion = mapped

        # 1) If the optimizer explicitly suggested a concrete model, honor it
        if suggestion and (suggestion in self.model_costs or settings.AI_SERVICE_PROVIDER == "ollama"):
            return suggestion

        # 2) Environment-configured model per persona (role) overrides defaults
        model_by_persona = getattr(settings, "AI_MODEL_BY_PERSONA", {}) or {}
        if persona in model_by_persona and model_by_persona[persona]:
            return model_by_persona[persona]

        # 3) Heuristic fallback by intent/persona using configured tiers
        tiers = getattr(settings, "AI_MODEL_TIERS", {}) or {}
        tier_normal = tiers.get("normal", "gpt-5")
        tier_mini = tiers.get("mini", "gpt-5-mini")
        tier_nano = tiers.get("nano", "gpt-5-nano")

        if intent in {"planeamento_prolongado", "analise_dados", "conselho_complexo"}:
            return tier_normal
        if intent in {"feedback_curto", "orientacao_imediata"}:
            return tier_mini
        if persona == "student":
            return tier_mini
        return tier_nano

    def estimate_cost(self, model_name: str, tokens: int) -> Decimal:
        cost = self.model_costs.get(model_name, Decimal("0.00100"))
        return cost * Decimal(tokens or 0) / Decimal(1000)

    def get_rate_limit(self, persona: str) -> int:
        return self.rate_limits.get(persona, 10)
