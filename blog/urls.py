from django.urls import path
from . import views

urlpatterns = [
    path('turmas/<int:class_id>/blog/', views.post_list, name='blog_post_list'),
    path('turmas/<int:class_id>/blog/post/<int:post_id>/', views.post_detail, name='blog_post_detail'),
    path('turmas/<int:class_id>/blog/novo/', views.post_create, name='blog_post_create'),
    path('turmas/<int:class_id>/blog/post/<int:post_id>/editar/', views.post_edit, name='blog_post_edit'),
    path('turmas/<int:class_id>/blog/post/<int:post_id>/remover/', views.post_remove, name='blog_post_remove'),
    path('turmas/<int:class_id>/blog/post/<int:post_id>/comentar/', views.post_comment, name='blog_post_comment'),
    path('turmas/<int:class_id>/blog/post/<int:post_id>/comentario/<int:comment_id>/remover/', views.comment_remove, name='blog_comment_remove'),
    path('turmas/<int:class_id>/blog/moderacao/', views.moderation_logs, name='blog_moderation_logs'),
    path('turmas/<int:class_id>/blog/post/<int:post_id>/restaurar/', views.post_restore, name='blog_post_restore'),
    path('turmas/<int:class_id>/blog/ajuda/', views.blog_help, name='blog_help'),
] 