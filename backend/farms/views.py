from rest_framework import generics, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from .models import Farm, Worker, Program, ProgramTask, ProgramChangeLog
from .serializers import (
    FarmSerializer, FarmListSerializer, WorkerSerializer,
    ProgramSerializer, ProgramListSerializer, ProgramTaskSerializer,
    FarmWithProgramSerializer
)
from .program_change_service import ProgramChangeService
from integrations.rotem import RotemIntegration
from integrations.models import IntegrationLog, IntegrationError


class FarmViewSet(ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    
    @action(detail=True, methods=['post'])
    def configure_integration(self, request, pk=None):
        """Configure system integration for a farm"""
        farm = self.get_object()
        integration_type = request.data.get('integration_type')
        
        if integration_type == 'rotem':
            # Validate Rotem credentials
            username = request.data.get('username')
            password = request.data.get('password')
            
            if not username or not password:
                return Response({
                    'error': 'Username and password are required for Rotem integration'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Test connection
            try:
                # Temporarily set credentials for testing
                farm.rotem_username = username
                farm.rotem_password = password
                farm.save()
                
                integration = RotemIntegration(farm)
                if integration.test_connection():
                    farm.integration_type = 'rotem'
                    farm.integration_status = 'active'
                    farm.save()
                    
                    # Sync house data
                    self._sync_rotem_houses(farm)
                    
                    return Response({
                        'status': 'success',
                        'message': 'Rotem integration configured successfully',
                        'integration_type': 'rotem',
                        'integration_status': 'active'
                    })
                else:
                    farm.integration_status = 'error'
                    farm.save()
                    return Response({
                        'error': 'Invalid Rotem credentials or connection failed'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                farm.integration_status = 'error'
                farm.save()
                return Response({
                    'error': f'Integration configuration failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif integration_type == 'none':
            farm.integration_type = 'none'
            farm.integration_status = 'not_configured'
            farm.has_system_integration = False
            farm.save()
            return Response({
                'status': 'success',
                'message': 'Integration disabled',
                'integration_type': 'none',
                'integration_status': 'not_configured'
            })
        
        return Response({
            'error': 'Invalid integration type'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test connection for integrated farms"""
        farm = self.get_object()
        
        if farm.integration_type == 'rotem':
            try:
                integration = RotemIntegration(farm)
                success = integration.test_connection()
                
                if success:
                    farm.integration_status = 'active'
                    farm.last_sync = timezone.now()
                    farm.save()
                    return Response({
                        'status': 'success',
                        'message': 'Connection test successful'
                    })
                else:
                    farm.integration_status = 'error'
                    farm.save()
                    return Response({
                        'status': 'error',
                        'message': 'Connection test failed'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': f'Connection test failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': 'No integration configured for this farm'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_data(self, request, pk=None):
        """Sync data from integrated system"""
        farm = self.get_object()
        
        if farm.integration_type == 'rotem':
            try:
                integration = RotemIntegration(farm)
                data = integration.sync_house_data(farm.id)
                
                # Update last sync time
                farm.last_sync = timezone.now()
                farm.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Data synced successfully',
                    'data_points': len(data.get('houses', []))
                })
                
            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': f'Data sync failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': 'No integration configured for this farm'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def integration_status(self, request, pk=None):
        """Get integration status and health"""
        farm = self.get_object()
        
        status_data = {
            'integration_type': farm.integration_type,
            'integration_status': farm.integration_status,
            'has_system_integration': farm.has_system_integration,
            'last_sync': farm.last_sync,
            'is_healthy': False,
            'health_details': {}
        }
        
        if farm.integration_type == 'rotem':
            try:
                integration = RotemIntegration(farm)
                health = integration.get_health_status()
                
                if health:
                    status_data['is_healthy'] = health.is_healthy
                    status_data['health_details'] = {
                        'success_rate_24h': health.success_rate_24h,
                        'consecutive_failures': health.consecutive_failures,
                        'average_response_time': health.average_response_time,
                        'last_successful_sync': health.last_successful_sync,
                        'last_attempted_sync': health.last_attempted_sync
                    }
            except Exception as e:
                status_data['health_details']['error'] = str(e)
        
        return Response(status_data)
    
    def _sync_rotem_houses(self, farm):
        """Sync houses from Rotem system"""
        try:
            integration = RotemIntegration(farm)
            house_count = integration.get_house_count(farm.id)
            
            # Create or update houses
            for i in range(1, house_count + 1):
                from houses.models import House
                house, created = House.objects.get_or_create(
                    farm=farm,
                    house_number=i,
                    defaults={
                        'capacity': 1000,  # Default capacity
                        'is_integrated': True,
                        'system_house_id': f'house_{i}',
                        'chicken_in_date': timezone.now().date(),  # Default date
                        'current_age_days': 0
                    }
                )
                if created:
                    # Set initial age from Rotem
                    age = integration.get_house_age(farm.id, i)
                    house.current_age_days = age
                    house.save()
                    
        except Exception as e:
            # Log error but don't fail the integration setup
            IntegrationError.objects.create(
                farm=farm,
                integration_type='rotem',
                error_type='house_sync',
                error_message=f'Failed to sync houses: {str(e)}'
            )


# Legacy views for backward compatibility
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


# Program Views
class ProgramListCreateView(generics.ListCreateAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProgramListSerializer
        return ProgramSerializer


class ProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    
    def update(self, request, *args, **kwargs):
        """Override update to detect program changes"""
        instance = self.get_object()
        
        # Get current tasks before update
        old_tasks = list(instance.tasks.all())
        
        # Perform the update
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get updated tasks
            instance.refresh_from_db()
            new_tasks = list(instance.tasks.all())
            
            # Detect changes
            changes = ProgramChangeService.detect_program_changes(instance, old_tasks, new_tasks)
            
            if changes:
                # Get impact analysis
                impact_analysis = ProgramChangeService.get_farm_impact_analysis(instance, changes)
                
                # Create change log
                change_log = ProgramChangeService.create_change_log(instance, changes)
                
                # Return response with change information
                response.data['change_detected'] = True
                response.data['change_log_id'] = change_log.id
                response.data['impact_analysis'] = {
                    'affected_farms_count': impact_analysis['impact_summary']['total_farms'],
                    'active_houses_count': impact_analysis['impact_summary']['active_houses'],
                    'changes_count': len(changes),
                    'critical_changes': impact_analysis['impact_summary']['critical_changes'],
                    'moderate_changes': impact_analysis['impact_summary']['moderate_changes'],
                    'minor_changes': impact_analysis['impact_summary']['minor_changes'],
                    'affected_farms': [
                        {
                            'id': farm.id,
                            'name': farm.name,
                            'active_houses': farm.active_houses
                        } for farm in impact_analysis['affected_farms']
                    ]
                }
            else:
                response.data['change_detected'] = False
        
        return response


@api_view(['GET'])
def program_tasks(request, program_id):
    """Get all tasks for a specific program"""
    program = get_object_or_404(Program, id=program_id)
    tasks = ProgramTask.objects.filter(program=program).order_by('day', 'priority', 'title')
    serializer = ProgramTaskSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def program_tasks_by_day(request, program_id, day):
    """Get tasks for a specific program and day"""
    program = get_object_or_404(Program, id=program_id)
    tasks = ProgramTask.objects.filter(program=program, day=day).order_by('priority', 'title')
    serializer = ProgramTaskSerializer(tasks, many=True)
    return Response(serializer.data)


class ProgramTaskListCreateView(generics.ListCreateAPIView):
    serializer_class = ProgramTaskSerializer

    def get_queryset(self):
        program_id = self.request.query_params.get('program_id')
        if program_id:
            return ProgramTask.objects.filter(program_id=program_id).order_by('day', 'priority', 'title')
        return ProgramTask.objects.all().order_by('day', 'priority', 'title')

    def perform_create(self, serializer):
        program_id = self.request.data.get('program_id')
        if program_id:
            program = get_object_or_404(Program, id=program_id)
            serializer.save(program=program)


class ProgramTaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProgramTask.objects.all()
    serializer_class = ProgramTaskSerializer


@api_view(['POST'])
def copy_program(request, program_id):
    """Copy an existing program to create a new one"""
    program = get_object_or_404(Program, id=program_id)
    new_name = request.data.get('name', f"{program.name} (Copy)")
    
    # Create new program
    new_program = Program.objects.create(
        name=new_name,
        description=program.description,
        duration_days=program.duration_days,
        is_active=True,
        is_default=False
    )
    
    # Copy all tasks
    for task in program.tasks.all():
        ProgramTask.objects.create(
            program=new_program,
            day=task.day,
            task_type=task.task_type,
            title=task.title,
            description=task.description,
            instructions=task.instructions,
            priority=task.priority,
            estimated_duration=task.estimated_duration,
            is_required=task.is_required,
            requires_confirmation=task.requires_confirmation,
            recurring_days=task.recurring_days
        )
    
    serializer = ProgramSerializer(new_program)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def default_program(request):
    """Get the default program"""
    try:
        program = Program.objects.get(is_default=True, is_active=True)
        serializer = ProgramSerializer(program)
        return Response(serializer.data)
    except Program.DoesNotExist:
        return Response(
            {'error': 'No default program found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def ensure_default_program(request):
    """Ensure a default program exists, create if needed"""
    try:
        # Check if default program already exists
        try:
            program = Program.objects.get(is_default=True, is_active=True)
            serializer = ProgramSerializer(program)
            return Response({
                'message': 'Default program already exists',
                'program': serializer.data,
                'total_tasks': program.tasks.count()
            })
        except Program.DoesNotExist:
            pass
        
        # Create default program using the management command
        from django.core.management import call_command
        from io import StringIO
        
        # Run the ensure_default_program command
        output = StringIO()
        call_command('ensure_default_program', stdout=output)
        
        # Get the created program
        program = Program.objects.get(is_default=True, is_active=True)
        serializer = ProgramSerializer(program)
        
        return Response({
            'message': 'Default program created successfully',
            'program': serializer.data,
            'total_tasks': program.tasks.count(),
            'command_output': output.getvalue()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to ensure default program: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def pending_program_changes(request):
    """Get all pending program changes that need user decision"""
    changes = ProgramChangeService.get_pending_changes()
    data = []
    
    for change in changes:
        data.append({
            'id': change.id,
            'program_name': change.program.name,
            'change_type': change.change_type,
            'change_description': change.change_description,
            'created_at': change.created_at,
            'affected_farms_count': change.affected_farms.count(),
            'affected_farms': [
                {
                    'id': farm.id,
                    'name': farm.name,
                    'active_houses': farm.active_houses
                } for farm in change.affected_farms.all()
            ]
        })
    
    return Response(data)


@api_view(['POST'])
def handle_program_change(request, change_log_id):
    """Handle a program change with user's choice"""
    try:
        change_log = ProgramChangeLog.objects.get(id=change_log_id)
        user_choice = request.data.get('choice')
        
        if user_choice not in ['retroactive', 'next_flock']:
            return Response(
                {'error': 'Invalid choice. Must be retroactive or next_flock'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        change_log.user_choice = user_choice
        change_log.save()
        
        if user_choice == 'retroactive':
            success = ProgramChangeService.apply_retroactive_changes(change_log)
            if not success:
                return Response(
                    {'error': 'Failed to apply retroactive changes'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response({
            'message': f'Program change handled successfully with choice: {user_choice}',
            'processed': change_log.is_processed
        })
        
    except ProgramChangeLog.DoesNotExist:
        return Response(
            {'error': 'Change log not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def program_change_impact(request, program_id):
    """Get impact analysis for a specific program"""
    try:
        program = Program.objects.get(id=program_id)
        affected_farms = ProgramChangeService.get_affected_farms(program)
        
        impact_data = {
            'program': {
                'id': program.id,
                'name': program.name,
                'total_tasks': program.total_tasks
            },
            'affected_farms': [
                {
                    'id': farm.id,
                    'name': farm.name,
                    'location': farm.location,
                    'active_houses': farm.active_houses,
                    'total_houses': farm.total_houses,
                    'houses': [
                        {
                            'id': house.id,
                            'name': house.name,
                            'chicken_in_date': house.chicken_in_date,
                            'chicken_out_date': house.chicken_out_date,
                            'current_day': house.current_day if house.chicken_in_date else None
                        } for house in farm.houses.filter(is_active=True)
                    ]
                } for farm in affected_farms
            ],
            'summary': {
                'total_farms': len(affected_farms),
                'total_active_houses': sum(farm.active_houses for farm in affected_farms),
                'farms_with_active_flocks': len([f for f in affected_farms if f.active_houses > 0])
            }
        }
        
        return Response(impact_data)
        
    except Program.DoesNotExist:
        return Response(
            {'error': 'Program not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# Updated Farm views to include program
class FarmWithProgramListCreateView(generics.ListCreateAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmWithProgramSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FarmListSerializer
        return FarmWithProgramSerializer


class FarmWithProgramDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmWithProgramSerializer
