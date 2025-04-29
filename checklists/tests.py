# checklists/tests.py
from django.test import TestCase, Client # Removed override_settings for now
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch
from django.contrib.auth.models import Group # Import Group

from .models import ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark
from classes.models import Class

User = get_user_model()

# --- Model Tests --- 

class ChecklistModelTests(TestCase):
    """Tests for the Checklist models."""
    @classmethod
    def setUpTestData(cls):
        """Set up non-modified objects used by all test methods."""
        cls.student = User.objects.create_user(username='student1', email='s1@test.com', password='pwd', role='aluno', status='ativo')
        cls.teacher = User.objects.create_user(username='teacher1', email='t1@test.com', password='pwd', role='professor', status='ativo')
        cls.class_obj = Class.objects.create(name='Test Class', year=2024)
        cls.class_obj.students.add(cls.student)
        cls.class_obj.teachers.add(cls.teacher)
        
        cls.template = ChecklistTemplate.objects.create(
            name='Math Basics', grade_level=5, subject='Math'
        )
        cls.item1 = ChecklistItem.objects.create(template=cls.template, description='Addition', order=1)
        cls.item2 = ChecklistItem.objects.create(template=cls.template, description='Subtraction', order=2)
        
        cls.status = ChecklistStatus.objects.create(
            template=cls.template, student=cls.student, student_class=cls.class_obj
        )

    def test_template_creation(self):
        self.assertEqual(str(self.template), "Math - Grade 5: Math Basics")
        self.assertEqual(self.template.items.count(), 2)

    def test_item_creation(self):
        self.assertEqual(str(self.item1), "Math Basics - Addition...")

    def test_status_creation(self):
        self.assertEqual(
            str(self.status),
            f"student1 - Math Basics (Test Class) - 0%"
        )
        self.assertEqual(self.status.percent_complete, 0)

    def test_mark_creation_and_status_update(self):
        self.assertEqual(ChecklistMark.objects.count(), 0)
        self.assertEqual(self.status.percent_complete, 0)
        mark1 = ChecklistMark.objects.create(
            status=self.status, item=self.item1, mark_status='completed', marked_by=self.student
        )
        self.assertEqual(ChecklistMark.objects.count(), 1)
        self.assertEqual(mark1.mark_status, 'completed')
        self.assertFalse(mark1.teacher_validated)
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0)
        mark2 = ChecklistMark.objects.create(
            status=self.status, item=self.item2, mark_status='in_progress', marked_by=self.student
        )
        self.assertEqual(ChecklistMark.objects.count(), 2)
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0)
        mark2.mark_status = 'completed'
        mark2.save()
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 100.0)
        mark1.mark_status = 'in_progress' 
        mark1.teacher_validated = True 
        mark1.save()
        self.assertFalse(mark1.teacher_validated)
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0)

# --- View Tests --- 

