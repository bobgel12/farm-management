from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime
from .models import House, HouseMonitoringSnapshot, HouseAlarm
from .serializers import (
    HouseSerializer, HouseListSerializer,
    HouseMonitoringSnapshotSerializer, HouseMonitoringSummarySerializer,
    HouseMonitoringStatsSerializer, HouseAlarmSerializer
)
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


# Monitoring endpoints

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_latest(request, house_id):
    """Get latest monitoring snapshot for a house"""
    house = get_object_or_404(House, id=house_id)
    snapshot = house.get_latest_snapshot()
    
    if not snapshot:
        return Response({
            'status': 'no_data',
            'message': 'No monitoring data available for this house'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = HouseMonitoringSnapshotSerializer(snapshot)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_history(request, house_id):
    """Get historical monitoring snapshots for a house"""
    house = get_object_or_404(House, id=house_id)
    
    # Get query parameters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    limit = int(request.query_params.get('limit', 100))
    
    # Default to last 24 hours if no dates provided
    if not end_date:
        end_date = timezone.now()
    else:
        try:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            end_date = timezone.now()
    
    if not start_date:
        start_date = end_date - timedelta(hours=24)
    else:
        try:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            start_date = end_date - timedelta(hours=24)
    
    snapshots = house.get_snapshots_for_range(start_date, end_date)[:limit]
    
    serializer = HouseMonitoringSummarySerializer(snapshots, many=True)
    return Response({
        'count': len(serializer.data),
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_monitoring_stats(request, house_id):
    """Get statistical aggregations for house monitoring data"""
    house = get_object_or_404(House, id=house_id)
    
    # Get period parameter (default 7 days)
    period = int(request.query_params.get('period', 7))
    
    stats = house.get_stats(days=period)
    
    if not stats:
        return Response({
            'status': 'no_data',
            'message': f'No monitoring data available for the last {period} days'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = HouseMonitoringStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_houses_monitoring_all(request, farm_id):
    """Get latest monitoring data for all houses in a farm"""
    farm = get_object_or_404(Farm, id=farm_id)
    houses = House.objects.filter(farm=farm, is_active=True)
    
    results = []
    for house in houses:
        snapshot = house.get_latest_snapshot()
        if snapshot:
            serializer = HouseMonitoringSummarySerializer(snapshot)
            results.append(serializer.data)
        else:
            results.append({
                'house_id': house.id,
                'house_number': house.house_number,
                'status': 'no_data',
                'message': 'No monitoring data available'
            })
    
    return Response({
        'farm_id': farm_id,
        'farm_name': farm.name,
        'houses_count': len(results),
        'houses': results
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def farm_houses_monitoring_dashboard(request, farm_id):
    """Get dashboard data with alerts and summaries for all houses"""
    farm = get_object_or_404(Farm, id=farm_id)
    houses = House.objects.filter(farm=farm, is_active=True)
    
    dashboard_data = {
        'farm_id': farm_id,
        'farm_name': farm.name,
        'total_houses': houses.count(),
        'houses': [],
        'alerts_summary': {
            'total_active': 0,
            'critical': 0,
            'warning': 0,
            'normal': 0
        },
        'connection_summary': {
            'connected': 0,
            'disconnected': 0
        }
    }
    
    for house in houses:
        snapshot = house.get_latest_snapshot()
        active_alarms = HouseAlarm.objects.filter(house=house, is_active=True).count()
        
        house_data = {
            'house_id': house.id,
            'house_number': house.house_number,
            'current_day': house.current_day,
            'status': house.status,
        }
        
        if snapshot:
            serializer = HouseMonitoringSummarySerializer(snapshot)
            house_data.update(serializer.data)
            
            # Update summary counts
            if snapshot.alarm_status == 'critical':
                dashboard_data['alerts_summary']['critical'] += 1
            elif snapshot.alarm_status == 'warning':
                dashboard_data['alerts_summary']['warning'] += 1
            else:
                dashboard_data['alerts_summary']['normal'] += 1
            
            if snapshot.is_connected:
                dashboard_data['connection_summary']['connected'] += 1
            else:
                dashboard_data['connection_summary']['disconnected'] += 1
        else:
            house_data['status'] = 'no_data'
        
        house_data['active_alarms_count'] = active_alarms
        dashboard_data['alerts_summary']['total_active'] += active_alarms
        
        dashboard_data['houses'].append(house_data)
    
    return Response(dashboard_data)
