from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from classes.models import Class
from .models import IndividualPlan


User = get_user_model()


class PitFlowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='prof', email='prof@escola.pt', password='x', role='professor', status='ativo')
        self.student = User.objects.create_user(username='aluno', email='aluno@escola.pt', password='x', role='aluno', status='ativo')
        self.turma = Class.objects.create(name='5º A', year=2025)
        self.turma.teachers.add(self.teacher)
        self.turma.students.add(self.student)

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


# Create your tests here.
