from django.urls import path
from . import views

app_name = 'infantinho_feedback'

urlpatterns = [
    path('submeter/', views.feedback_submit_view, name='feedback_submit'),
    path('obrigado/', views.feedback_thank_you_view, name='feedback_thank_you'),
    
    # URLs para ações de administrador
    path('item/<int:pk>/atualizar-status/', views.feedback_update_status_view, name='update_status'),
    path('item/<int:pk>/apagar/', views.feedback_delete_view, name='delete_feedback'),

    # Se implementar a vista de lista de feedback do utilizador:
    # path('meu-feedback/', views.my_feedback_list_view, name='my_feedback_list'),
] 