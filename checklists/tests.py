# checklists/tests.py
from django.test import TestCase, Client, override_settings # Import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch

from .models import ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark
from classes.models import Class

User = get_user_model()

# Remove _force_slash helper

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
        self.assertEqual(str(self.item1), "(Math Basics) Addition")

    def test_status_creation(self):
        self.assertEqual(
            str(self.status),
            f"student1 - Math Basics (Test Class) - 0%" # Initial percentage
        )
        self.assertEqual(self.status.percent_complete, 0)

    def test_mark_creation_and_status_update(self):
        # Initial state
        self.assertEqual(ChecklistMark.objects.count(), 0)
        self.assertEqual(self.status.percent_complete, 0)

        # Mark item 1 as completed
        mark1 = ChecklistMark.objects.create(
            status=self.status, item=self.item1, mark_status='completed', marked_by=self.student
        )
        self.assertEqual(ChecklistMark.objects.count(), 1)
        self.assertEqual(mark1.mark_status, 'completed')
        self.assertFalse(mark1.teacher_validated)
        # Status should be updated via mark save signal/method
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0) # 1 out of 2 items

        # Mark item 2 as in progress
        mark2 = ChecklistMark.objects.create(
            status=self.status, item=self.item2, mark_status='in_progress', marked_by=self.student
        )
        self.assertEqual(ChecklistMark.objects.count(), 2)
        # Status percentage shouldn't change
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0)

        # Mark item 2 as completed
        mark2.mark_status = 'completed'
        mark2.save()
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 100.0)
        
        # Mark item 1 back to in_progress (should reset validation and percentage)
        mark1.mark_status = 'in_progress' 
        mark1.teacher_validated = True # Simulate it was validated before
        mark1.save()
        self.assertFalse(mark1.teacher_validated) # Should be reset by save method
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0) # Back to 1 out of 2

# --- View Tests --- 

