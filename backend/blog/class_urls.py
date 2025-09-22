from django.urls import path
from . import views

# Reutiliza o mesmo app_name interno para compatibilidade com reverse
app_name = 'blog'

urlpatterns = [
    # Listagem do blog/diário por turma
    path('', views.post_list, name='post_list'),

    # Criar novo post dentro da turma
    path('novo/', views.post_create, name='post_create'),

    # Páginas auxiliares/moderação no contexto da turma
    path('moderacao/', views.moderation_logs, name='moderation_logs'),
    path('ajuda/', views.blog_help, name='blog_help'),
]


