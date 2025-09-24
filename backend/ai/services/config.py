from __future__ import annotations

import os
from dataclasses import dataclass
import json
from decimal import Decimal
from typing import Dict, Optional

from django.conf import settings

from ai.constants import (
    DEFAULT_MODEL_COSTS,
    DEFAULT_TIMEOUT_SECONDS,
    SUPPORTED_PROVIDERS,
    PROVIDER_OPENAI,
    PROVIDER_OLLAMA,
)


@dataclass
class ProviderConfig:
    name: str
    api_key: Optional[str]
    api_base: Optional[str] = None
    default_model: str = "gpt-5"
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    extra_params: Optional[Dict[str, str]] = None


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(key, getattr(settings, key, default) if hasattr(settings, key) else default)


def _json_env(key: str) -> Optional[Dict[str, str]]:
    raw = _env(key)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed  # type: ignore[return-value]
    except Exception:
        return None
    return None


def get_provider_config() -> ProviderConfig:
    configured_name = (
        getattr(settings, "AI_SERVICE_PROVIDER", None)
        or os.environ.get("AI_SERVICE_PROVIDER")
        or PROVIDER_OPENAI
    ).lower()

    if configured_name not in SUPPORTED_PROVIDERS:
        configured_name = PROVIDER_OPENAI

    if configured_name == PROVIDER_OPENAI:
        return ProviderConfig(
            name=PROVIDER_OPENAI,
            api_key=_env("OPENAI_API_KEY"),
            api_base=_env("OPENAI_API_BASE", "https://api.openai.com/v1"),
            default_model=getattr(settings, "AI_DEFAULT_MODEL", "gpt-5"),
        )

    if configured_name == PROVIDER_OLLAMA:
        # Ollama local server (no API key required by default)
        raw_opts = _json_env("OLLAMA_OPTIONS") or {}
        # Accept either {"num_ctx":4096} or {"options":{...}}
        if isinstance(raw_opts, dict) and "options" in raw_opts and isinstance(raw_opts.get("options"), dict):
            ollama_options = raw_opts.get("options") or {}
        else:
            ollama_options = raw_opts
        return ProviderConfig(
            name=PROVIDER_OLLAMA,
            api_key=_env("OLLAMA_API_KEY", ""),
            api_base=_env("OLLAMA_API_BASE", "http://localhost:11434"),
            default_model=getattr(settings, "AI_DEFAULT_MODEL", "llama3.1"),
            extra_params={
                "options": ollama_options or {},
            },
        )

    return ProviderConfig(
        name=configured_name,
        api_key=_env("GOOGLE_VERTEX_API_KEY"),
        api_base=_env("GOOGLE_VERTEX_API_BASE"),
        default_model=getattr(settings, "AI_DEFAULT_MODEL", "gpt-5"),
        extra_params={
            "project": _env("GOOGLE_VERTEX_PROJECT"),
            "location": _env("GOOGLE_VERTEX_LOCATION", "eu"),
        },
    )


def get_model_costs() -> Dict[str, Decimal]:
    overrides: Dict[str, str] = getattr(settings, "AI_MODEL_COSTS", {})
    costs: Dict[str, Decimal] = DEFAULT_MODEL_COSTS.copy()
    for model_name, value in overrides.items():
        try:
            costs[model_name] = Decimal(str(value))
        except Exception:
            continue
    return costs


def is_fake_mode_enabled() -> bool:
    setting_value = getattr(settings, "AI_FAKE_RESPONSES", None)
    if setting_value is not None:
        return bool(setting_value)
    return os.environ.get("AI_FAKE_RESPONSES", "True").lower() in {"1", "true", "yes"}
