from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from classes.models import Class
from .models import Project, ProjectTask


User = get_user_model()


class ProjectsFlowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='prof', email='prof@escola.pt', password='x', role='professor', status='ativo')
        self.student = User.objects.create_user(username='aluno', email='aluno@escola.pt', password='x', role='aluno', status='ativo')
        self.outsider = User.objects.create_user(username='outsider', email='outro@escola.pt', password='x', role='aluno', status='ativo')
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
            'members': [str(self.student.id)],
            # formset
            'tasks-TOTAL_FORMS': '1',
            'tasks-INITIAL_FORMS': '0',
            'tasks-MIN_NUM_FORMS': '0',
            'tasks-MAX_NUM_FORMS': '1000',
            'tasks-0-description': 'Preparar canteiros',
            'tasks-0-responsible': str(self.student.id),
            'tasks-0-due_date': '2026-02-05',
            'tasks-0-state': 'todo',
            'tasks-0-order': '1',
        }
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 302)
        project = Project.objects.get(title='Horta Escolar', student_class=self.turma)
        self.assertTrue(project.members.filter(id=self.teacher.id).exists())

    def test_student_can_create_project(self):
        self.client.login(username='aluno', password='x')
        url = reverse('projects:project_create', kwargs={'class_id': self.turma.id})
        data = {
            'title': 'Jornal da Escola',
            'description': 'Produção mensal de notícias',
            'start_date': '2026-03-01',
            'end_date': '2026-06-30',
            'product_description': 'Edição impressa',
            'members': [str(self.student.id), str(self.teacher.id)],
            'tasks-TOTAL_FORMS': '1',
            'tasks-INITIAL_FORMS': '0',
            'tasks-MIN_NUM_FORMS': '0',
            'tasks-MAX_NUM_FORMS': '1000',
            'tasks-0-description': 'Recolher artigos',
            'tasks-0-responsible': str(self.student.id),
            'tasks-0-due_date': '2026-03-15',
            'tasks-0-state': 'todo',
            'tasks-0-order': '1',
        }
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 302)
        project = Project.objects.get(title='Jornal da Escola', student_class=self.turma)
        self.assertTrue(project.members.filter(id=self.student.id).exists())

    def test_any_member_can_view_list(self):
        Project.objects.create(student_class=self.turma, title='Jornal da Escola')
        self.client.login(username='aluno', password='x')
        url = reverse('projects:project_list', kwargs={'class_id': self.turma.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Jornal da Escola')
        self.assertContains(resp, 'Novo Projeto')

    def test_outsider_cannot_view_list(self):
        self.client.login(username='outsider', password='x')
        url = reverse('projects:project_list', kwargs={'class_id': self.turma.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_project_update_permissions(self):
        project = Project.objects.create(student_class=self.turma, title='Robótica')
        project.members.add(self.student)
        task = ProjectTask.objects.create(project=project, description='Montar protótipo', state='todo')

        # Non member cannot edit
        self.client.login(username='outsider', password='x')
        url = reverse('projects:project_update', kwargs={'class_id': self.turma.id, 'project_id': project.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        # Member can edit
        self.client.login(username='aluno', password='x')
        update_data = {
            'title': 'Robótica 2.0',
            'description': 'Atualizado',
            'start_date': '',
            'end_date': '',
            'product_description': 'Apresentação final',
            'members': [str(self.student.id), str(self.teacher.id)],
            'tasks-TOTAL_FORMS': '1',
            'tasks-INITIAL_FORMS': '1',
            'tasks-MIN_NUM_FORMS': '0',
            'tasks-MAX_NUM_FORMS': '1000',
            'tasks-0-id': str(task.id),
            'tasks-0-description': 'Montar protótipo v2',
            'tasks-0-responsible': str(self.student.id),
            'tasks-0-due_date': '',
            'tasks-0-state': 'in_progress',
            'tasks-0-order': '1',
        }
        resp = self.client.post(url, data=update_data)
        self.assertEqual(resp.status_code, 302)
        project.refresh_from_db()
        task.refresh_from_db()
        self.assertEqual(project.title, 'Robótica 2.0')
        self.assertEqual(task.state, 'in_progress')

    def test_project_detail_requires_membership(self):
        project = Project.objects.create(student_class=self.turma, title='Teatro')
        self.client.login(username='outsider', password='x')
        url = reverse('projects:project_detail', kwargs={'class_id': self.turma.id, 'project_id': project.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        self.client.login(username='aluno', password='x')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Teatro')


# Create your tests here.
