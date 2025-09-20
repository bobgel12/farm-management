"""
URL configuration for chicken_management project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView

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
]

# React app routes
urlpatterns += [
    # Serve React app for all non-API routes
    path('', TemplateView.as_view(template_name='index.html')),
    # Catch-all for React Router (must be last)
    path('<path:path>', TemplateView.as_view(template_name='index.html')),
]
