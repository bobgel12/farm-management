from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Farm, Worker
from .serializers import FarmSerializer, FarmListSerializer, WorkerSerializer


class FarmListCreateView(generics.ListCreateAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer


class FarmDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer


@api_view(['GET'])
def farm_dashboard(request):
    """Get dashboard data for all farms"""
    farms = Farm.objects.filter(is_active=True)
    data = {
        'total_farms': farms.count(),
        'total_houses': sum(farm.total_houses for farm in farms),
        'active_houses': sum(farm.active_houses for farm in farms),
        'farms': FarmListSerializer(farms, many=True).data
    }
    return Response(data)


class WorkerListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkerSerializer

    def get_queryset(self):
        farm_id = self.request.query_params.get('farm_id')
        if farm_id:
            return Worker.objects.filter(farm_id=farm_id)
        return Worker.objects.all()

    def perform_create(self, serializer):
        farm_id = self.request.data.get('farm_id')
        if farm_id:
            farm = get_object_or_404(Farm, id=farm_id)
            serializer.save(farm=farm)


class WorkerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer


@api_view(['GET'])
def farm_workers(request, farm_id):
    """Get all workers for a specific farm"""
    farm = get_object_or_404(Farm, id=farm_id)
    workers = Worker.objects.filter(farm=farm, is_active=True)
    serializer = WorkerSerializer(workers, many=True)
    return Response(serializer.data)
