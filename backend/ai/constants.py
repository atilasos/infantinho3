from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict


DEFAULT_MODEL_COSTS: Dict[str, Decimal] = {
    "gpt-5-nano": Decimal("0.00015"),
    "gpt-5-mini": Decimal("0.00090"),
    "gpt-5": Decimal("0.00300"),
}

DEFAULT_MAX_TOKENS = 1200

DEFAULT_TIMEOUT_SECONDS = 30

DEFAULT_CACHE_TTL_SECONDS = 3600

DEFAULT_RATE_LIMITS = {
    "student": 12,
    "teacher": 24,
    "guardian": 6,
    "admin": 60,
}

PROMPT_OPTIMIZER_MODEL = "gpt-5-nano"
RESPONSE_GUARD_MODEL = "gpt-5-nano"

PROVIDER_OPENAI = "openai"
PROVIDER_VERTEX = "google-vertex"

SUPPORTED_PROVIDERS = {PROVIDER_OPENAI, PROVIDER_VERTEX}
