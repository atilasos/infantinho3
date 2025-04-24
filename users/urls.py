from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_choice, name='login_choice'),
    path('login/local/', views.login_local, name='login_local'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('login/microsoft/', views.login_microsoft, name='login_microsoft'),
    path('callback/microsoft/', views.callback_microsoft, name='callback_microsoft'),
    path('logout/microsoft/', views.logout_microsoft, name='logout_microsoft'),
] 