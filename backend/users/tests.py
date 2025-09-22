from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.test import override_settings # For changing settings in tests
from unittest.mock import patch, MagicMock # For mocking external calls
from django.contrib.auth.models import Group # Import Group
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User, GuardianRelation
from classes.models import Class

# Create your tests here.

class UserPromotionFlowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create groups first if they don't exist (idempotent)
        prof_group, _ = Group.objects.get_or_create(name='professor')
        admin_group, _ = Group.objects.get_or_create(name='admin')
        aluno_group, _ = Group.objects.get_or_create(name='aluno')
        
        cls.admin = User.objects.create_user(username='admin_test', email='admin@escola.pt', password='admin123', role='admin', status='ativo')
        cls.prof = User.objects.create_user(username='prof', email='prof@escola.pt', password='prof', role='professor', status='ativo')
        cls.guest = User.objects.create_user(username='guest', email='guest@escola.pt', password='guest', status='convidado')
        
        # Add users to groups
        cls.admin.groups.add(admin_group)
        cls.prof.groups.add(prof_group)
        
        cls.turma = Class.objects.create(name='7A', year=2025)
        cls.turma.teachers.add(cls.prof)

    def test_promote_guest_to_professor_by_admin(self):
        self.client.force_login(self.admin)
        self.guest.role = None
        self.guest.status = 'convidado'
        self.guest.save()
        self.guest.promote_to_role('professor')
        self.guest.save()
        self.guest.refresh_from_db()
        self.assertEqual(self.guest.role, 'professor')
        self.assertEqual(self.guest.status, 'ativo')

# === New Tests for Microsoft Authentication ===

class MicrosoftAuthCallbackTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Define the callback URL once
        self.callback_url = reverse('users:callback_microsoft')
        self.dummy_code = 'dummy_auth_code'

    @override_settings(ALLOWED_EMAIL_DOMAINS=['test.escola.pt'])
    @patch('msal.ConfidentialClientApplication')
    def test_microsoft_callback_allowed_domain(self, MockConfidentialClientApplication):
        """Test successful login and user creation with an allowed domain."""
        # --- Mock MSAL --- 
        mock_msal_instance = MagicMock()
        # Configure the return value for acquire_token_by_authorization_code
        mock_msal_instance.acquire_token_by_authorization_code.return_value = {
            'id_token_claims': {
                'preferred_username': 'aluno.teste@test.escola.pt',
                'name': 'Aluno Teste',
                'sub': 'unique_ms_id_123'
            },
            'access_token': 'dummy_access_token',
            # Add other token fields if your app uses them
        }
        # Configure the return value for get_authorization_request_url (not strictly needed for callback but good practice)
        mock_msal_instance.get_authorization_request_url.return_value = "http://dummy_auth_url"
        # Ensure the constructor returns our configured mock instance
        MockConfidentialClientApplication.return_value = mock_msal_instance
        # -----------------

        # Make the GET request to the callback view
        response = self.client.get(self.callback_url, {'code': self.dummy_code})

        # --- Assertions --- 
        # 1. Check MSAL was called correctly
        mock_msal_instance.acquire_token_by_authorization_code.assert_called_once_with(
            self.dummy_code,
            scopes=["User.Read"],
            redirect_uri=settings.AZURE_AD_REDIRECT_URI,
        )
        
        # 2. Check user creation/retrieval
        self.assertTrue(User.objects.filter(email='aluno.teste@test.escola.pt').exists())
        user = User.objects.get(email='aluno.teste@test.escola.pt')
        self.assertEqual(user.first_name, 'Aluno Teste')
        # Initially, the user should be created as 'convidado' by default if role assignment happens later
        # self.assertEqual(user.status, 'convidado') # Adjust if user creation logic changes

        # 3. Check user is logged in (session check)
        # Accessing session directly after client call
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        # 4. Check response is a redirect to home
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/') # Assumes redirect to root
        
        # 5. Check token stored in session (optional)
        self.assertIn('msal_token', self.client.session)
        self.assertEqual(self.client.session['msal_token']['id_token_claims']['preferred_username'], 'aluno.teste@test.escola.pt')

    @override_settings(ALLOWED_EMAIL_DOMAINS=['test.escola.pt']) # Only allow test.escola.pt
    @patch('msal.ConfidentialClientApplication')
    def test_microsoft_callback_disallowed_domain(self, MockConfidentialClientApplication):
        """Test that login is denied for a user with a disallowed email domain."""
        # --- Mock MSAL --- 
        mock_msal_instance = MagicMock()
        mock_msal_instance.acquire_token_by_authorization_code.return_value = {
            'id_token_claims': {
                'preferred_username': 'outsider@otherdomain.com', # Different domain
                'name': 'Out Sider',
                'sub': 'unique_ms_id_456'
            },
            'access_token': 'dummy_access_token_other',
        }
        MockConfidentialClientApplication.return_value = mock_msal_instance
        # -----------------

        # Make the GET request
        response = self.client.get(self.callback_url, {'code': self.dummy_code})

        # --- Assertions ---
        # 1. Check MSAL was called
        mock_msal_instance.acquire_token_by_authorization_code.assert_called_once()
        
        # 2. Check user was NOT created
        self.assertFalse(User.objects.filter(email='outsider@otherdomain.com').exists())

        # 3. Check user is NOT logged in
        self.assertNotIn('_auth_user_id', self.client.session)

        # 4. Check response is 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # 5. Check error message in response content
        self.assertContains(response, 'Acesso negado: O domínio "otherdomain.com" não é permitido.', status_code=403)
        
        # 6. Check token was NOT stored in session
        self.assertNotIn('msal_token', self.client.session)

    @override_settings(ALLOWED_EMAIL_DOMAINS=None) # Simulate setting not present
    @patch('msal.ConfidentialClientApplication')
    def test_microsoft_callback_no_allowed_domains_setting(self, MockConfidentialClientApplication):
        """Test that login proceeds if ALLOWED_EMAIL_DOMAINS is not set (current behavior)."""
        # --- Mock MSAL --- 
        mock_msal_instance = MagicMock()
        mock_msal_instance.acquire_token_by_authorization_code.return_value = {
            'id_token_claims': {
                'preferred_username': 'anyone@anydomain.com', # Any domain
                'name': 'Any One',
                'sub': 'unique_ms_id_789'
            },
            'access_token': 'dummy_access_token_any',
        }
        MockConfidentialClientApplication.return_value = mock_msal_instance
        # -----------------

        # Make the GET request
        response = self.client.get(self.callback_url, {'code': self.dummy_code})

        # --- Assertions --- 
        # 1. Check MSAL was called
        mock_msal_instance.acquire_token_by_authorization_code.assert_called_once()
        
        # 2. Check user WAS created
        self.assertTrue(User.objects.filter(email='anyone@anydomain.com').exists())
        user = User.objects.get(email='anyone@anydomain.com')

        # 3. Check user IS logged in
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        # 4. Check response is 302 Redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        
        # 5. Check token WAS stored in session
        self.assertIn('msal_token', self.client.session)

    def test_microsoft_callback_missing_code(self):
        """Test error response when the 'code' parameter is missing."""
        # Make the GET request without the 'code' parameter
        response = self.client.get(self.callback_url)

        # --- Assertions ---
        # 1. Check response is 400 Bad Request
        self.assertEqual(response.status_code, 400)
        
        # 2. Check error message in response content
        self.assertContains(response, 'Erro: código de autorização não recebido.', status_code=400)
        
        # 3. Check user is NOT logged in
        self.assertNotIn('_auth_user_id', self.client.session)
        
        # 4. Check token was NOT stored in session
        self.assertNotIn('msal_token', self.client.session)

    @patch('msal.ConfidentialClientApplication')
    def test_microsoft_callback_msal_error(self, MockConfidentialClientApplication):
        """Test error response when MSAL fails to return a valid token."""
        # --- Mock MSAL to return error --- 
        mock_msal_instance = MagicMock()
        # Simulate a result missing 'id_token_claims'
        mock_msal_instance.acquire_token_by_authorization_code.return_value = {
            'error': 'invalid_grant',
            'error_description': 'Invalid authorization code.'
            # Missing 'id_token_claims'
        }
        MockConfidentialClientApplication.return_value = mock_msal_instance
        # --------------------------------

        # Make the GET request
        response = self.client.get(self.callback_url, {'code': self.dummy_code})

        # --- Assertions ---
        # 1. Check MSAL was called
        mock_msal_instance.acquire_token_by_authorization_code.assert_called_once()

        # 2. Check response is 400 Bad Request
        self.assertEqual(response.status_code, 400)
        
        # 3. Check error message in response content
        self.assertContains(response, 'Erro ao obter token do Azure AD.', status_code=400)
        
        # 4. Check user is NOT logged in
        self.assertNotIn('_auth_user_id', self.client.session)
        
        # 5. Check token was NOT stored in session
        self.assertNotIn('msal_token', self.client.session)


