from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import House
from .serializers import HouseSerializer, HouseListSerializer
from farms.models import Farm
from tasks.task_scheduler import TaskScheduler


class HouseListCreateView(generics.ListCreateAPIView):
    serializer_class = HouseSerializer

    def get_queryset(self):
        farm_id = self.request.query_params.get('farm_id')
        if farm_id:
            return House.objects.filter(farm_id=farm_id)
        return House.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return HouseListSerializer
        return HouseSerializer

    def perform_create(self, serializer):
        house = serializer.save()
        # Automatically generate tasks for the new house
        TaskScheduler.generate_tasks_for_house(house)
        
        # Auto-complete past tasks if the house has a chicken_in_date in the past
        if house.chicken_in_date:
            current_day = house.current_day
            if current_day is not None and current_day > 0:
                from tasks.models import Task
                from django.utils import timezone
                
                past_tasks = Task.objects.filter(
                    house=house,
                    day_offset__lt=current_day,
                    is_completed=False
                )
                
                if past_tasks.exists():
                    past_tasks.update(
                        is_completed=True,
                        completed_at=timezone.now(),
                        completed_by='system_auto_complete',
                        notes='Automatically marked as completed - past task after house creation'
                    )
        
        return house


class HouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = House.objects.all()
    serializer_class = HouseSerializer


@api_view(['GET'])
def house_dashboard(request):
    """Get dashboard data for all houses"""
    houses = House.objects.filter(is_active=True)
    
    # Count houses by status
    status_counts = {}
    for house in houses:
        status = house.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Get houses that need attention today
    today_houses = []
    for house in houses:
        current_day = house.current_day
        if current_day is not None and current_day in [-1, 0, 1, 7, 8, 13, 14, 20, 21, 35, 39, 40, 41]:
            today_houses.append({
                'id': house.id,
                'farm_name': house.farm.name,
                'house_number': house.house_number,
                'current_day': current_day,
                'status': house.status
            })
    
    data = {
        'total_houses': houses.count(),
        'status_counts': status_counts,
        'today_houses': today_houses
    }
    return Response(data)


@api_view(['GET'])
def farm_houses(request, farm_id):
    """Get all houses for a specific farm"""
    farm = get_object_or_404(Farm, id=farm_id)
    houses = House.objects.filter(farm=farm)
    serializer = HouseListSerializer(houses, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def farm_house_detail(request, farm_id, house_id):
    """Get a specific house within a farm context"""
    farm = get_object_or_404(Farm, id=farm_id)
    house = get_object_or_404(House, id=house_id, farm=farm)
    serializer = HouseSerializer(house)
    return Response(serializer.data)


@api_view(['GET'])
def farm_task_summary(request, farm_id):
    """Get task summary for all houses in a farm"""
    farm = get_object_or_404(Farm, id=farm_id)
    houses = House.objects.filter(farm=farm, is_active=True)
    
    summary = {
        'farm_name': farm.name,
        'total_houses': houses.count(),
        'houses': []
    }
    
    for house in houses:
        current_day = house.current_day
        house_data = {
            'id': house.id,
            'house_number': house.house_number,
            'current_day': current_day,
            'status': house.status,
            'chicken_in_date': house.chicken_in_date,
            'chicken_out_date': house.chicken_out_date,
            'tasks': {
                'total': 0,
                'completed': 0,
                'pending': 0,
                'overdue': 0,
                'today': 0
            },
            'pending_tasks': []
        }
        
        if current_day is not None:
            from tasks.models import Task
            
            # Get all tasks for this house
            all_tasks = Task.objects.filter(house=house)
            house_data['tasks']['total'] = all_tasks.count()
            house_data['tasks']['completed'] = all_tasks.filter(is_completed=True).count()
            house_data['tasks']['pending'] = all_tasks.filter(is_completed=False).count()
            
            # Get today's tasks
            today_tasks = all_tasks.filter(day_offset=current_day, is_completed=False)
            house_data['tasks']['today'] = today_tasks.count()
            
            # Get overdue tasks (tasks from previous days that are incomplete)
            if current_day > 0:
                overdue_tasks = all_tasks.filter(
                    day_offset__lt=current_day,
                    is_completed=False
                )
                house_data['tasks']['overdue'] = overdue_tasks.count()
            
            # Get pending tasks (future tasks and today's tasks)
            pending_tasks = all_tasks.filter(
                day_offset__gte=current_day,
                is_completed=False
            ).order_by('day_offset', 'task_name')
            
            house_data['pending_tasks'] = [
                {
                    'id': task.id,
                    'task_name': task.task_name,
                    'description': task.description,
                    'day_offset': task.day_offset,
                    'task_type': task.task_type,
                    'is_today': task.day_offset == current_day
                }
                for task in pending_tasks
            ]
        
        summary['houses'].append(house_data)
    
    return Response(summary)
