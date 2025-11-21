from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Task, RecurringTask, EmailTask
from .serializers import TaskSerializer, TaskListSerializer, TaskCompletionSerializer, RecurringTaskSerializer
from .task_scheduler import TaskScheduler
from .email_service import TaskEmailService
from houses.models import House


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        house_id = self.request.query_params.get('house_id')
        day_offset = self.request.query_params.get('day_offset')
        
        queryset = Task.objects.all()
        
        if house_id:
            queryset = queryset.filter(house_id=house_id)
        
        if day_offset:
            queryset = queryset.filter(day_offset=day_offset)
        
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TaskListSerializer
        return TaskSerializer


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


@api_view(['POST'])
def complete_task(request, task_id):
    """Mark a task as completed"""
    task = get_object_or_404(Task, id=task_id)
    serializer = TaskCompletionSerializer(data=request.data)
    
    if serializer.is_valid():
        task.mark_completed(
            completed_by=serializer.validated_data.get('completed_by', ''),
            notes=serializer.validated_data.get('notes', '')
        )
        return Response(TaskSerializer(task).data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def house_tasks(request, house_id):
    """Get all tasks for a specific house"""
    house = get_object_or_404(House, id=house_id)
    tasks = Task.objects.filter(house=house).order_by('day_offset', 'task_name')
    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def today_tasks(request, house_id):
    """Get today's tasks for a specific house"""
    house = get_object_or_404(House, id=house_id)
    tasks = TaskScheduler.get_today_tasks(house)
    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def upcoming_tasks(request, house_id):
    """Get upcoming tasks for a specific house"""
    house = get_object_or_404(House, id=house_id)
    days_ahead = request.query_params.get('days', 7)
    tasks = TaskScheduler.get_upcoming_tasks(house, int(days_ahead))
    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def generate_tasks(request, house_id):
    """Generate all tasks for a house"""
    house = get_object_or_404(House, id=house_id)
    tasks = TaskScheduler.generate_tasks_for_house(house)
    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def task_dashboard(request):
    """Get dashboard data for tasks"""
    # Get all incomplete tasks
    incomplete_tasks = Task.objects.filter(is_completed=False)
    
    # Get today's tasks across all houses
    today_tasks = []
    for house in House.objects.filter(is_active=True):
        current_day = house.current_day
        if current_day is not None:
            house_tasks = Task.objects.filter(
                house=house,
                day_offset=current_day,
                is_completed=False
            )
            for task in house_tasks:
                today_tasks.append({
                    'id': task.id,
                    'house_name': str(house),
                    'farm_name': house.farm.name,
                    'task_name': task.task_name,
                    'description': task.description,
                    'task_type': task.task_type
                })
    
    # Get overdue tasks (tasks from previous days that are incomplete)
    overdue_tasks = []
    for house in House.objects.filter(is_active=True):
        current_day = house.current_day
        if current_day is not None and current_day > 0:
            overdue = Task.objects.filter(
                house=house,
                day_offset__lt=current_day,
                is_completed=False
            )
            for task in overdue:
                overdue_tasks.append({
                    'id': task.id,
                    'house_name': str(house),
                    'farm_name': house.farm.name,
                    'task_name': task.task_name,
                    'description': task.description,
                    'day_offset': task.day_offset,
                    'days_overdue': current_day - task.day_offset
                })
    
    data = {
        'total_incomplete_tasks': incomplete_tasks.count(),
        'today_tasks': today_tasks,
        'overdue_tasks': overdue_tasks,
        'overdue_count': len(overdue_tasks)
    }
    return Response(data)


class RecurringTaskListCreateView(generics.ListCreateAPIView):
    queryset = RecurringTask.objects.all()
    serializer_class = RecurringTaskSerializer


class RecurringTaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RecurringTask.objects.all()
    serializer_class = RecurringTaskSerializer


@api_view(['POST'])
def send_test_email(request):
    """Send a test email for a specific farm"""
    farm_id = request.data.get('farm_id')
    test_email = request.data.get('test_email')
    
    if not farm_id or not test_email:
        return Response(
            {'error': 'farm_id and test_email are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        success, message = TaskEmailService.send_test_email(farm_id, test_email)
        
        if success:
            return Response({'message': message})
        else:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'error': f'Failed to send test email: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def send_daily_tasks(request):
    """Manually trigger daily task email sending for all farms or specific farm"""
    farm_id = request.data.get('farm_id')
    force = request.data.get('force', False)  # Allow forcing resend even if already sent today
    
    try:
        if farm_id:
            # Send emails for specific farm
            from farms.models import Farm
            farm = Farm.objects.get(id=farm_id)
            sent_count, message = TaskEmailService.send_farm_task_reminders(farm, force=force)
            
            if sent_count > 0:
                return Response({
                    'message': message,
                    'sent': True
                })
            else:
                # Return 200 with warning message instead of error
                return Response({
                    'message': message,
                    'sent': False,
                    'warning': True
                })
        else:
            # Send emails for all farms
            sent_count = TaskEmailService.send_daily_task_reminders(force=force)
            if sent_count > 0:
                return Response({
                    'message': f'Successfully sent {sent_count} daily task reminder emails',
                    'sent': True
                })
            else:
                return Response({
                    'message': 'No emails were sent. This may be because emails were already sent today, no active workers found, or no tasks available.',
                    'sent': False,
                    'warning': True
                })
    except Farm.DoesNotExist:
        return Response(
            {'error': 'Farm not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to send daily task emails: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def email_history(request):
    """Get email sending history"""
    farm_id = request.query_params.get('farm_id')
    
    queryset = EmailTask.objects.all()
    if farm_id:
        queryset = queryset.filter(farm_id=farm_id)
    
    queryset = queryset.order_by('-sent_date', '-sent_time')
    
    data = []
    for email_task in queryset:
        data.append({
            'id': email_task.id,
            'farm_name': email_task.farm.name,
            'sent_date': email_task.sent_date,
            'sent_time': email_task.sent_time,
            'recipients': email_task.recipients,
            'subject': email_task.subject,
            'houses_included': email_task.houses_included,
            'tasks_count': email_task.tasks_count,
            'created_at': email_task.created_at
        })
    
    return Response(data)
