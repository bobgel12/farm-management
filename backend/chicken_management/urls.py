"""
URL configuration for chicken_management project.
"""
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
]

# Custom static file serving - MUST be before catch-all routes
urlpatterns += [
    # Serve static files with specific patterns
    path('static/js/<path:path>', static_views.serve_static_file),
    path('static/css/<path:path>', static_views.serve_static_file),
    path('static/media/<path:path>', static_views.serve_static_file),
    path('static/<path:path>', static_views.serve_static_file),
]

# React app routes - MUST be after static files
urlpatterns += [
    # Serve React app for all non-API routes
    path('', TemplateView.as_view(template_name='index.html')),
    # Catch-all for React Router (must be last)
    path('<path:path>', TemplateView.as_view(template_name='index.html')),
]
