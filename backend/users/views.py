from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, PasswordChangeForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

import msal

from .forms import GuardianRegistrationForm
from .models import GuardianRelation

# Create your views here.


def _style_form_fields(form):
    for field in form.fields.values():
        css = field.widget.attrs.get('class', '')
        classes = set(css.split()) if css else set()
        classes.add('form-control')
        field.widget.attrs['class'] = ' '.join(sorted(classes))

# View para iniciar o login via Azure AD

def login_microsoft(request):
    # Redireciona o utilizador para o login do Azure AD
    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.AZURE_AD_CLIENT_ID,
        client_credential=settings.AZURE_AD_CLIENT_SECRET,
        authority=settings.AZURE_AD_AUTHORITY,
    )
    # Scopes básicos para autenticação
    scopes = ["User.Read"]
    # Construir URL de autorização
    auth_url = msal_app.get_authorization_request_url(
        scopes,
        redirect_uri=settings.AZURE_AD_REDIRECT_URI,
        state=None  # Opcional: adicionar CSRF state
    )
    return HttpResponseRedirect(auth_url)

# View de callback após autenticação no Azure AD

def callback_microsoft(request):
    print('DEBUG callback_microsoft request.GET:', request.GET)
    # 1. Obter o código de autorização do request
    code = request.GET.get('code')
    if not code:
        return HttpResponse('Erro: código de autorização não recebido.', status=400)

    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.AZURE_AD_CLIENT_ID,
        client_credential=settings.AZURE_AD_CLIENT_SECRET,
        authority=settings.AZURE_AD_AUTHORITY,
    )
    scopes = ["User.Read"]

    # 2. Trocar o código por token
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=scopes,
        redirect_uri=settings.AZURE_AD_REDIRECT_URI,
    )
    print("MSAL result:", result)
    if "id_token_claims" not in result:
        return HttpResponse('Erro ao obter token do Azure AD.', status=400)

    claims = result["id_token_claims"]
    email = claims.get("preferred_username") or claims.get("email")
    name = claims.get("name")
    sub = claims.get("sub")

    if not email:
        return HttpResponse('Erro: email não encontrado no perfil do utilizador.', status=400)

    # === Domain Validation ===
    user_domain = email.split('@')[-1]
    allowed_domains = getattr(settings, 'ALLOWED_EMAIL_DOMAINS', [])
    if not allowed_domains:
        print("WARNING: ALLOWED_EMAIL_DOMAINS not set in settings. Allowing all domains.")
    elif user_domain.lower() not in [domain.lower() for domain in allowed_domains]:
        # Option 1: Deny login entirely
        return HttpResponse(f'Acesso negado: O domínio "{user_domain}" não é permitido.', status=403)
        # Option 2: Keep as guest (requires more logic later for role assignment)
        # print(f"INFO: User from non-allowed domain {user_domain} logging in as guest.")
        # is_guest = True # Flag to potentially skip role assignment later
    # === End Domain Validation ===

    # 3. Autenticar ou criar utilizador Django
    User = get_user_model()
    user, created = User.objects.get_or_create(email=email, defaults={
        'username': email,
        'first_name': name or '',
        # Adicionar outros campos se necessário
    })
    # Opcional: atualizar nome se mudou
    if not created and name and user.first_name != name:
        user.first_name = name
        user.save()

    # 4. Iniciar sessão Django
    # Explicitly specify the backend to avoid ValueError with multiple backends
    backend_path = 'django.contrib.auth.backends.ModelBackend'
    # You might need to ensure the user object has a 'backend' attribute set, 
    # or pass the backend path directly to login.
    # Setting the attribute is often preferred if the user object persists.
    user.backend = backend_path 
    login(request, user)

    # 5. Guardar tokens na sessão para futuras integrações (Teams, Graph, etc.)
    request.session['msal_token'] = result

    # 6. Redirecionar para página inicial ou dashboard
    return HttpResponseRedirect('/')

# View para logout

def logout_microsoft(request):
    # Termina a sessão local
    logout(request)
    # Opcional: terminar sessão no Azure AD também
    azure_logout_url = None
    if settings.AZURE_AD_AUTHORITY:
        azure_logout_url = f"{settings.AZURE_AD_AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={settings.AZURE_AD_REDIRECT_URI}"
    # Redirecionar para o logout do Azure AD ou para a página inicial
    return HttpResponseRedirect(azure_logout_url or '/')

def login_local(request):
    next_url = request.GET.get('next') or request.POST.get('next')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, _('Autenticação realizada com sucesso.'))
            if getattr(request.user, 'must_change_password', False):
                return redirect('users:force_password_change')
            return redirect(next_url or '/')
    else:
        form = AuthenticationForm()
    return render(
        request,
        'users/login.html',
        {
            'form': form,
            'local_login': True,
            'next': next_url,
        },
    )

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request, use_https=request.is_secure())
            return render(request, 'users/password_reset_done.html')
    else:
        form = PasswordResetForm()
    return render(request, 'users/password_reset.html', {'form': form})

def login_choice(request):
    """
    View para o utilizador escolher entre login local e Microsoft.
    Apenas mostra links/botões para as rotas já existentes.
    """
    return render(request, 'users/login_choice.html')


@login_required
def force_password_change(request):
    """Força utilizadores marcados a alterar a password antes de prosseguir."""
    if not getattr(request.user, 'must_change_password', False):
        return redirect('/')

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, data=request.POST)
        _style_form_fields(form)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])
            messages.success(request, _('Password atualizada com sucesso.'))
            return redirect('/')
    else:
        form = PasswordChangeForm(request.user)
        _style_form_fields(form)

    return render(request, 'users/force_password_change.html', {'form': form})


def guardian_register(request):
    """Permite o registo de encarregados através do número do aluno."""
    if request.user.is_authenticated:
        messages.info(request, _('Já tem sessão iniciada.'))
        return redirect('/')

    if request.method == 'POST':
        form = GuardianRegistrationForm(request.POST)
        _style_form_fields(form)
        if form.is_valid():
            guardian = form.save()
            GuardianRelation.objects.get_or_create(
                aluno=form.student,
                encarregado=guardian,
                defaults={'parentesco': form.cleaned_data.get('relationship')},
            )
            login(request, guardian, backend='users.backends.EmailOrUsernameBackend')
            messages.success(request, _('Conta de encarregado criada com sucesso.'))
            return redirect('/')
    else:
        form = GuardianRegistrationForm()
        _style_form_fields(form)

    return render(request, 'users/guardian_register.html', {'form': form})
