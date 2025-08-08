from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('turmas/<int:class_id>/projetos/', views.project_list, name='project_list'),
    path('turmas/<int:class_id>/projetos/novo/', views.project_create, name='project_create'),
    path('turmas/<int:class_id>/projetos/<int:project_id>/', views.project_detail, name='project_detail'),
]


