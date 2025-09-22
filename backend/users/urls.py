# users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views # Import Django auth views
from . import views

# Define app_name for namespacing if not already done elsewhere
app_name = 'users' 

urlpatterns = [
    path('login-choice/', views.login_choice, name='login_choice'),
    path('login/', views.login_local, name='login_local'), # Assuming this is the main login view
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password/change/', views.force_password_change, name='force_password_change'),
    path('register/guardian/', views.guardian_register, name='guardian_register'),
    
    # Microsoft SSO URLs
    path('login/microsoft/', views.login_microsoft, name='login_microsoft'),
    path('callback/microsoft/', views.callback_microsoft, name='callback_microsoft'),
    # Logout should ideally handle both local and Microsoft sessions if possible
    # path('logout/microsoft/', views.logout_microsoft, name='logout_microsoft'), 
    
    # Add Django's built-in LogoutView
    path('logout/', auth_views.LogoutView.as_view(), name='logout'), 
    # Note: LogoutView redirects to settings.LOGOUT_REDIRECT_URL by default
    # You might need to define LOGOUT_REDIRECT_URL in settings.py (e.g., '/' or 'login_choice')
]
