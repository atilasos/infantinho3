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

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Authentication URLs (login, logout, password reset, etc.)
    path('auth/', include('users.urls')),
    
    # Class-related URLs (listing classes, class detail)
    # Assuming classes.urls contains paths like 'turmas/', 'turmas/<int:class_id>/'
    path('', include('classes.urls')),
    
    # Landing page (consider moving this into classes.urls if it's the root)
    path('', landing_page, name='landing_page'), 
    
    # Blog URLs - Nested under a specific class ID
    # This will make blog URLs like /turmas/123/blog/ and /turmas/123/blog/post/456/
    path('turmas/<int:class_id>/blog/', include('blog.urls', namespace='blog')), 
    
    # Checklists URLs
    path('checklists/', include('checklists.urls', namespace='checklists')),
    
    # CKEditor URLs (Only needed if using django-ckeditor-uploader)
    # path('ckeditor/', include('ckeditor_uploader.urls')), # Commented out as uploader is not used
    
    # General Help View
    path('ajuda/', HelpView.as_view(), name='ajuda'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
