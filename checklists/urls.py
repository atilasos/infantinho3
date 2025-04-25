from django.urls import path
from .views import MyChecklistsView, ChecklistDetailView, ChecklistTurmaView

app_name = 'checklists'

urlpatterns = [
    path('minhas/', MyChecklistsView.as_view(), name='my_checklists'),
    path('<int:template_id>/', ChecklistDetailView.as_view(), name='checklist_detail'),
    path('turma/<int:class_id>/<int:template_id>/', ChecklistTurmaView.as_view(), name='checklist_turma'),
] 