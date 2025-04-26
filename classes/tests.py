from django.test import TestCase
from django.urls import reverse
from users.models import User
from classes.models import Class

# Create your tests here.

class AddStudentPermissionTest(TestCase):
    def setUp(self):
        self.prof = User.objects.create_user(username='prof', email='prof@escola.pt', password='prof', role='professor', status='ativo')
        self.outsider = User.objects.create_user(username='out', email='out@escola.pt', password='out', role='professor', status='ativo')
        self.guest = User.objects.create_user(username='guest', email='guest@escola.pt', password='guest', status='convidado')
        self.turma = Class.objects.create(name='7A', year=2025)
        self.turma.teachers.add(self.prof)

    def test_only_professor_of_turma_can_promote(self):
        self.client.force_login(self.outsider)
        url = reverse('add_student', args=[self.turma.id])
        response = self.client.post(url, {'user_id': self.guest.id}, follow=True)
        self.guest.refresh_from_db()
        self.assertNotEqual(self.guest.role, 'aluno')
        self.assertContains(response, 'Acesso negado.')
