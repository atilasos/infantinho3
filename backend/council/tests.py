from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from classes.models import Class
from rest_framework.test import APITestCase, APIClient
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


class CouncilAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username='api-prof', email='api-prof@test.com', password='x', role='professor', status='ativo'
        )
        cls.student = User.objects.create_user(
            username='api-aluno', email='api-aluno@test.com', password='x', role='aluno', status='ativo'
        )
        cls.turma = Class.objects.create(name='API Turma', year=2026)
        cls.turma.teachers.add(cls.teacher)
        cls.turma.students.add(cls.student)

        cls.decision = CouncilDecision.objects.create(
            student_class=cls.turma,
            date='2026-01-10',
            description='Organizar feira do livro',
            category='activity',
        )
        cls.proposal = StudentProposal.objects.create(
            student_class=cls.turma,
            author=cls.student,
            text='Criar clube de leitura',
        )

    def setUp(self):
        self.client = APIClient()

    def test_teacher_creates_decision_api(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('council-decision-list')
        payload = {
            'student_class_id': self.turma.id,
            'date': '2026-02-15',
            'description': 'Definir novo horário de estudo autónomo',
            'category': 'learning_goal',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201)

    def test_teacher_updates_decision_status(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('council-decision-update-status', args=[self.decision.id])
        response = self.client.post(url, {'status': CouncilDecision.Status.IN_PROGRESS}, format='json')
        self.assertEqual(response.status_code, 200)
        self.decision.refresh_from_db()
        self.assertEqual(self.decision.status, CouncilDecision.Status.IN_PROGRESS)

    def test_student_submits_proposal_api(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('council-proposal-list')
        response = self.client.post(url, {'student_class_id': self.turma.id, 'text': 'Organizar campeonato de xadrez'}, format='json')
        self.assertEqual(response.status_code, 201)

    def test_teacher_sets_proposal_status(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('council-proposal-set-status', args=[self.proposal.id])
        response = self.client.post(url, {'status': StudentProposal.ProposalStatus.APPROVED}, format='json')
        self.assertEqual(response.status_code, 200)
        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.status, StudentProposal.ProposalStatus.APPROVED)
