# checklists/tests.py
from django.test import TestCase, Client # Removed override_settings for now
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from unittest.mock import patch
from django.contrib.auth.models import Group # Import Group
from rest_framework.test import APITestCase, APIClient

from checklists.models import ChecklistTemplate, ChecklistItem, ChecklistStatus, ChecklistMark
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
            name='Math Basics'
        )
        cls.item1 = ChecklistItem.objects.create(template=cls.template, code='ADD', text='Addition', order=1)
        cls.item2 = ChecklistItem.objects.create(template=cls.template, code='SUB', text='Subtraction', order=2)
        
        cls.status = ChecklistStatus.objects.create(
            template=cls.template, student=cls.student, student_class=cls.class_obj
        )

    def test_template_creation(self):
        self.assertEqual(str(self.template), 'Math Basics v1')
        self.assertEqual(self.template.version, 1)
        self.assertTrue(self.template.is_published)
        self.assertEqual(self.template.items.count(), 2)

    def test_item_creation(self):
        # __str__ shows code or first part of text
        self.assertIn('Addition', str(self.item1))
        self.assertFalse(self.item1.contracted_in_council)

    def test_status_creation(self):
        self.assertEqual(
            str(self.status),
            f"{self.student.username} - {self.template.name} ({self.class_obj.name}) - 0%"
        )
        self.assertEqual(self.status.percent_complete, 0)

    def test_mark_creation_and_status_update(self):
        self.assertEqual(ChecklistMark.objects.count(), 0)
        self.assertEqual(self.status.percent_complete, 0)
        mark1 = ChecklistMark.objects.create(
            status_record=self.status, item=self.item1, mark_status='COMPLETED', marked_by=self.student
        )
        self.assertEqual(ChecklistMark.objects.count(), 1)
        self.assertEqual(mark1.mark_status, 'COMPLETED')
        self.assertFalse(mark1.teacher_validated)
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0)
        mark2 = ChecklistMark.objects.create(
            status_record=self.status, item=self.item2, mark_status='IN_PROGRESS', marked_by=self.student
        )
        self.assertEqual(ChecklistMark.objects.count(), 2)
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0)
        mark2.mark_status = 'COMPLETED'
        mark2.save()
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 100.0)
        mark1.mark_status = 'IN_PROGRESS' 
        mark1.teacher_validated = True 
        mark1.save()
        self.assertFalse(mark1.teacher_validated)
        self.status.refresh_from_db()
        self.assertEqual(self.status.percent_complete, 50.0)

# --- View Tests --- 

