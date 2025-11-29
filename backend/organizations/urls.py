from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet, basename='organization')
router.register(r'organization-users', views.OrganizationUserViewSet, basename='organization-user')

urlpatterns = [
    path('', include(router.urls)),
    # Public invite endpoints
    path('invites/<str:token>/info/', views.InviteInfoView.as_view(), name='invite-info'),
    path('invites/<str:token>/accept/', views.AcceptInviteView.as_view(), name='accept-invite'),
]

