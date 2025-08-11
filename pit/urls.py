from django.urls import path
from . import views

app_name = 'pit'

urlpatterns = [
    # Aluno
    path('meu-atual/', views.my_current_plan_redirect, name='my_current_plan'),
    path('turmas/<int:class_id>/novo/', views.plan_create, name='plan_create'),
    path('turmas/<int:class_id>/planos/<int:plan_id>/editar/', views.plan_edit, name='plan_edit'),

    # Professor
    path('turmas/<int:class_id>/planos/', views.TeacherPlanListView.as_view(), name='teacher_plan_list'),
    path('turmas/<int:class_id>/planos/<int:plan_id>/aprovar/', views.TeacherPlanApproveView.as_view(), name='teacher_plan_approve'),
]


