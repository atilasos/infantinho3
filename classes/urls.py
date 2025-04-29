from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('turmas/', views.class_list, name='class_list'),
    path('turmas/<int:class_id>/', views.class_detail, name='class_detail'),
    path('turmas/<int:class_id>/adicionar-aluno/', views.add_student, name='add_student'),
    path('gerir-turmas/', views.manage_classes, name='manage_classes'),
    path('turmas/<int:class_id>/aluno/<int:student_id>/', views.student_detail, name='student_detail'),
] 