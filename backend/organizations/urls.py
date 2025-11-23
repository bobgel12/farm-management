from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet, basename='organization')
router.register(r'organization-users', views.OrganizationUserViewSet, basename='organization-user')

urlpatterns = [
    path('', include(router.urls)),
]

