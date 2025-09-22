"""Root API router for Infantinho headless backend."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.api.views import UserViewSet, CurrentUserViewSet
from classes.api.views import ClassViewSet
from blog.api.views import PostViewSet, PublicPostListAPIView
from checklists.api.views import ChecklistTemplateViewSet, ChecklistStatusViewSet, ChecklistMarkViewSet
from pit.api.views import IndividualPlanViewSet, PlanTaskViewSet
from projects.api.views import ProjectViewSet, ProjectTaskViewSet
from council.api.views import CouncilDecisionViewSet, StudentProposalViewSet
from ai.api.views import AssistantAPIView, SessionDetailAPIView, AssistantFeedbackAPIView
from users.api.auth_views import (
    MicrosoftLoginInitAPIView,
    MicrosoftCallbackAPIView,
    TokenRefreshCookieAPIView,
    LogoutAPIView,
    LocalLoginAPIView,
    GuardianRegisterAPIView,
    ForcePasswordChangeAPIView,
)
from diary.api.views import (
    ClassDiaryActiveAPIView,
    ClassDiaryEntryAPIView,
    ClassDiarySessionDetailAPIView,
    ClassDiarySessionsListAPIView,
    ClassDiaryStartAPIView,
)

router = DefaultRouter(trailing_slash=False)
router.register('users', UserViewSet, basename='user')
router.register('classes', ClassViewSet, basename='class')
router.register('blog/posts', PostViewSet, basename='blog-post')
router.register('checklists/templates', ChecklistTemplateViewSet, basename='checklist-template')
router.register('checklists/statuses', ChecklistStatusViewSet, basename='checklist-status')
router.register('checklists/marks', ChecklistMarkViewSet, basename='checklist-mark')
router.register('pit/plans', IndividualPlanViewSet, basename='pit-plan')
router.register('pit/tasks', PlanTaskViewSet, basename='pit-task')
router.register('projects', ProjectViewSet, basename='project')
router.register('project-tasks', ProjectTaskViewSet, basename='project-task')
router.register('council/decisions', CouncilDecisionViewSet, basename='council-decision')
router.register('council/proposals', StudentProposalViewSet, basename='council-proposal')

current_user_view = CurrentUserViewSet.as_view({'get': 'list'})

urlpatterns = [
    path('', include(router.urls)),
    path('me', current_user_view, name='api-current-user'),
    path('blog/public', PublicPostListAPIView.as_view(), name='blog-public-list'),
    path('ai/assistant', AssistantAPIView.as_view(), name='ai-assistant'),
    path('ai/sessions/<uuid:session_id>', SessionDetailAPIView.as_view(), name='ai-session-detail'),
    path('ai/feedback', AssistantFeedbackAPIView.as_view(), name='ai-feedback'),
    path('auth/microsoft/login', MicrosoftLoginInitAPIView.as_view(), name='auth-microsoft-login'),
    path('auth/microsoft/callback', MicrosoftCallbackAPIView.as_view(), name='auth-microsoft-callback'),
    path('auth/login/local', LocalLoginAPIView.as_view(), name='auth-login-local'),
    path('auth/register/guardian', GuardianRegisterAPIView.as_view(), name='auth-register-guardian'),
    path('auth/password/change', ForcePasswordChangeAPIView.as_view(), name='auth-password-change'),
    path('auth/token/refresh', TokenRefreshCookieAPIView.as_view(), name='auth-token-refresh'),
    path('auth/logout', LogoutAPIView.as_view(), name='auth-logout'),
    path('classes/<int:class_id>/diary/active', ClassDiaryActiveAPIView.as_view(), name='class-diary-active'),
    path('classes/<int:class_id>/diary/sessions', ClassDiarySessionsListAPIView.as_view(), name='class-diary-sessions'),
    path('classes/<int:class_id>/diary/sessions/<int:session_id>', ClassDiarySessionDetailAPIView.as_view(), name='class-diary-session-detail'),
    path('classes/<int:class_id>/diary/entries', ClassDiaryEntryAPIView.as_view(), name='class-diary-entry'),
    path('classes/<int:class_id>/diary/start', ClassDiaryStartAPIView.as_view(), name='class-diary-start'),
]