# Removed @override_settings
class ChecklistViewTests(TestCase):
    """Tests for the Checklist views and workflow."""
    @classmethod
    def setUpTestData(cls):
        # Create groups
        prof_group, _ = Group.objects.get_or_create(name='professor')
        aluno_group, _ = Group.objects.get_or_create(name='aluno')
        admin_group, _ = Group.objects.get_or_create(name='administrador') # In case admin is needed

        cls.admin = User.objects.create_superuser(username='admin', email='admin@test.com', password='pwd')
        cls.teacher = User.objects.create_user(username='prof', email='prof@test.com', password='pwd', role='professor', status='ativo')
        cls.student = User.objects.create_user(username='aluno', email='aluno@test.com', password='pwd', role='aluno', status='ativo')
        cls.other_student = User.objects.create_user(username='outro', email='outro@test.com', password='pwd', role='aluno', status='ativo')
        cls.other_teacher = User.objects.create_user(username='prof2', email='prof2@test.com', password='pwd', role='professor', status='ativo')
        
        # Add users to groups
        cls.admin.groups.add(admin_group) # Add admin to its group
        cls.teacher.groups.add(prof_group)
        cls.student.groups.add(aluno_group)
        cls.other_student.groups.add(aluno_group)
        cls.other_teacher.groups.add(prof_group)
        
        cls.turma = Class.objects.create(name='5A', year=2024)
        cls.turma.teachers.add(cls.teacher)
        cls.turma.students.add(cls.student)
        
        cls.template = ChecklistTemplate.objects.create(name='Portuguese 5th Grade', grade_level=5, subject='Portuguese')
        cls.item1 = ChecklistItem.objects.create(template=cls.template, description='Read texts', order=1)
        cls.item2 = ChecklistItem.objects.create(template=cls.template, description='Write texts', order=2, council_agreed=True)
        
        cls.status = ChecklistStatus.objects.create(template=cls.template, student=cls.student, student_class=cls.turma)
        
        # URLs should be defined in tests using reverse, not here
        # cls.my_checklists_url = reverse('checklists:my_checklists')
        # cls.detail_url = reverse('checklists:checklist_detail', args=[cls.template.id])
        # cls.turma_url = reverse('checklists:checklist_turma', args=[cls.turma.id, cls.template.id])
        # cls.login_url = reverse('users:login_choice')
        # cls.class_detail_url = reverse('class_detail', args=[cls.turma.id])

    # --- Basic Access Tests --- 

    def test_my_checklists_view_requires_login(self):
        my_checklists_url = reverse('checklists:my_checklists')
        login_url = reverse('users:login_choice')
        # Use follow=True on the GET request
        response = self.client.get(my_checklists_url, follow=True) 
        # Assert the final redirect destination and status code (usually 302 for login)
        self.assertRedirects(response, f"{login_url}?next={my_checklists_url}", status_code=302)

    def test_checklist_detail_view_requires_login(self):
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        login_url = reverse('users:login_choice')
        response = self.client.get(detail_url, follow=True)
        self.assertRedirects(response, f"{login_url}?next={detail_url}", status_code=302)

    def test_checklist_turma_view_requires_login(self):
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        login_url = reverse('users:login_choice')
        response = self.client.get(turma_url, follow=True)
        self.assertRedirects(response, f"{login_url}?next={turma_url}", status_code=302)

    # --- Group Permission Tests ---
    def test_student_views_access(self):
        """Test student access to student views and denial for teacher views."""
        my_checklists_url = reverse('checklists:my_checklists')
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        login_url = reverse('users:login_choice')
        
        self.client.force_login(self.student)
        
        response_my = self.client.get(my_checklists_url)
        self.assertEqual(response_my.status_code, 200, "Student should access My Checklists")
        
        response_detail = self.client.get(detail_url)
        self.assertEqual(response_detail.status_code, 200, "Student should access Checklist Detail")
        
        response_turma = self.client.get(turma_url)
        # Should redirect to login because student doesn't have 'professor' group
        self.assertEqual(response_turma.status_code, 302, "Student should be redirected from Turma view")
        self.assertIn(login_url, response_turma.url, "Student should be redirected to login for Turma view")

    def test_teacher_views_access(self):
        """Test teacher access to teacher views and denial for student views."""
        my_checklists_url = reverse('checklists:my_checklists')
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        login_url = reverse('users:login_choice')

        self.client.force_login(self.teacher)
        
        response_turma = self.client.get(turma_url)
        self.assertEqual(response_turma.status_code, 200, "Teacher should access Turma view")
        
        response_my = self.client.get(my_checklists_url)
        # Should redirect to login because teacher doesn't have 'aluno' group
        self.assertEqual(response_my.status_code, 302, "Teacher should be redirected from My Checklists")
        self.assertIn(login_url, response_my.url, "Teacher should be redirected to login for My Checklists")
        
        response_detail = self.client.get(detail_url)
        # Should redirect to login because teacher doesn't have 'aluno' group
        self.assertEqual(response_detail.status_code, 302, "Teacher should be redirected from Checklist Detail")
        self.assertIn(login_url, response_detail.url, "Teacher should be redirected to login for Checklist Detail")

    # --- Workflow Tests --- 

    def test_student_can_view_and_mark_item(self):
        """Test student accesses detail view and marks an item via POST."""
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id]) # Define URL here
        self.client.force_login(self.student)
        
        # GET request - Use follow=True 
        response_get = self.client.get(detail_url, follow=True)
        self.assertEqual(response_get.status_code, 200) 
        self.assertEqual(response_get.request['PATH_INFO'], detail_url)
        self.assertContains(response_get, self.template.name)
        self.assertContains(response_get, self.item1.description)
        
        # POST request - follow=True is already default for POST redirects
        response_post = self.client.post(detail_url, {
            'item_id': self.item1.id, 
            'mark_status': 'completed', 
            'comment': 'Finished it!' 
        }, follow=True) 
        self.assertEqual(response_post.status_code, 200) 
        self.assertContains(response_post, "Objective updated successfully!")
        self.assertEqual(response_post.request['PATH_INFO'], detail_url)
        
        mark = ChecklistMark.objects.filter(item=self.item1, status=self.status).latest('marked_at')
        self.assertEqual(mark.mark_status, 'completed')
        self.assertEqual(mark.comment, 'Finished it!')
        self.assertFalse(mark.teacher_validated)
        self.assertEqual(mark.marked_by, self.student)

    def test_teacher_can_view_turma_and_validate(self):
        """Test teacher accesses class view and validates/rectifies a mark via POST."""
        # Define URLs needed for this test
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        
        ChecklistMark.objects.create(status=self.status, item=self.item1, mark_status='completed', marked_by=self.student)
        
        self.client.force_login(self.teacher)
        
        # GET request - Use follow=True
        response_get = self.client.get(turma_url, follow=True)
        self.assertEqual(response_get.status_code, 200) 
        self.assertEqual(response_get.request['PATH_INFO'], turma_url)
        self.assertContains(response_get, self.template.name)
        self.assertContains(response_get, self.student.username)
        self.assertContains(response_get, self.item1.description)

        # POST request
        response_post = self.client.post(turma_url, {
            'student_id': self.student.id, 
            'item_id': self.item1.id, 
            'mark_status': 'completed', 
            'comment': 'Validated by teacher' 
        }, follow=True)
        self.assertEqual(response_post.status_code, 200) 
        self.assertContains(response_post, "Mark validated/rectified")
        self.assertEqual(response_post.request['PATH_INFO'], turma_url)

        mark = ChecklistMark.objects.filter(item=self.item1, status=self.status).latest('marked_at')
        self.assertEqual(mark.mark_status, 'completed')
        self.assertEqual(mark.comment, 'Validated by teacher')
        self.assertTrue(mark.teacher_validated)
        self.assertEqual(mark.marked_by, self.teacher)

    # --- Permission Tests --- 

    def test_other_student_cannot_access_checklist_detail(self):
        """Test a student cannot access checklist detail if not assigned."""
        # Define URL needed
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        
        self.client.force_login(self.other_student)
        # Use follow=True and expect 404 at the end
        response = self.client.get(detail_url, follow=True) 
        self.assertEqual(response.status_code, 404) 
        
        response_post = self.client.post(detail_url, {'item_id': self.item1.id, 'mark_status': 'completed'}, follow=True)
        self.assertEqual(response_post.status_code, 404)

    def test_other_teacher_cannot_access_checklist_turma(self):
        """Test a teacher not assigned to the class cannot access turma view."""
        # Define URLs needed
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        class_detail_url = reverse('class_detail', args=[self.turma.id]) # Target for redirect
        
        self.client.force_login(self.other_teacher)
        # Use follow=True for GET
        response = self.client.get(turma_url, follow=True)
        # Check the final redirect target (class detail page)
        self.assertRedirects(response, class_detail_url, status_code=302, target_status_code=200) # Expect final page to be OK
        
        # Use follow=True for POST
        response_post = self.client.post(turma_url, {'student_id': self.student.id, 'item_id': self.item1.id, 'mark_status': 'completed'}, follow=True)
        self.assertRedirects(response_post, class_detail_url, status_code=302, target_status_code=200)

    # --- Notification Tests --- 

    @patch('checklists.views.send_mail')
    def test_notifications_on_update(self, mock_send_mail):
        """Test email notifications are triggered correctly."""
        # Define URLs needed
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        
        # Student marks item -> teachers should be notified
        self.client.force_login(self.student)
        post_response = self.client.post(detail_url, {'item_id': self.item1.id, 'mark_status': 'completed', 'comment': 'Done'})
        # Check POST redirects successfully (status 302)
        self.assertEqual(post_response.status_code, 302) # POST should redirect before following

        self.assertTrue(mock_send_mail.called, "send_mail was not called after student update")
        args, kwargs = mock_send_mail.call_args
        self.assertIn(self.teacher.email, args[3]) 
        mock_send_mail.reset_mock() 
        
        # Teacher validates -> student should be notified
        self.client.force_login(self.teacher)
        post_response_teacher = self.client.post(turma_url, {
            'student_id': self.student.id, 
            'item_id': self.item1.id, 
            'mark_status': 'completed', 
            'comment': 'Good job'
        })
        self.assertEqual(post_response_teacher.status_code, 302) # POST should redirect
        
        self.assertTrue(mock_send_mail.called, "send_mail was not called after teacher update")
        args2, kwargs2 = mock_send_mail.call_args
        self.assertIn(self.student.email, args2[3])
