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
    # Add a simple root endpoint for debugging
    path('', lambda request: JsonResponse({'status': 'ok', 'message': 'Chicken House Management API'})),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
