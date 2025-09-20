"""
URL configuration for chicken_management project.
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView
from . import static_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('farms.urls')),
    path('api/', include('houses.urls')),
    path('api/', include('tasks.urls')),
    path('api/', include('authentication.urls')),
    path('api/', include('health.urls')),
    # Debug endpoint
    path('debug/static/', lambda request: JsonResponse({
        'static_url': settings.STATIC_URL,
        'static_root': str(settings.STATIC_ROOT),
        'staticfiles_dirs': [str(d) for d in settings.STATICFILES_DIRS],
    })),
    # Test static file serving
    path('test-static/', lambda request: JsonResponse({
        'message': 'Static file serving test',
        'test_url': '/static/js/main.52f69ca9.js'
    })),
    # Test if static file exists
    path('test-static-file/', lambda request: JsonResponse({
        'message': 'Testing static file existence',
        'js_file': '/static/js/main.52f69ca9.js',
        'css_file': '/static/css/main.233b3b67.css'
    })),
    # Debug file existence
    path('debug-files/', lambda request: JsonResponse({
        'message': 'Checking if static files exist',
        'static_root': str(settings.STATIC_ROOT),
        'static_dirs': [str(d) for d in settings.STATICFILES_DIRS],
        'files_exist': {
            'js_file': str(os.path.exists(os.path.join(settings.STATIC_ROOT, 'js', 'main.52f69ca9.js'))),
            'css_file': str(os.path.exists(os.path.join(settings.STATIC_ROOT, 'css', 'main.233b3b67.css'))),
        }
    })),
    # Static file serving - MUST be before catch-all routes
    path('static/js/<path:path>', static_views.serve_static_file),
    path('static/css/<path:path>', static_views.serve_static_file),
    path('static/media/<path:path>', static_views.serve_static_file),
    path('static/<path:path>', static_views.serve_static_file),
    # Serve React app for all non-API routes
    path('', TemplateView.as_view(template_name='index.html')),
    # Catch-all for React Router (must be last)
    path('<path:path>', TemplateView.as_view(template_name='index.html')),
]
