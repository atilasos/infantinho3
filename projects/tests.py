from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from classes.models import Class
from .models import Project


User = get_user_model()


class ProjectsFlowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='prof', email='prof@escola.pt', password='x', role='professor', status='ativo')
        self.student = User.objects.create_user(username='aluno', email='aluno@escola.pt', password='x', role='aluno', status='ativo')
        self.turma = Class.objects.create(name='5º A', year=2025)
        self.turma.teachers.add(self.teacher)
        self.turma.students.add(self.student)

    def test_teacher_can_create_project(self):
        self.client.login(username='prof', password='x')
        url = reverse('projects:project_create', kwargs={'class_id': self.turma.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = {
            'title': 'Horta Escolar',
            'description': 'Projeto de horta da turma',
            'start_date': '2026-02-01',
            'end_date': '2026-03-01',
            'product_description': 'Apresentação e colheita',
            'members': [self.student.id],
            # formset
            'projecttask_set-TOTAL_FORMS': '1',
            'projecttask_set-INITIAL_FORMS': '0',
            'projecttask_set-MIN_NUM_FORMS': '0',
            'projecttask_set-MAX_NUM_FORMS': '1000',
            'projecttask_set-0-description': 'Preparar canteiros',
            'projecttask_set-0-responsible': self.student.id,
            'projecttask_set-0-due_date': '2026-02-05',
            'projecttask_set-0-state': 'todo',
            'projecttask_set-0-order': '1',
        }
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Project.objects.filter(title='Horta Escolar', student_class=self.turma).exists())

    def test_any_member_can_view_list(self):
        Project.objects.create(student_class=self.turma, title='Jornal da Escola')
        self.client.login(username='aluno', password='x')
        url = reverse('projects:project_list', kwargs={'class_id': self.turma.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Jornal da Escola')


# Create your tests here.
