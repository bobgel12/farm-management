from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RotemDataViewSet, MLPredictionViewSet, MLModelViewSet, RotemControllerViewSet,
    RotemFarmViewSet, RotemUserViewSet, RotemScrapeLogViewSet, RotemScraperViewSet
)
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import RotemFarm
from .serializers import RotemFarmSerializer

router = DefaultRouter()
router.register(r'data', RotemDataViewSet)
router.register(r'predictions', MLPredictionViewSet)
router.register(r'ml-models', MLModelViewSet)
router.register(r'controllers', RotemControllerViewSet)
router.register(r'farms', RotemFarmViewSet, basename='rotem-farm')
router.register(r'users', RotemUserViewSet)
router.register(r'logs', RotemScrapeLogViewSet)
router.register(r'scraper', RotemScraperViewSet, basename='scraper')

@api_view(['GET'])
def farm_detail(request, farm_id):
    """Farm detail endpoint using farm_id as lookup field"""
    try:
        farm = get_object_or_404(RotemFarm, farm_id=farm_id)
        serializer = RotemFarmSerializer(farm)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=404)

urlpatterns = [
    # Simple test endpoint - put this BEFORE router to take precedence
    path('farms/<str:farm_id>/', farm_detail, name='farm-detail-test'),
    path('', include(router.urls)),
]
