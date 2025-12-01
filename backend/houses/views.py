from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime
from .models import House, HouseMonitoringSnapshot, HouseAlarm, Device, DeviceStatus, ControlSettings, TemperatureCurve, HouseConfiguration, Sensor
from .serializers import (
    HouseSerializer, HouseListSerializer,
    HouseMonitoringSnapshotSerializer, HouseMonitoringSummarySerializer,
    HouseMonitoringStatsSerializer, HouseAlarmSerializer,
    HouseComparisonSerializer, DeviceSerializer, DeviceStatusSerializer,
    ControlSettingsSerializer, TemperatureCurveSerializer,
    HouseConfigurationSerializer, SensorSerializer
)
from farms.models import Farm
from tasks.task_scheduler import TaskScheduler
from tasks.serializers import TaskSerializer


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def house_details(request, house_id):
    """Get comprehensive house details including monitoring, devices, flock, tasks, and feed"""
    house = get_object_or_404(House, id=house_id)
    
    # Get latest snapshot
    snapshot = house.get_latest_snapshot()
    
    # Get active alarms
    active_alarms = HouseAlarm.objects.filter(house=house, is_active=True)
    
    # Get tasks for this house
    from tasks.models import Task
    from tasks.serializers import TaskSerializer
    tasks = Task.objects.filter(house=house).order_by('day_offset', 'task_name')
    
    # Group tasks by status
    current_day = house.current_day
    upcoming_tasks = []
    past_tasks = []
    today_tasks = []
    completed_tasks = []
    
    for task in tasks:
        if task.is_completed:
            completed_tasks.append(task)
        elif current_day is not None:
            if task.day_offset < current_day:
                past_tasks.append(task)
            elif task.day_offset == current_day:
                today_tasks.append(task)
            else:
                upcoming_tasks.append(task)
        else:
            upcoming_tasks.append(task)
    
    # Build comprehensive response
    details = {
        'house': HouseSerializer(house).data,
        'monitoring': HouseMonitoringSnapshotSerializer(snapshot).data if snapshot else None,
        'alarms': HouseAlarmSerializer(active_alarms, many=True).data,
        'stats': house.get_stats(days=7) if snapshot else None,
        'tasks': {
            'all': TaskSerializer(tasks, many=True).data,
            'today': TaskSerializer(today_tasks, many=True).data,
            'upcoming': TaskSerializer(upcoming_tasks, many=True).data,
            'past': TaskSerializer(past_tasks, many=True).data,
            'completed': TaskSerializer(completed_tasks, many=True).data,
            'total': tasks.count(),
            'completed_count': len(completed_tasks),
            'pending_count': tasks.count() - len(completed_tasks),
        },
    }
    
    return Response(details)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def houses_comparison(request):
    """Get comparison data for multiple houses across farms"""
    # Get query parameters
    farm_id = request.query_params.get('farm_id')
    house_ids = request.query_params.getlist('house_ids')
    favorites_only = request.query_params.get('favorites', 'false').lower() == 'true'
    
    # Build queryset
    houses = House.objects.filter(is_active=True)
    
    if farm_id:
        houses = houses.filter(farm_id=farm_id)
    
    if house_ids:
        houses = houses.filter(id__in=house_ids)
    
    # TODO: Implement favorites when user preferences are added
    # if favorites_only:
    #     houses = houses.filter(id__in=user_favorite_house_ids)
    
    # Get comparison data for each house
    comparison_data = []
    
    for house in houses:
        snapshot = house.get_latest_snapshot()
        # Use age_days which prefers Rotem's current_age_days over calculated current_day
        age_days = house.age_days
        
        # Determine if house is full (has chickens)
        is_full_house = age_days is not None and age_days >= 0
        
        # Get ventilation mode from snapshot or default
        ventilation_mode = None
        if snapshot:
            # Try to extract ventilation mode from raw_data or sensor_data
            raw_data = snapshot.raw_data or {}
            sensor_data = snapshot.sensor_data or {}
            
            # Check common ventilation mode fields
            ventilation_mode = (
                raw_data.get('ventilation_mode') or
                raw_data.get('ventMode') or
                sensor_data.get('ventilation_mode') or
                'Minimum Vent.'  # Default
            )
        
        house_comparison = {
            'house_id': house.id,
            'house_number': house.house_number,
            'farm_id': house.farm.id,
            'farm_name': house.farm.name,
            
            # House Status - use age_days for consistency (prefers Rotem age over calculated)
            'current_day': age_days,
            'age_days': age_days,
            'current_age_days': house.current_age_days,
            'is_integrated': house.is_integrated,
            'status': house.status,
            'is_full_house': is_full_house,
            
            # Time
            'last_update_time': snapshot.timestamp if snapshot else None,
            
            # Metrics - Temperature
            'average_temperature': snapshot.average_temperature if snapshot else None,
            'outside_temperature': snapshot.outside_temperature if snapshot else None,
            'tunnel_temperature': None,  # Will be extracted from sensor_data if available
            'target_temperature': snapshot.target_temperature if snapshot else None,
            
            # Metrics - Environment
            'static_pressure': snapshot.static_pressure if snapshot else None,
            'inside_humidity': snapshot.humidity if snapshot else None,
            'ventilation_mode': ventilation_mode,
            'ventilation_level': snapshot.ventilation_level if snapshot else None,
            'airflow_cfm': snapshot.airflow_cfm if snapshot else None,
            
            # Metrics - Consumption (Daily)
            'water_consumption': snapshot.water_consumption if snapshot else None,
            'feed_consumption': snapshot.feed_consumption if snapshot else None,
            
            # Metrics - Bird Status
            'bird_count': snapshot.bird_count if snapshot else None,
            'livability': snapshot.livability if snapshot else None,
            'growth_day': snapshot.growth_day if snapshot else None,
            
            # Additional status
            'is_connected': snapshot.is_connected if snapshot else False,
            'has_alarms': snapshot.has_alarms if snapshot else False,
            'alarm_status': snapshot.alarm_status if snapshot else 'normal',
        }
        
        # Extract tunnel temperature from sensor data if available
        if snapshot and snapshot.sensor_data:
            sensor_data = snapshot.sensor_data
            # Try common field names for tunnel temperature
            house_comparison['tunnel_temperature'] = (
                sensor_data.get('tunnel_temperature') or
                sensor_data.get('tunnelTemp') or
                sensor_data.get('tunnel_temp') or
                None
            )
        
        comparison_data.append(house_comparison)
    
    # Sort by farm name, then house number
    comparison_data.sort(key=lambda x: (x['farm_name'], x['house_number']))
    
    serializer = HouseComparisonSerializer(comparison_data, many=True)
    return Response({
        'count': len(serializer.data),
        'houses': serializer.data
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def house_devices(request, house_id):
    """Get all devices for a house or create a new device"""
    house = get_object_or_404(House, id=house_id)
    
    if request.method == 'GET':
        devices = Device.objects.filter(house=house)
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(house=house)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def device_detail(request, device_id):
    """Get, update, or delete a specific device"""
    device = get_object_or_404(Device, id=device_id)
    
    if request.method == 'GET':
        serializer = DeviceSerializer(device)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = DeviceSerializer(device, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            # Create status history record
            DeviceStatus.objects.create(
                device=device,
                status=device.status,
                percentage=device.percentage,
                notes=f"Updated via API"
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        device.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def device_control(request, device_id):
    """Control a device (turn on/off, set percentage, etc.)"""
    device = get_object_or_404(Device, id=device_id)
    
    action = request.data.get('action')  # 'on', 'off', 'set_percentage'
    percentage = request.data.get('percentage')
    
    if action == 'on':
        device.status = 'on'
    elif action == 'off':
        device.status = 'off'
    elif action == 'set_percentage' and percentage is not None:
        device.status = 'on'
        device.percentage = max(0, min(100, float(percentage)))
    else:
        return Response(
            {'error': 'Invalid action or missing parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    device.save()
    
    # Create status history record
    DeviceStatus.objects.create(
        device=device,
        status=device.status,
        percentage=device.percentage,
        notes=f"Controlled via API: {action}"
    )
    
    serializer = DeviceSerializer(device)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_status_history(request, device_id):
    """Get status history for a device"""
    device = get_object_or_404(Device, id=device_id)
    
    limit = int(request.query_params.get('limit', 100))
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    history = DeviceStatus.objects.filter(device=device)
    
    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            history = history.filter(timestamp__gte=start_date)
        except (ValueError, AttributeError):
            pass
    
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            history = history.filter(timestamp__lte=end_date)
        except (ValueError, AttributeError):
            pass
    
    history = history[:limit]
    serializer = DeviceStatusSerializer(history, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def house_control_settings(request, house_id):
    """Get or update control settings for a house"""
    house = get_object_or_404(House, id=house_id)
    
    # Get or create control settings
    control_settings, created = ControlSettings.objects.get_or_create(house=house)
    
    if request.method == 'GET':
        serializer = ControlSettingsSerializer(control_settings)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = ControlSettingsSerializer(
            control_settings,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def temperature_curve(request, house_id):
    """Get or update temperature curve for a house"""
    house = get_object_or_404(House, id=house_id)
    control_settings, _ = ControlSettings.objects.get_or_create(house=house)
    
    if request.method == 'GET':
        curves = TemperatureCurve.objects.filter(control_settings=control_settings)
        serializer = TemperatureCurveSerializer(curves, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Update or create temperature curve points
        curve_data = request.data
        if isinstance(curve_data, list):
            # Bulk update
            TemperatureCurve.objects.filter(control_settings=control_settings).delete()
            curves = []
            for item in curve_data:
                curve = TemperatureCurve.objects.create(
                    control_settings=control_settings,
                    day=item['day'],
                    target_temperature=item['target_temperature'],
                    notes=item.get('notes', '')
                )
                curves.append(curve)
            serializer = TemperatureCurveSerializer(curves, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Single curve point
            serializer = TemperatureCurveSerializer(data=curve_data)
            if serializer.is_valid():
                serializer.save(control_settings=control_settings)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def house_configuration(request, house_id):
    """Get or update house configuration"""
    house = get_object_or_404(House, id=house_id)
    config, created = HouseConfiguration.objects.get_or_create(house=house)
    
    if request.method == 'GET':
        serializer = HouseConfigurationSerializer(config)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = HouseConfigurationSerializer(
            config,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def house_sensors(request, house_id):
    """Get or create sensors for a house"""
    house = get_object_or_404(House, id=house_id)
    
    if request.method == 'GET':
        sensors = Sensor.objects.filter(house=house)
        serializer = SensorSerializer(sensors, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = SensorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(house=house)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_water_anomaly_detection(request, house_id=None):
    """
    Trigger water consumption anomaly detection on demand
    
    Can be called with:
    - house_id in URL path: Check specific house
    - farm_id in request body: Check all houses in farm
    - No parameters: Check all Rotem-integrated houses
    
    If Celery workers are not available, runs synchronously as fallback.
    """
    from houses.tasks import monitor_water_consumption
    from celery.result import AsyncResult
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        farm_id = request.data.get('farm_id')
        run_sync = request.data.get('run_sync', False)  # Allow forcing synchronous execution
        
        # Import the implementation function for synchronous execution
        from houses.tasks import monitor_water_consumption_impl
        
        # Check if we should run synchronously (if CELERY_TASK_ALWAYS_EAGER is set or run_sync is True)
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False) or run_sync:
            logger.info(f"Running water consumption monitoring synchronously (house_id={house_id}, farm_id={farm_id})")
            # Run synchronously using the implementation function
            result = monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id)
            
            return Response({
                'status': 'success',
                'message': 'Water consumption anomaly detection completed',
                'task_id': None,
                'house_id': house_id,
                'farm_id': farm_id,
                'result': result,
                'execution_mode': 'synchronous',
            }, status=status.HTTP_200_OK)
        
        # Try to run asynchronously
        try:
            task_result = monitor_water_consumption.delay(house_id=house_id, farm_id=farm_id)
            
            # Check if task is actually queued (not stuck in PENDING)
            # Wait a moment to see if it gets picked up
            import time
            time.sleep(0.5)
            
            async_result = AsyncResult(task_result.id)
            if async_result.state == 'PENDING':
                # Task is still pending - workers might not be running
                # Check if we can connect to the broker
                try:
                    from celery import current_app
                    inspect = current_app.control.inspect()
                    active_workers = inspect.active()
                    
                    if not active_workers:
                        # No active workers, run synchronously as fallback
                        logger.warning("No Celery workers available, running synchronously as fallback")
                        result = monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id)
                        
                        return Response({
                            'status': 'success',
                            'message': 'Water consumption anomaly detection completed (ran synchronously - no workers available)',
                            'task_id': None,
                            'house_id': house_id,
                            'farm_id': farm_id,
                            'result': result,
                            'execution_mode': 'synchronous_fallback',
                            'warning': 'Celery workers are not running. Task executed synchronously.',
                        }, status=status.HTTP_200_OK)
                except Exception as inspect_error:
                    logger.warning(f"Could not inspect Celery workers: {inspect_error}. Running synchronously as fallback.")
                    result = monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id)
                    
                    return Response({
                        'status': 'success',
                        'message': 'Water consumption anomaly detection completed (ran synchronously)',
                        'task_id': None,
                        'house_id': house_id,
                        'farm_id': farm_id,
                        'result': result,
                        'execution_mode': 'synchronous_fallback',
                        'warning': 'Could not verify Celery workers. Task executed synchronously.',
                    }, status=status.HTTP_200_OK)
            
            logger.info(f"Triggered water consumption monitoring task {task_result.id} (house_id={house_id}, farm_id={farm_id})")
            
            return Response({
                'status': 'success',
                'message': 'Water consumption anomaly detection started',
                'task_id': task_result.id,
                'house_id': house_id,
                'farm_id': farm_id,
                'execution_mode': 'asynchronous',
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as celery_error:
            # Celery error - fallback to synchronous execution
            logger.warning(f"Celery task submission failed: {celery_error}. Running synchronously as fallback.")
            result = monitor_water_consumption_impl(house_id=house_id, farm_id=farm_id)
            
            return Response({
                'status': 'success',
                'message': 'Water consumption anomaly detection completed (ran synchronously)',
                'task_id': None,
                'house_id': house_id,
                'farm_id': farm_id,
                'result': result,
                'execution_mode': 'synchronous_fallback',
                'warning': f'Celery unavailable: {str(celery_error)}. Task executed synchronously.',
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error triggering water anomaly detection: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_water_anomaly_detection_status(request, task_id):
    """
    Check the status and results of a water consumption anomaly detection task
    """
    from celery.result import AsyncResult
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get task result
        task_result = AsyncResult(task_id)
        
        # Check task state
        task_state = task_result.state
        
        response_data = {
            'task_id': task_id,
            'state': task_state,
        }
        
        if task_state == 'PENDING':
            response_data['status'] = 'pending'
            response_data['message'] = 'Task is waiting to be processed'
        elif task_state == 'PROGRESS':
            response_data['status'] = 'running'
            response_data['message'] = 'Task is currently running'
            # Include progress info if available
            if task_result.info:
                response_data['info'] = task_result.info
        elif task_state == 'SUCCESS':
            response_data['status'] = 'success'
            response_data['message'] = 'Task completed successfully'
            # Get the result
            result = task_result.result
            if isinstance(result, dict):
                response_data.update({
                    'houses_checked': result.get('houses_checked', 0),
                    'alerts_created': result.get('alerts_created', 0),
                    'emails_sent': result.get('emails_sent', 0),
                    'timestamp': result.get('timestamp'),
                })
            else:
                response_data['result'] = result
        elif task_state == 'FAILURE':
            response_data['status'] = 'failure'
            response_data['message'] = 'Task failed'
            # Get error info
            try:
                response_data['error'] = str(task_result.info)
            except:
                response_data['error'] = 'Unknown error occurred'
        else:
            response_data['status'] = 'unknown'
            response_data['message'] = f'Task state: {task_state}'
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
