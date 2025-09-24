from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional

import requests

from ai.constants import PROVIDER_OPENAI, PROVIDER_OLLAMA
from requests import HTTPError, RequestException

from ai.exceptions import ProviderNotConfiguredError, RateLimitError, AIServiceError
from ai.services.config import ProviderConfig, get_provider_config, is_fake_mode_enabled


@dataclass
class ProviderResponse:
    content: str
    model: str
    usage: Dict[str, int]
    raw: Dict[str, Any]


class BaseProvider:
    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        self.config = config or get_provider_config()
        # Some providers (e.g., Ollama) don't require API keys
        if not self.config.api_key and not is_fake_mode_enabled() and self.config.name != PROVIDER_OLLAMA:
            raise ProviderNotConfiguredError("Nenhuma chave API fornecida para o serviço de IA.")

    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs: Any) -> ProviderResponse:
        raise NotImplementedError


class OpenAIProvider(BaseProvider):
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        if is_fake_mode_enabled():
            content = self._fake_completion(messages)
            return ProviderResponse(
                content=content,
                model=model or self.config.default_model,
                usage={"prompt_tokens": 200, "completion_tokens": 200, "total_tokens": 400},
                raw={"fake": True},
            )

        payload = {
            "model": model or self.config.default_model,
            "messages": messages,
        }
        payload.update(kwargs)

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{self.config.api_base}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
        except HTTPError as exc:
            status = exc.response.status_code if exc.response else None
            detail = exc.response.text if exc.response is not None else ''
            if status == 429:
                raise RateLimitError("Limite do provedor de IA atingido. Tenta novamente daqui a pouco.") from exc
            message = f"Erro ao contactar o provedor IA ({status})."
            if detail:
                message += f" Detalhe: {detail}"
            raise AIServiceError(message) from exc
        except RequestException as exc:
            raise AIServiceError("Não foi possível contactar o provedor de IA. Verifica a ligação à internet e as credenciais.") from exc

        data = response.json()
        choice = data["choices"][0]
        message = choice.get("message", {})
        usage = data.get("usage", {})
        return ProviderResponse(
            content=message.get("content", ""),
            model=data.get("model", payload["model"]),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            raw=data,
        )

    @staticmethod
    def _fake_completion(messages: List[Dict[str, str]]) -> str:
        last_message = messages[-1]["content"] if messages else ""
        return (
            "[Resposta simulada] Ainda não estamos ligados ao serviço real de IA. "
            "Resumo do pedido: " + last_message[:200]
        )


def get_provider(config: Optional[ProviderConfig] = None) -> BaseProvider:
    cfg = config or get_provider_config()
    if cfg.name == PROVIDER_OPENAI:
        return OpenAIProvider(cfg)
    if cfg.name == PROVIDER_OLLAMA:
        # Minimal inline provider for Ollama chat completions
        class OllamaProvider(BaseProvider):
            def chat_completion(self, messages, model=None, **kwargs):
                if is_fake_mode_enabled():
                    content = OpenAIProvider._fake_completion(messages)
                    return ProviderResponse(
                        content=content,
                        model=model or (self.config.default_model or "llama3.1"),
                        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        raw={"fake": True},
                    )

                # Prefer native Ollama chat API for compatibility
                payload = {
                    "model": model or (self.config.default_model or "llama3.1"),
                    "messages": messages,
                    "stream": False,
                }
                payload.update(kwargs)
                # Merge configured options into payload
                options = (self.config.extra_params or {}).get("options") or {}
                if options:
                    payload["options"] = {**options, **payload.get("options", {})}
                url = f"{self.config.api_base}/api/chat"
                logging.getLogger(__name__).info("OLLAMA request %s payload=%s", url, payload)
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        timeout=self.config.timeout_seconds,
                    )
                    response.raise_for_status()
                except HTTPError as exc:
                    status = exc.response.status_code if exc.response else None
                    detail = exc.response.text if exc.response is not None else ''
                    if status == 429:
                        raise RateLimitError("Limite do provedor de IA atingido no Ollama.") from exc
                    message = f"Erro ao contactar Ollama ({status})."
                    if detail:
                        message += f" Detalhe: {detail}"
                    raise AIServiceError(message) from exc
                except RequestException as exc:
                    raise AIServiceError("Não foi possível contactar o Ollama local. Verifique se está a correr em http://localhost:11434.") from exc

                data = response.json()
                logging.getLogger(__name__).info("OLLAMA response status=%s keys=%s", response.status_code, list(data.keys()))
                # Native Ollama returns: { message: { role, content }, eval_count, prompt_eval_count, model, ... }
                msg_obj = data.get("message") or {}
                content = msg_obj.get("content") or data.get("response") or ""
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                usage = {
                    "prompt_tokens": int(prompt_tokens or 0),
                    "completion_tokens": int(completion_tokens or 0),
                    "total_tokens": int(prompt_tokens or 0) + int(completion_tokens or 0),
                    "latency_ms": int((data.get("total_duration") or 0) / 1_000_000),
                }
                return ProviderResponse(
                    content=content,
                    model=data.get("model") or payload["model"],
                    usage=usage,
                    raw=data,
                )

        return OllamaProvider(cfg)

    # Fallback
    return OpenAIProvider(cfg)
