"""
URL configuration for chicken_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('farms.urls')),
    path('api/', include('houses.urls')),
    path('api/', include('tasks.urls')),
    path('api/', include('authentication.urls')),
    path('api/', include('health.urls')),
    path('api/', include('integrations.urls')),
    path('api/rotem/', include('rotem_scraper.urls')),
    path('api/', include('organizations.urls')),
    path('api/', include('reporting.urls')),
    path('api/', include('analytics.urls')),
    # API root endpoint
    path('', lambda request: JsonResponse({
        'status': 'ok', 
        'message': 'Chicken House Management API',
        'version': '1.0.0',
        'endpoints': {
            'farms': '/api/farms/',
            'houses': '/api/houses/',
            'tasks': '/api/tasks/',
            'auth': '/api/auth/',
            'health': '/api/health/',
            'integrations': '/api/ml/',
            'rotem': '/api/rotem/',
            'admin': '/admin/'
        }
    })),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
