from rest_framework import generics, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from .models import Farm, Worker, Program, ProgramTask, ProgramChangeLog, Breed, Flock, FlockPerformance, FlockComparison
from .serializers import (
    FarmSerializer, FarmListSerializer, WorkerSerializer,
    ProgramSerializer, ProgramListSerializer, ProgramTaskSerializer,
    FarmWithProgramSerializer, BreedSerializer, BreedListSerializer,
    FlockSerializer, FlockListSerializer, FlockPerformanceSerializer,
    FlockComparisonSerializer
)
from .program_change_service import ProgramChangeService
from integrations.rotem import RotemIntegration
from integrations.models import IntegrationLog, IntegrationError


class FarmViewSet(ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    
    def get_queryset(self):
        """Filter farms based on organization"""
        queryset = Farm.objects.all()
        
        # Filter by organization if specified
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        
        # If user is authenticated and not staff, filter by user's organizations
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            from organizations.models import OrganizationUser
            user_organizations = OrganizationUser.objects.filter(
                user=self.request.user,
                is_active=True
            ).values_list('organization_id', flat=True)
            queryset = queryset.filter(organization_id__in=user_organizations)
        
        return queryset.order_by('name')
    
    def update(self, request, *args, **kwargs):
        """Override update to detect program changes and regenerate tasks"""
        instance = self.get_object()
        old_program_id = instance.program_id if instance.program else None
        
        # Perform the update
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Refresh instance to get updated program
            instance.refresh_from_db()
            new_program_id = instance.program_id if instance.program else None
            
            # Check if program changed
            if old_program_id != new_program_id and new_program_id is not None:
                # Program changed, regenerate tasks for all active houses
                try:
                    from .program_change_service import ProgramChangeService
                    success = ProgramChangeService.regenerate_tasks_for_farm(instance, force_regenerate=True)
                    if success:
                        response.data['program_changed'] = True
                        response.data['tasks_regenerated'] = True
                        response.data['message'] = f'Tasks regenerated for all active houses using program "{instance.program.name}"'
                except Exception as e:
                    response.data['program_changed'] = True
                    response.data['tasks_regenerated'] = False
                    response.data['error'] = f'Failed to regenerate tasks: {str(e)}'
        
        return response
    
    @action(detail=True, methods=['post'])
    def configure_integration(self, request, pk=None):
        """Configure system integration for a farm"""
        farm = self.get_object()
        integration_type = request.data.get('integration_type')
        program_id = request.data.get('program_id')
        
        # Update program if provided
        if program_id:
            try:
                program = Program.objects.get(id=program_id, is_active=True)
                old_program_id = farm.program_id if farm.program else None
                farm.program = program
                farm.save()
                
                # If program changed, regenerate tasks
                if old_program_id != program_id:
                    from .program_change_service import ProgramChangeService
                    ProgramChangeService.regenerate_tasks_for_farm(farm, force_regenerate=True)
            except Program.DoesNotExist:
                return Response({
                    'error': f'Program with id {program_id} not found'
                }, status=status.HTTP_400_BAD_REQUEST)
        
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
        """Sync data from integrated system and generate houses/tasks"""
        farm = self.get_object()
        
        # Check if farm has a program before generating tasks
        force_regenerate = request.data.get('force_regenerate', False)
        if not farm.program:
            # Try to get default program
            try:
                default_program = Program.objects.get(is_default=True, is_active=True)
                farm.program = default_program
                farm.save()
            except Program.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Farm has no program assigned. Please select a program in the Configuration dialog before generating tasks.',
                    'requires_program_selection': True
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if farm.integration_type == 'rotem':
            try:
                integration = RotemIntegration(farm)
                
                # Sync house data (sensor data)
                data = integration.sync_house_data(farm.id)
                
                # Generate/update houses and tasks
                self._sync_rotem_houses(farm, force_regenerate=force_regenerate)
                
                # Update last sync time
                farm.last_sync = timezone.now()
                farm.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Data synced successfully and houses/tasks generated',
                    'data_points': len(data.get('houses', [])),
                    'program_used': farm.program.name if farm.program else None
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
    
    def _sync_rotem_houses(self, farm, force_regenerate=False):
        """Sync houses from Rotem system and generate tasks"""
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
                
                # Get age from Rotem system (returns 0 if not available)
                age = integration.get_house_age(farm.id, i)
                house.current_age_days = age
                
                # Calculate batch start date based on age
                if age > 0:
                    # Calculate the actual chicken in date based on current age
                    house.batch_start_date = timezone.now().date() - timezone.timedelta(days=age)
                    house.chicken_in_date = house.batch_start_date  # Set chicken_in_date to the calculated batch start date
                    house.expected_harvest_date = house.batch_start_date + timezone.timedelta(days=49)  # Typical 7-week cycle
                    house.current_day = age
                else:
                    # If age is 0, set default dates for new batch
                    house.batch_start_date = timezone.now().date()
                    house.chicken_in_date = house.batch_start_date
                    house.expected_harvest_date = house.batch_start_date + timezone.timedelta(days=49)
                    house.current_day = 0
                
                house.save()
                
                # Generate tasks for this house based on its age and assigned program
                # Generate tasks if age >= 0 (house exists, even if empty)
                self._generate_house_tasks(house, farm, force_regenerate=force_regenerate)
                
                # Log successful house sync
                IntegrationLog.objects.create(
                    farm=farm,
                    integration_type='rotem',
                    action='sync_house',
                    status='success',
                    message=f'Synced house {i} with age {age} days'
                )
                    
        except Exception as e:
            # Log error but don't fail the integration setup
            IntegrationError.objects.create(
                farm=farm,
                integration_type='rotem',
                error_type='house_sync',
                error_message=f'Failed to sync houses: {str(e)}',
                error_code='HOUSE_SYNC_FAILED'
            )
    
    def _generate_house_tasks(self, house, farm, force_regenerate=False):
        """Generate tasks for a house based on its age and assigned program"""
        try:
            from tasks.models import Task
            from tasks.task_scheduler import TaskScheduler
            
            # Check if farm has a program assigned
            program = farm.program
            if not program:
                # Try to get default program
                try:
                    program = Program.objects.get(is_default=True, is_active=True)
                except Program.DoesNotExist:
                    IntegrationError.objects.create(
                        farm=farm,
                        integration_type='rotem',
                        error_type='task_generation',
                        error_message=f'Cannot generate tasks for house {house.house_number}: farm has no program assigned and no default program exists',
                        error_code='NO_PROGRAM_ASSIGNED'
                    )
                    return []
            
            # Check if tasks already exist
            existing_tasks_count = Task.objects.filter(house=house).count()
            if existing_tasks_count > 0 and not force_regenerate:
                # Tasks already exist, return existing tasks
                IntegrationLog.objects.create(
                    farm=farm,
                    integration_type='rotem',
                    action='generate_tasks',
                    status='skipped',
                    message=f'Tasks already exist for house {house.house_number} ({existing_tasks_count} tasks). Use force_regenerate=True to regenerate.'
                )
                return list(Task.objects.filter(house=house))
            
            # Get the house's current day (day_offset)
            current_day = house.current_day
            if current_day is None:
                # If no current_day, calculate from chicken_in_date
                if house.chicken_in_date:
                    from django.utils import timezone
                    days_since_in = (timezone.now().date() - house.chicken_in_date).days
                    current_day = days_since_in
                    house.current_day = current_day
                    house.save()
                else:
                    # Can't generate tasks without a day reference
                    IntegrationError.objects.create(
                        farm=farm,
                        integration_type='rotem',
                        error_type='task_generation',
                        error_message=f'Cannot generate tasks for house {house.house_number}: no current_day or chicken_in_date',
                        error_code='TASK_GENERATION_FAILED'
                    )
                    return []
            
            # Generate tasks from program
            try:
                tasks = TaskScheduler.generate_tasks_from_program(house, program, force_regenerate=force_regenerate)
            except ValueError as e:
                # If program has no tasks, fall back to default templates
                tasks = TaskScheduler.generate_tasks_for_house(house)
            
            # Log task generation
            IntegrationLog.objects.create(
                farm=farm,
                integration_type='rotem',
                action='generate_tasks',
                status='success',
                message=f'Generated {len(tasks)} Task objects for house {house.house_number} from program "{program.name}" (Day {current_day})'
            )
            
            return tasks
            
        except Exception as e:
            IntegrationError.objects.create(
                farm=farm,
                integration_type='rotem',
                error_type='task_generation',
                error_message=f'Failed to generate tasks for house {house.house_number}: {str(e)}',
                error_code='TASK_GENERATION_FAILED'
            )
            return []
    
    def _create_default_program_tasks(self, program):
        """Create default broiler program tasks"""
        default_tasks = [
            # Week 1 (Days 1-7)
            {'task_name': 'Daily Health Check', 'description': 'Check bird health, temperature, and behavior', 'task_type': 'health_check', 'priority': 'high', 'start_day': 1, 'end_day': 49, 'estimated_duration': 30},
            {'task_name': 'Feed Management', 'description': 'Monitor feed consumption and adjust feeders', 'task_type': 'feeding', 'priority': 'high', 'start_day': 1, 'end_day': 49, 'estimated_duration': 45},
            {'task_name': 'Water System Check', 'description': 'Check water lines, nipples, and pressure', 'task_type': 'water_management', 'priority': 'high', 'start_day': 1, 'end_day': 49, 'estimated_duration': 20},
            {'task_name': 'Temperature Monitoring', 'description': 'Monitor house temperature and adjust heating', 'task_type': 'environmental', 'priority': 'high', 'start_day': 1, 'end_day': 14, 'estimated_duration': 15},
            
            # Week 2-3 (Days 8-21)
            {'task_name': 'Ventilation Check', 'description': 'Check ventilation system and air quality', 'task_type': 'environmental', 'priority': 'medium', 'start_day': 8, 'end_day': 49, 'estimated_duration': 25},
            {'task_name': 'Litter Management', 'description': 'Check litter condition and add fresh bedding if needed', 'task_type': 'housekeeping', 'priority': 'medium', 'start_day': 8, 'end_day': 49, 'estimated_duration': 60},
            
            # Week 4-5 (Days 22-35)
            {'task_name': 'Weight Check', 'description': 'Sample birds for weight monitoring', 'task_type': 'monitoring', 'priority': 'medium', 'start_day': 22, 'end_day': 49, 'estimated_duration': 30},
            {'task_name': 'Feed Adjustment', 'description': 'Adjust feed type based on bird age', 'task_type': 'feeding', 'priority': 'medium', 'start_day': 22, 'end_day': 35, 'estimated_duration': 20},
            
            # Week 6-7 (Days 36-49)
            {'task_name': 'Pre-Harvest Preparation', 'description': 'Prepare for harvest - reduce feed, check equipment', 'task_type': 'harvest_prep', 'priority': 'high', 'start_day': 36, 'end_day': 49, 'estimated_duration': 45},
            {'task_name': 'Equipment Check', 'description': 'Check all equipment for harvest readiness', 'task_type': 'maintenance', 'priority': 'medium', 'start_day': 42, 'end_day': 49, 'estimated_duration': 30},
        ]
        
        for task_data in default_tasks:
            ProgramTask.objects.create(
                program=program,
                task_name=task_data['task_name'],
                description=task_data['description'],
                task_type=task_data['task_type'],
                priority=task_data['priority'],
                start_day=task_data['start_day'],
                end_day=task_data['end_day'],
                estimated_duration=task_data['estimated_duration'],
                is_active=True
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


# Breed Views
class BreedViewSet(ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = []  # Will be handled by authentication middleware
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BreedListSerializer
        return BreedSerializer
    
    def get_queryset(self):
        """Filter breeds based on organization if needed"""
        queryset = Breed.objects.filter(is_active=True)
        # Add organization filtering if needed in the future
        return queryset


# Flock Views
class FlockViewSet(ModelViewSet):
    queryset = Flock.objects.all()
    serializer_class = FlockSerializer
    permission_classes = []  # Will be handled by authentication middleware
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FlockListSerializer
        return FlockSerializer
    
    def get_queryset(self):
        """Filter flocks based on house, farm, or organization"""
        queryset = Flock.objects.select_related('house', 'breed', 'house__farm').all()
        
        # Filter by house
        house_id = self.request.query_params.get('house_id')
        if house_id:
            queryset = queryset.filter(house_id=house_id)
        
        # Filter by farm
        farm_id = self.request.query_params.get('farm_id')
        if farm_id:
            queryset = queryset.filter(house__farm_id=farm_id)
        
        # Filter by organization
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(house__farm__organization_id=organization_id)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter active flocks
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by breed
        breed_id = self.request.query_params.get('breed_id')
        if breed_id:
            queryset = queryset.filter(breed_id=breed_id)
        
        return queryset.order_by('-arrival_date', 'batch_number')
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get performance records for a flock"""
        flock = self.get_object()
        performance_records = flock.performance_records.all().order_by('record_date', 'flock_age_days')
        serializer = FlockPerformanceSerializer(performance_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_performance_record(self, request, pk=None):
        """Add a performance record for a flock"""
        flock = self.get_object()
        serializer = FlockPerformanceSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                flock=flock,
                recorded_by=request.user if request.user.is_authenticated else None
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark flock as completed"""
        flock = self.get_object()
        
        from farms.services import FlockManagementService
        
        actual_harvest_date = request.data.get('actual_harvest_date')
        final_count = request.data.get('final_count')
        
        updated_flock = FlockManagementService.complete_flock(
            flock,
            actual_harvest_date=actual_harvest_date,
            final_count=final_count
        )
        
        serializer = self.get_serializer(updated_flock)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """Get comprehensive flock summary"""
        flock = self.get_object()
        
        from farms.services import FlockManagementService
        summary = FlockManagementService.get_flock_summary(flock)
        
        return Response(summary)
    
    @action(detail=True, methods=['post'])
    def calculate_performance(self, request, pk=None):
        """Calculate and record flock performance"""
        flock = self.get_object()
        
        from farms.services import FlockManagementService
        
        record_date = request.data.get('record_date')
        if record_date:
            from datetime import datetime
            record_date = datetime.strptime(record_date, '%Y-%m-%d').date()
        
        performance = FlockManagementService.calculate_flock_performance(flock, record_date)
        
        serializer = FlockPerformanceSerializer(performance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FlockPerformanceViewSet(ModelViewSet):
    queryset = FlockPerformance.objects.all()
    serializer_class = FlockPerformanceSerializer
    permission_classes = []  # Will be handled by authentication middleware
    
    def get_queryset(self):
        """Filter performance records based on flock"""
        queryset = FlockPerformance.objects.select_related('flock').all()
        
        flock_id = self.request.query_params.get('flock_id')
        if flock_id:
            queryset = queryset.filter(flock_id=flock_id)
        
        return queryset.order_by('-record_date', '-flock_age_days')


class FlockComparisonViewSet(ModelViewSet):
    queryset = FlockComparison.objects.all()
    serializer_class = FlockComparisonSerializer
    permission_classes = []  # Will be handled by authentication middleware
    
    def get_queryset(self):
        """Filter comparisons based on user"""
        queryset = FlockComparison.objects.prefetch_related('flocks').all()
        
        # Filter by organization if needed
        organization_id = self.request.query_params.get('organization_id')
        if organization_id:
            queryset = queryset.filter(flocks__house__farm__organization_id=organization_id).distinct()
        
        # Filter by creator
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Calculate comparison results for a comparison"""
        comparison = self.get_object()
        
        from farms.services import FlockManagementService
        
        # Get comparison metrics
        metrics = request.data.get('metrics', comparison.comparison_metrics or [])
        
        # Use service to calculate comparison
        flocks = comparison.flocks.all()
        results = FlockManagementService.compare_flocks(flocks, metrics)
        
        # Save results
        comparison.comparison_metrics = metrics
        comparison.comparison_results = results
        comparison.save()
        
        return Response({
            'comparison': FlockComparisonSerializer(comparison).data,
            'results': results
        })
    
    def _calculate_comparison(self, comparison, metrics):
        """Calculate comparison results between flocks"""
        flocks = comparison.flocks.all()
        results = {
            'flocks': [],
            'comparisons': {}
        }
        
        for flock in flocks:
            flock_data = {
                'id': flock.id,
                'batch_number': flock.batch_number,
                'house': str(flock.house),
                'arrival_date': flock.arrival_date.isoformat(),
                'breed': flock.breed.name if flock.breed else None,
            }
            
            # Calculate metrics for each flock
            for metric in metrics:
                value = self._calculate_metric(flock, metric)
                flock_data[metric] = value
            
            results['flocks'].append(flock_data)
        
        # Calculate comparisons
        if len(flocks) > 1:
            for metric in metrics:
                values = [f[metric] for f in results['flocks'] if metric in f and f[metric] is not None]
                if values:
                    results['comparisons'][metric] = {
                        'min': min(values),
                        'max': max(values),
                        'average': sum(values) / len(values),
                        'range': max(values) - min(values)
                    }
        
        return results
    
    def _calculate_metric(self, flock, metric):
        """Calculate a specific metric for a flock"""
        if metric == 'mortality_rate':
            return flock.mortality_rate
        elif metric == 'livability':
            return flock.livability
        elif metric == 'current_age_days':
            return flock.current_age_days
        elif metric == 'days_until_harvest':
            return flock.days_until_harvest
        elif metric == 'current_chicken_count':
            return flock.current_chicken_count
        elif metric == 'mortality_count':
            return flock.mortality_count
        # Add more metrics as needed
        return None
