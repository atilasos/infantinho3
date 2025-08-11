from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from classes.models import Class
from .models import CouncilDecision, StudentProposal


User = get_user_model()


class CouncilFlowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='prof', email='prof@escola.pt', password='x', role='professor', status='ativo')
        self.student = User.objects.create_user(username='aluno', email='aluno@escola.pt', password='x', role='aluno', status='ativo')
        self.turma = Class.objects.create(name='5º A', year=2025)
        self.turma.teachers.add(self.teacher)
        self.turma.students.add(self.student)

    def test_teacher_can_create_decision(self):
        self.client.login(username='prof', password='x')
        url = reverse('council:decision_create', kwargs={'class_id': self.turma.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = {
            'date': '2026-02-10',
            'description': 'Regra: falar um de cada vez nas apresentações',
            'category': 'rule',
            'status': 'pending',
            'responsible': '',
        }
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(CouncilDecision.objects.filter(student_class=self.turma, category='rule').exists())

    def test_student_can_submit_proposal(self):
        self.client.login(username='aluno', password='x')
        url = reverse('council:proposal_create', kwargs={'class_id': self.turma.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = {'text': 'Ter mais tempo de TEA às quartas-feiras'}
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(StudentProposal.objects.filter(student_class=self.turma, author=self.student).exists())


# Create your tests here.
