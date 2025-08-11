from django.urls import path
from . import views

app_name = 'council'

urlpatterns = [
    path('turmas/<int:class_id>/conselho/', views.decision_list, name='decision_list'),
    path('turmas/<int:class_id>/conselho/decisao/nova/', views.decision_create, name='decision_create'),
    path('turmas/<int:class_id>/conselho/proposta/nova/', views.proposal_create, name='proposal_create'),
]


