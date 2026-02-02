from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    # Main chat interface
    path('chat/', views.chat_view, name='chat'),
    path('turmas/<int:class_id>/chat/', views.chat_view, name='chat_with_class'),
    
    # API endpoints
    path('api/send/', views.send_message, name='send_message'),
    path('api/new/', views.new_conversation, name='new_conversation'),
    path('turmas/<int:class_id>/api/new/', views.new_conversation, name='new_conversation_with_class'),
]
