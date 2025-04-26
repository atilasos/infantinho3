from django.test import TestCase
from django.urls import reverse
from users.models import User
from classes.models import Class

# Create your tests here.

class UserPromotionFlowTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', email='admin@escola.pt', password='admin', role='admin', status='ativo')
        self.prof = User.objects.create_user(username='prof', email='prof@escola.pt', password='prof', role='professor', status='ativo')
        self.guest = User.objects.create_user(username='guest', email='guest@escola.pt', password='guest', status='convidado')
        self.turma = Class.objects.create(name='7A', year=2025)
        self.turma.teachers.add(self.prof)

    def test_promote_guest_to_aluno_by_professor(self):
        self.client.force_login(self.prof)
        url = reverse('add_student', args=[self.turma.id])
        response = self.client.post(url, {'user_id': self.guest.id}, follow=True)
        self.guest.refresh_from_db()
        self.assertEqual(self.guest.role, 'aluno')
        self.assertEqual(self.guest.status, 'ativo')
        self.assertIn(self.guest, self.turma.students.all())
        self.assertContains(response, 'promovido a aluno')

    def test_promote_guest_to_professor_by_admin(self):
        self.client.force_login(self.admin)
        self.guest.role = None
        self.guest.status = 'convidado'
        self.guest.save()
        self.guest.promote_to_role('professor')
        self.guest.refresh_from_db()
        self.assertEqual(self.guest.role, 'professor')
        self.assertEqual(self.guest.status, 'ativo')
