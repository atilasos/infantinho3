from datetime import date, timedelta

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from classes.models import Class
from rest_framework.test import APITestCase, APIClient
from users.models import GuardianRelation

from .models import (
    IndividualPlan,
    PlanTask,
    PitTemplate,
    TemplateSection,
    TemplateSuggestion,
    PlanSuggestion,
    PlanLogEntry,
)
from .services import generate_weekly_plan
from council.models import CouncilDecision


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
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 7),
            status=IndividualPlan.PlanStatus.DRAFT,
            general_objectives='Consolidar leitura e escrita.',
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
        log = PlanLogEntry.objects.filter(plan=self.plan).latest('created_at')
        self.assertEqual(log.action, PlanLogEntry.Action.STATUS_CHANGE)
        self.assertEqual(log.actor, self.student)

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
        log = PlanLogEntry.objects.filter(plan=self.plan).latest('created_at')
        self.assertEqual(log.action, PlanLogEntry.Action.STATUS_CHANGE)
        self.assertEqual(log.actor, self.teacher)

    def test_export_pdf_returns_binary(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('pit-plan-export-pdf', args=[self.plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertIn('attachment; filename=', response['Content-Disposition'])

    def test_task_updates(self):
        self.client.force_authenticate(user=self.student)
        task_url = reverse('pit-task-detail', args=[self.task.id])
        response = self.client.patch(task_url, {'state': PlanTask.TaskState.IN_PROGRESS}, format='json')
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.state, PlanTask.TaskState.IN_PROGRESS)
        log = PlanLogEntry.objects.filter(plan=self.plan).latest('created_at')
        self.assertEqual(log.action, PlanLogEntry.Action.UPDATED)
        self.assertEqual(log.actor, self.student)

    def test_task_delete_logs_entry(self):
        self.client.force_authenticate(user=self.teacher)
        task = PlanTask.objects.create(plan=self.plan, description='Apagar', subject='Matemática')
        url = reverse('pit-task-detail', args=[task.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        log = PlanLogEntry.objects.filter(plan=self.plan).latest('created_at')
        self.assertEqual(log.action, PlanLogEntry.Action.UPDATED)
        self.assertEqual(log.actor, self.teacher)

    def test_plan_patch_logs_entry(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('pit-plan-detail', args=[self.plan.id])
        response = self.client.patch(url, {'general_objectives': 'Rever leitura intensiva'}, format='json')
        self.assertEqual(response.status_code, 200)
        log = PlanLogEntry.objects.filter(plan=self.plan).latest('created_at')
        self.assertEqual(log.action, PlanLogEntry.Action.UPDATED)
        self.assertEqual(log.actor, self.student)

    def test_student_cannot_access_other_plan(self):
        other_student = User.objects.create_user(
            username='other-student', email='other@student.pt', password='x', role='aluno', status='ativo'
        )
        other_plan = IndividualPlan.objects.create(
            student=other_student,
            student_class=self.turma,
            period_label='Semana secreta',
        )
        self.client.force_authenticate(user=self.student)
        url = reverse('pit-plan-detail', args=[other_plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_parent_can_view_child_plan(self):
        guardian = User.objects.create_user(
            username='guardian', email='guardian@demo.pt', password='x', role='encarregado', status='ativo'
        )
        GuardianRelation.objects.create(encarregado=guardian, aluno=self.student)
        self.client.force_authenticate(user=guardian)
        url = reverse('pit-plan-detail', args=[self.plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_parent_cannot_edit_child_plan(self):
        guardian = User.objects.create_user(
            username='guardian', email='guardian2@demo.pt', password='x', role='encarregado', status='ativo'
        )
        GuardianRelation.objects.create(encarregado=guardian, aluno=self.student)
        self.client.force_authenticate(user=guardian)
        url = reverse('pit-plan-detail', args=[self.plan.id])
        response = self.client.patch(url, {'general_objectives': 'Tentativa'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_professor_can_access_students_plan(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('pit-plan-detail', args=[self.plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_professor_cannot_access_other_class_plan(self):
        other_class = Class.objects.create(name='Outro', year=2027)
        student_other = User.objects.create_user(
            username='aluno2', email='aluno2@demo.pt', password='x', role='aluno', status='ativo'
        )
        other_class.students.add(student_other)
        other_plan = IndividualPlan.objects.create(
            student=student_other,
            student_class=other_class,
            period_label='Semana 2',
        )
        self.client.force_authenticate(user=self.teacher)
        url = reverse('pit-plan-detail', args=[other_plan.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_student_cannot_create_task_for_other_student(self):
        other_student = User.objects.create_user(
            username='other2', email='other2@demo.pt', password='x', role='aluno', status='ativo'
        )
        other_plan = IndividualPlan.objects.create(
            student=other_student,
            student_class=self.turma,
            period_label='Semana 99',
        )
        self.client.force_authenticate(user=self.student)
        url = reverse('pit-task-list')
        response = self.client.post(
            url,
            {
                'plan': other_plan.id,
                'description': 'Tarefa não autorizada',
                'subject': 'Português',
                'state': PlanTask.TaskState.PENDING,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_encarregado_cannot_create_task(self):
        guardian = User.objects.create_user(
            username='guardian3', email='guardian3@demo.pt', password='x', role='encarregado', status='ativo'
        )
        GuardianRelation.objects.create(encarregado=guardian, aluno=self.student)
        self.client.force_authenticate(user=guardian)
        url = reverse('pit-task-list')
        response = self.client.post(
            url,
            {
                'plan': self.plan.id,
                'description': 'Tentativa encarregado',
                'subject': 'Matemática',
                'state': PlanTask.TaskState.PENDING,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)


class PitGenerationServiceTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='prof-svc', email='prof-svc@example.com', password='x', role='professor', status='ativo'
        )
        self.student = User.objects.create_user(
            username='al-svc', email='al-svc@example.com', password='x', role='aluno', status='ativo'
        )
        self.turma = Class.objects.create(name='7.ºC', year=7)
        self.turma.teachers.add(self.teacher)
        self.turma.students.add(self.student)

        self.template = PitTemplate.objects.create(
            name='Modelo Base', version=2, created_by=self.teacher, student_class=self.turma
        )
        self.section = TemplateSection.objects.create(template=self.template, title='TEA', order=1)
        TemplateSuggestion.objects.create(
            template=self.template,
            section=self.section,
            text='Ler 20 minutos por dia.',
            order=1,
            is_pending=False,
        )

    def test_service_generates_plan_with_template(self):
        result = generate_weekly_plan(student=self.student, student_class=self.turma)
        plan = result.plan
        self.assertEqual(plan.template, self.template)
        self.assertEqual(plan.template_version, self.template.version)
        self.assertTrue(plan.suggestions_imported)
        self.assertEqual(plan.suggestions.count(), 1)
        self.assertEqual(plan.sections.count(), 1)
        self.assertEqual(result.created_sections, 1)
        self.assertEqual(plan.log_entries.count(), 1)
        log_entry = plan.log_entries.first()
        self.assertEqual(log_entry.action, log_entry.Action.GENERATED)

    def test_service_transports_pending_tasks(self):
        origin_plan = IndividualPlan.objects.create(
            student=self.student,
            student_class=self.turma,
            template=self.template,
            template_version=self.template.version,
            period_label='Semana anterior',
            start_date=date.today() - timedelta(days=14),
            end_date=date.today() - timedelta(days=8),
        )
        PlanTask.objects.create(plan=origin_plan, description='Tarefa pendente', state='pending', order=1)
        PlanTask.objects.create(plan=origin_plan, description='Tarefa concluída', state='done', order=2)

        result = generate_weekly_plan(student=self.student, student_class=self.turma)
        plan = result.plan
        texts = list(plan.suggestions.values_list('text', flat=True))
        self.assertTrue(any('Tarefa pendente' in text for text in texts))
        self.assertTrue(plan.pendings_imported)

    def test_service_imports_recent_council_decisions(self):
        CouncilDecision.objects.create(
            student_class=self.turma,
            date=date.today() - timedelta(days=3),
            description='Organizar escala do TEA',
            category=CouncilDecision.Category.ACTIVITY,
            status=CouncilDecision.Status.PENDING,
            responsible=self.teacher,
        )

        result = generate_weekly_plan(student=self.student, student_class=self.turma)
        self.assertGreaterEqual(result.created_council, 1)
        plan = result.plan
        self.assertTrue(
            plan.suggestions.filter(origin=PlanSuggestion.SuggestionSource.COUNCIL).exists()
        )
