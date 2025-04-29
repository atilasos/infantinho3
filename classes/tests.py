from django.test import TestCase
from django.urls import reverse
from users.models import User
from classes.models import Class
from django.contrib.auth.models import Group

# Create your tests here.

class ClassViewPermissionsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create groups
        prof_group, _ = Group.objects.get_or_create(name='professor')
        admin_group, _ = Group.objects.get_or_create(name='administrador')
        aluno_group, _ = Group.objects.get_or_create(name='aluno')
        
        # Create users with roles
        cls.prof = User.objects.create_user(username='prof', email='prof@escola.pt', password='prof', role='professor', status='ativo')
        cls.admin = User.objects.create_user(username='admin', email='admin@escola.pt', password='admin', role='administrador', status='ativo')
        cls.student = User.objects.create_user(username='aluno1', email='aluno1@escola.pt', password='aluno1', role='aluno', status='ativo')
        cls.other_prof = User.objects.create_user(username='prof2', email='prof2@escola.pt', password='prof2', role='professor', status='ativo')
        cls.guest = User.objects.create_user(username='guest', email='guest@escola.pt', password='guest', status='convidado')
        
        # Add users to groups
        cls.prof.groups.add(prof_group)
        cls.admin.groups.add(admin_group)
        cls.student.groups.add(aluno_group)
        cls.other_prof.groups.add(prof_group)
        
        # Create class and assign teacher & student
        cls.turma = Class.objects.create(name='7A', year=2025)
        cls.turma.teachers.add(cls.prof)
        cls.turma.students.add(cls.student)

    def test_only_professor_of_turma_can_promote(self):
        # Test access denial for a professor NOT teaching the class
        self.client.force_login(self.other_prof)
        url = reverse('add_student', args=[self.turma.id])
        response = self.client.post(url, {'user_id': self.guest.id})
        # Check it redirects (likely due to the internal check, not the decorator)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('class_detail', args=[self.turma.id]))
        # Check user was NOT promoted
        self.guest.refresh_from_db()
        self.assertNotEqual(self.guest.role, 'aluno')
        # Follow redirect to check message (optional, requires session middleware)
        # follow_response = self.client.get(response.url)
        # self.assertContains(follow_response, 'Apenas professores desta turma')
        
    def test_professor_of_turma_can_promote(self):
        """ Test that the assigned professor can successfully promote a guest."""
        # This test is moved from users/tests.py
        self.client.force_login(self.prof)
        url = reverse('add_student', args=[self.turma.id])
        # Need a guest user specific to this test to avoid state issues
        guest_user = User.objects.create_user(username='guest_promote', email='guest_promote@test.com', status='convidado')
        
        response = self.client.post(url, {'user_id': guest_user.id})
        
        # Check intermediate redirect response
        self.assertEqual(response.status_code, 302, "POST request should redirect after success.")
        self.assertEqual(response.url, reverse('class_detail', args=[self.turma.id]), "Should redirect to class detail.")

        # Now check the database state 
        guest_user.refresh_from_db()
        self.assertEqual(guest_user.role, 'aluno', "Role should be 'aluno' after promote_to_role call.")
        self.assertEqual(guest_user.status, 'ativo')
        self.assertIn(guest_user, self.turma.students.all())
        
        # Optionally, follow the redirect now and check the final page content
        final_response = self.client.get(response.url)
        self.assertContains(final_response, 'promovido a aluno')
    
    # === Tests for manage_classes view ===

    def test_manage_classes_get_access(self):
        """Test GET access control for the manage_classes view."""
        url = reverse('manage_classes')
        self.assertEqual(url, '/gerir-turmas/')
        
        # Guest -> Redirect to login
        response_guest = self.client.get(url)
        self.assertEqual(response_guest.status_code, 302)
        self.assertIn(reverse('users:login_choice'), response_guest.url)
        
        # Student -> Redirect/Forbidden (depends on decorator behavior)
        self.client.force_login(self.student)
        response_student = self.client.get(url)
        # user_passes_test redirects by default if test fails
        self.assertEqual(response_student.status_code, 302)
        self.assertIn(reverse('users:login_choice'), response_student.url) 
        # Or check for 403 if you configured user_passes_test differently
        # self.assertEqual(response_student.status_code, 403)
        self.client.logout()
        
        # Professor -> Allowed
        self.client.force_login(self.prof)
        response_prof = self.client.get(url)
        self.assertEqual(response_prof.status_code, 200)
        self.assertTemplateUsed(response_prof, 'classes/manage_classes.html')
        self.client.logout()
        
        # Admin -> Allowed
        self.client.force_login(self.admin)
        response_admin = self.client.get(url)
        self.assertEqual(response_admin.status_code, 200)
        self.assertTemplateUsed(response_admin, 'classes/manage_classes.html')

    def test_manage_classes_post_create_success(self):
        """Test successful class creation via POST by an admin/professor."""
        url = reverse('manage_classes')
        self.assertEqual(url, '/gerir-turmas/')
        initial_class_count = Class.objects.count()
        # Need IDs of users to pass in POST data for ManyToMany field
        post_data = {
            'name': 'Nova Turma Teste',
            'year': 2026,
            'teachers': [self.prof.id, self.other_prof.id]
        }
        
        # Test with Professor
        self.client.force_login(self.prof)
        response_prof = self.client.post(url, post_data)
        self.assertEqual(response_prof.status_code, 302, "Should redirect after successful creation by prof.")
        self.assertRedirects(response_prof, url, msg_prefix="Redirect URL mismatch for prof.")
        self.assertEqual(Class.objects.count(), initial_class_count + 1, "Class count should increase by 1.")
        new_class = Class.objects.get(name='Nova Turma Teste')
        self.assertIn(self.prof, new_class.teachers.all())
        self.assertIn(self.other_prof, new_class.teachers.all())
        self.client.logout()
        
        # Test with Admin (create another class)
        initial_class_count = Class.objects.count()
        post_data['name'] = 'Outra Turma Admin'
        post_data['teachers'] = [self.prof.id] # Only one teacher this time
        self.client.force_login(self.admin)
        response_admin = self.client.post(url, post_data)
        self.assertEqual(response_admin.status_code, 302, "Should redirect after successful creation by admin.")
        self.assertRedirects(response_admin, url, msg_prefix="Redirect URL mismatch for admin.")
        self.assertEqual(Class.objects.count(), initial_class_count + 1, "Class count should increase by 1 for admin.")
        new_class_admin = Class.objects.get(name='Outra Turma Admin')
        self.assertIn(self.prof, new_class_admin.teachers.all())
        self.assertEqual(new_class_admin.teachers.count(), 1)

    def test_manage_classes_post_invalid_data(self):
        """Test POST with invalid data re-renders form with errors."""
        url = reverse('manage_classes')
        self.assertEqual(url, '/gerir-turmas/')
        initial_class_count = Class.objects.count()
        post_data = {
            'name': '', # Invalid: empty name
            'year': 2026,
            'teachers': [self.prof.id]
        }
        self.client.force_login(self.prof)
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200, "Should re-render form on invalid data.")
        self.assertTemplateUsed(response, 'classes/manage_classes.html')
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors) # Check for form errors
        self.assertEqual(Class.objects.count(), initial_class_count, "Class count should not change on invalid POST.")

    def test_manage_classes_post_access_denied(self):
        """Test that unauthorized users cannot create classes via POST."""
        url = reverse('manage_classes')
        self.assertEqual(url, '/gerir-turmas/')
        initial_class_count = Class.objects.count()
        post_data = {'name': 'Test Denied', 'year': 2026, 'teachers': [self.prof.id]}
        
        # Student
        self.client.force_login(self.student)
        response_student = self.client.post(url, post_data)
        self.assertNotEqual(response_student.status_code, 200) # Should not be success
        self.assertTrue(response_student.status_code == 302 or response_student.status_code == 403)
        self.client.logout()
        
        # Guest
        response_guest = self.client.post(url, post_data)
        self.assertEqual(response_guest.status_code, 302)
        self.assertIn(reverse('users:login_choice'), response_guest.url)
        
        self.assertEqual(Class.objects.count(), initial_class_count, "Class count should not change for unauthorized POST.")

    # Add tests for POST (class creation) here later
