from __future__ import annotations

from django.test import TestCase, override_settings
from django.urls import reverse

from ai.models import AIRequest
from classes.models import Class
from users.models import User


class AIAssistantViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="aluno",
            email="aluno@example.com",
            password="senha",
            role="aluno",
            status="ativo",
        )
        self.turma = Class.objects.create(name="5.º A", year=2025)
        self.turma.students.add(self.user)
        self.client.force_login(self.user)

    @override_settings(AI_FAKE_RESPONSES=True)
    def test_returns_response_and_creates_request_log(self) -> None:
        payload = {
            "message": "Preciso de ideias para o trabalho.",
            "origin_app": "pit",
            "class_id": self.turma.id,
        }
        response = self.client.post(reverse("ai:assistant"), data=payload)
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertIn("response", data)
        self.assertTrue(data["session_id"])
        self.assertTrue(AIRequest.objects.filter(user=self.user).exists())

    @override_settings(AI_FAKE_RESPONSES=True)
    def test_feedback_endpoint_updates_response(self) -> None:
        response = self.client.post(reverse("ai:assistant"), data={"message": "Olá"})
        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        request_id = payload.get("request_id")
        self.assertIsNotNone(request_id)

        feedback_response = self.client.post(
            reverse("ai:feedback"),
            data={"request_id": request_id, "feedback": "helpful"},
        )
        self.assertEqual(feedback_response.status_code, 200)
        ai_request = AIRequest.objects.get(id=request_id)
        self.assertEqual(ai_request.response_log.user_feedback, "helpful")

    @override_settings(AI_RATE_LIMITS={"student": 1})
    def test_rate_limit_is_enforced(self) -> None:
        from decimal import Decimal

        from ai.exceptions import RateLimitError
        from ai.services.quotas import QuotaManager

        manager = QuotaManager({"student": 1})
        # Primeiro pedido deve passar
        manager.ensure_within_limits(self.user, "student", None, Decimal("0.1"))
        manager.register_usage(self.user, "student", None, Decimal("0.1"))

        # Segundo pedido deve exceder o limite diário de 1
        with self.assertRaises(RateLimitError):
            manager.ensure_within_limits(self.user, "student", None, Decimal("0.1"))

    @override_settings(AI_FAKE_RESPONSES=True)
    def test_cached_response_sets_flag(self) -> None:
        payload = {"message": "Fala-me sobre o conselho."}
        first = self.client.post(reverse("ai:assistant"), data=payload)
        self.assertEqual(first.status_code, 200, first.content)
        meta_first = first.json().get("meta", {})
        self.assertFalse(meta_first.get("cached", False))

        second = self.client.post(reverse("ai:assistant"), data=payload)
        self.assertEqual(second.status_code, 200)
        meta_second = second.json().get("meta", {})
        self.assertTrue(meta_second.get("cached", False))
