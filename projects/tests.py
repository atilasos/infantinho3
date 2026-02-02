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
        self.student2 = User.objects.create_user(username='aluno2', email='aluno2@escola.pt', password='x', role='aluno', status='ativo')
        self.turma = Class.objects.create(name='5º A', year=2025)
        self.turma.teachers.add(self.teacher)
        self.turma.students.add(self.student)
        self.turma.students.add(self.student2)

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

    def test_project_member_can_edit(self):
        """Test that a project member can edit the project."""
        project = Project.objects.create(student_class=self.turma, title='Projeto Teste')
        project.members.add(self.student)
        
        self.client.login(username='aluno', password='x')
        url = reverse('projects:project_edit', kwargs={'class_id': self.turma.id, 'project_id': project.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
        # Update title (using only fields in the form)
        data = {
            'title': 'Projeto Atualizado',
            'description': project.description or '',
            'start_date': '',
            'end_date': '',
            'product_description': '',
            'members': [self.student.id],
            'tasks-TOTAL_FORMS': '0',
            'tasks-INITIAL_FORMS': '0',
            'tasks-MIN_NUM_FORMS': '0',
            'tasks-MAX_NUM_FORMS': '1000',
        }
        resp = self.client.post(url, data=data)
        # Debug: print form errors if any
        if resp.status_code == 200:
            print("Form errors:", resp.context.get('form').errors if resp.context and 'form' in resp.context else 'N/A')
            print("Formset errors:", resp.context.get('formset').errors if resp.context and 'formset' in resp.context else 'N/A')
        self.assertEqual(resp.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.title, 'Projeto Atualizado')

    def test_non_member_cannot_edit(self):
        """Test that a non-member student cannot edit the project."""
        project = Project.objects.create(student_class=self.turma, title='Projeto Teste')
        project.members.add(self.student)  # student is member, not student2
        
        self.client.login(username='aluno2', password='x')
        url = reverse('projects:project_edit', kwargs={'class_id': self.turma.id, 'project_id': project.id})
        resp = self.client.get(url)
        # Should redirect with error message
        self.assertEqual(resp.status_code, 302)

    def test_teacher_can_edit_any_project(self):
        """Test that a teacher can edit any project in their class."""
        project = Project.objects.create(student_class=self.turma, title='Projeto Aluno')
        project.members.add(self.student)
        
        self.client.login(username='prof', password='x')
        url = reverse('projects:project_edit', kwargs={'class_id': self.turma.id, 'project_id': project.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)


# Create your tests here.
