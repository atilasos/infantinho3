from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

from django.core.cache import cache

from ai.constants import DEFAULT_CACHE_TTL_SECONDS


class AIResponseCache:
    def __init__(self, ttl: int = DEFAULT_CACHE_TTL_SECONDS) -> None:
        self.ttl = ttl

    def make_key(self, persona: str, intent: str, optimized_prompt: str, context: Dict[str, Any]) -> str:
        context_for_cache = {
            key: value for key, value in context.items() if key != "timestamp"
        }
        payload = json.dumps(
            {
                "persona": persona,
                "intent": intent,
                "prompt": optimized_prompt,
                "context": context_for_cache,
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"ai-response:{digest}"

    def get(self, persona: str, intent: str, optimized_prompt: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key = self.make_key(persona, intent, optimized_prompt, context)
        return cache.get(key)

    def set(
        self,
        persona: str,
        intent: str,
        optimized_prompt: str,
        context: Dict[str, Any],
        response: Dict[str, Any],
    ) -> None:
        key = self.make_key(persona, intent, optimized_prompt, context)
        cache.set(key, response, timeout=self.ttl)
