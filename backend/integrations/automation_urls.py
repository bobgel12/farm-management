from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .automation_views import AutomationWorkflowViewSet
from .webhook_views import n8n_webhook_dispatcher

router = DefaultRouter()
router.register(r'automations', AutomationWorkflowViewSet, basename='automation')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/n8n/', n8n_webhook_dispatcher, name='n8n_webhook_dispatcher'),
]