@override_settings(APPEND_SLASH=False) # Disable APPEND_SLASH for view tests
class ChecklistViewTests(TestCase):
    """Tests for the Checklist views and workflow."""
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', email='admin@test.com', password='pwd')
        self.teacher = User.objects.create_user(username='prof', email='prof@test.com', password='pwd', role='professor', status='ativo')
        self.student = User.objects.create_user(username='aluno', email='aluno@test.com', password='pwd', role='aluno', status='ativo')
        self.other_student = User.objects.create_user(username='outro', email='outro@test.com', password='pwd', role='aluno', status='ativo')
        self.other_teacher = User.objects.create_user(username='prof2', email='prof2@test.com', password='pwd', role='professor', status='ativo')
        
        self.turma = Class.objects.create(name='5A', year=2024)
        self.turma.teachers.add(self.teacher)
        self.turma.students.add(self.student)
        
        self.template = ChecklistTemplate.objects.create(name='Portuguese 5th Grade', grade_level=5, subject='Portuguese')
        self.item1 = ChecklistItem.objects.create(template=self.template, description='Read texts', order=1)
        self.item2 = ChecklistItem.objects.create(template=self.template, description='Write texts', order=2, council_agreed=True)
        
        self.status = ChecklistStatus.objects.create(template=self.template, student=self.student, student_class=self.turma)
        
        # URLs (no need for _force_slash now)
        self.my_checklists_url = reverse('checklists:my_checklists')
        self.detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        self.turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        self.login_url = reverse('users:login_choice') # Assuming namespace 'users'
        self.class_detail_url = reverse('class_detail', args=[self.turma.id]) # No namespace needed if global

    # --- Basic Access Tests --- 

    def test_my_checklists_view_requires_login(self):
        response = self.client.get(self.my_checklists_url)
        # Expect redirect (302) to login
        self.assertRedirects(response, f"{self.login_url}?next={self.my_checklists_url}", status_code=302)

    def test_checklist_detail_view_requires_login(self):
        response = self.client.get(self.detail_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.detail_url}", status_code=302)

    def test_checklist_turma_view_requires_login(self):
        response = self.client.get(self.turma_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.turma_url}", status_code=302)

    # --- Workflow Tests --- 

    def test_student_can_view_and_mark_item(self):
        """Test student accesses detail view and marks an item via POST."""
        self.client.force_login(self.student)
        
        # GET request 
        response_get = self.client.get(self.detail_url)
        self.assertEqual(response_get.status_code, 200) # Expect 200 OK directly
        self.assertContains(response_get, self.template.name)
        self.assertContains(response_get, self.item1.description)
        
        # POST request to mark item1 as completed
        response_post = self.client.post(self.detail_url, {
            'item_id': self.item1.id, 
            'mark_status': 'completed', 
            'comment': 'Finished it!' 
        }, follow=True) 
        self.assertEqual(response_post.status_code, 200) # Should redirect back to detail view
        self.assertContains(response_post, "Objective updated successfully!")
        self.assertEqual(response_post.request['PATH_INFO'], self.detail_url)
        
        # Verify mark was created correctly in DB
        mark = ChecklistMark.objects.filter(item=self.item1, status=self.status).latest('marked_at')
        self.assertEqual(mark.mark_status, 'completed')
        self.assertEqual(mark.comment, 'Finished it!')
        self.assertFalse(mark.teacher_validated)
        self.assertEqual(mark.marked_by, self.student)

    def test_teacher_can_view_turma_and_validate(self):
        """Test teacher accesses class view and validates/rectifies a mark via POST."""
        ChecklistMark.objects.create(status=self.status, item=self.item1, mark_status='completed', marked_by=self.student)
        
        self.client.force_login(self.teacher)
        
        # GET request 
        response_get = self.client.get(self.turma_url)
        self.assertEqual(response_get.status_code, 200) # Expect 200 OK
        self.assertContains(response_get, self.template.name)
        self.assertContains(response_get, self.student.username)
        self.assertContains(response_get, self.item1.description)

        # POST request to validate/rectify item1 for the student
        response_post = self.client.post(self.turma_url, {
            'student_id': self.student.id, 
            'item_id': self.item1.id, 
            'mark_status': 'completed', 
            'comment': 'Validated by teacher' 
        }, follow=True)
        self.assertEqual(response_post.status_code, 200) # Redirects back to turma view
        self.assertContains(response_post, "Mark validated/rectified")
        self.assertEqual(response_post.request['PATH_INFO'], self.turma_url)

        # Verify a new mark was created with validation
        mark = ChecklistMark.objects.filter(item=self.item1, status=self.status).latest('marked_at')
        self.assertEqual(mark.mark_status, 'completed')
        self.assertEqual(mark.comment, 'Validated by teacher')
        self.assertTrue(mark.teacher_validated)
        self.assertEqual(mark.marked_by, self.teacher)

    # --- Permission Tests --- 

    def test_other_student_cannot_access_checklist_detail(self):
        """Test a student cannot access checklist detail if not assigned."""
        self.client.force_login(self.other_student)
        response = self.client.get(self.detail_url)
        # Expect 404 because the ChecklistStatus object doesn't exist for this student/template
        self.assertEqual(response.status_code, 404) 
        
        response_post = self.client.post(self.detail_url, {'item_id': self.item1.id, 'mark_status': 'completed'})
        self.assertEqual(response_post.status_code, 404)

    def test_other_teacher_cannot_access_checklist_turma(self):
        """Test a teacher not assigned to the class cannot access turma view."""
        self.client.force_login(self.other_teacher)
        response = self.client.get(self.turma_url)
        # Permission check in view dispatch redirects (302) to class detail page
        self.assertRedirects(response, self.class_detail_url, status_code=302)
        
        response_post = self.client.post(self.turma_url, {'student_id': self.student.id, 'item_id': self.item1.id, 'mark_status': 'completed'})
        self.assertRedirects(response_post, self.class_detail_url, status_code=302)

    # --- Notification Tests --- 

    @patch('checklists.views.send_mail')
    def test_notifications_on_update(self, mock_send_mail):
        """Test email notifications are triggered correctly."""
        # Student marks item -> teachers should be notified
        self.client.force_login(self.student)
        post_response = self.client.post(self.detail_url, {'item_id': self.item1.id, 'mark_status': 'completed', 'comment': 'Done'})
        self.assertEqual(post_response.status_code, 302) # Check POST redirects 

        self.assertTrue(mock_send_mail.called, "send_mail was not called after student update")
        args, kwargs = mock_send_mail.call_args
        self.assertIn(self.teacher.email, args[3]) 
        mock_send_mail.reset_mock() 
        
        # Teacher validates -> student should be notified
        self.client.force_login(self.teacher)
        post_response_teacher = self.client.post(self.turma_url, {
            'student_id': self.student.id, 
            'item_id': self.item1.id, 
            'mark_status': 'completed', 
            'comment': 'Good job'
        })
        self.assertEqual(post_response_teacher.status_code, 302)
        
        self.assertTrue(mock_send_mail.called, "send_mail was not called after teacher update")
        args2, kwargs2 = mock_send_mail.call_args
        self.assertIn(self.student.email, args2[3])
