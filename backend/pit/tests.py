from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from classes.models import Class
from rest_framework.test import APITestCase, APIClient

from .models import IndividualPlan, PlanTask


User = get_user_model()


class PitFlowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='prof', email='prof@escola.pt', password='x', role='professor', status='ativo')
        self.student = User.objects.create_user(username='aluno', email='aluno@escola.pt', password='x', role='aluno', status='ativo')
        self.turma = Class.objects.create(name='5º A', year=2025)
        self.turma.teachers.add(self.teacher)
        self.turma.students.add(self.student)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='noreply@test.com')
    def test_student_can_create_and_submit_pit(self):
        self.client.login(username='aluno', password='x')
        url = reverse('pit:plan_create', kwargs={'class_id': self.turma.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        post_data = {
            'period_label': 'Semana 1 - Jan 2026',
            'start_date': '2026-01-03',
            'end_date': '2026-01-07',
            'general_objectives': 'Melhorar leitura',
            # formset management
            'tasks-TOTAL_FORMS': '1',
            'tasks-INITIAL_FORMS': '0',
            'tasks-MIN_NUM_FORMS': '0',
            'tasks-MAX_NUM_FORMS': '1000',
            'tasks-0-description': 'Ler capítulo 1',
            'tasks-0-subject': 'Português',
            'tasks-0-state': 'pending',
            'tasks-0-evidence_link': '',
            'tasks-0-order': '1',
        }
        resp = self.client.post(url, data=post_data)
        self.assertEqual(resp.status_code, 302)
        plan = IndividualPlan.objects.get(student=self.student)
        self.assertEqual(plan.status, IndividualPlan.PlanStatus.DRAFT)

        # Edit and submit
        edit_url = reverse('pit:plan_edit', kwargs={'class_id': self.turma.id, 'plan_id': plan.id})
        post_data['submit'] = '1'
        resp = self.client.post(edit_url, data=post_data)
        self.assertEqual(resp.status_code, 302)
        plan.refresh_from_db()
        self.assertEqual(plan.status, IndividualPlan.PlanStatus.SUBMITTED)
        self.assertTrue(any(self.teacher.email in email.to for email in mail.outbox))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='noreply@test.com')
    def test_teacher_can_approve_submitted_pit(self):
        # Create a submitted plan
        plan = IndividualPlan.objects.create(
            student=self.student,
            student_class=self.turma,
            period_label='Semana 2',
            status=IndividualPlan.PlanStatus.SUBMITTED,
        )
        self.client.login(username='prof', password='x')
        list_url = reverse('pit:teacher_plan_list', kwargs={'class_id': self.turma.id})
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, 200)

        approve_url = reverse('pit:teacher_plan_approve', kwargs={'class_id': self.turma.id, 'plan_id': plan.id})
        resp = self.client.post(approve_url, data={'action': 'approve'})
        self.assertEqual(resp.status_code, 302)
        plan.refresh_from_db()
        self.assertEqual(plan.status, IndividualPlan.PlanStatus.APPROVED)
        self.assertTrue(any(self.student.email in email.to for email in mail.outbox))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='noreply@test.com')
    def test_student_self_evaluation_updates_plan_and_notifies(self):
        plan = IndividualPlan.objects.create(
            student=self.student,
            student_class=self.turma,
            period_label='Semana 3',
            status=IndividualPlan.PlanStatus.APPROVED,
        )
        url = reverse('pit:plan_self_evaluate', kwargs={'class_id': self.turma.id, 'plan_id': plan.id})
        self.client.login(username='aluno', password='x')

        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)

        response_post = self.client.post(url, data={'self_evaluation': 'Refleti sobre o meu progresso.'})
        self.assertEqual(response_post.status_code, 302)
        plan.refresh_from_db()
        self.assertEqual(plan.status, IndividualPlan.PlanStatus.CONCLUDED)
        self.assertEqual(plan.self_evaluation, 'Refleti sobre o meu progresso.')
        self.assertTrue(any(self.teacher.email in email.to for email in mail.outbox))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='noreply@test.com')
    def test_teacher_evaluation_updates_plan_and_notifies_student(self):
        plan = IndividualPlan.objects.create(
            student=self.student,
            student_class=self.turma,
            period_label='Semana 4',
            status=IndividualPlan.PlanStatus.CONCLUDED,
            self_evaluation='Aprendi bastante.'
        )
        url = reverse('pit:plan_teacher_evaluate', kwargs={'class_id': self.turma.id, 'plan_id': plan.id})
        self.client.login(username='prof', password='x')

        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)

        response_post = self.client.post(url, data={'teacher_evaluation': 'Excelente compromisso.'})
        self.assertEqual(response_post.status_code, 302)
        plan.refresh_from_db()
        self.assertEqual(plan.status, IndividualPlan.PlanStatus.EVALUATED)
        self.assertEqual(plan.teacher_evaluation, 'Excelente compromisso.')
        self.assertTrue(any(self.student.email in email.to for email in mail.outbox))