class ChecklistViewTests(TestCase):
    """Tests for the Checklist views and workflow."""
    @classmethod
    def setUpTestData(cls):
        # Create groups
        prof_group, _ = Group.objects.get_or_create(name='professor')
        aluno_group, _ = Group.objects.get_or_create(name='aluno')
        admin_group, _ = Group.objects.get_or_create(name='administrador') # In case admin is needed

        cls.admin = User.objects.create_superuser(username='admin_checklists', email='admin@test.com', password='pwd')
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
        
        cls.template = ChecklistTemplate.objects.create(name='Portuguese 5th Grade')
        cls.item1 = ChecklistItem.objects.create(template=cls.template, code='READ', text='Read texts', order=1)
        cls.item2 = ChecklistItem.objects.create(template=cls.template, code='WRITE', text='Write texts', order=2)
        
        cls.status = ChecklistStatus.objects.create(template=cls.template, student=cls.student, student_class=cls.turma)

    # --- Basic Access Tests --- 

    def test_my_checklists_view_requires_login(self):
        my_checklists_url = reverse('checklists:my_checklists')
        login_url = reverse('users:login_choice')
        response = self.client.get(my_checklists_url, follow=True) 
        self.assertRedirects(response, f"{login_url}?next={my_checklists_url}", status_code=302)

    def test_checklist_detail_view_requires_login(self):
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        login_url = reverse('users:login_choice')
        response = self.client.get(detail_url, follow=True)
        self.assertRedirects(response, f"{login_url}?next={detail_url}", status_code=302)

    def test_checklist_turma_view_requires_login(self):
        login_url = reverse('users:login_choice')
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
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
        self.assertEqual(response_my.status_code, 302, "Teacher should be redirected from My Checklists")
        self.assertIn(login_url, response_my.url, "Teacher should be redirected to login for My Checklists")
        
        response_detail = self.client.get(detail_url)
        self.assertEqual(response_detail.status_code, 302, "Teacher should be redirected from Checklist Detail")
        self.assertIn(login_url, response_detail.url, "Teacher should be redirected to login for Checklist Detail")

    # --- Workflow Tests --- 

    def test_student_can_view_and_mark_item(self):
        """Test student accesses detail view and marks an item via POST."""
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        self.client.force_login(self.student)
        
        response_get = self.client.get(detail_url, follow=True)
        self.assertEqual(response_get.status_code, 200) 
        self.assertEqual(response_get.request['PATH_INFO'], detail_url)
        self.assertContains(response_get, self.template.name)
        self.assertContains(response_get, self.item1.text)
        
        response_post = self.client.post(detail_url, {
            'item_id': self.item1.id, 
            'mark_status': 'COMPLETED', 
            'comment': 'Finished it!' 
        }, follow=True) 
        self.assertEqual(response_post.status_code, 200) 
        self.assertContains(response_post, _('Objective updated successfully!'))
        self.assertEqual(response_post.request['PATH_INFO'], detail_url)
        
        mark = ChecklistMark.objects.filter(item=self.item1, status_record=self.status).latest('marked_at')
        self.assertEqual(mark.mark_status, 'COMPLETED')
        self.assertEqual(mark.comment, 'Finished it!')
        self.assertFalse(mark.teacher_validated)
        self.assertEqual(mark.marked_by, self.student)

    def test_teacher_view_highlights_council_items(self):
        self.item1.contracted_in_council = True
        self.item1.save(update_fields=['contracted_in_council'])
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        self.client.force_login(self.teacher)
        response = self.client.get(turma_url)
        self.assertContains(response, 'council-item-header')
        self.assertContains(response, 'data-council="true"')

    def test_student_detail_highlights_council_items(self):
        self.item1.contracted_in_council = True
        self.item1.save(update_fields=['contracted_in_council'])
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        self.client.force_login(self.student)
        response = self.client.get(detail_url)
        self.assertContains(response, 'council-badge')
        self.assertContains(response, 'data-council="true"')

    def test_teacher_can_view_turma_and_validate(self):
        """Test teacher accesses class view and validates/rectifies a mark via POST."""
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        
        ChecklistMark.objects.create(status_record=self.status, item=self.item1, mark_status='COMPLETED', marked_by=self.student)
        
        self.client.force_login(self.teacher)
        
        response_get = self.client.get(turma_url, follow=True)
        self.assertEqual(response_get.status_code, 200) 
        self.assertEqual(response_get.request['PATH_INFO'], turma_url)
        self.assertContains(response_get, self.template.name)
        self.assertContains(response_get, self.student.username)
        self.assertContains(response_get, self.item1.text)

        response_post = self.client.post(turma_url, {
            'student_id': self.student.id, 
            'item_id': self.item1.id, 
            'mark_status': 'COMPLETED', 
            'comment': 'Validated by teacher' 
        }, follow=True)
        self.assertEqual(response_post.status_code, 200) 
        success_msg = _('Mark validated/rectified for {student_name}.').format(
            student_name=self.student.get_full_name() or self.student.username
        )
        self.assertContains(response_post, success_msg)
        self.assertEqual(response_post.request['PATH_INFO'], turma_url)

        mark = ChecklistMark.objects.filter(item=self.item1, status_record=self.status).latest('marked_at')
        self.assertEqual(mark.mark_status, 'COMPLETED')
        self.assertEqual(mark.comment, 'Validated by teacher')
        self.assertTrue(mark.teacher_validated)
        self.assertEqual(mark.marked_by, self.teacher)

    # --- Permission Tests --- 

    def test_other_student_cannot_access_checklist_detail(self):
        """Test a student cannot access checklist detail if not assigned."""
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        
        self.client.force_login(self.other_student)
        response = self.client.get(detail_url, follow=True) 
        self.assertEqual(response.status_code, 404) 
        
        response_post = self.client.post(detail_url, {'item_id': self.item1.id, 'mark_status': 'COMPLETED'}, follow=True)
        self.assertEqual(response_post.status_code, 404)

    def test_other_teacher_cannot_access_checklist_turma(self):
        """Test a teacher not assigned to the class cannot access turma view."""
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])
        class_detail_url = reverse('classes:class_list')
        
        self.client.force_login(self.other_teacher)
        response = self.client.get(turma_url, follow=True)
        self.assertRedirects(response, class_detail_url, status_code=302, target_status_code=200) 
        
        response_post = self.client.post(turma_url, {'student_id': self.student.id, 'item_id': self.item1.id, 'mark_status': 'COMPLETED'}, follow=True)
        self.assertRedirects(response_post, class_detail_url, status_code=302, target_status_code=200)

    # --- Notification Tests --- 

    @patch('checklists.views.dispatch_notification')
    def test_notifications_on_update(self, mock_dispatch):
        """Test email notifications are triggered correctly."""
        detail_url = reverse('checklists:checklist_detail', args=[self.template.id])
        turma_url = reverse('checklists:checklist_turma', args=[self.turma.id, self.template.id])

        # Student marks item -> teachers should be notified
        self.client.force_login(self.student)
        post_response = self.client.post(detail_url, {'item_id': self.item1.id, 'mark_status': 'COMPLETED', 'comment': 'Done'})
        self.assertEqual(post_response.status_code, 302)

        self.assertTrue(mock_dispatch.called, "dispatch_notification was not called after student update")
        _, kwargs = mock_dispatch.call_args
        self.assertIn(self.teacher.email, kwargs['recipients'])
        self.assertEqual(kwargs['category'], 'checklist_student_update')
        mock_dispatch.reset_mock()

        # Teacher validates -> student should be notified
        self.client.force_login(self.teacher)
        post_response_teacher = self.client.post(turma_url, {
            'student_id': self.student.id, 
            'item_id': self.item1.id, 
            'mark_status': 'COMPLETED', 
            'comment': 'Good job'
        })
        self.assertEqual(post_response_teacher.status_code, 302) 

        self.assertTrue(mock_dispatch.called, "dispatch_notification was not called after teacher update")
        _, kwargs2 = mock_dispatch.call_args
        self.assertIn(self.student.email, kwargs2['recipients'])
        self.assertEqual(kwargs2['category'], 'checklist_teacher_update')


