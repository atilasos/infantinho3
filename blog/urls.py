# blog/urls.py
from django.urls import path
from . import views

# Define an app_name for namespacing
app_name = 'blog'

urlpatterns = [
    # URLs relative to /turmas/<int:class_id>/blog/
    path('', views.post_list, name='post_list'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('novo/', views.post_create, name='post_create'),
    path('post/<int:post_id>/editar/', views.post_edit, name='post_edit'),
    path('post/<int:post_id>/remover/', views.post_remove, name='post_remove'),
    path('post/<int:post_id>/restaurar/', views.post_restore, name='post_restore'),
    path('post/<int:post_id>/comentar/', views.post_comment, name='post_comment'),
    path('post/<int:post_id>/comentario/<int:comment_id>/remover/', views.comment_remove, name='comment_remove'),
    path('moderacao/', views.moderation_logs, name='moderation_logs'),
    path('ajuda/', views.blog_help, name='blog_help'),
] 
