from django.urls import path

from ai import views

app_name = "ai"

urlpatterns = [
    path("assistant/", views.ai_assistant_view, name="assistant"),
    path("feedback/", views.ai_feedback_view, name="feedback"),
    path("session/<uuid:session_id>/", views.session_detail_view, name="session-detail"),
]
