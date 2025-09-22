from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from django.utils import timezone

from ai.constants import DEFAULT_RATE_LIMITS
from ai.exceptions import QuotaExceededError, RateLimitError
from ai.models import AIUsageQuota


@dataclass
class QuotaDecision:
    allowed: bool
    reason: Optional[str] = None


class QuotaManager:
    def __init__(self, rate_limits: Optional[dict] = None) -> None:
        self.rate_limits = rate_limits or DEFAULT_RATE_LIMITS

    def ensure_within_limits(
        self,
        user,
        persona: str,
        class_context,
        cost: Decimal,
    ) -> QuotaDecision:
        today = timezone.localdate()
        quota = self._get_or_create_quota(user, persona, class_context, today)
        if quota.max_requests and quota.requests_made >= quota.max_requests:
            raise RateLimitError("Limite diário de pedidos de IA atingido.")
        if quota.max_cost and quota.cost_accumulated + cost > quota.max_cost:
            raise QuotaExceededError("Limite de custo diário atingido para IA.")
        return QuotaDecision(allowed=True)

    def register_usage(
        self,
        user,
        persona: str,
        class_context,
        cost: Decimal,
    ) -> None:
        today = timezone.localdate()
        quota = self._get_or_create_quota(user, persona, class_context, today)
        quota.register_usage(cost)

    def _get_or_create_quota(self, user, persona: str, class_context, day: date) -> AIUsageQuota:
        defaults = {
            "max_requests": self.rate_limits.get(persona, 10),
            "max_cost": Decimal("1.50000"),
        }
        quota, _ = AIUsageQuota.objects.get_or_create(
            scope=AIUsageQuota.SCOPE_USER,
            user=user,
            class_context=class_context,
            period_start=day,
            period_end=day,
            defaults=defaults,
        )
        return quota
