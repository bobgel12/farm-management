"""
Django management command to ensure a default program exists
"""
from django.core.management.base import BaseCommand
from farms.models import Program, ProgramTask
from tasks.task_scheduler import TaskScheduler


class Command(BaseCommand):
    help = 'Ensure a default program exists in the database'

    def handle(self, *args, **options):
        # Check if default program already exists
        try:
            default_program = Program.objects.get(is_default=True, is_active=True)
            self.stdout.write(
                self.style.SUCCESS(f'Default program already exists: {default_program.name}')
            )
            return
        except Program.DoesNotExist:
            pass

        # Create default program from existing task scheduler
        self.stdout.write('Creating default program from task scheduler...')
        
        default_program = Program.objects.create(
            name="Default Chicken Program",
            description="Default program based on existing task scheduler templates",
            duration_days=40,
            is_active=True,
            is_default=True
        )
        
        # Convert task scheduler templates to program tasks
        self.create_program_tasks_from_scheduler(default_program)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created default program: {default_program.name}')
        )

    def create_program_tasks_from_scheduler(self, program):
        """Create program tasks from the existing task scheduler templates"""
        task_templates = TaskScheduler.TASK_TEMPLATES
        tasks_created = 0
        
        for day_offset, tasks in task_templates.items():
            for task_template in tasks:
                # Map task types to program task types
                task_type_mapping = {
                    'setup': 'one_time',
                    'daily': 'daily',
                    'special': 'one_time',
                    'exit': 'one_time',
                    'cleanup': 'one_time'
                }
                
                # Map task types to priorities
                priority_mapping = {
                    'setup': 'critical',
                    'daily': 'medium',
                    'special': 'high',
                    'exit': 'critical',
                    'cleanup': 'low'
                }
                
                program_task_type = task_type_mapping.get(task_template['task_type'], 'daily')
                priority = priority_mapping.get(task_template['task_type'], 'medium')
                
                # Create program task
                ProgramTask.objects.create(
                    program=program,
                    day=day_offset,
                    task_type=program_task_type,
                    title=task_template['task_name'],
                    description=task_template['description'],
                    instructions=task_template['description'],  # Use description as instructions
                    priority=priority,
                    estimated_duration=30,  # Default 30 minutes
                    is_required=True,
                    requires_confirmation=False
                )
                tasks_created += 1
        
        # Add recurring tasks
        self.add_recurring_tasks_to_program(program)
        
        self.stdout.write(f'Created {tasks_created} tasks for default program')

    def add_recurring_tasks_to_program(self, program):
        """Add recurring tasks to the program"""
        recurring_tasks = [
            {
                'day': 0, 'task_type': 'recurring', 'title': 'Generator Check',
                'description': 'Check generator every Monday at 9am',
                'instructions': '1. Check generator fuel level\n2. Test generator start\n3. Check oil level\n4. Record status',
                'priority': 'high', 'estimated_duration': 30, 'is_required': True,
                'recurring_days': [0]  # Monday
            },
            {
                'day': 0, 'task_type': 'recurring', 'title': 'Feed Bin Check',
                'description': 'Check and report feed bin every Monday and Thursday',
                'instructions': '1. Check feed levels\n2. Record consumption\n3. Report to management\n4. Order if needed',
                'priority': 'medium', 'estimated_duration': 20, 'is_required': True,
                'recurring_days': [0, 3]  # Monday and Thursday
            }
        ]
        
        for task_data in recurring_tasks:
            ProgramTask.objects.create(program=program, **task_data)
