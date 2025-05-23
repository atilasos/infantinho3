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
from django.conf import settings
from django.conf.urls.static import static
from checklists.views import HelpView # Used for /ajuda/
from blog.views import post_list_public # Import the new public view

urlpatterns = [
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
    path('turmas/', include('classes.urls')), # Keep other class URLs under /turmas/
    
    # --- Root path now points to the public blog list --- 
    path('', post_list_public, name='landing_page'), # Use the same name for simplicity for now
    
    # --- Blog URLs are now global under /blog/ --- 
    path('blog/', include('blog.urls', namespace='blog')), 
    
    # Checklists URLs
    path('checklists/', include('checklists.urls', namespace='checklists')),
    
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
