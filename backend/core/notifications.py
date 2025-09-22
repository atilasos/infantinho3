"""Central notification helpers for email and future webhooks."""
from __future__ import annotations

import json
import logging
from typing import Iterable, Mapping
from urllib.request import Request, urlopen
from urllib.error import URLError

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def dispatch_notification(
    *,
    subject: str,
    message: str,
    recipients: Iterable[str],
    category: str = 'general',
    metadata: Mapping[str, object] | None = None,
) -> None:
    """Send notification emails and optionally fan out to a webhook.

    - Ignores empty email addresses.
    - Falls back to logging if sending falha.
    - Supports optional webhook (JSON POST) configurado via
      ``NOTIFICATION_WEBHOOK_URL`` nas settings.
    """
    emails = [email for email in recipients if email]
    if not emails:
        logger.debug('Skip notification %s: no recipients', category)
        return

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@infantinho.local')
    try:
        send_mail(subject, message, from_email, emails, fail_silently=False)
    except Exception as exc:  # pragma: no cover - opt-in logging during dev
        logger.warning('Falha ao enviar email (%s): %s', category, exc)

    webhook_url = getattr(settings, 'NOTIFICATION_WEBHOOK_URL', None)
    if not webhook_url:
        return

    payload = {
        'category': category,
        'subject': subject,
        'message': message,
        'recipients': emails,
        'metadata': metadata or {},
    }

    try:
        request = Request(
            webhook_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urlopen(request, timeout=5) as response:  # nosec B310 - controlled URL via settings
            logger.debug('Notification webhook dispatched (%s): %s', category, response.status)
    except URLError as exc:
        logger.debug('Webhook indisponível (%s): %s', category, exc)
    except Exception as exc:  # pragma: no cover - hardening
        logger.warning('Erro inesperado no webhook (%s): %s', category, exc)
