from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Farm, Worker, Program, ProgramTask
from .serializers import (
    FarmSerializer, FarmListSerializer, WorkerSerializer,
    ProgramSerializer, ProgramListSerializer, ProgramTaskSerializer,
    FarmWithProgramSerializer
)


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
