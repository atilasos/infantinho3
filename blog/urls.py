# blog/urls.py
from django.urls import path
from . import views

# Define an app_name for namespacing
app_name = 'blog'

urlpatterns = [
    # Public list (now acts as main blog index)
    path('', views.post_list_public, name='post_list_public'),
    
    # --- New Global Post Creation URL --- 
    path('criar/', views.post_create_global, name='post_create_global'),
    # -----------------------------------
    
    # --- TinyMCE Image Upload URL --- 
    path('tinymce/upload_image/', views.tinymce_image_upload, name='tinymce_image_upload'),
    # --------------------------------
    
    # Post specific actions (global, identified by post_id)
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/editar/', views.post_edit, name='post_edit'),
    path('post/<int:post_id>/remover/', views.post_remove, name='post_remove'),
    path('post/<int:post_id>/restaurar/', views.post_restore, name='post_restore'),
    path('post/<int:post_id>/comentar/', views.post_comment, name='post_comment'),
    # Comment remove URL only needs comment_id as view gets post from comment
    path('comment/<int:comment_id>/remover/', views.comment_remove, name='comment_remove'),
    
    # --- New Approval Workflow URLs --- 
    path('post/<int:post_id>/aprovar/', views.post_approve, name='post_approve'),
    path('pendentes/', views.post_pending_list, name='post_pending_list'),
    # ----------------------------------

    # TODO: Revisit these class-specific URLs. Do we still need them?
    # If post_create requires class context, how do we provide it without class_id in URL?
    # Maybe move post_create to be under /turmas/<id>/blog/criar ?
    # path('post/novo/', views.post_create, name='post_create'), # REMOVED
    # path('posts/', views.post_list, name='post_list'), # Keep for now?
    # path('ajuda/', views.blog_help, name='blog_help'), # REMOVED
    # path('moderacao/', views.moderation_logs, name='moderation_logs'), # REMOVED
] 
