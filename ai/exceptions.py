class AIServiceError(Exception):
    """Erro genérico ao processar pedidos de IA."""


class ProviderNotConfiguredError(AIServiceError):
    """Lançada quando não existe configuração válida para o provider."""


class QuotaExceededError(AIServiceError):
    """Lançada quando o utilizador ou turma excede a quota disponível."""


class UnsafeContentError(AIServiceError):
    """Indica que a resposta foi bloqueada pelo guardião de segurança."""


class RateLimitError(AIServiceError):
    """Indica que o limite de pedidos por período foi excedido."""
