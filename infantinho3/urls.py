"""
URL configuration for infantinho3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from users import views as user_views # Not directly used here
from classes.views import landing_page # Used for root path
from classes import views as class_views
from django.conf import settings
from django.conf.urls.static import static
from checklists.views import HelpView # Used for /ajuda/
from blog.views import post_list_public # Import the new public view

urlpatterns = [
    # Expor nomes globais exigidos pelos testes para classes
    path('gerir-turmas/', class_views.manage_classes, name='manage_classes'),
    path('turmas/<int:class_id>/adicionar-aluno/', class_views.add_student, name='add_student'),
    path('turmas/', class_views.class_list, name='class_list'),
    path('turmas/<int:class_id>/', class_views.class_detail, name='class_detail'),

    # Admin site
    path('admin/', admin.site.urls),
    
    # Authentication URLs (login, logout, password reset, etc.)
    path('auth/', include('users.urls')),
    
    # --- Impersonate URLs ---
    path('impersonate/', include('impersonate.urls')),
    # ------------------------
    
    # --- Nested Diary URLs under Classes --- 
    path('turmas/<int:class_id>/diario/', include('diary.urls', namespace='diary')), 
    # ---------------------------------------
    
    # Class-related URLs (including landing page at root)
    path('', include('classes.urls')), # global names
    path('', include(('classes.urls', 'classes'), namespace='classes')), # namespaced for templates
    # Blog por turma (aninhado sob /turmas/<id>/blog/) com namespace distinto
    path('turmas/<int:class_id>/blog/', include('blog.class_urls', namespace='class_blog')), 
    
    # --- Root path now points to the public blog list --- 
    path('', post_list_public, name='landing_page'), # Use the same name for simplicity for now
    
    # --- Blog URLs are now global under /blog/ --- 
    path('blog/', include('blog.urls', namespace='blog')), 
    
    # Checklists URLs
    path('checklists/', include('checklists.urls', namespace='checklists')),
    # PIT URLs
    path('pit/', include('pit.urls', namespace='pit')),
    # Projects URLs
    path('', include('projects.urls', namespace='projects')),
    # Council URLs
    path('', include('council.urls', namespace='council')),
    
    # CKEditor URLs (Only needed if using django-ckeditor-uploader)
    # path('ckeditor/', include('ckeditor_uploader.urls')), # Commented out as uploader is not used
    
    # --- TinyMCE URLs --- ADDED
    path('tinymce/', include('tinymce.urls')),
    # ---------------------
    
    # General Help View
    path('ajuda/', HelpView.as_view(), name='ajuda'),

    # Infantinho Feedback URLs
    path('feedback/', include('infantinho_feedback.urls', namespace='infantinho_feedback')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
