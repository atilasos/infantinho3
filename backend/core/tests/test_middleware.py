import json
from unittest.mock import patch

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient

User = get_user_model()


@override_settings(
    LOGGING={
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {'class': 'logging.StreamHandler'},
        },
        'loggers': {
            'audit': {
                'handlers': ['console'],
                'level': 'INFO',
            }
        },
    }
)
class AuditMiddlewareTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='audit-user',
            email='audit@example.com',
            password='secret',
            role='aluno',
            status='ativo',
        )
        self.client.force_authenticate(self.user)

    def test_audit_log_is_produced_for_mutating_request(self):
        with patch('core.middleware.AuditLogMiddleware._log_request_response') as mocked_logger:
            response = self.client.post(reverse('pit-plan-list'), data={'student_class_id': 999}, format='json')
        self.assertNotEqual(response.status_code, 500)
        mocked_logger.assert_called_once()