class MicrosoftAuthAPITests(APITestCase):
    @override_settings(
        AZURE_AD_CLIENT_ID='client-id',
        AZURE_AD_CLIENT_SECRET='client-secret',
        AZURE_AD_TENANT_ID='tenant-id',
        AZURE_AD_REDIRECT_URI='https://example.com/callback',
    )
    def test_login_init_returns_authorization_url(self):
        response = self.client.get(reverse('auth-microsoft-login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('authorization_url', response.data)
        self.assertIn('state', response.data)

    @override_settings(
        AZURE_AD_CLIENT_ID='client-id',
        AZURE_AD_CLIENT_SECRET='client-secret',
        AZURE_AD_TENANT_ID='tenant-id',
        AZURE_AD_REDIRECT_URI='https://example.com/callback',
    )
    @patch('users.api.auth_views._build_msal_app')
    def test_callback_returns_jwt_tokens(self, mock_msal_app):
        mock_instance = MagicMock()
        mock_instance.acquire_token_by_authorization_code.return_value = {
            'id_token_claims': {
                'preferred_username': 'apiuser@test.com',
            },
            'access_token': 'token',
        }
        mock_msal_app.return_value = mock_instance

        session = self.client.session
        session['azure_oauth_state'] = 'abc'
        session.save()

        response = self.client.get(reverse('auth-microsoft-callback'), {'code': '123', 'state': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertTrue(User.objects.filter(email='apiuser@test.com').exists())

    @override_settings(
        AZURE_AD_CLIENT_ID='client-id',
        AZURE_AD_CLIENT_SECRET='client-secret',
        AZURE_AD_TENANT_ID='tenant-id',
        AZURE_AD_REDIRECT_URI='https://example.com/callback',
    )
    def test_refresh_without_cookie_returns_error(self):
        response = self.client.post(reverse('auth-token-refresh'))
        self.assertEqual(response.status_code, 401)
# Add more tests here: etc.


class DefaultAdminCreationTests(TestCase):
    def test_default_admin_user_exists(self):
        admin_user = User.objects.get(username='admin')
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.must_change_password)
        self.assertTrue(admin_user.check_password('admin'))


class ForcePasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='force_user',
            email='force@test.com',
            password='StartPass123!',
            role='admin',
            status='ativo',
            must_change_password=True,
        )

    def test_redirects_to_force_password_change(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('users:guardian_register'))
        self.assertRedirects(response, reverse('users:force_password_change'))

    def test_password_change_clears_flag(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('users:force_password_change'),
            {
                'old_password': 'StartPass123!',
                'new_password1': 'UpdatedPass456!',
                'new_password2': 'UpdatedPass456!',
            },
            follow=True,
        )
        self.assertEqual(response.redirect_chain[-1][0], '/')
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        self.assertTrue(self.user.check_password('UpdatedPass456!'))


class GuardianRegistrationTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name='encarregado')
        Group.objects.get_or_create(name='aluno')
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='StudentPass123!',
            role='aluno',
            status='ativo',
            student_number='A123',
        )

    def test_guardian_registration_creates_user_and_relation(self):
        payload = {
            'first_name': 'Maria',
            'last_name': 'Silva',
            'email': 'maria.guardian@test.com',
            'student_number': 'A123',
            'relationship': 'Mãe',
            'password1': 'GuardianPass123!',
            'password2': 'GuardianPass123!',
        }
        response = self.client.post(reverse('users:guardian_register'), payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        guardian = User.objects.get(email='maria.guardian@test.com')
        self.assertEqual(guardian.role, 'encarregado')
        self.assertTrue(guardian.check_password('GuardianPass123!'))
        self.assertFalse(guardian.must_change_password)
        self.assertTrue(
            GuardianRelation.objects.filter(aluno=self.student, encarregado=guardian).exists()
        )
        self.assertEqual(int(self.client.session['_auth_user_id']), guardian.id)


class LocalLoginAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='local_admin',
            email='local_admin@test.com',
            password='AdmPass123!',
            role='admin',
            status='ativo',
        )

    def test_successful_local_login(self):
        response = self.client.post(
            reverse('auth-login-local'),
            {'username': 'local_admin', 'password': 'AdmPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertFalse(response.data['must_change_password'])

    def test_must_change_password_flag(self):
        self.user.must_change_password = True
        self.user.save(update_fields=['must_change_password'])
        response = self.client.post(
            reverse('auth-login-local'),
            {'username': 'local_admin', 'password': 'AdmPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['must_change_password'])

    def test_invalid_credentials(self):
        response = self.client.post(
            reverse('auth-login-local'),
            {'username': 'local_admin', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)


class GuardianRegistrationAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Group.objects.get_or_create(name='encarregado')
        Group.objects.get_or_create(name='aluno')
        cls.student = User.objects.create_user(
            username='student_api',
            email='student_api@test.com',
            password='StudentPass123!',
            role='aluno',
            status='ativo',
            student_number='S321',
        )

    def test_guardian_registration_api(self):
        payload = {
            'first_name': 'João',
            'last_name': 'Silva',
            'email': 'joao.encarregado@test.com',
            'student_number': 'S321',
            'relationship': 'Pai',
            'password1': 'GuardianPass123!',
            'password2': 'GuardianPass123!',
        }
        response = self.client.post(reverse('auth-register-guardian'), payload, format='json')
        self.assertEqual(response.status_code, 200)
        guardian = User.objects.get(email='joao.encarregado@test.com')
        self.assertEqual(response.data['user']['email'], guardian.email)
        self.assertIn('access', response.data)
        self.assertTrue(
            GuardianRelation.objects.filter(aluno=self.student, encarregado=guardian).exists()
        )


class ForcePasswordChangeAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='force_api',
            email='force_api@test.com',
            password='InitialPass123!',
            role='admin',
            status='ativo',
            must_change_password=True,
        )
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        # Simulate refresh cookie for rotation
        self.client.cookies[settings.JWT_AUTH_REFRESH_COOKIE] = str(refresh)

    def test_force_password_change_success(self):
        response = self.client.post(
            reverse('auth-password-change'),
            {
                'old_password': 'InitialPass123!',
                'new_password1': 'BrandNewPass456!',
                'new_password2': 'BrandNewPass456!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        self.assertTrue(self.user.check_password('BrandNewPass456!'))
