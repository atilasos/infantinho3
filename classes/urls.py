from django.urls import path
from . import views

urlpatterns = [
    path('turmas/', views.class_list, name='class_list'),
    path('turmas/<int:class_id>/', views.class_detail, name='class_detail'),
    path('turmas/<int:class_id>/adicionar-aluno/', views.add_student, name='add_student'),
    path('admin/turmas/', views.manage_classes, name='manage_classes'),
] 