class ChecklistAPITests(APITestCase):
    """Smoke tests for the headless checklist endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username='api_student', email='api_student@test.com', password='pwd', role='aluno', status='ativo'
        )
        cls.teacher = User.objects.create_user(
            username='api_teacher', email='api_teacher@test.com', password='pwd', role='professor', status='ativo'
        )

        cls.turma = Class.objects.create(name='API Turma', year=2025)
        cls.turma.students.add(cls.student)
        cls.turma.teachers.add(cls.teacher)

        cls.template = ChecklistTemplate.objects.create(name='API Template')
        cls.template.classes.add(cls.turma)
        cls.item = ChecklistItem.objects.create(template=cls.template, code='API1', text='Objetivo API', order=1)

        cls.status = ChecklistStatus.objects.create(
            template=cls.template,
            student=cls.student,
            student_class=cls.turma,
        )
        cls.mark = ChecklistMark.objects.create(
            status_record=cls.status,
            item=cls.item,
            mark_status='IN_PROGRESS',
            marked_by=cls.student,
        )

    def test_student_lists_only_their_statuses(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('checklist-status-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['template']['name'], self.template.name)

    def test_student_updates_mark_to_completed(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('checklist-mark-detail', args=[self.mark.id])
        response = self.client.patch(
            url,
            {'mark_status': 'COMPLETED', 'comment': 'feito'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.mark.refresh_from_db()
        self.assertEqual(self.mark.mark_status, 'COMPLETED')
        self.assertFalse(self.mark.teacher_validated)
        self.assertEqual(self.mark.comment, 'feito')

    def test_student_cannot_validate_mark(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('checklist-mark-detail', args=[self.mark.id])
        response = self.client.patch(
            url,
            {'mark_status': 'VALIDATED'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.mark.refresh_from_db()
        self.assertEqual(self.mark.mark_status, 'IN_PROGRESS')
        self.assertFalse(self.mark.teacher_validated)

    def test_teacher_validates_completed_mark(self):
        self.mark.mark_status = 'COMPLETED'
        self.mark.save()

        self.client.force_authenticate(user=self.teacher)
        url = reverse('checklist-mark-detail', args=[self.mark.id])
        response = self.client.patch(
            url,
            {'teacher_validated': True},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.mark.refresh_from_db()
        self.assertTrue(self.mark.teacher_validated)

    def test_professor_creates_template_with_items(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('checklist-template-list')
        payload = {
            'name': 'Novo Modelo Avaliação',
            'description': 'Modelo criado via API.',
            'version': 1,
            'class_ids': [self.turma.id],
            'items': [
                {'code': 'OBJ1', 'text': 'Objetivo 1', 'order': 1, 'contracted_in_council': False},
                {'code': 'OBJ2', 'text': 'Objetivo 2', 'order': 2, 'contracted_in_council': True},
            ],
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        template_id = response.data['id']
        template = ChecklistTemplate.objects.get(id=template_id)
        self.assertEqual(template.items.count(), 2)
        self.assertEqual(template.classes.count(), 1)

    def test_student_cannot_create_template(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('checklist-template-list')
        response = self.client.post(url, {'name': 'Modelo inválido', 'version': 1}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_professor_updates_template_items(self):
        self.client.force_authenticate(user=self.teacher)
        url = reverse('checklist-template-detail', args=[self.template.id])
        payload = {
            'name': 'API Template Atualizado',
            'description': 'Atualizado',
            'version': 2,
            'items': [
                {'id': self.item.id, 'code': 'API1', 'text': 'Objetivo API editado', 'order': 1, 'contracted_in_council': False},
                {'code': 'API2', 'text': 'Novo objetivo', 'order': 2, 'contracted_in_council': False},
            ],
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.template.refresh_from_db()
        self.assertEqual(self.template.version, 2)
        self.assertEqual(self.template.items.count(), 2)
        self.assertTrue(self.template.items.filter(code='API2').exists())

    def test_student_creates_status_from_template(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('checklist-status-list')
        fresh_template = ChecklistTemplate.objects.create(name='Template Novo')
        fresh_template.classes.add(self.turma)
        ChecklistItem.objects.create(template=fresh_template, code='N1', text='Item novo', order=1)
        payload = {
            'template_id': fresh_template.id,
            'student_class_id': self.turma.id,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        status_id = response.data['id']
        status = ChecklistStatus.objects.get(id=status_id)
        self.assertEqual(status.student, self.student)
        self.assertEqual(status.template_version, fresh_template.version)
        self.assertEqual(status.marks.count(), fresh_template.items.count())

    def test_student_cannot_duplicate_status(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('checklist-status-list')
        payload = {
            'template_id': self.template.id,
            'student_class_id': self.turma.id,
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_student_updates_notes_and_submits(self):
        template = ChecklistTemplate.objects.create(name='Template Autosave', version=2)
        template.classes.add(self.turma)
        ChecklistItem.objects.create(template=template, code='AUTO', text='Item autosave', order=1)
        status = ChecklistStatus.objects.create(
            template=template,
            template_version=template.version,
            student=self.student,
            student_class=self.turma,
        )
        status.initialise_marks()
        self.client.force_authenticate(user=self.student)
        url = reverse('checklist-status-detail', args=[status.id])
        resp_notes = self.client.patch(url, {'student_notes': 'Notas automáticas'}, format='json')
        self.assertEqual(resp_notes.status_code, 200)
        status.refresh_from_db()
        self.assertEqual(status.student_notes, 'Notas automáticas')
        resp_submit = self.client.patch(url, {'state': 'submitted'}, format='json')
        self.assertEqual(resp_submit.status_code, 200)
        status.refresh_from_db()
        self.assertEqual(status.state, ChecklistStatus.LVState.SUBMITTED)
        self.assertIsNotNone(status.submitted_at)
