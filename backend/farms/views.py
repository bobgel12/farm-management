from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Farm, Worker, Program, ProgramTask, ProgramChangeLog
from .serializers import (
    FarmSerializer, FarmListSerializer, WorkerSerializer,
    ProgramSerializer, ProgramListSerializer, ProgramTaskSerializer,
    FarmWithProgramSerializer
)
from .program_change_service import ProgramChangeService


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
