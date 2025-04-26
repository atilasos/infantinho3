from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
import msal
from django.contrib.auth import login, get_user_model, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth import authenticate
from django.shortcuts import redirect

# Create your views here.

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
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form, 'local_login': True})

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