# Create your tests here.


class PitAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username='api-prof', email='api-prof@test.com', password='x', role='professor', status='ativo'
        )
        cls.student = User.objects.create_user(
            username='api-aluno', email='api-aluno@test.com', password='x', role='aluno', status='ativo'
        )
        cls.turma = Class.objects.create(name='API 6ºB', year=2026)
        cls.turma.teachers.add(cls.teacher)
        cls.turma.students.add(cls.student)

        cls.plan = IndividualPlan.objects.create(
            student=cls.student,
            student_class=cls.turma,
            period_label='Semana API',
        )
        cls.task = PlanTask.objects.create(
            plan=cls.plan,
            description='Ler artigo',
            subject='Português',
        )

    def setUp(self):
        self.client = APIClient()

    def test_student_can_create_plan_and_submit(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('pit-plan-list')
        payload = {
            'student_class_id': self.turma.id,
            'period_label': 'Semana 2 API',
            'start_date': '2026-03-01',
            'end_date': '2026-03-05',
            'general_objectives': 'Aprofundar leitura',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        plan_id = response.data['id']

        submit_url = reverse('pit-plan-submit', args=[plan_id])
        submit_response = self.client.post(submit_url)
        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data['status'], IndividualPlan.PlanStatus.SUBMITTED)

    def test_teacher_decision_flow(self):
        self.plan.status = IndividualPlan.PlanStatus.SUBMITTED
        self.plan.save()
        self.client.force_authenticate(user=self.teacher)
        decision_url = reverse('pit-plan-teacher-decision', args=[self.plan.id])
        approve = self.client.post(decision_url, {'decision': 'approve'}, format='json')
        self.assertEqual(approve.status_code, 200)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, IndividualPlan.PlanStatus.APPROVED)

        return_resp = self.client.post(decision_url, {'decision': 'return'}, format='json')
        self.assertEqual(return_resp.status_code, 200)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, IndividualPlan.PlanStatus.DRAFT)

    def test_student_self_evaluation_api(self):
        self.plan.status = IndividualPlan.PlanStatus.APPROVED
        self.plan.save()
        self.client.force_authenticate(user=self.student)
        url = reverse('pit-plan-self-evaluation', args=[self.plan.id])
        response = self.client.post(url, {'self_evaluation': 'Refleti cuidadosamente.'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, IndividualPlan.PlanStatus.CONCLUDED)
        self.assertEqual(self.plan.self_evaluation, 'Refleti cuidadosamente.')

    def test_teacher_evaluation_api(self):
        self.plan.status = IndividualPlan.PlanStatus.CONCLUDED
        self.plan.save()
        self.client.force_authenticate(user=self.teacher)
        url = reverse('pit-plan-teacher-evaluation', args=[self.plan.id])
        response = self.client.post(url, {'teacher_evaluation': 'Excelente progresso.'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, IndividualPlan.PlanStatus.EVALUATED)
        self.assertEqual(self.plan.teacher_evaluation, 'Excelente progresso.')

    def test_task_updates(self):
        self.client.force_authenticate(user=self.student)
        task_url = reverse('pit-task-detail', args=[self.task.id])
        response = self.client.patch(task_url, {'state': PlanTask.TaskState.IN_PROGRESS}, format='json')
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.state, PlanTask.TaskState.IN_PROGRESS)
