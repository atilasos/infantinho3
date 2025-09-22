"""Authentication endpoints for Microsoft SSO and JWT issuance."""
from __future__ import annotations

import secrets
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
import msal

from users.api.serializers import UserSerializer, GuardianRegistrationSerializer

User = get_user_model()

MS_SCOPES = ["openid", "profile", "email", "offline_access"]


def _state_session_key() -> str:
    return 'azure_oauth_state'


def _build_authorization_url(state: str) -> str:
    params = {
        'client_id': settings.AZURE_AD_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.AZURE_AD_REDIRECT_URI,
        'response_mode': 'query',
        'scope': ' '.join(MS_SCOPES),
        'state': state,
        'prompt': 'select_account',
    }
    authority = settings.AZURE_AD_AUTHORITY or f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}"
    return f"{authority}/oauth2/v2.0/authorize?{urlencode(params)}"


def _build_msal_app() -> msal.ConfidentialClientApplication:
    authority = settings.AZURE_AD_AUTHORITY or f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}"
    return msal.ConfidentialClientApplication(
        client_id=settings.AZURE_AD_CLIENT_ID,
        client_credential=settings.AZURE_AD_CLIENT_SECRET,
        authority=authority,
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
    response.set_cookie(
        key=settings.JWT_AUTH_REFRESH_COOKIE,
        value=refresh_token,
        max_age=max_age,
        secure=settings.JWT_AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.JWT_AUTH_REFRESH_COOKIE,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
    )


class MicrosoftLoginInitAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        if not settings.AZURE_AD_CLIENT_ID or not settings.AZURE_AD_CLIENT_SECRET:
            return Response({'error': 'Azure AD não configurado.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        state = secrets.token_urlsafe(32)
        request.session[_state_session_key()] = state
        authorization_url = _build_authorization_url(state)
        return Response({'authorization_url': authorization_url, 'state': state})


class MicrosoftCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        stored_state = request.session.get(_state_session_key())
        incoming_state = request.query_params.get('state')
        if not stored_state or stored_state != incoming_state:
            return Response({'error': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Código não fornecido.'}, status=status.HTTP_400_BAD_REQUEST)

        app = _build_msal_app()
        token_result = app.acquire_token_by_authorization_code(
            code,
            scopes=MS_SCOPES,
            redirect_uri=settings.AZURE_AD_REDIRECT_URI,
        )
        if 'error' in token_result:
            return Response({'error': token_result.get('error_description', 'Falha ao obter token.')}, status=status.HTTP_400_BAD_REQUEST)

        claims = token_result.get('id_token_claims', {})
        email = claims.get('preferred_username') or claims.get('email')
        if not email:
            return Response({'error': 'Email não fornecido pelo Azure AD.'}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(email=email, defaults={'username': email, 'status': 'convidado'})
        if created:
            user.set_unusable_password()
        if not user.username:
            user.username = email
        if getattr(user, 'status', None) is None:
            user.status = 'convidado'
        user.last_login = timezone.now()
        user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        serializer = UserSerializer(user, context={'request': request})
        response = Response({'access': access_token, 'user': serializer.data})
        _set_refresh_cookie(response, refresh_token)
        request.session.pop(_state_session_key(), None)
        return response


class TokenRefreshCookieAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE) or request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token em falta.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({'error': 'Refresh token inválido.'}, status=status.HTTP_401_UNAUTHORIZED)

        data = serializer.validated_data
        response = Response({'access': data['access']})
        if 'refresh' in data:
            _set_refresh_cookie(response, data['refresh'])
        return response


class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:  # pragma: no cover
                pass
        response = Response({'ok': True})
        _clear_refresh_cookie(response)
        return response


class LocalLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = (request.data.get('username') or request.data.get('email') or '').strip()
        password = request.data.get('password') or ''
        if not username or not password:
            return Response({'error': 'Credenciais inválidas.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'error': 'Email ou password inválidos.'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({'error': 'Conta inativa. Contacte o administrador.'}, status=status.HTTP_403_FORBIDDEN)

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        serializer = UserSerializer(user, context={'request': request})
        response = Response({
            'access': access_token,
            'user': serializer.data,
            'must_change_password': user.must_change_password,
        })
        _set_refresh_cookie(response, str(refresh))
        return response


class GuardianRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = GuardianRegistrationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        guardian = serializer.save()

        refresh = RefreshToken.for_user(guardian)
        access_token = str(refresh.access_token)
        user_data = UserSerializer(guardian, context={'request': request}).data

        response = Response({
            'access': access_token,
            'user': user_data,
            'must_change_password': guardian.must_change_password,
        })
        _set_refresh_cookie(response, str(refresh))
        return response


class ForcePasswordChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        form = PasswordChangeForm(request.user, data=request.data)
        if not form.is_valid():
            return Response({'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        user = form.save()
        user.must_change_password = False
        user.save(update_fields=['must_change_password'])
        update_session_auth_hash(request, user)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        data = UserSerializer(user, context={'request': request}).data

        response = Response({'access': access_token, 'user': data})
        _set_refresh_cookie(response, str(refresh))
        return response
