"""
URL configuration for academico URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Import core views for error handling (imports are used by Django's URL configuration)
# These are referenced by name in Django's URL configuration
from core.views import handler403 as core_handler403  # noqa: F401
from core.views import handler404 as core_handler404  # noqa: F401
from core.views import handler500 as core_handler500  # noqa: F401

# Configure Django to use our custom error handlers
handler403 = 'core.views.handler403'
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Core app
    path('', include('core.urls')),
    
    # Authentication (using Django's built-in views)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Redirect admin to /admin/
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),
    
    # Redirect root to home
    path('', RedirectView.as_view(url='/', permanent=True)),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Enable debug toolbar if installed
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
