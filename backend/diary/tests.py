from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from classes.models import Class
from diary.models import DiaryEntry, DiarySession
from users.models import User


class DiaryAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = User.objects.create_user(
            username='teacher_diary',
            email='teacher_diary@test.com',
            password='pass12345',
            role='professor',
            status='ativo',
        )
        cls.student = User.objects.create_user(
            username='student_diary',
            email='student_diary@test.com',
            password='pass12345',
            role='aluno',
            status='ativo',
        )
        cls.outsider = User.objects.create_user(
            username='outsider_diary',
            email='outsider_diary@test.com',
            password='pass12345',
            role='aluno',
            status='ativo',
        )

        cls.turma = Class.objects.create(name='Diário', year=2025)
        cls.turma.teachers.add(cls.teacher)
        cls.turma.students.add(cls.student)

        cls.session = DiarySession.objects.create(turma=cls.turma, status='ACTIVE')
        DiaryEntry.objects.create(
            session=cls.session,
            column='GOSTEI',
            content='Trabalhámos em grupo e funcionou bem.',
            author=cls.student,
        )

        cls.archived_session = DiarySession.objects.create(
            turma=cls.turma,
            status='ARCHIVED',
            end_date=timezone.localdate(),
        )
        DiaryEntry.objects.create(
            session=cls.archived_session,
            column='QUEREMOS',
            content='Visitar o museu da eletricidade.',
            author=cls.teacher,
        )

    def test_student_fetches_active_diary(self):
        self.client.force_authenticate(self.student)
        url = reverse('class-diary-active', args=[self.turma.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['class']['id'], self.turma.id)
        self.assertEqual(payload['session']['id'], self.session.id)
        columns = {col['key']: col for col in payload['columns']}
        self.assertIn('GOSTEI', columns)
        self.assertEqual(len(columns['GOSTEI']['entries']), 1)

    def test_outsider_cannot_access_diary(self):
        self.client.force_authenticate(self.outsider)
        url = reverse('class-diary-active', args=[self.turma.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_adds_entry(self):
        self.client.force_authenticate(self.student)
        url = reverse('class-diary-entry', args=[self.turma.id])
        response = self.client.post(
            url,
            {'column': 'FIZEMOS', 'content': 'Preparamos a exposição de ciências.'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DiaryEntry.objects.filter(session=self.session).count(), 2)

    def test_teacher_starts_new_session(self):
        self.client.force_authenticate(self.teacher)
        url = reverse('class-diary-start', args=[self.turma.id])
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'ARCHIVED')
        self.assertEqual(DiarySession.objects.filter(turma=self.turma, status='ACTIVE').count(), 1)

    def test_teacher_lists_sessions(self):
        self.client.force_authenticate(self.teacher)
        url = reverse('class-diary-sessions', args=[self.turma.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(len(payload), 2)

    def test_student_cannot_list_sessions(self):
        self.client.force_authenticate(self.student)
        url = reverse('class-diary-sessions', args=[self.turma.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_fetches_archived_session(self):
        self.client.force_authenticate(self.teacher)
        url = reverse('class-diary-session-detail', args=[self.turma.id, self.archived_session.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['session']['status'], 'ARCHIVED')
        columns = {col['key']: col for col in payload['columns']}
        self.assertEqual(len(columns['QUEREMOS']['entries']), 1)
